#!/usr/bin/env python3
"""Private local fixture: real production Hop portal -> native Human RPC. No proof factories."""
import signal,argparse,base64,hashlib,hmac,html,http.client,http.cookies,http.server,json,os,pathlib,re,secrets,socket,struct,subprocess,sys,threading,time,urllib.parse
from cryptography.hazmat.primitives.asymmetric import rsa,padding,ed25519
from cryptography.hazmat.primitives import hashes,serialization
os.umask(0o077)
def b64(x):return base64.urlsafe_b64encode(x).decode().rstrip('=')
def private(p,data):
 p=pathlib.Path(p);temporary=p.with_name(p.name+'.pending-'+secrets.token_hex(8))
 try:
  descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(descriptor,'w') as output:
   output.write(data if isinstance(data,str) else json.dumps(data,indent=2)+'\n');output.flush();os.fsync(output.fileno())
  os.replace(temporary,p)
 finally:temporary.unlink(missing_ok=True)
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def need(ok,stage):
 if not ok:raise RuntimeError(stage)
def form(body,name):
 m=re.search(r'name="'+re.escape(name)+r'"[^>]*value="([^"]*)"',body);need(m,'missing_form_'+name);return html.unescape(m[1])
def code(seed):
 key=base64.b32decode(seed+'='*((8-len(seed)%8)%8));x=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=x[-1]&15;return f'{(struct.unpack(">I",x[o:o+4])[0]&0x7fffffff)%1000000:06d}'
