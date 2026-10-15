import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

MODULE = Path(__file__).with_name('counted_backend.py')
spec = importlib.util.spec_from_file_location('counted_backend', MODULE)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class ActualWireCounter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.counter = backend.Counter(self.root/'result.json', 'x-owned-secret', b'private-fixture-value')
        self.server = backend.Server(self.counter)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.worker.join(); self.tmp.cleanup()

    def send(self, raw):
        with socket.create_connection(self.server.server_address) as s:
            s.sendall(raw)
            s.shutdown(socket.SHUT_WR)
            return s.recv(4096).split(b'\r\n')[0]

    def test_actual_body_and_get_count_without_secret_or_body_recording(self):
        for method, body in [('POST', b'actual-body'), ('GET', b'')]:
            length = b'Content-Length: '+str(len(body)).encode()+b'\r\n' if method != 'GET' else b''
            status = self.send(method.encode()+b' /effect HTTP/1.1\r\nHost: localhost\r\n'+length+b'X-Owned-Secret: private-fixture-value\r\n\r\n'+body)
            self.assertIn(b'204', status)
        state = self.counter.snapshot()
        self.assertEqual((state['request_count'], state['effect_count']), (2,2))
        self.assertEqual(state['last_effect']['body_sha256'], hashlib.sha256(b'').hexdigest())
        self.assertTrue(state['last_effect']['credential_match'])
        raw = (self.root/'result.json').read_bytes()
        for secret in (b'private-fixture-value', b'actual-body'):
            self.assertNotIn(secret, raw)
        self.assertEqual((self.root/'result.json').stat().st_mode & 0o777, 0o600)

    def test_denied_duplicate_framing_truncation_and_oversize_have_no_effect(self):
        requests = [
            b'Content-Length: 0\r\n',
            b'Content-Length: 0\r\nX-Owned-Secret: private-fixture-value\r\nX-Owned-Secret: private-fixture-value\r\n',
            b'Content-Length: 0\r\nContent-Length: 0\r\n',
            b'Transfer-Encoding: chunked\r\n',
            b'Content-Length: 1048577\r\n',
            b'Content-Length: 5\r\nX-Owned-Secret: private-fixture-value\r\n',
        ]
        for headers in requests:
            self.send(b'POST /effect HTTP/1.1\r\nHost: localhost\r\n'+headers+b'\r\n')
        self.assertEqual(self.counter.snapshot()['effect_count'], 0)
        self.assertEqual(self.counter.snapshot()['request_count'], len(requests))

    def test_unknown_query_never_persisted_but_request_detected(self):
        self.assertIn(b'404', self.send(b'GET /effect?secret=must-not-record HTTP/1.1\r\nHost: localhost\r\n\r\n'))
        self.assertEqual(self.counter.snapshot()['request_count'], 1)
        self.assertNotIn(b'must-not-record', (self.root/'result.json').read_bytes())

    def test_unsupported_application_method_still_detects_dispatch(self):
        self.assertIn(b'405', self.send(b'TRACE /effect HTTP/1.1\r\nHost: localhost\r\n\r\n'))
        self.assertEqual(self.counter.snapshot()['request_count'], 1)
        self.assertEqual(self.counter.snapshot()['effect_count'], 0)

    def test_concurrent_effects_have_exact_count(self):
        def call():
            self.send(b'PATCH /effect HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1\r\nX-Owned-Secret: private-fixture-value\r\n\r\nx')
        threads=[threading.Thread(target=call) for _ in range(12)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(self.counter.snapshot()['effect_count'],12)


class ProcessOwnership(unittest.TestCase):
    def test_real_process_atomic_ready_snapshot_and_owned_shutdown(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'owned';ready=root/'ready.json'
            p=subprocess.Popen([sys.executable,str(MODULE),'--directory',str(root),'--ready',str(ready)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+5
                while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                info=json.loads(ready.read_text())
                self.assertTrue(info['endpoint'].startswith('http://127.0.0.1:'))
                self.assertEqual(ready.stat().st_mode & 0o777,0o600)
                p.stdin.write('{"op":"snapshot"}\n');p.stdin.flush()
                self.assertEqual(json.loads(p.stdout.readline())['request_count'],0)
                p.stdin.write('{"op":"shutdown"}\n');p.stdin.flush()
                self.assertTrue(json.loads(p.stdout.readline())['ok'])
                self.assertEqual(p.wait(timeout=5),0)
                address=info['endpoint'].split(':')[-1]
                with self.assertRaises(OSError):socket.create_connection(('127.0.0.1',int(address)),timeout=.2)
            finally:
                if p.poll() is None:p.terminate();p.wait(timeout=5)
                for f in (p.stdin,p.stdout,p.stderr):f.close()

if __name__ == '__main__':unittest.main()
