#!/usr/bin/env python3
"""Owned disposable API-server qualification. Render by default; execution is explicit."""
import argparse, base64, copy, hashlib, http.client, json, os, pathlib, re, secrets, ssl, subprocess, sys, time

PREFIX='sar-qualification-'
IMAGE=re.compile(r'^(registry\.k8s\.io/kube-apiserver|registry\.k8s\.io/etcd)@sha256:[0-9a-f]{64}$')
def check_images(api,etcd,pum):
    if not IMAGE.fullmatch(api) or not api.startswith('registry.k8s.io/kube-apiserver@'):raise ValueError('pinned official API-server digest required')
    if not IMAGE.fullmatch(etcd) or not etcd.startswith('registry.k8s.io/etcd@'):raise ValueError('pinned official etcd digest required')
    if not re.fullmatch(r'[^\s@]+@sha256:[0-9a-f]{64}',pum):raise ValueError('exact Pum candidate digest required')

def _policy_base():
    return {'version':1,'information_classes':['public','restricted'],'services':{'api':{'authorization_context':'kubernetes_api','permissions':['read','write'],'roles':{'reader':{'permissions':['read','write'],'information_classes':['public'],'minimum_aal':0}},'users':{'k8sapi:owned-cluster:reader':['reader']},'networks':[],'require_guard':False}},'resources':{'settings':{'service':'api','information_class':'public','actions':{'get':'read','patch':'write'},'minimum_aal':0}},'kubernetes_authorization':{'version':1,'principals':[{'cluster':'owned-cluster','user':'fixture-reader','uid':{'mode':'absent'},'required_groups':['fixture-readers'],'required_extra':{},'subject':'k8sapi:owned-cluster:reader'}],'routes':[{'cluster':'owned-cluster','attributes':{'kind':'resource','group':'','version':'v1','resource':'configmaps','subresource':'','namespace':'owned-fixture','name':'settings','verb':'get'},'service':'api','resource':'settings','action':'get'}]}}

def policy():
    p=_policy_base();route=copy.deepcopy(p['kubernetes_authorization']['routes'][0]);route['attributes']['verb']='patch';route['action']='patch';p['kubernetes_authorization']['routes'].append(route);return p

def authorization_config():
    return {'apiVersion':'apiserver.config.k8s.io/v1','kind':'AuthorizationConfiguration','authorizers':[{'type':'Webhook','name':'pumgye','webhook':{'authorizedTTL':'1s','unauthorizedTTL':'1s','cacheAuthorizedRequests':False,'cacheUnauthorizedRequests':False,'timeout':'3s','subjectAccessReviewVersion':'v1','matchConditionSubjectAccessReviewVersion':'v1','failurePolicy':'Deny','connectionInfo':{'type':'KubeConfigFile','kubeConfigFile':'/fixture/webhook.json'}}}]}