class Issuer:
 def __init__(self):
  self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048);self.codes={};outer=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def reply(self,status,obj=None,location=None):
    data=json.dumps(obj).encode() if obj is not None else b'';self.send_response(status)
    if location:self.send_header('Location',location)
    self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   def do_GET(self):
    u=urllib.parse.urlsplit(self.path);q={k:v[0] for k,v in urllib.parse.parse_qs(u.query).items()}
    if u.path=='/.well-known/openid-configuration':self.reply(200,{'issuer':outer.url,'authorization_endpoint':outer.url+'/authorize','token_endpoint':outer.url+'/token','jwks_uri':outer.url+'/jwks','response_types_supported':['code'],'subject_types_supported':['public'],'id_token_signing_alg_values_supported':['RS256']})
    elif u.path=='/jwks':
     n=outer.key.public_key().public_numbers();self.reply(200,{'keys':[{'kty':'RSA','kid':'owned','use':'sig','alg':'RS256','n':b64(n.n.to_bytes(256,'big')),'e':b64(n.e.to_bytes(3,'big'))}]})
    elif u.path=='/authorize':
     need(q.get('client_id')=='native-owned-client' and q.get('code_challenge_method')=='S256','issuer_authorize');c=secrets.token_urlsafe(24);outer.codes[c]=q;self.reply(302,location=q['redirect_uri']+'?'+urllib.parse.urlencode({'code':c,'state':q['state']}))
    else:self.reply(404)
   def do_POST(self):
    need(self.path=='/token','issuer_token_path');q={k:v[0] for k,v in urllib.parse.parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()).items()};old=outer.codes.pop(q['code']);need(q.get('redirect_uri')==old['redirect_uri'] and b64(hashlib.sha256(q['code_verifier'].encode()).digest())==old['code_challenge'],'issuer_pkce');now=int(time.time());h=b64(json.dumps({'alg':'RS256','kid':'owned','typ':'JWT'},separators=(',',':')).encode());p=b64(json.dumps({'iss':outer.url,'sub':'owned-native-subject','aud':'native-owned-client','iat':now,'exp':now+300,'auth_time':now,'nonce':old['nonce'],'name':'Native'},separators=(',',':')).encode());signed=(h+'.'+p).encode();jwt=h+'.'+p+'.'+b64(outer.key.sign(signed,padding.PKCS1v15(),hashes.SHA256()));self.reply(200,{'id_token':jwt,'access_token':'owned-only','token_type':'Bearer','expires_in':300})
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.url='http://127.0.0.1:'+str(self.server.server_port);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def close(self):self.server.shutdown();self.server.server_close()
class Browser:
 def __init__(self,fixture):self.f=fixture;self.cookies={}
 def request(self,host,target,method='GET',fields=None,gateway=False):
  h={'Host':host,'x-forwarded-proto':'https','x-forwarded-for':'192.0.2.10','Accept':'text/html','sec-fetch-mode':'navigate','sec-fetch-dest':'document','sec-fetch-site':'same-origin'}
  jar=self.cookies.setdefault(host,{});
  if jar:h['Cookie']='; '.join(k+'='+v for k,v in jar.items())
  if gateway:h.update({'x-hopae-gateway-key':self.f.caller,'x-hopae-contract':'1','x-original-url':'https://'+host+target,'x-original-method':method,'x-hangang-canonical-path':urllib.parse.urlsplit(target).path,'x-hangang-route-id':'owned-route','x-forwarded-host':host})
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
 def portal(self,url,method='GET',fields=None):
  u=urllib.parse.urlsplit(url);need(u.hostname=='auth.example.test','portal_fixed_host');return self.request(u.hostname,u.path+('?' +u.query if u.query else ''),method,fields)
 def login(self):
  s,h,b=self.request('app.example.test','/data',gateway=True);need(s==302,'gateway_login_'+str(s));location=h['location'];s,h,b=self.portal(location);txn=urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)['txn'][0]
  if s==200:s,h,b=self.request('auth.example.test','/login/native','POST',{'csrf':form(b,'csrf'),'txn':txn})
  if self.f.provider=='ldap':
   need(s==200,'ldap_password_page_'+str(s));s,h,b=self.request('auth.example.test','/login/native/password','POST',{'csrf':form(b,'csrf'),'challenge':form(b,'challenge'),'username':'alice','password':self.f.ldap_password})
  else:
   need(s==302,'oidc_redirect_'+str(s));u=urllib.parse.urlsplit(h['location']);c=http.client.HTTPConnection(u.hostname,u.port,timeout=5);c.request('GET',u.path+'?'+u.query);r=c.getresponse();need(r.status==302,'oidc_authorize');callback=r.getheader('Location');r.read();c.close();s,h,b=self.portal(callback)
  need(s==302,'provider_callback_'+str(s));u=urllib.parse.urlsplit(h['location']);need(u.hostname=='app.example.test','handoff_host');s,h,b=self.request(u.hostname,u.path+'?'+u.query,gateway=True);need(s in (200,302),'handoff_'+str(s));need('__Host-hopae' in self.cookies['app.example.test'],'app_cookie')
 def enroll_and_elevate(self):
  if self.f.totp_seed is None:
   s,h,b=self.request('auth.example.test','/security/totp');need(s==200,'totp_get_'+str(s));s,h,b=self.request('auth.example.test','/security/totp/prepare','POST',{'csrf':form(b,'csrf')});need(s==200,'totp_prepare_'+str(s));m=re.search(r'id="totp-key"[^>]*value="([^"]+)"',b);need(m,'totp_seed');seed=html.unescape(m[1]);s,h,b=self.request('auth.example.test','/security/totp/confirm','POST',{'csrf':form(b,'csrf'),'enrollment':form(b,'enrollment'),'code':code(seed)});need(s==200,'totp_confirm_'+str(s));self.f.totp_seed=seed
  seed=self.f.totp_seed;counter=int(time.time())//30
  while int(time.time())//30==counter:time.sleep(.1)
  s,h,b=self.request('app.example.test','/elevated',gateway=True);need(s==302,'stepup_redirect_'+str(s));s,h,b=self.portal(h['location']);need(s==200,'stepup_get_'+str(s));s,h,b=self.request('auth.example.test','/stepup','POST',{'csrf':form(b,'csrf'),'txn':form(b,'txn'),'code':code(seed)});need(s==302,'stepup_post_'+str(s));u=urllib.parse.urlsplit(h['location']);s,h,b=self.request(u.hostname,u.path+('?' +u.query if u.query else ''),gateway=True);need(s in (200,302),'stepup_handoff_'+str(s))
 def revoke(self):
  s,h,b=self.request('auth.example.test','/logout');need(s==200,'logout_get_'+str(s));s,h,b=self.request('auth.example.test','/logout','POST',{'csrf':form(b,'csrf')});need(s in (200,302),'logout_post_'+str(s))
