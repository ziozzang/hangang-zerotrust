import contextlib
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('rollout',Path(__file__).with_name('hopae_state_rollout.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class RolloutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.state=self.root/'state';self.state.mkdir()
        (self.state/'hopae.lock').touch();self.db=self.state/'hopae.db'
        with sqlite3.connect(self.db) as db:
            db.execute('CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)');db.execute('INSERT INTO schema_migrations VALUES(2)')
            db.execute('CREATE TABLE sessions(secret TEXT)');db.execute("INSERT INTO sessions VALUES('PRIVATE_SENTINEL')")
        (self.state/'key').write_bytes(b'PRIVATE_SENTINEL')
        self.config=self.root/'config.json';self.config.write_text(json.dumps({'state_dir':'/state','gateway':{},'providers':[]}))
        self.backup=self.root/'backup'
    def prepare(self):r.prepare(self.state,self.config,self.backup)
    def test_consistent_sqlite_backup_and_private_modes(self):
        self.prepare();m=r.verify_bundle(self.backup)
        self.assertEqual(m['schema'],2)
        self.assertEqual(r.schema(self.backup/'state/hopae.db'),2)
        for p in self.backup.rglob('*'):
            self.assertEqual(p.stat().st_mode&0o777,0o700 if p.is_dir() else 0o600)
        self.assertEqual((self.backup/'state/key').read_bytes(),b'PRIVATE_SENTINEL')
    def test_wal_committed_rows_captured_not_raw_wal(self):
        db=sqlite3.connect(self.db);self.addCleanup(db.close);db.execute('PRAGMA journal_mode=WAL')
        db.execute("INSERT INTO sessions VALUES('second')");db.commit()
        self.prepare()
        with sqlite3.connect(self.backup/'state/hopae.db') as saved:
            self.assertEqual(saved.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],2)
        self.assertFalse((self.backup/'state/hopae.db-wal').exists())
    def test_live_owner_refused_without_destination(self):
        with (self.state/'hopae.lock').open('rb') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(r.Refused):self.prepare()
        self.assertFalse(self.backup.exists())
    def test_live_other_process_refused(self):
        child=subprocess.Popen([os.sys.executable,'-c','import fcntl,sys;f=open(sys.argv[1],"rb");fcntl.flock(f,fcntl.LOCK_EX);print("ready",flush=True);sys.stdin.read()',str(self.state/'hopae.lock')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(),'ready')
            with self.assertRaises(r.Refused):self.prepare()
        finally:child.communicate('',timeout=5)
    def test_sqlite_busy_backup_has_bounded_failure(self):
        with sqlite3.connect(self.db) as owner:
            owner.execute('BEGIN EXCLUSIVE')
            with patch.object(r,'BACKUP_SECONDS',0.01):
                with self.assertRaises(r.Refused):r.sqlite_copy(self.db,self.root/'busy-copy')
            owner.rollback()

    def test_source_change_refuses_and_removes_partial(self):
        original=r.sqlite_copy
        def change(source,target):
            original(source,target);(self.state/'key').write_text('changed')
        with patch.object(r,'sqlite_copy',change):
            with self.assertRaises(r.Refused):self.prepare()
        self.assertFalse(self.backup.exists())
    def test_nonempty_destination_never_overwritten(self):
        self.backup.mkdir();(self.backup/'keep').write_text('keep')
        with self.assertRaises(r.Refused):self.prepare()
        self.assertEqual((self.backup/'keep').read_text(),'keep')
    def test_symlink_and_hardlink_source_refused(self):
        (self.state/'link').symlink_to(self.state/'key')
        with self.assertRaises(r.Refused):self.prepare()
        (self.state/'link').unlink();os.link(self.state/'key',self.state/'hard')
        with self.assertRaises(r.Refused):self.prepare()
    def test_external_database_refused(self):
        self.config.write_text(json.dumps({'state_dir':'/state','store':{'path':'/elsewhere/hopae.db'}}))
        with self.assertRaises(ValueError):self.prepare()
    def test_parent_traversal_database_refused(self):
        self.config.write_text(json.dumps({'state_dir':'/state','store':{'path':'/state/../other.db'}}))
        with self.assertRaises(r.Refused):self.prepare()
    def test_backup_tamper_refuses_clone(self):
        self.prepare();(self.backup/'state/key').write_text('tampered')
        with self.assertRaises(r.Refused):r.clone_bundle(self.backup,self.root/'clone')
        self.assertFalse((self.root/'clone').exists())
    def test_external_private_files_captured_and_verified(self):
        env=self.root/'private.env';env.write_text('PRIVATE_SENTINEL')
        r.prepare(self.state,self.config,self.backup,[env]);r.verify_bundle(self.backup)
        self.assertEqual((self.backup/'private/0').read_text(),'PRIVATE_SENTINEL')
    def test_portable_bundle_hashes_do_not_depend_on_inode(self):
        import shutil
        self.prepare();copied=self.root/'copied';shutil.copytree(self.backup,copied)
        self.assertNotEqual((copied/'state/key').stat().st_ino,(self.backup/'state/key').stat().st_ino)
        r.verify_bundle(copied)
    def test_public_backup_permissions_refused(self):
        self.prepare();(self.backup/'config.json').chmod(0o644)
        with self.assertRaises(r.Refused):r.verify_bundle(self.backup)

    def test_restore_unchanged_current_separate_and_old_schema(self):
        self.prepare();seal=self.root/'seal.json';r.seal(self.state,seal)
        original=r.inventory(self.state);out=self.root/'restored'
        r.restore(self.backup,self.state,seal,out)
        self.assertEqual(r.schema(out/'state/hopae.db'),2)
        self.assertEqual(r.inventory(self.state),original)
        self.assertEqual(r.read_json(out/'RESTORE.json')['schema'],2)
    def test_restore_changed_current_refuses(self):
        self.prepare();seal=self.root/'seal.json';r.seal(self.state,seal)
        with sqlite3.connect(self.db) as db:db.execute("INSERT INTO sessions VALUES('new-session')")
        with self.assertRaises(r.Refused):r.restore(self.backup,self.state,seal,self.root/'restored')
        self.assertFalse((self.root/'restored').exists())
    def test_restore_live_current_refuses(self):
        self.prepare();seal=self.root/'seal.json';r.seal(self.state,seal)
        with (self.state/'hopae.lock').open('rb') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            with self.assertRaises(r.Refused):r.restore(self.backup,self.state,seal,self.root/'restored')
    def test_shadow_fixed_offline_commands_and_schema(self):
        self.prepare();candidate=self.root/'candidate';candidate.write_bytes(b'candidate')
        calls=[]
        def runner(argv,**kwargs):
            calls.append(argv)
            config=r.read_json(Path(argv[argv.index('--config')+1]))
            if argv[-2:]==['providers','import']:
                with sqlite3.connect(config['store']['path']) as db:db.execute('INSERT INTO schema_migrations VALUES(10)')
            return subprocess.CompletedProcess(argv,0)
        out=self.root/'shadow';r.shadow(self.backup,out,candidate,r.digest(candidate),runner)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][:5],['unshare','--user','--map-root-user','--net','--'])
        self.assertEqual(calls[0][-1],'--check');self.assertEqual(calls[1][-2:],['providers','import'])
        self.assertEqual(r.schema(self.db),2);self.assertEqual(r.schema(out/'state/hopae.db'),10)
    def test_shadow_wrong_candidate_hash_no_output(self):
        self.prepare();candidate=self.root/'candidate';candidate.write_bytes(b'candidate')
        with self.assertRaises(r.Refused):r.shadow(self.backup,self.root/'shadow',candidate,'0'*64)
        self.assertFalse((self.root/'shadow').exists())
    def test_shadow_failed_namespace_never_qualifies(self):
        self.prepare();candidate=self.root/'candidate';candidate.write_bytes(b'candidate')
        def runner(argv,**kwargs):return subprocess.CompletedProcess(argv,1)
        out=self.root/'shadow'
        with self.assertRaises(r.Refused):r.shadow(self.backup,out,candidate,r.digest(candidate),runner)
        self.assertFalse((out/'qualification.json').exists())
    @unittest.skipUnless(os.environ.get('HOPAE_ROLLOUT_OLD_BINARY') and os.environ.get('HOPAE_ROLLOUT_CANDIDATE'), 'explicit exact native binaries required')
    def test_actual_old_native_store_to_candidate_schema10_offline(self):
        import shutil
        old=self.root/'old-hopae';shutil.copyfile(os.environ['HOPAE_ROLLOUT_OLD_BINARY'],old);old.chmod(0o700)
        state=self.root/'native-state';config=self.root/'native-config.json'
        config.write_text(json.dumps({'state_dir':str(state),'portal':{'public_url':'https://auth.example.test'},'gateway':{'kind':'hangang','caller_key_env':'OWNED_ROLLOUT_CALLER'},'apps':[{'app_id':'app','hosts':['app.example.test']}]}))
        with patch.dict(os.environ,{'OWNED_ROLLOUT_CALLER':'r'*48}):
            initial=subprocess.run(['unshare','--user','--map-root-user','--net','--',str(old),'--config',str(config),'providers','import'],capture_output=True,timeout=60)
            self.assertEqual(initial.returncode,0,'old native offline import failed; output withheld')
            (state/'hopae.lock').touch(mode=0o600)
            original_schema=r.schema(state/'hopae.db');self.assertLess(original_schema,10)
            backup=self.root/'native-backup';r.prepare(state,config,backup)
            candidate=Path(os.environ['HOPAE_ROLLOUT_CANDIDATE']).absolute()
            shadow=self.root/'native-shadow';r.shadow(backup,shadow,candidate,r.digest(candidate))
            self.assertEqual(r.schema(state/'hopae.db'),original_schema)
            self.assertEqual(r.schema(shadow/'state/hopae.db'),10)
            seal=self.root/'native-seal';r.seal(state,seal)
            restored=self.root/'native-restored';r.restore(backup,state,seal,restored)
            self.assertEqual(r.schema(restored/'state/hopae.db'),original_schema)

    def test_cli_error_redacts_paths_and_secret(self):
        stream=io.StringIO()
        with patch.object(os.sys,'argv',['tool','prepare','--state-dir',str(self.state),'--config',str(self.root/'PRIVATE_SENTINEL'),'--output',str(self.backup)]),contextlib.redirect_stdout(stream):
            self.assertEqual(r.main(),1)
        self.assertNotIn('PRIVATE_SENTINEL',stream.getvalue());self.assertNotIn(str(self.root),stream.getvalue())

if __name__=='__main__':unittest.main()
