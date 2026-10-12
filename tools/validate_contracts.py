#!/usr/bin/env python3
"""Validate draft schemas, synthetic bundles, invariants and local documentation links."""
from pathlib import Path
import copy,hashlib,json,re
from datetime import datetime
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
validators={}
for name in ['catalog','policy','bundle','decision','event']:
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
# Privacy fixture: event envelopes have no credential/body/header escape hatch.
v=load('examples/event.json');v['authorization']='fixture secret'
assert not validators['event'].is_valid(v),'credential telemetry must be rejected'
# JSON fixtures use fixed historical times. This is not a live credential validator.
for md in ROOT.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',md.read_text()):
  target=target.split('#',1)[0]
  if not target or '://' in target or target.startswith('mailto:'):continue
  assert (md.parent/target).exists(),f'broken local link: {md.relative_to(ROOT)} -> {target}'
print(f'PASS: 5 schemas/examples, compatible bundle and {len(cases)+1} adversarial/privacy cases; local documentation links valid.')
