import unittest
from world_http_facts import failure_body_facts, response_facts


class Facts(unittest.TestCase):
    def test_exact_body_only(self):
        self.assertEqual(failure_body_facts(503,b'authorization refused'),{'failure_code':'authorization_refused'})
        for body in [b'authorization refused\n', b'authorization refused reserved-secret']:
            facts=failure_body_facts(503,body)
            self.assertEqual(facts['failure_code'],'other')
            self.assertNotIn('reserved-secret',str(facts))
            self.assertEqual(len(facts['failure_body_sha256']),64)

    def test_success_body_has_no_metadata(self):
        self.assertEqual(failure_body_facts(200,b'reserved-origin-secret'),{})
        self.assertNotIn('body',str(response_facts(200,b'reserved-origin-secret',1,2)))

    def test_response_facts_survive_later_backend_failure(self):
        last=response_facts(503,b'Pumgye authority unavailable',1,84)
        try:raise TimeoutError('backend diagnostic')
        except TimeoutError:pass
        self.assertEqual(last['status'],503)
        self.assertEqual(last['failure_code'],'pumgye_authority_unavailable')
        self.assertIsNone(last['backend_delta'])

    def test_actual_request_records_status_before_backend_read_failure(self):
        import ast
        import time
        from pathlib import Path
        from types import SimpleNamespace
        tree=ast.parse(Path(__file__).with_name('kubernetes_world_smoke.py').read_text())
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='request')
        class Channel:
            status=503
            def __init__(self,*a,**kw):pass
            def request(self,*a,**kw):pass
            def getresponse(self):return self
            def read(self):return b'authorization refused'
            def close(self):pass
        reads=[]
        def backend_count():
            reads.append(1)
            if len(reads)>1:raise TimeoutError('diagnostic unavailable')
            return 0
        scope={'default_key':None,'Gateway':Channel,'args':SimpleNamespace(composition=False,native_resource=True), 'time':time,'backend_count':backend_count}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-request>','exec'),scope)
        with self.assertRaises(TimeoutError):scope['request']()
        self.assertEqual(scope['request'].last['status'],503)
        self.assertEqual(scope['request'].last['failure_code'],'authorization_refused')
        self.assertIsNone(scope['request'].last['backend_delta'])


if __name__=='__main__':unittest.main()
