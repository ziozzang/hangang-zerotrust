"""Owned wrapper transport/IPC smoke only, never a native proof fixture."""
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
from supervisor import Supervisor, private
from tap_runtime import NativeTap, METHODS, PUM_METHODS


class CallerConfiguration(unittest.TestCase):
    def test_identical_callers_refused_before_auxiliary_spawn(self):
        with tempfile.TemporaryDirectory() as d:
            caller=Path(d)/'caller';caller.write_text('a'*32)
            supervisor=mock.Mock();supervisor.root=Path(d)
            with self.assertRaisesRegex(RuntimeError,'tap_distinct_callers'):
                NativeTap(supervisor,{}, {'caller_file':str(caller)},'a'*32,'unused')
            supervisor.start_tap.assert_not_called()


    def test_pum_outbound_must_be_distinct_from_both_other_callers(self):
        for reused in ('a'*32,'i'*32):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);hop_file=root/'hop-caller';private(hop_file,b'a'*32);pum_file=root/'pum-caller';private(pum_file,reused.encode())
                spec={'server_name':'localhost','ca':'unused','certificate':'unused','key':'unused','endpoint':'https://127.0.0.1:1'}
                supervisor=mock.Mock();supervisor.root=root
                with self.assertRaisesRegex(RuntimeError,'tap_distinct_pum_caller'):
                    NativeTap(supervisor,{},dict(spec,caller_file=str(hop_file)),'i'*32,'unused',pum=dict(spec,caller_file=str(pum_file)))
                supervisor.start_tap.assert_not_called()


@unittest.skipUnless(os.environ.get('OWNED_FOUR_CORE_MANIFEST') and os.environ.get('OWNED_GRPC_PYTHON'),'explicit actual tap transport smoke')
class ActualTapProcess(unittest.TestCase):
    def test_exact_public_helper_private_ready_snapshot_and_group_cleanup(self):
        entries=json.loads(Path(os.environ['OWNED_FOUR_CORE_MANIFEST']).read_text())
        parent=Path(tempfile.mkdtemp(prefix='four-core-tap-runtime-'));parent.chmod(0o700)
        supervisor=Supervisor(parent/'owned',entries)
        try:
            tls=supervisor.pki();caller=supervisor.root/'hop-caller';private(caller,b'o'*36)
            with socket.socket() as reserved:
                reserved.bind(('127.0.0.1',0));unused=reserved.getsockname()[1]
            hop=dict(tls['hopae'],endpoint='https://127.0.0.1:'+str(unused),caller_file=str(caller))
            pum_caller=supervisor.root/'pum-caller';private(pum_caller,b'p'*36)
            pum=dict(tls['pumgye'],endpoint='https://127.0.0.1:'+str(unused),caller_file=str(pum_caller))
            tap=NativeTap(supervisor,tls['tap'],hop,'i'*36,os.environ['OWNED_GRPC_PYTHON'],pum=pum)
            self.assertEqual(tap.metadata['caller_file'],str(tap.root/'inbound'))
            self.assertEqual(tap.pum_metadata['endpoint'],tap.metadata['endpoint'])
            self.assertEqual(tap.snapshot(),{'contract':'qualification-grpc-tap-v1','inflight':0,'stages':{m:{'received':0,'forwarded':0,'ok':0,'refused':0} for m in METHODS+PUM_METHODS}})
            self.assertEqual((tap.root/'ready.json').stat().st_mode & 0o777,0o600)
            config=json.loads((tap.root/'config.json').read_text());self.assertNotIn('qualification',config)
            # No upstream peer/proof is created. This gate covers actual PUBLICtap startup only.
            address=tap.address
        finally:supervisor.close()
        host,port=address.rsplit(':',1)
        with self.assertRaises(OSError):socket.create_connection((host,int(port)),timeout=.2)
        private(parent/'RESULT.json',{'passed':True,'scope':'actual PUBLICtap wrapper readiness/IPC/groupcleanup only; no upstreamproof/HTTPchain'})
        print('PRIVATE_RESULT='+str(parent/'RESULT.json'),flush=True)

if __name__=='__main__':unittest.main()
