import copy,hashlib,json,pathlib,tarfile,tempfile,time,unittest
from unittest.mock import Mock
import kubernetes_sar_qualification as q

class QualificationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=pathlib.Path(cls.temp.name);q.certificates(cls.root,'sar-qualification-abcdef123456')
  cls.material={p.name:p.read_text() for p in cls.root.iterdir() if p.suffix in ('.pem','.key')};cls.material.update({'sar-token':'s'*40,'admin-token':'a'*40,'decision-token':'d'*40})
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def render(self):return q.render('sar-qualification-abcdef123456','registry.k8s.io/kube-apiserver@sha256:'+'a'*64,'registry.k8s.io/etcd@sha256:'+'b'*64,'owned/pumgye@sha256:'+'c'*64,self.material)
 def test_authorization_failclosed_cache_disabled_not_invalid_ttl(self):
  a=q.authorization_config();w=a['authorizers'][0]['webhook'];self.assertEqual(a['apiVersion'],'apiserver.config.k8s.io/v1');self.assertEqual(w['failurePolicy'],'Deny');self.assertFalse(w['cacheAuthorizedRequests']);self.assertFalse(w['cacheUnauthorizedRequests']);self.assertNotEqual(w['authorizedTTL'],'0s');self.assertEqual(w['subjectAccessReviewVersion'],'v1');self.assertEqual(len(a['authorizers']),1)
 def test_only_owned_namespaced_nonprivileged_objects_no_rbac_or_host(self):
  docs=self.render();self.assertEqual([d['kind'] for d in docs],['Namespace','Secret','Service','Pod','Pod'])
  for d in docs[1:]:self.assertEqual(d['metadata']['namespace'],docs[0]['metadata']['name'])
  for pod in docs[3:]:
   self.assertFalse(pod['spec'].get('hostNetwork',False));self.assertFalse(pod['spec']['automountServiceAccountToken']);self.assertTrue(pod['spec']['securityContext']['runAsNonRoot'])
   for c in pod['spec']['containers']:self.assertFalse(c['securityContext']['allowPrivilegeEscalation']);self.assertEqual(c['securityContext']['capabilities']['drop'],['ALL'])
   self.assertFalse(any('hostPath' in v or 'persistentVolumeClaim' in v for v in pod['spec']['volumes']))
 def test_no_bootstrap_or_reader_private_key_uploaded(self):
  data=self.render()[1]['data'];self.assertNotIn('ca.key',data)
  for who in ['bootstrap','reader','unknown']:self.assertNotIn(who+'.key',data);self.assertNotIn(who+'.pem',data)
 def test_policy_no_network_or_workload_fallback_and_exact_uid_absent(self):
  p=q.policy();s=p['services']['api'];self.assertEqual(s['authorization_context'],'kubernetes_api');self.assertFalse(s['require_guard']);self.assertEqual(s['networks'],[]);self.assertNotIn('workload_users',s);m=p['kubernetes_authorization']['principals'][0];self.assertEqual(m['uid'],{'mode':'absent'});self.assertNotIn('system:masters',m['required_groups']);self.assertEqual(m['user'],'fixture-reader')
 def test_named_patch_is_mapped_to_same_native_resource_write_permission(self):
  p=q.policy();routes=p['kubernetes_authorization']['routes'];self.assertEqual({r['attributes']['verb'] for r in routes},{'get','patch'});self.assertEqual({r['resource'] for r in routes},{'settings'});self.assertEqual(p['resources']['settings']['actions']['patch'],'write');self.assertIn('write',p['services']['api']['roles']['reader']['permissions'])
 def test_pod_secret_projections_exclude_other_owner_credentials(self):
  docs=self.render();api=docs[4]['spec']['volumes'][0]['secret']['items'];pum=docs[3]['spec']['volumes'][0]['secret']['items'];self.assertNotIn('sar.key',[x['key'] for x in api]);self.assertNotIn('reviewer.key',[x['key'] for x in pum]);self.assertNotIn('admin-token',[x['key'] for x in api])
 def test_floating_nonofficial_digest_and_wrong_namespace_refuse(self):
  for api in ['registry.k8s.io/kube-apiserver:v1.37.1','evil.test/kube-apiserver@sha256:'+'a'*64]:
   with self.assertRaises(ValueError):q.check_images(api,'registry.k8s.io/etcd@sha256:'+'b'*64,'owned/pum@sha256:'+'c'*64)
  with self.assertRaises(ValueError):q.render('default','x','y','z',self.material)
 def test_cleanup_atomic_uid_and_resourceversion_preconditions(self):
  kube=Mock(return_value=json.dumps({'metadata':{'uid':'owned','resourceVersion':'42'}}).encode());q.uid_delete(kube,'/api/v1/namespaces/owned','owned');self.assertEqual(kube.call_args.kwargs['body']['preconditions'],{'uid':'owned','resourceVersion':'42'})
 def test_cleanup_replacement_never_deleted(self):
  kube=Mock(return_value=json.dumps({'metadata':{'uid':'replacement','resourceVersion':'42'}}).encode())
  with self.assertRaises(ValueError):q.uid_delete(kube,'/api/v1/namespaces/owned','old')
  self.assertEqual(kube.call_count,1)
 def test_missing_or_stale_backup_fails_before_any_cluster_action(self):
  for b in [{},{'cold_backup':True,'completed_unix':0}]:
   with self.assertRaises(ValueError):q.validate_prerequisites(b,{},'owned/pum@sha256:'+'a'*64)

 def test_management_is_loopback_sar_is_verified_public_listener(self):
  docs=self.render();args=docs[3]['spec']['containers'][0]['args'];self.assertEqual(args[args.index('--listen')+1],'127.0.0.1:8080')
  import base64
  self.assertEqual(json.loads(base64.b64decode(docs[1]['data']['sar.json']))['listen'],'0.0.0.0:8443')
 def test_primary_failure_preserved_all_cleanup_steps_run_and_result_written(self):
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d)/'result.json';ran=[];primary=AssertionError('private original')
   def bad():ran.append('cleanup');raise ValueError('private cleanup')
   def baseline():ran.append('baseline')
   q.finalize_evidence({'passed':True},primary,[('cleanup',bad),('baseline',baseline)],path)
   v=json.loads(path.read_text());self.assertFalse(v['passed']);self.assertEqual(v['primary_error'],'AssertionError');self.assertEqual(ran,['cleanup','baseline']);self.assertEqual(v['finalization_errors'][0]['stage'],'cleanup');self.assertNotIn('private',path.read_text())
 def test_cleanup_failure_alone_prevents_success_but_preserves_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d)/'result.json'
   def bad():raise RuntimeError()
   with self.assertRaises(RuntimeError):q.finalize_evidence({'passed':True},None,[('baseline',bad)],path)
   self.assertFalse(json.loads(path.read_text())['passed'])
 def test_runtime_image_wrong_id_spec_or_missing_container_refuses(self):
  specs={'api':'official@sha256:'+'a'*64};att={'api':{'image':specs['api'],'image_id':'containerd://verified'}};pods=[{'spec':{'containers':[{'name':'api','image':specs['api']}]},'status':{'containerStatuses':[{'name':'api','imageID':'containerd://verified'}]}}]
  self.assertEqual(len(q.verify_runtime_images(pods,specs,att)),1)
  for mutate in ['id','spec','missing']:
   bad=copy.deepcopy(pods)
   if mutate=='id':bad[0]['status']['containerStatuses'][0]['imageID']='containerd://other'
   elif mutate=='spec':bad[0]['spec']['containers'][0]['image']='other'
   else:bad[0]['status']['containerStatuses']=[]
   with self.assertRaises(ValueError):q.verify_runtime_images(bad,specs,att)
 def test_remote_receipt_single_local_copy_validates_and_mismatch_refuses(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'payload').write_text('fixture')
   with tarfile.open(root/'backup.tgz','w:gz') as t:t.add(root/'payload',arcname='payload')
   archive=root/'backup.tgz';sha=hashlib.sha256(archive.read_bytes()).hexdigest();size=archive.stat().st_size
   receipt={'cold_backup':True,'completed_unix':time.time(),'sha256':sha,'size_bytes':size,'offhost_archive':str(archive),'remote_verification':{'archive':'remote/private/backup.tgz','cold_backup':True,'verified_unix':time.time(),'sha256':sha,'size_bytes':size,'tar_pass':True}}
   candidate={'image':'owned@sha256:'+'a'*64,'version':'0.1.9','features':['observed-authentication'],'sar_listener':True,'source':'a'*40,'binary_sha256':'b'*64}
   q.validate_prerequisites(receipt,candidate,candidate['image'])
   for field,value in [('sha256','f'*64),('size_bytes',size+1),('tar_pass',False)]:
    bad=copy.deepcopy(receipt);bad['remote_verification'][field]=value
    with self.assertRaises(ValueError):q.validate_prerequisites(bad,candidate,candidate['image'])

 def test_private_diagnostics_only_owned_pods_and_no_secret_reads(self):
  calls=[]
  def kube(*args):
   calls.append(args)
   if args[:2]==('get','namespace'):return json.dumps({'metadata':{'uid':'ns-owned'}}).encode()
   if 'logs' in args:return b'bounded fixture startup failure'
   return json.dumps({'metadata':{'uid':'pod-owned'},'spec':{'containers':[{'name':'api'}]},'status':{'phase':'Pending'}}).encode()
  with tempfile.TemporaryDirectory() as d:
   out=pathlib.Path(d);q.collect_diagnostics(kube,'owned','ns-owned',{'api':'pod-owned'},out)
   self.assertTrue((out/'pod-api-api-private.log').exists());self.assertTrue((out/'pod-status-private.json').exists())
  self.assertFalse(any('secret' in ' '.join(c).lower() for c in calls));self.assertTrue(all('owned' in c for c in calls))
 def test_diagnostic_failure_does_not_skip_cleanup_or_mask_primary(self):
  calls=[]
  def kube(*args):
   if args[:2]==('get','namespace'):return json.dumps({'metadata':{'uid':'ns-owned'}}).encode()
   if 'logs' in args:raise RuntimeError('fixture log read failure')
   return json.dumps({'metadata':{'uid':'pod-owned'},'spec':{'containers':[{'name':'api'}]},'status':{}}).encode()
  with tempfile.TemporaryDirectory() as d:
   out=pathlib.Path(d);e={'passed':True}
   q.finalize_evidence(e,AssertionError(),[('diagnostics',lambda:q.collect_diagnostics(kube,'owned','ns-owned',{'api':'pod-owned'},out)),('cleanup',lambda:calls.append('cleanup')),('baseline',lambda:calls.append('baseline'))],out/'result.json')
   self.assertEqual(calls,['cleanup','baseline']);self.assertEqual(e['primary_error'],'AssertionError');self.assertFalse(e['passed']);self.assertEqual(e['finalization_errors'][0]['stage'],'diagnostics');self.assertTrue((out/'pod-status-private.json').exists())
 def test_replaced_namespace_refuses_diagnostics_without_pod_or_logs(self):
  kube=Mock(return_value=json.dumps({'metadata':{'uid':'replacement'}}).encode())
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):q.collect_diagnostics(kube,'owned','old',{'api':'pod'},pathlib.Path(d))
  self.assertEqual(kube.call_count,1)

 def test_pod_running_requires_all_containers_not_merely_phase(self):
  pod={'spec':{'containers':[{'name':'api'},{'name':'etcd'}]},'status':{'phase':'Pending','containerStatuses':[]}}
  self.assertFalse(q.pod_running(pod));pod['status']['phase']='Running';self.assertFalse(q.pod_running(pod));pod['status']['containerStatuses']=[{'name':'api','state':{'waiting':{}}},{'name':'etcd','state':{'running':{}}}];self.assertFalse(q.pod_running(pod));pod['status']['containerStatuses'][0]['state']={'running':{}};self.assertTrue(q.pod_running(pod))
 def test_startup_poll_waits_before_forward_with_original_ten_second_bound(self):
  good={'spec':{'containers':[{'name':'api'}]},'status':{'phase':'Running','containerStatuses':[{'name':'api','state':{'running':{}}}]}}
  values=iter([{'spec':good['spec'],'status':{'phase':'Pending'}},good]);reads=[]
  def read():reads.append(1);return next(values)
  q.wait_pod_running(read,lambda:True,now=lambda:0,sleep=lambda _:None);self.assertEqual(len(reads),2)
  times=iter([0,10])
  with self.assertRaises(RuntimeError):q.wait_pod_running(lambda:{},lambda:True,now=lambda:next(times),sleep=lambda _:None)
 def test_derived_api_requires_exact_official_binary_and_fixed_namespace(self):
  from build_sar_apiserver_image import OFFICIAL,LAYER,BINARY_SHA
  image='docker.io/sar-qualification/kube-apiserver@sha256:'+'a'*64
  proof={'kind':'reviewed-capability-free-apiserver','official_image':OFFICIAL,'official_layer':LAYER,'official_binary_sha256':BINARY_SHA,'final_binary_sha256':BINARY_SHA,'staged_capability_absent':True,'final_capability_absent':True,'local_constrained_exec_version':'Kubernetes v1.37.1','image':image,'config_id':'sha256:'+'b'*64}
  q.validate_derived_api(image,proof)
  for key,value in [('final_binary_sha256','f'*64),('final_capability_absent',False),('official_image','evil'),('local_constrained_exec_version','unknown')]:
   bad=copy.deepcopy(proof);bad[key]=value
   with self.assertRaises(ValueError):q.validate_derived_api(image,bad)
  with self.assertRaises(ValueError):q.validate_derived_api(image.replace('sar-qualification','arbitrary'),proof)

 def test_api_advertises_actual_pod_ip_without_shell_or_host_network(self):
  pod=self.render()[4];api=next(c for c in pod['spec']['containers'] if c['name']=='api')
  self.assertIn('--advertise-address=$(POD_IP)',api['args']);self.assertNotIn('--advertise-address=127.0.0.1',api['args'])
  self.assertEqual(api['env'],[{'name':'POD_IP','valueFrom':{'fieldRef':{'fieldPath':'status.podIP'}}}]);self.assertEqual(api['command'],['/usr/local/bin/kube-apiserver']);self.assertFalse(pod['spec'].get('hostNetwork',False));self.assertFalse(api['securityContext']['allowPrivilegeEscalation']);self.assertEqual(api['securityContext']['capabilities']['drop'],['ALL']);self.assertIn('--tls-cert-file=/fixture/api.pem',api['args'])

if __name__=='__main__':unittest.main()
