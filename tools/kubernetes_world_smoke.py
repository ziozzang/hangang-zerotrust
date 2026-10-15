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
    parser.add_argument('--sumunjang-native-source',action='store_true')
    parser.add_argument('--sumunjang-crd-manifest',type=Path)
    parser.add_argument('--receipt-client',type=Path)
    parser.add_argument('--receipt-clock-diagnostic',type=Path)
    parser.add_argument('--authenticated-client',type=Path)
    parser.add_argument('--native-resource',action='store_true')
    parser.add_argument('--credential-projection',action='store_true')
    parser.add_argument('--observed',action='store_true',help='Require native observed authentication, permit and credential output owners')
    parser.add_argument('--composition',action='store_true',help='Service-only API key plus HTTPS relay in a fifth owned Pod')
    parser.add_argument('--composition-mode',choices=['all','any'],default='all')
    parser.add_argument('--evidence-dir',type=Path,help='Private owned diagnostics directory; never stores credential configuration')
    args=parser.parse_args()
    if args.composition and not (args.observed and args.credential_projection and args.receipt_client):
        parser.error('--composition requires --observed --credential-projection and the composition SDK receipt client')
    if not args.composition and args.composition_mode!='all':parser.error('--composition-mode requires --composition')
    if args.sumunjang_native_source != bool(args.sumunjang_crd_manifest):
        parser.error('--sumunjang-native-source and --sumunjang-crd-manifest must be used together')
    if args.observed and not args.credential_projection:
        parser.error('--observed requires --credential-projection and an observed SDK receipt client')
    if args.credential_projection and not args.native_resource:
        parser.error('credential projection requires native resource qualification')
    if args.credential_projection and (not args.receipt_client or not args.resource_catalog or args.authenticated_client):
        parser.error('credential projection requires receipt client and resource catalog; qualify the direct authenticated client separately without native route ownership')
    if args.native_resource and not (args.authenticated_client or args.credential_projection):
        parser.error('native resource requires authenticated client qualification')
    if args.authenticated_client and not (args.receipt_client and args.resource_catalog):
        parser.error('authenticated client requires receipt client and resource catalog')
    for component in ['hangang','hopae','sumunjang','pumgye','echo']:
        image=getattr(args,component+'_image')
        if '@' in image and not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}',image):
            parser.error(component+' image requires a canonical SHA-256 digest')
    if args.evidence_dir:
        args.evidence_dir.mkdir(mode=0o700,parents=True,exist_ok=False)
    wrapper=args.kubectl.resolve(strict=True)
    node=str(args.node_binary.resolve(strict=True)) if args.node_binary else shutil.which('node')
    if args.browser_probe and not node:parser.error('browser probe requires --node-binary when node is not in PATH')
    namespace='owned-world-'+secrets.token_hex(6);created=False;forwards=[];owned_crd_uid=None;native_policy_uid=None
    crd_name='sumunjangpolicies.policy.hangang.dev'
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
            ext=root/f'{name}.ext';ext.write_text('basicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage='+usage+'\nsubjectAltName='+','.join('DNS:'+c+'.'+namespace+'.svc' for c in (['hangang','hopae','sumunjang','pumgye','relay'] if args.composition else ['hangang','hopae','sumunjang','pumgye']))+',DNS:app.example.test,IP:127.0.0.1\n')
            openssl('x509','-req','-in',root/f'{name}.csr','-CA',root/'ca.pem','-CAkey',root/'ca.key','-CAcreateserial','-days','1','-extfile',ext,'-out',root/f'{name}.pem')
        tokens={name:secrets.token_hex(32) for name in ['api','caller','gateway-admin','guard-collector','guard-admin','pum-decision','pum-admin','hopae-delegation']}
        if args.composition:
            tokens.update({name:secrets.token_hex(32) for name in ['remote-api','remote-other','other-local','relay-control']})
        def composition_wire(entries):
            return base64.urlsafe_b64encode(json.dumps({'version':1,'credentials':[{'slot':slot,'credential':credential} for slot,credential in entries]},separators=(',',':')).encode()).decode().rstrip('=')
        composition_key=composition_wire([('local',tokens['api']),('partner',tokens.get('remote-api',''))])
        default_key=composition_key if args.composition else tokens['api']
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
        if args.composition:
            profile=hop['authentication_gateway']['profiles'][0]
            profile['api_keys'].append({'token_env':'OWNED_OTHER_KEY','subject':'other'})
            profile['api_relay']={'url':f'https://relay.{namespace}.svc:9443/verify','issuer':'owned-partner','timeout_ms':500,'allow_private_endpoints':True,'ca_file':'/tls/ca.crt'}
            profile['composition']={'mode':args.composition_mode,'timeout_ms':800,'slots':[{'id':'local','provider':'api_key'},{'id':'partner','provider':'api_relay'}],'identities':[{'subject':subject,'bindings':[{'slot':'local','issuer':'hopae:owned','realm':'services','subject':subject,'kind':'service'},{'slot':'partner','issuer':'owned-partner','realm':'services','subject':partner,'kind':'service'}]} for subject,partner in [('worker','partner-worker'),('other','partner-other')]]}
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
        if args.credential_projection:
            openssl('genpkey','-algorithm','ED25519','-out',root/'permit.pem')
            permit_seed=subprocess.check_output(['openssl','pkey','-in',str(root/'permit.pem'),'-outform','DER'],stderr=subprocess.DEVNULL)
            permit_public=subprocess.check_output(['openssl','pkey','-in',str(root/'permit.pem'),'-pubout','-outform','DER'],stderr=subprocess.DEVNULL)
            assert len(permit_seed)==48 and len(permit_public)==44
            tokens['permit-seed']=base64.b64encode(permit_seed[-32:]).decode()
            tokens['origin-bearer']=secrets.token_urlsafe(32)
            tokens['route-caller']=secrets.token_hex(32)
            permit_pin={'issuer_ref':'owned-permit','key_epoch':1,'public_key':base64.b64encode(permit_public[-32:]).decode()}
            gateway['revision']=1
            gateway['http'][0]['auth']['native_resource'].update(permission_permit=permit_pin,project_credentials=True)
            hop['receipt_permit_keys']=[permit_pin]
            hop['credential_projection']={'revision':1,'plans':[{'service':'orders','audience':'orders-api','resource':'db:orders','action':'select','minimum_aal':0,'credential':{'type':'bearer_reference','secret_ref':'fixture:origin'}}]}
            hop['projection_receiver']={'authority':dict(tls('pumgye'),address=f'https://pumgye.{namespace}.svc:9087',token_env='PUMGYE_DECISION_TOKEN'),'secrets':[{'reference':'fixture:origin','token_env':'OWNED_ORIGIN_BEARER'}]}
        if args.observed:
            gateway['http'][0]['auth']['native_resource']['observed']={
                'identity_authority':'world1','minimum_profile_revision':1,
                'minimum_application_generation':1,'minimum_key_registry_revision':1,
                'source_error_ppm':500,'receiver_error_ppm':500,
                'maximum_final_header_bytes':32768,
            }
            hop['projection_receiver']['observed_clock_rates']={'source_ppm':500,'receiver_ppm':500}
        items=[]
        def resource(kind,name,**fields):
            obj={'apiVersion':'v1','kind':kind,'metadata':{'name':name,'namespace':namespace,'labels':{'app.kubernetes.io/part-of':'owned-hangang-world'}},**fields};items.append(obj);return obj
        config_map=resource('ConfigMap','world-config',data={'hopae.json':json.dumps(hop),'hangang.json':json.dumps(gateway),'pumgye.json':json.dumps({'revision':0,'policy':policy}),'sumunjang.json':json.dumps({'mode':'enforce','allow':[]})})
        if args.authenticated_client or args.credential_projection:
            config_map['data']['authentication-trust.json']=json.dumps({'entries':[{'issuer_ref':'owned-world','key_epoch':1,'identity_epoch':'world1','service':'orders','audience':'orders-api','minimum_revision':1,'public_key':receipt_pin}]})
            native_tls={'ca':'/tls/ca.crt','certificate':'/tls/client.crt','key':'/tls/client.key'}
            config_map['data']['authentication-live.json']=json.dumps(dict(native_tls,issuer_ref='owned-world',address=f'https://hopae.{namespace}.svc:8703',server_name=f'hopae.{namespace}.svc',token_env='HOPAE_TEST_GATEWAY_KEY'))
            config_map['data']['network-live.json']=json.dumps(dict(native_tls,address=f'https://sumunjang.{namespace}.svc:9082',server_name=f'sumunjang.{namespace}.svc',token_env='HANGANG_GUARD_COLLECTOR_TOKEN'))
        if args.observed:
            live=json.loads(config_map['data']['authentication-live.json'])
            live['observed_clock_rates']={'source_ppm':500,'receiver_ppm':500}
            config_map['data']['authentication-live.json']=json.dumps(live)
        if args.credential_projection:
            config_map['data']['permit-key.json']=json.dumps(dict(permit_pin,seed_env='OWNED_PERMIT_SEED'))
            config_map['data']['route-owner.json']=json.dumps({'listen':'0.0.0.0:8444','certificate':'/tls/tls.crt','key':'/tls/tls.key','client_ca':'/tls/ca.crt','token_env':'OWNED_ROUTE_CALLER'})
            config_map['data']['route-live.json']=json.dumps(dict(tls('hangang'),address=f'https://hangang.{namespace}.svc:8444',token_env='OWNED_ROUTE_CALLER'))
            config_map['data']['projection-live.json']=json.dumps(dict(tls('hopae'),address=f'https://hopae.{namespace}.svc:8703',token_env='HOPAE_TEST_GATEWAY_KEY'))
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
        if args.composition:
            config_map['data']['composition-relay.js']="const https=require('https'),fs=require('fs');let calls=0,unavailable=false;const server=https.createServer({key:fs.readFileSync('/tls/tls.key'),cert:fs.readFileSync('/tls/tls.crt')},(q,r)=>{let parts=[],size=0;q.on('data',c=>{size+=c.length;if(size>2048){q.destroy();return;}parts.push(c)});q.on('end',()=>{const reply=(status,value)=>{let body=JSON.stringify(value);r.writeHead(status,{'content-type':'application/json','content-length':Buffer.byteLength(body)});r.end(body)};if(q.url==='/__state'){if(q.headers.authorization!=='Bearer '+process.env.RELAY_CONTROL){reply(401,{});return;}if(q.method==='POST'){try{let next=JSON.parse(Buffer.concat(parts).toString());if(Object.keys(next).some(k=>k!=='unavailable')||typeof next.unavailable!=='boolean'){reply(400,{});return;}unavailable=next.unavailable}catch{reply(400,{});return;}}reply(200,{calls,unavailable});return;}if(q.url!=='/verify'||q.method!=='POST'){reply(404,{});return;}calls++;if(unavailable){reply(503,{});return;}let subject=q.headers.authorization==='Bearer '+process.env.REMOTE_API?'partner-worker':q.headers.authorization==='Bearer '+process.env.REMOTE_OTHER?'partner-other':null;let body;try{body=JSON.parse(Buffer.concat(parts).toString())}catch{reply(400,{});return;}if(!subject){reply(401,{});return;}if(body.service_id!=='orders'){reply(200,{active:false});return;}reply(200,{active:true,subject,service_id:'orders',expires_at:Date.now()+900})})});server.listen(9443,'0.0.0.0');"
        resource('Secret','world-credentials',stringData=tokens)
        resource('Secret','world-tls',stringData={'tls.crt':(root/'server.pem').read_text(),'tls.key':(root/'server.key').read_text(),'ca.crt':(root/'ca.pem').read_text(),'client.crt':(root/'client.pem').read_text(),'client.key':(root/'client.key').read_text()})
        def env(name,key):return {'name':name,'valueFrom':{'secretKeyRef':{'name':'world-credentials','key':key}}}
        commands={
            'hopae':['run','--config','/config/hopae.json'],
            'pumgye':['--listen','0.0.0.0:9084','--decision-listen','0.0.0.0:9085','--grpc-listen','0.0.0.0:9087','--readiness-listen','0.0.0.0:9086','--database','/state/pumgye.sqlite3','--policy','/config/pumgye.json','--tls-cert','/tls/tls.crt','--tls-key','/tls/tls.key','--client-ca','/tls/ca.crt'],
            'sumunjang':['--management-tls','--listen','0.0.0.0:9080','--decision-listen','0.0.0.0:9081','--grpc-listen','0.0.0.0:9082','--database','/state/sumunjang.sqlite3','--bootstrap-policy','/config/sumunjang.json','--decision-tls-cert','/tls/tls.crt','--decision-tls-key','/tls/tls.key','--decision-client-ca','/tls/ca.crt','--threads','2'],
            'hangang':['--config','/config/hangang.json','--database','sqlite:/state/hangang.sqlite3','--docker-connection-state','/state/docker-connections.json','--admin-users-db','/state/admin/admin-users.sqlite3','--admin-plugins','/state/plugins.json','--listen','0.0.0.0:8443','--admin','127.0.0.1:9080','--tls-cert','/tls/tls.crt','--tls-key','/tls/tls.key','--threads','2','--lua-workers','1','--drain-seconds','1','--guard-url','http://127.0.0.1:9','--guard-decision-tcp',f'sumunjang.{namespace}.svc:9082','--guard-decision-grpc','--guard-decision-server-name',f'sumunjang.{namespace}.svc','--guard-decision-ca','/tls/ca.crt','--guard-decision-cert','/tls/client.crt','--guard-decision-key','/tls/client.key','--guard-timeout-ms','1000']}
        if args.sumunjang_native_source:
            source_args=commands['sumunjang'];position=source_args.index('--bootstrap-policy');del source_args[position:position+2]
            source_args+=['--kubernetes-authority','/config/sumunjang-source.json','--readiness-listen','0.0.0.0:9083']
        environments={'hopae':[env('HOPAE_CONSOLE_DELEGATION_KEY','hopae-delegation'),env('OWNED_API_KEY','api'),env('HOPAE_TEST_GATEWAY_KEY','caller')],'sumunjang':[env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector'),env('HANGANG_GUARD_ADMIN_TOKEN','guard-admin')],'pumgye':[env('PUMGYE_DECISION_TOKEN','pum-decision'),env('PUMGYE_ADMIN_TOKEN','pum-admin')],'hangang':[env('HOPAE_CONSOLE_DELEGATION_KEY','hopae-delegation'),env('HANGANG_GUARD_ADMIN_TOKEN','guard-admin'),env('FIXTURE_KEY','caller'),env('HANGANG_ADMIN_TOKEN','gateway-admin'),env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector'),env('PUMGYE_DECISION_TOKEN','pum-decision'),env('PUMGYE_ADMIN_TOKEN','pum-admin')]}
        if args.composition:environments['hopae'].append(env('OWNED_OTHER_KEY','other-local'))
        if args.receipt_client:environments['hopae'].append(env('OWNED_RECEIPT_SEED','receipt-seed'))
        if args.authenticated_client or args.credential_projection:
            commands['pumgye']+=['--authentication-trust','/config/authentication-trust.json','--authentication-live','/config/authentication-live.json','--network-live','/config/network-live.json']
            environments['pumgye']+=[env('HOPAE_TEST_GATEWAY_KEY','caller'),env('HANGANG_GUARD_COLLECTOR_TOKEN','guard-collector')]
        if args.credential_projection:
            commands['hangang']+=['--route-owner-config','/config/route-owner.json']
            commands['pumgye']+=['--permit-key','/config/permit-key.json','--route-live','/config/route-live.json','--projection-live','/config/projection-live.json']
            environments['hangang'].append(env('OWNED_ROUTE_CALLER','route-caller'))
            environments['pumgye']+=[env('OWNED_ROUTE_CALLER','route-caller'),env('OWNED_PERMIT_SEED','permit-seed')]
            environments['hopae']+=[env('PUMGYE_DECISION_TOKEN','pum-decision'),env('OWNED_ORIGIN_BEARER','origin-bearer')]
        if args.observed:
            commands['pumgye']+=['--observed-permits','--observed-authority','owned-world']
        for name in commands:
            resource('PersistentVolumeClaim',name+'-state',spec={'accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':'1Gi'}}})
            container={'name':name,'image':getattr(args,name+'_image'),'imagePullPolicy':'Never','args':commands[name],'env':environments[name],'securityContext':{'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},'resources':{'requests':{'cpu':'100m','memory':'64Mi'},'limits':{'cpu':'2','memory':'512Mi'}},'volumeMounts':[{'name':'config','mountPath':'/config','readOnly':True},{'name':'tls','mountPath':'/tls','readOnly':True},{'name':'state','mountPath':'/state'}]}
            probe={'hopae':8700,'pumgye':9086,'sumunjang':9082,'hangang':8443}[name]
            container['readinessProbe']={'tcpSocket':{'port':probe},'periodSeconds':2}
            if name=='sumunjang' and args.sumunjang_native_source:container['readinessProbe']={'httpGet':{'port':9083,'path':'/readyz'},'periodSeconds':1,'failureThreshold':1}
            if name=='pumgye':container['readinessProbe']={'httpGet':{'port':9086,'path':'/-/ready'},'periodSeconds':2}
            deployment=resource('Deployment',name,spec={'replicas':1,'strategy':{'type':'Recreate'},'selector':{'matchLabels':{'app':name}},'template':{'metadata':{'labels':{'app':name}},'spec':{'automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':65532,'runAsGroup':65532,'fsGroup':65532,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[container],'volumes':[{'name':'config','configMap':{'name':'world-config'}},{'name':'tls','secret':{'secretName':'world-tls','defaultMode':416}},{'name':'state','persistentVolumeClaim':{'claimName':name+'-state'}}]}}});deployment['apiVersion']='apps/v1'
            if name=='sumunjang' and args.sumunjang_native_source:
                deployment['spec']['template']['spec'].update(serviceAccountName='native-source',automountServiceAccountToken=True)
            if name=='hangang':
                deployment['spec']['template']['spec']['initContainers']=[{'name':'private-admin-state','image':args.echo_image,'imagePullPolicy':'IfNotPresent','command':['/bin/sh','-ec','umask 077; mkdir -p /state/admin /state/plugins; chmod 0700 /state/admin /state/plugins; cp /config/plugins.json /state/plugins.json; cp /config/plugin.manifest.json /state/plugins/manifest.json;  for db in admin-users.sqlite3 plugin-audit.sqlite3; do for suffix in "" -wal -shm; do f="/state/admin/$db$suffix"; if [ -e "$f" ]; then chmod 0600 "$f"; fi; done; done'],'securityContext':{'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'state','mountPath':'/state'}]}]
                init=deployment['spec']['template']['spec']['initContainers'][0]
                init['volumeMounts'].append({'name':'config','mountPath':'/config','readOnly':True})
                init['command'][2]+='; '+ '; '.join('cp /config/plugin.'+asset+' /state/plugins/'+asset for asset in manifest['assets'])+'; chmod 0600 /state/plugins.json /state/plugins/*'
                if args.hopae_plugin:
                    init['command'][2]+='; mkdir -p /state/hopae-plugin; chmod 0700 /state/hopae-plugin; cp /config/hopae.manifest.json /state/hopae-plugin/manifest.json; '+ '; '.join(hop_copies)+'; chmod 0600 /state/hopae-plugin/*'
            ports={'hangang':[8443],'hopae':([8702,8703] if args.hopae_plugin else [8703]),'pumgye':[9084,9087],'sumunjang':[9080,9082]}[name]
            if name=='hangang' and args.credential_projection:ports.append(8444)
            if name=='sumunjang' and args.sumunjang_native_source:ports.append(9083)
            resource('Service',name,spec={'selector':{'app':name},'ports':[{'name':'p'+str(p),'port':p,'targetPort':p} for p in ports]})
        echo=resource('Deployment','echo',spec={'replicas':1,'selector':{'matchLabels':{'app':'echo'}},'template':{'metadata':{'labels':{'app':'echo'}},'spec':{'automountServiceAccountToken':False,'containers':[{'name':'echo','image':args.echo_image,'imagePullPolicy':'IfNotPresent','command':['node','-e',"let count=0;require('http').createServer((q,r)=>{r.setHeader('content-type','application/json');if(q.url==='/__count'){r.end(JSON.stringify({count}));return;}count++;let chunks=[];q.on('data',c=>chunks.push(c));q.on('end',()=>r.end(JSON.stringify({headers:q.headers,method:q.method,path:q.url,body:Buffer.concat(chunks).toString('utf8')})));}).listen(8080,'0.0.0.0');"],'args':['--']}]}}});echo['apiVersion']='apps/v1'
        resource('Service','echo',spec={'selector':{'app':'echo'},'ports':[{'port':8080,'targetPort':8080}]})
        if args.composition:
            relay=resource('Deployment','relay',spec={'replicas':1,'selector':{'matchLabels':{'app':'relay'}},'template':{'metadata':{'labels':{'app':'relay'}},'spec':{'automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':65532,'runAsGroup':65532,'fsGroup':65532},'containers':[{'name':'relay','image':args.echo_image,'imagePullPolicy':'IfNotPresent','command':['node','/config/composition-relay.js'],'env':[env('REMOTE_API','remote-api'),env('REMOTE_OTHER','remote-other'),env('RELAY_CONTROL','relay-control')],'securityContext':{'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},'readinessProbe':{'tcpSocket':{'port':9443},'periodSeconds':2},'resources':{'requests':{'cpu':'50m','memory':'32Mi'},'limits':{'cpu':'1','memory':'128Mi'}},'volumeMounts':[{'name':'config','mountPath':'/config','readOnly':True},{'name':'tls','mountPath':'/tls','readOnly':True}]}],'volumes':[{'name':'config','configMap':{'name':'world-config'}},{'name':'tls','secret':{'secretName':'world-tls','defaultMode':416}}]}}});relay['apiVersion']='apps/v1'
            resource('Service','relay',spec={'selector':{'app':'relay'},'ports':[{'port':9443,'targetPort':9443}]})
        native_spec={'policy':{'mode':'enforce','auto_block':False,'allow':[]},'rules':{'version':1,'rules':[]},'blocks':[]}
        source_role={'apiVersion':'rbac.authorization.k8s.io/v1','kind':'Role','metadata':{'name':'native-source','namespace':namespace},'rules':[{'apiGroups':['policy.hangang.dev'],'resources':['sumunjangpolicies'],'resourceNames':['native'],'verbs':['get']}]}
        source_config=None
        try:
            if args.sumunjang_native_source:
                import yaml
                assert not kube('get','crd',crd_name,'--ignore-not-found','-o','name').strip(),'preexisting global CRD must not be modified'
                crd=next(item for item in yaml.safe_load_all(args.sumunjang_crd_manifest.read_text()) if item and item.get('kind')=='CustomResourceDefinition')
                assert crd['metadata']['name']==crd_name and crd['spec']['group']=='policy.hangang.dev'
                crd['metadata']['labels']={'hangang.dev/qualification':namespace}
                # CREATE is intentional: an intervening creator must cause refusal.
                kube('create','-f','-',body=json.dumps(crd).encode())
                owned_crd_uid=json.loads(kube('get','crd',crd_name,'-o','json'))['metadata']['uid']
                kube('wait','--for=condition=Established','crd/'+crd_name,'--timeout=60s')
            kube('create','namespace',namespace);created=True
            if args.sumunjang_native_source:
                native_policy={'apiVersion':'policy.hangang.dev/v1alpha1','kind':'SumunjangPolicy','metadata':{'name':'native','namespace':namespace},'spec':native_spec}
                source_items=[{'apiVersion':'v1','kind':'ServiceAccount','metadata':{'name':'native-source','namespace':namespace}},source_role,{'apiVersion':'rbac.authorization.k8s.io/v1','kind':'RoleBinding','metadata':{'name':'native-source','namespace':namespace},'subjects':[{'kind':'ServiceAccount','name':'native-source','namespace':namespace}],'roleRef':{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':'native-source'}},native_policy]
                kube('create','-f','-',body=json.dumps({'apiVersion':'v1','kind':'List','items':source_items}).encode())
                native_policy_uid=json.loads(kube('-n',namespace,'get','sumunjangpolicy','native','-o','json'))['metadata']['uid']
                source_config={'api':'https://kubernetes.default.svc','namespace':namespace,'name':'native','uid':native_policy_uid,'ca':'/var/run/secrets/kubernetes.io/serviceaccount/ca.crt','token_file':'/var/run/secrets/kubernetes.io/serviceaccount/token'}
                config_map['data']['sumunjang-source.json']=json.dumps(source_config)
                print('Owned native Sum source: '+namespace+' UID '+native_policy_uid,flush=True)
            kube('apply','-f','-',body=json.dumps({'apiVersion':'v1','kind':'List','items':items}).encode(),timeout=300)
            for name in [*commands,'echo',*(['relay'] if args.composition else [])]:
                kube('-n',namespace,'rollout','status','deployment/'+name,'--timeout=120s',timeout=135)
                print('Ready: '+name,flush=True)
            def forward(name,remote):
                local=port();log=(root/(name+'-'+str(remote)+'.log')).open('wb')
                process=subprocess.Popen([str(wrapper),'-n',namespace,'port-forward','deployment/'+name,f'{local}:{remote}'],stdout=log,stderr=log);forwards.append(process)
                # Control-plane port-forward setup may traverse a lossy management
                # link. This changes no proof budget or application-call retry.
                for _ in range(600):
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
            qualification_phase='protected-request'
            def request(method='GET',key=default_key):
                c=Gateway('app.example.test',8443,timeout=3);headers={'Host':'app.example.test','x-forwarded-user':'forged','x-hopae-aal':'3'}
                if key:headers['Authorization']=('Hopae-Compose ' if args.composition else 'Bearer ')+key
                if args.native_resource:headers['Content-Type']='text/plain'
                before=backend_count()
                begun=time.monotonic();request_at_ms=round(time.time()*1000)
                c.request(method,'/secure',body=b'owned final entity' if args.native_resource else None,headers=headers);r=c.getresponse();data=r.read();status=r.status;c.close()
                after=backend_count()
                request.last={'at_unix_ms':request_at_ms,'status':status,'elapsed_ms':round((time.monotonic()-begun)*1000),'backend_delta':after-before}
                assert after==before+(1 if status==200 else 0),'refused Kubernetes request reached application backend'
                if status==200 and args.credential_projection:
                    projected={k.lower():v for k,v in json.loads(data)['headers'].items()}
                    assert projected.get('authorization')=='Bearer '+tokens['origin-bearer'],'owned origin credential mismatch'
                    assert projected.get('authorization')!='Bearer '+tokens['api'],'incoming credential leaked'
                    if args.composition:
                        assert all(secret.encode() not in data for secret in [tokens['api'],tokens['remote-api'],tokens['remote-other'],tokens['other-local'],tokens['caller'],composition_key]),'composition credential/envelope/caller reached origin'
                return status,data
            def api(local,path,method='GET',body=None,token=None,extra=None):
                c=http.client.HTTPConnection('127.0.0.1',local,timeout=3);headers={'Authorization':'Bearer '+(token or tokens['gateway-admin']),'Content-Type':'application/json'}
                if extra:headers.update(extra)
                c.request(method,path,body=None if body is None else json.dumps(body),headers=headers);r=c.getresponse();data=r.read();status=r.status;metadata=dict(r.getheaders());c.close();return status,json.loads(data),metadata
            def eventually(work,seconds=30):
                deadline=time.monotonic()+seconds
                while time.monotonic()<deadline:
                    try:
                        value=work()
                        if value:return value
                    except (OSError,http.client.HTTPException):pass
                    time.sleep(.1)
                raise AssertionError('owned native source convergence deadline')
            def native_patch(spec):
                assert json.loads(kube('-n',namespace,'get','sumunjangpolicy','native','-o','json'))['metadata']['uid']==native_policy_uid,'source object changed before operator mutation'
                kube('-n',namespace,'patch','sumunjangpolicy','native','--type=merge','-p',json.dumps({'spec':spec}))
            if args.sumunjang_native_source:
                native_management=forward('sumunjang',9080);native_readiness=forward('sumunjang',9083)
                source_ctx=ssl.create_default_context(cafile=str(root/'ca.pem'));source_ctx.load_cert_chain(str(root/'client.pem'),str(root/'client.key'))
                def source_report():
                    class Source(http.client.HTTPSConnection):
                        def connect(self):self.sock=source_ctx.wrap_socket(socket.create_connection(('127.0.0.1',native_management),timeout=3),server_hostname='sumunjang.'+namespace+'.svc')
                    c=Source('sumunjang.'+namespace+'.svc',9080,timeout=3);c.request('GET','/v1/kubernetes/authority',headers={'Authorization':'Bearer '+tokens['guard-admin']});r=c.getresponse();value=json.loads(r.read());c.close();assert r.status==200;return value
                def source_ready():
                    c=http.client.HTTPConnection('127.0.0.1',native_readiness,timeout=3);c.request('GET','/readyz');r=c.getresponse();r.read();c.close();return r.status
                eventually(lambda:source_report().get('available') and source_ready()==200)
            status,body=request();assert status==200,'initial protected request status '+str(status)
            echoed=json.loads(body);headers={k.lower():v for k,v in echoed['headers'].items()}
            if args.native_resource:assert echoed['path']=='/api/secure' and echoed['body']=='owned final entity','native final target/entity was not preserved'
            assert headers['x-forwarded-user']==subject and headers['x-hopae-aal']=='0'
            if not args.credential_projection:assert 'authorization' not in headers
            else:print('PASS: actual four-Pod native permission and paired credential projection delivers only the separate origin bearer over mTLS Service DNS')
            if args.composition:
                expected=401 if args.composition_mode=='all' else 200
                assert request(key=composition_wire([('local',tokens['api'])]))[0]==expected
                assert request(key=composition_wire([('partner',tokens['remote-api'])]))[0]==expected
                for entries in [[('local','invalid-local-at-least-thirty-two-bytes'),('partner',tokens['remote-api'])],[('local',tokens['api']),('partner','invalid-remote-at-least-thirty-two-bytes')],[('local',tokens['api']),('partner',tokens['remote-other'])]]:
                    assert request(key=composition_wire(entries))[0]==401,'invalid or ambiguous presented sibling accepted'
                print('PASS: Kubernetes service-only composition '+args.composition_mode+' uses fixed credential slots and explicit verified identities; missing/invalid/ambiguous factors and secret isolation checked')
            assert request('POST')[0]==403 and request(key=None)[0]==401
            if args.receipt_client:
                receipt_port=forward('hopae',8703)
                receipt_config={'settings':{'transport':'grpc','address':f'localhost:{receipt_port}','tls':{'server_name':f'hopae.{namespace}.svc','ca':str(root/'ca.pem'),'certificate':str(root/'client.pem'),'key':str(root/'client.key')}},'issuer_ref':'owned-world','key_epoch':1,'public_key':receipt_pin,'service':'orders','audience':'orders-api','method':'GET','target':'/secure','body':'','headers':[['x-hopae-contract','1'],['x-forwarded-host','app.example.test'],['x-forwarded-proto','https'],['x-forwarded-port','8443'],['x-forwarded-for','127.0.0.1'],['x-original-method','GET'],['x-original-url','https://app.example.test:8443/secure']]}
                if args.observed:receipt_config.update(identity_authority='world1',source_ppm=500,receiver_ppm=500)
                if args.composition:receipt_config['credential_scheme']='hopae_compose'
                receipt_path=root/'receipt-client.json';receipt_path.write_text(json.dumps(receipt_config))
                receipt_environment=dict(os.environ,OWNED_RECEIPT_CALLER=tokens['caller'],OWNED_RECEIPT_CREDENTIAL=default_key)
                with (root/'receipt-client.log').open('w') as log:
                    result=subprocess.run([str(args.receipt_client.resolve()),str(receipt_path)],input='allow\n',env=receipt_environment,text=True,stdout=subprocess.PIPE,stderr=log,timeout=10)
                if result.returncode!=0 and args.receipt_clock_diagnostic:
                    diagnostic=subprocess.run([str(args.receipt_clock_diagnostic.resolve()),str(receipt_path)],env=receipt_environment,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10)
                    if diagnostic.returncode==0:
                        facts=json.loads(diagnostic.stdout)
                        allowed={'diagnostic_only','signature_and_binding_valid','ordinary_local_time_accepts','issued_minus_local_received_ms','rpc_elapsed_ms'}
                        assert set(facts)==allowed and facts['diagnostic_only'] is True
                        print('Receipt clock diagnostic: '+json.dumps(facts,sort_keys=True),flush=True)
                    else:print('Receipt clock diagnostic transport refused',flush=True)
                receipt_result=json.loads(result.stdout) if result.returncode==0 else {}
                assert result.returncode==0 and receipt_result.get('allowed') is True,'Kubernetes native receipt refused'
                if args.observed:
                    assert receipt_result.get('contract')=='hopae-observed-sdk-v1' and all(
                        receipt_result.get(step) is True for step in ['issued','independently_observed','refreshed']
                    ),'observed qualification requires actual SDK issue/independent observation/consuming refresh client'
                print('PASS: actual Hopae Pod native issuer and independent management-host client verify request-bound authentication over mTLS Service DNS'+(' using observed issue, independent observation and consuming refresh' if args.observed else ''))
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
            policy_route=next((route['path'] for route in manifest['routes'] if route['method']=='GET' and route['path'] in ['policy/document','policy']),None)
            assert policy_route is not None,'owned plugin has no declared policy read route'
            assert api(admin,f'/v1/plugins/{plugin_id}/{policy_route}')[0]==200
            if args.browser_probe:
                browser_config=root/'browser.json'
                browser_config.write_text(json.dumps({'base':f'http://127.0.0.1:{admin}','token':tokens['gateway-admin'],'plugin':plugin_id,'hopae':bool(args.hopae_plugin),'resourceCatalog':args.resource_catalog,'application':{'gatewayPort':public,'backendPort':backend,'ca':str(root/'ca.pem'),'key':default_key},'hopaeRestart':{'kubectl':str(wrapper),'namespace':namespace},'nativeSource':({'kubectl':str(wrapper),'namespace':namespace,'name':'native','uid':native_policy_uid} if args.sumunjang_native_source else None)}))
                if args.composition:
                    browser_document=json.loads(browser_config.read_text())
                    browser_document['application']['credentialScheme']='hopae_compose'
                    browser_document['redactionSecrets']=[*tokens.values(),composition_key]
                    browser_config.write_text(json.dumps(browser_document))
                subprocess.run([node,str(args.browser_probe.resolve()),str(browser_config)],check=True,timeout=240)
            status,document,metadata=api(admin,'/v1/pumgye/policy');assert status==200
            if args.resource_catalog:
                baseline=json.loads(json.dumps(document['policy']['resources']))
                for field,value in [('information_class','restricted'),('minimum_aal',1),('service','billing')]:
                    document['policy']['resources']['db:orders'][field]=value
                    status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                    qualification_phase='catalog-denial:'+field
                    decision,_=request()
                    assert status==200 and decision==403,f'catalog denial field={field}, publication_status={status}, request={request.last}'
                    document['policy']['resources']=json.loads(json.dumps(baseline))
                    status,document,_=api(admin,'/v1/pumgye/policy','PUT',document,extra={'If-Match':f'"{document["revision"]}"','x-hangang-config-revision':metadata['x-hangang-config-revision']})
                    qualification_phase='catalog-restoration:'+field
                    decision,_=request()
                    assert status==200 and decision==200,f'catalog restoration field={field}, publication_status={status}, request={request.last}'
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
            # Readiness is TCP-only: fresh owned diagnostic GETs must fail closed
            # while native mTLS dependencies reconnect. Every refusal is checked
            # against the backend counter by request(); no request is replayed.
            for _ in range(20):
                restart_status=request()[0]
                assert restart_status in (200,503),'gateway restart returned unexpected status '+str(restart_status)
                if restart_status==200:break
                print('Gateway restart dependency reconnect remains fail-closed',flush=True)
                time.sleep(.1)
            else:raise AssertionError('gateway did not recover after owned Pod replacement')
            if args.sumunjang_native_source:
                assert api(admin,f'/v1/plugins/{plugin_id}/blocks','POST',{'network':'127.0.0.1/32','expires_at':int(time.time())+600,'reason':'must be refused'})[0]==409
                assert api(admin,f'/v1/plugins/{plugin_id}/blocks','DELETE',{'network':'127.0.0.1/32'})[0]==409
                native_patch({'blocks':[{'network':'127.0.0.1/32','expires_at':int(time.time())+600,'reason':'owned CRD fixture'}]})
                eventually(lambda:request()[0]==403)
                native_patch({'blocks':[]});eventually(lambda:request()[0]==200)
                print('PASS: operator CRD block403/unblock200, source-owned manual409 and actual backend non-dispatch',flush=True)
                kube('-n',namespace,'patch','role','native-source','--type=merge','-p',json.dumps({'rules':[]}))
                eventually(lambda:not source_report().get('available') and source_ready()==503)
                for _ in range(3):assert request()[0]==503
                previous=json.loads(kube('-n',namespace,'get','pods','-l','app=sumunjang','-o','json'))['items'][0]['metadata']['uid']
                kube('-n',namespace,'rollout','restart','deployment/sumunjang')
                def replacement():
                    return next((p for p in json.loads(kube('-n',namespace,'get','pods','-l','app=sumunjang','-o','json'))['items'] if p['metadata']['uid']!=previous and p['status'].get('phase')=='Running'),None)
                eventually(replacement,120)
                native_management=forward('sumunjang',9080);native_readiness=forward('sumunjang',9083)
                assert not source_report().get('available') and source_ready()==503
                for _ in range(3):assert request()[0]==503
                kube('-n',namespace,'patch','role','native-source','--type=merge','-p',json.dumps({'rules':source_role['rules']}))
                eventually(lambda:source_report().get('available') and source_ready()==200)
                kube('-n',namespace,'rollout','status','deployment/sumunjang','--timeout=120s')
                eventually(lambda:request()[0]==200)
                print('PASS: live source RBAC withdrawal/readiness503 and persistent checkpoint Pod replacement never dispatch, fresh authenticated recovery',flush=True)
                kube('-n',namespace,'delete','sumunjangpolicy','native','--wait=true')
                eventually(lambda:not source_report().get('available') and source_ready()==503)
                kube('create','-f','-',body=json.dumps(native_policy).encode())
                new_uid=json.loads(kube('-n',namespace,'get','sumunjangpolicy','native','-o','json'))['metadata']['uid'];assert new_uid!=native_policy_uid
                for _ in range(3):assert request()[0]==503
                source_config['uid']=new_uid;config_map['data']['sumunjang-source.json']=json.dumps(source_config)
                kube('-n',namespace,'patch','configmap','world-config','--type=merge','-p',json.dumps({'data':{'sumunjang-source.json':json.dumps(source_config)}}))
                time.sleep(.2);assert not source_report().get('available') and request()[0]==503
                kube('-n',namespace,'rollout','restart','deployment/sumunjang');kube('-n',namespace,'rollout','status','deployment/sumunjang','--timeout=120s',timeout=135)
                native_management=forward('sumunjang',9080);native_readiness=forward('sumunjang',9083)
                eventually(lambda:source_report().get('available') and source_ready()==200 and request()[0]==200)
                native_policy_uid=new_uid
                print('PASS: actual source deletion/UID replacement/config-only edit fail closed; explicit repin+new generation recovers full observed chain',flush=True)
            else:
                assert api(admin,f'/v1/plugins/{plugin_id}/blocks','POST',{'network':'127.0.0.1/32','expires_at':int(time.time())+600,'reason':'owned K8s fixture'},tokens['gateway-admin'])[0]==200
                assert request()[0]==403
                assert api(admin,f'/v1/plugins/{plugin_id}/blocks','DELETE',{'network':'127.0.0.1/32'},tokens['gateway-admin'])[0]==200 and request()[0]==200
            if args.composition:
                relay_port=forward('relay',9443)
                def relay_state(unavailable=None):
                    class Relay(http.client.HTTPSConnection):
                        def connect(self):self.sock=ctx.wrap_socket(socket.create_connection(('127.0.0.1',relay_port),timeout=3),server_hostname='relay.'+namespace+'.svc')
                    connection=Relay('relay.'+namespace+'.svc',9443,timeout=3)
                    connection.request('GET' if unavailable is None else 'POST','/__state',body=None if unavailable is None else json.dumps({'unavailable':unavailable}),headers={'Authorization':'Bearer '+tokens['relay-control'],'Content-Type':'application/json'})
                    response=connection.getresponse();value=json.loads(response.read());connection.close();assert response.status==200;return value
                relay_state(True)
                for _ in range(3):assert request()[0]==503
                count=relay_state()['calls']
                assert request()[0]==503 and relay_state()['calls']==count,'open circuit contacted unavailable relay'
                relay_state(False)
                assert request()[0]==503 and relay_state()['calls']==count,'provider recovery silently bypassed open circuit'
                # Explicit owned Pod replacement gives a new source/runtime owner;
                # durable profile/replay history stays on its original PVC.
                kube('-n',namespace,'rollout','restart','deployment/hopae')
                kube('-n',namespace,'rollout','status','deployment/hopae','--timeout=120s',timeout=135)
                eventually(lambda:request()[0]==200)
                print('PASS: actual HTTPS relay outage opens circuit, suppresses calls after peer recovery, explicit Hopae Pod replacement preserves durable configuration and recovers fresh observed composition')
            kube('-n',namespace,'scale','deployment/sumunjang','--replicas=0')
            kube('-n',namespace,'wait','--for=delete','pod','-l','app=sumunjang','--timeout=60s')
            assert request()[0]==503
            print(('PASS: native Kubernetes Sum source and scratch HTTPGet readiness; ' if args.sumunjang_native_source else '')+'PASS: actual four independent K8s Pods, nonroot static artifacts, mTLS Service DNS, protected request identity, method/guest denial, real pinned console discovery/assets, mTLS plugin management reads/mutations, delegated policy CAS, immediate revocation, PVC/authority/gateway Pod replacement, private administrator state, refused backend non-dispatch and network authority outage')
        except Exception as failure:
            print('Owned qualification failed: '+type(failure).__name__,flush=True)
            facts={'at_unix_ms':round(time.time()*1000),'phase':locals().get('qualification_phase','startup'),'last_request':getattr(locals().get('request'),'last',None)}
            if args.sumunjang_native_source and 'source_report' in locals():
                try:
                    report=source_report()
                    facts['source']={name:report[name] for name in ['available','generation','revision','policy_revision','network_revision','source_revision'] if name in report and isinstance(report[name],(bool,int,str))}
                    facts['source_readiness_status']=source_ready()
                except Exception: facts['source_diagnostic']='unavailable'
            if 'admin' in locals() and 'api' in locals():
                try:
                    code,status,_=api(admin,'/v1/status')
                    facts['root_status']={'http_status':code,**{name:status[name] for name in ['version','uptime_secs','revision','config_revision','generation'] if name in status and isinstance(status[name],(bool,int,str))}}
                except Exception:facts['root_diagnostic']='unavailable'
            print('Owned safe failure facts: '+json.dumps(facts,sort_keys=True),flush=True)
            if args.evidence_dir:(args.evidence_dir/'failure-facts.json').write_text(json.dumps(facts,indent=2)+'\n')
            if created:
                for name in commands:
                    try:
                        diagnostic=kube('-n',namespace,'logs','deployment/'+name,'--tail=200').decode(errors='replace')
                        for value in [*tokens.values(),*([composition_key] if args.composition else [])]:diagnostic=diagnostic.replace(value,'[redacted]')
                        for file in ['server.key','client.key','ca.key']:diagnostic=diagnostic.replace((root/file).read_text(),'[redacted key]')
                        if args.evidence_dir:(args.evidence_dir/(name+'.log')).write_text(diagnostic[-65536:])
                        print('Owned diagnostic '+name+': '+diagnostic[-4000:],flush=True)
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
            if owned_crd_uid:
                current=json.loads(kube('get','crd',crd_name,'-o','json'))
                assert current['metadata']['uid']==owned_crd_uid,'owned CRD replaced; refusing cleanup'
                assert not json.loads(kube('get','sumunjangpolicies','-A','-o','json'))['items'],'other CRD instances exist; refusing cleanup'
                # Qualification requires no concurrent operator creating other
                # native policy instances. UID+RV preconditions prevent deleting
                # a replaced global object between this read and DELETE.
                options={'apiVersion':'v1','kind':'DeleteOptions','preconditions':{'uid':owned_crd_uid,'resourceVersion':current['metadata']['resourceVersion']}}
                kube('delete','--raw','/apis/apiextensions.k8s.io/v1/customresourcedefinitions/'+crd_name,'-f','-',body=json.dumps(options).encode())
                kube('wait','--for=delete','crd/'+crd_name,'--timeout=60s')
                print('Exact created CRD UID cleaned after instance absence check',flush=True)


if __name__=='__main__':main()