def certificates(root,namespace):
    def run(*args):subprocess.run(['openssl',*args],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    run('req','-x509','-newkey','rsa:2048','-nodes','-days','2','-subj','/CN=owned-sar-ca','-keyout','ca.key','-out','ca.pem')
    for name,subject,usage,san in [('api','/CN=api.fixture.test','serverAuth','DNS:api.fixture.test,IP:127.0.0.1'),('sar','/CN=sar','serverAuth',f'DNS:sar.{namespace}.svc'),('reviewer','/CN=owned-apiserver','clientAuth','DNS:owned.example.test'),('bootstrap','/CN=fixture-bootstrap/O=system:masters','clientAuth','DNS:owned.example.test'),('reader','/CN=fixture-reader/O=fixture-readers','clientAuth','DNS:owned.example.test'),('unknown','/CN=fixture-unknown/O=fixture-readers','clientAuth','DNS:owned.example.test')]:
        run('req','-new','-newkey','rsa:2048','-nodes','-subj',subject,'-keyout',name+'.key','-out',name+'.csr')
        (root/(name+'.ext')).write_text('basicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage='+usage+'\nsubjectAltName='+san+'\n')
        run('x509','-req','-in',name+'.csr','-CA','ca.pem','-CAkey','ca.key','-CAcreateserial','-days','2','-extfile',name+'.ext','-out',name+'.pem')
    run('genrsa','-out','service-account.key','2048')
    for f in root.iterdir():f.chmod(0o600)

def render(namespace,api_image,etcd_image,pum_image,material):
    if not re.fullmatch(PREFIX+r'[a-z0-9]{8,20}',namespace):raise ValueError('owned namespace prefix/suffix required')
    check_images(api_image,etcd_image,pum_image)
    authority=f'sar.{namespace}.svc:8443'
    files=copy.deepcopy(material)
    fingerprint=hashlib.sha256(ssl.PEM_cert_to_DER_cert(files['reviewer.pem'])).hexdigest()
    files['authorization.json']=json.dumps(authorization_config())
    files['webhook.json']=json.dumps({'apiVersion':'v1','kind':'Config','clusters':[{'name':'sar','cluster':{'server':'https://'+authority+'/v1/kubernetes/subjectaccessreviews','certificate-authority':'/fixture/ca.pem'}}],'users':[{'name':'reviewer','user':{'client-certificate':'/fixture/reviewer.pem','client-key':'/fixture/reviewer.key','token':files['sar-token']}}],'contexts':[{'name':'sar','context':{'cluster':'sar','user':'reviewer'}}],'current-context':'sar'})
    files['sar.json']=json.dumps({'version':1,'listen':'0.0.0.0:8443','cluster':'owned-cluster','authority':authority,'certificate':'/fixture/sar.pem','key':'/fixture/sar.key','client_ca':'/fixture/ca.pem','client_sha256':[fingerprint],'caller_token_env':'SAR_CALLER_TOKEN'})
    files['policy.json']=json.dumps({'revision':1,'policy':policy()})
    # Private CA signing key, bootstrap/ordinary client keys stay LOCAL, never mounted.
    allowed={'ca.pem','api.pem','api.key','sar.pem','sar.key','reviewer.pem','reviewer.key','service-account.key','authorization.json','webhook.json','sar.json','policy.json','sar-token','admin-token','decision-token'}
    secret={'apiVersion':'v1','kind':'Secret','metadata':{'name':'fixture','namespace':namespace},'type':'Opaque','data':{k:base64.b64encode(v.encode()).decode() for k,v in files.items() if k in allowed}}
    security={'runAsNonRoot':True,'runAsUser':65532,'runAsGroup':65532,'fsGroup':65532,'seccompProfile':{'type':'RuntimeDefault'}}
    mount={'name':'fixture','mountPath':'/fixture','readOnly':True}
    def container(name,image,args):return {'name':name,'image':image,'args':args,'securityContext':{'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']},'readOnlyRootFilesystem':True},'volumeMounts':[mount],'resources':{'requests':{'cpu':'50m','memory':'128Mi'},'limits':{'cpu':'2','memory':'1Gi'}}}
    def pod(name,containers,volumes):return {'apiVersion':'v1','kind':'Pod','metadata':{'name':name,'namespace':namespace,'labels':{'owned-sar':name}},'spec':{'automountServiceAccountToken':False,'restartPolicy':'Never','securityContext':security,'containers':containers,'volumes':[{'name':'fixture','secret':{'secretName':'fixture','defaultMode':0o440,'items':[{'key':key,'path':key} for key in (['ca.pem','api.pem','api.key','reviewer.pem','reviewer.key','service-account.key','authorization.json','webhook.json'] if name=='api' else ['ca.pem','sar.pem','sar.key','sar.json','policy.json'])]}},*volumes]}}
    etcd=container('etcd',etcd_image,['--data-dir=/data/etcd','--listen-client-urls=http://127.0.0.1:2379','--advertise-client-urls=http://127.0.0.1:2379','--listen-peer-urls=http://127.0.0.1:2380','--initial-advertise-peer-urls=http://127.0.0.1:2380','--initial-cluster=default=http://127.0.0.1:2380']);etcd['command']=['/usr/local/bin/etcd'];etcd['volumeMounts'].append({'name':'data','mountPath':'/data'})
    api=container('api',api_image,['--bind-address=0.0.0.0','--secure-port=6443','--advertise-address=127.0.0.1','--etcd-servers=http://127.0.0.1:2379','--service-cluster-ip-range=10.249.0.0/24','--tls-cert-file=/fixture/api.pem','--tls-private-key-file=/fixture/api.key','--client-ca-file=/fixture/ca.pem','--anonymous-auth=false','--authorization-config=/fixture/authorization.json','--service-account-key-file=/fixture/service-account.key','--service-account-signing-key-file=/fixture/service-account.key','--service-account-issuer=https://issuer.example.test','--profiling=false','--cert-dir=/data/certs']);api['volumeMounts'].append({'name':'data','mountPath':'/data'})
    api['command']=['/usr/local/bin/kube-apiserver']
    pum=container('pumgye',pum_image,['--listen','127.0.0.1:8080','--database','/data/policy.sqlite3','--policy','/fixture/policy.json','--kubernetes-authorization-config','/fixture/sar.json']);pum['volumeMounts'].append({'name':'data','mountPath':'/data'});pum['env']=[{'name':env,'valueFrom':{'secretKeyRef':{'name':'fixture','key':key}}} for env,key in [('PUMGYE_ADMIN_TOKEN','admin-token'),('PUMGYE_DECISION_TOKEN','decision-token'),('SAR_CALLER_TOKEN','sar-token')]]
    return [{'apiVersion':'v1','kind':'Namespace','metadata':{'name':namespace}},secret,{'apiVersion':'v1','kind':'Service','metadata':{'name':'sar','namespace':namespace},'spec':{'selector':{'owned-sar':'pumgye'},'ports':[{'port':8443,'targetPort':8443}]}},pod('pumgye',[pum],[{'name':'data','emptyDir':{}}]),pod('api',[etcd,api],[{'name':'data','emptyDir':{}}])]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--api-image',required=True);p.add_argument('--etcd-image',required=True);p.add_argument('--pum-image',required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--kubectl');p.add_argument('--backup-evidence',type=pathlib.Path);p.add_argument('--approval',choices=['owned-disposable-only']);p.add_argument('--candidate-evidence',type=pathlib.Path);a=p.parse_args()
    os.umask(0o077);a.output.mkdir(mode=0o700,parents=True,exist_ok=False);ns=PREFIX+secrets.token_hex(6);certificates(a.output,ns)
    material={f.name:f.read_text() for f in a.output.iterdir() if f.suffix in ('.pem','.key')};material.update({k:secrets.token_urlsafe(40) for k in ['sar-token','admin-token','decision-token']})
    docs=render(ns,a.api_image,a.etcd_image,a.pum_image,material);(a.output/'manifest-private.json').write_text(json.dumps({'apiVersion':'v1','kind':'List','items':docs}))
    if a.execute:
        if not a.kubectl or not a.backup_evidence or not a.approval or not a.candidate_evidence:p.error('execution requires kubectl, verified backup evidence and explicit owned approval')
        execute(a,docs,material)
    else:print('Rendered private fixture; no cluster access. '+str(a.output))

