"""Render complete owned manifests through a fake kubectl; no cluster access."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CompositionManifests(unittest.TestCase):
    def render(self, composition):
        with tempfile.TemporaryDirectory(prefix='world-render-test-') as temporary:
            root = Path(temporary)
            wrapper = root/'kubectl'
            wrapper.write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
args=sys.argv[1:]
if args[:3]==['apply','-f','-']:
 Path(os.environ['OWNED_RENDER_FILE']).write_bytes(sys.stdin.buffer.read())
if 'rollout' in args:sys.exit(23)
''')
            wrapper.chmod(0o700)
            (root/'fixture.json').write_text(json.dumps({'apps':[{}]}))
            (root/'manifest.json').write_text(json.dumps({'id':'guard','assets':{}}))
            argv=[sys.executable,str(Path(__file__).with_name('kubernetes_world_smoke.py')),'--kubectl',str(wrapper),'--hopae-fixture',str(root/'fixture.json'),'--sumunjang-plugin',str(root),'--echo-image','node:fixture']
            for name in ['hangang','hopae','pumgye','sumunjang']:
                argv+=['--'+name+'-image',name+':fixture']
            if composition:
                argv+=['--composition','--observed','--credential-projection','--native-resource','--resource-catalog','--receipt-client','/unused/fixed-composition-probe']
            output=root/'rendered.json'
            result=subprocess.run(argv,env=dict(os.environ,OWNED_RENDER_FILE=str(output)),capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0) # Deliberate refusal before real rollout/forward.
            document=json.loads(output.read_text())
            return document['items']

    def test_responsive_flag_refuses_without_actual_browser_probe(self):
        argv=[sys.executable,str(Path(__file__).with_name('kubernetes_world_smoke.py')),'--kubectl','/unused','--hopae-fixture','/unused','--sumunjang-plugin','/unused','--echo-image','node:fixture','--pumgye-responsive']
        for name in ['hangang','hopae','pumgye','sumunjang']:
            argv+=['--'+name+'-image',name+':fixture']
        result=subprocess.run(argv,capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,2)
        self.assertIn('--pumgye-responsive requires --browser-probe',result.stderr)

    def test_default_has_no_composition_resources_or_credentials(self):
        items=self.render(False)
        self.assertNotIn('relay',[item['metadata']['name'] for item in items])
        config=next(item for item in items if item['kind']=='ConfigMap')
        profile=json.loads(config['data']['hopae.json'])['authentication_gateway']['profiles'][0]
        self.assertNotIn('composition',profile)
        self.assertNotIn('api_relay',profile)
        credentials=next(item for item in items if item['kind']=='Secret' and item['metadata']['name']=='world-credentials')
        self.assertNotIn('remote-api',credentials['stringData'])

    def test_composition_has_fixed_https_trust_and_disjoint_secret_environments(self):
        items=self.render(True)
        config=next(item for item in items if item['kind']=='ConfigMap')
        profile=json.loads(config['data']['hopae.json'])['authentication_gateway']['profiles'][0]
        self.assertEqual(profile['composition']['mode'],'all')
        self.assertTrue(profile['api_relay']['url'].startswith('https://relay.owned-world-'))
        self.assertEqual(profile['api_relay']['ca_file'],'/tls/ca.crt')
        self.assertNotIn('rejectUnauthorized',config['data']['composition-relay.js'])
        pods={item['metadata']['name']:item['spec']['template']['spec'] for item in items if item['kind']=='Deployment'}
        relay_env={entry['name'] for entry in pods['relay']['containers'][0]['env']}
        hop_env={entry['name'] for entry in pods['hopae']['containers'][0]['env']}
        self.assertEqual(relay_env,{'REMOTE_API','REMOTE_OTHER','RELAY_CONTROL'})
        self.assertTrue({'OWNED_API_KEY','OWNED_OTHER_KEY'}.issubset(hop_env))
        self.assertTrue(relay_env.isdisjoint(hop_env))
        self.assertFalse(pods['relay']['automountServiceAccountToken'])
        self.assertEqual(pods['relay']['containers'][0]['command'],['node','/config/composition-relay.js'])


if __name__=='__main__':
    unittest.main()
