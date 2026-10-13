#!/usr/bin/env python3
"""Validate draft schemas, synthetic bundles, invariants and local documentation links."""
from pathlib import Path
import copy,hashlib,json,re
from datetime import datetime
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
validators={}
for name in ['catalog','policy','bundle','decision','event','membership','projection_request']:
 s=load(f'schemas/{name}.schema.json');Draft202012Validator.check_schema(s);validators[name]=Draft202012Validator(s,format_checker=FormatChecker());validators[name].validate(load(f'examples/{name}.json'))
def check(c,p,b,check_hashes=False):
 validators['catalog'].validate(c);validators['policy'].validate(p);validators['bundle'].validate(b)
 assert c['authority_epoch']==p['authority_epoch']==b['authority_epoch'],'authority epoch mismatch'
 assert c['revision']==p['catalog_revision']==b['catalog_revision'] and p['revision']==b['policy_revision'],'revision mismatch'
 assert datetime.fromisoformat(b['valid_from'].replace('Z','+00:00'))<datetime.fromisoformat(b['valid_until'].replace('Z','+00:00')),'invalid bundle validity'
 resources={};bindings=set();rules=set()
 for resource in c['resources']:
  rid=resource['resource_id'];assert rid not in resources,'duplicate resource';resources[rid]=resource
  for binding in resource['bindings']:
   key=(binding['route_id'],binding['method']);assert key not in bindings,'ambiguous resource/action binding';bindings.add(key);assert binding['action'] in resource['actions'],'unknown binding action'
 for rule in p['rules']:
  assert rule['rule_id'] not in rules,'duplicate rule';rules.add(rule['rule_id']);condition=rule['conditions'];facts=set(condition['required_facts'])
  assert 'network' in facts,'network condition needs network fact'
  assert not (condition['min_aal']>0 or condition['entitlements']) or 'identity' in facts,'identity conditions need identity fact'
  kinds={o['kind'] for o in rule['obligations']};assert kinds<=set(b['supported_obligations']),'unsupported obligation'
  for rid in rule['resources']:
   assert rid in resources,'unknown policy resource';resource=resources[rid]
   assert set(rule['actions'])<=set(resource['actions']),'unknown action'
   assert resource['classification']['level'] in condition['allowed_classes'],'classification conflict'
   assert resource['classification']['level']=='public' or 'identity' in facts,'protected resource cannot grant anonymous access'
   if resource['tenant_mode']=='application_enforced':assert condition['tenant_constraint']=='application_enforced' and 'application_object_authorization' in kinds,'tenant/object enforcement missing'
 if check_hashes:
  for name in ['catalog','policy']:assert hashlib.sha256((ROOT/f'examples/{name}.json').read_bytes()).hexdigest()==b[name+'_sha256'],'bundle hash mismatch'
 return True
c,p,b=(load(f'examples/{name}.json') for name in ['catalog','policy','bundle']);check(c,p,b,True)
cases=[]
def reject(name,change):
 cc,pp,bb=copy.deepcopy((c,p,b));change(cc,pp,bb)
 try:check(cc,pp,bb)
 except (AssertionError,ValidationError):
  cases.append(name);return
 raise AssertionError('unsafe bundle accepted: '+name)
