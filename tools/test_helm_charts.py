#!/usr/bin/env python3
"""Offline render tests for charts/hangang-world and charts/hangang-world-crds.

Needs `helm` (v3) on PATH or HELM=/path/to/helm; skipped otherwise. No cluster is
contacted. Set WORLD_KUBECONFORM=1 (with kubeconform on PATH) to also validate
the rendered objects against the Kubernetes, cert-manager and Prometheus
Operator schemas; that fetches schemas over the network. Set PROMTOOL to a
promtool binary to also parse the PrometheusRule expressions.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / 'charts/hangang-world'
CRDS = ROOT / 'charts/hangang-world-crds'
PROFILES = ['minimal', 'ha', 'byo-certs', 'admin', 'console']
HELM = os.environ.get('HELM') or shutil.which('helm') or str(Path.home() / '.local/bin/helm')
KUBECONFORM = shutil.which('kubeconform') or str(Path.home() / '.local/bin/kubeconform')
PROMTOOL = os.environ.get('PROMTOOL') or shutil.which('promtool') or ''
DIGEST = 'sha256:' + 'e' * 64


def helm(*argv, check=True):
    # Never let helm discover a cluster from the caller's kubeconfig.
    env = dict(os.environ, KUBECONFIG=os.devnull, HELM_KUBECONTEXT='')
    result = subprocess.run([HELM, *argv], capture_output=True, text=True, timeout=120, env=env)
    if check and result.returncode:
        raise AssertionError(result.stderr)
    return result


def render(*overrides, profile='minimal', chart=WORLD, namespace='world'):
    argv = ['template', 'w', str(chart), '-n', namespace]
    if chart == WORLD:
        argv += ['-f', str(WORLD / 'ci' / f'{profile}-values.yaml')]
    for override in overrides:
        argv += ['--set-json' if override.startswith('json:') else '--set', override.removeprefix('json:')]
    return [doc for doc in yaml.safe_load_all(helm(*argv).stdout) if doc]


def refused(*overrides, profile='minimal'):
    argv = ['template', 'w', str(WORLD), '-n', 'world', '-f', str(WORLD / 'ci' / f'{profile}-values.yaml')]
    for override in overrides:
        argv += ['--set-json' if override.startswith('json:') else '--set', override.removeprefix('json:')]
    result = helm(*argv, check=False)
    return result.returncode != 0, result.stderr


def notes(*overrides):
    """Render NOTES.txt offline: `helm install --dry-run` would contact a cluster."""
    with tempfile.TemporaryDirectory() as directory:
        copy = Path(directory) / 'hangang-world'
        shutil.copytree(WORLD, copy)
        source = (copy / 'templates/NOTES.txt').read_text()
        (copy / 'templates/NOTES.txt').unlink()
        (copy / 'templates/_notes.tpl').write_text('{{- define "test.notes" -}}' + source + '{{- end -}}')
        (copy / 'templates/zz-notes.yaml').write_text(
            'apiVersion: v1\nkind: ConfigMap\nmetadata: {name: notes}\ndata:\n  notes: {{ include "test.notes" . | toJson }}\n')
        argv = ['template', 'w', str(copy), '-n', 'world', '-f', str(WORLD / 'ci/minimal-values.yaml'),
                '--show-only', 'templates/zz-notes.yaml']
        for override in overrides:
            argv += ['--set', override]
        return yaml.safe_load(helm(*argv).stdout)['data']['notes']


def by_kind(docs, kind):
    return [doc for doc in docs if doc['kind'] == kind]


def named(docs, kind, suffix):
    matches = [doc for doc in by_kind(docs, kind) if doc['metadata']['name'].endswith(suffix)]
    assert len(matches) == 1, (kind, suffix, [d['metadata']['name'] for d in by_kind(docs, kind)])
    return matches[0]


@unittest.skipUnless(Path(HELM).exists(), 'helm is not installed')
class WorldChart(unittest.TestCase):
    def test_schema_file_is_generated_from_the_builder(self):
        with tempfile.TemporaryDirectory() as directory:
            current = (WORLD / 'values.schema.json').read_text()
            subprocess.run([sys.executable, str(ROOT / 'tools/helm/build_world_schema.py')], check=True, capture_output=True)
            self.assertEqual(current, (WORLD / 'values.schema.json').read_text(), 'run tools/helm/build_world_schema.py')
            del directory

    def test_lint_every_profile_and_the_crd_chart(self):
        for profile in PROFILES:
            helm('lint', '--strict', str(WORLD), '-f', str(WORLD / 'ci' / f'{profile}-values.yaml'))
        helm('lint', '--strict', str(CRDS))

    def test_default_values_refuse_to_install_without_digests_and_credentials(self):
        result = helm('template', 'w', str(WORLD), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('digest', result.stderr)

    def test_pod_hardening_and_digest_pinning(self):
        for profile in PROFILES:
            docs = render(profile=profile)
            pods = [d['spec']['template']['spec'] for d in by_kind(docs, 'Deployment')]
            pods += [d['spec'] for d in by_kind(docs, 'Pod')]
            self.assertTrue(pods)
            for pod in pods:
                security = pod['securityContext']
                self.assertTrue(security['runAsNonRoot'])
                self.assertEqual(security['seccompProfile']['type'], 'RuntimeDefault')
                for container in pod['containers'] + pod.get('initContainers', []):
                    context = container['securityContext']
                    self.assertTrue(context['readOnlyRootFilesystem'], container['name'])
                    self.assertFalse(context['allowPrivilegeEscalation'])
                    self.assertEqual(context['capabilities']['drop'], ['ALL'])
                    self.assertRegex(container['image'], r'@sha256:[a-f0-9]{64}$')
                    self.assertIn('limits', container['resources'])
                    if pod in pods[:-1] or 'readinessProbe' in container:
                        self.assertIn('readinessProbe', container)
            self.assertFalse(by_kind(docs, 'Secret'), 'the chart never renders Secret values')

    def test_minimal_profile_wiring(self):
        docs = render()
        names = {d['metadata']['name'] for d in by_kind(docs, 'Deployment')}
        self.assertEqual(names, {f'w-hangang-world-{c}' for c in ['hangang', 'hopae', 'pumgye', 'sumunjang']})
        gateway = named(docs, 'Deployment', '-hangang')['spec']['template']['spec']
        args = gateway['containers'][0]['args']
        self.assertIn('--kubernetes-protection-config', args)
        self.assertIn('w-hangang-world-sumunjang.world.svc:9082', args)
        self.assertEqual(args[args.index('--guard-failure-mode') + 1], 'deny')
        self.assertEqual(args[args.index('--admin') + 1], '127.0.0.1:9000')
        self.assertEqual(args[args.index('--admin-tls-cert') + 1], '/tls/tls.crt', 'admin is TLS even on loopback')
        self.assertEqual(args[args.index('--kubernetes-namespace') + 1], '$(POD_NAMESPACE)')
        settings = json.loads(named(docs, 'ConfigMap', '-hangang-protection')['data']['settings.json'])
        self.assertTrue(settings['require_protection'])
        self.assertEqual(settings['client_address'], {'mode': 'service_local', 'namespace': 'world', 'name': 'w-hangang-world-hangang'})
        auth = settings['identity_profiles']['default']['auth']
        self.assertEqual(auth['native']['address'], 'w-hangang-world-hopae.world.svc:8703')
        self.assertEqual(auth['native']['tls']['server_name'], 'w-hangang-world-hopae.world.svc')
        self.assertIn('x-hopae-aal', auth['response_headers'])
        authority = settings['pumgye_authority']
        self.assertEqual((authority['transport'], authority['decision_address']), ('grpc', 'w-hangang-world-pumgye.world.svc:9087'))
        service = named(docs, 'Service', '-hangang')['spec']
        self.assertEqual((service['type'], service['externalTrafficPolicy']), ('LoadBalancer', 'Local'))
        hopae = json.loads(named(docs, 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual(hopae['listen']['grpc_gateway'], '0.0.0.0:8703')
        self.assertEqual(hopae['store'], {'kind': 'sqlite'})
        self.assertEqual(hopae['authentication'], {'source': 'config', 'reload_interval_ms': 1000}, 'values own the authentication profiles by default')
        self.assertEqual(hopae['reload'], {'tls_interval_secs': 10})
        self.assertEqual(hopae['apps'][0]['app_id'], 'app')
        store = json.loads(named(render('hopae.authentication.source=store'), 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual(store['authentication'], {'source': 'store', 'reload_interval_ms': 1000})
        self.assertEqual(len(by_kind(docs, 'PersistentVolumeClaim')), 3)
        for claim in by_kind(docs, 'PersistentVolumeClaim'):
            self.assertEqual(claim['metadata']['annotations']['helm.sh/resource-policy'], 'keep')
        for deployment in by_kind(docs, 'Deployment'):
            if not deployment['metadata']['name'].endswith('-hangang'):
                self.assertEqual(deployment['spec']['strategy']['type'], 'Recreate')
                self.assertFalse(deployment['spec']['template']['spec']['automountServiceAccountToken'])
        self.assertFalse(by_kind(docs, 'PodDisruptionBudget'), 'single replicas get no PDB that would block drains')
        test = by_kind(docs, 'Pod')[0]
        self.assertEqual(test['metadata']['annotations']['helm.sh/hook'], 'test')

    def test_certificates_cover_service_dns_and_spiffe_identity(self):
        docs = render()
        issuers = {d['metadata']['name'] for d in by_kind(docs, 'Issuer')}
        self.assertEqual(issuers, {'w-hangang-world-selfsigned', 'w-hangang-world-ca'})
        certificate = named(docs, 'Certificate', '-pumgye')['spec']
        self.assertIn('w-hangang-world-pumgye.world.svc', certificate['dnsNames'])
        self.assertEqual(certificate['uris'], ['spiffe://cluster.local/ns/world/sa/w-hangang-world-pumgye'])
        self.assertEqual(set(certificate['usages']), {'server auth', 'client auth', 'digital signature', 'key encipherment'})
        self.assertEqual(certificate['issuerRef']['name'], 'w-hangang-world-ca')
        ha = render(profile='ha')
        self.assertFalse(by_kind(ha, 'Issuer'), 'an external issuer replaces the bootstrap CA')
        self.assertEqual(named(ha, 'Certificate', '-hopae')['spec']['issuerRef']['kind'], 'ClusterIssuer')
        byo = render(profile='byo-certs')
        self.assertFalse(by_kind(byo, 'Certificate'))
        volumes = named(byo, 'Deployment', '-hopae')['spec']['template']['spec']['volumes']
        self.assertEqual(next(v for v in volumes if v['name'] == 'tls')['secret']['secretName'], 'world-hopae-tls')

    def test_least_privilege_rbac(self):
        docs = render()
        role = by_kind(docs, 'Role')[0]
        self.assertFalse(by_kind(docs, 'ClusterRole'))
        resources = {r for rule in role['rules'] for r in rule['resources']}
        self.assertEqual(resources, {'services', 'ingresses', 'protectionpolicies', 'protectionpolicies/status'})
        for rule in role['rules']:
            self.assertNotIn('*', rule['verbs'] + rule['resources'] + rule['apiGroups'])
            self.assertNotIn('create', rule['verbs'])
            self.assertNotIn('delete', rule['verbs'])
        ha = render(profile='ha')
        cluster = by_kind(ha, 'ClusterRole')[0]
        resources = {r for rule in cluster['rules'] for r in rule['resources']}
        self.assertIn('secrets', resources, 'kubernetesTls reads TLS Secrets')
        self.assertIn('ingresses/status', resources, 'publishAddress writes Ingress status')
        self.assertEqual(by_kind(ha, 'ClusterRoleBinding')[0]['subjects'][0]['namespace'], 'world')
        accounts = {d['metadata']['name']: d.get('automountServiceAccountToken') for d in by_kind(docs, 'ServiceAccount')}
        self.assertEqual(sum(1 for value in accounts.values() if value), 1)

    def test_network_policies_restrict_component_flows(self):
        docs = render()
        policies = {d['metadata']['name']: d['spec'] for d in by_kind(docs, 'NetworkPolicy')}
        self.assertEqual(policies['w-hangang-world-default-deny'].get('ingress'), None)
        pumgye = policies['w-hangang-world-pumgye']['ingress'][0]
        sources = [peer['podSelector']['matchLabels'].get('app.kubernetes.io/name') for peer in pumgye['from']]
        self.assertEqual(sources, ['hangang', 'world-test'])
        sumunjang = policies['w-hangang-world-sumunjang']['ingress'][0]
        self.assertEqual([p['podSelector']['matchLabels']['app.kubernetes.io/name'] for p in sumunjang['from']], ['hangang', 'pumgye', 'world-test'])
        ha = render(profile='ha')
        gateway = next(d['spec'] for d in by_kind(ha, 'NetworkPolicy') if d['metadata']['name'].endswith('-hangang'))
        self.assertEqual(gateway['ingress'][0]['from'][0], {'ipBlock': {'cidr': '10.0.0.0/8'}})
        self.assertEqual(gateway['ingress'][1]['ports'], [{'port': 9000, 'protocol': 'TCP'}])
        self.assertFalse(by_kind(render('networkPolicy.enabled=false'), 'NetworkPolicy'))

    def test_ha_profile(self):
        docs = render(profile='ha')
        gateway = named(docs, 'Deployment', '-hangang')
        self.assertEqual(gateway['spec']['replicas'], 3)
        self.assertEqual(gateway['spec']['strategy']['rollingUpdate'], {'maxUnavailable': 0, 'maxSurge': 1})
        args = gateway['spec']['template']['spec']['containers'][0]['args']
        self.assertEqual(args[args.index('--proxy-protocol-from') + 1], '10.0.0.0/24')
        self.assertNotIn('--kubernetes-namespace', args)
        self.assertIn('--admin-tls-cert', args)
        settings = json.loads(named(docs, 'ConfigMap', '-hangang-protection')['data']['settings.json'])
        self.assertEqual(settings['client_address'], {'mode': 'proxy_protocol'})
        self.assertEqual(settings['pumgye_services'], {'orders': ['shop']})
        self.assertEqual(settings['identity_profiles']['corp-sso']['namespaces'], ['shop', 'payroll'])
        hopae = named(docs, 'Deployment', '-hopae')
        self.assertEqual((hopae['spec']['replicas'], hopae['spec']['strategy']['type']), (1, 'Recreate'))
        env = {e['name']: e['valueFrom']['secretKeyRef'] for e in hopae['spec']['template']['spec']['containers'][0]['env']}
        self.assertEqual(env['HOPAE_PROVIDER_CORP_CLIENT_SECRET'], {'name': 'hopae-providers', 'key': 'corp'})
        config = json.loads(named(docs, 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual(config['store'], {'kind': 'sqlite'})
        claims = {d['metadata']['name'] for d in by_kind(docs, 'PersistentVolumeClaim')}
        self.assertEqual(claims, {'w-hangang-world-pumgye-state', 'w-hangang-world-hopae-state'}, 'a restored Sumunjang claim needs no new PVC')
        pdbs = {d['metadata']['name'] for d in by_kind(docs, 'PodDisruptionBudget')}
        self.assertEqual(pdbs, {'w-hangang-world-hangang'})
        monitor = named(docs, 'ServiceMonitor', '-hangang')['spec']['endpoints'][0]
        self.assertEqual((monitor['scheme'], monitor['authorization']['credentials']['key']), ('https', 'hangang-admin-token'))
        args = gateway['spec']['template']['spec']['containers'][0]['args']
        self.assertEqual(args[args.index('--kubernetes-max-staleness-seconds') + 1], '600')
        self.assertEqual(args[args.index('--tls-reload-seconds') + 1], '30')

    def test_invalid_values_are_refused(self):
        cases = {
            'missing digest': ['hopae.image.digest='],
            'tag-only image': ['hangang.image.digest=latest'],
            'inline secret value': ['credentials.token=abc'],
            'unknown key': ['hangang.replica=2'],
            'sqlite with replicas': ['hopae.replicas=2'],
            'single-writer Pumgye scaled': ['pumgye.replicas=2'],
            'postgres without HA backend': ['hopae.storage.backend=postgresql'],
            'unreleased Hopae PostgreSQL store': ['hopae.storage.backend=postgresql', 'global.ha.backend=postgresql',
                                                  'global.ha.postgresql.existingSecret=pg', 'hopae.replicas=2'],
            'proxy protocol without CIDRs': ['hangang.clientAddress.mode=proxyProtocol'],
            'serviceLocal on ClusterIP': ['hangang.service.type=ClusterIP'],
            'chart-owned Hopae key': ['json:hopae.config={"listen":{"portal":"0.0.0.0:1"}}'],
            'chart-owned Hopae authentication key': ['json:hopae.config={"authentication":{"source":"store"}}'],
            'unknown authentication source': ['hopae.authentication.source=file'],
            'metrics without admin listener': ['monitoring.serviceMonitor.enabled=true'],
            'protection without Pumgye': ['pumgye.enabled=false'],
            'guard without Sumunjang': ['sumunjang.enabled=false'],
            'existing secrets unnamed': ['tls.mode=existingSecrets'],
            'test image without digest': ['tests.image.digest='],
            'invalid CIDR': ['hangang.clientAddress.mode=proxyProtocol', 'hangang.clientAddress.proxyProtocolFrom[0]=not-a-cidr'],
            'stale threshold below watch timeout': ['hangang.staleSeconds=30'],
            'staleness bound below the stale threshold': ['hangang.staleSeconds=120', 'hangang.maxStalenessSeconds=60'],
            'staleness bound above an hour': ['hangang.maxStalenessSeconds=3601'],
            'unknown readiness mode': ['hangang.readiness=always'],
            'Hopae reload interval below 200 ms': ['hopae.authentication.reloadIntervalMs=100'],
            'chart-owned Hopae reload key': ['json:hopae.config={"reload":{"tls_interval_secs":1}}'],
            'Pumgye TLS polling off': ['pumgye.tlsReloadSeconds=0'],
            'Sumunjang TLS polling above an hour': ['sumunjang.tlsReloadSeconds=3601'],
            'BYO monitoring without a scrape client certificate': ['tls.mode=existingSecrets'] + [
                f'tls.existingSecrets.{component}=world-{component}-tls' for component in ['hangang', 'hopae', 'pumgye', 'sumunjang']
            ] + ['monitoring.serviceMonitor.enabled=true', 'hangang.admin.exposeMetrics=true'],
            'unavailable ratio above one': ['monitoring.prometheusRule.decisionUnavailableRatio=2'],
            'console operators without the assertion key': ['hopae.consoleOperators.enabled=true'],
            'console operators on the default app': ['hopae.consoleOperators.enabled=true', 'operatorAssurance.keySecret.name=k',
                                                     'hopae.consoleOperators.appId=default'],
            'chart-owned Hopae console_operators': ['json:hopae.config={"console_operators":{"app_id":"x"}}'],
            'console settings while the console is off': ['hangang.console.disableLocalLogin=true'],
            'console without SSO but local login disabled': ['hangang.console.enabled=true', 'hangang.console.disableLocalLogin=true'],
            'console SSO without a public URL': ['hangang.console.enabled=true', 'hangang.console.sso.enabled=true'],
            'console with metrics exposure': ['hangang.console.enabled=true', 'hangang.admin.exposeMetrics=true'],
            'operator policy without Hopae operators': ['hangang.console.enabled=true', 'hangang.console.sso.enabled=true',
                                                        'hangang.console.sso.publicUrl=https://console.example.test/',
                                                        'hangang.console.sso.operatorPolicy.enabled=true', 'operatorAssurance.keySecret.name=k'],
            'audit log outside the audit volume': ['hangang.console.enabled=true', 'hangang.console.auditLog=/tmp/a.jsonl'],
            'Hopae metrics without the admin listener': ['hopae.metrics.enabled=true', 'hopae.metrics.tokenSecret.name=t'],
            'Hopae metrics without a credential': ['hopae.metrics.enabled=true', 'hopae.admin.enabled=true', 'hopae.admin.delegation.enabled=false'],
            'admin without delegation key': ['hopae.admin.enabled=true'],
            'owner without admin listener': ['pumgye.hopaeOwner.enabled=true', 'pumgye.hopaeOwner.tokenSecret.name=t',
                                             'json:pumgye.hopaeOwner.lifecycle={}'],
            'owner without token': ['hopae.admin.enabled=true', 'hopae.admin.delegation.enabled=false',
                                    'pumgye.hopaeOwner.enabled=true', 'json:pumgye.hopaeOwner.lifecycle={}'],
            'owner without inputs': ['hopae.admin.enabled=true', 'hopae.admin.delegation.enabled=false',
                                     'pumgye.hopaeOwner.enabled=true', 'pumgye.hopaeOwner.tokenSecret.name=t'],
            'admin URL with a path': ['hopae.admin.enabled=true', 'hopae.admin.publicUrl=https://admin.example.test/x'],
            'BYO certificates without the admin certificate': ['tls.mode=existingSecrets'] + [
                f'tls.existingSecrets.{component}=world-{component}-tls' for component in ['hangang', 'hopae', 'pumgye', 'sumunjang']
            ] + ['hopae.admin.enabled=true', 'hopae.admin.delegation.enabled=false'],
        }
        for label, overrides in cases.items():
            failed, error = refused(*overrides)
            self.assertTrue(failed, label)
        # Disabling a component also lifts its digest requirement.
        docs = render('hangang.protection.enabled=false', 'hangang.guard.enabled=false',
                      'hopae.enabled=false', 'pumgye.enabled=false', 'sumunjang.enabled=false', 'hopae.image.digest=')
        self.assertEqual({d['metadata']['name'] for d in by_kind(docs, 'Deployment')}, {'w-hangang-world-hangang'})

    def test_hopae_admin_listener_and_pumgye_owner(self):
        docs = render(profile='admin')
        config = json.loads(named(docs, 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual(config['listen']['admin'], '0.0.0.0:8702')
        self.assertEqual(config['listen']['admin_tls'], {'certificate': '/tls-admin/tls.crt', 'key': '/tls-admin/tls.key', 'client_ca': '/tls/ca.crt'})
        self.assertEqual(config['admin']['public_url'], 'https://w-hangang-world-hopae-admin.world.svc:8702')
        self.assertEqual(config['admin']['hangang_delegation'], {'authority': 'hangang', 'key_env': 'HOPAE_CONSOLE_DELEGATION_KEY'})
        self.assertEqual(config['admin']['users'], [{'email': 'owner@example.test', 'role': 'admin'}], 'operator admin keys are merged')
        self.assertNotIn('service_audience', config['admin'])
        hopae = named(docs, 'Deployment', '-hopae')['spec']['template']['spec']
        env = {e['name']: e['valueFrom']['secretKeyRef'] for e in hopae['containers'][0]['env']}
        self.assertEqual(env['HOPAE_CONSOLE_DELEGATION_KEY'], {'name': 'hopae-console-delegation', 'key': 'key'})
        volumes = {v['name']: v for v in hopae['volumes']}
        self.assertEqual(volumes['admin-tls']['secret']['secretName'], 'w-hangang-world-hopae-admin-tls')
        service = named(docs, 'Service', '-hopae-admin')['spec']
        self.assertEqual((service['type'], service['ports'][0]['port']), ('ClusterIP', 8702))
        certificate = named(docs, 'Certificate', '-hopae-admin')['spec']
        self.assertEqual(certificate['dnsNames'], ['w-hangang-world-hopae-admin.world.svc'])
        policy = named(docs, 'NetworkPolicy', '-hopae-admin')['spec']['ingress'][0]
        self.assertEqual(policy['ports'], [{'port': 8702, 'protocol': 'TCP'}])
        self.assertEqual([p['podSelector']['matchLabels']['app.kubernetes.io/name'] for p in policy['from']], ['hangang', 'pumgye'])
        for other in by_kind(docs, 'NetworkPolicy'):
            for rule in other['spec'].get('ingress', []):
                if any(p.get('port') == 8702 for p in rule.get('ports', [])):
                    self.assertEqual(other['metadata']['name'], 'w-hangang-world-hopae-admin')
        pumgye = named(docs, 'Deployment', '-pumgye')['spec']['template']['spec']['containers'][0]
        self.assertEqual(pumgye['args'][pumgye['args'].index('--hopae-owner') + 1], '/config/hopae-owner.json')
        token = next(e for e in pumgye['env'] if e['name'] == 'PUMGYE_HOPAE_TOKEN')['valueFrom']['secretKeyRef']
        self.assertEqual(token, {'name': 'pumgye-hopae-service-credential', 'key': 'token'})
        owner = json.loads(named(docs, 'ConfigMap', '-pumgye-bootstrap')['data']['hopae-owner.json'])
        self.assertEqual(owner['address'], 'https://w-hangang-world-hopae-admin.world.svc:8702/')
        self.assertEqual((owner['certificate'], owner['key'], owner['ca'], owner['token_env']),
                         ('/tls/tls.crt', '/tls/tls.key', '/tls/ca.crt', 'PUMGYE_HOPAE_TOKEN'))
        self.assertEqual(owner['projection']['audience'], 'pumgye')
        self.assertEqual(owner['audience'], 'https://w-hangang-world-hopae-admin.world.svc:8702', 'sent as x-hopae-audience')
        # Disabled by default: nothing admin-related is rendered.
        plain = render()
        self.assertFalse([d for d in plain if d['metadata']['name'].endswith('-admin')])
        custom = render(
            'hopae.admin.publicUrl=https://hopae-admin.example.test', 'hopae.admin.serviceAudience=world-admin', profile='admin')
        config = json.loads(named(custom, 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual((config['admin']['public_url'], config['admin']['service_audience']), ('https://hopae-admin.example.test', 'world-admin'))
        self.assertEqual(named(custom, 'Certificate', '-hopae-admin')['spec']['dnsNames'],
                         ['hopae-admin.example.test', 'w-hangang-world-hopae-admin.world.svc'])

    def test_runtime_knobs_probes_and_live_reload(self):
        docs = render()
        gateway = named(docs, 'Deployment', '-hangang')['spec']['template']['spec']['containers'][0]
        args = gateway['args']
        self.assertEqual(args[args.index('--kubernetes-max-staleness-seconds') + 1], '300')
        self.assertEqual(args[args.index('--kubernetes-readiness') + 1], 'snapshot')
        self.assertEqual(args[args.index('--tls-reload-seconds') + 1], '10')
        self.assertEqual(gateway['readinessProbe']['httpGet']['path'], '/-/ready')
        pumgye = named(docs, 'Deployment', '-pumgye')['spec']['template']['spec']['containers'][0]
        self.assertEqual(pumgye['args'][pumgye['args'].index('--tls-reload-interval-secs') + 1], '10')
        self.assertNotIn('--metrics-token-env', pumgye['args'])
        sumunjang = named(docs, 'Deployment', '-sumunjang')['spec']['template']['spec']['containers'][0]
        args = sumunjang['args']
        self.assertIn('--management-tls', args)
        self.assertEqual(args[args.index('--listen') + 1], '0.0.0.0:9080')
        self.assertEqual(args[args.index('--readiness-listen') + 1], '0.0.0.0:9083')
        self.assertEqual(args[args.index('--tls-reload-seconds') + 1], '10')
        self.assertEqual(sumunjang['readinessProbe']['httpGet'], {'path': '/readyz', 'port': 'readiness'})
        self.assertEqual(sumunjang['livenessProbe']['httpGet'], {'path': '/healthz', 'port': 'readiness'})
        self.assertNotIn(9083, [p['port'] for p in named(docs, 'Service', '-sumunjang')['spec']['ports']], 'probe port stays out of the Service')
        # Hopae: the ConfigMap is a directory mount (never subPath) and only
        # restart-requiring keys roll the Pod in config mode.
        hopae = named(docs, 'Deployment', '-hopae')['spec']['template']
        mount = next(m for m in hopae['spec']['containers'][0]['volumeMounts'] if m['name'] == 'config')
        self.assertEqual(mount, {'name': 'config', 'mountPath': '/config', 'readOnly': True})
        for deployment in by_kind(docs, 'Deployment'):
            for container in deployment['spec']['template']['spec']['containers']:
                self.assertFalse([m for m in container.get('volumeMounts', []) if 'subPath' in m], container['name'])
        checksum = hopae['metadata']['annotations']['checksum/config']
        profiles = 'json:hopae.config.authentication_gateway={"profiles":[]}'
        live = named(render(profiles), 'Deployment', '-hopae')['spec']['template']['metadata']['annotations']['checksum/config']
        self.assertEqual(live, checksum, 'profile edits are reconciled live, without a rollout')
        restart = named(render('hopae.config.portal.public_url=https://login.example.test'), 'Deployment', '-hopae')
        self.assertNotEqual(restart['spec']['template']['metadata']['annotations']['checksum/config'], checksum)
        store = named(render('hopae.authentication.source=store'), 'Deployment', '-hopae')['spec']['template']['metadata']['annotations']['checksum/config']
        stored = named(render('hopae.authentication.source=store', profiles), 'Deployment', '-hopae')
        self.assertNotEqual(stored['spec']['template']['metadata']['annotations']['checksum/config'], store, 'store mode bootstraps on start')
        tuned = json.loads(named(render('hopae.authentication.reloadIntervalMs=0', 'hopae.tlsReloadSeconds=60'),
                                 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual((tuned['authentication']['reload_interval_ms'], tuned['reload']), (0, {'tls_interval_secs': 60}))
        self.assertFalse(by_kind(docs, 'ServiceMonitor') + by_kind(docs, 'PrometheusRule'))

    def test_service_monitors_and_alerts(self):
        docs = render(profile='ha')
        monitors = {d['metadata']['name']: d['spec'] for d in by_kind(docs, 'ServiceMonitor')}
        self.assertEqual(set(monitors), {f'w-hangang-world-{c}' for c in ['hangang', 'pumgye', 'sumunjang']}, 'Hopae has no /metrics')
        for component, key in [('pumgye', 'pumgye-metrics-token'), ('sumunjang', 'guard-metrics-token')]:
            endpoint = monitors[f'w-hangang-world-{component}']['endpoints'][0]
            self.assertEqual((endpoint['port'], endpoint['scheme'], endpoint['path']), ('management', 'https', '/metrics'))
            self.assertEqual(endpoint['authorization']['credentials'], {'name': 'hangang-world-credentials', 'key': key})
            tls = endpoint['tlsConfig']
            self.assertEqual(tls['serverName'], f'w-hangang-world-{component}.world.svc')
            self.assertEqual(tls['cert']['secret']['name'], 'w-hangang-world-metrics-client-tls')
            self.assertEqual(tls['keySecret'], {'name': 'w-hangang-world-metrics-client-tls', 'key': 'tls.key'})
            self.assertNotIn('insecureSkipVerify', tls)
        client = named(docs, 'Certificate', '-metrics-client')['spec']
        self.assertEqual(client['usages'], ['client auth', 'digital signature', 'key encipherment'])
        self.assertEqual(client['issuerRef']['name'], 'world-ca')
        pumgye = named(docs, 'Deployment', '-pumgye')['spec']['template']['spec']['containers'][0]
        self.assertEqual(pumgye['args'][pumgye['args'].index('--metrics-token-env') + 1], 'PUMGYE_METRICS_TOKEN')
        self.assertEqual(next(e for e in pumgye['env'] if e['name'] == 'PUMGYE_METRICS_TOKEN')['valueFrom']['secretKeyRef']['key'], 'pumgye-metrics-token')
        sumunjang = named(docs, 'Deployment', '-sumunjang')['spec']['template']['spec']['containers'][0]
        self.assertEqual(next(e for e in sumunjang['env'] if e['name'] == 'HANGANG_GUARD_METRICS_TOKEN')['valueFrom']['secretKeyRef']['key'], 'guard-metrics-token')
        policies = {d['metadata']['name']: d['spec'] for d in by_kind(docs, 'NetworkPolicy')}
        for component, port in [('pumgye', 9084), ('sumunjang', 9080)]:
            rule = policies[f'w-hangang-world-{component}']['ingress'][1]
            self.assertEqual(rule['ports'], [{'port': port, 'protocol': 'TCP'}])
            self.assertEqual(rule['from'], [{'namespaceSelector': {'matchLabels': {'kubernetes.io/metadata.name': 'monitoring'}}}])
        rules = by_kind(docs, 'PrometheusRule')[0]['spec']['groups']
        alerts = {r['alert']: r['expr'] for group in rules for r in group['rules']}
        for name in ['HangangProtectedRoutesFailClosed', 'HangangKubernetesSnapshotStale', 'HangangTLSReloadFailing',
                     'PumgyeTLSReloadFailing', 'PumgyeCertificateExpiringSoon', 'PumgyeDecisionsUnavailable',
                     'SumunjangCheckpointStale', 'SumunjangTLSReloadFailing', 'SumunjangCertificateExpiringSoon',
                     'SumunjangDecisionsUnavailable', 'WorldCertificateExpiringSoon']:
            self.assertIn(name, alerts)
        self.assertIn('< 604800', alerts['PumgyeCertificateExpiringSoon'])
        self.assertIn('job="w-hangang-world-hangang-admin"', alerts['HangangTLSReloadFailing'])
        self.assertIn('> 60', alerts['SumunjangCheckpointStale'])
        self.assertNotIn('PumgyeHopaeFeedStale', alerts, 'no Hopae owner feed in the HA profile')
        owner = {r['alert']: r['expr'] for group in by_kind(render('monitoring.prometheusRule.enabled=true', profile='admin'), 'PrometheusRule')[0]['spec']['groups']
                 for r in group['rules']}
        self.assertIn('> 900', owner['PumgyeHopaeFeedStale'], 'defaults to the projection max_staleness_secs')
        self.assertNotIn('HangangTLSReloadFailing', owner, 'Hangang alerts need its metrics listener')
        byo = render(profile='byo-certs')
        self.assertFalse([d for d in by_kind(byo, 'Certificate')])
        endpoint = named(byo, 'ServiceMonitor', '-sumunjang')['spec']['endpoints'][0]
        self.assertEqual(endpoint['tlsConfig']['cert']['secret']['name'], 'world-metrics-client-tls')
        byo_alerts = {r['alert'] for group in by_kind(byo, 'PrometheusRule')[0]['spec']['groups'] for r in group['rules']}
        self.assertNotIn('WorldCertificateExpiringSoon', byo_alerts, 'no cert-manager without certManager mode')

    @unittest.skipUnless(PROMTOOL and Path(PROMTOOL).exists(), 'set PROMTOOL=/path/to/promtool')
    def test_alert_expressions_parse(self):
        for profile in ['ha', 'admin', 'byo-certs', 'console']:
            extra = [] if profile == 'console' else ['hangang.admin.exposeMetrics=true']
            docs = render('monitoring.prometheusRule.enabled=true', 'monitoring.serviceMonitor.enabled=true', *extra, profile=profile)
            with tempfile.NamedTemporaryFile('w', suffix='.yaml') as rules:
                yaml.safe_dump(by_kind(docs, 'PrometheusRule')[0]['spec'], rules)
                rules.flush()
                result = subprocess.run([PROMTOOL, 'check', 'rules', rules.name], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_console_operator_assurance_and_hopae_metrics(self):
        docs = render(profile='console')
        pod = named(docs, 'Deployment', '-hangang')['spec']['template']['spec']
        gateway, console = pod['containers']
        args = gateway['args']
        self.assertNotIn('--admin-tls-cert', args, 'the console reaches the authority over loopback HTTP')
        self.assertEqual(args[args.index('--admin') + 1], '127.0.0.1:9000')
        self.assertEqual(console['command'], ['/usr/local/bin/hangang-console'])
        cargs = console['args']
        self.assertEqual(cargs[cargs.index('--upstream') + 1], 'http://127.0.0.1:9000/')
        self.assertIn('--disable-local-login', cargs)
        self.assertEqual(cargs[cargs.index('--audit-log') + 1], '/var/log/hangang-console/audit.jsonl')
        self.assertEqual(cargs[cargs.index('--hopae-sso') + 1], '/etc/hangang/console/sso.json')
        env = {e['name']: e['valueFrom']['secretKeyRef'] for e in console['env']}
        self.assertEqual(env['CONSOLE_OPERATOR_ASSERTION_KEY'], {'name': 'world-operator-assertion', 'key': 'key'})
        config = named(docs, 'ConfigMap', '-hangang-console')['data']
        sso = json.loads(config['sso.json'])
        self.assertEqual(sso['native_address'], 'w-hangang-world-hopae.world.svc:8704')
        self.assertEqual(sso['native_tls']['server_name'], 'w-hangang-world-hopae.world.svc')
        self.assertEqual(sso['operator_policy'], {'assertion_key_env': 'CONSOLE_OPERATOR_ASSERTION_KEY', 'minimum_aal': 2,
                                                  'require_factor': 'webauthn', 'accept_enrollment_grace': False,
                                                  'sensitive_max_age_seconds': 300, 'step_up_path': '/ui/step-up'})
        self.assertEqual(json.loads(config['plugins.json']), {'plugins': []})
        self.assertEqual(named(docs, 'Service', '-hangang-console')['spec']['ports'][0]['port'], 19080)
        hopae = json.loads(named(docs, 'ConfigMap', '-hopae-config')['data']['hopae.json'])
        self.assertEqual(hopae['listen']['native_gateway'], '0.0.0.0:8704')
        self.assertEqual(hopae['console_operators'], {'app_id': 'console', 'require_aal': 2, 'require_factor': 'webauthn',
                                                      'step_up_path': '/ui/step-up', 'step_up_max_age_secs': 300,
                                                      'assertion_key_env': 'HOPAE_CONSOLE_ASSERTION_KEY'})
        henv = {e['name']: e['valueFrom']['secretKeyRef'] for e in named(docs, 'Deployment', '-hopae')['spec']['template']['spec']['containers'][0]['env']}
        self.assertEqual(henv['HOPAE_CONSOLE_ASSERTION_KEY'], {'name': 'world-operator-assertion', 'key': 'key'})
        policies = {d['metadata']['name']: d['spec'] for d in by_kind(docs, 'NetworkPolicy')}
        self.assertIn({'port': 8704, 'protocol': 'TCP'}, policies['w-hangang-world-hopae']['ingress'][0]['ports'])
        console_rule = policies['w-hangang-world-hangang']['ingress'][-1]
        self.assertEqual(console_rule['ports'], [{'port': 19080, 'protocol': 'TCP'}])
        self.assertEqual(console_rule['from'][0]['podSelector']['matchLabels']['app.kubernetes.io/name'], 'hangang')
        self.assertEqual(policies['w-hangang-world-hopae-admin']['ingress'][1]['ports'], [{'port': 8702, 'protocol': 'TCP'}])
        monitors = {d['metadata']['name']: d['spec'] for d in by_kind(docs, 'ServiceMonitor')}
        self.assertEqual(set(monitors), {f'w-hangang-world-{c}' for c in ['hopae', 'pumgye', 'sumunjang']})
        endpoint = monitors['w-hangang-world-hopae']['endpoints'][0]
        self.assertEqual((endpoint['port'], endpoint['scheme'], endpoint['path']), ('admin', 'https', '/metrics'))
        self.assertEqual(endpoint['authorization']['credentials'], {'name': 'hopae-metrics-credential', 'key': 'token'})
        self.assertEqual(endpoint['tlsConfig']['serverName'], 'w-hangang-world-hopae-admin.world.svc')
        self.assertEqual(endpoint['tlsConfig']['ca']['secret']['name'], 'w-hangang-world-hopae-admin-tls')
        self.assertEqual(endpoint['tlsConfig']['cert']['secret']['name'], 'w-hangang-world-metrics-client-tls')
        self.assertEqual(monitors['w-hangang-world-hopae']['selector']['matchLabels']['hangang.dev/endpoint'], 'admin')
        alerts = {r['alert']: r['expr'] for g in by_kind(docs, 'PrometheusRule')[0]['spec']['groups'] for r in g['rules']}
        for name in ['HopaeStoreDown', 'HopaeTLSReloadFailing', 'HopaeCertificateExpiringSoon', 'HopaeConfigReloadFailing']:
            self.assertIn('job="w-hangang-world-hopae-admin"', alerts[name])
        # Off by default: nothing console- or operator-related is rendered.
        plain = render()
        self.assertEqual(len(named(plain, 'Deployment', '-hangang')['spec']['template']['spec']['containers']), 1)
        self.assertNotIn('console_operators', json.loads(named(plain, 'ConfigMap', '-hopae-config')['data']['hopae.json']))
        self.assertNotIn('native_gateway', json.loads(named(plain, 'ConfigMap', '-hopae-config')['data']['hopae.json'])['listen'])

    def test_client_address_modes(self):
        docs = render('hangang.clientAddress.mode=hostNetwork', 'hangang.service.type=ClusterIP')
        pod = named(docs, 'Deployment', '-hangang')['spec']['template']['spec']
        self.assertTrue(pod['hostNetwork'])
        self.assertEqual(pod['dnsPolicy'], 'ClusterFirstWithHostNet')
        docs = render('hangang.clientAddress.mode=none')
        settings = json.loads(named(docs, 'ConfigMap', '-hangang-protection')['data']['settings.json'])
        self.assertEqual(settings['client_address'], {'mode': 'none'})
        self.assertEqual(named(docs, 'Service', '-hangang')['spec']['externalTrafficPolicy'], 'Cluster')
        self.assertIn('client address is not preserved', notes('hangang.clientAddress.mode=none'))
        self.assertNotIn('client address is not preserved', notes())

    @unittest.skipUnless(os.environ.get('WORLD_KUBECONFORM') and Path(KUBECONFORM).exists(), 'set WORLD_KUBECONFORM=1 with kubeconform installed')
    def test_rendered_objects_match_published_schemas(self):
        for profile in PROFILES:
            rendered = helm('template', 'w', str(WORLD), '-n', 'world', '-f', str(WORLD / 'ci' / f'{profile}-values.yaml')).stdout
            with tempfile.NamedTemporaryFile('w', suffix='.yaml') as manifest:
                manifest.write(rendered)
                manifest.flush()
                result = subprocess.run([KUBECONFORM, '-strict', '-summary', '-kubernetes-version', '1.29.0',
                                         '-schema-location', 'default', '-schema-location',
                                         'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json',
                                         manifest.name],
                                        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Invalid: 0, Errors: 0, Skipped: 0', result.stdout)


@unittest.skipUnless(Path(HELM).exists(), 'helm is not installed')
class CrdChart(unittest.TestCase):
    def test_crds_are_kept_and_roles_aggregate(self):
        docs = render(chart=CRDS)
        crd = by_kind(docs, 'CustomResourceDefinition')[0]
        self.assertEqual(crd['metadata']['name'], 'protectionpolicies.world.hangang.dev')
        self.assertEqual(crd['metadata']['annotations']['helm.sh/resource-policy'], 'keep')
        self.assertNotIn('x-kubernetes-preserve-unknown-fields', json.dumps(crd))
        roles = {d['metadata']['name']: d for d in by_kind(docs, 'ClusterRole')}
        self.assertEqual(set(roles), {'world-admin', 'world-editor', 'world-viewer'})
        self.assertEqual(roles['world-viewer']['metadata']['labels']['rbac.authorization.k8s.io/aggregate-to-view'], 'true')
        editor_resources = {r for rule in roles['world-editor']['rules'] for r in rule['resources']}
        self.assertNotIn('protectionpolicies/status', editor_resources, 'status belongs to the controller')

    def test_crd_matches_the_hangang_source_schema_rules(self):
        crd = by_kind(render(chart=CRDS), 'CustomResourceDefinition')[0]
        spec = crd['spec']['versions'][0]['schema']['openAPIV3Schema']['properties']['spec']
        self.assertIn('x-kubernetes-validations', spec)
        actions = spec['properties']['authorization']['properties']['pumgye']['properties']['actions']
        self.assertEqual(actions['x-kubernetes-list-type'], 'map')


if __name__ == '__main__':
    unittest.main()
