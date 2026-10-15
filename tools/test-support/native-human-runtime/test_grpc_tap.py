import asyncio
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest

import grpc

spec = importlib.util.spec_from_file_location('grpc_tap', Path(__file__).with_name('grpc_tap.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
METHOD = '/hangang.hopae.v1.Authentication/Verify'


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return f'127.0.0.1:{sock.getsockname()[1]}'


class Echo(grpc.GenericRpcHandler):
    def __init__(self):
        self.calls = 0
        self.delay = 0
        self.reply = None
        self.last = None
    def service(self, details):
        async def call(raw, context):
            if list(context.invocation_metadata()).count(('authorization', 'Bearer ' + getattr(self,'caller','b'*48))) != 1:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, 'caller')
            self.calls += 1
            self.last = raw
            if self.delay:
                await asyncio.sleep(self.delay)
            return self.reply if self.reply is not None else raw
        return grpc.unary_unary_rpc_method_handler(call)


class Transport(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='owned-grpc-tap-')
        cls.root = Path(cls.directory.name)
        def command(*args):
            subprocess.run(['openssl', *args], cwd=cls.root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        command('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '1', '-subj', '/CN=owned-tap-test')
        command('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'peer.key', '-out', 'peer.csr', '-subj', '/CN=localhost')
        (cls.root / 'ext').write_text('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth\n')
        command('x509', '-req', '-in', 'peer.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial', '-out', 'peer.pem', '-days', '1', '-extfile', 'ext')
        for name, value in [('inbound', 'a' * 48), ('outbound', 'b' * 48)]:
            (cls.root / name).write_text(value)
        for path in cls.root.iterdir():
            path.chmod(0o600)
    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()
    async def asyncSetUp(self):
        self.echo = Echo()
        self.upstream = grpc.aio.server(options=(('grpc.max_send_message_length', 65536),))
        self.upstream.add_generic_rpc_handlers((self.echo,))
        self.address = port()
        ca = (self.root / 'ca.pem').read_bytes()
        key = (self.root / 'peer.key').read_bytes()
        cert = (self.root / 'peer.pem').read_bytes()
        self.upstream.add_secure_port(self.address, grpc.ssl_server_credentials([(key, cert)], root_certificates=ca, require_client_auth=True))
        await self.upstream.start()
        self.config = {'listen': port(), 'tls': {'ca': str(self.root/'ca.pem'), 'key': str(self.root/'peer.key'), 'certificate': str(self.root/'peer.pem')}, 'inbound_caller_file': str(self.root/'inbound'), 'maximum_inflight': 2,
            'upstreams': {METHOD: {'endpoint': self.address, 'server_name': 'localhost', 'ca': str(self.root/'ca.pem'), 'key': str(self.root/'peer.key'), 'certificate': str(self.root/'peer.pem'), 'caller_file': str(self.root/'outbound')}}}
        self.tap = m.Tap(self.config)
        await self.tap.start()
        self.channel = grpc.aio.secure_channel(self.config['listen'], grpc.ssl_channel_credentials(ca, key, cert), options=(('grpc.ssl_target_name_override','localhost'), ('grpc.enable_retries',0)))
        self.rpc = self.channel.unary_unary(METHOD)
    async def asyncTearDown(self):
        await self.channel.close()
        await self.tap.close()
        await self.upstream.stop(0)
        self.assertEqual(self.tap.inflight, 0)
    def auth(self):
        return (('authorization', 'Bearer ' + 'a' * 48),)
    async def refused(self, call, codes):
        with self.assertRaises(grpc.aio.AioRpcError) as error:
            await call
        self.assertIn(error.exception.code(), codes)
    async def test_exact_raw_bytes_distinct_credentials_and_safe_counters(self):
        raw = b'\x00opaque-cookie-and-receipt\xff'
        self.assertEqual(await self.rpc(raw, metadata=self.auth(), timeout=.8), raw)
        self.assertEqual(self.echo.last, raw)
        stats = self.tap.snapshot()
        self.assertEqual(stats['stages'][METHOD], {'received':1,'forwarded':1,'ok':1,'refused':0})
        self.assertNotIn('opaque', json.dumps(stats))
        self.assertNotIn('Bearer', json.dumps(stats))
    async def test_new_pum_fixed_methods_exact_caps_and_raw_bytes_over_actual_tls(self):
        # Actual transport echo only: not a permission or native proof fixture.
        await self.tap.close()
        new_methods={'/hangang.pumgye.v1.Authorization/Decide':2048,'/hangang.pumgye.v1.HumanResourceAuthorization/Decide':2048,'/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue':8192}
        spec=self.config['upstreams'][METHOD]
        self.config['upstreams']={name:dict(spec) for name in new_methods}
        self.config['listen']=port();self.tap=m.Tap(self.config);await self.tap.start()
        await self.channel.close()
        ca=(self.root/'ca.pem').read_bytes();key=(self.root/'peer.key').read_bytes();cert=(self.root/'peer.pem').read_bytes()
        self.channel=grpc.aio.secure_channel(self.config['listen'],grpc.ssl_channel_credentials(ca,key,cert),options=(('grpc.ssl_target_name_override','localhost'),('grpc.enable_retries',0)))
        for name,limit in new_methods.items():
            call=self.channel.unary_unary(name);raw=b'opaque\x00'+b'x'*(limit-7)
            self.assertEqual(await call(raw,metadata=self.auth(),timeout=.8),raw)
            calls=self.echo.calls
            await self.refused(call(raw+b'x',metadata=self.auth(),timeout=.8),{grpc.StatusCode.RESOURCE_EXHAUSTED})
            self.assertEqual(self.echo.calls,calls)
            self.assertEqual(self.tap.snapshot()['stages'][name],{'received':2,'forwarded':1,'ok':1,'refused':1})
    async def test_hop_and_pum_use_distinct_fixed_upstreams_and_callers(self):
        other=Echo();other.caller='c'*48
        peer=grpc.aio.server();peer.add_generic_rpc_handlers((other,));address=port()
        ca=(self.root/'ca.pem').read_bytes();key=(self.root/'peer.key').read_bytes();cert=(self.root/'peer.pem').read_bytes()
        peer.add_secure_port(address,grpc.ssl_server_credentials([(key,cert)],root_certificates=ca,require_client_auth=True));await peer.start()
        caller=self.root/'pum-outbound';caller.write_text('c'*48);caller.chmod(0o600)
        try:
            await self.tap.close();self.config['listen']=port()
            name='/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue'
            spec=dict(self.config['upstreams'][METHOD],endpoint=address,caller_file=str(caller));self.config['upstreams'][name]=spec
            self.tap=m.Tap(self.config);await self.tap.start();await self.channel.close()
            self.channel=grpc.aio.secure_channel(self.config['listen'],grpc.ssl_channel_credentials(ca,key,cert),options=(('grpc.ssl_target_name_override','localhost'),('grpc.enable_retries',0)))
            for path in (METHOD,name):
                self.assertEqual(await self.channel.unary_unary(path)(b'exact-raw',metadata=self.auth(),timeout=.8),b'exact-raw')
            self.assertEqual((self.echo.calls,other.calls),(1,1))
        finally:await peer.stop(0)
    async def test_absent_duplicate_wrong_caller_never_forward(self):
        for auth in [(), self.auth()*2, (('authorization','Bearer wrong'),)]:
            await self.refused(self.rpc(b'x',metadata=auth,timeout=.5), {grpc.StatusCode.UNAUTHENTICATED})
        self.assertEqual(self.echo.calls,0)
    async def test_unknown_method_and_oversize_never_forward(self):
        await self.refused(self.channel.unary_unary('/hangang.hopae.v1.Other/Verify')(b'x',metadata=self.auth(),timeout=.5),{grpc.StatusCode.UNIMPLEMENTED})
        await self.refused(self.rpc(b'x'*(m.METHODS[METHOD]+1),metadata=self.auth(),timeout=.5),{grpc.StatusCode.RESOURCE_EXHAUSTED})
        self.assertEqual(self.echo.calls,0)
    async def test_original_deadline_no_retry_and_missing_deadline_refused(self):
        await self.refused(self.rpc(b'x',metadata=self.auth()),{grpc.StatusCode.DEADLINE_EXCEEDED})
        self.echo.delay=.2
        await self.refused(self.rpc(b'x',metadata=self.auth(),timeout=.03),{grpc.StatusCode.DEADLINE_EXCEEDED})
        await asyncio.sleep(.03)
        self.assertEqual(self.echo.calls,1)
    async def test_cancellation_releases_inflight(self):
        self.echo.delay=1
        call=self.rpc(b'x',metadata=self.auth(),timeout=.8)
        while not self.echo.calls:
            await asyncio.sleep(.001)
        call.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await call
        for _ in range(100):
            if not self.tap.inflight:
                break
            await asyncio.sleep(.001)
        self.assertEqual(self.tap.inflight,0)
    async def test_oversize_reply_refused(self):
        self.echo.reply=b'x'*(m.MAX_REPLY+1)
        await self.refused(self.rpc(b'x',metadata=self.auth(),timeout=.8),{grpc.StatusCode.RESOURCE_EXHAUSTED})
    async def test_plaintext_or_missing_mtls_cannot_reach_upstream(self):
        channel=grpc.aio.insecure_channel(self.config['listen'])
        try:
            await self.refused(channel.unary_unary(METHOD)(b'x',metadata=self.auth(),timeout=.1),{grpc.StatusCode.UNAVAILABLE,grpc.StatusCode.DEADLINE_EXCEEDED})
        finally:
            await channel.close()
        channel=grpc.aio.secure_channel(self.config['listen'],grpc.ssl_channel_credentials((self.root/'ca.pem').read_bytes()),options=(('grpc.ssl_target_name_override','localhost'),))
        try:
            await self.refused(channel.unary_unary(METHOD)(b'x',metadata=self.auth(),timeout=.2),{grpc.StatusCode.UNAVAILABLE,grpc.StatusCode.DEADLINE_EXCEEDED})
        finally:
            await channel.close()
        self.assertEqual(self.echo.calls,0)
    async def test_capacity_refuses_without_forward_or_retry(self):
        self.echo.delay=1
        calls=[self.rpc(b'x', metadata=self.auth(), timeout=.8) for _ in range(2)]
        try:
            for _ in range(200):
                if self.echo.calls == 2:
                    break
                await asyncio.sleep(.001)
            self.assertEqual(self.echo.calls,2)
            await self.refused(self.rpc(b'x',metadata=self.auth(),timeout=.5),{grpc.StatusCode.RESOURCE_EXHAUSTED})
            self.assertEqual(self.echo.calls,2)
        finally:
            for call in calls:
                call.cancel()
            for call in calls:
                with self.assertRaises(asyncio.CancelledError):
                    await call
            await asyncio.sleep(.01)

    async def test_cli_atomic_ready_safe_snapshot_shutdown_and_sigterm_cleanup(self):
        import sys
        with tempfile.TemporaryDirectory(prefix='owned-tap-cli-') as directory:
            root=Path(directory)
            config=json.loads(json.dumps(self.config))
            config['listen']=port()
            config_file=root/'config.json'
            config_file.write_text(json.dumps(config)); config_file.chmod(0o600)
            ready=root/'ready.json'
            for operation in ['shutdown','sigterm']:
                process=await asyncio.create_subprocess_exec(sys.executable, str(Path(m.__file__)),
                    '--config', str(config_file), '--ready', str(ready), stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                try:
                    for _ in range(200):
                        if ready.exists(): break
                        await asyncio.sleep(.005)
                    self.assertEqual(json.loads(ready.read_text())['endpoint'],config['listen'])
                    self.assertEqual(ready.stat().st_mode & 0o777,0o600)
                    process.stdin.write(b'{"op":"snapshot"}\n'); await process.stdin.drain()
                    snapshot=json.loads(await asyncio.wait_for(process.stdout.readline(),1))
                    self.assertEqual(snapshot['contract'],'qualification-grpc-tap-v1')
                    if operation=='shutdown':
                        process.stdin.write(b'{"op":"shutdown"}\n'); await process.stdin.drain()
                        self.assertEqual(json.loads(await asyncio.wait_for(process.stdout.readline(),1)),{'ok':True,'op':'shutdown'})
                        self.assertEqual(await asyncio.wait_for(process.wait(),2),0)
                    else:
                        process.terminate()
                        await asyncio.wait_for(process.wait(),2)
                    with socket.socket() as listener:
                        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                        host, port_number=config['listen'].rsplit(':',1)
                        listener.bind((host,int(port_number)))
                finally:
                    if process.returncode is None:
                        process.kill(); await process.wait()
                    process.stdin.close()
                    ready.unlink(missing_ok=True)

    async def test_parent_loss_closes_listener_even_with_stdin_pipe_open(self):
        import os
        import sys
        with tempfile.TemporaryDirectory(prefix='owned-tap-parent-') as directory:
            root=Path(directory)
            config=json.loads(json.dumps(self.config)); config['listen']=port()
            config_file=root/'config.json'; config_file.write_text(json.dumps(config)); config_file.chmod(0o600)
            ready=root/'ready.json'
            launcher = """import os,subprocess,sys,time
p=subprocess.Popen([sys.executable,sys.argv[1],'--config',sys.argv[2],'--ready',sys.argv[3]],stdin=sys.stdin,stdout=sys.stdout,stderr=sys.stderr)
for _ in range(400):
 if os.path.exists(sys.argv[3]): break
 time.sleep(.005)
print(p.pid,flush=True)
os._exit(0)
"""
            process=await asyncio.create_subprocess_exec(sys.executable,'-c',launcher,str(Path(m.__file__)),str(config_file),str(ready),
                stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            pid=None
            try:
                pid=int(await asyncio.wait_for(process.stdout.readline(),3))
                self.assertTrue(ready.exists())
                # Parent is gone, but the grandparent intentionally keeps stdin
                # writer open. EOF cannot explain the child's cleanup.
                for _ in range(400):
                    state=Path(f'/proc/{pid}/stat')
                    if not state.exists() or state.read_text().split(') ',1)[1].startswith('Z '): break
                    await asyncio.sleep(.005)
                else: self.fail('owned tap remained live after parent loss')
                with socket.socket() as listener:
                    listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                    host, number=config['listen'].rsplit(':',1); listener.bind((host,int(number)))
            finally:
                process.stdin.close()
                await asyncio.wait_for(process.wait(),2)
                if pid is not None:
                    state=Path(f'/proc/{pid}/stat')
                    if state.exists() and not state.read_text().split(') ',1)[1].startswith('Z '):
                        os.kill(pid,9)

    async def test_file_bounds_permissions_and_nonregular_input_refuse(self):
        import os
        with tempfile.TemporaryDirectory(prefix='owned-tap-input-') as directory:
            root=Path(directory)
            raw=root/'raw'; raw.write_bytes(b'x'*65); raw.chmod(0o600)
            with self.assertRaises(ValueError): m.read_private(raw,64)
            raw.write_text('a'*48); raw.chmod(0o644)
            with self.assertRaises(ValueError): m.token(raw)
            fifo=root/'pipe'; os.mkfifo(fifo,0o600)
            with self.assertRaises(ValueError): m.read_private(fifo,64)

    async def test_bad_fixed_config_refuses_before_channels(self):
        for change in ['same-caller','unknown-method','nonloopback']:
            config=json.loads(json.dumps(self.config))
            if change=='same-caller': config['upstreams'][METHOD]['caller_file']=config['inbound_caller_file']
            if change=='unknown-method': config['upstreams']['/bad/Call']=config['upstreams'].pop(METHOD)
            if change=='nonloopback': config['upstreams'][METHOD]['endpoint']='192.0.2.1:443'
            with self.assertRaises(ValueError): m.Tap(config)


if __name__ == '__main__':
    unittest.main()
