"""Owned local process/PKI boundary for actual native four-core qualification.
No proof constructors, route references, cluster access or operating configuration.
"""
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import time
import sys

CORES = frozenset(('hangang', 'hopae', 'pumgye', 'sumunjang'))

def require(ok, stage):
    if not ok:
        raise RuntimeError(stage)

def private(path, value):
    path = pathlib.Path(path)
    raw = json.dumps(value, sort_keys=True).encode() if not isinstance(value, bytes) else value
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())

def preflight(entries):
    """Exact owner-supplied source/hash pins checked before any child or PKI."""
    require(type(entries) is dict and set(entries) == CORES, 'four_core_manifest')
    result = {}
    for name, entry in entries.items():
        require(type(entry) is dict and set(entry) in ({'binary','sha256','source'},{'binary','sha256','source','source_state','provenance','provenance_sha256'}), 'binary_fields')
        if 'source_state' in entry:
            require(entry['source_state'] in ('committed',), 'source_state')
            provenance=pathlib.Path(entry['provenance']).resolve(strict=True)
            require(provenance.is_file() and provenance.stat().st_size<=1048576, 'provenance_bound')
            require(hashlib.sha256(provenance.read_bytes()).hexdigest()==entry['provenance_sha256'], 'provenance_hash')
        for key, size in [('sha256', 64), ('source', 40)]:
            text = entry[key]
            require(type(text) is str and len(text) == size and all(c in '0123456789abcdef' for c in text), 'binary_pin')
        path = pathlib.Path(entry['binary']).resolve(strict=True)
        require(path.is_file() and os.access(path, os.X_OK), 'binary_executable')
        digest = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                digest.update(block)
        require(digest.hexdigest() == entry['sha256'], 'binary_hash')
        # Source is a reviewed provenance assertion; binary SHA is measured here.
        result[name] = dict(entry, binary=str(path))
    return result

class OwnedProcess:
    """Expose core termination without reaping the process-group lifetime holder."""
    def __init__(self, guardian, status):
        self.guardian = guardian
        self.status = status
        self.pid = guardian.pid
        self.stdin = guardian.stdin
        self.stdout = guardian.stdout

    def poll(self):
        if self.status.exists():
            require(self.status.stat().st_size <= 64, 'owned_exit_bound')
            value = json.loads(self.status.read_text())
            require(type(value) is dict and set(value) == {'exit'} and type(value['exit']) is int and -255 <= value['exit'] <= 255, 'owned_exit_shape')
            return value['exit']
        # WNOWAIT leaves a dead guardian's PID reserved until owned group cleanup.
        state = os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if state is not None:
            raise RuntimeError('owned_guardian_died')
        return None

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self.poll()
            if result is not None:
                return result
            time.sleep(.01)
        raise subprocess.TimeoutExpired('owned_core', timeout)

class Supervisor:
    def __init__(self, directory, entries):
        self.entries = preflight(entries)
        self.root = pathlib.Path(directory)
        self.root.mkdir(mode=0o700, parents=False, exist_ok=False)
        self.children = []
        self.closed = False
        private(self.root / 'binary-preflight.json', self.entries)

    def pki(self):
        """One fresh private CA; fixed loopback names, distinct per-core leaves."""
        def openssl(*args):
            result = subprocess.run(['openssl', *args], cwd=self.root, capture_output=True, timeout=15)
            require(result.returncode == 0, 'owned_pki')
        openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=owned-four-core-ca', '-keyout', 'ca.key', '-out', 'ca.pem', '-addext', 'basicConstraints=critical,CA:TRUE')
        identities = {}
        for name in sorted(CORES | {'tap', 'probe'}):
            private(self.root / (name + '.extensions'), b'basicConstraints=critical,CA:FALSE\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth\n')
            openssl('req', '-new', '-newkey', 'rsa:2048', '-nodes', '-subj', '/CN=owned-' + name, '-keyout', name + '.key', '-out', name + '.csr')
            openssl('x509', '-req', '-in', name + '.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key', '-CAcreateserial', '-days', '1', '-extfile', name + '.extensions', '-out', name + '.pem')
            identities[name] = {k: str(self.root / v) for k, v in {'ca': 'ca.pem', 'certificate': name + '.pem', 'key': name + '.key'}.items()}
            identities[name]['server_name'] = 'localhost'
        for path in self.root.iterdir():
            path.chmod(0o600)
        private(self.root / 'tls-paths.json', identities)
        return identities

    def start(self, name, argv, environment):
        require(not self.closed and name in CORES and not any(n == name for n, *_ in self.children), 'owned_child')
        require(argv and pathlib.Path(argv[0]).resolve() == pathlib.Path(self.entries[name]['binary']), 'owned_binary')
        return self._start(name, argv, environment, False)

    def start_tap(self, interpreter, script, expected_sha256, argv, environment):
        require(not self.closed and not any(n == 'tap' for n, *_ in self.children), 'owned_tap')
        require(hashlib.sha256(pathlib.Path(script).read_bytes()).hexdigest() == expected_sha256, 'tap_source_hash')
        return self._start('tap', [interpreter, script, *argv], environment, True)

    def _start(self, name, argv, environment, ipc):
        log = open(self.root / (name + '-private.log'), 'xb', buffering=0)
        os.chmod(log.name, 0o600)
        try:
            guardian = subprocess.Popen([sys.executable, str(pathlib.Path(__file__).with_name('group_guardian.py')), str(os.getpid()), str(self.root / (name + '-exit.json')), *argv], env=dict(os.environ, **environment), stdin=subprocess.PIPE, stdout=subprocess.PIPE if ipc else log, stderr=log if ipc else subprocess.STDOUT, start_new_session=True)
            child = OwnedProcess(guardian, self.root / (name + '-exit.json'))
        except BaseException:
            log.close()
            raise
        self.children.append((name, child, log))
        return child

    def close(self):
        if self.closed:
            return
        self.closed = True
        failures = []
        for name, child, log in reversed(self.children):
            try:
                # Do not poll/reap guardian before group cleanup: even a dead
                # guardian remains a zombie reserving its PID/PGID. Descendants
                # are signalled even if the core exited long before cleanup.
                os.killpg(child.pid, signal.SIGTERM)
                # Guardian ignores TERM while the core gets its graceful exit.
                # It reserves PGID until the final KILL catches any surviving
                # descendant, including one whose original core already exited.
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
                finally:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.guardian.wait(timeout=5)
            except Exception:
                failures.append(name)
            finally:
                try:
                    if child.stdin:
                        child.stdin.close()
                    if child.stdout:
                        child.stdout.close()
                except Exception:
                    failures.append(name + '_stdin')
                try:
                    log.close()
                except Exception:
                    failures.append(name + '_log')
        private(self.root / 'cleanup.json', {'attempted': [n for n, *_ in self.children], 'failed': failures})
        require(not failures, 'owned_cleanup')

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        try:
            self.close()
        except Exception:
            if typ is None:
                raise
        return False
