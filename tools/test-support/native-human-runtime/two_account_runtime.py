#!/usr/bin/env python3
"""Additive actual OIDC portal adapter. No native proof/session constructors."""
from runtime_fixture import *
import runtime_fixture as base


def load_scopes(path):
 data=json.loads(pathlib.Path(path).read_text())
 need(isinstance(data,list) and 1<=len(data)<=16,'scope_count')
 keys={'service','audience','application','route','route_revision','destination_sha256','header_revision','headers','reserved_headers','maximum_entity_bytes'}
 seen=set();application=None
 for s in data:
  need(isinstance(s,dict) and set(s)==keys,'scope_keys')
  for k in ('service','audience','application','route'):
   need(isinstance(s[k],str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',s[k]) is not None,'scope_identifier')
  for k in ('route_revision','header_revision'):
   need(type(s[k]) is int and 1<=s[k]<=9007199254740991,'scope_revision')
  need(isinstance(s['destination_sha256'],str) and re.fullmatch('[0-9a-f]{64}',s['destination_sha256']) is not None and s['destination_sha256']!='0'*64,'scope_destination')
  need(type(s['maximum_entity_bytes']) is int and 0<=s['maximum_entity_bytes']<=16777216,'scope_body_limit')
  for k,limit in [('headers',16),('reserved_headers',64)]:
   need(isinstance(s[k],list) and len(s[k])<=limit and all(isinstance(x,str) and 1<=len(x)<=128 and re.fullmatch(r"[a-z0-9!#$%&'*+.^_`|~-]+",x) for x in s[k]) and len(set(s[k]))==len(s[k]),'scope_header_manifest')
  forbidden={'authorization','proxy-authorization','proxy-authenticate','www-authenticate','cookie','set-cookie','host','forwarded','connection','keep-alive','content-length','transfer-encoding','te','trailer','upgrade','expect'}
  need(all(x not in forbidden and not x.startswith(('x-forwarded-','x-hopae-','x-hangang-','x-pumgye-','x-sumunjang-')) and x not in s['reserved_headers'] for x in s['headers']),'scope_reserved_header')
  identity=(s['service'],s['audience'],s['application'],s['route'],s['route_revision'],s['destination_sha256'],s['header_revision'],tuple(sorted(s['headers'])))
  need(identity not in seen,'scope_duplicate');seen.add(identity)
  if application is None:application=s['application']
  need(s['application']==application,'scope_one_application')
 return data


def sdk_scope(s):
 return {'service':s['service'],'audience':s['audience'],'app_id':s['application'],'route_id':s['route'],'route_revision':s['route_revision'],'destination_sha256':list(bytes.fromhex(s['destination_sha256'])),'header_policy_revision':s['header_revision'],'header_names':s['headers'],'reserved_names':s['reserved_headers']}

class TwoAccountIssuer:
 def __init__(self):
  self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048);self.codes={};outer=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def reply(self,status,obj=None,location=None):
    data=json.dumps(obj).encode() if obj is not None else b'';self.send_response(status)
    if location:self.send_header('Location',location)
    self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   def do_GET(self):
    try:self.get()
    except (RuntimeError,KeyError,ValueError):self.reply(400)
   def get(self):
    self.connection.settimeout(2)
    u=urllib.parse.urlsplit(self.path);q={k:v[0] for k,v in urllib.parse.parse_qs(u.query).items()}
    if u.path=='/.well-known/openid-configuration':self.reply(200,{'issuer':outer.url,'authorization_endpoint':outer.url+'/authorize','token_endpoint':outer.url+'/token','jwks_uri':outer.url+'/jwks','response_types_supported':['code'],'subject_types_supported':['public'],'id_token_signing_alg_values_supported':['RS256']})
    elif u.path=='/jwks':
     n=outer.key.public_key().public_numbers();self.reply(200,{'keys':[{'kty':'RSA','kid':'owned','use':'sig','alg':'RS256','n':b64(n.n.to_bytes(256,'big')),'e':b64(n.e.to_bytes(3,'big'))}]})
    elif u.path=='/authorize':
     need(q.get('client_id')=='native-owned-client' and q.get('code_challenge_method')=='S256' and q.get('owned_account') in ('a','b'),'issuer_authorize');c=secrets.token_urlsafe(24);outer.codes[c]=q;self.reply(302,location=q['redirect_uri']+'?'+urllib.parse.urlencode({'code':c,'state':q['state']}))
    else:self.reply(404)
   def do_POST(self):
    try:self.post()
    except (RuntimeError,KeyError,ValueError):self.reply(400)
   def post(self):
    self.connection.settimeout(2)
    need(self.headers.get('Content-Length','').isdigit() and int(self.headers['Content-Length'])<=8192,'issuer_body_limit')
    need(self.path=='/token','issuer_token_path');q={k:v[0] for k,v in urllib.parse.parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()).items()};old=outer.codes.pop(q['code']);need(q.get('redirect_uri')==old['redirect_uri'] and b64(hashlib.sha256(q['code_verifier'].encode()).digest())==old['code_challenge'],'issuer_pkce');now=int(time.time());h=b64(json.dumps({'alg':'RS256','kid':'owned','typ':'JWT'},separators=(',',':')).encode());p=b64(json.dumps({'iss':outer.url,'sub':'owned-native-subject-'+old['owned_account'],'aud':'native-owned-client','iat':now,'exp':now+300,'auth_time':now,'nonce':old['nonce'],'name':'Native'},separators=(',',':')).encode());signed=(h+'.'+p).encode();jwt=h+'.'+p+'.'+b64(outer.key.sign(signed,padding.PKCS1v15(),hashes.SHA256()));self.reply(200,{'id_token':jwt,'access_token':'owned-only','token_type':'Bearer','expires_in':300})
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.url='http://127.0.0.1:'+str(self.server.server_port);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def close(self):self.server.shutdown();self.server.server_close()
class AccountBrowser(base.Browser):
 def __init__(self,fixture,account):
  super().__init__(fixture);self.account=account
 def request(self,host,target,method='GET',fields=None,gateway=False):
  h={'Host':host,'x-forwarded-proto':'https','x-forwarded-for':'192.0.2.10','Accept':'text/html','sec-fetch-mode':'navigate','sec-fetch-dest':'document','sec-fetch-site':'same-origin'}
  jar=self.cookies.setdefault(host,{});
  if jar:h['Cookie']='; '.join(k+'='+v for k,v in jar.items())
  if gateway:h.update({'x-hopae-gateway-key':self.f.caller,'x-hopae-contract':'1','x-original-url':'https://'+host+target,'x-original-method':method,'x-hangang-canonical-path':urllib.parse.urlsplit(target).path,'x-hangang-route-id':self.f.route,'x-forwarded-host':host})
  if fields is not None:h.update({'Content-Type':'application/x-www-form-urlencoded','Origin':'https://'+host});data=urllib.parse.urlencode(fields)
  else:data=None
  c=http.client.HTTPConnection('127.0.0.1',self.f.gateway if gateway else self.f.portal,timeout=5);c.request(method,'/_hopae/verify' if gateway else target,body=data,headers=h);r=c.getresponse();body=r.read(262144).decode(errors='replace');status=r.status;headers=r.getheaders();c.close()
  for k,v in headers:
   if k.lower()=='set-cookie':
    x=http.cookies.SimpleCookie();x.load(v)
    for name,m in x.items():
     if m['max-age']=='0':jar.pop(name,None)
     else:jar[name]=m.value
  private(self.f.root/'last-response-private.json',{'status':status,'body':body})
  return status,dict((k.lower(),v) for k,v in headers),body
 def login(self):
  s,h,b=self.request('app.example.test','/data',gateway=True);need(s==302,'gateway_login_'+str(s));location=h['location'];s,h,b=self.portal(location);txn=urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)['txn'][0]
  if s==200:s,h,b=self.request('auth.example.test','/login/native','POST',{'csrf':form(b,'csrf'),'txn':txn})
  if self.f.provider=='ldap':
   need(s==200,'ldap_password_page_'+str(s));s,h,b=self.request('auth.example.test','/login/native/password','POST',{'csrf':form(b,'csrf'),'challenge':form(b,'challenge'),'username':'alice','password':self.f.ldap_password})
  else:
   need(s==302,'oidc_redirect_'+str(s));u=urllib.parse.urlsplit(h['location']);c=http.client.HTTPConnection(u.hostname,u.port,timeout=5);c.request('GET',u.path+'?'+u.query+'&owned_account='+self.account);r=c.getresponse();need(r.status==302,'oidc_authorize');callback=r.getheader('Location');r.read();c.close();s,h,b=self.portal(callback)
  need(s==302,'provider_callback_'+str(s));u=urllib.parse.urlsplit(h['location']);need(u.hostname=='app.example.test','handoff_host');s,h,b=self.request(u.hostname,u.path+'?'+u.query,gateway=True);need(s in (200,302),'handoff_'+str(s));need('__Host-hopae' in self.cookies['app.example.test'],'app_cookie')
