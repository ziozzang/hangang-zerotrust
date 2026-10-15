"""Local provenance, renderer and UID cleanup failure checks; never calls a cluster."""
import hashlib
import copy
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
        args = SimpleNamespace(workload=True, hopae_plugin=root/'reviewed-hopae-plugin', browser_probe=None, authenticated_client=None, sumunjang_native_source=False,
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

    def test_old_tap_source_or_hash_is_not_adopted_by_new_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, _ = self.args(Path(temporary))
            digest=hashlib.sha256(args.receipt_client.read_bytes()).hexdigest()
            original=json.loads(args.workload_capabilities.read_text())
            with patch.object(runtime,'PROBE_SHA256',digest),patch.object(runtime,'HELD_SHA256',digest),patch('subprocess.run') as run:
                for field, old in [('source','eae0d97534da69f0ea931ca54b1ed7d586d7ba61'),('binary_sha256','71f9a8b33c8648f3be8f0376c835ace3b1e110dfadc3d692a955a966607706ae')]:
                    bad=copy.deepcopy(original)
                    bad['qualification_tools']['workload_tap'][field]=old
                    args.workload_capabilities.write_text(json.dumps(bad))
                    with self.assertRaisesRegex(ValueError,'qualification tap'):runtime.preflight(args)
                run.assert_not_called()

    def test_missing_hopae_plugin_refuses_before_external_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            args, _ = self.args(Path(temporary))
            args.hopae_plugin = None
            with patch('subprocess.run') as run:
                with self.assertRaisesRegex(ValueError, 'hopae-plugin'): runtime.preflight(args)
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

    def test_verify_diagnostics_do_not_count_as_replay_or_mask_failures(self):
        diagnostic={'event':'workload_verify_stage','stage':'upstream_completed','tonic_code':'ok','reply_status':'200','elapsed_ms':5,'ingress_count':1,'admitted_count':1,'upstream_completed_count':1,'cancelled_count':0}
        replay={'event':'workload_pair_replay','passed':True,'replay_status':'Unavailable','auth_and_permit_owner_checks':'before_and_after_replay','original_first_reply_returned_unchanged':True,'elapsed_ms':10}
        lines=[diagnostic]
        owner=runtime.Workload(SimpleNamespace(evidence_dir=None),'owned-world-test',lambda *a,**kw:'\n'.join(json.dumps(v) for v in lines).encode(),{})
        self.assertEqual(owner.replay_facts(),[])
        with self.assertRaises(AssertionError):owner.check_replay_increment([])
        lines.extend([replay,diagnostic]);owner.check_replay_increment([])
        self.assertEqual(owner.verify_diagnostics,[diagnostic,diagnostic])
        self.assertEqual(len(owner.replay_facts()),1)
        replay['passed']=False
        with self.assertRaises(AssertionError):owner.check_replay_increment([])
        for field,bad in [('reply_status','reserved-secret'),('tonic_code','arbitrary'),('elapsed_ms',True),('ingress_count',-1),('stage','arbitrary')]:
            malformed=copy.deepcopy(diagnostic);malformed[field]=bad;lines[:]=[malformed]
            with self.assertRaises(AssertionError):owner.replay_facts()
        malformed=copy.deepcopy(diagnostic);malformed['secret']='reserved-secret';lines[:]=[malformed]
        with self.assertRaises(AssertionError):owner.replay_facts()
        lines[:]=[{'event':'unknown'}]
        with self.assertRaises(AssertionError):owner.replay_facts()

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

class FinalPrerequisites(unittest.TestCase):
    def test_rbac_measures_exact_metadata_gets_and_client_tokenrequest_denial(self):
        calls=[]
        def kube(*args,**kw):
            attrs=json.loads(kw['body'])['spec']['resourceAttributes']
            account=args[args.index('--as')+1].split(':')[-1]
            calls.append((account,attrs))
            allowed=(account=='workload-reviewer' and ((attrs['resource']=='tokenreviews' and attrs['verb']=='create')
                or (attrs['verb']=='get' and attrs.get('subresource') is None and
                    (attrs['resource'],attrs.get('name')) in [('serviceaccounts','workload-client'),('pods','workload-bound')])))
            return json.dumps({'status':{'allowed':allowed}}).encode()
        owner=runtime.Workload(SimpleNamespace(),'owned-world-test',kube,{})
        owner.check_rbac()
        for account,resource,name,subresource in [('workload-reviewer','serviceaccounts','workload-client',None),
            ('workload-reviewer','pods','workload-bound',None),('workload-reviewer','serviceaccounts','workload-reviewer',None),
            ('workload-reviewer','pods','unrelated-owned-negative',None),
            ('workload-client','serviceaccounts','workload-reviewer','token'),('workload-client','serviceaccounts','workload-client','token')]:
            self.assertTrue(any(a==account and r['resource']==resource and r.get('name')==name and r.get('subresource')==subresource for a,r in calls))
        def escalated(*args,**kw):return b'{"status":{"allowed":true}}'
        owner.kube=escalated
        with self.assertRaisesRegex(AssertionError,'RBAC'):owner.check_rbac()

    def recovery_owner(self):
        entries=[]
        def kube(*args,**kw):return '\n'.join(json.dumps(x) for x in entries).encode()
        return runtime.Workload(SimpleNamespace(evidence_dir=None),'owned-world-test',kube,{}),entries

    def test_restoration_503_zeroeffects_then_200_oneeffect_and_new_safe_replay(self):
        owner,entries=self.recovery_owner();calls=[]
        def request():
            code,delta=(503,0) if not calls else (200,1)
            calls.append(code);request.last={'backend_delta':delta}
            entries.append({'event':'workload_pair_replay','passed':code==200,'elapsed_ms':5,
                'replay_status':'Unavailable','auth_and_permit_owner_checks':'before_and_after_replay',
                'original_first_reply_returned_unchanged':True})
            return code,b'owned-body'
        with patch.object(runtime.time,'sleep'):
            self.assertEqual(owner.restored_http(request),(200,b'owned-body'))
        self.assertEqual(calls,[503,200])
        self.assertFalse(entries[0]['passed']);self.assertTrue(entries[1]['passed'])

    def test_restoration_rejects_other_statuses_sideeffects_or_transport_immediately(self):
        for code,delta in [(403,0),(401,0),(500,0),(503,1),(200,0),(200,2)]:
            owner,_=self.recovery_owner();calls=[]
            def request():calls.append(code);request.last={'backend_delta':delta};return code,b''
            with self.assertRaises(AssertionError):owner.restored_http(request)
            self.assertEqual(calls,[code])
        owner,_=self.recovery_owner()
        def unavailable():raise OSError('owned fixture unavailable')
        with self.assertRaises(OSError):owner.restored_http(unavailable)

    def test_restoration_deadline_and_missing_success_replay_refuse(self):
        owner,_=self.recovery_owner();calls=[]
        def request():calls.append(503);request.last={'backend_delta':0};return 503,b''
        with patch.object(runtime.time,'monotonic',side_effect=[0,0,1,2]),patch.object(runtime.time,'sleep'):
            with self.assertRaisesRegex(AssertionError,'deadline'):owner.restored_http(request,seconds=1)
        self.assertEqual(calls,[503])
        def success():success.last={'backend_delta':1};return 200,b''
        with self.assertRaisesRegex(AssertionError,'replay'):owner.restored_http(success)


class ProfileOwnerRealm(unittest.TestCase):
    def owner(self, failure=None):
        original = {'authority_id': 'owned', 'profiles': [{'service_id': 'orders',
            'host': 'app.example.test', 'realm': 'owned-cluster',
            'kubernetes_tokenreview': {'connection': {'cluster_id': 'owned-cluster'}},
            'api_keys': [], 'networks': ['192.0.2.0/24']}]}
        state = {'revision': 7, 'configuration': copy.deepcopy(original), 'digest': 'a'*64}
        calls = []
        def api(admin, path, method='GET', body=None):
            self.assertEqual(admin, 123)
            calls.append((path, method, copy.deepcopy(body)))
            if method == 'GET':
                readback = copy.deepcopy(state)
                if failure == 'readback_config' and state['revision'] == 8:
                    readback['configuration']['profiles'][0]['realm'] = 'unexpected'
                if failure == 'readback_revision' and state['revision'] == 8:
                    readback['revision'] = 7
                if failure == 'readback_digest' and state['revision'] == 8:
                    readback['digest'] = 'c'*64
                return 200, readback, {}
            self.assertEqual(path, runtime.PROFILE_PATH + '/publish')
            self.assertEqual(set(body), {'revision', 'configuration'})
            if failure == 'stale' or body['revision'] != state['revision']:
                return 409, {}, {}
            state.update(revision=state['revision']+1,
                         configuration=copy.deepcopy(body['configuration']), digest='b'*64)
            if failure == 'transport' and state['revision'] == 8:
                raise OSError('owned fixture uncertain response')
            reply = {'revision': state['revision'], 'digest': state['digest']}
            if failure == 'ack_revision': reply['revision'] += 1
            if failure == 'ack_digest': reply['digest'] = 'invalid'
            return 200, reply, {}
        return original, state, calls, api

    def scope(self, api):
        return runtime.temporary_workload_realm(api, 123, service='orders',
            host='app.example.test', original_realm='owned-cluster', changed_realm='changed-cluster')

    def test_changed_owner_is_active_before_probe_and_restored_with_current_cas(self):
        original, state, calls, api = self.owner()
        with self.scope(api):
            self.assertEqual(state['revision'], 8)
            profile = state['configuration']['profiles'][0]
            self.assertEqual(profile['realm'], 'changed-cluster')
            self.assertEqual(profile['kubernetes_tokenreview']['connection']['cluster_id'], 'changed-cluster')
            self.assertEqual(calls[-1][1], 'GET')
        self.assertEqual(state['configuration'], original)
        self.assertEqual(state['revision'], 9)
        self.assertEqual([c[2]['revision'] for c in calls if c[1]=='POST'], [7, 8])
        self.assertEqual(calls[-1][1], 'GET')
        self.assertEqual(original['profiles'][0]['realm'], 'owned-cluster')

    def test_stale_or_mismatched_publication_never_reaches_probe(self):
        for failure in ['stale', 'ack_revision', 'ack_digest', 'readback_revision', 'readback_digest', 'readback_config']:
            with self.subTest(failure=failure):
                _, _, _, api = self.owner(failure)
                reached = False
                with self.assertRaises(AssertionError):
                    with self.scope(api): reached = True
                self.assertFalse(reached)

    def test_failed_probe_restores_original_without_hiding_original_failure(self):
        original, state, _, api = self.owner()
        with self.assertRaisesRegex(RuntimeError, 'probe failed'):
            with self.scope(api): raise RuntimeError('probe failed')
        self.assertEqual(state['configuration'], original)
        self.assertEqual(state['revision'], 9)

    def test_unrelated_owner_is_not_overwritten_on_restoration(self):
        _, state, calls, api = self.owner()
        with self.assertRaisesRegex(AssertionError, 'restoration owner mismatch'):
            with self.scope(api):
                state['configuration']['profiles'][0]['realm'] = 'another-writer'
                state['revision'] += 1
        self.assertEqual(len([c for c in calls if c[1]=='POST']), 1)

    def test_lost_publish_response_restores_with_new_cas_without_replaying_mutation(self):
        original, state, calls, api = self.owner('transport')
        reached = False
        with self.assertRaisesRegex(OSError, 'uncertain response'):
            with self.scope(api): reached = True
        self.assertFalse(reached)
        self.assertEqual(state['configuration'], original)
        self.assertEqual(state['revision'], 9)
        self.assertEqual([c[2]['revision'] for c in calls if c[1]=='POST'], [7, 8])
        self.assertEqual(calls[-1][1], 'GET')

    def test_stale_restoration_is_a_failure_and_is_not_retried(self):
        _, state, calls, api = self.owner()
        def stale_restore(admin, path, method='GET', body=None):
            if method == 'POST' and body['revision'] == 8:
                calls.append((path, method, copy.deepcopy(body)))
                return 409, {}, {}
            return api(admin, path, method, body)
        with self.assertRaisesRegex(AssertionError, 'publication refused'):
            with self.scope(stale_restore): pass
        self.assertEqual([c[2]['revision'] for c in calls if c[1]=='POST'], [7, 8])
        self.assertEqual(state['configuration']['profiles'][0]['realm'], 'changed-cluster')

    def test_wrong_or_ambiguous_original_profile_refuses_before_publication(self):
        for ambiguous in [False, True]:
            _, state, calls, api = self.owner()
            if ambiguous: state['configuration']['profiles'] *= 2
            else: state['configuration']['profiles'][0]['kubernetes_tokenreview']['connection']['cluster_id'] = 'other'
            with self.assertRaisesRegex(AssertionError, 'selection mismatch'):
                with self.scope(api): self.fail('must not probe')
            self.assertFalse(any(c[1]=='POST' for c in calls))


if __name__=='__main__': unittest.main()
