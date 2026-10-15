"""Control-flow tests only. Mock status/metadata never qualify native proofs."""
import hashlib
import unittest
from unittest import mock
from pum_runtime import initial_policy
from scenarios import run_fresh_gates, ScenarioFailure


class FreshGateControl(unittest.TestCase):
    def objects(self, statuses):
        hop,pum,root,backend,network=[mock.Mock() for _ in range(5)]
        hop.login_account.return_value='private-cookie2-path'
        pum.grant.return_value={'revision':2};pum.withdraw.return_value={'revision':3}
        pum.policy.side_effect=lambda:initial_policy('192.0.2.10');pum.publish.return_value={'revision':2}
        state={'request_count':0,'effect_count':0,'last_effect':None}
        backend.snapshot.side_effect=lambda:dict(state)
        iterator=iter(statuses)
        def send(cookie,body):
            status=next(iterator)
            if status==204:
                state['request_count']+=1;state['effect_count']+=1
                state['last_effect']={'body_sha256':hashlib.sha256(body).hexdigest(),'credential_match':True}
            return {'status':status}
        root.effect.side_effect=send
        observer=mock.Mock(return_value={'subject':'human1:'+'a'*64,'aal':2,'issued':True,'independently_observed':True,'scope_sha256':'1'*64})
        return hop,pum,root,backend,network,observer
    def run_case(self,objects):
        h,p,r,b,n,o=objects
        return run_fresh_gates(h,p,r,b,n,'human1:'+'a'*64,'private-cookie1-path',o)
    def test_exact_fresh_gate_sequence_and_real_owner_method_contract(self):
        objects=self.objects([403,204,403,204,204,403,204,403,204]);facts=self.run_case(objects)
        self.assertTrue(facts['passed']);self.assertFalse(facts['in_flight_withdrawal_proved'])
        self.assertEqual(len(facts['checks']),9)
        objects[0].login_account.assert_called_once_with('a',2)
        self.assertEqual(objects[4].cas.call_args_list,[mock.call(True),mock.call(False)])
    def test_503_cannot_be_counted_as_policy_or_network_denial(self):
        objects=self.objects([403,204,403,204,204,403,204,503])
        with self.assertRaises(ScenarioFailure) as failure:self.run_case(objects)
        facts=failure.exception.facts
        self.assertFalse(facts['passed']);self.assertEqual(facts['failed_stage'],'actual_sum_deny')
        self.assertEqual(facts['checks'][-1]['status'],503)
        self.assertEqual(objects[4].cas.call_args_list[-1],mock.call(False))
    def test_wrong_aal_observation_stops_before_positive_request(self):
        objects=self.objects([403,204,403]);objects[5].return_value['aal']=1
        with self.assertRaises(ScenarioFailure) as failure:self.run_case(objects)
        self.assertEqual(failure.exception.facts['failed_stage'],'actual_sdk_aal2_observe')
        self.assertEqual(objects[2].effect.call_count,3)
    def test_restore_failure_kept_separate_from_primary_status(self):
        objects=self.objects([503]);objects[4].cas.side_effect=RuntimeError('private-native-details-must-not-log')
        with self.assertRaises(ScenarioFailure) as failure:self.run_case(objects)
        facts=failure.exception.facts
        self.assertEqual(facts['checks'][0]['status'],503);self.assertEqual(facts['cleanup_failures'],['network'])
        self.assertNotIn('private-native-details',str(facts))

if __name__=='__main__':unittest.main()