class Fixture(base.Fixture):
 def __init__(self,args):
  self.root=pathlib.Path(args.directory);self.root.mkdir(mode=0o700,parents=True,exist_ok=False);self.provider='oidc';self.issuer=TwoAccountIssuer();self.portal=port();self.gateway=port();self.grpc=port();self.caller=secrets.token_urlsafe(36);self.browsers={};self.process=None;self.totp_seeds={};self.account='a';self.ldap=None;self.ldap_password=None
  def sslcmd(*a):subprocess.run(['openssl',*a],cwd=self.root,check=True,capture_output=True)
  sslcmd('req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=owned-ca','-keyout','ca.key','-out','ca.pem','-addext','basicConstraints=critical,CA:TRUE')
  sslcmd('req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=localhost','-keyout','peer.key','-out','peer.csr');private(self.root/'extensions','basicConstraints=critical,CA:FALSE\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth\n');sslcmd('x509','-req','-in','peer.csr','-CA','ca.pem','-CAkey','ca.key','-CAcreateserial','-days','1','-extfile','extensions','-out','peer.pem')
  seed=secrets.token_bytes(32);pub=ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);scopes=args.prepared_scopes;scope=scopes[0];self.route=scope['route']
  provider={'provider_id':'native','kind':'oidc','client_id':'native-owned-client','issuer':self.issuer.url,'allow_private_endpoints':True,'client_secret_env':'OWNED_PROVIDER_SECRET'}
  cfg={'state_dir':str(self.root/'state'),'listen':{'portal':f'127.0.0.1:{self.portal}','gateway':f'127.0.0.1:{self.gateway}','grpc_gateway':f'127.0.0.1:{self.grpc}','native_gateway_tls':{'certificate':str(self.root/'peer.pem'),'key':str(self.root/'peer.key'),'client_ca':str(self.root/'ca.pem')}},'portal':{'public_url':'https://auth.example.test'},'gateway':{'kind':'hangang','caller_key_env':'OWNED_CALLER'},'human_material_key_env':'OWNED_MATERIAL','totp_keyring':{'active_key':'owned','keys':[{'id':'owned','key_env':'OWNED_TOTP'}]},'providers':[provider],'apps':[{'app_id':scope['application'],'hosts':['app.example.test'],'binding':{'ip':'strict','ua':'off','on_mismatch':'terminate_session'},'step_up':[{'path_prefix':'/elevated','require':{'aal':2}}]}],'receipt_issuer':{'issuer_ref':'native-human','key_epoch':1,'identity_authority_epoch':'owned-human','public_key':base64.b64encode(pub).decode(),'seed_env':'OWNED_SIGNING','scopes':[{'service':s,'audience':a} for s,a in sorted({(v['service'],v['audience']) for v in scopes})],'human_receipts':{'source_revision':7,'scopes':scopes,'capacity':1024,'retained_bytes':33554432}}};private(self.root/'config.json',cfg);private(self.root/'caller',self.caller)
  env=dict(os.environ,OWNED_CALLER=self.caller,OWNED_MATERIAL=b64(secrets.token_bytes(32)),OWNED_TOTP=b64(secrets.token_bytes(32)),OWNED_SIGNING=base64.b64encode(seed).decode(),OWNED_PROVIDER_SECRET=secrets.token_urlsafe(32))
  if self.ldap:env['OWNED_LDAP_BIND_KEY']=self.ldap.bind
  self.log=open(self.root/'runtime-private.log','w');self.process=subprocess.Popen([args.binary,'--config',str(self.root/'config.json'),'run'],env=env,stdout=self.log,stderr=subprocess.STDOUT)
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   need(self.process.poll() is None,'runtime_exit')
   try:
    c=http.client.HTTPConnection('127.0.0.1',self.portal,timeout=.2);c.request('GET','/healthz');r=c.getresponse();ok=r.status==200;r.read();c.close()
    if ok:break
   except OSError:pass
   time.sleep(.05)
  else:raise RuntimeError('runtime_readiness')
  self.metadata={'endpoint':f'https://127.0.0.1:{self.grpc}','server_name':'localhost','ca':str(self.root/'ca.pem'),'certificate':str(self.root/'peer.pem'),'key':str(self.root/'peer.key'),'caller_file':str(self.root/'caller'),'public_key':pub.hex(),'issuer_ref':'native-human','key_epoch':1,'identity_authority':'owned-human','minimum_source_revision':7,'minimum_application_generation':1,'minimum_key_registry_revision':1,'scope':sdk_scope(scope),'scopes':[sdk_scope(v) for v in scopes],'provider':self.provider,'binary_sha256':hashlib.sha256(pathlib.Path(args.binary).read_bytes()).hexdigest()}

 @property
 def totp_seed(self):return self.totp_seeds.get(self.account)
 @totp_seed.setter
 def totp_seed(self,value):self.totp_seeds[self.account]=value
 def login_account(self,account,aal):
  need(account in ('a','b') and type(aal) is int and aal in (1,2),'login_account')
  self.account=account;b=AccountBrowser(self,account);b.login()
  if aal==2:b.enroll_and_elevate()
  self.browsers[(account,aal)]=b;p=self.root/('cookie-'+account+'-'+str(aal));private(p,b.cookies['app.example.test']['__Host-hopae']);return str(p)

