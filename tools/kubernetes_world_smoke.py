#!/usr/bin/env python3
"""Owned four-service Kubernetes request enforcement fixture, explicit kubeconfig wrapper."""
import argparse
import base64
import hashlib
import http.client
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import socket
import ssl
import struct
import subprocess
import tempfile
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--kubectl',required=True,type=Path)
    parser.add_argument('--hopae-fixture',required=True,type=Path)
    for name in ['hangang','hopae','sumunjang','pumgye']:parser.add_argument('--'+name+'-image',required=True)
    parser.add_argument('--echo-image',required=True)
    parser.add_argument('--sumunjang-plugin',required=True,type=Path)
    parser.add_argument('--hopae-plugin',type=Path)
    parser.add_argument('--browser-probe',type=Path)
    parser.add_argument('--node-binary',type=Path)
    parser.add_argument('--resource-catalog',action='store_true')
    parser.add_argument('--receipt-client',type=Path)
    parser.add_argument('--authenticated-client',type=Path)
    parser.add_argument('--native-resource',action='store_true')
    args=parser.parse_args()
    if args.native_resource and not args.authenticated_client:
        parser.error('native resource requires authenticated client qualification')
    if args.authenticated_client and not (args.receipt_client and args.resource_catalog):
        parser.error('authenticated client requires receipt client and resource catalog')
    for component in ['hangang','hopae','sumunjang','pumgye','echo']:
        image=getattr(args,component+'_image')
        if '@' in image and not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}',image):
            parser.error(component+' image requires a canonical SHA-256 digest')
    wrapper=args.kubectl.resolve(strict=True)
    node=str(args.node_binary.resolve(strict=True)) if args.node_binary else shutil.which('node')
    if args.browser_probe and not node:parser.error('browser probe requires --node-binary when node is not in PATH')
    namespace='owned-world-'+secrets.token_hex(6);created=False;forwards=[]
    os.umask(0o077)
    def kube(*argv,body=None,timeout=120):
        result=subprocess.run([str(wrapper),*argv],input=body,capture_output=True,timeout=timeout)
        if result.returncode:raise RuntimeError('owned Kubernetes operation failed: '+argv[0])
        return result.stdout
    def port():
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='world-owned-pods-') as temporary:
        root=Path(temporary)
        def openssl(*argv):subprocess.run(['openssl',*map(str,argv)],check=True,capture_output=True)
        openssl('req','-x509','-newkey','rsa:2048','-nodes','-keyout',root/'ca.key','-out',root/'ca.pem','-days','1','-subj','/CN=Owned world CA','-addext','basicConstraints=critical,CA:TRUE')
        for name,usage in [('server','serverAuth'),('client','clientAuth')]:
            openssl('req','-new','-newkey','rsa:2048','-nodes','-keyout',root/f'{name}.key','-out',root/f'{name}.csr','-subj',f'/CN={name}')
            ext=root/f'{name}.ext';ext.write_text('basicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage='+usage+'\nsubjectAltName='+','.join('DNS:'+c+'.'+namespace+'.svc' for c in ['hangang','hopae','sumunjang','pumgye'])+',DNS:app.example.test,IP:127.0.0.1\n')
            openssl('x509','-req','-in',root/f'{name}.csr','-CA',root/'ca.pem','-CAkey',root/'ca.key','-CAcreateserial','-days','1','-extfile',ext,'-out',root/f'{name}.pem')
        tokens={name:secrets.token_hex(32) for name in ['api','caller','gateway-admin','guard-collector','guard-admin','pum-decision','pum-admin','hopae-delegation']}
        def tls(name):return {'server_name':name+'.'+namespace+'.svc','ca':'/tls/ca.crt','certificate':'/tls/client.crt','key':'/tls/client.key'}
        digest=hashlib.sha256(bytes([1]))
        for value in ['hopae:owned','services','worker']:
            value=value.encode();digest.update(struct.pack('!Q',len(value)));digest.update(value)
        subject='s_'+digest.hexdigest()[:48]
        hop=json.loads(args.hopae_fixture.read_text());hop['providers']=[];hop['state_dir']='/state'
        hop['listen']={'portal':'0.0.0.0:8700','gateway':'127.0.0.1:8701','grpc_gateway':'0.0.0.0:8703','native_gateway_tls':{'certificate':'/tls/tls.crt','key':'/tls/tls.key','client_ca':'/tls/ca.crt'}}
        if args.hopae_plugin:
            hop['listen']['admin']='0.0.0.0:8702'
            hop['listen']['admin_tls']={'certificate':'/tls/tls.crt','key':'/tls/tls.key','client_ca':'/tls/ca.crt'}
            hop['admin']={'public_url':'https://admin.example.test','hangang_delegation':{'authority':'hangang','key_env':'HOPAE_CONSOLE_DELEGATION_KEY'}}
        hop['apps'][0].update(app_id='orders',ports=[8443])
        hop['authentication_gateway']={'authority_id':'owned','profiles':[{'service_id':'orders','host':'app.example.test','ports':[8443],'realm':'services','api_keys':[{'token_env':'OWNED_API_KEY','subject':'worker'}],'networks':['127.0.0.1/32']}]}
        policy={'version':1,'information_classes':['internal'],'services':{'orders':{'permissions':['read','write'],'require_guard':True,'roles':{'reader':{'permissions':['read'],'information_classes':['internal'],'minimum_aal':0}},'users':{subject:['reader']},'networks':[{'cidr':'127.0.0.1/32','roles':['reader']}]}}}
        gateway={'http':[{'id':'orders','host':'app.example.test','path_prefix':'/secure','access_mode':'protected','backends':[f'http://echo.{namespace}.svc:8080'],'auth':{'url':'http://127.0.0.1:8701/_hopae/verify','native':{'transport':'grpc','address':f'hopae.{namespace}.svc:8703','tls':tls('hopae')},'request_headers':['authorization'],'response_headers':['x-forwarded-user','x-hopae-aal','x-hopae-principal-kind'],'static_request_headers':{'x-hopae-gateway-key':{'env':'FIXTURE_KEY'},'x-hopae-contract':'1'},'forward_response':True},'resource_policy':{'resource_id':'orders','principal':{'source':'external','subject_header':'x-forwarded-user'},'allow':[],'pumgye':{'service_id':'orders','information_class':'internal','permissions':{'GET':['read'],'POST':['write']}}}}],'pumgye_authority':{'transport':'grpc','decision_address':f'pumgye.{namespace}.svc:9087','management_address':f'pumgye.{namespace}.svc:9084','decision_token_env':'PUMGYE_DECISION_TOKEN','admin_token_env':'PUMGYE_ADMIN_TOKEN','tls':tls('pumgye'),'timeout_ms':1000}}
        if args.resource_catalog:
            policy['information_classes'].append('restricted')
            policy['services']['billing']=json.loads(json.dumps(policy['services']['orders']))
            policy['resources']={'db:orders':{'service':'orders','information_class':'internal','actions':{'select':'read','update':'write'},'minimum_aal':0}}
            route=gateway['http'][0]['resource_policy'];route.pop('pumgye');route['pumgye_resource']={'service_id':'orders','resource':'db:orders','actions':{'GET':'select','POST':'update'}}
        if args.receipt_client:
            openssl('genpkey','-algorithm','ED25519','-out',root/'receipt-issuer.pem')
            seed=subprocess.check_output(['openssl','pkey','-in',str(root/'receipt-issuer.pem'),'-outform','DER'],stderr=subprocess.DEVNULL)
            public_key=subprocess.check_output(['openssl','pkey','-in',str(root/'receipt-issuer.pem'),'-pubout','-outform','DER'],stderr=subprocess.DEVNULL)
            assert len(seed)==48 and len(public_key)==44
            tokens['receipt-seed']=base64.b64encode(seed[-32:]).decode()
            receipt_pin=base64.b64encode(public_key[-32:]).decode()
            hop['receipt_issuer']={'issuer_ref':'owned-world','key_epoch':1,'identity_authority_epoch':'world1','public_key':receipt_pin,'seed_env':'OWNED_RECEIPT_SEED','scopes':[{'service':'orders','audience':'orders-api'}]}
        if args.native_resource:
            gateway['http'][0]['auth']['native_resource']={'issuer_ref':'owned-world','key_epoch':1,'public_key':receipt_pin,'audience':'orders-api'}
            gateway['http'][0]['backends'][0]+='/api'
        items=[]
        def resource(kind,name,**fields):
            obj={'apiVersion':'v1','kind':kind,'metadata':{'name':name,'namespace':namespace,'labels':{'app.kubernetes.io/part-of':'owned-hangang-world'}},**fields};items.append(obj);return obj
        config_map=resource('ConfigMap','world-config',data={'hopae.json':json.dumps(hop),'hangang.json':json.dumps(gateway),'pumgye.json':json.dumps({'revision':0,'policy':policy}),'sumunjang.json':json.dumps({'mode':'enforce','allow':[]})})
        if args.authenticated_client:
            config_map['data']['authentication-trust.json']=json.dumps({'entries':[{'issuer_ref':'owned-world','key_epoch':1,'identity_epoch':'world1','service':'orders','audience':'orders-api','minimum_revision':1,'public_key':receipt_pin}]})
            native_tls={'ca':'/tls/ca.crt','certificate':'/tls/client.crt','key':'/tls/client.key'}
            config_map['data']['authentication-live.json']=json.dumps(dict(native_tls,issuer_ref='owned-world',address=f'https://hopae.{namespace}.svc:8703',server_name=f'hopae.{namespace}.svc',token_env='HOPAE_TEST_GATEWAY_KEY'))
            config_map['data']['network-live.json']=json.dumps(dict(native_tls,address=f'https://sumunjang.{namespace}.svc:9082',server_name=f'sumunjang.{namespace}.svc',token_env='HANGANG_GUARD_COLLECTOR_TOKEN'))
        manifest_bytes=(args.sumunjang_plugin/'manifest.json').read_bytes()
        manifest=json.loads(manifest_bytes);plugin_id=manifest['id']
        config_map['data']['plugin.manifest.json']=manifest_bytes.decode()
        for name,digest_value in manifest['assets'].items():
            assert re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*',name),'invalid owned plugin asset name'
            asset=(args.sumunjang_plugin/name).read_bytes()
            assert hashlib.sha256(asset).hexdigest()==digest_value,'owned plugin digest mismatch'
            config_map['data']['plugin.'+name]=asset.decode()
        binding={'id':plugin_id,'directory':'/state/plugins','manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'backend':f'https://sumunjang.{namespace}.svc:9080','token_env':'HANGANG_GUARD_ADMIN_TOKEN','tls':tls('sumunjang')}
        config_map['data']['plugins.json']=json.dumps({'plugins':[binding],'audit_database':'/state/admin/plugin-audit.sqlite3'})
        hop_copies=[]
        if args.hopae_plugin:
            raw=(args.hopae_plugin/'manifest.json').read_bytes();hop_manifest=json.loads(raw)
            assert hop_manifest['id']=='hopae'
            config_map['data']['hopae.manifest.json']=raw.decode()
            for asset_name,expected in hop_manifest['assets'].items():
                assert re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*',asset_name)
                content=(args.hopae_plugin/asset_name).read_bytes();assert hashlib.sha256(content).hexdigest()==expected
                config_map['data']['hopae.'+asset_name]=content.decode()
                hop_copies.append('cp /config/hopae.'+asset_name+' /state/hopae-plugin/'+asset_name)
            plugins=json.loads(config_map['data']['plugins.json'])
            plugins['plugins'].append({'id':'hopae','directory':'/state/hopae-plugin','manifest_sha256':hashlib.sha256(raw).hexdigest(),'backend':f'https://hopae.{namespace}.svc:8702','token_env':'HOPAE_CONSOLE_DELEGATION_KEY','delegate_actor':True,'delegation_authority':'hangang','tls':tls('hopae')})
            config_map['data']['plugins.json']=json.dumps(plugins)
        resource('Secret','world-credentials',stringData=tokens)
        resource('Secret','world-tls',stringData={'tls.crt':(root/'server.pem').read_text(),'tls.key':(root/'server.key').read_text(),'ca.crt':(root/'ca.pem').read_text(),'client.crt':(root/'client.pem').read_text(),'client.key':(root/'client.key').read_text()})
        def env(name,key):return {'name':name,'valueFrom':{'secretKeyRef':{'name':'world-credentials','key':key}}}
        commands={
            'hopae':['run','--config','/config/hopae.json'],
            'pumgye':['--listen','0.0.0.0:9084','--decision-listen','0.0.0.0:9085','--grpc-listen','0.0.0.0:9087','--readiness-listen','0.0.0.0:9086','--database','/state/pumgye.sqlite3','--policy','/config/pumgye.json','--tls-cert','/tls/tls.crt','--tls-key','/tls/tls.key','--client-ca','/tls/ca.crt'],
            'sumunjang':['--management-tls','--listen','0.0.0.0:9080','--decision-listen','0.0.0.0:9081','--grpc-listen','0.0.0.0:9082','--database','/state/sumunjang.sqlite3','--bootstrap-policy','/config/sumunjang.json','--decision-tls-cert','/tls/tls.crt','--decision-tls-key','/tls/tls.key','--decision-client-ca','/tls/ca.crt','--threads','2'],
            'hangang':['--config','/config/hangang.json','--database','sqlite:/state/hangang.sqlite3','--docker-connection-state','/state/docker-connections.json','--admin-users-db','/state/admin/admin-users.sqlite3','--admin-plugins','/state/plugins.json','--listen','0.0.0.0:8443','--admin','127.0.0.1:9080','--tls-cert','/tls/tls.crt','--tls-key','/tls/tls.key','--threads','2','--lua-workers','1','--drain-seconds','1','--guard-url','http://127.0.0.1:9','--guard-decision-tcp',f'sumunjang.{namespace}.svc:9082','--guard-decision-grpc','--guard-decision-server-name',f'sumunjang.{namespace}.svc','--guard-decision-ca','/tls/ca.crt','--guard-decision-cert','/tls/client.crt','--guard-decision-key','/tls/client.key','--guard-timeout-ms','1000']}
        environments={'hopae':[env('HOPAE_CONSOLE_DELEGATION_KEY','hopae-delegation'),env('OWNED_API_KEY','api'),env('HOPAE_TEST_GATEWAY_KEY','caller')],'sumunjang':[env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector'),env('HANGANG_GUARD_ADMIN_TOKEN','guard-admin')],'pumgye':[env('PUMGYE_DECISION_TOKEN','pum-decision'),env('PUMGYE_ADMIN_TOKEN','pum-admin')],'hangang':[env('HOPAE_CONSOLE_DELEGATION_KEY','hopae-delegation'),env('HANGANG_GUARD_ADMIN_TOKEN','guard-admin'),env('FIXTURE_KEY','caller'),env('HANGANG_ADMIN_TOKEN','gateway-admin'),env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector'),env('PUMGYE_DECISION_TOKEN','pum-decision'),env('PUMGYE_ADMIN_TOKEN','pum-admin')]}
        if args.receipt_client:environments['hopae'].append(env('OWNED_RECEIPT_SEED','receipt-seed'))
        if args.authenticated_client:
            commands['pumgye']+=['--authentication-trust','/config/authentication-trust.json','--authentication-live','/config/authentication-live.json','--network-live','/config/network-live.json']
            environments['pumgye']+=[env('HOPAE_TEST_GATEWAY_KEY','caller'),env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector')]
        for name in commands:
            resource('PersistentVolumeClaim',name+'-state',spec={'accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':'1Gi'}}})
            container={'name':name,'image':getattr(args,name+'_image'),'imagePullPolicy':'Never','args':commands[name],'env':environments[name],'securityContext':{'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},'resources':{'requests':{'cpu':'100m','memory':'64Mi'},'limits':{'cpu':'2','memory':'512Mi'}},'volumeMounts':[{'name':'config','mountPath':'/config','readOnly':True},{'name':'tls','mountPath':'/tls','readOnly':True},{'name':'state','mountPath':'/state'}]}
            probe={'hopae':8700,'pumgye':9086,'sumunjang':9082,'hangang':8443}[name]
            container['readinessProbe']={'tcpSocket':{'port':probe},'periodSeconds':2}
            if name=='pumgye':container['readinessProbe']={'httpGet':{'port':9086,'path':'/-/ready'},'periodSeconds':2}
            deployment=resource('Deployment',name,spec={'replicas':1,'strategy':{'type':'Recreate'},'selector':{'matchLabels':{'app':name}},'template':{'metadata':{'labels':{'app':name}},'spec':{'automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':65532,'runAsGroup':65532,'fsGroup':65532,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[container],'volumes':[{'name':'config','configMap':{'name':'world-config'}},{'name':'tls','secret':{'secretName':'world-tls','defaultMode':416}},{'name':'state','persistentVolumeClaim':{'claimName':name+'-state'}}]}}});deployment['apiVersion']='apps/v1'
            if name=='hangang':
                deployment['spec']['template']['spec']['initContainers']=[{'name':'private-admin-state','image':args.echo_image,'imagePullPolicy':'IfNotPresent','command':['/bin/sh','-ec','umask 077; mkdir -p /state/admin /state/plugins; chmod 0700 /state/admin /state/plugins; cp /config/plugins.json /state/plugins.json; cp /config/plugin.manifest.json /state/plugins/manifest.json;  for db in admin-users.sqlite3 plugin-audit.sqlite3; do for suffix in "" -wal -shm; do f="/state/admin/$db$suffix"; if [ -e "$f" ]; then chmod 0600 "$f"; fi; done; done'],'securityContext':{'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'state','mountPath':'/state'}]}]
                init=deployment['spec']['template']['spec']['initContainers'][0]
                init['volumeMounts'].append({'name':'config','mountPath':'/config','readOnly':True})
                init['command'][2]+='; '+ '; '.join('cp /config/plugin.'+asset+' /state/plugins/'+asset for asset in manifest['assets'])+'; chmod 0600 /state/plugins.json /state/plugins/*'
                if args.hopae_plugin:
                    init['command'][2]+='; mkdir -p /state/hopae-plugin; chmod 0700 /state/hopae-plugin; cp /config/hopae.manifest.json /state/hopae-plugin/manifest.json; '+ '; '.join(hop_copies)+'; chmod 0600 /state/hopae-plugin/*'
            ports={'hangang':[8443],'hopae':([8702,8703] if args.hopae_plugin else [8703]),'pumgye':[9084,9087],'sumunjang':[9080,9082]}[name]
            resource('Service',name,spec={'selector':{'app':name},'ports':[{'name':'p'+str(p),'port':p,'targetPort':p} for p in ports]})
        echo=resource('Deployment','echo',spec={'replicas':1,'selector':{'matchLabels':{'app':'echo'}},'template':{'metadata':{'labels':{'app':'echo'}},'spec':{'automountServiceAccountToken':False,'containers':[{'name':'echo','image':args.echo_image,'imagePullPolicy':'IfNotPresent','command':['node','-e',"let count=0;require('http').createServer((q,r)=>{r.setHeader('content-type','application/json');if(q.url==='/__count'){r.end(JSON.stringify({count}));return;}count++;let chunks=[];q.on('data',c=>chunks.push(c));q.on('end',()=>r.end(JSON.stringify({headers:q.headers,method:q.method,path:q.url,body:Buffer.concat(chunks).toString('utf8')})));}).listen(8080,'0.0.0.0');"],'args':['--']}]}}});echo['apiVersion']='apps/v1'
        resource('Service','echo',spec={'selector':{'app':'echo'},'ports':[{'port':8080,'targetPort':8080}]})
        try:
            kube('create','namespace',namespace);created=True
            kube('apply','-f','-',body=json.dumps({'apiVersion':'v1','kind':'List','items':items}).encode(),timeout=300)
            for name in [*commands,'echo']:
                kube('-n',namespace,'rollout','status','deployment/'+name,'--timeout=120s',timeout=135)
                print('Ready: '+name,flush=True)
            def forward(name,remote):
                local=port();log=(root/(name+'-'+str(remote)+'.log')).open('wb')
                process=subprocess.Popen([str(wrapper),'-n',namespace,'port-forward','deployment/'+name,f'{local}:{remote}'],stdout=log,stderr=log);forwards.append(process)
                for _ in range(100):
                    if process.poll() is not None:raise RuntimeError('owned port-forward exited')
                    try:
                        with socket.create_connection(('127.0.0.1',local),timeout=.1):return local
                    except OSError:time.sleep(.05)
                raise RuntimeError('owned port-forward deadline')
            public=forward('hangang',8443);admin=forward('hangang',9080);backend=forward('echo',8080)
            ctx=ssl.create_default_context(cafile=str(root/'ca.pem'))
            class Gateway(http.client.HTTPSConnection):
                def connect(self):self.sock=ctx.wrap_socket(socket.create_connection(('127.0.0.1',public),timeout=3),server_hostname='app.example.test')
            def backend_count():
                # Only the idempotent diagnostic read may retry a port-forward
                # transport failure. Never replay the protected application call.
                deadline=time.monotonic()+10
                for attempt in range(3):
                    c=http.client.HTTPConnection('127.0.0.1',backend,timeout=min(3,max(.1,deadline-time.monotonic())))
                    try:
                        c.request('GET','/__count');r=c.getresponse();data=json.loads(r.read())
                        assert r.status==200 and type(data['count']) is int and data['count']>=0
                        return data['count']
                    except (OSError,http.client.HTTPException):
                        if attempt==2 or time.monotonic()>=deadline:raise
                        print('Read-only backend counter transport retry',flush=True)
                    finally:c.close()
            def request(method='GET',key=tokens['api']):
                c=Gateway('app.example.test',8443,timeout=3);headers={'Host':'app.example.test','x-forwarded-user':'forged','x-hopae-aal':'3'}
                if key:headers['Authorization']='Bearer '+key
                if args.native_resource:headers['Content-Type']='text/plain'
                before=backend_count()
                c.request(method,'/secure',body=b'owned final entity' if args.native_resource else None,headers=headers);r=c.getresponse();data=r.read();status=r.status;c.close()
                assert backend_count()==before+(1 if status==200 else 0),'refused Kubernetes request reached application backend'
                return status,data
            def api(local,path,method='GET',body=None,token=None,extra=None):
                c=http.client.HTTPConnection('127.0.0.1',local,timeout=3);headers={'Authorization':'Bearer '+(token or tokens['gateway-admin']),'Content-Type':'application/json'}
                if extra:headers.update(extra)
                c.request(method,path,body=None if body is None else json.dumps(body),headers=headers);r=c.getresponse();data=r.read();status=r.status;metadata=dict(r.getheaders());c.close();return status,json.loads(data),metadata
            status,body=request();assert status==200,'initial protected request status '+str(status)
            echoed=json.loads(body);headers={k.lower():v for k,v in echoed['headers'].items()}
            if args.native_resource:assert echoed['path']=='/api/secure' and echoed['body']=='owned final entity','native final target/entity was not preserved'
            assert headers['x-forwarded-user']==subject and headers['x-hopae-aal']=='0' and 'authorization' not in headers
            assert request('POST')[0]==403 and request(key=None)[0]==401
            if args.receipt_client:
                receipt_port=forward('hopae',8703)
                receipt_config={'settings':{'transport':'grpc','address':f'localhost:{receipt_port}','tls':{'server_name':f'hopae.{namespace}.svc','ca':str(root/'ca.pem'),'certificate':str(root/'client.pem'),'key':str(root/'client.key')}},'issuer_ref':'owned-world','key_epoch':1,'public_key':receipt_pin,'service':'orders','audience':'orders-api','method':'GET','target':'/secure','body':'','headers':[['x-hopae-contract','1'],['x-forwarded-host','app.example.test'],['x-forwarded-proto','https'],['x-forwarded-port','8443'],['x-forwarded-for','127.0.0.1'],['x-original-method','GET'],['x-original-url','https://app.example.test:8443/secure']]}
                receipt_path=root/'receipt-client.json';receipt_path.write_text(json.dumps(receipt_config))
                receipt_environment=dict(os.environ,OWNED_RECEIPT_CALLER=tokens['caller'],OWNED_RECEIPT_CREDENTIAL=tokens['api'])
                with (root/'receipt-client.log').open('w') as log:
                    result=subprocess.run([str(args.receipt_client.resolve()),str(receipt_path)],input='allow\n',env=receipt_environment,text=True,stdout=subprocess.PIPE,stderr=log,timeout=10)
                assert result.returncode==0 and json.loads(result.stdout)['allowed'] is True,'Kubernetes native receipt refused'
                print('PASS: actual Hopae Pod native issuer and Hangang client verify a request-bound service receipt over mTLS Service DNS')
                if args.authenticated_client:
                    pum=forward('pumgye',9084)
                    authenticated_config=json.loads(json.dumps(receipt_config))
                    authenticated_config.update(identity_epoch='world1',qualification_ip='127.0.0.1',pumgye_endpoint=f'https://127.0.0.1:{pum}/v1/resource/authenticated-decision')
                    authenticated_path=root/'authenticated-client.json';authenticated_path.write_text(json.dumps(authenticated_config))
                    authenticated_environment=dict(receipt_environment,PUMGYE_DECISION_TOKEN=tokens['pum-decision'])
                    with (root/'authenticated-client.log').open('w') as log:
                        result=subprocess.run([str(args.authenticated_client.resolve()),str(authenticated_path)],input='allow\n',env=authenticated_environment,text=True,stdout=subprocess.PIPE,stderr=log,timeout=10)
                    if result.returncode!=0:
                        diagnostic=(root/'authenticated-client.log').read_text(errors='replace')
                        for secret in tokens.values():diagnostic=diagnostic.replace(secret,'[redacted]')
                        raise AssertionError('Kubernetes authenticated resource client failed: '+diagnostic[-500:])
                    assert json.loads(result.stdout)['allowed'] is True,'Kubernetes authenticated resource endpoint refused'
                    print('PASS: actual Pumgye Pod authenticated resource endpoint combines Hopae live receipt and Sumunjang Enforce over mTLS Service DNS')


            status,plugins,_=api(admin,'/v1/plugins');assert status==200 and any(p['id']==plugin_id for p in plugins['plugins'])
            c=http.client.HTTPConnection('127.0.0.1',admin,timeout=3)
            c.request('GET',f'/ui/plugins/{plugin_id}/'+manifest['entry'],headers={'Authorization':'Bearer '+tokens['gateway-admin']});asset_response=c.getresponse();asset_bytes=asset_response.read();c.close()
            assert asset_response.status==200 and hashlib.sha256(asset_bytes).hexdigest()==manifest['assets'][manifest['entry']]
            assert api(admin,f'/v1/plugins/{plugin_id}/policy')[0]==200
            if args.browser_probe:
                browser_config=root/'browser.json'
                browser_config.write_text(json.dumps({'base':f'http://127.0.0.1:{admin}','token':tokens['gateway-admin'],'plugin':plugin_id,'hopae':bool(args.hopae_plugin),'resourceCatalog':args.resource_catalog,'application':{'gatewayPort':public,'backendPort':backend,'ca':str(root/'ca.pem'),'key':tokens['api']},'hopaeRestart':{'kubectl':str(wrapper),'namespace':namespace}}))
                subprocess.run([node,str(args.browser_probe.resolve()),str(browser_config)],check=True,timeout=240)
            status,document,metadata=api(admin,'/v1/pumgye/policy');assert status==200
            if args.resource_catalog:
                baseline=json.loads(json.dumps(document['policy']['resources']))
                for field,value in [('information_class','restricted'),('minimum_aal',1),('service','billing')]:
                    document['policy']['resources']['db:orders'][field]=value
                    status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                    assert status==200 and request()[0]==403,'catalog change failed to refuse '+field
                    document['policy']['resources']=json.loads(json.dumps(baseline))
                    status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                    assert status==200 and request()[0]==200
                document['policy']['resources']={}
                status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                assert status==200 and request()[0]==403
                document['policy']['resources']=baseline
                status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                assert status==200 and request()[0]==200
            document['policy']['services']['orders']['users']={}
            status,updated,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']});assert status==200 and request()[0]==403
            # Persisted revocation must survive an actual Pod replacement.
            kube('-n',namespace,'rollout','restart','deployment/pumgye');kube('-n',namespace,'rollout','status','deployment/pumgye','--timeout=120s',timeout=135)
            for _ in range(20):
                status=request()[0];assert status in (403,503)
                if status==403:break
                time.sleep(.1)
            else:raise AssertionError('authority reconnect deadline')
            updated['policy']['services']['orders']['users']={subject:['reader']}
            status,restored,_=api(admin,'/v1/pumgye/policy','PUT',updated,extra={'If-Match':f'"{updated["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']});assert status==200 and request()[0]==200
            kube('-n',namespace,'rollout','restart','deployment/hangang')
            kube('-n',namespace,'rollout','status','deployment/hangang','--timeout=120s',timeout=135)
            public=forward('hangang',8443);admin=forward('hangang',9080)
            assert request()[0]==200,'gateway private admin state did not survive Pod replacement'
            assert api(admin,f'/v1/plugins/{plugin_id}/blocks','POST',{'network':'127.0.0.1/32','expires_at':int(time.time())+600,'reason':'owned K8s fixture'},tokens['gateway-admin'])[0]==200
            assert request()[0]==403
            assert api(admin,f'/v1/plugins/{plugin_id}/blocks','DELETE',{'network':'127.0.0.1/32'},tokens['gateway-admin'])[0]==200 and request()[0]==200
            kube('-n',namespace,'scale','deployment/sumunjang','--replicas=0')
            kube('-n',namespace,'wait','--for=delete','pod','-l','app=sumunjang','--timeout=60s')
            assert request()[0]==503
            print('PASS: actual four independent K8s Pods, nonroot static artifacts, mTLS Service DNS, protected request identity, method/guest denial, real pinned console discovery/assets, mTLS plugin management reads/mutations, delegated policy CAS, immediate revocation, PVC/authority/gateway Pod replacement, private administrator state, refused backend non-dispatch and network authority outage')
        except Exception:
            if created:
                for name in commands:
                    try:
                        diagnostic=kube('-n',namespace,'logs','deployment/'+name,'--tail=15').decode(errors='replace')
                        for value in tokens.values():diagnostic=diagnostic.replace(value,'[redacted]')
                        for file in ['server.key','client.key','ca.key']:diagnostic=diagnostic.replace((root/file).read_text(),'[redacted key]')
                        print('Owned diagnostic '+name+': '+diagnostic[:4000],flush=True)
                    except (RuntimeError,subprocess.TimeoutExpired):pass
            raise
        finally:
            for process in forwards:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            if created:
                kube('delete','namespace',namespace,'--wait=true','--timeout=120s',timeout=135)
                print('Owned namespace removed; retained synthetic PVs remain under the cluster Retain policy.')


if __name__=='__main__':main()