class OwnedLdap:
 def __init__(self,root,starttls):
  self.root=root/'ldap';self.root.mkdir(mode=0o700);(self.root/'db').mkdir(mode=0o700);self.name='owned-human-native-ldap-'+secrets.token_hex(6);self.bind=secrets.token_hex(32);self.password=secrets.token_hex(32);self.port=port();self.start_port=port()
  import shutil
  for f in ('ca.pem','peer.pem','peer.key'):shutil.copyfile(root/f,self.root/f)
  private(self.root/'slapd.conf','include /etc/ldap/schema/core.schema\ninclude /etc/ldap/schema/cosine.schema\ninclude /etc/ldap/schema/inetorgperson.schema\npidfile /owned/slapd.pid\nargsfile /owned/slapd.args\nmodulepath /usr/lib/ldap\nmoduleload back_mdb\nTLSCACertificateFile /owned/ca.pem\nTLSCertificateFile /owned/peer.pem\nTLSCertificateKeyFile /owned/peer.key\ndatabase mdb\nmaxsize 16777216\nsuffix "dc=example,dc=test"\nrootdn "cn=reader,dc=example,dc=test"\nrootpw '+self.bind+'\ndirectory /owned/db\naccess to * by dn.exact="cn=reader,dc=example,dc=test" manage by self read by anonymous auth\n')
  ldif='dn: dc=example,dc=test\nobjectClass: dcObject\nobjectClass: organization\ndc: example\no: Owned fixture\n\ndn: uid=alice,dc=example,dc=test\nobjectClass: inetOrgPerson\nuid: alice\ncn: Alice\nsn: Owned\nuserPassword: '+self.password+'\n'
  image='hopae/owned-openldap:bookworm';subprocess.run(['docker','image','inspect',image],check=True,capture_output=True);subprocess.run(['docker','run','--rm','-i','-v',str(self.root)+':/owned',image,'slapadd','-f','/owned/slapd.conf'],input=ldif.encode(),check=True,capture_output=True)
  try:
   subprocess.run(['docker','run','-d','--rm','--network','host','--name',self.name,'-v',str(self.root)+':/owned',image,'slapd','-f','/owned/slapd.conf','-h',f'ldaps://127.0.0.1:{self.port} ldap://127.0.0.1:{self.start_port}','-d','0'],check=True,capture_output=True)
   deadline=time.monotonic()+5
   while True:
    try:
     with socket.create_connection(('127.0.0.1',self.port),timeout=.2):break
    except OSError:
     need(time.monotonic()<deadline,'ldap_readiness');time.sleep(.05)
  except BaseException:self.close();raise
  self.config={'endpoint':('ldap://127.0.0.1:'+str(self.start_port)) if starttls else ('ldaps://127.0.0.1:'+str(self.port)),'starttls':starttls,'ca':str(self.root/'ca.pem'),'base_dn':'dc=example,dc=test','bind_dn':'cn=reader,dc=example,dc=test','bind_password_env':'OWNED_LDAP_BIND_KEY','username_attribute':'uid','subject_attribute':'entryUUID','timeout_ms':1000}
 def close(self):subprocess.run(['docker','rm','-f',self.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
class Fixture:
 def __init__(self,args):
  self.root=pathlib.Path(args.directory);self.root.mkdir(mode=0o700,parents=True,exist_ok=False);self.provider=args.provider;self.issuer=Issuer() if self.provider=='oidc' else None;self.portal=port();self.gateway=port();self.grpc=port();self.caller=secrets.token_urlsafe(36);self.browsers={};self.process=None;self.totp_seed=None;self.ldap=None;self.ldap_password=None
  def sslcmd(*a):subprocess.run(['openssl',*a],cwd=self.root,check=True,capture_output=True)
  sslcmd('req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=owned-ca','-keyout','ca.key','-out','ca.pem','-addext','basicConstraints=critical,CA:TRUE')
  sslcmd('req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=localhost','-keyout','peer.key','-out','peer.csr');private(self.root/'extensions','basicConstraints=critical,CA:FALSE\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth\n');sslcmd('x509','-req','-in','peer.csr','-CA','ca.pem','-CAkey','ca.key','-CAcreateserial','-days','1','-extfile','extensions','-out','peer.pem')
  if self.provider=='ldap':
   if 'OWNED_LDAP_CONFIG' not in os.environ:self.ldap=OwnedLdap(self.root,args.ldap_starttls)
   self.ldap_password=self.ldap.password if self.ldap else os.environ['OWNED_LDAP_USER_PASSWORD']
  seed=secrets.token_bytes(32);pub=ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);scope={'service':'orders','audience':'orders-api','application':'app','route':'owned-route','route_revision':11,'destination_sha256':'12'*32,'header_revision':13,'headers':[],'reserved_headers':['x-owned-secret'],'maximum_entity_bytes':16777216}
  provider={'provider_id':'native','kind':'oidc','client_id':'native-owned-client','issuer':self.issuer.url,'allow_private_endpoints':True,'client_secret_env':'OWNED_PROVIDER_SECRET'} if self.provider=='oidc' else {'provider_id':'native','kind':'ldap','ldap':self.ldap.config if self.ldap else json.loads(os.environ['OWNED_LDAP_CONFIG'])}
  cfg={'state_dir':str(self.root/'state'),'listen':{'portal':f'127.0.0.1:{self.portal}','gateway':f'127.0.0.1:{self.gateway}','grpc_gateway':f'127.0.0.1:{self.grpc}','native_gateway_tls':{'certificate':str(self.root/'peer.pem'),'key':str(self.root/'peer.key'),'client_ca':str(self.root/'ca.pem')}},'portal':{'public_url':'https://auth.example.test'},'gateway':{'kind':'hangang','caller_key_env':'OWNED_CALLER'},'human_material_key_env':'OWNED_MATERIAL','totp_keyring':{'active_key':'owned','keys':[{'id':'owned','key_env':'OWNED_TOTP'}]},'providers':[provider],'apps':[{'app_id':'app','hosts':['app.example.test'],'binding':{'ip':'strict','ua':'off','on_mismatch':'terminate_session'},'step_up':[{'path_prefix':'/elevated','require':{'aal':2}}]}],'receipt_issuer':{'issuer_ref':'native-human','key_epoch':1,'identity_authority_epoch':'owned-human','public_key':base64.b64encode(pub).decode(),'seed_env':'OWNED_SIGNING','scopes':[{'service':'orders','audience':'orders-api'}],'human_receipts':{'source_revision':7,'scopes':[scope],'capacity':1024,'retained_bytes':33554432}}};private(self.root/'config.json',cfg);private(self.root/'caller',self.caller)
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
  self.metadata={'endpoint':f'https://127.0.0.1:{self.grpc}','server_name':'localhost','ca':str(self.root/'ca.pem'),'certificate':str(self.root/'peer.pem'),'key':str(self.root/'peer.key'),'caller_file':str(self.root/'caller'),'public_key':pub.hex(),'issuer_ref':'native-human','key_epoch':1,'identity_authority':'owned-human','minimum_source_revision':7,'minimum_application_generation':1,'minimum_key_registry_revision':1,'scope':{'service':'orders','audience':'orders-api','app_id':'app','route_id':'owned-route','route_revision':11,'destination_sha256':[18]*32,'header_policy_revision':13,'header_names':[],'reserved_names':['x-owned-secret']},'provider':self.provider,'binary_sha256':hashlib.sha256(pathlib.Path(args.binary).read_bytes()).hexdigest()}
 def login(self,aal):
  need(type(aal) is int and aal in (1,2),'aal');b=Browser(self);b.login()
  if aal==2:b.enroll_and_elevate()
  self.browsers[aal]=b;p=self.root/('cookie-'+str(aal));private(p,b.cookies['app.example.test']['__Host-hopae']);return str(p)
 def close(self):
  if getattr(self,'process',None) is not None:
   self.process.terminate()
   try:self.process.wait(timeout=10)
   except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
  if getattr(self,'issuer',None):self.issuer.close()
  if getattr(self,'ldap',None):self.ldap.close()
  if getattr(self,'log',None):self.log.close()
def main():
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
 parent=os.getppid()
 def watch_parent():
  while os.getppid()==parent:time.sleep(.2)
  os.kill(os.getpid(),signal.SIGTERM)
 threading.Thread(target=watch_parent,daemon=True).start()
 p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--directory',required=True);p.add_argument('--provider',choices=['oidc','ldap'],default='oidc');p.add_argument('--ready',required=True);p.add_argument('--ldap-starttls',action='store_true');a=p.parse_args();f=None
 try:
  f=Fixture.__new__(Fixture);f.__init__(a);f.metadata['cookies']={'1':f.login(1)};private(a.ready,f.metadata)
  while True:
   line=sys.stdin.readline(4097)
   if not line:break
   if len(line)>4096:raise RuntimeError('command_limit')
   try:
    q=json.loads(line);op=q['op'];r={'ok':True,'op':op}
    if op=='login':r.update(aal=q['aal'],cookie_file=f.login(q['aal']))
    elif op=='revoke':f.browsers[q['aal']].revoke()
    elif op=='shutdown':print(json.dumps(r),flush=True);break
    else:raise RuntimeError('unknown_op')
    print(json.dumps(r),flush=True)
   except Exception as e:print(json.dumps({'ok':False,'stage':str(e) if isinstance(e,RuntimeError) else type(e).__name__}),flush=True)
 finally:
  if f:f.close()
if __name__=='__main__':main()
