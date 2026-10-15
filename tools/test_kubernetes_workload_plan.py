"""Pure render/parser tests. No Kubernetes, credentials, Cargo or remote calls."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from kubernetes_workload_plan import bootstrap, configuration_patches, stable_subject, token_request, validate_mode


class WorkloadPlan(unittest.TestCase):
    def test_existing_native_cross_component_golden_and_uid_separation(self):
        args = ['https://issuer.example.test', 'example-cluster', 'blue', 'worker', 'sa-1', 'worker-pod', 'pod-1']
        self.assertEqual(stable_subject(*args), 's_529be5b595ab327853eabe2d1adf52256e262af036510607')
        for index in [0, 1, 2, 3, 4, 5, 6]:
            changed = args.copy()
            changed[index] += '-other'
            self.assertNotEqual(stable_subject(*changed), stable_subject(*args))

    def test_bootstrap_has_only_owned_minimal_reviewer_permission(self):
        items = bootstrap('owned-world-example', 'example.test/node@sha256:' + '1' * 64)
        role = next(x for x in items if x['kind'] == 'ClusterRole')
        self.assertEqual(role['rules'], [{'apiGroups': ['authentication.k8s.io'], 'resources': ['tokenreviews'], 'verbs': ['create']}])
        binding = next(x for x in items if x['kind'] == 'ClusterRoleBinding')
        self.assertEqual(binding['roleRef']['name'], role['metadata']['name'])
        self.assertEqual(binding['subjects'], [{'kind': 'ServiceAccount', 'name': 'workload-reviewer', 'namespace': 'owned-world-example'}])
        local = next(x for x in items if x['kind'] == 'Role')
        self.assertEqual(local['metadata']['namespace'],'owned-world-example')
        self.assertEqual(local['rules'],[
            {'apiGroups':[''],'resources':['serviceaccounts'],'resourceNames':['workload-client'],'verbs':['get']},
            {'apiGroups':[''],'resources':['pods'],'resourceNames':['workload-bound'],'verbs':['get']}])
        local_binding=next(x for x in items if x['kind']=='RoleBinding')
        self.assertEqual(local_binding['roleRef'],{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':local['metadata']['name']})
        self.assertEqual(local_binding['subjects'],binding['subjects'])
        self.assertEqual(local_binding['metadata']['namespace'],'owned-world-example')
        pod = next(x for x in items if x['kind'] == 'Pod')
        self.assertFalse(pod['spec']['automountServiceAccountToken'])
        self.assertEqual(pod['spec']['serviceAccountName'], 'workload-client')
        self.assertNotIn('Secret', [x['kind'] for x in items])
        for namespace, image in [('default', 'x@sha256:' + '1'*64), ('owned-world-example', 'node:latest')]:
            with self.assertRaises(ValueError): bootstrap(namespace, image)

    def test_pod_bound_request_and_class_specific_configs(self):
        request = token_request('owned-world-example', 'workload-client', 'workload-bound', 'pod-1', 'orders-workload')
        self.assertEqual(request['body']['spec']['boundObjectRef'], {'apiVersion': 'v1', 'kind': 'Pod', 'name': 'workload-bound', 'uid': 'pod-1'})
        self.assertEqual(request['body']['spec']['audiences'], ['orders-workload'])
        patch = configuration_patches(namespace='owned-world-example', api_origin='https://kubernetes.example.test/', issuer='https://issuer.example.test', cluster='example-cluster', audience='orders-workload', sa_uid='sa-1', pod_uid='pod-1')
        self.assertEqual(patch['pum_subject_maps']['users'], {})
        self.assertEqual(len(patch['pum_subject_maps']['workload_users']), 1)
        self.assertEqual(patch['root_observed_patch'], {'authentication_class': 'workload'})
        profile = patch['hop_profile']
        self.assertEqual(profile['api_keys'], [])
        self.assertEqual(profile['networks'], [])
        self.assertNotIn('composition', profile)
        self.assertNotIn('ca_pem', profile['kubernetes_tokenreview']) # only env reference, no CA contents
        self.assertNotIn('reviewer_token', profile['kubernetes_tokenreview'])
        bad = dict(namespace='owned-world-example', api_origin='http://unsafe.example.test/', issuer='https://issuer.example.test', cluster='example-cluster', audience='orders-workload', sa_uid='sa-1', pod_uid='pod-1')
        with self.assertRaises(ValueError): configuration_patches(**bad)

    def test_mode_matrix_and_live_runner_cannot_fall_back_to_service(self):
        good = dict(workload=True, composition=False, observed=True, credential_projection=True, native_resource=True, resource_catalog=True, receipt_client=True)
        validate_mode(**good)
        for name in ['observed', 'credential_projection', 'native_resource', 'resource_catalog', 'receipt_client']:
            bad = copy.copy(good); bad[name] = False
            with self.assertRaises(ValueError): validate_mode(**bad)
        with self.assertRaisesRegex(ValueError, 'cannot be combined'): validate_mode(**dict(good, composition=True))
        # Legacy paths do not acquire Workload prerequisites.
        validate_mode(**dict.fromkeys(good, False))
        argv = [sys.executable, str(Path(__file__).with_name('kubernetes_world_smoke.py')), '--kubectl', '/never/invoked', '--hopae-fixture', '/unused', '--sumunjang-plugin', '/unused', '--echo-image', 'example.test/node:fixture', '--workload', '--observed', '--credential-projection', '--native-resource', '--resource-catalog', '--receipt-client', '/unused']
        for component in ['hangang', 'hopae', 'pumgye', 'sumunjang']: argv += ['--' + component + '-image', 'example.test/' + component + ':fixture']
        result = subprocess.run(argv, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--workload requires --workload-capabilities', result.stderr)
        result = subprocess.run(argv + ['--composition'], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn('cannot be combined', result.stderr)


if __name__ == '__main__': unittest.main()
