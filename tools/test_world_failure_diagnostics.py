import json
from pathlib import Path
import tempfile
import unittest
from world_failure_diagnostics import capture, finish, redact, cleanup_forwards, cleanup_namespace


class Diagnostics(unittest.TestCase):
    def test_redaction(self):
        self.assertNotIn('secret',redact('secret eyJabc.def.ghi -----BEGIN PRIVATE KEY-----x-----END PRIVATE KEY-----',['secret']))
        self.assertEqual(len(redact('x'*70000,[])),65536)

    def test_primary_survives_all_cleanup_failures(self):
        calls=[]
        def broken(): calls.append(1);raise ValueError('private')
        def kube(*args): return json.dumps({'items':[]}).encode()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(TimeoutError,'original'):
                try: raise TimeoutError('original')
                finally: finish([('one',broken),('two',broken)],{'nodes':{},'pods':{}},kube,Path(root))
            facts=json.loads((Path(root)/'cleanup-facts.json').read_text())
            self.assertEqual(len(calls),2);self.assertEqual(facts['primary_error_type'],'TimeoutError')

    def test_cleanup_failure_fails_success_and_checks_baseline(self):
        def kube(*args): return json.dumps({'items':[]}).encode()
        with self.assertRaises(RuntimeError):finish([],{'nodes':{'old':True},'pods':{}},kube,None)

    def test_exact_pod_status_previous_logs_and_replacement(self):
        calls=[];pod={'metadata':{'name':'reserved','uid':'pod-1'},'status':{'phase':'Running','containerStatuses':[{'name':'app','restartCount':2,'lastState':{'terminated':{'exitCode':1,'reason':'Error','message':'secret'}}}]}}
        def kube(*args,**kwargs):
            calls.append(args)
            if 'namespace' in args:return b'{"metadata":{"uid":"ns-1"}}'
            if 'pods' in args:return json.dumps({'items':[pod]}).encode()
            if 'pod' in args:return json.dumps(pod).encode()
            return b'secret'
        with tempfile.TemporaryDirectory() as root:
            capture(kube,'owned','ns-1',Path(root),['secret'])
            status=json.loads((Path(root)/'pods-before-cleanup.json').read_text())
            self.assertEqual(status[0]['containers'][0]['restartCount'],2)
            self.assertNotIn('secret',json.dumps(status))
            self.assertTrue(any('--previous' in x for x in calls))
            self.assertTrue(all(p.read_text()=='[redacted]' for p in Path(root).glob('*.log')))
            with self.assertRaises(RuntimeError):capture(kube,'owned','replacement',Path(root),[])

    def test_replacement_during_log_read_discards_bytes(self):
        for replace_namespace in [False, True]:
            read=[False]
            def kube(*args,**kwargs):
                if 'namespace' in args:return json.dumps({'metadata':{'uid':'new' if read[0] and replace_namespace else 'ns'}}).encode()
                pod={'metadata':{'name':'reserved','uid':'new' if read[0] and not replace_namespace else 'pod'},'status':{'containerStatuses':[{'name':'app'}]}}
                if 'pods' in args:return json.dumps({'items':[pod]}).encode()
                if 'pod' in args:return json.dumps(pod).encode()
                read[0]=True;return b'oldlog'
            with tempfile.TemporaryDirectory() as root:
                capture(kube,'owned','ns',Path(root),[])
                self.assertEqual(list(Path(root).glob('*.log')),[])

    def test_namespace_atomic_delete_and_replacement_refusal(self):
        calls=[]
        def kube(*args,**kwargs):
            calls.append((args,kwargs))
            return b'{"metadata":{"uid":"old","resourceVersion":"7"}}'
        cleanup_namespace(kube,'owned','old')
        delete=next(x for x in calls if x[0][0]=='delete')
        self.assertEqual(delete[0],('delete','--raw','/api/v1/namespaces/owned','-f','-'))
        self.assertEqual(json.loads(delete[1]['body'])['preconditions'],{'uid':'old','resourceVersion':'7'})
        calls.clear()
        with self.assertRaises(RuntimeError):cleanup_namespace(kube,'owned','new')
        self.assertFalse(any(x[0][0]=='delete' for x in calls))

    def test_forward_failure_does_not_skip_later_processes(self):
        calls=[]
        class Process:
            def __init__(self,bad):self.bad=bad
            def terminate(self):
                calls.append(self.bad)
                if self.bad:raise OSError('failed')
            def wait(self,**kwargs):calls.append('wait')
        with self.assertRaises(RuntimeError):cleanup_forwards([Process(True),Process(False)])
        self.assertEqual(calls,[True,False,'wait'])


if __name__=='__main__':unittest.main()
