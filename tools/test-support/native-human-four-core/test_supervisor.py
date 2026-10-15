import hashlib
import pathlib
import tempfile
import unittest
from unittest import mock
import supervisor as s

class Tests(unittest.TestCase):
    def entries(self, root):
        binary = root / 'binary'
        binary.write_bytes(b'#!/bin/sh\nexit 0\n')
        binary.chmod(0o700)
        return {n: {'binary':str(binary), 'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(), 'source':'1'*40} for n in s.CORES}

    def test_preflight_mismatch_before_directory_or_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); entries=self.entries(root)
            entries['hopae']['sha256']='0'*64
            with mock.patch.object(s.subprocess,'Popen') as spawn:
                with self.assertRaisesRegex(RuntimeError,'binary_hash'):
                    s.Supervisor(root/'owned',entries)
                spawn.assert_not_called()
            self.assertFalse((root/'owned').exists())

    def test_actual_child_closed_and_private_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            with s.Supervisor(root/'owned',self.entries(root)) as owned:
                child=owned.start('hopae',[owned.entries['hopae']['binary']],{})
                self.assertEqual(child.wait(timeout=3),0)
            self.assertEqual((owned.root/'cleanup.json').stat().st_mode & 0o777,0o600)
            self.assertEqual(owned.root.stat().st_mode & 0o777,0o700)
            with self.assertRaises(FileExistsError):s.Supervisor(owned.root,self.entries(root))

    def test_cleanup_attempts_all_preserves_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);owned=s.Supervisor(root/'owned',self.entries(root))
            children=[]
            for n in ('hopae','pumgye'):
                child=mock.Mock();child.poll.return_value=None;child.pid=1234
                log=mock.Mock();owned.children.append((n,child,log));children.append(child)
            with mock.patch.object(s.os,'killpg',side_effect=[OSError(),None,None]):
                with self.assertRaisesRegex(ValueError,'primary'):
                    with owned:raise ValueError('primary')
            children[0].guardian.wait.assert_called_once()
            self.assertTrue(owned.closed)

    def test_exited_core_descendant_listener_is_closed(self):
        import socket, sys, time
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);binary=root/'core'
            binary.write_text('#!'+sys.executable+'\nimport subprocess,sys\nsubprocess.Popen([sys.executable,"-c",'+repr('import socket,time,pathlib; s=socket.socket();s.bind(("127.0.0.1",0));s.listen();pathlib.Path('+repr(str(root/'port'))+').write_text(str(s.getsockname()[1]));time.sleep(60)')+'])\n')
            binary.chmod(0o700)
            entries={n:{'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'source':'1'*40} for n in s.CORES}
            owned=s.Supervisor(root/'owned',entries)
            try:
                core=owned.start('hopae',[str(binary)],{})
                self.assertEqual(core.wait(timeout=3),0)
                until=time.monotonic()+3
                while not (root/'port').exists() and time.monotonic()<until:time.sleep(.01)
                port=int((root/'port').read_text())
                sock=socket.create_connection(('127.0.0.1',port),timeout=1);sock.close()
            finally:owned.close()
            until=time.monotonic()+2
            while time.monotonic()<until:
                try:sock=socket.create_connection(('127.0.0.1',port),timeout=.1);sock.close()
                except OSError:break
                time.sleep(.01)
            else:self.fail('owned descendant listener survived cleanup')

    def test_supervisor_abrupt_exit_closes_owned_group(self):
        import subprocess, socket, sys, time
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);core=root/'core'
            script='import socket,time,pathlib; s=socket.socket();s.bind(("127.0.0.1",0));s.listen();pathlib.Path('+repr(str(root/'port'))+').write_text(str(s.getsockname()[1]));time.sleep(60)'
            core.write_text('#!'+sys.executable+'\nimport subprocess,sys\nsubprocess.Popen([sys.executable,"-c",'+repr(script)+'])\n');core.chmod(0o700)
            entries={n:{'binary':str(core),'sha256':hashlib.sha256(core.read_bytes()).hexdigest(),'source':'1'*40} for n in s.CORES}
            runner=root/'parent.py'
            runner.write_text('import sys,os,time,pathlib\nsys.path.insert(0,'+repr(str(pathlib.Path(s.__file__).parent))+')\nfrom supervisor import Supervisor\ns=Supervisor('+repr(str(root/'owned'))+','+repr(entries)+')\ns.start("hopae",['+repr(str(core))+'],{})\nwhile not pathlib.Path('+repr(str(root/'port'))+').exists():time.sleep(.01)\nos._exit(0)\n')
            parent=subprocess.Popen([sys.executable,str(runner)])
            self.assertEqual(parent.wait(timeout=5),0)
            port=int((root/'port').read_text());until=time.monotonic()+13
            while time.monotonic()<until:
                try:client=socket.create_connection(('127.0.0.1',port),timeout=.1);client.close()
                except OSError:break
                time.sleep(.1)
            else:self.fail('abrupt supervisor exit left owned listener')

    def test_exact_shape_and_boolean_pins_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries=self.entries(pathlib.Path(tmp));entries['hopae']['source']=True
            with self.assertRaisesRegex(RuntimeError,'binary_pin'):s.preflight(entries)
            entries=self.entries(pathlib.Path(tmp));entries['hopae']['secret']='never log'
            with self.assertRaisesRegex(RuntimeError,'binary_fields'):s.preflight(entries)

if __name__=='__main__':unittest.main()
