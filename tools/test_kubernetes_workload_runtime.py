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
        manifest = root/'capabilities.json'; manifest.write_text(json.dumps({'version':1,'components':components, 'qualification_tools': {'workload_tap': {'image':'example.test/tap@sha256:'+'5'*64,'source':runtime.TAP_SOURCE,'binary_sha256':runtime.TAP_SHA256}}}))
        args = SimpleNamespace(workload=True, browser_probe=None, authenticated_client=None, sumunjang_native_source=False,
            workload_capabilities=manifest, workload_utility_image='example.test/node@sha256:'+'4'*64,
            workload_issuer='https://issuer.example.test', workload_cluster_id='example-cluster',
            workload_reviewer_audience='https://issuer.example.test', receipt_client=probe,
            workload_tap_image='example.test/tap@sha256:'+'5'*64,workload_held_client=probe,
            workload_backup_evidence=root/'backup-proof.json',echo_image='example.test/echo@sha256:'+'6'*64)
        archive=root/'offhost-backup'; archive.write_bytes(b'owned fixture backup')
        args.workload_backup_evidence.write_text(json.dumps({'version':1,'cold_snapshot':True,'offhost_verified':True,
            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'offhost_path':str(archive)}))
        for name, entry in components.items(): setattr(args, name+'_image', entry['image'])
        return args, components

    def test_every_provenance_gate_precedes_any_external_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, components = self.args(Path(temporary))
            with patch.object(runtime, 'PROBE_SHA256', hashlib.sha256(args.receipt_client.read_bytes()).hexdigest()), patch.object(runtime, 'HELD_SHA256', hashlib.sha256(args.receipt_client.read_bytes()).hexdigest()), patch('subprocess.run') as run:
                runtime.preflight(args)
                original = json.loads(args.workload_capabilities.read_text())
                for name in components:
                    bad = json.loads(args.workload_capabilities.read_text())
                    bad['components'][name]['capabilities'] = []
                    args.workload_capabilities.write_text(json.dumps(bad))
                    with self.assertRaisesRegex(ValueError, 'capability'): runtime.preflight(args)
                    args.workload_capabilities.write_text(json.dumps(original))
                for name, capability in [('pumgye','workload_resource_metadata_decision'),('hangang','workload_typed_http_preliminary_gate')]:
                    bad=json.loads(json.dumps(original));bad['components'][name]['capabilities'].remove(capability)
                    args.workload_capabilities.write_text(json.dumps(bad))
                    with self.assertRaisesRegex(ValueError,'capability'):runtime.preflight(args)
                    args.workload_capabilities.write_text(json.dumps(original))
                args.receipt_client.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'hash'): runtime.preflight(args)
                run.assert_not_called()

    def test_backup_tap_audience_and_held_inputs_refuse_before_external_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, _ = self.args(Path(temporary))
            digest=hashlib.sha256(args.receipt_client.read_bytes()).hexdigest()
            with patch.object(runtime,'PROBE_SHA256',digest),patch.object(runtime,'HELD_SHA256',digest),patch('subprocess.run') as run:
                runtime.preflight(args)
                archive=Path(json.loads(args.workload_backup_evidence.read_text())['offhost_path'])
                original=archive.read_bytes();archive.write_bytes(b'x'*len(original))
                with self.assertRaisesRegex(ValueError,'full SHA'):runtime.preflight(args)
                archive.write_bytes(original)
                args.workload_reviewer_audience='orders-workload'
                with self.assertRaisesRegex(ValueError,'audience'):runtime.preflight(args)
                args.workload_reviewer_audience='https://issuer.example.test'
                args.echo_image='example.test/echo:latest'
                with self.assertRaisesRegex(ValueError,'digest'):runtime.preflight(args)
                args.echo_image='example.test/echo@sha256:'+'6'*64
                document=json.loads(args.workload_capabilities.read_text());document['qualification_tools']['workload_tap']['source']='0'*40
                args.workload_capabilities.write_text(json.dumps(document))
                with self.assertRaisesRegex(ValueError,'tap capability'):runtime.preflight(args)
                run.assert_not_called()

    def test_owned_tap_fixed_mtls_root_peer_and_direct_pum_peer(self):
        args=SimpleNamespace(workload_tap_image='example.test/tap@sha256:'+'5'*64)
        owner=runtime.Workload(args,'owned-world-test',None,{'caller':'fixture','pum-decision':'fixture2'})
        items=[{'kind':'Secret','metadata':{'name':'world-credentials'},'stringData':{}}]
        config={'data':{'authentication-live.json':'unchanged-real-hop','projection-live.json':'unchanged-real-hop'}}
        gateway={'http':[{'auth':{'native':{'address':'hopae.owned-world-test.svc:8703','tls':{'server_name':'hopae.owned-world-test.svc'}}}}]}
        envs={'hangang':[{'name':'FIXTURE_KEY','valueFrom':{'secretKeyRef':{'name':'world-credentials','key':'caller'}}}]}
        def env(name,key):return {'name':name,'valueFrom':{'secretKeyRef':{'name':'world-credentials','key':key}}}
        owner.install_tap(items,config,gateway,envs,env)
        tap=json.loads(config['data']['workload-tap.json'])
        self.assertEqual(tap['hop']['address'],'https://hopae.owned-world-test.svc:8703')
        self.assertEqual(tap['pum']['address'],'https://pumgye.owned-world-test.svc:9087')
        self.assertEqual(config['data']['authentication-live.json'],'unchanged-real-hop')
        self.assertEqual(config['data']['projection-live.json'],'unchanged-real-hop')
        self.assertEqual(gateway['http'][0]['auth']['native']['tls']['server_name'],'workload-tap.owned-world-test.svc')
        self.assertEqual(envs['hangang'][0]['valueFrom']['secretKeyRef']['key'],'tap-caller')
        deployment=next(x for x in items if x['kind']=='Deployment');pod=deployment['spec']['template']['spec']
        self.assertFalse(pod['automountServiceAccountToken']);self.assertEqual(pod['volumes'][1]['secret']['secretName'],'world-tap-tls')
        self.assertEqual(pod['containers'][0]['image'],args.workload_tap_image)
        self.assertNotIn('hostNetwork',pod)

    def test_safe_replay_counter_requires_one_new_pass_and_drops_untrusted_fields(self):
        args=SimpleNamespace(evidence_dir=None)
        value={'event':'workload_pair_replay','passed':True,'replay_status':'Unavailable','auth_and_permit_owner_checks':'before_and_after_replay','original_first_reply_returned_unchanged':True,'elapsed_ms':10,'secret':'must-not-copy'}
        owner=runtime.Workload(args,'owned-world-test',lambda *a,**kw:json.dumps(value).encode(),{})
        facts=owner.replay_facts();self.assertNotIn('secret',facts[0]);owner.check_replay_increment([])
        with self.assertRaises(AssertionError):owner.check_replay_increment(facts)
        value['passed']=False
        with self.assertRaises(AssertionError):owner.check_replay_increment([])

    def test_cleanup_continues_after_global_uid_conflict_without_deleting_replacement(self):
        calls=[]
        def kube(*args,**kw):
            calls.append((args,kw))
            if '/owned-binding' in args:raise RuntimeError('UID conflict')
            return b'{}'
        owner=runtime.Workload(SimpleNamespace(),'owned-world-test',kube,{})
        owner.namespace_uid='namespace-original';owner.globals=[('/owned-role','role-original'),('/owned-binding','binding-original')]
        with self.assertRaisesRegex(RuntimeError,'global cleanup'):owner.cleanup()
        deletes=[json.loads(kw['body'])['preconditions']['uid'] for args,kw in calls if 'body' in kw]
        self.assertEqual(deletes,['binding-original','role-original','namespace-original'])

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



class ProbeRefusalClassification(unittest.TestCase):
    def test_fixed_trust_startup_error_is_not_a_native_owner_denial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);probe=root/'probe';probe.write_bytes(b'fixture')
            owner=runtime.Workload(SimpleNamespace(receipt_client=probe),'owned-world-test',None,{'caller':'fixture'})
            result=SimpleNamespace(returncode=1,stdout=json.dumps({'allowed':False,'probe_error':'policy'}))
            with patch.object(runtime.subprocess,'run',return_value=result):
                with self.assertRaisesRegex(AssertionError,'probe failed'):owner.probe(root,{},'fixture',False)
                self.assertTrue(owner.probe(root,{},'fixture',False,startup_refusal=True)['startup_trust_refused'])

if __name__=='__main__': unittest.main()
