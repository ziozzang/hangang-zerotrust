#!/usr/bin/env python3
"""Owned loopback effect counter. No proof/authentication capability is created."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import signal
import threading
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

MAX_BODY = 1024 * 1024


def private_json(path, value):
    import tempfile
    path = Path(path)
    fd, pending = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, path)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)


class Counter:
    def __init__(self, result, credential_header=None, credential=None):
        self.result = Path(result)
        self.credential_header = credential_header
        self.credential = credential
        self.lock = threading.Lock()
        self.value = {'request_count': 0, 'effect_count': 0, 'last_request': None, 'last_effect': None}
        private_json(self.result, self.value)

    def received(self, method, target):
        with self.lock:
            self.value['request_count'] += 1
            self.value['last_request'] = {'method': method, 'path': '/effect' if target == '/effect' else '[unrecognized]'}
            private_json(self.result, self.value)

    def effect(self, method, body, headers):
        names = sorted(set(name.lower() for name in headers.keys()))
        values = headers.get_all(self.credential_header, []) if self.credential_header else []
        if self.credential is not None and (len(values) != 1 or not hmac.compare_digest(values[0].encode('latin-1'), self.credential)):
            return False
        with self.lock:
            value = {**self.value, 'effect_count': self.value['effect_count'] + 1,
                     'last_effect': {'method': method, 'path': '/effect',
                                     'body_length': len(body), 'body_sha256': hashlib.sha256(body).hexdigest(),
                                     'header_names': names, 'credential_present': bool(values),
                                     'credential_match': self.credential is not None}}
            private_json(self.result, value)
            self.value = value
        return True

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.value))


class Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    block_on_close = True

    def __init__(self, counter):
        self.counter = counter
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(('127.0.0.1', 0), Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        self.request.settimeout(1)
        super().setup()

    def log_message(self, *args):
        pass

    def handle_expect_100(self):
        self.reply(417)
        return False

    def reply(self, status):
        self.send_response(status)
        self.send_header('Content-Length', '0')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True

    def __getattr__(self, name):
        if name.startswith('do_'):
            return self.unsupported
        raise AttributeError(name)

    def unsupported(self):
        self.server.counter.received(self.command, self.path)
        self.reply(405)

    def do_effect(self):
        self.server.counter.received(self.command, self.path)
        # Only this fixed path is ever persisted; query/path credentials cannot leak.
        if self.path != '/effect':
            self.reply(404)
            return
        if sum(len(k) + len(v) + 4 for k, v in self.headers.items()) > 8192 or len(self.headers) > 64:
            self.reply(431)
            return
        lengths = self.headers.get_all('Content-Length', [])
        if not lengths and self.command in ('GET', 'HEAD', 'OPTIONS'):
            lengths = ['0']
        if self.headers.get_all('Transfer-Encoding') or self.headers.get_all('Expect') or len(lengths) != 1:
            self.reply(400)
            return
        raw = lengths[0]
        if not raw.isascii() or not raw.isdecimal() or len(raw) > 7 or str(int(raw)) != raw:
            self.reply(400)
            return
        size = int(raw)
        if size > MAX_BODY:
            self.reply(413)
            return
        try:
            body = self.rfile.read(size)
            if len(body) != size:
                self.reply(400)
                return
            allowed = self.server.counter.effect(self.command, body, self.headers)
            self.reply(204 if allowed else 403)
        except (TimeoutError, OSError):
            self.close_connection = True

    do_POST = do_effect
    do_PUT = do_effect
    do_PATCH = do_effect
    do_DELETE = do_effect

    do_GET = do_effect
    do_HEAD = do_effect
    do_OPTIONS = do_effect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--ready', required=True)
    parser.add_argument('--credential-header')
    parser.add_argument('--credential-file')
    args = parser.parse_args()
    root = Path(args.directory)
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    ready = Path(args.ready)
    if ready.parent.resolve() != root.resolve() or ready.exists():
        parser.error('ready must be a new file directly inside owned directory')
    if bool(args.credential_header) != bool(args.credential_file):
        parser.error('credential header and file required together')
    name = args.credential_header
    if name and (len(name) > 128 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789!#$%&'*+-.^_`|~" for c in name)):
        parser.error('credential header must be canonical lowercase token')
    credential = Path(args.credential_file).read_bytes() if args.credential_file else None
    if credential is not None and (not credential or len(credential) > 4096 or any(b < 32 or b == 127 for b in credential)):
        parser.error('credential must contain exact nonempty bounded header bytes, no newline')
    counter = Counter(root / 'result.json', name, credential)
    server = Server(counter)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    parent = os.getppid()
    def parent_watch():
        while not stop.wait(.2):
            if os.getppid() != parent:
                stop.set()
    threading.Thread(target=parent_watch, daemon=True).start()
    worker.start()
    try:
        private_json(ready, {'endpoint': f'http://127.0.0.1:{server.server_port}',
                             'effect_path': '/effect', 'result_file': str(counter.result),
                             'credential_header': name, 'max_body_bytes': MAX_BODY})
        def commands():
            while not stop.is_set():
                line = sys.stdin.readline(4097)
                if not line:
                    stop.set()
                    break
                try:
                    if len(line) > 4096:
                        raise ValueError()
                    request = json.loads(line)
                    if request == {'op': 'snapshot'}:
                        print(json.dumps({'ok': True, **counter.snapshot()}), flush=True)
                    elif request == {'op': 'shutdown'}:
                        print(json.dumps({'ok': True, 'op': 'shutdown'}), flush=True)
                        stop.set()
                    else:
                        raise ValueError()
                except (ValueError, TypeError):
                    print(json.dumps({'ok': False, 'stage': 'invalid_command'}), flush=True)
        threading.Thread(target=commands, daemon=True).start()
        while not stop.wait(.2):
            pass
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


if __name__ == '__main__':
    main()
