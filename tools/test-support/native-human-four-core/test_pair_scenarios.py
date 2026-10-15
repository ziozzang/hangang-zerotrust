import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import pair_scenarios as s

METHODS=(s.VERIFY,s.ISSUE,s.PROJECT,s.PERMIT,s.DECIDE)

def snapshot(mode,armed=False):
    return {'stages':{m:{'received':0,'forwarded':0,'ok':0,'refused':0} for m in METHODS},'qualification':{'mode':mode,'armed':armed,'requires_runner_query_budget_check':mode=='exact_pair_replay','counts':{n:0 for n in ('cookie_substitutions','replay_attempts','replay_refused','pum_before','pum_after','control_sequence_complete','failed')},'last_replay':None}}

def entry(status=204):
    return {'response':{'status':status},'request_delta':1 if status==204 else 0,'effect_delta':1 if status==204 else 0,'expected_body_sha256':'actual','last_effect':{'body_sha256':'actual','credential_match':True,'header_names':['authorization']}}

class Tests(unittest.TestCase):
    def config(self,root):
        p=root/'config';p.write_text(json.dumps({'gateway':{'verify_budget_ms':400},'projection_receiver':{'observed_clock_rates':{'source_ppm':500,'receiver_ppm':500}}}))
        return p,hashlib.sha256(p.read_bytes()).hexdigest()

    def test_actual_budget_rates_quantum_boundary_and_config_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,digest=self.config(Path(tmp))
            gate=s.query_budget_gate(p,digest,20000000)
            self.assertTrue(gate['query_expiry_excluded']);self.assertEqual(gate['original_admission_limit_ms'],399)
            self.assertEqual(gate['conservative_elapsed_upper_ms'],23)
            self.assertFalse(s.query_budget_gate(p,digest,398000000)['query_expiry_excluded'])
            for invalid in (True,-1,1000000001):
                with self.assertRaises(RuntimeError):s.query_budget_gate(p,digest,invalid)
            p.write_text(p.read_text().replace('400','1000'))
            with self.assertRaisesRegex(RuntimeError,'actual_startup_config_hash'):s.query_budget_gate(p,digest,0)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError,'actual_default_query_budget'):s.query_budget_gate(p,digest,0)

    def test_lineage_requires_actual_issue_success_and_zero_permission(self):
        before=snapshot('issue_cookie_b');after=copy.deepcopy(before);after['qualification']['armed']=True;after['qualification']['counts']['cookie_substitutions']=1
        for method in (s.VERIFY,s.ISSUE,s.DECIDE):after['stages'][method]['ok']=1
        observations={'a':{'subject':'a'},'b':{'subject':'b'}}
        def run(after):
            tap=mock.Mock();tap.snapshot.side_effect=[copy.deepcopy(before),copy.deepcopy(before),after]
            with mock.patch.object(s,'effect',side_effect=[entry(),entry(),entry(503)]):return s.run_lineage(tap,None,None,{'a':'cookieA','b':'cookieB'},observations)
        self.assertTrue(run(after)['passed'])
        for method,field in [(s.PERMIT,'received'),(s.PROJECT,'received')]:
            broken=copy.deepcopy(after);broken['stages'][method][field]=1
            with self.assertRaises(s.PairFailure):run(broken)
        broken=copy.deepcopy(after);broken['stages'][s.ISSUE]['ok']=0
        with self.assertRaises(s.PairFailure):run(broken)

    def test_transport_prepare_has_zero_observe_rpcs_and_precedes_arm(self):
        for contaminated in (False,True):
            before=snapshot('exact_pair_replay')
            before['stages'][s.OBSERVE]={'received':0,'forwarded':0,'ok':0,'refused':0}
            prepared=copy.deepcopy(before)
            prepared['qualification']['replay_transport']={'prepared':True,'elapsed_boottime_ns':10}
            if contaminated:prepared['stages'][s.OBSERVE]['received']=1
            tap=mock.Mock();tap.snapshot.side_effect=[before,before,prepared,prepared]
            tap.prepare_replay_transport.return_value={'ok':True,'op':'prepare_replay_transport','prepared':True,'elapsed_boottime_ns':10}
            with mock.patch.object(s,'effect',side_effect=[entry(),entry(503)]):
                with self.assertRaises(s.PairFailure) as failed:
                    s.run_replay(tap,None,None,'cookie','unused','unused',prepare_transport=True)
            tap.prepare_replay_transport.assert_called_once_with()
            self.assertEqual(tap.arm.call_count,0 if contaminated else 1)
            self.assertFalse(failed.exception.facts['passed'])
            self.assertEqual(failed.exception.facts['transport_preparation']['prepared'],True)

    def test_transport_prepare_refusal_never_arms(self):
        before=snapshot('exact_pair_replay')
        before['stages'][s.OBSERVE]={'received':0,'forwarded':0,'ok':0,'refused':0}
        tap=mock.Mock();tap.snapshot.side_effect=[before,before]
        tap.prepare_replay_transport.return_value={'ok':False,'op':'prepare_replay_transport','stage':'transport'}
        with mock.patch.object(s,'effect',return_value=entry()):
            with self.assertRaises(s.PairFailure):s.run_replay(tap,None,None,'cookie','unused','unused',prepare_transport=True)
        tap.arm.assert_not_called()

    def test_replay_fails_inconclusive_if_original_query_may_expire(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,digest=self.config(Path(tmp));before=snapshot('exact_pair_replay');after=copy.deepcopy(before)
            after['qualification']['armed']=True
            for name in ('replay_attempts','replay_refused','pum_before','pum_after','control_sequence_complete'):after['qualification']['counts'][name]=1
            after['qualification']['last_replay']={'through_replay_elapsed_boottime_ns':398000000}
            for method in (s.ISSUE,s.PERMIT,s.PROJECT):after['stages'][method]['ok']=1
            tap=mock.Mock();tap.snapshot.side_effect=[before,before,after]
            with mock.patch.object(s,'effect',side_effect=[entry(),entry()]):
                with self.assertRaises(s.PairFailure) as failed:s.run_replay(tap,None,None,'cookie',p,digest)
            self.assertTrue(failed.exception.facts['inconclusive'])
            self.assertFalse(failed.exception.facts['passed'])
            self.assertFalse(failed.exception.facts['query_budget']['query_expiry_excluded'])

if __name__=='__main__':unittest.main()
