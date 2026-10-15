"""Opt-in live Workload orchestration. Imported without network side effects.

Execution requires parent-approved artifacts and an exclusive owned-cluster lease.
Pure tests use fake kube functions; never manufacture native SDK capabilities.
"""
import base64
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import subprocess
import time
from kubernetes_workload_plan import bootstrap, configuration_patches, token_request

TAP_SHA256 = '775a14a97c3842a9161911e4f2168195d6e19d2dc62faaaf419d513da6740806'
HELD_SHA256 = 'c6e34ba9429a0ecc9f24803640d69b5f7159734da3557d3924de353d634d33c2'
TAP_SOURCE = '640a3dd487d81d908e8caedfeeb830e15357df9d'
PROBE_SHA256 = 'faa10e924f47db73a2ab4c35da372b64f8bcec97e476dcdb6bc65e9d7d95c65a'
REQUIRED = {'hopae': ['workload_observed_authentication', 'workload_observed_projection_contract3'],
            'pumgye': ['workload_observed_permits', 'typed_workload_users', 'workload_resource_metadata_decision'],
            'hangang': ['workload_observed_dispatch', 'raw_observed_transport_fence', 'workload_typed_http_preliminary_gate'],
            'sumunjang': ['native_network_check']}


PROFILE_PATH = '/v1/plugins/hopae/authentication/profiles'


def read_profile_owner(api, admin):
    code, document, _ = api(admin, PROFILE_PATH)
    if (code != 200 or not isinstance(document, dict)
            or type(document.get('revision')) is not int or document['revision'] < 1
            or not isinstance(document.get('configuration'), dict)
            or not re.fullmatch(r'[0-9a-f]{64}', document.get('digest', ''))):
        raise AssertionError('native profile owner readback unavailable')
    return copy.deepcopy(document)


def publish_profile_owner(api, admin, current, configuration):
    # The existing authenticated plugin transport supplies signed native admin
    # delegation. This is a durable owning CAS, never a bootstrap-file mutation.
    code, acknowledged, _ = api(admin, PROFILE_PATH + '/publish', 'POST', {
        'revision': current['revision'], 'configuration': configuration})
    if (code != 200 or not isinstance(acknowledged, dict)
            or type(acknowledged.get('revision')) is not int
            or acknowledged['revision'] != current['revision'] + 1
            or not re.fullmatch(r'[0-9a-f]{64}', acknowledged.get('digest', ''))):
        raise AssertionError('native profile publication refused or mismatched')
    active = read_profile_owner(api, admin)
    if (active['revision'] != acknowledged['revision']
            or active['digest'] != acknowledged['digest']
            or active['configuration'] != configuration):
        raise AssertionError('native profile publication activation mismatch')
    return active


@contextmanager
def temporary_workload_realm(api, admin, *, service, host, original_realm, changed_realm):
    original = read_profile_owner(api, admin)
    changed = copy.deepcopy(original['configuration'])
    profiles = [p for p in changed.get('profiles', [])
                if p.get('service_id') == service and p.get('host') == host]
    if (len(profiles) != 1 or profiles[0].get('realm') != original_realm
            or profiles[0].get('kubernetes_tokenreview', {}).get('connection', {}).get('cluster_id') != original_realm
            or changed_realm == original_realm):
        raise AssertionError('native Workload realm owner selection mismatch')
    profiles[0]['realm'] = changed_realm
    profiles[0]['kubernetes_tokenreview']['connection']['cluster_id'] = changed_realm
    try:
        publish_profile_owner(api, admin, original, changed)
        yield
    finally:
        # Reconcile an uncertain publication with one read; never replay it or
        # overwrite a third configuration. Restore using the CURRENT revision.
        current = read_profile_owner(api, admin)
        if current['configuration'] == changed:
            publish_profile_owner(api, admin, current, original['configuration'])
        elif current['configuration'] != original['configuration']:
            raise AssertionError('native profile restoration owner mismatch')


