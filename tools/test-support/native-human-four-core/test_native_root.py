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

if __name__=='__main__':unittest.main()
