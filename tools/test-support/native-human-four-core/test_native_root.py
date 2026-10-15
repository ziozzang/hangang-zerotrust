import hashlib
import struct
import unittest
from native_root import destination,source_scope

class Tests(unittest.TestCase):
    def test_actual_origin_fixed_framing_and_target_separation(self):
        expected=hashlib.sha256(b'hangang-human-origin-v1\0'+struct.pack('>I',4)+b'http'+struct.pack('>I',9)+b'127.0.0.1'+struct.pack('>H',1234)).hexdigest()
        self.assertEqual(destination('http://127.0.0.1:1234'),expected)
        self.assertNotEqual(destination('http://127.0.0.1:1235'),expected)
        scope=source_scope('http://127.0.0.1:1234')
        self.assertEqual(scope['headers'],['x-tenant'])
        self.assertEqual(scope['reserved_headers'],['authorization'])
        for bad in ('http://127.0.0.1:1234/effect','http://client.example.test:1234','http://u@127.0.0.1:1234','http://127.0.0.1:1234?q=secret'):
            with self.assertRaises(RuntimeError):destination(bad)


class AuthorityRouting(unittest.TestCase):
    def test_only_decision_routes_through_tap_management_stays_direct(self):
        import json,pathlib,tempfile,types
        from unittest import mock
        from native_root import NativeRoot
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);collector=root/'collector';collector.write_text('owned-native-collector-key')
            supervisor=types.SimpleNamespace(root=root,entries={'hangang':{'binary':'/owned/hangang'}})
            tls=dict(ca='/owned/ca',certificate='/owned/client',key='/owned/key',server_name='localhost')
            hop=dict(endpoint='https://127.0.0.1:1111',issuer_ref='native-human',public_key='owned-hop-key')
            pum=types.SimpleNamespace(endpoint='https://127.0.0.1:2222',admin_endpoint='https://127.0.0.1:3333',public_key='owned-pum-key',admin='private-owned-admin')
            network=dict(endpoint='https://127.0.0.1:4444',http_url='https://127.0.0.1:5555',collector_file=str(collector))
            with mock.patch('native_root.ssl.create_default_context'):
                runtime=NativeRoot(supervisor,tls,'http://127.0.0.1:6666',hop,pum,network,'tap-inbound','tap-inbound','route-caller',decision_endpoint='https://127.0.0.1:7777')
            cfg=json.loads((runtime.root/'config.json').read_text());authority=cfg['pumgye_authority']
            self.assertEqual(authority['decision_address'],'127.0.0.1:7777')
            self.assertEqual(authority['management_address'],'127.0.0.1:3333')
            self.assertEqual(cfg['http'][0]['auth']['native']['address'],'127.0.0.1:1111')
            self.assertEqual(cfg['http'][0]['resource_policy']['pumgye_resource']['actions'],{'GET':'select','POST':'select'})
            self.assertEqual(runtime.environment['FOUR_PUM_CALLER'],'tap-inbound')
            self.assertNotIn('private-owned-admin',(runtime.root/'config.json').read_text())

if __name__=='__main__':unittest.main()