def main():
 p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--directory',required=True);p.add_argument('--ready',required=True);p.add_argument('--source-scopes-json',required=True);a=p.parse_args();f=None
 # Validate only server-owned startup metadata before any owned process is started.
 a.prepared_scopes=load_scopes(a.source_scopes_json)
 need(pathlib.Path(a.ready).parent.resolve()==pathlib.Path(a.directory).resolve() and not pathlib.Path(a.ready).exists(),'ready_owned_path')
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(143));parent=os.getppid()
 def watch_parent():
  while os.getppid()==parent:time.sleep(.2)
  os.kill(os.getpid(),signal.SIGTERM)
 threading.Thread(target=watch_parent,daemon=True).start()
 try:
  f=Fixture.__new__(Fixture);f.__init__(a);f.metadata['accounts']=['a','b'];f.metadata['cookies']={account:{'1':f.login_account(account,1)} for account in ('a','b')};private(a.ready,f.metadata)
  while True:
   line=sys.stdin.readline(4097)
   if not line:break
   if len(line)>4096:raise RuntimeError('command_limit')
   try:
    q=json.loads(line);op=q['op'];r={'ok':True,'op':op}
    if op=='login':r.update(account=q['account'],aal=q['aal'],cookie_file=f.login_account(q['account'],q['aal']))
    elif op=='revoke':
     need(q['account'] in ('a','b') and type(q['aal']) is int and q['aal'] in (1,2),'revoke_account');f.browsers[(q['account'],q['aal'])].revoke()
    elif op=='shutdown':print(json.dumps(r),flush=True);break
    else:raise RuntimeError('unknown_op')
    print(json.dumps(r),flush=True)
   except Exception as e:print(json.dumps({'ok':False,'stage':str(e) if isinstance(e,RuntimeError) else type(e).__name__}),flush=True)
 finally:
  if f:f.close()
if __name__=='__main__':main()
