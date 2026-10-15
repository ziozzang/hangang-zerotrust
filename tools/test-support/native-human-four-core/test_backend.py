import http.client
import pathlib
import tempfile
import unittest
from backend import Backend

class Tests(unittest.TestCase):
    def test_actual_bearer_effect_and_no_credential_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend=Backend(pathlib.Path(tmp)/'backend',b'Bearer owned-fixture-origin')
            try:
                def send(auth):
                    c=http.client.HTTPConnection('127.0.0.1',backend.server.server_port,timeout=2)
                    c.request('POST','/effect',body=b'actualbody',headers={'Authorization':auth});r=c.getresponse();status=r.status;r.read();c.close();return status
                self.assertNotEqual(send('owned-fixture-origin'),200)
                self.assertEqual(backend.snapshot()['request_count'],1)
                self.assertEqual(backend.snapshot()['effect_count'],0)
                self.assertEqual(send('Bearer owned-fixture-origin'),204)
                value=backend.snapshot();self.assertEqual(value['request_count'],2);self.assertEqual(value['effect_count'],1)
                self.assertEqual(value['last_effect']['body_length'],10)
                self.assertNotIn('owned-fixture-origin',(backend.root/'counter.json').read_text())
            finally:backend.close()

    def test_string_or_raw_secret_refuses_before_listener(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'backend'
            for value in ('Bearer secret',b'secret'):
                with self.assertRaises(ValueError):Backend(root,value)
                self.assertFalse(root.exists())

if __name__=='__main__':unittest.main()