def preflight(args):
    """Check local reviewed provenance before even resolving the kube wrapper."""
    if not args.workload:
        return
    if args.browser_probe or args.authenticated_client or args.sumunjang_native_source:
        raise ValueError('Workload runner does not yet support browser/admin UX, legacy authenticated client or combined Sum CRD source qualification')
    for name in ['workload_capabilities', 'workload_utility_image', 'workload_issuer', 'workload_cluster_id', 'workload_reviewer_audience', 'workload_tap_image', 'workload_held_client', 'workload_backup_evidence']:
        if not getattr(args, name):
            raise ValueError('--workload requires --' + name.replace('_', '-'))
    if not getattr(args, 'hopae_plugin', None):
        raise ValueError('--workload requires --hopae-plugin for owning profile CAS qualification')
    document = json.loads(args.workload_capabilities.read_text())
    if document.get('version') != 1:
        raise ValueError('reviewed Workload artifact capability manifest version1 required')
    for component, required in REQUIRED.items():
        entry = document.get('components', {}).get(component, {})
        if (entry.get('image') != getattr(args, component + '_image')
                or not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', entry.get('image', ''))
                or not re.fullmatch(r'[0-9a-f]{40}', entry.get('source', ''))
                or not re.fullmatch(r'[0-9a-f]{64}', entry.get('binary_sha256', ''))
                or not set(required).issubset(entry.get('capabilities', []))):
            raise ValueError('missing reviewed exact Workload artifact capability: ' + component)
    if (not args.receipt_client.is_file() or not os.access(args.receipt_client, os.X_OK)
            or hashlib.sha256(args.receipt_client.read_bytes()).hexdigest() != PROBE_SHA256):
        raise ValueError('frozen public Workload SDK probe hash/executable mismatch')
    tap = document.get('qualification_tools', {}).get('workload_tap', {})
    if (tap.get('image') != args.workload_tap_image
            or not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', args.workload_tap_image)
            or tap.get('source') != TAP_SOURCE or tap.get('binary_sha256') != TAP_SHA256):
        raise ValueError('reviewed exact qualification tap capability required')
    if (not args.workload_held_client.is_file() or not os.access(args.workload_held_client, os.X_OK)
            or hashlib.sha256(args.workload_held_client.read_bytes()).hexdigest() != HELD_SHA256):
        raise ValueError('frozen held public SDK probe hash/executable mismatch')
    # Reviewed backup attestation is not automatic signature/coldness validation.
    # Verify offhost file size+full SHA locally before the first kube operation.
    backup = json.loads(args.workload_backup_evidence.read_text())
    if (backup.get('version') != 1 or backup.get('cold_snapshot') is not True
            or backup.get('offhost_verified') is not True
            or not re.fullmatch(r'[0-9a-f]{64}', backup.get('sha256', ''))
            or type(backup.get('bytes')) is not int or backup['bytes'] <= 0):
        raise ValueError('reviewed cold offhost backup evidence required')
    archive = Path(backup.get('offhost_path', ''))
    if not archive.is_file() or archive.stat().st_size != backup['bytes']:
        raise ValueError('offhost backup size mismatch')
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != backup['sha256']:
        raise ValueError('offhost backup full SHA mismatch')
    if not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', args.echo_image):
        raise ValueError('Workload echo/Node utility requires exact reviewed image digest')
    if args.workload_reviewer_audience == 'orders-workload':
        raise ValueError('reviewer API audience must differ from workload audience')
    bootstrap('owned-world-preflight', args.workload_utility_image)
    configuration_patches(namespace='owned-world-preflight', api_origin='https://kubernetes.default.svc',
        issuer=args.workload_issuer, cluster=args.workload_cluster_id, audience='orders-workload', sa_uid='preflight-sa', pod_uid='preflight-pod')


def token_credential(result):
    status = result.get('status', {})
    token = status.get('token')
    expiry = datetime.fromisoformat(status.get('expirationTimestamp', '').replace('Z', '+00:00'))
    if (not isinstance(token, str) or not 32 <= len(token) <= 16384
            or expiry.tzinfo is None or expiry.timestamp() <= datetime.now(timezone.utc).timestamp() + 60):
        raise ValueError('bounded nonexpired TokenRequest credential required')
    return token


def delete_owned(kube, path, uid, resource_version=None):
    """Server-side UID precondition; no GET-then-unconditional-DELETE race."""
    if not uid:
        raise ValueError('owned UID required before deletion')
    preconditions = {'uid': uid}
    if resource_version:
        preconditions['resourceVersion'] = resource_version
    return kube('delete', '--raw', path, '-f', '-', body=json.dumps({
        'apiVersion': 'v1', 'kind': 'DeleteOptions', 'preconditions': preconditions}).encode())