reject('unknown classification',lambda c,p,b:c['resources'][0]['classification'].update(level='unknown'))
reject('forged classification override field',lambda c,p,b:c['resources'][0].update(trust_client_class=True))
reject('ambiguous binding',lambda c,p,b:c['resources'][1]['bindings'].append(copy.deepcopy(c['resources'][0]['bindings'][0])))
reject('stale catalog',lambda c,p,b:p.update(catalog_revision=2))
reject('wrong authority epoch',lambda c,p,b:b.update(authority_epoch='other-authority'))
reject('missing identity for sensitive grant',lambda c,p,b:p['rules'][0]['conditions'].update(required_facts=['network'],min_aal=0,entitlements=[]))
reject('tenant obligation missing',lambda c,p,b:p['rules'][0].update(obligations=[]))
reject('unsupported obligation',lambda c,p,b:b.update(supported_obligations=[]))
reject('unknown action',lambda c,p,b:p['rules'][0].update(actions=['destroy']))
reject('public downgrade policy conflict',lambda c,p,b:c['resources'][0]['classification'].update(level='public'))
reject('backwards validity',lambda c,p,b:b.update(valid_until=b['valid_from']))
# Membership is a separate draft control-plane contract, never an identity proof.
from urllib.parse import urlparse
def check_membership(m,previous=None):
 validators['membership'].validate(m)
 start=datetime.fromisoformat(m['valid_from'].replace('Z','+00:00'));end=datetime.fromisoformat(m['valid_until'].replace('Z','+00:00'))
 assert 0<(end-start).total_seconds()*1000<=m['max_staleness_ms'],'invalid membership lease'
 ids=set();endpoints=set();protocol={'hopae':'HOP1','sumunjang':'HGD1','pumgye':'PPG1'}[m['domain']]
 for node in m['nodes']:
  assert node['node_id'] not in ids,'duplicate member';ids.add(node['node_id'])
  ep=node['endpoint'];key=(ep['host'],ep['port']);assert key not in endpoints,'ambiguous member endpoint';endpoints.add(key)
  assert ep['protocol']==protocol,'wrong domain native protocol'
  identity=urlparse(ep['tls_service_identity']);assert identity.scheme=='spiffe' and identity.netloc and identity.path==f"/{m['domain']}/{node['node_id']}",'wrong member service identity scope'
  if node['state']=='ready':
   assert node['compiled_revision']>=m['minimum_revision'],'ready before snapshot catch-up'
   assert node['snapshot_sha256']!='0'*64,'ready without snapshot digest'
 if previous:
  assert (m['domain'],m['authority_id'],m['authority_epoch'])==(previous['domain'],previous['authority_id'],previous['authority_epoch']),'unapproved authority change'
  assert m['generation']>=previous['generation'] and m['minimum_revision']>=previous['minimum_revision'],'membership/revision rollback'
  if m['generation']==previous['generation']:
   assert m['nodes']==previous['nodes'] and m['minimum_revision']==previous['minimum_revision'],'changed members without generation'
 return True
membership=load('examples/membership.json');check_membership(membership)
def reject_membership(name,change,previous=None):
 candidate=copy.deepcopy(membership);change(candidate)
 try:check_membership(candidate,previous)
 except (AssertionError,ValidationError):cases.append(name);return
 raise AssertionError('unsafe membership accepted: '+name)
reject_membership('stale ready member',lambda m:m['nodes'][0].update(compiled_revision=6))
reject_membership('plaintext member',lambda m:m['nodes'][0]['endpoint'].update(mtls=False))
reject_membership('duplicate node',lambda m:m['nodes'].append(copy.deepcopy(m['nodes'][0])))
reject_membership('cross-domain protocol',lambda m:m['nodes'][0]['endpoint'].update(protocol='HOP1'))
reject_membership('cross-domain peer identity',lambda m:m['nodes'][0]['endpoint'].update(tls_service_identity='spiffe://example.test/hopae/pumgye-a'))
reject_membership('unbounded membership lease',lambda m:m.update(valid_until='2026-01-01T00:00:06Z'))
reject_membership('membership rollback',lambda m:m.update(generation=2),membership)
reject_membership('silent node reincarnation',lambda m:m['nodes'][0].update(incarnation='new-boot'),membership)
reject_membership('unapproved epoch reset',lambda m:m.update(authority_epoch='other-epoch'),membership)
# Privacy fixture: event envelopes have no credential/body/header escape hatch.
v=load('examples/event.json');v['authorization']='fixture secret'
assert not validators['event'].is_valid(v),'credential telemetry must be rejected'
# Proposed projection structure only; this is not receipt authentication or issuance.
projection=load('examples/projection_request.json');decision=load('examples/decision.json')
context={key:copy.deepcopy(value) for key,value in projection.items()}
for name in ['identity_valid_until','network_valid_until','plan_valid_until']:
 context[name]=projection['valid_until']
