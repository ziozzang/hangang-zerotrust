#!/usr/bin/env python3
"""Pure preparation helpers; no Kubernetes calls, tokens or execution capability."""
import hashlib
import re
import struct
from urllib.parse import urlsplit


SCOPE = {'service': 'orders', 'audience': 'orders-api'}


def validate_mode(*, workload, composition, observed, credential_projection,
                  native_resource, resource_catalog, receipt_client):
    if not workload:
        return
    if composition:
        raise ValueError('--workload cannot be combined with --composition (All or Any)')
    if not all([observed, credential_projection, native_resource, resource_catalog, receipt_client]):
        raise ValueError('--workload requires --observed --credential-projection --native-resource --resource-catalog --receipt-client')


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', value):
        raise ValueError('bounded DNS label required')
    return value


def _https(value, origin=False):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or len(value) > 256
            or (origin and parsed.path not in ['', '/'])):
        raise ValueError('fixed verified HTTPS reference required')
    return value


def stable_subject(issuer, cluster, namespace, service_account, sa_uid, pod, pod_uid):
    """Same native Workload hash domains; wire kind3 is NOT the hash byte2."""
    for value in [namespace, service_account, pod]:
        _name(value)
    for value in [sa_uid, pod_uid, cluster]:
        if not isinstance(value, str) or not 1 <= len(value) <= 128 or not re.fullmatch(r'[A-Za-z0-9_.:-]+', value):
            raise ValueError('bounded source identity required')
    _https(issuer)
    inner = hashlib.sha256(b'hopae:kubernetes:pod-subject:v1\0')
    for value in [namespace, service_account, sa_uid, pod, pod_uid]:
        encoded = value.encode()
        inner.update(struct.pack('!I', len(encoded)))
        inner.update(encoded)
    native = 'w_' + inner.hexdigest()
    outer = hashlib.sha256(bytes([2]))
    for value in [issuer, cluster, native]:
        encoded = value.encode()
        outer.update(struct.pack('!Q', len(encoded)))
        outer.update(encoded)
    return 's_' + outer.hexdigest()[:48]


def token_request(namespace, service_account, pod, pod_uid, audience):
    _name(namespace); _name(service_account); _name(pod)
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,128}', pod_uid):
        raise ValueError('actual bound Pod UID required')
    if not audience or len(audience) > 256 or any(ord(c) < 33 for c in audience):
        raise ValueError('explicit bounded audience required')
    return {'path': f'/api/v1/namespaces/{namespace}/serviceaccounts/{service_account}/token',
            'body': {'apiVersion': 'authentication.k8s.io/v1', 'kind': 'TokenRequest',
                     'spec': {'audiences': [audience], 'expirationSeconds': 600,
                              'boundObjectRef': {'apiVersion': 'v1', 'kind': 'Pod', 'name': pod, 'uid': pod_uid}}}}


def bootstrap(namespace, utility_image):
    _name(namespace)
    if not namespace.startswith('owned-world-'):
        raise ValueError('exclusive owned namespace required')
    if not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', utility_image):
        raise ValueError('exact utility image digest required')
    def obj(kind, name, api='v1', **fields):
        metadata = {'name': name, 'labels': {'app.kubernetes.io/part-of': 'owned-hangang-workload'}}
        if kind not in ['ClusterRole', 'ClusterRoleBinding']:
            metadata['namespace'] = namespace
        return {'apiVersion': api, 'kind': kind, 'metadata': metadata, **fields}
    reviewer_role = namespace + '-tokenreview'
    return [
        obj('ServiceAccount', 'workload-reviewer', automountServiceAccountToken=False),
        obj('ServiceAccount', 'workload-client', automountServiceAccountToken=False),
        obj('Pod', 'workload-bound', spec={'serviceAccountName': 'workload-client',
            'automountServiceAccountToken': False, 'restartPolicy': 'Never',
            'containers': [{'name': 'hold', 'image': utility_image,
                'command': ['node', '-e', 'setInterval(()=>{},60000)'],
                'securityContext': {'allowPrivilegeEscalation': False, 'readOnlyRootFilesystem': True,
                                    'capabilities': {'drop': ['ALL']}},
                'resources': {'requests': {'cpu': '5m', 'memory': '16Mi'},
                              'limits': {'cpu': '100m', 'memory': '64Mi'}}}]}),
        obj('ClusterRole', reviewer_role, 'rbac.authorization.k8s.io/v1', rules=[
            {'apiGroups': ['authentication.k8s.io'], 'resources': ['tokenreviews'], 'verbs': ['create']}]),
        obj('ClusterRoleBinding', reviewer_role, 'rbac.authorization.k8s.io/v1',
            roleRef={'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'ClusterRole', 'name': reviewer_role},
            subjects=[{'kind': 'ServiceAccount', 'name': 'workload-reviewer', 'namespace': namespace}]),
    ]


def configuration_patches(*, namespace, api_origin, issuer, cluster, audience, sa_uid, pod_uid):
    """Only observed source object facts/configuration; never JWT claim-derived authority."""
    _name(namespace); _https(api_origin, origin=True)
    subject = stable_subject(issuer, cluster, namespace, 'workload-client', sa_uid, 'workload-bound', pod_uid)
    token_request(namespace, 'workload-client', 'workload-bound', pod_uid, audience)
    return {
        'qualification_status': 'preparation_only_not_executed',
        'derived_expected_subject': subject,
        'publication_requires_public_sdk_subject_match': True,
        'hop_profile': {'service_id': 'orders', 'host': 'app.example.test', 'ports': [8443],
            'realm': cluster, 'api_keys': [], 'networks': [],
            'kubernetes_tokenreview': {'connection': {'api_origin': api_origin, 'issuer': issuer,
                'cluster_id': cluster, 'audience': audience, 'namespaces': [namespace], 'timeout_ms': 500},
                'ca_pem_env': 'OWNED_KUBERNETES_CA', 'reviewer_token_env': 'OWNED_REVIEWER_TOKEN', 'token_prefix': 'k8s:'}},
        'hop_workload_receipts': {'scopes': [dict(SCOPE)], 'capacity': 131072},
        'hop_projection_receiver_workload_observed_scopes': [dict(SCOPE)],
        'pum_subject_maps': {'users': {}, 'workload_users': {subject: ['reader']}},
        'root_observed_patch': {'authentication_class': 'workload'},
        'pum_activation': ['--workload-observed-permits', '--workload-authentication-live', '/config/workload-authentication-live.json'],
        'bound_token_request': token_request(namespace, 'workload-client', 'workload-bound', pod_uid, audience),
    }
