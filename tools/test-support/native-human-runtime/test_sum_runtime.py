import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
import sum_runtime as runtime


class PureBoundaries(unittest.TestCase):
    def test_private_ready_and_canonical_ip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ready';runtime.private_json(p,{'endpoint':'https://127.0.0.1:1'})
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            self.assertEqual(json.loads(p.read_text())['endpoint'],'https://127.0.0.1:1')
    def test_binary_mismatch_fails_before_tls_or_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            binary=Path(d)/'binary';binary.write_bytes(b'not-the-qualified-binary')
            args=argparse.Namespace(directory=str(Path(d)/'owned'),binary=str(binary),binary_sha256='0'*64)
            with mock.patch.object(runtime.subprocess,'Popen') as spawn:
                with self.assertRaisesRegex(RuntimeError,'binary_sha256'):runtime.Fixture(args)
                spawn.assert_not_called()


@unittest.skipUnless(os.environ.get('OWNED_SUM_BINARY'),'explicit actual production Sum fixture')
class ActualProductionSum(unittest.TestCase):
    def test_actual_mtls_network_cas_block_restore_and_cleanup(self):
        import grpc
        directory=Path(tempfile.mkdtemp(prefix='native-sum-runtime-evidence-'));directory.chmod(0o700)
        args=argparse.Namespace(directory=str(directory/'owned'),binary=os.environ['OWNED_SUM_BINARY'],binary_sha256=runtime.PUBLIC_036_SHA,sum_source=os.environ['OWNED_SUM_SOURCE'],client_ip='192.0.2.10',tls_json=None)
        fixture=None;result={'passed':False,'checks':[]}
        try:
            fixture=runtime.Fixture(args)
            initial=fixture.check();self.assertEqual((initial['verdict'],initial['mode']),(1,2));result['checks'].append('native_enforce_allow')
            for token in ['incorrect-owned-caller',fixture.admin]:
                with self.assertRaises(grpc.RpcError) as refused:fixture.check(token=token)
                self.assertEqual(refused.exception.code(),grpc.StatusCode.UNAUTHENTICATED)
            result['checks'].append('wrong_and_admin_caller_refused')
            with fixture.make_channel(client=False) as channel:
                with self.assertRaises(grpc.RpcError) as refused:fixture.check(channel=channel)
                self.assertIn(refused.exception.code(),[grpc.StatusCode.UNAVAILABLE,grpc.StatusCode.DEADLINE_EXCEEDED])
            result['checks'].append('missing_mtls_refused')
            stale=fixture.cas(True)
            denied=fixture.check();self.assertEqual((denied['verdict'],denied['mode']),(2,2));self.assertGreater(denied['revision'],initial['revision']);result['checks'].append('actual_cas_clear_allow_and_block_deny')
            status,_=fixture.management('/v1/policy/document',{'expected_revision':stale['revision'],'policy':stale['policy']},'PUT');self.assertEqual(status,409)
            self.assertEqual(fixture.check()['verdict'],2);result['checks'].append('stale_cas_refused_without_restore')
            fixture.cas(False)
            restored=fixture.check();self.assertEqual((restored['verdict'],restored['mode']),(1,2));self.assertGreater(restored['revision'],denied['revision']);result['checks'].append('actual_cas_unblock_restore')
            result.update(passed=True,binary_sha256=fixture.binary_sha,network_proto_sha256=fixture.proto_sha)
        finally:
            if fixture:
                port=fixture.transport;fixture.close()
                with self.assertRaises(OSError):socket.create_connection(('127.0.0.1',port),timeout=.2)
                result['cleanup']=True
            runtime.private_json(directory/'RESULT.json',result)
            print('PRIVATE_RESULT='+str(directory/'RESULT.json'),flush=True)

if __name__=='__main__':unittest.main()