def validate_prerequisites(backup,candidate,pum_image):
    # Trusted parent's remote receipt is an attestation, not crypto authority.
    if backup.get('cold_backup') is not True or not 0 <= time.time()-backup.get('completed_unix',0) <= 21600:raise ValueError('fresh cold backup required')
    expected=backup.get('sha256','');size=backup.get('size_bytes');remote=backup.get('remote_verification',{})
    if not re.fullmatch('[0-9a-f]{64}',expected) or not isinstance(size,int) or size<=0:raise ValueError('full backup SHA/size required')
    if remote.get('sha256')!=expected or remote.get('size_bytes')!=size or remote.get('tar_pass') is not True or remote.get('cold_backup') is not True or not remote.get('archive') or not 0 <= time.time()-remote.get('verified_unix',0) <=21600:raise ValueError('matching fresh remote cold verification receipt required')
    path=pathlib.Path(backup['offhost_archive']);h=hashlib.sha256()
    if path.stat().st_size!=size:raise ValueError('offhost backup size mismatch')
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    if h.hexdigest()!=expected:raise ValueError('offhost backup bytes mismatch')
    subprocess.run(['tar','-tzf',str(path)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if candidate.get('image')!=pum_image or candidate.get('version')!='0.1.9' or 'observed-authentication' not in candidate.get('features',[]) or candidate.get('sar_listener') is not True or not re.fullmatch('[0-9a-f]{40}',candidate.get('source','')) or not re.fullmatch('[0-9a-f]{64}',candidate.get('binary_sha256','')):raise ValueError('exact qualified production-feature SAR candidate required')

def uid_delete(kube,path,uid):
    current=json.loads(kube('get','--raw',path))
    if current['metadata']['uid']!=uid:raise ValueError('owned UID changed; refuse deletion')
    options={'apiVersion':'v1','kind':'DeleteOptions','preconditions':{'uid':uid,'resourceVersion':current['metadata']['resourceVersion']}}
    kube('delete','--raw',path,'-f','-',body=options)

def require_runtime_attestation(expected_specs,attestation):
    if set(attestation)!=set(expected_specs):raise ValueError('complete parent runtime image attestation required')
    for name,image in expected_specs.items():
        proof=attestation[name];image_id=proof.get('image_id','')
        if proof.get('image')!=image or not isinstance(image_id,str) or not 1<=len(image_id)<=1024 or any(c.isspace() for c in image_id):raise ValueError('invalid parent image attestation')

def verify_runtime_images(pods,expected_specs,attestation):
    require_runtime_attestation(expected_specs,attestation)
    seen=set();evidence=[]
    for pod in pods:
        specs={c['name']:c['image'] for c in pod['spec']['containers']}
        for status in pod.get('status',{}).get('containerStatuses',[]):
            name=status['name']
            if name not in expected_specs or name in seen:raise ValueError('unexpected runtime container')
            expected=expected_specs[name];proof=attestation[name]
            if specs.get(name)!=expected or proof.get('image')!=expected or not proof.get('image_id') or status.get('imageID')!=proof['image_id']:raise ValueError('runtime image identity mismatch')
            seen.add(name);evidence.append({'container':name,'spec':expected,'image_id':status['imageID']})
    if seen!=set(expected_specs):raise ValueError('runtime container identity missing')
    return evidence

def finalize_evidence(evidence,primary,actions,path):
    # Cleanup failures never replace the original failure or skip later checks.
    evidence['primary_error']=None if primary is None else type(primary).__name__
    errors=[]
    for name,action in actions:
        try:action()
        except BaseException as error:errors.append({'stage':name,'error_type':type(error).__name__})
    evidence['finalization_errors']=errors
    evidence['passed']=bool(evidence.get('passed')) and primary is None and not errors
    path.write_text(json.dumps(evidence,indent=2))
    if primary is None and errors:raise RuntimeError('cleanup/baseline incomplete; private evidence preserved')

def execute(a,docs,material):
    candidate=json.loads(a.candidate_evidence.read_text())
    validate_prerequisites(json.loads(a.backup_evidence.read_text()),candidate,a.pum_image)
    pins=json.loads(pathlib.Path(__file__).with_name('kubernetes_sar_images.json').read_text())
    if a.api_image!='registry.k8s.io/kube-apiserver@'+pins['kube-apiserver']['linux_amd64_digest'] or a.etcd_image!='registry.k8s.io/etcd@'+pins['etcd']['linux_amd64_digest']:raise ValueError('execution requires reviewed official platform digests')
    require_runtime_attestation({'api':a.api_image,'etcd':a.etcd_image,'pumgye':a.pum_image},candidate.get('runtime_images',{}))
    namespace=docs[0]['metadata']['name'];owned_uid=None;forwards=[];evidence={'passed':False,'namespace':namespace,'checks':[],'images':{'api':a.api_image,'etcd':a.etcd_image,'pum':a.pum_image}}
    def kube(*args,body=None):
        raw=None if body is None else json.dumps(body).encode()
        r=subprocess.run([a.kubectl,*args],input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
        if r.returncode:
            (a.output/('kubectl-failure-'+secrets.token_hex(4)+'.log')).write_bytes(r.stderr)
            raise RuntimeError('kubectl operation failed; diagnostics preserved privately')
        return r.stdout
    baseline=json.loads(kube('get','pods','-A','-o','json'));nodes=json.loads(kube('get','nodes','-o','json'))
    if len(nodes['items'])!=2 or not all(any(c['type']=='Ready' and c['status']=='True' for c in n['status']['conditions']) for n in nodes['items']):raise ValueError('expected two Ready nodes')
    if any(p['metadata']['namespace']==namespace for p in baseline['items']):raise ValueError('namespace collision')
    def require_owner():
        actual=json.loads(kube('get','namespace',namespace,'-o','json'))
        if actual['metadata']['uid']!=owned_uid:raise ValueError('namespace owner replaced')
    def create(obj):
        require_owner();return json.loads(kube('create','-f','-','-o','json',body=obj))
    def forward(pod,remote):
        import socket
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        log=(a.output/('forward-'+pod+'-'+str(remote)+'.log')).open('ab')
        process=subprocess.Popen([a.kubectl,'-n',namespace,'port-forward','--address','127.0.0.1','pod/'+pod,str(port)+':'+str(remote)],stdout=log,stderr=log);forwards.append((process,log))
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('owned port-forward failed')
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.2):return port
            except OSError:time.sleep(.1)
        raise RuntimeError('owned port-forward timeout')
    def api(port,who,method,path,payload=None):
        context=ssl.create_default_context(cafile=str(a.output/'ca.pem'));context.load_cert_chain(str(a.output/(who+'.pem')),str(a.output/(who+'.key')))
        c=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=12)
        c.request(method,path,None if payload is None else json.dumps(payload),{'Content-Type':'application/merge-patch+json' if method=='PATCH' else 'application/json'});r=c.getresponse();data=r.read();c.close();return r.status,data
    def eventually(fn,seconds=90):
        end=time.monotonic()+seconds
        while True:
            try:
                result=fn()
                if result:return result
            except (OSError,http.client.HTTPException):pass
            if time.monotonic()>end:raise RuntimeError('owned readiness deadline')
            time.sleep(.3)
    try:
        # Atomic create, never apply/adopt an existing namespace.
        owned_uid=json.loads(kube('create','-f','-','-o','json',body=docs[0]))['metadata']['uid'];evidence['namespace_uid']=owned_uid
        for obj in docs[1:]:create(obj)
        api_port=forward('api',6443);pum_port=forward('pumgye',8080)
        bootstrap=[('/api/v1/namespaces',{'apiVersion':'v1','kind':'Namespace','metadata':{'name':'owned-fixture'}}),('/api/v1/namespaces/owned-fixture/configmaps',{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'settings'},'data':{'counter':'unchanged'}})]
        for path,obj in bootstrap:
            def boot():
                status,_=api(api_port,'bootstrap','POST',path,obj)
                if status==201:return True
                if status in (500,503):return False
                raise RuntimeError('bootstrap create refused')
            eventually(boot)
        evidence['runtime_image_ids']=verify_runtime_images(json.loads(kube('-n',namespace,'get','pods','-o','json'))['items'],{'api':a.api_image,'etcd':a.etcd_image,'pumgye':a.pum_image},candidate.get('runtime_images',{}))
        path='/api/v1/namespaces/owned-fixture/configmaps/settings'
        revision=1
        def publish(value):
            nonlocal revision
            c=http.client.HTTPConnection('127.0.0.1',pum_port,timeout=5);c.request('PUT','/v1/policy',json.dumps({'revision':revision,'policy':value}),{'Authorization':'Bearer '+material['admin-token'],'If-Match':'"'+str(revision)+'"','Content-Type':'application/json'});r=c.getresponse();r.read();c.close()
            if r.status!=200:raise RuntimeError('native owning CAS failed')
            revision+=1
        def expect(name,who='reader',method='GET',request_path=path,allowed=False):
            status,data=api(api_port,who,method,request_path,{'data':{'counter':'MUTATED'}} if method=='PATCH' else None)
            if allowed:
                if status!=200 or json.loads(data).get('data')!={'counter':'unchanged'}:raise AssertionError(name)
            elif status==200:raise AssertionError(name)
            elif status not in (403,500,503):raise AssertionError(name+' unexpected HTTP status')
            evidence['checks'].append({'name':name,'status':status})
        expect('native-allow',allowed=True);expect('unknown-user',who='unknown');expect('unknown-resource',request_path=path+'-unknown')
        def patch(value,allowed):
            status,_=api(api_port,'reader','PATCH',path,{'data':{'counter':value}})
            if status!=(200 if allowed else 403):raise AssertionError('mapped PATCH permission mismatch')
            evidence['checks'].append({'name':'mapped-patch-allow' if allowed else 'mapped-patch-denied','status':status})
        def counter(expected):
            status,data=api(api_port,'bootstrap','GET',path)
            if status!=200 or json.loads(data).get('data')!={'counter':expected}:raise AssertionError('backend side effect mismatch')
        patch('first',True);counter('first')
        denied_write=policy();denied_write['services']['api']['users']={};publish(denied_write);patch('MUST-NOT-APPLY',False);counter('first')
        publish(policy());patch('second',True);counter('second');patch('unchanged',True)
        evidence['checks'].append({'name':'actual-mapped-patch-withdraw-no-backend-change-reallow','passed':True})
        denied=policy();denied['services']['api']['users']={};publish(denied);expect('grant-withdraw');publish(policy());expect('native-reallow',allowed=True)
        denied=policy();denied['services']['api']['roles']['reader']['minimum_aal']=1;publish(denied);expect('role-aal-deny');publish(policy())
        denied=policy();denied['resources']['settings']['information_class']='restricted';publish(denied);expect('class-deny');publish(policy());expect('class-recovery',allowed=True)
        require_owner();pum=json.loads(kube('-n',namespace,'get','pod','pumgye','-o','json'));uid_delete(kube,'/api/v1/namespaces/'+namespace+'/pods/pumgye',pum['metadata']['uid'])
        eventually(lambda:not json.loads(kube('-n',namespace,'get','pods','-o','json'))['items'] or all(x['metadata']['name']!='pumgye' for x in json.loads(kube('-n',namespace,'get','pods','-o','json'))['items']))
        expect('pum-outage-failclosed');create(docs[3]);eventually(lambda:api(api_port,'reader','GET',path)[0]==200);evidence['recovery_runtime_image_ids']=verify_runtime_images(json.loads(kube('-n',namespace,'get','pods','-o','json'))['items'],{'api':a.api_image,'etcd':a.etcd_image,'pumgye':a.pum_image},candidate.get('runtime_images',{}));expect('outage-recovery-and-backend-unchanged',allowed=True)
        evidence['passed']=True
    finally:
        primary=sys.exc_info()[1]
        def stop_forward(process,log):
            try:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
            finally:log.close()
        def cleanup():
            if owned_uid:
                uid_delete(kube,'/api/v1/namespaces/'+namespace,owned_uid)
                eventually(lambda:all(n['metadata']['name']!=namespace for n in json.loads(kube('get','namespaces','-o','json'))['items']))
                evidence['cleanup_uid_precondition']=True
        def pod_baseline():
            after=json.loads(kube('get','pods','-A','-o','json'));old={x['metadata']['uid'] for x in baseline['items']};now={x['metadata']['uid'] for x in after['items']}
            evidence['original_pod_uids_preserved']=old<=now
            if not old<=now:raise RuntimeError('original Pod identity changed')
        def node_baseline():
            nodes=json.loads(kube('get','nodes','-o','json'));ready=len(nodes['items'])==2 and all(any(c['type']=='Ready' and c['status']=='True' for c in n['status']['conditions']) for n in nodes['items']);evidence['nodes_ready']=ready
            if not ready:raise RuntimeError('node baseline changed')
        actions=[('forward-stop-'+str(i),lambda process=process,log=log:stop_forward(process,log)) for i,(process,log) in enumerate(forwards)]
        actions.extend([('owned-cleanup',cleanup),('pod-baseline',pod_baseline),('node-baseline',node_baseline)])
        finalize_evidence(evidence,primary,actions,a.output/'result.json')

if __name__=='__main__':main()
