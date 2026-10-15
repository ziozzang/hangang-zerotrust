"""Opt-in live Workload orchestration. Imported without network side effects.

Execution requires parent-approved artifacts and an exclusive owned-cluster lease.
Pure tests use fake kube functions; never manufacture native SDK capabilities.
"""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from kubernetes_workload_plan import bootstrap, configuration_patches, token_request

PROBE_SHA256 = 'faa10e924f47db73a2ab4c35da372b64f8bcec97e476dcdb6bc65e9d7d95c65a'
REQUIRED = {'hopae': ['workload_observed_authentication', 'workload_observed_projection_contract3'],
            'pumgye': ['workload_observed_permits', 'typed_workload_users'],
            'hangang': ['workload_observed_dispatch', 'raw_observed_transport_fence'],
            'sumunjang': ['native_network_check']}


def preflight(args):
    """Check local reviewed provenance before even resolving the kube wrapper."""
    if not args.workload:
        return
    if args.browser_probe or args.authenticated_client or args.sumunjang_native_source:
        raise ValueError('Workload runner does not yet support browser/admin UX, legacy authenticated client or combined Sum CRD source qualification')
    for name in ['workload_capabilities', 'workload_utility_image', 'workload_issuer', 'workload_cluster_id', 'workload_reviewer_audience']:
        if not getattr(args, name):
            raise ValueError('--workload requires --' + name.replace('_', '-'))
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

    def check_rbac(self):
        for account, group, resource, verb, allowed in [
                ('workload-reviewer', 'authentication.k8s.io', 'tokenreviews', 'create', True),
                ('workload-reviewer', '', 'secrets', 'list', False),
                ('workload-reviewer', '', 'serviceaccounts', 'create', False),
                ('workload-client', 'authentication.k8s.io', 'tokenreviews', 'create', False),
                ('workload-client', '', 'secrets', 'list', False)]:
            attributes = {'group': group, 'resource': resource, 'verb': verb}
            if resource != 'tokenreviews': attributes['namespace'] = self.namespace
            if resource == 'serviceaccounts': attributes.update(subresource='token', name='workload-client')
            review = {'apiVersion': 'authorization.k8s.io/v1', 'kind': 'SelfSubjectAccessReview', 'spec': {'resourceAttributes': attributes}}
            result = json.loads(self.kube('create', '--raw', '/apis/authorization.k8s.io/v1/selfsubjectaccessreviews',
                '--as', f'system:serviceaccount:{self.namespace}:{account}', '-f', '-', body=json.dumps(review).encode()))
            if result.get('status', {}).get('allowed') is not allowed:
                raise AssertionError('owned reviewer/client RBAC exceeds or misses declared scope')

    def api_authenticates(self, credential):
        result = json.loads(self.kube('create', '--raw', '/apis/authentication.k8s.io/v1/tokenreviews', '-f', '-', body=json.dumps({
            'apiVersion': 'authentication.k8s.io/v1', 'kind': 'TokenReview',
            'spec': {'token': credential.removeprefix('k8s:'), 'audiences': ['orders-workload']}}).encode()))
        authenticated = result.get('status', {}).get('authenticated', False)
        if type(authenticated) is not bool:
            raise AssertionError('TokenReview boolean status required')
        return authenticated

    def probe(self, root, config, credential, expected=True):
        path = root / 'workload-probe.json'
        path.write_text(json.dumps(config)); path.chmod(0o600)
        result = subprocess.run([str(self.args.receipt_client.resolve()), str(path)], input='allow\n' if expected else 'deny\n',
            env=dict(os.environ, OWNED_RECEIPT_CALLER=self.tokens['caller'], OWNED_RECEIPT_CREDENTIAL=credential),
            text=True, capture_output=True, timeout=10)
        # Errors are intentionally generic: do not include provider/probe stderr/token payloads.
        if result.returncode != 0:
            raise AssertionError('public Workload SDK probe failed')
        facts = json.loads(result.stdout)
        if facts.get('contract') != 'hopae-workload-observed-sdk-v1' or facts.get('allowed') is not expected:
            raise AssertionError('public Workload SDK contract mismatch')
        if expected and (facts.get('kind') != 3 or facts.get('aal') != 0
                or not all(facts.get(x) is True for x in ['issued', 'independently_observed', 'refreshed'])):
            raise AssertionError('public Workload SDK native evidence missing')
        return facts

    def qualify(self, root, forward, request, api, admin, eventually, receipt_pin):
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
        code, body = request()
        assert code == 200
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
        self.probe(root, wrong, self.primary, False)
        # A locally fixed cluster realm is part of native identity association,
        # not a Kubernetes-attested claim. A deliberately different configured
        # realm yields a different verified subject and must lose the old grant.
        changed = copy.deepcopy(self.hop)
        profile = changed['authentication_gateway']['profiles'][0]
        profile['realm'] = 'wrong-owned-cluster'
        profile['kubernetes_tokenreview']['connection']['cluster_id'] = 'wrong-owned-cluster'
        for next_hop, expected_status in [(changed, 403), (self.hop, 200)]:
            self.kube('-n', self.namespace, 'patch', 'configmap', 'world-config', '--type=merge', '-p', json.dumps({'data': {'hopae.json': json.dumps(next_hop)}}))
            self.kube('-n', self.namespace, 'rollout', 'restart', 'deployment/hopae')
            self.kube('-n', self.namespace, 'rollout', 'status', 'deployment/hopae', '--timeout=120s', timeout=135)
            config = probe_config(forward('hopae', 8703))
            verified = self.probe(root, config, self.primary)
            assert (verified['subject_ref'] == subject) is (expected_status == 200)
            assert request()[0] == expected_status
        publish({}, {subject: ['reader']})
        assert request()[0] == 403, 'Workload borrowed users grant'
        publish({subject: ['reader']})
        assert request()[0] == 200
        # Actual OS Pod restart; every request must obtain fresh proof/permit/output.
        self.kube('-n', self.namespace, 'rollout', 'restart', 'deployment/hopae')
        self.kube('-n', self.namespace, 'rollout', 'status', 'deployment/hopae', '--timeout=120s', timeout=135)
        config = probe_config(forward('hopae', 8703))
        self.probe(root, config, self.primary)
        eventually(lambda: request()[0] == 200)
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
        eventually(lambda: request()[0] == 200)
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
        print('LIMIT: no Workload browser/admin UX or direct captured-pair replay/restart qualification; API propagation is distinct from original1s source evidence.', flush=True)

    def cleanup(self):
        for path, uid in reversed(self.globals):
            delete_owned(self.kube, path, uid)
        if self.namespace_uid:
            delete_owned(self.kube, '/api/v1/namespaces/' + self.namespace, self.namespace_uid)
            self.kube('wait', '--for=delete', 'namespace/' + self.namespace, '--timeout=120s', timeout=135)
