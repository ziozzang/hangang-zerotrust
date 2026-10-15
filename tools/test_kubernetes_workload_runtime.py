"""Local provenance, renderer and UID cleanup failure checks; never calls a cluster."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import kubernetes_workload_runtime as runtime


class RuntimePreparation(unittest.TestCase):
    def args(self, root):
        probe = root/'probe'; probe.write_bytes(b'fixed owned fixture probe'); probe.chmod(0o700)
        components = {name: {'image': 'example.test/'+name+'@sha256:'+'1'*64, 'source':'2'*40,
            'binary_sha256':'3'*64, 'capabilities': capabilities.copy()} for name, capabilities in runtime.REQUIRED.items()}
        manifest = root/'capabilities.json'; manifest.write_text(json.dumps({'version':1,'components':components}))
        args = SimpleNamespace(workload=True, browser_probe=None, authenticated_client=None, sumunjang_native_source=False,
            workload_capabilities=manifest, workload_utility_image='example.test/node@sha256:'+'4'*64,
            workload_issuer='https://issuer.example.test', workload_cluster_id='example-cluster',
            workload_reviewer_audience='https://issuer.example.test', receipt_client=probe)
        for name, entry in components.items(): setattr(args, name+'_image', entry['image'])
        return args, components

    def test_every_provenance_gate_precedes_any_external_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, components = self.args(Path(temporary))
            with patch.object(runtime, 'PROBE_SHA256', hashlib.sha256(args.receipt_client.read_bytes()).hexdigest()), patch('subprocess.run') as run:
                runtime.preflight(args)
                for name in components:
                    bad = json.loads(args.workload_capabilities.read_text())
                    bad['components'][name]['capabilities'] = []
                    args.workload_capabilities.write_text(json.dumps(bad))
                    with self.assertRaisesRegex(ValueError, 'capability'): runtime.preflight(args)
                    args.workload_capabilities.write_text(json.dumps({'version':1,'components':components}))
                args.receipt_client.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'hash'): runtime.preflight(args)
                run.assert_not_called()

    def test_raw_delete_carries_original_uid_not_current_replacement(self):
        calls=[]
        def kube(*args, **kwargs): calls.append((args, json.loads(kwargs['body']))); return b'{}'
        runtime.delete_owned(kube, '/apis/rbac.authorization.k8s.io/v1/clusterroles/owned-world-test', 'original-uid', '4')
        self.assertEqual(calls[0][1]['preconditions'], {'uid':'original-uid','resourceVersion':'4'})
        with self.assertRaises(ValueError): runtime.delete_owned(kube, '/never', '')
        self.assertEqual(len(calls),1)
        def conflict(*args, **kwargs): raise RuntimeError('UID precondition conflict')
        with self.assertRaises(RuntimeError): runtime.delete_owned(conflict, '/owned', 'old')

    def test_partial_creation_tracks_global_uid_and_cleanup_never_deletes_unknown(self):
        calls=[]
        def kube(*args, **kwargs):
            calls.append((args, kwargs))
            if args[0]=='create': return json.dumps({'metadata': {'uid':'created-uid'}}).encode()
            return b'{}'
        owner=runtime.Workload(SimpleNamespace(), 'owned-world-test', kube, {})
        owner.create({'kind':'ClusterRole','metadata':{'name':'owned-world-test-role'}})
        owner.cleanup()
        self.assertEqual(len(calls),2)
        self.assertEqual(json.loads(calls[-1][1]['body'])['preconditions'], {'uid':'created-uid'})
        self.assertTrue(any('/clusterroles/owned-world-test-role' in value for value in calls[-1][0]))

    def test_expired_or_missing_tokenrequest_expiry_is_not_a_new_lease(self):
        for status in [{}, {'token':'x'*64}, {'token':'x'*64,'expirationTimestamp':'2000-01-01T00:00:00Z'}]:
            with self.assertRaises(ValueError): runtime.token_credential({'status':status})

    def test_namespace_replacement_refuses_before_any_child_creation(self):
        calls=[]
        def kube(*args, **kwargs):
            calls.append(args)
            return b'{"metadata":{"uid":"replacement"}}'
        owner=runtime.Workload(SimpleNamespace(), 'owned-world-test', kube, {})
        owner.namespace_uid='original'
        with self.assertRaisesRegex(ValueError, 'replaced'):
            owner.prepare([], {}, {}, {}, {}, {}, {}, None)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],'get')

    def test_token_request_credential_is_only_stdin_and_private_memory(self):
        calls=[]
        private='owned-private-placeholder-'+'x'*64
        def kube(*args, **kwargs):
            calls.append((args,kwargs))
            return json.dumps({'status':{'token':private,'expirationTimestamp':'2099-01-01T00:00:00Z'}}).encode()
        tokens={}
        owner=runtime.Workload(SimpleNamespace(), 'owned-world-test', kube, tokens)
        credential=owner.mint('orders-workload',uid='pod-uid')
        self.assertEqual(credential,'k8s:'+private)
        self.assertNotIn(private,str(calls[0][0]))
        self.assertEqual(json.loads(calls[0][1]['body'])['spec']['boundObjectRef']['uid'],'pod-uid')
        self.assertIn(private,tokens.values()) # diagnostic redaction owner, no evidence output

    def test_token_review_does_not_treat_transport_error_as_revocation(self):
        def unavailable(*args, **kwargs): raise RuntimeError('unavailable')
        owner=runtime.Workload(SimpleNamespace(), 'owned-world-test', unavailable, {})
        with self.assertRaises(RuntimeError): owner.api_authenticates('k8s:private-placeholder')
        def denied(*args, **kwargs):
            body=json.loads(kwargs['body']); self.assertEqual(body['spec']['audiences'],['orders-workload'])
            return b'{"status":{"authenticated":false}}'
        owner.kube=denied
        self.assertFalse(owner.api_authenticates('k8s:private-placeholder'))


if __name__=='__main__': unittest.main()
