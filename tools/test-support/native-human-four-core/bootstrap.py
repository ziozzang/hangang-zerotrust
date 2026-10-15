"""Prepare actual native Hop before its first login, with one shared fixture PKI.
Reuses the qualified real OIDC/portal/TOTP browser; never writes session rows.
"""
import base64
import copy
import http.client
import pathlib
import secrets
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'native-human-runtime'))
import two_account_runtime as two
from supervisor import private, require
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def public_key(seed):
    return base64.b64encode(ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

def hop_config(root, addresses, tls, issuer_url, scopes, pum_endpoint, permit_public):
    """All inputs are fixed server-owned fixture setup, not request descriptors."""
    require(set(addresses)=={'portal','gateway','grpc'},'hop_addresses')
    require(scopes and all(s['application']==scopes[0]['application'] for s in scopes),'hop_application')
    cfg={
      'state_dir':str(root/'state'),
      'listen':{'portal':addresses['portal'],'gateway':addresses['gateway'],'grpc_gateway':addresses['grpc'],'native_gateway_tls':{'certificate':tls['certificate'],'key':tls['key'],'client_ca':tls['ca']}},
      'portal':{'public_url':'https://auth.example.test'},
      'gateway':{'kind':'hangang','caller_key_env':'FOUR_HOP_CALLER'},
      'human_material_key_env':'FOUR_MATERIAL',
      'totp_keyring':{'active_key':'owned','keys':[{'id':'owned','key_env':'FOUR_TOTP'}]},
      'providers':[{'provider_id':'native','kind':'oidc','client_id':'native-owned-client','issuer':issuer_url,'allow_private_endpoints':True,'client_secret_env':'FOUR_PROVIDER_SECRET'}],
      'apps':[{'app_id':scopes[0]['application'],'hosts':['app.example.test'],'binding':{'ip':'strict','ua':'off','on_mismatch':'terminate_session'},'step_up':[{'path_prefix':'/elevated','require':{'aal':2}}]}],
      'receipt_issuer':{'issuer_ref':'native-human','key_epoch':1,'identity_authority_epoch':'owned-human','public_key':'','seed_env':'FOUR_SIGNING','scopes':[{'service':s,'audience':a} for s,a in sorted({(x['service'],x['audience']) for x in scopes})],'human_receipts':{'source_revision':7,'scopes':copy.deepcopy(scopes),'capacity':131072,'retained_bytes':268435456}},
      'receipt_permit_keys':[{'issuer_ref':'pumgye','key_epoch':1,'public_key':permit_public}],
      'projection_receiver':{'authority':dict(tls,address=pum_endpoint,token_env='FOUR_PUM_CALLER'),'human_observed_scopes':[dict(service=s,audience=a,application=app,route=r) for s,a,app,r in sorted({(x['service'],x['audience'],x['application'],x['route']) for x in scopes})],'observed_clock_rates':{'source_ppm':500,'receiver_ppm':500},'secrets':[{'reference':'owned:origin','token_env':'FOUR_ORIGIN_SECRET'}]},
      'credential_projection':{'revision':1,'plans':[{'service':s,'audience':a,'minimum_aal':1,'resource':'db:orders','action':'select','credential':{'type':'bearer_reference','secret_ref':'owned:origin'}} for s,a in sorted({(x['service'],x['audience']) for x in scopes})]}}
    return cfg

class NativeHop(two.Fixture):
    """Actual provider/browser behavior; process ownership stays in Supervisor."""
    def __init__(self, supervisor, tls, scopes, pum_endpoint, permit_public, caller, pum_caller, origin_secret):
        self.issuer=None
        try:
            self._initialize(supervisor,tls,scopes,pum_endpoint,permit_public,caller,pum_caller,origin_secret)
        except BaseException:
            self.close()
            raise

    def _initialize(self,supervisor,tls,scopes,pum_endpoint,permit_public,caller,pum_caller,origin_secret):
        self.root=supervisor.root/'hop';self.root.mkdir(mode=0o700)
        self.provider='oidc';self.issuer=two.TwoAccountIssuer();self.process=None;self.log=None;self.ldap=None
        self.browsers={};self.totp_seeds={};self.account='a';self.route=scopes[0]['route'];self.caller=caller
        self.portal=two.port();self.gateway=two.port();self.grpc=two.port()
        addresses={k:'127.0.0.1:'+str(getattr(self,k)) for k in ('portal','gateway','grpc')}
        seed=secrets.token_bytes(32)
        cfg=hop_config(self.root,addresses,tls,self.issuer.url,scopes,pum_endpoint,permit_public)
        cfg['receipt_issuer']['public_key']=public_key(seed)
        private(self.root/'config.json',cfg)
        env={'FOUR_HOP_CALLER':caller,'FOUR_PUM_CALLER':pum_caller,'FOUR_ORIGIN_SECRET':origin_secret,'FOUR_MATERIAL':two.b64(secrets.token_bytes(32)),'FOUR_TOTP':two.b64(secrets.token_bytes(32)),'FOUR_SIGNING':base64.b64encode(seed).decode(),'FOUR_PROVIDER_SECRET':secrets.token_urlsafe(32)}
        self.process=supervisor.start('hopae',[supervisor.entries['hopae']['binary'],'--config',str(self.root/'config.json'),'run'],env)
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            require(self.process.poll() is None,'hop_startup_exit')
            try:
                conn=http.client.HTTPConnection('127.0.0.1',self.portal,timeout=.2)
                conn.request('GET','/healthz');reply=conn.getresponse();ok=reply.status==200;reply.read();conn.close()
                if ok:break
            except OSError:pass
            time.sleep(.05)
        else:raise RuntimeError('hop_readiness')
        private(self.root/'caller',caller.encode())
        self.metadata=dict(tls,caller_file=str(self.root/'caller'),scope=two.sdk_scope(scopes[0]),minimum_source_revision=7,minimum_application_generation=1,minimum_key_registry_revision=1,identity_authority='owned-human',key_epoch=1,**{'endpoint':'https://'+addresses['grpc'],'public_key':cfg['receipt_issuer']['public_key'],'issuer_ref':'native-human','source_revision':7,'scopes':[two.sdk_scope(s) for s in scopes]})

    def close(self):
        # Supervisor owns the exact process; this object owns only the issuer.
        if self.issuer is not None:
            self.issuer.close();self.issuer=None
