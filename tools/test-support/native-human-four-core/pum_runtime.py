"""Actual Pum bootstrap/CAS. Trusted fixture setup is not authentication evidence."""
import base64
import copy
import http.client
import ipaddress
import json
from pathlib import Path
import re
import secrets
import socket
import ssl
import time
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from supervisor import private, require


def port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def initial_policy(client_ip):
    ip = ipaddress.ip_address(client_ip)
    network = str(ip) + ('/32' if ip.version == 4 else '/128')
    return {'revision': 1, 'policy': {'version': 1, 'information_classes': ['internal'],
        'services': {'orders': {'permissions': ['read'], 'require_guard': True,
            'roles': {'reader1': {'permissions': ['read'], 'information_classes': ['internal'], 'minimum_aal': 1},
                      'reader2': {'permissions': ['read'], 'information_classes': ['internal'], 'minimum_aal': 2}},
            'users': {}, 'workload_users': {}, 'human_users': {},
            'networks': [{'cidr': network, 'roles': ['reader1']}]}},
        'resources': {'db:orders': {'service': 'orders', 'information_class': 'internal', 'actions': {'select': 'read'}}}}}


def transport(tls, address, token_env):
    require(address.startswith('https://'), 'pum_owner_https')
    return dict(tls, address=address, token_env=token_env)


