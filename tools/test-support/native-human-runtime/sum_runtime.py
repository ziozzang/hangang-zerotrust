#!/usr/bin/env python3
"""Owned actual Sum process; never a synthetic Network/Check authority."""
import argparse
import hashlib
import importlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from counted_backend import private_json

NETWORK_PROTO_SHA = '5723fa6c5616b229679b9c7b26c5da5e994b300f4d98a542f91d4cb0fba6cecf'
PUBLIC_036_SHA = '25a197f1c39bddf63fe4c168294536475ed2b4ba2aa16bcbe7ee4ac2dfec8654'


def need(value, stage):
    if not value:
        raise RuntimeError(stage)


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def private_bytes(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(value)


def tls_material(root):
    def run(*argv):
        subprocess.run(['openssl', *argv], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=owned-sum-ca', '-keyout', str(root/'ca.key'), '-out', str(root/'ca.pem'), '-addext', 'basicConstraints=critical,CA:TRUE')
    run('req', '-new', '-newkey', 'rsa:2048', '-nodes', '-subj', '/CN=localhost', '-keyout', str(root/'peer.key'), '-out', str(root/'peer.csr'))
    private_bytes(root/'extensions', b'basicConstraints=critical,CA:FALSE\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth\n')
    run('x509', '-req', '-in', str(root/'peer.csr'), '-CA', str(root/'ca.pem'), '-CAkey', str(root/'ca.key'), '-CAcreateserial', '-days', '1', '-extfile', str(root/'extensions'), '-out', str(root/'peer.pem'))
    return {'ca': str(root/'ca.pem'), 'server_certificate': str(root/'peer.pem'), 'server_key': str(root/'peer.key'), 'certificate': str(root/'peer.pem'), 'key': str(root/'peer.key'), 'server_name': 'localhost'}


class Fixture:
    def __init__(self, args):
        self.process = None
        self.log = None
        self.channel = None
        self.root = Path(args.directory)
        self.root.mkdir(mode=0o700, exist_ok=False)
        try:
            self.initialize(args)
        except BaseException:
            try:
                self.close()
            except BaseException:
                pass
            raise

    def initialize(self, args):
        binary = Path(args.binary).resolve()
        self.binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
        need(self.binary_sha == args.binary_sha256, 'binary_sha256')
        import grpc
        self.grpc = grpc
        self.ip = str(ipaddress.ip_address(args.client_ip))
        self.network = self.ip + ('/32' if ':' not in self.ip else '/128')
        self.tls = json.loads(Path(args.tls_json).read_text()) if args.tls_json else tls_material(self.root)
        need(set(self.tls) == {'ca', 'server_certificate', 'server_key', 'certificate', 'key', 'server_name'}, 'tls_keys')
        need(self.tls['server_name'] == 'localhost', 'tls_fixed_name')
        for key in ('ca', 'server_certificate', 'server_key', 'certificate', 'key'):
            need(Path(self.tls[key]).is_file(), 'tls_path')
        proto = Path(args.sum_source)/'crates/guard-grpc/proto/network.proto'
        self.proto_sha = hashlib.sha256(proto.read_bytes()).hexdigest()
        need(self.proto_sha == NETWORK_PROTO_SHA, 'network_proto_sha256')
        subprocess.run([sys.executable, '-m', 'grpc_tools.protoc', '-I'+str(proto.parent), '--python_out='+str(self.root), '--grpc_python_out='+str(self.root), str(proto)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.path.insert(0, str(self.root))
        self.pb = importlib.import_module('network_pb2')
        self.rpc = importlib.import_module('network_pb2_grpc')
        self.admin = secrets.token_hex(32)
        self.collector = secrets.token_hex(32)
        private_bytes(self.root/'collector', self.collector.encode())
        self.http, self.native, self.transport = port(), port(), port()
        private_json(self.root/'bootstrap.json', {'mode': 'enforce', 'allow': [self.network], 'auto_block': False})
        argv = [str(binary), '--bootstrap-policy', str(self.root/'bootstrap.json'), '--supervised', '--listen', f'127.0.0.1:{self.http}', '--database', str(self.root/'authority.sqlite3'), '--decision-listen', f'127.0.0.1:{self.native}', '--grpc-listen', f'127.0.0.1:{self.transport}', '--decision-tls-cert', self.tls['server_certificate'], '--decision-tls-key', self.tls['server_key'], '--decision-client-ca', self.tls['ca'], '--management-tls']
        self.log = open(self.root/'runtime-private.log', 'wb')
        self.process = subprocess.Popen(argv, env=dict(os.environ, HANGANG_GUARD_ADMIN_TOKEN=self.admin, HANGANG_GUARD_COLLECTOR_TOKEN=self.collector), stdout=self.log, stderr=self.log, start_new_session=True)
        self.context = ssl.create_default_context(cafile=self.tls['ca'])
        self.context.load_cert_chain(self.tls['certificate'], self.tls['key'])
        deadline = time.monotonic()+15
        while True:
            need(self.process.poll() is None, 'sum_process_exit')
            try:
                if self.management('/healthz', token=False)[0] == 200:
                    break
            except OSError:
                pass
            need(time.monotonic() < deadline, 'sum_readiness')
            time.sleep(.05)
        self.channel = self.make_channel()
        grpc.channel_ready_future(self.channel).result(timeout=5)
        self.stub = self.rpc.NetworkStub(self.channel)
        self.ready = {'endpoint': f'https://127.0.0.1:{self.transport}', 'server_name': 'localhost', 'ca': self.tls['ca'], 'certificate': self.tls['certificate'], 'key': self.tls['key'], 'collector_file': str(self.root/'collector'), 'client_ip': self.ip, 'binary_sha256': self.binary_sha, 'network_proto_sha256': self.proto_sha}

    def make_channel(self, client=True):
        credentials = self.grpc.ssl_channel_credentials(Path(self.tls['ca']).read_bytes(), Path(self.tls['key']).read_bytes() if client else None, Path(self.tls['certificate']).read_bytes() if client else None)
        return self.grpc.secure_channel(f'127.0.0.1:{self.transport}', credentials, options=(('grpc.ssl_target_name_override', 'localhost'),))

    def management(self, path, data=None, method=None, token=True):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer '+self.admin
        request = urllib.request.Request(f'https://127.0.0.1:{self.http}'+path, data=None if data is None else json.dumps(data).encode(), headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, context=self.context, timeout=2) as response:
                return response.status, json.loads(response.read(65537))
        except urllib.error.HTTPError as response:
            return response.code, json.loads(response.read(65537))

    def check(self, token=None, channel=None):
        reply = self.rpc.NetworkStub(channel or self.channel).Check(self.pb.NetworkRequest(request_id=42, ip=ipaddress.ip_address(self.ip).packed), timeout=2, metadata=[('authorization', 'Bearer '+(self.collector if token is None else token))])
        need(reply.request_id == 42, 'network_correlation')
        return {'verdict': reply.verdict, 'mode': reply.mode, 'revision': reply.revision, 'ttl_ms': reply.ttl_ms}

    def cas(self, denied):
        status, document = self.management('/v1/policy/document')
        need(status == 200, 'policy_document')
        policy = document['policy']
        policy['mode'] = 'enforce'
        policy['allow'] = [] if denied else [self.network]
        # Empty allow is not deny-all. A real native block establishes denial.
        status, _ = self.management('/v1/policy/document', {'expected_revision': document['revision'], 'policy': policy}, 'PUT')
        need(status == 200, 'policy_cas')
        self.block(denied)
        return document

    def block(self, enabled):
        payload = {'network': self.network, 'expires_at': int(time.time())+600, 'reason': 'owned fixture'} if enabled else {'network': self.network}
        status, _ = self.management('/v1/blocks', payload, 'POST' if enabled else 'DELETE')
        need(status == 200, 'block_update')

    def close(self):
        errors = []
        if self.channel is not None:
            try:
                self.channel.close()
            except Exception:
                errors.append('channel_cleanup')
        if self.process is not None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait(timeout=5)
            except Exception:
                errors.append('process_cleanup')
                try:
                    if self.process.poll() is None:
                        os.killpg(self.process.pid, signal.SIGKILL)
                        self.process.wait(timeout=5)
                except Exception:
                    errors.append('process_kill_cleanup')
        if self.log is not None:
            try:
                self.log.close()
            except Exception:
                errors.append('log_cleanup')
        if errors:
            private_json(self.root/'cleanup-private.json', {'stages': errors})
            raise RuntimeError('sum_cleanup')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', required=True)
    parser.add_argument('--binary-sha256', default=PUBLIC_036_SHA)
    parser.add_argument('--sum-source', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--ready', required=True)
    parser.add_argument('--client-ip', default='192.0.2.10')
    parser.add_argument('--tls-json')
    args = parser.parse_args()
    need(Path(args.ready).parent.resolve() == Path(args.directory).resolve(), 'ready_ownership')
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    parent = os.getppid()
    def watch():
        while os.getppid() == parent:
            time.sleep(.2)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=watch, daemon=True).start()
    fixture = None
    try:
        fixture = Fixture(args)
        private_json(args.ready, fixture.ready)
        while True:
            line = sys.stdin.readline(4097)
            if not line:
                break
            need(len(line) <= 4096, 'command_limit')
            try:
                command = json.loads(line)
                op = command.get('op')
                if op == 'check':
                    reply = fixture.check()
                elif op in ('deny', 'restore'):
                    fixture.cas(op == 'deny'); reply = fixture.check()
                elif op in ('block', 'unblock'):
                    fixture.block(op == 'block'); reply = fixture.check()
                elif op == 'shutdown':
                    print(json.dumps({'ok': True}), flush=True); break
                else:
                    raise RuntimeError('unknown_op')
                print(json.dumps({'ok': True, **reply}), flush=True)
            except Exception as error:
                print(json.dumps({'ok': False, 'stage': str(error) if isinstance(error, RuntimeError) else type(error).__name__}), flush=True)
    finally:
        if fixture:
            fixture.close()

if __name__ == '__main__':
    main()
