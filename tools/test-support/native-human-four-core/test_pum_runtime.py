import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import pum_runtime as pum
from supervisor import Supervisor, private


class PolicyMetadata(unittest.TestCase):
    def test_initial_policy_is_guarded_and_all_principal_maps_empty(self):
        document=pum.initial_policy('192.0.2.10');service=document['policy']['services']['orders']
        self.assertTrue(service['require_guard'])
        for key in ('users','workload_users','human_users'):self.assertEqual(service[key],{})
        self.assertEqual(document['policy']['resources']['db:orders']['actions'],{'select':'read'})
        self.assertEqual(service['roles']['reader2']['minimum_aal'],2)
        # Native compiler combines the network and user assurance floors by max.
        # Baseline network must not impose AAL2 on every Human user.
        self.assertEqual(service['networks'],[{'cidr':'192.0.2.10/32','roles':['reader1']}])
    def test_scoped_grants_use_management_cas_and_never_legacy_fallback(self):
        # Pure policy metadata validation only; these labels are NOT verified identities.
        runtime=pum.PumRuntime.__new__(pum.PumRuntime);runtime.policy=lambda:pum.initial_policy('192.0.2.10')
        runtime.request=mock.Mock(return_value=(200,{'revision':2}))
        runtime.grant(['human1:'+'1'*64],2)
        method,document,revision=runtime.request.call_args.args
        self.assertEqual((method,revision),('PUT',1))
        self.assertEqual(document['policy']['services']['orders']['human_users'],{'human1:'+'1'*64:['reader2']})
        for subject in ['s48:abc','human1:'+'A'*64,'human1:bad']:
            with self.assertRaises(RuntimeError):runtime.grant([subject])
        for aal in [0,3,True]:
            with self.assertRaises(RuntimeError):runtime.grant(['human1:'+'1'*64],aal)
        bad=pum.initial_policy('192.0.2.10');bad['policy']['services']['orders']['users']['legacy']=['reader1']
        with self.assertRaises(RuntimeError):runtime.publish(bad)
    def test_transport_requires_https(self):
        with self.assertRaises(RuntimeError):pum.transport({},'http://example.test','CALLER')


@unittest.skipUnless(os.environ.get('OWNED_FOUR_CORE_MANIFEST'),'explicit exact binaries startup gate')
class ActualPumStartup(unittest.TestCase):
    def test_actual_observed_binary_starts_empty_guarded_authority_over_mtls(self):
        # Startup only: actual Sum is live; auth/route/plan endpoints are unsupplied and no proof is requested.
        from native_sum import NativeSum
        entries=json.loads(Path(os.environ['OWNED_FOUR_CORE_MANIFEST']).read_text())
        parent=Path(tempfile.mkdtemp(prefix='four-core-pum-startup-'));parent.chmod(0o700)
        supervisor=Supervisor(parent/'owned',entries)
        try:
            identities=supervisor.pki();tls=identities['pumgye']
            network=NativeSum(supervisor,identities['sumunjang'])
            runtime=pum.PumRuntime(supervisor,tls,'owned-pum-caller-at-least-thirty-two-bytes')
            scope={'service':'orders','audience':'orders-api','app_id':'app','route_id':'owned-route','route_revision':11,'destination_sha256':[18]*32,'header_policy_revision':13,'header_names':['x-tenant'],'reserved_names':['authorization']}
            # Trusted fixed configuration metadata; no source peer or opaque evidence factory.
            separate_key=pum.ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(pum.serialization.Encoding.Raw,pum.serialization.PublicFormat.Raw)
            ready=runtime.start({'issuer_ref':'native-human','public_key':pum.base64.b64encode(separate_key).decode(),'endpoint':'https://127.0.0.1:'+str(pum.port())},network.ready,{'address':'https://127.0.0.1:'+str(pum.port())},[scope],{'address':'https://127.0.0.1:'+str(pum.port())},'owned-hop-caller-at-least-thirty-two-bytes','owned-route-caller-at-least-thirty-two-bytes')
            self.assertEqual(ready['endpoint'],runtime.endpoint)
            original=runtime.policy()
            updated=runtime.publish(original)
            self.assertEqual(updated['revision'],original['revision']+1)
            self.assertEqual(runtime.request('PUT',original,original['revision'])[0],409)
            policy=runtime.policy()['policy']['services']['orders']
            self.assertFalse(policy.get('human_users',{}));self.assertFalse(policy['users']);self.assertTrue(policy['require_guard'])
            private(parent/'RESULT.json',{'passed':True,'scope':'actual Sum plus observed Pum startup/mandatory TLS admin/empty policy CAS and stale409 only; no auth/route/plan proof/permission/fullchain claim','binary_sha256':entries['pumgye']['sha256']})
        finally:
            supervisor.close()
        print('PRIVATE_RESULT='+str(parent/'RESULT.json'),flush=True)

if __name__=='__main__':unittest.main()