class PumRuntime:
    def __init__(self, supervisor, tls, caller, client_ip='192.0.2.10', grpc_port=None, admin_port=None):
        require(type(caller) is str and 32 <= len(caller) <= 4096, 'pum_caller')
        require(set(tls) == {'ca', 'certificate', 'key', 'server_name'} and tls['server_name'] == 'localhost', 'pum_tls')
        self.supervisor = supervisor
        self.root = supervisor.root/'pum'
        self.root.mkdir(mode=0o700)
        self.tls = dict(tls)
        self.caller = caller
        self.admin = secrets.token_hex(32)
        self.seed = secrets.token_bytes(32)
        self.public_key = base64.b64encode(ed25519.Ed25519PrivateKey.from_private_bytes(self.seed).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
        self.grpc_port = grpc_port or port()
        self.admin_port = admin_port or port()
        require(type(self.grpc_port) is int and type(self.admin_port) is int and 1 <= self.grpc_port <= 65535 and 1 <= self.admin_port <= 65535 and self.grpc_port != self.admin_port, 'pum_ports')
        self.endpoint = f'https://127.0.0.1:{self.grpc_port}'
        self.admin_endpoint = f'https://127.0.0.1:{self.admin_port}'
        self.document = initial_policy(client_ip)
        self.client_ip = str(ipaddress.ip_address(client_ip))
        self.process = None
        self.context = ssl.create_default_context(cafile=tls['ca'])
        self.context.load_cert_chain(tls['certificate'], tls['key'])

    def start(self, hopready, sumready, route_transport, scopes, plan_transport, hop_caller, route_caller, network_caller=None):
        require(self.process is None, 'pum_already_started')
        require(scopes and all(s['service'] == 'orders' and s['audience'] == 'orders-api' for s in scopes), 'pum_fixed_scopes')
        require(hopready['issuer_ref'] == 'native-human', 'pum_hop_issuer')
        key = base64.b64decode(hopready['public_key'], validate=True)
        require(len(key) == 32, 'pum_hop_public_key')
        require(str(ipaddress.ip_address(sumready['client_ip'])) == self.client_ip, 'pum_network_ip')
        if network_caller is None:
            network_caller = Path(sumready['collector_file']).read_text()
        def write(name, value):
            path = self.root/name
            private(path, value)
            return str(path)
        policy = write('policy.json', self.document)
        trust = write('trust.json', {'entries': [{'issuer_ref': 'native-human', 'key_epoch': 1, 'identity_epoch': 'owned-human', 'service': 'orders', 'audience': 'orders-api', 'minimum_revision': 7, 'public_key': hopready['public_key']}]})
        hop = transport(self.tls, hopready['endpoint'], 'FOUR_HOP_CALLER')
        hop.update(issuer_ref='native-human', observed_clock_rates={'source_ppm': 500, 'receiver_ppm': 500})
        human = write('human.json', {'transport': hop, 'minimum_source_revision': 7, 'minimum_application_generation': 1, 'minimum_key_registry_revision': 1, 'scopes': copy.deepcopy(scopes)})
        network = write('network.json', transport(self.tls, sumready['endpoint'], 'FOUR_NETWORK_CALLER'))
        route = write('route.json', transport(self.tls, route_transport['address'], 'FOUR_ROUTE_CALLER'))
        plan = write('plan.json', transport(self.tls, plan_transport['address'], 'FOUR_HOP_CALLER'))
        signer = write('signer.json', {'issuer_ref': 'pumgye', 'key_epoch': 1, 'public_key': self.public_key, 'seed_env': 'FOUR_PUM_SEED'})
        argv = [self.supervisor.entries['pumgye']['binary'], '--listen', f'127.0.0.1:{self.admin_port}', '--grpc-listen', f'127.0.0.1:{self.grpc_port}', '--database', str(self.root/'authority.sqlite3'), '--policy', policy, '--tls-cert', self.tls['certificate'], '--tls-key', self.tls['key'], '--client-ca', self.tls['ca'], '--human-observed-permits', '--human-authentication-live', human, '--authentication-trust', trust, '--permit-key', signer, '--network-live', network, '--route-live', route, '--projection-live', plan]
        env = {'PUMGYE_ADMIN_TOKEN': self.admin, 'PUMGYE_DECISION_TOKEN': self.caller, 'FOUR_HOP_CALLER': hop_caller, 'FOUR_ROUTE_CALLER': route_caller, 'FOUR_NETWORK_CALLER': network_caller, 'FOUR_PUM_SEED': base64.b64encode(self.seed).decode()}
        self.process = self.supervisor.start('pumgye', argv, env)
        deadline = time.monotonic()+15
        while True:
            require(self.process.poll() is None, 'pum_startup_exit')
            try:
                status, document = self.request('GET')
                if status == 200:
                    require(document['policy']['services']['orders'].get('human_users', {}) == {}, 'pum_initial_empty')
                    break
            except OSError:
                pass
            require(time.monotonic() < deadline, 'pum_readiness')
            time.sleep(.05)
        self.ready = {'endpoint': self.endpoint, 'public_key': self.public_key, 'issuer_ref': 'pumgye', 'key_epoch': 1, 'identity_authority': 'pumgye', 'revision': document['revision'], **self.tls}
        return self.ready

    def request(self, method, document=None, revision=None):
        connection = http.client.HTTPSConnection('127.0.0.1', self.admin_port, context=self.context, timeout=2)
        headers = {'Authorization': 'Bearer '+self.admin, 'Content-Type': 'application/json'}
        if revision is not None:
            headers['If-Match'] = '"'+str(revision)+'"'
        try:
            connection.request(method, '/v1/policy', body=None if document is None else json.dumps(document), headers=headers)
            response = connection.getresponse()
            raw = response.read(65537)
            require(len(raw) <= 65536, 'pum_management_body')
            if response.status >= 400:
                return response.status, None # Preserve status without logging arbitrary error body.
            return response.status, json.loads(raw)
        finally:
            connection.close()

    def policy(self):
        status, document = self.request('GET')
        require(status == 200, 'pum_policy_get')
        return document

    def grant(self, subjects, minimum_aal=1):
        require(type(minimum_aal) is int and minimum_aal in (1, 2), 'pum_aal')
        require(type(subjects) is list and 1 <= len(subjects) <= 16 and len(set(subjects)) == len(subjects), 'pum_subjects')
        require(all(type(s) is str and re.fullmatch('human1:[0-9a-f]{64}', s) for s in subjects), 'pum_subject')
        document = self.policy()
        for subject in subjects:
            document['policy']['services']['orders'].setdefault('human_users', {})[subject] = ['reader'+str(minimum_aal)]
        return self.publish(document)

    def withdraw(self, subjects):
        require(type(subjects) is list and 1 <= len(subjects) <= 16 and all(type(s) is str and re.fullmatch('human1:[0-9a-f]{64}', s) for s in subjects), 'pum_subjects')
        document = self.policy()
        for subject in subjects:
            document['policy']['services']['orders'].setdefault('human_users', {}).pop(subject, None)
        return self.publish(document)

    def publish(self, document):
        # Policy is low-frequency owning metadata, never an auth/source proof.
        require(not document['policy']['services']['orders']['users'] and not document['policy']['services']['orders'].get('workload_users', {}), 'pum_no_class_fallback')
        status, updated = self.request('PUT', document, document['revision'])
        require(status == 200, 'pum_policy_cas')
        return updated
