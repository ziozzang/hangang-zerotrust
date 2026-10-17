#!/usr/bin/env python3
"""Generate charts/hangang-world/values.schema.json (strict, additionalProperties: false).

Run after changing values.yaml; tools/test_helm_charts.py checks the file is current.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'charts/hangang-world/values.schema.json'

DNS_LABEL = '^[a-z0-9]([-a-z0-9]{0,61}[a-z0-9])?$'
DNS_SUBDOMAIN = '^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$'
SECRET_NAME = {'type': 'string', 'maxLength': 253, 'pattern': '^$|' + DNS_SUBDOMAIN}
KEY = {'type': 'string', 'minLength': 1, 'maxLength': 253, 'pattern': '^[-._a-zA-Z0-9]+$'}
DURATION = {'type': 'string', 'pattern': '^([0-9]+(\\.[0-9]+)?(ns|us|µs|ms|s|m|h))+$'}
CIDR = {'type': 'string', 'maxLength': 49, 'pattern': '^[0-9a-fA-F:.]+/[0-9]{1,3}$'}
QUANTITY = {'type': ['string', 'number'], 'pattern': '^[+-]?([0-9.]+)([eEinumkKMGTP]*[-+]?[0-9]*)$'}


def obj(properties, required=(), extra=False, **more):
    schema = {'type': 'object', 'additionalProperties': extra, 'properties': properties}
    if required:
        schema['required'] = list(required)
    schema.update(more)
    return schema


def free_object(description):
    return {'type': 'object', 'description': description}


def string_map():
    return {'type': 'object', 'additionalProperties': {'type': 'string', 'maxLength': 4096}, 'maxProperties': 64}


def image(name):
    return obj({
        'repository': {'type': 'string', 'minLength': 1, 'maxLength': 255, 'pattern': '^[a-z0-9]([-a-z0-9._/:]*[a-z0-9])?$'},
        'tag': {'type': 'string', 'maxLength': 128, 'pattern': '^[A-Za-z0-9_][A-Za-z0-9_.-]*$',
                'description': 'Informational; the digest decides what runs.'},
        'digest': {'type': 'string', 'pattern': '^$|^sha256:[a-f0-9]{64}$',
                   'description': f'Required image digest for {name} (sha256:<64 hex>). Tags alone are refused.'},
        'pullPolicy': {'enum': ['IfNotPresent', 'Always', 'Never']},
    }, required=['repository'])


RESOURCES = obj({
    'requests': obj({'cpu': QUANTITY, 'memory': QUANTITY, 'ephemeral-storage': QUANTITY}),
    'limits': obj({'cpu': QUANTITY, 'memory': QUANTITY, 'ephemeral-storage': QUANTITY}),
}, required=['requests', 'limits'])
PDB = obj({'enabled': {'type': 'boolean'}, 'maxUnavailable': {'type': 'integer', 'minimum': 1}})
PERSISTENCE = obj({
    'size': {'type': 'string', 'pattern': '^[0-9]+(Ki|Mi|Gi|Ti)$'},
    'storageClassName': {'type': 'string', 'maxLength': 253},
    'existingClaim': SECRET_NAME,
})
SCHEDULING = {
    'podAnnotations': string_map(),
    'podLabels': string_map(),
    'nodeSelector': string_map(),
    'tolerations': {'type': 'array', 'maxItems': 32, 'items': {'type': 'object'}},
    'affinity': {'type': 'object'},
    'priorityClassName': {'type': 'string', 'maxLength': 253},
}


def component(name, extra, required=(), replicas_max=None):
    replicas = {'type': 'integer', 'minimum': 1, 'maximum': 16}
    if replicas_max:
        replicas['maximum'] = replicas_max
        replicas['description'] = f'{name} is a single writer in this release; replicas > 1 needs a shared backend it does not have yet.'
    properties = {'enabled': {'type': 'boolean'}, 'replicas': replicas, 'image': image(name),
                  'resources': RESOURCES, **SCHEDULING, **extra}
    schema = obj(properties, required=['enabled', 'replicas', 'image', 'resources', *required])
    # An enabled component must pin its image by digest.
    schema['if'] = {'properties': {'enabled': {'const': True}}}
    schema['then'] = {'properties': {'image': {'required': ['digest'], 'properties': {'digest': {'minLength': 71}}}}}
    return schema


def storage(backends):
    return obj({'backend': {'enum': backends}}, required=['backend'])


schema = obj({
    'global': obj({
        'trustDomain': {'type': 'string', 'minLength': 1, 'maxLength': 253, 'pattern': DNS_SUBDOMAIN},
        'imagePullSecrets': {'type': 'array', 'maxItems': 16, 'items': obj({'name': {'type': 'string', 'pattern': DNS_SUBDOMAIN}}, required=['name'])},
        'ha': obj({
            'backend': {'enum': ['none', 'postgresql']},
            'postgresql': obj({'existingSecret': SECRET_NAME, 'urlKey': KEY,
                               'caSecret': obj({'name': SECRET_NAME, 'key': KEY}, required=['name', 'key'])}),
        }, required=['backend']),
    }, required=['trustDomain', 'ha']),
    'credentials': obj({
        'existingSecret': {'type': 'string', 'minLength': 1, 'maxLength': 253, 'pattern': DNS_SUBDOMAIN,
                           'description': 'Pre-created Secret with the shared API credentials. Inline secret values are not accepted.'},
        'keys': obj({k: KEY for k in ['hangangAdminToken', 'hopaeGatewayKey', 'guardCollectorToken', 'guardAdminToken', 'pumgyeDecisionToken', 'pumgyeAdminToken', 'pumgyeMetricsToken', 'guardMetricsToken']},
                    required=['hangangAdminToken', 'hopaeGatewayKey', 'guardCollectorToken', 'guardAdminToken', 'pumgyeDecisionToken', 'pumgyeAdminToken']),
    }, required=['existingSecret', 'keys']),
    'tls': obj({
        'mode': {'enum': ['certManager', 'existingSecrets']},
        'certManager': obj({
            'issuerRef': obj({'name': {'type': 'string', 'maxLength': 253, 'pattern': '^$|' + DNS_SUBDOMAIN},
                              'kind': {'enum': ['Issuer', 'ClusterIssuer']},
                              'group': {'type': 'string', 'maxLength': 253, 'pattern': DNS_SUBDOMAIN}}, required=['name', 'kind', 'group']),
            'duration': DURATION, 'renewBefore': DURATION, 'caDuration': DURATION,
            'privateKey': obj({'algorithm': {'enum': ['ECDSA', 'Ed25519', 'RSA']}, 'size': {'type': 'integer', 'enum': [256, 384, 2048, 3072, 4096]}}, required=['algorithm']),
        }),
        'existingSecrets': obj({c: SECRET_NAME for c in ['hangang', 'hopae', 'pumgye', 'sumunjang', 'hopaeAdmin']}),
    }, required=['mode']),
    'operatorAssurance': obj({
        'seedSecret': obj({'name': SECRET_NAME, 'key': KEY}, required=['name', 'key']),
        'keyId': {'type': 'string', 'pattern': '^$|^[A-Za-z0-9._-]{1,64}$'},
        'publicKey': {'type': 'string', 'pattern': '^$|^[A-Za-z0-9+/]{43}=$', 'description': 'Base64 Ed25519 public key (not secret).'},
        'nextKey': obj({'keyId': {'type': 'string', 'pattern': '^$|^[A-Za-z0-9._-]{1,64}$'},
                        'publicKey': {'type': 'string', 'pattern': '^$|^[A-Za-z0-9+/]{43}=$'}}),
    }),
    'networkPolicy': obj({
        'enabled': {'type': 'boolean'},
        'publicFrom': {'type': 'array', 'maxItems': 64, 'items': {'type': 'object'}},
        'metricsFrom': {'type': 'array', 'maxItems': 64, 'items': {'type': 'object'}},
    }, required=['enabled']),
    'monitoring': obj({
        'serviceMonitor': obj({
            'enabled': {'type': 'boolean'}, 'interval': DURATION, 'scrapeTimeout': DURATION, 'labels': string_map(),
            'clientCertificate': obj({'existingSecret': SECRET_NAME})}),
        'prometheusRule': obj({
            'enabled': {'type': 'boolean'}, 'labels': string_map(),
            'certificateExpiryDays': {'type': 'integer', 'minimum': 1, 'maximum': 365},
            'certManagerExpiry': {'type': 'boolean'},
            'checkpointAgeSeconds': {'type': 'integer', 'minimum': 1, 'maximum': 86400},
            'projectionStalenessSeconds': {'type': 'integer', 'minimum': 0, 'maximum': 604800},
            'decisionUnavailableRatio': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 1}}),
    }),
    'tests': obj({'enabled': {'type': 'boolean'}, 'image': obj({
        'repository': {'type': 'string', 'minLength': 1, 'maxLength': 255},
        'tag': {'type': 'string', 'maxLength': 128},
        'digest': {'type': 'string', 'pattern': '^$|^sha256:[a-f0-9]{64}$'}})}, required=['enabled']),
    'hangang': component('Hangang', {
        'ingressClass': obj({'name': {'type': 'string', 'minLength': 1, 'maxLength': 253, 'pattern': DNS_SUBDOMAIN},
                             'create': {'type': 'boolean'}, 'default': {'type': 'boolean'}}, required=['name']),
        'watchScope': {'enum': ['Namespace', 'Cluster']},
        'publishAddress': {'type': 'string', 'maxLength': 253, 'pattern': '^$|^[0-9a-fA-F:.]+$|' + DNS_SUBDOMAIN},
        'kubernetesTls': {'type': 'boolean'},
        'staleSeconds': {'type': 'integer', 'minimum': 31, 'maximum': 3600},
        'maxStalenessSeconds': {'type': 'integer', 'minimum': 60, 'maximum': 3600,
                                'description': 'ADR 0022 bounded staleness; at least staleSeconds.'},
        'readiness': {'enum': ['snapshot', 'fresh']},
        'advertisedPort': {'type': ['integer', 'null'], 'minimum': 1, 'maximum': 65535},
        'tlsReloadSeconds': {'type': 'integer', 'minimum': 0, 'maximum': 3600},
        'protection': obj({
            'enabled': {'type': 'boolean'},
            'requireProtection': {'type': 'boolean'},
            'identityProfiles': {'type': 'object', 'minProperties': 1, 'maxProperties': 64,
                                 'propertyNames': {'pattern': DNS_LABEL},
                                 'additionalProperties': obj({
                                     'namespaces': {'type': 'array', 'maxItems': 1024, 'items': {'type': 'string', 'pattern': DNS_LABEL}},
                                     'requestHeaders': {'type': 'array', 'minItems': 1, 'maxItems': 32, 'items': {'type': 'string', 'pattern': '^[a-z0-9-]{1,128}$'}},
                                     'forwardResponse': {'type': 'boolean'}})},
            'pumgyeServices': {'type': 'object', 'maxProperties': 4096,
                               'propertyNames': {'pattern': '^[A-Za-z0-9_.:-]{1,128}$'},
                               'additionalProperties': {'type': 'array', 'maxItems': 1024, 'items': {'type': 'string', 'pattern': DNS_LABEL}}},
        }, required=['enabled', 'requireProtection']),
        'guard': obj({'enabled': {'type': 'boolean'}, 'timeoutMs': {'type': 'integer', 'minimum': 1, 'maximum': 5000}}, required=['enabled']),
        'service': obj({
            'type': {'enum': ['ClusterIP', 'NodePort', 'LoadBalancer']},
            'port': {'type': 'integer', 'minimum': 1, 'maximum': 65535},
            'nodePort': {'type': ['integer', 'null'], 'minimum': 1, 'maximum': 65535},
            'annotations': string_map(),
            'loadBalancerSourceRanges': {'type': 'array', 'maxItems': 64, 'items': CIDR},
        }, required=['type', 'port']),
        'clientAddress': obj({
            'mode': {'enum': ['serviceLocal', 'proxyProtocol', 'hostNetwork', 'none']},
            'proxyProtocolFrom': {'type': 'array', 'maxItems': 64, 'items': CIDR},
        }, required=['mode']),
        'admin': obj({'exposeMetrics': {'type': 'boolean'}}),
        'console': obj({
            'enabled': {'type': 'boolean'},
            'command': {'type': 'string', 'pattern': '^/[A-Za-z0-9._/-]{1,255}$'},
            'plugins': {'type': 'array', 'maxItems': 32, 'items': {'type': 'object'}},
            'sso': obj({
                'enabled': {'type': 'boolean'},
                'publicUrl': {'type': 'string', 'maxLength': 300, 'pattern': '^$|^https://[a-z0-9]([-a-z0-9.]*[a-z0-9])?(:[0-9]{1,5})?/$'},
                'cookie': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{1,64}$'},
                'accounts': {'type': 'object', 'maxProperties': 1024,
                             'propertyNames': {'pattern': '^[A-Za-z0-9_.-]{1,128}$'},
                             'additionalProperties': {'type': 'string', 'minLength': 1, 'maxLength': 128}},
                'operatorPolicy': obj({
                    'enabled': {'type': 'boolean'},
                    'minimumAal': {'type': 'integer', 'minimum': 1, 'maximum': 3},
                    'requireFactor': {'enum': ['webauthn', 'any']},
                    'acceptEnrollmentGrace': {'type': 'boolean'},
                    'sensitiveMaxAgeSeconds': {'type': 'integer', 'minimum': 30, 'maximum': 3600},
                    'stepUpPath': {'type': 'string', 'pattern': '^/[A-Za-z0-9._/-]{0,255}$'}}, required=['enabled']),
            }, required=['enabled']),
            'disableLocalLogin': {'type': 'boolean'},
            'operatorAudit': obj({'persistent': {'type': 'boolean'},
                                  'maxRecords': {'type': 'integer', 'minimum': 100, 'maximum': 1000000},
                                  'retentionDays': {'type': 'integer', 'minimum': 1, 'maximum': 3650}}),
            'auditLog': {'type': 'string', 'maxLength': 255, 'pattern': '^$|^/var/log/hangang-console/[A-Za-z0-9._-]{1,128}$'},
            'resources': RESOURCES,
        }, required=['enabled']),
        'pdb': PDB,
        'topologySpreadConstraints': {'type': 'array', 'maxItems': 8, 'items': {'type': 'object'}},
        'terminationGracePeriodSeconds': {'type': 'integer', 'minimum': 15, 'maximum': 600},
    }, required=['ingressClass', 'watchScope', 'protection', 'guard', 'service', 'clientAddress']),
    'hopae': component('Hopae', {
        'storage': obj({
            'backend': {'enum': ['sqlite', 'postgresql']},
            'postgresql': obj({'poolSize': {'type': 'integer', 'minimum': 1, 'maximum': 128},
                               'connectTimeoutMs': {'type': 'integer', 'minimum': 100, 'maximum': 60000},
                               'statementTimeoutMs': {'type': 'integer', 'minimum': 10, 'maximum': 600000}}),
            'migration': obj({'enabled': {'type': 'boolean'}, 'fromClaim': SECRET_NAME,
                              'timeoutSeconds': {'type': 'integer', 'minimum': 60, 'maximum': 86400}}),
        }, required=['backend']),
        'persistence': PERSISTENCE,
        'authentication': obj({'source': {'enum': ['config', 'store']},
                               'reloadIntervalMs': {'type': ['integer', 'null'], 'minimum': 0, 'maximum': 60000,
                                                    'not': {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 200}}},
                              required=['source']),
        'tlsReloadSeconds': {'type': ['integer', 'null'], 'minimum': 0, 'maximum': 3600},
        'preStopSleepSeconds': {'type': 'integer', 'minimum': 0, 'maximum': 120},
        'consoleOperators': obj({
            'enabled': {'type': 'boolean'},
            'appId': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{1,64}$', 'not': {'const': 'default'}},
            'requireAal': {'enum': [2, 3]},
            'requireFactor': {'enum': ['webauthn', 'any']},
            'stepUpPath': {'type': 'string', 'pattern': '^/[A-Za-z0-9._/-]{0,255}$'},
            'stepUpMaxAgeSecs': {'type': 'integer', 'minimum': 30, 'maximum': 3600},
            'enrollmentGraceUntil': {'type': ['integer', 'null'], 'minimum': 0},
        }, required=['enabled']),
        'metrics': obj({'enabled': {'type': 'boolean'}, 'tokenSecret': obj({'name': SECRET_NAME, 'key': KEY}, required=['name', 'key'])}, required=['enabled']),
        'portalIngress': obj({'enabled': {'type': 'boolean'},
                              'host': {'type': 'string', 'maxLength': 253, 'pattern': '^$|' + DNS_SUBDOMAIN},
                              'tlsSecret': SECRET_NAME,
                              'reason': {'type': 'string', 'minLength': 8, 'maxLength': 256}}, required=['enabled']),
        'config': obj({}, extra=True, description='Hopae configuration minus the chart-owned listen, state_dir, store, gateway, authentication, reload and console_operators.',
                      **{'not': {'anyOf': [{'required': [k]} for k in ['listen', 'state_dir', 'store', 'gateway', 'authentication', 'reload', 'console_operators']]}}),
        'extraSecretEnv': {'type': 'array', 'maxItems': 64, 'items': obj({
            'name': {'type': 'string', 'pattern': '^[A-Z_][A-Z0-9_]{0,127}$'},
            'secretName': {'type': 'string', 'pattern': DNS_SUBDOMAIN, 'maxLength': 253},
            'key': KEY}, required=['name', 'secretName', 'key'])},
        'pdb': PDB,
        'admin': obj({
            'enabled': {'type': 'boolean'},
            'publicUrl': {'type': 'string', 'maxLength': 300, 'pattern': '^$|^https://[a-z0-9]([-a-z0-9.]*[a-z0-9])?(:[0-9]{1,5})?$'},
            'untrustedPeers': {'enum': ['as_client', 'refuse']},
            'serviceAudience': {'type': 'string', 'maxLength': 256, 'pattern': '^[\\x21-\\x7e]*$'},
            'delegation': obj({'enabled': {'type': 'boolean'}, 'keySecret': obj({'name': SECRET_NAME, 'key': KEY}, required=['name', 'key'])}, required=['enabled']),
        }, required=['enabled']),
    }, required=['storage', 'persistence', 'config', 'authentication']),
    'pumgye': component('Pumgye', {
        'storage': storage(['sqlite']),
        'persistence': PERSISTENCE,
        'bootstrapPolicy': free_object('Pumgye bootstrap document, used only when the database is empty.'),
        'hopaeOwner': obj({
            'enabled': {'type': 'boolean'},
            'tokenSecret': obj({'name': SECRET_NAME, 'key': KEY}, required=['name', 'key']),
            'projection': {'anyOf': [{'type': 'null'}, obj({
                'audience': {'type': 'string', 'minLength': 1, 'maxLength': 256},
                'keys': {'type': 'array', 'minItems': 1, 'maxItems': 16, 'items': obj({
                    'issuer_ref': {'type': 'string', 'minLength': 1, 'maxLength': 128},
                    'key_epoch': {'type': 'integer', 'minimum': 0},
                    'public_key': {'type': 'string', 'pattern': '^[A-Za-z0-9+/]{43}=$'}}, required=['issuer_ref', 'key_epoch', 'public_key'])},
                'max_age_secs': {'type': 'integer', 'minimum': 1, 'maximum': 86400},
                'max_staleness_secs': {'type': 'integer', 'minimum': 1, 'maximum': 604800},
                'poll_interval_secs': {'type': 'integer', 'minimum': 1, 'maximum': 3600}}, required=['audience', 'keys'])]},
            'lifecycle': {'anyOf': [{'type': 'null'}, obj({
                'poll_interval_secs': {'type': 'integer', 'minimum': 1, 'maximum': 3600},
                'reconcile_interval_secs': {'type': 'integer', 'minimum': 1, 'maximum': 604800}})]},
        }, required=['enabled']),
        'tlsReloadSeconds': {'type': 'integer', 'minimum': 1, 'maximum': 3600},
    }, required=['storage', 'persistence', 'bootstrapPolicy'], replicas_max=1),
    'sumunjang': component('Sumunjang', {
        'storage': storage(['sqlite']),
        'persistence': PERSISTENCE,
        'bootstrapPolicy': free_object('Sumunjang bootstrap policy, used only when the database is empty.'),
        'threads': {'type': 'integer', 'minimum': 1, 'maximum': 64},
        'tlsReloadSeconds': {'type': 'integer', 'minimum': 0, 'maximum': 3600},
    }, required=['storage', 'persistence', 'bootstrapPolicy'], replicas_max=1),
}, required=['global', 'credentials', 'tls', 'networkPolicy', 'hangang', 'hopae', 'pumgye', 'sumunjang'])
schema['$schema'] = 'https://json-schema.org/draft-07/schema#'
schema['title'] = 'hangang-world values'
OUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {OUT.relative_to(ROOT)}')
