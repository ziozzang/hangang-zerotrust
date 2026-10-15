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
            self.assertEqual(tap.arm(),{'ok':False,'op':'arm','stage':'not_configured'})
            self.assertEqual((tap.root/'ready.json').stat().st_mode & 0o777,0o600)
            config=json.loads((tap.root/'config.json').read_text());self.assertNotIn('qualification',config)
            # No upstream peer/proof is created. This gate covers actual PUBLICtap startup only.
            address=tap.address
        finally:supervisor.close()
        host,port=address.rsplit(':',1)
        with self.assertRaises(OSError):socket.create_connection((host,int(port)),timeout=.2)
        private(parent/'RESULT.json',{'passed':True,'scope':'actual PUBLICtap wrapper readiness/IPC/groupcleanup only; no upstreamproof/HTTPchain'})
        print('PRIVATE_RESULT='+str(parent/'RESULT.json'),flush=True)


    @unittest.skipUnless(os.environ.get('HUMAN_TAP_GATEWAY_PROTO') and os.environ.get('HUMAN_TAP_DECISION_PROTO'),'explicit pinned hook schemas')
    def test_actual_private_ipc_unarmed_then_arm_and_duplicate_refused(self):
        entries=json.loads(Path(os.environ['OWNED_FOUR_CORE_MANIFEST']).read_text())
        parent=Path(tempfile.mkdtemp(prefix='four-core-tap-arm-'));parent.chmod(0o700)
        supervisor=Supervisor(parent/'owned',entries)
        try:
            tls=supervisor.pki();caller=supervisor.root/'hop-caller';private(caller,b'o'*36)
            cookie=supervisor.root/'cookie-b';private(cookie,b'owned-control-fixture-cookie-not-proof')
            hop=dict(tls['hopae'],endpoint='https://127.0.0.1:1',caller_file=str(caller))
            qualification={'mode':'issue_cookie_b','schemas':{'gateway_proto':os.environ['HUMAN_TAP_GATEWAY_PROTO'],'decision_proto':os.environ['HUMAN_TAP_DECISION_PROTO']},'cookie_b_file':str(cookie),'initially_armed':False}
            tap=NativeTap(supervisor,tls['tap'],hop,'i'*36,os.environ['OWNED_GRPC_PYTHON'],qualification=qualification)
            self.assertFalse(tap.snapshot()['qualification']['armed'])
            self.assertEqual(tap.arm(),{'ok':True,'op':'arm','armed':True})
            self.assertEqual(tap.arm(),{'ok':False,'op':'arm','stage':'already_armed'})
            self.assertTrue(tap.snapshot()['qualification']['armed'])
        finally:supervisor.close()


    @unittest.skipUnless(os.environ.get('HUMAN_TAP_GATEWAY_PROTO') and os.environ.get('HUMAN_TAP_DECISION_PROTO'),'explicit pinned hook schemas')
    def test_actual_replay_wrapper_mounts_fixed_direct_pum_observe(self):
        entries=json.loads(Path(os.environ['OWNED_FOUR_CORE_MANIFEST']).read_text());parent=Path(tempfile.mkdtemp(prefix='four-core-tap-replay-'));parent.chmod(0o700)
        supervisor=Supervisor(parent/'owned',entries)
        try:
            tls=supervisor.pki();hop_file=supervisor.root/'hop-caller';private(hop_file,b'h'*36);pum_file=supervisor.root/'pum-caller';private(pum_file,b'p'*36)
            hop=dict(tls['hopae'],endpoint='https://127.0.0.1:1',caller_file=str(hop_file));pum=dict(tls['pumgye'],endpoint='https://127.0.0.1:2',caller_file=str(pum_file))
            qualification={'mode':'exact_pair_replay','schemas':{'gateway_proto':os.environ['HUMAN_TAP_GATEWAY_PROTO'],'decision_proto':os.environ['HUMAN_TAP_DECISION_PROTO']},'initially_armed':False}
            tap=NativeTap(supervisor,tls['tap'],hop,'i'*36,os.environ['OWNED_GRPC_PYTHON'],pum=pum,qualification=qualification)
            state=tap.snapshot();self.assertEqual(len(state['stages']),8)
            self.assertIn('/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe',state['stages'])
            self.assertFalse(state['qualification']['armed']);self.assertTrue(tap.arm()['ok'])
        finally:supervisor.close()

if __name__=='__main__':unittest.main()
