"""Actual Root route owner and immutable Human dispatch fixture configuration."""
import base64
import hashlib
import http.client
import pathlib
import secrets
import ssl
import struct
import time
import urllib.parse
from supervisor import private, require
import bootstrap


def destination(origin):
    parsed=urllib.parse.urlsplit(origin)
    require(parsed.scheme in ('http','https') and parsed.hostname=='127.0.0.1' and not parsed.username and parsed.path in ('','/') and not parsed.query and not parsed.fragment,'fixed_origin')
    scheme=parsed.scheme.encode();host=parsed.hostname.encode();port=parsed.port or (443 if parsed.scheme=='https' else 80)
    framed=b'hangang-human-origin-v1\0'+struct.pack('>I',len(scheme))+scheme+struct.pack('>I',len(host))+host+struct.pack('>H',port)
    return hashlib.sha256(framed).hexdigest()


def source_scope(origin):
    return {'service':'orders','audience':'orders-api','application':'app','route':'owned-route','route_revision':11,'destination_sha256':destination(origin),'header_revision':13,'headers':['x-tenant'],'reserved_headers':['authorization'],'maximum_entity_bytes':16777216}

class NativeRoot:
    def __init__(self, supervisor, tls, backend_origin, hop, pum, sumready, hop_caller, pum_caller, route_caller, decision_endpoint=None):
        self.supervisor=supervisor;self.tls=tls;self.root=supervisor.root/'root';self.root.mkdir(mode=0o700)
        self.listen=bootstrap.two.port();self.admin=bootstrap.two.port();self.route_port=bootstrap.two.port()
        self.route_transport=dict(tls,address=f'https://127.0.0.1:{self.route_port}',token_env='FOUR_ROUTE_CALLER')
        self.route_caller=route_caller;self.hop_caller=hop_caller;self.pum_caller=pum_caller
        native={'audience':'orders-api','issuer_ref':hop['issuer_ref'],'key_epoch':1,'public_key':hop['public_key'],'permission_permit':{'issuer_ref':'pumgye','key_epoch':1,'public_key':pum.public_key},'project_credentials':True,'maximum_body_bytes':1048576,'body_timeout_ms':1000,'observed':{'authentication_class':'human','identity_authority':'owned-human','minimum_profile_revision':7,'minimum_application_generation':1,'minimum_key_registry_revision':1,'source_error_ppm':500,'receiver_error_ppm':500,'maximum_final_header_bytes':32768},'human_binding':{'app_id':'app','header_policy_revision':13,'header_names':['x-tenant']}}
        authority={'transport':'grpc','decision_address':(decision_endpoint or pum.endpoint).removeprefix('https://'),'management_address':pum.admin_endpoint.removeprefix('https://'),'decision_token_env':'FOUR_PUM_CALLER','admin_token_env':'FOUR_PUM_ADMIN','pool_size':8,'timeout_ms':1000,'minimum_revision':1,'tls':tls}
        route={'id':'owned-route','host':'app.example.test','path_prefix':'/effect','access_mode':'protected','backends':[backend_origin],'auth':{'url':'http://127.0.0.1:9/_hopae/verify','native':{'transport':'grpc','address':hop['endpoint'].removeprefix('https://'),'pool_size':8,'tls':tls},'request_headers':['cookie','user-agent'],'response_headers':['x-forwarded-user','x-hopae-aal','x-hopae-principal-kind'],'static_request_headers':{'x-hopae-gateway-key':{'env':'FOUR_HOP_CALLER'}},'native_resource':native},'resource_policy':{'resource_id':'orders','principal':{'source':'external','subject_header':'x-forwarded-user'},'allow':[],'pumgye_resource':{'service_id':'orders','resource':'db:orders','actions':{'POST':'select','GET':'select'}}}}
        private(self.root/'config.json',{'revision':11,'http':[route],'pumgye_authority':authority})
        private(self.root/'route-owner.json',{'listen':f'127.0.0.1:{self.route_port}','certificate':tls['certificate'],'key':tls['key'],'client_ca':tls['ca'],'token_env':'FOUR_ROUTE_CALLER'})
        self.argv=[supervisor.entries['hangang']['binary'],'--config',str(self.root/'config.json'),'--listen',f'127.0.0.1:{self.listen}','--admin',f'127.0.0.1:{self.admin}','--tls-cert',tls['certificate'],'--tls-key',tls['key'],'--advertised-port','443','--route-owner-config',str(self.root/'route-owner.json'),'--trusted-proxy-cidrs','127.0.0.1/32','--guard-url',sumready['http_url'],'--guard-decision-tcp',sumready['endpoint'].removeprefix('https://'),'--guard-decision-grpc','--guard-decision-server-name','localhost','--guard-decision-ca',tls['ca'],'--guard-decision-cert',tls['certificate'],'--guard-decision-key',tls['key'],'--guard-token-env','FOUR_SUM_CALLER','--guard-timeout-ms','1000']
        self.environment={'HANGANG_ADMIN_TOKEN':secrets.token_urlsafe(36),'FOUR_HOP_CALLER':hop_caller,'FOUR_PUM_CALLER':pum_caller,'FOUR_PUM_ADMIN':pum.admin,'FOUR_ROUTE_CALLER':route_caller,'FOUR_SUM_CALLER':pathlib.Path(sumready['collector_file']).read_text()}
        self.context=ssl.create_default_context(cafile=tls['ca'])

    def start(self):
        self.process=self.supervisor.start('hangang',self.argv,self.environment)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            require(self.process.poll() is None,'root_startup_exit')
            try:
                conn=http.client.HTTPSConnection('127.0.0.1',self.listen,context=self.context,timeout=.2)
                conn.request('GET','/owned-readiness',headers={'Host':'unmatched.example.test'});response=conn.getresponse();response.read(4096);conn.close();break
            except OSError:time.sleep(.05)
        else:raise RuntimeError('root_readiness')

    def effect(self,cookie_file,body=b'actual-human-effect'):
        cookie=pathlib.Path(cookie_file).read_text()
        conn=http.client.HTTPSConnection('127.0.0.1',self.listen,context=self.context,timeout=5)
        try:
            conn.request('POST','/effect',body=body,headers={'Host':'app.example.test','X-Forwarded-For':'192.0.2.10','Cookie':'__Host-hopae='+cookie,'x-tenant':'owned-tenant','Content-Type':'application/octet-stream'})
            response=conn.getresponse();data=response.read(65537)
            require(len(data)<=65536,'root_response_bound')
            known={b'resource permission denied':'resource_permission_denied',b'authorization refused':'authorization_refused',b'Pumgye authority unavailable':'pumgye_authority_unavailable',b'native authentication context unavailable':'native_authentication_context_unavailable',b'native resource authority unavailable':'native_resource_authority_unavailable',b'native resource permission denied':'native_resource_permission_denied',b'native route owner unavailable':'native_route_owner_unavailable',b'Human projection slot unavailable':'human_projection_slot_unavailable',b'native dispatch transport unavailable':'native_dispatch_transport_unavailable'}
            result={'status':response.status,'body_length':len(data),'body_sha256':hashlib.sha256(data).hexdigest()}
            if response.status!=200 and data in known:result['fixed_error']=known[data]
            return result
        finally:conn.close()
