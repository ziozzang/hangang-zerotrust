import importlib.util,json,os,pathlib,tempfile,threading,unittest
from unittest import mock
spec=importlib.util.spec_from_file_location('runtime_fixture',pathlib.Path(__file__).with_name('runtime_fixture.py'));runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
class AtomicPrivatePublication(unittest.TestCase):
 def publication(self,existing):
  with tempfile.TemporaryDirectory(prefix='owned-human-ipc-test-') as root:
   path=pathlib.Path(root)/'ready.json'
   if existing:runtime.private(path,{'generation':'old'})
   entered=threading.Event();release=threading.Event();errors=[];real_fsync=os.fsync
   def blocked(fd):entered.set();self.assertTrue(release.wait(3));real_fsync(fd)
   def writer():
    try:runtime.private(path,{'generation':'new','payload':'x'*10000})
    except BaseException as e:errors.append(e)
   with mock.patch.object(runtime.os,'fsync',blocked):
    thread=threading.Thread(target=writer);thread.start();self.assertTrue(entered.wait(3))
    try:
     if existing:self.assertEqual(json.loads(path.read_text()),{'generation':'old'})
     else:self.assertFalse(path.exists())
     pending=list(path.parent.glob('*.pending-*'));self.assertEqual(len(pending),1);self.assertEqual(pending[0].stat().st_mode&0o777,0o600)
    finally:release.set();thread.join(3)
   self.assertFalse(errors);self.assertFalse(thread.is_alive());self.assertEqual(json.loads(path.read_text())['generation'],'new');self.assertEqual(path.stat().st_mode&0o777,0o600);self.assertFalse(list(path.parent.glob('*.pending-*')))
 def test_first_ready_invisible_until_complete(self):self.publication(False)
 def test_replacement_retains_old_complete_json_until_publish(self):self.publication(True)
 def test_failed_replace_preserves_previous_and_removes_pending(self):
  with tempfile.TemporaryDirectory(prefix='owned-human-ipc-failure-') as root:
   path=pathlib.Path(root)/'ready.json';runtime.private(path,{'generation':'old'})
   with mock.patch.object(runtime.os,'replace',side_effect=OSError('controlled fixture publication failure')):
    with self.assertRaises(OSError):runtime.private(path,{'generation':'new'})
   self.assertEqual(json.loads(path.read_text()),{'generation':'old'});self.assertFalse(list(path.parent.glob('*.pending-*')))
if __name__=='__main__':unittest.main()
