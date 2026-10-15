import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
spec=importlib.util.spec_from_file_location('four_core_run',Path(__file__).with_name('run.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class Tests(unittest.TestCase):
    def setup(self,root):
        binary=root/'observer';binary.write_bytes(b'owned')
        fields={'endpoint','server_name','ca','certificate','key','caller_file','public_key','issuer_ref','key_epoch','identity_authority','minimum_source_revision','minimum_application_generation','minimum_key_registry_revision','scope'}
        ready=root/'ready';ready.write_text(json.dumps(dict.fromkeys(fields,'fixed')))
        value={'contract':'human-seed-observer-v1','seed_only':True,'issued':True,'independently_observed':True,'subject':'human1:'+'1'*64,'aal':1,'scope_sha256':'2'*64}
        return binary,ready,value

    def test_exact_real_cli_shape_and_output_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary,ready,value=self.setup(root)
            with mock.patch.object(runner.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps(value).encode())) as child:
                result=runner.observe(str(binary),hashlib.sha256(binary.read_bytes()).hexdigest(),ready,root/'cookie',root,'a')
            self.assertEqual(result,value)
            argv=child.call_args.args[0]
            self.assertEqual(len(argv),2)
            config=json.loads(Path(argv[1]).read_text())
            self.assertEqual(config['bound_headers'],[{'name':'x-tenant','value':'bootstrap'}])
            self.assertEqual(config['method'],'POST')
            self.assertEqual((root/'subject-a.json').stat().st_mode&0o777,0o600)

    def test_unknown_secret_field_is_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary,ready,value=self.setup(root);value['receipt']='must-never-persist'
            with mock.patch.object(runner.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=json.dumps(value).encode())):
                with self.assertRaisesRegex(RuntimeError,'observer_output_shape'):
                    runner.observe(str(binary),hashlib.sha256(binary.read_bytes()).hexdigest(),ready,root/'cookie',root,'a')
            self.assertFalse((root/'subject-a.json').exists())
            self.assertNotIn('must-never-persist',(root/'observer-a-private.log').read_text())

if __name__=='__main__':unittest.main()