class Workload:
    def __init__(self, args, namespace, kube, tokens):
        self.args, self.namespace, self.kube, self.tokens = args, namespace, kube, tokens
        self.globals = []
        self.namespace_uid = None
        self.patch = None
        self.held_processes = []

    def create(self, item):
        result = json.loads(self.kube('create', '-f', '-', '-o', 'json', body=json.dumps(item).encode()))
        uid = result['metadata']['uid']
        if item['kind'] in ['ClusterRole', 'ClusterRoleBinding']:
            plural = {'ClusterRole': 'clusterroles', 'ClusterRoleBinding': 'clusterrolebindings'}[item['kind']]
            self.globals.append((f'/apis/rbac.authorization.k8s.io/v1/{plural}/' + item['metadata']['name'], uid))
        return result

    def mint(self, audience, pod='workload-bound', uid=None, service_account='workload-client'):
        if uid is None:
            uid = json.loads(self.kube('-n', self.namespace, 'get', 'pod', pod, '-o', 'json'))['metadata']['uid']
        query = token_request(self.namespace, service_account, pod, uid, audience)
        result = json.loads(self.kube('create', '--raw', query['path'], '-f', '-', body=json.dumps(query['body']).encode()))
        token = token_credential(result)
        # Never stdout/argv/evidence. Existing diagnostics redact every token value.
        self.tokens['workload-' + str(len(self.tokens))] = token
        return 'k8s:' + token

    def prepare(self, items, config_map, hop, policy, gateway, commands, environments, env):
        current_uid = json.loads(self.kube('get', 'namespace', self.namespace, '-o', 'json'))['metadata']['uid']
        if not self.namespace_uid or current_uid != self.namespace_uid:
            raise ValueError('owned namespace replaced before bootstrap')
        owned = bootstrap(self.namespace, self.args.workload_utility_image)
        for item in owned:
            self.create(item)
        self.kube('-n', self.namespace, 'wait', '--for=condition=Ready', 'pod/workload-bound', '--timeout=120s', timeout=135)
        self.check_rbac()
        sa = json.loads(self.kube('-n', self.namespace, 'get', 'serviceaccount', 'workload-client', '-o', 'json'))
        pod = json.loads(self.kube('-n', self.namespace, 'get', 'pod', 'workload-bound', '-o', 'json'))
        discovery = json.loads(self.kube('get', '--raw', '/.well-known/openid-configuration'))
        if discovery.get('issuer') != self.args.workload_issuer:
            raise ValueError('verified cluster discovery issuer differs from pinned issuer')
        ca = json.loads(self.kube('-n', self.namespace, 'get', 'configmap', 'kube-root-ca.crt', '-o', 'json'))['data']['ca.crt']
        if '-----BEGIN CERTIFICATE-----' not in ca:
            raise ValueError('Kubernetes verified CA unavailable')
        self.tokens['kubernetes-ca'] = ca
        # Reviewer token is separate, API-audience only, requested600s, private.
        reviewer = {'apiVersion': 'authentication.k8s.io/v1', 'kind': 'TokenRequest',
                    'spec': {'audiences': [self.args.workload_reviewer_audience], 'expirationSeconds': 600}}
        result = json.loads(self.kube('create', '--raw', f'/api/v1/namespaces/{self.namespace}/serviceaccounts/workload-reviewer/token', '-f', '-', body=json.dumps(reviewer).encode()))
        self.tokens['reviewer-token'] = token_credential(result)
        self.patch = configuration_patches(namespace=self.namespace, api_origin='https://kubernetes.default.svc',
            issuer=self.args.workload_issuer, cluster=self.args.workload_cluster_id, audience='orders-workload',
            sa_uid=sa['metadata']['uid'], pod_uid=pod['metadata']['uid'])
        hop['authentication_gateway']['profiles'] = [self.patch['hop_profile']]
        hop['receipt_issuer']['workload_receipts'] = self.patch['hop_workload_receipts']
        hop['projection_receiver']['workload_observed_scopes'] = self.patch['hop_projection_receiver_workload_observed_scopes']
        gateway['http'][0]['auth']['native_resource']['observed'].update(self.patch['root_observed_patch'])
        # No derived identity grant is published until public SDK verification.
        for service in policy['services'].values():
            service['users'] = {}; service['workload_users'] = {}
        config_map['data'].update({'hopae.json': json.dumps(hop), 'hangang.json': json.dumps(gateway),
                                  'pumgye.json': json.dumps({'revision': 0, 'policy': policy})})
        config_map['data']['workload-authentication-live.json'] = config_map['data']['authentication-live.json']
        position = commands['pumgye'].index('--observed-permits')
        commands['pumgye'][position] = '--workload-observed-permits'
        position = commands['pumgye'].index('--authentication-live')
        commands['pumgye'][position:position + 2] = ['--workload-authentication-live', '/config/workload-authentication-live.json']
        environments['hopae'][:] = [item for item in environments['hopae'] if item['name'] != 'OWNED_API_KEY']
        environments['hopae'] += [env('OWNED_KUBERNETES_CA', 'kubernetes-ca'), env('OWNED_REVIEWER_TOKEN', 'reviewer-token')]
        for item in items:
            if item['kind'] == 'Secret' and item['metadata']['name'] == 'world-credentials':
                item['stringData'] = self.tokens
        self.hop = copy.deepcopy(hop)
        self.primary = self.mint('orders-workload', uid=pod['metadata']['uid'])
        if not self.api_authenticates(self.primary):
            raise AssertionError('actual API refuses initial owned Pod-bound token')
        return self.primary

    def install_tap(self, items, config_map, gateway, environments, env):
        """Only owned namespace objects; fixed peers and distinct ingress caller."""
        namespace = self.namespace
        self.tokens['tap-caller'] = secrets.token_hex(32)
        def peer(name, caller):
            return {'address': f'https://{name}.{namespace}.svc:' + ('8703' if name == 'hopae' else '9087'),
                    'server_name': f'{name}.{namespace}.svc', 'ca': '/tls/ca.crt',
                    'certificate': '/tls/client.crt', 'key': '/tls/client.key', 'caller_env': caller}
        config = {'listen': '0.0.0.0:8703', 'certificate': '/tls/tls.crt', 'key': '/tls/tls.key',
                  'client_ca': '/tls/ca.crt', 'caller_env': 'OWNED_TAP_CALLER',
                  'hop': peer('hopae', 'OWNED_RECEIPT_CALLER'), 'pum': peer('pumgye', 'OWNED_PUM_CALLER'),
                  'hop_source_ppm': 500, 'pum_source_ppm': 500, 'receiver_ppm': 500}
        config_map['data']['workload-tap.json'] = json.dumps(config)
        native = gateway['http'][0]['auth']['native']
        native['address'] = f'workload-tap.{namespace}.svc:8703'
        native['tls']['server_name'] = f'workload-tap.{namespace}.svc'
        for item in environments['hangang']:
            if item['name'] == 'FIXTURE_KEY':
                item['valueFrom']['secretKeyRef']['key'] = 'tap-caller'
        config_map['data']['hangang.json'] = json.dumps(gateway)
        metadata = {'name': 'workload-tap', 'namespace': namespace}
        container = {'name': 'workload-tap', 'image': self.args.workload_tap_image,
            'imagePullPolicy': 'Never', 'command': ['/workload-replay-tap'], 'args': ['/config/workload-tap.json'],
            'env': [env('OWNED_TAP_CALLER', 'tap-caller'), env('OWNED_RECEIPT_CALLER', 'caller'),
                    env('OWNED_PUM_CALLER', 'pum-decision')],
            'securityContext': {'readOnlyRootFilesystem': True, 'allowPrivilegeEscalation': False, 'capabilities': {'drop': ['ALL']}},
            'resources': {'requests': {'cpu': '50m', 'memory': '32Mi'}, 'limits': {'cpu': '1', 'memory': '128Mi'}},
            'readinessProbe': {'tcpSocket': {'port': 8703}, 'periodSeconds': 2},
            'volumeMounts': [{'name': 'config', 'mountPath': '/config', 'readOnly': True}, {'name': 'tls', 'mountPath': '/tls', 'readOnly': True}]}
        items.extend([{'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': metadata,
            'spec': {'replicas': 1, 'strategy': {'type': 'Recreate'}, 'selector': {'matchLabels': {'app': 'workload-tap'}},
                'template': {'metadata': {'labels': {'app': 'workload-tap'}}, 'spec': {
                    'automountServiceAccountToken': False, 'securityContext': {'runAsNonRoot': True,
                    'runAsUser': 65532, 'runAsGroup': 65532, 'fsGroup': 65532, 'seccompProfile': {'type': 'RuntimeDefault'}},
                    'containers': [container], 'volumes': [{'name': 'config', 'configMap': {'name': 'world-config'}},
                        {'name': 'tls', 'secret': {'secretName': 'world-tap-tls', 'defaultMode': 416}}]}}}},
            {'apiVersion': 'v1', 'kind': 'Service', 'metadata': metadata,
                'spec': {'selector': {'app': 'workload-tap'}, 'ports': [{'port': 8703, 'targetPort': 8703}]}}])
        for item in items:
            if item['kind'] == 'Secret' and item['metadata']['name'] == 'world-credentials':
                item['stringData'] = self.tokens

    def replay_facts(self):
        raw = self.kube('-n', self.namespace, 'logs', 'deployment/workload-tap').decode()
        facts = []
        for line in raw.splitlines():
            value = json.loads(line)
            if value.get('event') != 'workload_pair_replay':
                raise AssertionError('unexpected tap evidence event')
            if type(value.get('passed')) is not bool or type(value.get('elapsed_ms')) is not int or value['elapsed_ms'] < 0:
                raise AssertionError('invalid safe tap counters')
            # Copy only allowlisted scalar metadata, never raw logging payloads.
            facts.append({key: value[key] for key in ['event', 'passed', 'replay_status',
                'auth_and_permit_owner_checks', 'original_first_reply_returned_unchanged', 'elapsed_ms'] if key in value})
        return facts

    def check_replay_increment(self, before):
        facts = self.replay_facts()
        added = facts[len(before):]
        if len(added) != 1 or added[0].get('passed') is not True or added[0].get('replay_status') != 'Unavailable' or added[0].get('auth_and_permit_owner_checks') != 'before_and_after_replay' or added[0].get('original_first_reply_returned_unchanged') is not True:
            raise AssertionError('actual owned pair replay qualification missing or failed')
        print('PASS: actual pair replay before first reply; native auth/permit owners current before/after; backend exactly once; flattened refusal not SQL-row-specific', flush=True)
        if self.args.evidence_dir:
            (self.args.evidence_dir/'workload-pair-replay.json').write_text(json.dumps(added, indent=2)+'\n')

    def check_rbac(self):
        checks = [
            ('workload-reviewer', 'authentication.k8s.io', 'tokenreviews', 'create', None, None, True),
            ('workload-reviewer', '', 'serviceaccounts', 'get', 'workload-client', None, True),
            ('workload-reviewer', '', 'pods', 'get', 'workload-bound', None, True),
            ('workload-reviewer', '', 'serviceaccounts', 'get', 'workload-reviewer', None, False),
            ('workload-reviewer', '', 'pods', 'get', 'unrelated-owned-negative', None, False),
            ('workload-reviewer', '', 'pods', 'list', None, None, False),
            ('workload-reviewer', '', 'pods', 'watch', None, None, False),
            ('workload-reviewer', '', 'pods', 'delete', 'workload-bound', None, False),
            ('workload-reviewer', '', 'secrets', 'list', None, None, False),
            ('workload-reviewer', '', 'serviceaccounts', 'create', 'workload-client', 'token', False),
            ('workload-client', '', 'serviceaccounts', 'create', 'workload-reviewer', 'token', False),
            ('workload-client', '', 'serviceaccounts', 'create', 'workload-client', 'token', False),
            ('workload-client', '', 'serviceaccounts', 'get', 'workload-client', None, False),
            ('workload-client', '', 'pods', 'get', 'workload-bound', None, False),
            ('workload-client', 'authentication.k8s.io', 'tokenreviews', 'create', None, None, False),
            ('workload-client', '', 'secrets', 'list', None, None, False),
        ]
        for account, group, resource, verb, name, subresource, allowed in checks:
            attributes = {'group': group, 'resource': resource, 'verb': verb}
            if resource != 'tokenreviews': attributes['namespace'] = self.namespace
            if name is not None: attributes['name'] = name
            if subresource is not None: attributes['subresource'] = subresource
            review = {'apiVersion': 'authorization.k8s.io/v1', 'kind': 'SelfSubjectAccessReview', 'spec': {'resourceAttributes': attributes}}
            result = json.loads(self.kube('create', '--raw', '/apis/authorization.k8s.io/v1/selfsubjectaccessreviews',
                '--as', f'system:serviceaccount:{self.namespace}:{account}', '-f', '-', body=json.dumps(review).encode()))
            if result.get('status', {}).get('allowed') is not allowed:
                raise AssertionError('owned reviewer/client RBAC exceeds or misses declared scope')

    def restored_http(self, request, seconds=30):
        """Only restoration probes may retry503. Every call keeps its own budget."""
        deadline = time.monotonic() + seconds
        refusals = 0
        while time.monotonic() < deadline:
            replay_before = self.replay_facts()
            code, body = request()
            # The actual request helper independently counts before/after EVERY
            # response. Recheck its safe result so future refactors cannot skip it.
            delta = getattr(request, 'last', {}).get('backend_delta')
            if code == 200:
                if delta != 1:
                    raise AssertionError('restored success did not reach backend exactly once')
                self.check_replay_increment(replay_before)
                print('PASS: bounded restored HTTP200 after ' + str(refusals) + ' HTTP503/backend0 observations; perrequest budgets unchanged', flush=True)
                return code, body
            if code != 503 or delta != 0:
                raise AssertionError('restoration allows only HTTP503/backend0 before HTTP200/backend1')
            refusals += 1
            time.sleep(min(.1, max(0, deadline - time.monotonic())))
        raise AssertionError('owned HTTP restoration deadline')

    def api_authenticates(self, credential):
        result = json.loads(self.kube('create', '--raw', '/apis/authentication.k8s.io/v1/tokenreviews', '-f', '-', body=json.dumps({
            'apiVersion': 'authentication.k8s.io/v1', 'kind': 'TokenReview',
            'spec': {'token': credential.removeprefix('k8s:'), 'audiences': ['orders-workload']}}).encode()))
        authenticated = result.get('status', {}).get('authenticated', False)
        if type(authenticated) is not bool:
            raise AssertionError('TokenReview boolean status required')
        return authenticated

    def probe(self, root, config, credential, expected=True, startup_refusal=False):
        path = root / 'workload-probe.json'
        path.write_text(json.dumps(config)); path.chmod(0o600)
        result = subprocess.run([str(self.args.receipt_client.resolve()), str(path)], input='allow\n' if expected else 'deny\n',
            env=dict(os.environ, OWNED_RECEIPT_CALLER=self.tokens['caller'], OWNED_RECEIPT_CREDENTIAL=credential),
            text=True, capture_output=True, timeout=10)
        # Errors are intentionally generic: do not include provider/probe stderr/token payloads.
        if startup_refusal:
            facts = json.loads(result.stdout)
            if result.returncode != 1 or facts.get('probe_error') != 'policy':
                raise AssertionError('fixed probe startup trust mismatch was not refused')
            return {'startup_trust_refused': True}
        if result.returncode != 0:
            raise AssertionError('public Workload SDK probe failed')
        facts = json.loads(result.stdout)
        if facts.get('contract') != 'hopae-workload-observed-sdk-v1' or facts.get('allowed') is not expected:
            raise AssertionError('public Workload SDK contract mismatch')
        if expected and (facts.get('kind') != 3 or facts.get('aal') != 0
                or not all(facts.get(x) is True for x in ['issued', 'independently_observed', 'refreshed'])):
            raise AssertionError('public Workload SDK native evidence missing')
        return facts

    def held_line(self, process, command):
        if process.poll() is not None:
            raise AssertionError('held public probe exited')
        process.stdin.write(command+'\n'); process.stdin.flush()
        ready, _, _ = select.select([process.stdout], [], [], 10)
        if not ready:
            raise AssertionError('held public probe deadline')
        line = process.stdout.readline(16385)
        if len(line) > 16384 or not line.endswith('\n'):
            raise AssertionError('held public probe framing')
        return json.loads(line)

    def begin_held(self, root, config, port):
        held = copy.deepcopy(config)
        held['settings']['address'] = f'localhost:{port}'
        held['settings']['tls']['server_name'] = f'workload-tap.{self.namespace}.svc'
        path = root/'held-workload-probe.json'; path.write_text(json.dumps(held)); path.chmod(0o600)
        process = subprocess.Popen([str(self.args.workload_held_client.resolve()), str(path)],
            env=dict(os.environ, OWNED_RECEIPT_CALLER=self.tokens['tap-caller'], OWNED_RECEIPT_CREDENTIAL=self.primary),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.held_processes.append(process)
        if self.held_line(process, 'hold').get('held') is not True:
            raise AssertionError('held public evidence missing')
        return process

    def finish_held(self, process):
        # Fresh proof is independent; does not replace process-held old context.
        # It confirms the stable tap/real-Hop connection is healthy after restart.
        fresh = self.held_line(process, 'allow')
        if fresh.get('allowed') is not True:
            raise AssertionError('fresh postrestart public SDK connection failed')
        facts = self.held_line(process, 'held-refuse')
        if facts.get('held_refused') is not True:
            raise AssertionError('old held source accepted after replacement')
        print('PASS: held original evidence refused after actual Hop Pod replacement; same public connection fresh proof works; original1s expiry independently explains old refusal', flush=True)
        if self.args.evidence_dir:
            (self.args.evidence_dir/'workload-held-refusal.json').write_text(json.dumps({
                'held_refused': True, 'fresh_connection_verified': True,
                'elapsed_since_before_issue_ms': facts.get('elapsed_since_before_issue_ms'),
                'cause': 'not_attributed; original1s expiry may explain refusal'}, indent=2)+'\n')
        process.stdin.close(); process.wait(timeout=10)
        if process.returncode != 0:
            raise AssertionError('held public probe completion')

    def qualify(self, root, forward, request, api, admin, eventually, receipt_pin):
        # Fail explicitly if the actual configured plugin/admin route is absent;
        # a provided package path alone does not establish live authorization.
        read_profile_owner(api, admin)
        port = forward('hopae', 8703)
        def probe_config(port):
            return {'settings': {'transport': 'grpc', 'address': f'localhost:{port}', 'tls': {
                'server_name': f'hopae.{self.namespace}.svc', 'ca': str(root/'ca.pem'),
                'certificate': str(root/'client.pem'), 'key': str(root/'client.key')}},
                'issuer_ref': 'owned-world', 'key_epoch': 1, 'public_key': receipt_pin,
                'service': 'orders', 'audience': 'orders-api', 'method': 'GET', 'target': '/secure', 'body': '',
                'identity_authority': 'world1', 'source_ppm': 500, 'receiver_ppm': 500,
                'headers': [['x-hopae-contract','1'], ['x-forwarded-host','app.example.test'], ['x-forwarded-proto','https'],
                    ['x-forwarded-port','8443'], ['x-forwarded-for','127.0.0.1'], ['x-original-method','GET'],
                    ['x-original-url','https://app.example.test:8443/secure']]}
        config = probe_config(port)
        facts = self.probe(root, config, self.primary)
        subject = facts['subject_ref']
        if subject != self.patch['derived_expected_subject']:
            raise AssertionError('public verified subject differs from actual owned UID derivation')
        assert request()[0] == 403, 'ungranted verified Workload must not borrow legacy rights'
        def publish(grants, legacy=None):
            code, document, metadata = api(admin, '/v1/pumgye/policy')
            assert code == 200
            document['policy']['services']['orders']['workload_users'] = grants
            document['policy']['services']['orders']['users'] = legacy or {}
            code, _, _ = api(admin, '/v1/pumgye/policy', 'PUT', document, extra={
                'If-Match': f'"{document["revision"]}"', 'x-hangang-config-revision': metadata['x-hangang-config-revision']})
            assert code == 200
        publish({subject: ['reader']})
        replay_before = self.replay_facts()
        code, body = request()
        assert code == 200
        self.check_replay_increment(replay_before)
        headers = {name.lower(): value for name, value in json.loads(body)['headers'].items()}
        assert headers.get('x-forwarded-user') == subject and headers.get('x-hopae-aal') == '0' and headers.get('x-hopae-principal-kind') == 'workload'
        assert request('POST')[0] == 403
        assert request(key=None)[0] != 200
        wrong_audience = self.mint('wrong-workload-audience')
        self.probe(root, config, wrong_audience, False)
        assert request(key=wrong_audience)[0] != 200
        # Tampered UID/issuer cannot acquire trust from payload claims; native API verifies signature.
        raw = self.primary.removeprefix('k8s:')
        parts = raw.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)))
        for field in ['issuer', 'sa_uid', 'pod_uid']:
            changed = copy.deepcopy(payload)
            if field == 'issuer': changed['iss'] = 'https://wrong-issuer.example.test'
            elif field == 'sa_uid': changed['kubernetes.io']['serviceaccount']['uid'] = 'wrong-sa-uid'
            else: changed['kubernetes.io']['pod']['uid'] = 'wrong-pod-uid'
            encoded = base64.urlsafe_b64encode(json.dumps(changed, separators=(',', ':')).encode()).decode().rstrip('=')
            credential = 'k8s:' + '.'.join([parts[0], encoded, parts[2]])
            self.tokens['tampered-' + field] = credential
            self.probe(root, config, credential, False)
            assert request(key=credential)[0] != 200
        wrong = dict(config, identity_authority='wrong-owner')
        self.probe(root, wrong, self.primary, False, startup_refusal=True)
        # A locally fixed cluster realm is part of native identity association,
        # not a Kubernetes-attested claim. A deliberately different configured
        # realm yields a different verified subject and must lose the old grant.
        # Durable native profiles own this setting after initial bootstrap.
        # Publication/readback completes before the public SDK is invoked;
        # restoration also verifies the acknowledged current owner revision.
        with temporary_workload_realm(api, admin, service='orders', host='app.example.test',
                original_realm=self.args.workload_cluster_id, changed_realm='wrong-owned-cluster'):
            verified = self.probe(root, config, self.primary)
            assert verified['subject_ref'] != subject
            assert request()[0] == 403
        verified = self.probe(root, config, self.primary)
        assert verified['subject_ref'] == subject
        self.restored_http(request)
        publish({}, {subject: ['reader']})
        assert request()[0] == 403, 'Workload borrowed users grant'
        publish({subject: ['reader']})
        assert request()[0] == 200
        # Hold the original proof through an actual OS Pod replacement.
        held = self.begin_held(root, config, forward('workload-tap', 8703))
        # Actual OS Pod restart; every request must obtain fresh proof/permit/output.
        self.kube('-n', self.namespace, 'rollout', 'restart', 'deployment/hopae')
        self.kube('-n', self.namespace, 'rollout', 'status', 'deployment/hopae', '--timeout=120s', timeout=135)
        config = probe_config(forward('hopae', 8703))
        self.probe(root, config, self.primary)
        self.restored_http(request)
        self.finish_held(held)
        # Minimal reviewer role withdrawal, then explicit newly owned restoration.
        path, uid = self.globals[-1]
        delete_owned(self.kube, path, uid)
        self.globals.pop()
        time.sleep(1.1)
        self.probe(root, config, self.primary, False)
        assert request()[0] != 200
        binding = next(item for item in bootstrap(self.namespace, self.args.workload_utility_image) if item['kind'] == 'ClusterRoleBinding')
        self.create(binding)
        # Provider circuit can remain open; explicit native process replacement restores fresh owner.
        self.kube('-n', self.namespace, 'rollout', 'restart', 'deployment/hopae')
        self.kube('-n', self.namespace, 'rollout', 'status', 'deployment/hopae', '--timeout=120s', timeout=135)
        config = probe_config(forward('hopae', 8703))
        self.probe(root, config, self.primary)
        self.restored_http(request)
        # API deletion propagation is measured separately from Hop's original1s source record.
        pod = json.loads(self.kube('-n', self.namespace, 'get', 'pod', 'workload-bound', '-o', 'json'))
        delete_owned(self.kube, f'/api/v1/namespaces/{self.namespace}/pods/workload-bound', pod['metadata']['uid'])
        begun = time.monotonic()
        eventually(lambda: not self.api_authenticates(self.primary), seconds=90)
        self.probe(root, config, self.primary, False)
        time.sleep(1.1)
        assert request()[0] != 200
        pod_withdraw_ms = round((time.monotonic()-begun)*1000)
        # Recreate same Pod name: actual new UID changes native subject. Old grant
        # must not authorize it; only independently verified new subject is published.
        self.kube('-n', self.namespace, 'wait', '--for=delete', 'pod/workload-bound', '--timeout=60s')
        new_pod = self.create(next(x for x in bootstrap(self.namespace, self.args.workload_utility_image) if x['kind'] == 'Pod'))
        self.kube('-n', self.namespace, 'wait', '--for=condition=Ready', 'pod/workload-bound', '--timeout=120s', timeout=135)
        fresh = self.mint('orders-workload', uid=new_pod['metadata']['uid'])
        sa = json.loads(self.kube('-n', self.namespace, 'get', 'serviceaccount', 'workload-client', '-o', 'json'))
        expected = configuration_patches(namespace=self.namespace, api_origin='https://kubernetes.default.svc', issuer=self.args.workload_issuer,
            cluster=self.args.workload_cluster_id, audience='orders-workload', sa_uid=sa['metadata']['uid'], pod_uid=new_pod['metadata']['uid'])['derived_expected_subject']
        # A denial circuit may be latched; a fresh native process is the explicit recovery.
        self.kube('-n', self.namespace, 'rollout', 'restart', 'deployment/hopae')
        self.kube('-n', self.namespace, 'rollout', 'status', 'deployment/hopae', '--timeout=120s', timeout=135)
        config = probe_config(forward('hopae', 8703))
        verified = self.probe(root, config, fresh)
        assert verified['subject_ref'] == expected and expected != subject
        assert request(key=fresh)[0] == 403
        publish({expected: ['reader']})
        assert request(key=fresh)[0] == 200
        delete_owned(self.kube, f'/api/v1/namespaces/{self.namespace}/serviceaccounts/workload-client', sa['metadata']['uid'])
        begun = time.monotonic()
        eventually(lambda: not self.api_authenticates(fresh), seconds=90)
        self.probe(root, config, fresh, False)
        time.sleep(1.1)
        assert request(key=fresh)[0] != 200
        print('PASS: Workload actual public SDK verified subject→typed Pum grant→contract3→backend; audience/claims/owner/map denial, reviewer role withdrawal, Hop restart, Pod UID replacement/explicit grant and SA withdrawal; pod_API_withdraw_ms=' + str(pod_withdraw_ms) + ' sa_API_withdraw_ms=' + str(round((time.monotonic()-begun)*1000)), flush=True)
        print('LIMIT: no Human or Workload browser/admin UX; restart-held refusal may also be original1s expiry; replay status is flattened; API propagation is distinct from original1s source evidence.', flush=True)

    def cleanup(self):
        # Attempt every owned cleanup even if one UID conflict/transport fails.
        # Replacement objects are always protected by API UID preconditions.
        failures = []
        for process in self.held_processes:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
        for path, uid in reversed(self.globals):
            try: delete_owned(self.kube, path, uid)
            except (RuntimeError, subprocess.TimeoutExpired): failures.append('owned global cleanup refused')
        if self.namespace_uid:
            try:
                delete_owned(self.kube, '/api/v1/namespaces/' + self.namespace, self.namespace_uid)
                self.kube('wait', '--for=delete', 'namespace/' + self.namespace, '--timeout=120s', timeout=135)
            except (RuntimeError, subprocess.TimeoutExpired): failures.append('owned namespace cleanup refused')
        if failures:
            raise RuntimeError('; '.join(failures))
        print('Owned Workload namespace and exact created global UIDs cleaned', flush=True)
