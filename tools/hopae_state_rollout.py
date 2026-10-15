#!/usr/bin/env python3
"""Offline Hop state preparation. Never stops, deploys, or replaces a live owner."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import time

MAX_FILE = 1024 * 1024 * 1024
MAX_FILES = 10000
BACKUP_SECONDS = 10

class Refused(Exception):
    pass

def require(value):
    if not value:
        raise Refused()

def regular(path):
    require(path.is_absolute() and path == path.resolve())
    st = path.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1)
    require(st.st_size <= MAX_FILE)
    return st

def digest(path):
    regular(path)
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, value):
    with open(path, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n'); out.flush(); os.fsync(out.fileno())

def fresh(path):
    require(not path.exists() and not path.is_symlink())
    path.mkdir(mode=0o700)

def inventory(root):
    require(root.is_dir() and root.absolute() == root.resolve())
    result = {}
    for index, path in enumerate(sorted(root.rglob('*'))):
        require(index < MAX_FILES)
        require(not path.is_symlink())
        if path.is_dir():
            continue
        st = regular(path)
        require(len(result) < MAX_FILES)
        # SQLite read-only backup can alter SHM reader marks; SHM is not data.
        shm = path.name.endswith('-shm') and path.with_name(path.name[:-4]).is_file() and sqlite_file(path.with_name(path.name[:-4]))
        result[str(path.relative_to(root))] = {'sha256': None if shm else digest(path), 'size': st.st_size,
            'mode': stat.S_IMODE(st.st_mode), 'uid': st.st_uid, 'gid': st.st_gid,
            'inode': st.st_ino, 'device': st.st_dev}
    return result

def durable_inventory(root):
    return {name: {k: v for k, v in entry.items() if k not in ('inode', 'device')}
            for name, entry in inventory(root).items()}

@contextlib.contextmanager
def stopped(state):
    # Same Linux flock primitive as Rust std::fs::File::try_lock used by Hop.
    path = state / 'hopae.lock'
    before = regular(path)
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        require(os.fstat(fd).st_ino == before.st_ino)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refused() from None
        yield
        require(path.lstat().st_ino == before.st_ino)
    finally:
        os.close(fd)

def read_json(path):
    require(regular(path).st_size <= 4 * 1024 * 1024)
    return json.loads(path.read_text())

def copy_private(source, target):
    regular(source)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with source.open('rb') as inp, open(target, 'xb', opener=lambda p, f: os.open(p, f, 0o600)) as out:
        shutil.copyfileobj(inp, out); out.flush(); os.fsync(out.fileno())

def schema(path):
    with contextlib.closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        require(db.execute('PRAGMA integrity_check').fetchall() == [('ok',)])
        return db.execute('SELECT COALESCE(MAX(version),0) FROM schema_migrations').fetchone()[0]

def sqlite_copy(source, target):
    with open(target, 'xb', opener=lambda p, f: os.open(p, f, 0o600)):
        pass
    with contextlib.closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=0.1)) as inp:
        with contextlib.closing(sqlite3.connect(target)) as out:
            deadline = time.monotonic() + BACKUP_SECONDS
            def progress(status, remaining, total):
                require(time.monotonic() < deadline)
            inp.backup(out, pages=128, progress=progress, sleep=0.05)
            out.execute('PRAGMA journal_mode=DELETE')
            require(out.execute('PRAGMA integrity_check').fetchall() == [('ok',)])
    os.chmod(target, 0o600)

def sqlite_file(path):
    with path.open('rb') as inp:
        return inp.read(16) == b'SQLite format 3\0'

def copy_state(source, output, records):
    for path in source.rglob('*'):
        if path.is_dir():
            (output / path.relative_to(source)).mkdir(parents=True, exist_ok=True, mode=0o700)
    databases = {name for name in records if sqlite_file(source / name)}
    require('hopae.db' in databases or databases)
    for name in records:
        if name == 'hopae.lock' or any(name == db + suffix for db in databases for suffix in ('-wal', '-shm', '-journal')):
            continue
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if name in databases:
            sqlite_copy(source / name, target)
        else:
            copy_private(source / name, target)
    # Fresh destination owner lock, never copy advisory-lock contents as authority.
    (output / 'hopae.lock').touch(mode=0o600)

def db_relative(config):
    configured = Path(config['state_dir'])
    db = Path(config.get('store', {}).get('path') or configured / 'hopae.db')
    relative = db.relative_to(configured)
    require(relative.parts and '..' not in relative.parts)
    return relative

def verify_bundle(root):
    require(stat.S_IMODE(root.stat().st_mode) == 0o700)
    for path in root.rglob('*'):
        require(not path.is_symlink())
        require(stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600))
    manifest = read_json(root / 'manifest.json')
    require(manifest['contract'] == 'hopae-offline-state-v1')
    relative = Path(manifest['database'])
    require(not relative.is_absolute() and relative.parts and '..' not in relative.parts)
    require(str(relative) in manifest['backup_inventory'])
    require(durable_inventory(root / 'state') == manifest['backup_inventory'])
    require(digest(root / 'config.json') == manifest['config_sha256'])
    require(schema(root / 'state' / relative) == manifest['schema'])
    require(durable_inventory(root / 'private') == manifest['private_inventory'])
    return manifest

def prepare(state, config_path, output, private_files=()):
    require(not output.resolve().is_relative_to(state.resolve()))
    with stopped(state):
        before = inventory(state)
        config_hash = digest(config_path)
        config = read_json(config_path); relative = db_relative(config)
        require(str(relative) in before)
        private_hashes = [digest(p) for p in private_files]
        fresh(output)
        try:
            (output / 'state').mkdir(mode=0o700)
            (output / 'private').mkdir(mode=0o700)
            copy_state(state, output / 'state', before)
            copy_private(config_path, output / 'config.json')
            for index, path in enumerate(private_files):
                copy_private(path, output / 'private' / str(index))
            require(inventory(state) == before and digest(config_path) == config_hash)
            require([digest(p) for p in private_files] == private_hashes)
            write_json(output / 'manifest.json', {
                'contract': 'hopae-offline-state-v1', 'database': str(relative),
                'schema': schema(output / 'state' / relative),
                'source_inventory': before, 'backup_inventory': durable_inventory(output / 'state'),
                'config_sha256': config_hash, 'private_inventory': durable_inventory(output / 'private'),
                'private_sources': [str(p.resolve()) for p in private_files],
                'scope': 'offline sole-owner backup; no deployment; exclude concurrent lockless admin CLI',
            })
        except BaseException:
            shutil.rmtree(output)
            raise

def clone_bundle(backup, output):
    manifest = verify_bundle(backup)
    fresh(output)
    try:
        (output / 'state').mkdir(mode=0o700)
        copy_state(backup / 'state', output / 'state', manifest['backup_inventory'])
        copy_private(backup / 'config.json', output / 'config.json')
        (output / 'private').mkdir(mode=0o700)
        for name in manifest['private_inventory']:
            copy_private(backup / 'private' / name, output / 'private' / name)
    except BaseException:
        shutil.rmtree(output); raise
    return manifest

def shadow(backup, output, candidate, expected_sha256, runner=subprocess.run):
    require(len(expected_sha256) == 64 and digest(candidate) == expected_sha256)
    manifest = clone_bundle(backup, output)
    config = read_json(output / 'config.json')
    config['state_dir'] = str((output / 'state').resolve())
    config.setdefault('store', {})['path'] = str((output / 'state' / manifest['database']).resolve())
    (output / 'config.json').unlink(); write_json(output / 'config.json', config)
    # Never start a server or permit outbound networking. Fixed actual CLI only.
    prefix = ['unshare', '--user', '--map-root-user', '--net', '--', str(candidate.resolve()), '--config', str((output / 'config.json').resolve())]
    for name, args in [('check', ['--check']), ('migrate', ['providers', 'import'])]:
        log = output / (name + '.private.log')
        with open(log, 'xb', opener=lambda p, f: os.open(p, f, 0o600)) as stream:
            result = runner(prefix + args, stdout=stream, stderr=stream, timeout=60, check=False)
        require(result.returncode == 0)
        require(digest(candidate) == expected_sha256)
    require(schema(output / 'state' / manifest['database']) == 10)
    write_json(output / 'qualification.json', {'contract':'hopae-offline-shadow-v1',
        'candidate_sha256':expected_sha256, 'schema':10,
        'backup_manifest_sha256':digest(backup / 'manifest.json'),
        'scope':'actual offline check+provider-import migration only; not serving/authentication qualification'})

def seal(state, output):
    with stopped(state):
        write_json(output, {'contract':'hopae-stopped-state-seal-v1', 'inventory':inventory(state)})

def restore(backup, current_state, current_seal, output):
    expected = read_json(current_seal)
    require(expected['contract'] == 'hopae-stopped-state-seal-v1')
    require(not output.resolve().is_relative_to(current_state.resolve()))
    with stopped(current_state):
        require(inventory(current_state) == expected['inventory'])
        manifest = clone_bundle(backup, output)
        require(inventory(current_state) == expected['inventory'])
        write_json(output / 'RESTORE.json', {'contract':'hopae-offline-rollback-v1',
            'schema':manifest['schema'], 'backup_manifest_sha256':digest(backup / 'manifest.json'),
            'current_seal_sha256':digest(current_seal),
            'scope':'prepared separate restore directory only; current state/config untouched; sole-owner cutover required'})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--state-dir',type=Path,required=True); p.add_argument('--config',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--private-file',type=Path,action='append',default=[])
    p = sub.add_parser('shadow'); p.add_argument('--backup',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--candidate',type=Path,required=True); p.add_argument('--sha256',required=True)
    p = sub.add_parser('seal'); p.add_argument('--state-dir',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    p = sub.add_parser('restore'); p.add_argument('--backup',type=Path,required=True); p.add_argument('--current-state-dir',type=Path,required=True); p.add_argument('--current-seal',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    try:
        if args.operation == 'prepare': prepare(args.state_dir.absolute(),args.config.absolute(),args.output.absolute(),args.private_file)
        elif args.operation == 'shadow': shadow(args.backup.absolute(),args.output.absolute(),args.candidate.absolute(),args.sha256)
        elif args.operation == 'seal': seal(args.state_dir.absolute(),args.output.absolute())
        else: restore(args.backup.absolute(),args.current_state_dir.absolute(),args.current_seal.resolve(),args.output.absolute())
        print(json.dumps({'ok':True,'operation':args.operation}))
        return 0
    except (Exception, KeyboardInterrupt):
        print(json.dumps({'ok':False,'operation':args.operation,'reason':'offline_state_operation_refused'}))
        return 1

if __name__ == '__main__':
    sys.exit(main())