def projection_structure(request,permit,expected,now,consumed=()):
 validators['projection_request'].validate(request);validators['decision'].validate(permit)
 assert permit['outcome']=='allow','non-permit projection'
 for key in ['request_id','decision_id','subject_ref','resource_id','action','revisions']:
  assert request[key]==permit[key],'decision binding mismatch'
 for key in ['request_id','decision_id','subject_ref','resource_id','action','service_id','plan_ref','audience_ref','method','request_digest','authentication_receipt_ref','issuance_nonce']:
  assert request[key]==expected[key],'native request/plan binding mismatch'
 assert request['revisions']==expected['revisions'],'stale native revision'
 issued=datetime.fromisoformat(request['issued_at'].replace('Z','+00:00'))
 expires=datetime.fromisoformat(request['valid_until'].replace('Z','+00:00'))
 ceiling=min(datetime.fromisoformat(value.replace('Z','+00:00')) for value in
  [permit['valid_until'],expected['identity_valid_until'],expected['network_valid_until'],expected['plan_valid_until']])
 assert issued<=now<expires<=ceiling and 0<(expires-issued).total_seconds()<=1,'invalid projection lease'
 assert (request['decision_id'],request['issuance_nonce']) not in consumed,'replayed issuance'
projection_now=datetime.fromisoformat('2026-10-12T00:00:29.750+00:00')
projection_structure(projection,decision,context,projection_now)
def reject_projection(name,mutate,permit=None,consumed=()):
 candidate=copy.deepcopy(projection);mutate(candidate)
 try:projection_structure(candidate,permit or decision,context,projection_now,consumed)
 except (AssertionError,ValidationError):cases.append(name);return
 raise AssertionError('unsafe projection structure accepted: '+name)
for key in ['subject_ref','service_id','plan_ref','audience_ref','method','request_digest','authentication_receipt_ref','revisions']:
 replacement={'revisions':{**projection['revisions'],'identity':2},'method':'POST','request_digest':'b'*64}.get(key,'other')
 reject_projection('projection changed '+key,lambda p,k=key,v=replacement:p.update({k:v}))
for key in ['authorization','allowed','aal','upstream_url']:
 reject_projection('projection caller authority '+key,lambda p,k=key:p.update({k:'forged'}))
reject_projection('projection denied',lambda p:None,{**decision,'outcome':'deny'})
reject_projection('projection replay',lambda p:None,consumed=[(projection['decision_id'],projection['issuance_nonce'])])
reject_projection('projection future',lambda p:p.update(issued_at='2026-10-12T00:00:29.900Z'))
reject_projection('projection expired',lambda p:p.update(valid_until='2026-10-12T00:00:29.700Z'))
reject_projection('projection prolonged',lambda p:p.update(issued_at='2026-10-12T00:00:28Z'))
reject_projection('projection jointly forged subject',lambda p:p.update(subject_ref='other'),{**decision,'subject_ref':'other'})
for name in ['identity_valid_until','network_valid_until','plan_valid_until']:
 shorter={**context,name:'2026-10-12T00:00:29.800Z'}
 try:projection_structure(projection,decision,shorter,projection_now)
 except AssertionError:cases.append('projection exceeds '+name)
 else:raise AssertionError('projection ignored native freshness ceiling')
# JSON fixtures use fixed historical times. This is not a live credential validator.
for md in ROOT.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',md.read_text()):
  target=target.split('#',1)[0]
  if not target or '://' in target or target.startswith('mailto:'):continue
  assert (md.parent/target).exists(),f'broken local link: {md.relative_to(ROOT)} -> {target}'
print(f'PASS: {len(validators)} schemas/examples, compatible bundle and {len(cases)+1} adversarial/privacy cases; local documentation links valid.')
