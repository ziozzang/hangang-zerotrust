import base64
import copy
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
import urllib.parse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
sys.path.insert(0,str(Path(__file__).parent))
import two_account_runtime as adapter


def scope():
 return {'service':'orders','audience':'orders-api','application':'app','route':'owned-route','route_revision':11,'destination_sha256':'12'*32,'header_revision':13,'headers':['x-intent'],'reserved_headers':['x-owned-secret'],'maximum_entity_bytes':16777216}

class Configuration(unittest.TestCase):
 def load(self,value):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'scope.json';p.write_text(json.dumps(value));return adapter.load_scopes(p)
 def test_server_owned_scopes_preserve_dynamic_destination_and_sorted_manifest_semantics(self):
  first=scope();second=copy.deepcopy(first);second['destination_sha256']='34'*32
  actual=self.load([first,second]);self.assertEqual(len(actual),2)
  converted=adapter.sdk_scope(actual[1]);self.assertEqual(converted['destination_sha256'],[52]*32);self.assertEqual(converted['header_policy_revision'],13)
 def test_rejects_ambiguous_duplicate_reserved_and_invalid_scopes(self):
  mutations=[lambda s:s.update(route_revision=True),lambda s:s.update(destination_sha256='00'*32),lambda s:s.update(headers=['Cookie']),lambda s:s.update(headers=['authorization']),lambda s:s.update(headers=['x-owned-secret']),lambda s:s.update(headers=['x-intent','x-intent']),lambda s:s.update(maximum_entity_bytes=16777217),lambda s:s.update(application='bad\napp'),lambda s:s.update(unknown=True)]
  for mutate in mutations:
   s=scope();mutate(s)
   with self.assertRaises(RuntimeError):self.load([s])
  for values in [[],[scope()]*2,[scope()]*17,[scope(),dict(scope(),application='different')]]:
   with self.assertRaises(RuntimeError):self.load(values)
 def test_prepared_scopes_reach_startup_config_before_process_launch(self):
  # Configuration-only mock: no authentication/session/proof success is claimed.
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'owned';binary=Path(d)/'dummy';binary.write_bytes(b'configuration-only')
   first=scope();second=dict(first,destination_sha256='34'*32)
   args=SimpleNamespace(directory=str(root),binary=str(binary),prepared_scopes=[first,second])
   process=mock.Mock();process.poll.return_value=None
   response=mock.Mock();response.status=200
   connection=mock.Mock();connection.getresponse.return_value=response
   f=adapter.Fixture.__new__(adapter.Fixture)
   with mock.patch.object(adapter.subprocess,'run'),mock.patch.object(adapter.subprocess,'Popen',return_value=process) as launch,mock.patch.object(adapter.http.client,'HTTPConnection',return_value=connection):
    try:
     f.__init__(args)
     config=json.loads((root/'config.json').read_text())
     self.assertEqual(config['receipt_issuer']['human_receipts']['scopes'],args.prepared_scopes)
     self.assertEqual(config['apps'][0]['app_id'],first['application'])
     self.assertEqual(f.route,first['route'])
     self.assertEqual(len(f.metadata['scopes']),2)
     self.assertEqual(launch.call_count,1)
    finally:f.close()
 def test_browser_uses_only_fixed_prepared_route_marker(self):
  with tempfile.TemporaryDirectory() as d:
   fixture=SimpleNamespace(root=Path(d),caller='private-owned-caller',gateway=1,portal=2,route='fixed-route')
   connection=mock.Mock();response=mock.Mock();response.status=200;response.read.return_value=b'';response.getheaders.return_value=[];connection.getresponse.return_value=response
   with mock.patch.object(adapter.http.client,'HTTPConnection',return_value=connection):
    adapter.AccountBrowser(fixture,'a').request('app.example.test','/data',gateway=True)
   self.assertEqual(connection.request.call_args.kwargs['headers']['x-hangang-route-id'],'fixed-route')
 def test_each_account_keeps_separate_totp_seed(self):
  f=adapter.Fixture.__new__(adapter.Fixture);f.totp_seeds={};f.account='a';f.totp_seed='a-private';f.account='b';self.assertIsNone(f.totp_seed);f.totp_seed='b-private';f.account='a';self.assertEqual(f.totp_seed,'a-private')

class ActualOwnedIssuer(unittest.TestCase):
 def setUp(self):self.issuer=adapter.TwoAccountIssuer()
 def tearDown(self):self.issuer.close()
 def request(self,method,path,body=None):
  u=urllib.parse.urlsplit(self.issuer.url);c=http.client.HTTPConnection(u.hostname,u.port,timeout=3);c.request(method,path,body,{'Content-Type':'application/x-www-form-urlencoded'});r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result
 def authorize(self,account):
  verifier='private-verifier-'+account
  q={'client_id':'native-owned-client','code_challenge_method':'S256','code_challenge':adapter.b64(hashlib.sha256(verifier.encode()).digest()),'redirect_uri':'https://auth.example.test/callback','state':'state-'+account,'nonce':'nonce-'+account,'owned_account':account}
  status,headers,_=self.request('GET','/authorize?'+urllib.parse.urlencode(q));self.assertEqual(status,302)
  code=urllib.parse.parse_qs(urllib.parse.urlsplit(headers['Location']).query)['code'][0];return code,verifier
 def token(self,code,verifier):return self.request('POST','/token',urllib.parse.urlencode({'code':code,'code_verifier':verifier,'redirect_uri':'https://auth.example.test/callback'}))
 def test_two_actual_signed_tokens_have_distinct_subjects_and_bound_nonce(self):
  subjects=[]
  for account in ['a','b']:
   code,verifier=self.authorize(account);status,_,raw=self.token(code,verifier);self.assertEqual(status,200)
   jwt=json.loads(raw)['id_token'];h,p,s=jwt.split('.');decode=lambda x:base64.urlsafe_b64decode(x+'='*((4-len(x)%4)%4))
   self.issuer.key.public_key().verify(decode(s),(h+'.'+p).encode(),padding.PKCS1v15(),hashes.SHA256())
   claims=json.loads(decode(p));self.assertEqual(claims['nonce'],'nonce-'+account);self.assertEqual(claims['iss'],self.issuer.url);subjects.append(claims['sub'])
   self.assertEqual(self.token(code,verifier)[0],400)
  self.assertNotEqual(*subjects)
 def test_wrong_pkce_and_unknown_account_cannot_issue(self):
  code,_=self.authorize('a');self.assertEqual(self.token(code,'wrong-verifier')[0],400)
  self.assertEqual(self.request('GET','/authorize?'+urllib.parse.urlencode({'client_id':'native-owned-client','code_challenge_method':'S256','owned_account':'unknown'}))[0],400)

if __name__=='__main__':unittest.main()
