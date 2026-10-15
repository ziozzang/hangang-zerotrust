"""Pinned DTO/actual TLS tests only: opaque fixture bytes are NOT real proofs."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import unittest

import grpc
import test_grpc_tap as base
import grpc_tap_hooks as hooks


class Peer(grpc.GenericRpcHandler):
    def __init__(self,wire):
        self.wire=wire
        self.calls=[]
        self.replay_code=grpc.StatusCode.UNAVAILABLE
        self.replay_detail='native Human projection refused'
        self.report_change=None
        self.delay=0
        self.output_budget=900
    def service(self,details):
        async def call(raw,context):
            if list(context.invocation_metadata()).count(('authorization','Bearer '+'b'*48)) != 1:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED,'caller')
            self.calls.append((details.method,raw))
            if details.method == hooks.PROJECT:
                number=sum(name==hooks.PROJECT for name,_ in self.calls)
                if number==1 and getattr(self,'first_delay',0):await asyncio.sleep(self.first_delay)
                if number>1:
                    if self.delay: await asyncio.sleep(self.delay)
                    if self.replay_code is not None:
                        await context.abort(self.replay_code,self.replay_detail)
                project,query=self.wire.pair(raw)
                return self.wire.output(request_id=project.request_id,request_sha256=query.request.request_sha256,
                    chain_sha256=hashlib.sha256(project.permission_query).digest(),remaining_ms=self.output_budget,
                    header_value=b'opaque-output-fixture').SerializeToString()
            if details.method == hooks.OBSERVE:
                query=self.wire.query.FromString(raw)
                count=sum(name==hooks.OBSERVE for name,_ in self.calls)
                if count==2 and getattr(self,'after_entered',None) is not None:
                    self.after_entered.set();await asyncio.sleep(1)
                report=self.wire.report(request_id=query.request_id,receipt_sha256=hashlib.sha256(query.permit.receipt).digest(),
                    clock_domain=query.permit.binding.authority_epoch,owner_now_ms=count,
                    remaining_ms=800-count,proof_remaining_ms=900-count,
                    policy_revision=1,network_revision=2,route_revision=3,plan_revision=4)
                if self.report_change: self.report_change(report,count)
                return report.SerializeToString()
            return raw
        return grpc.unary_unary_rpc_method_handler(call)


class Qualification(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        gateway=os.environ.get('HUMAN_TAP_GATEWAY_PROTO')
        decision=os.environ.get('HUMAN_TAP_DECISION_PROTO')
        if not gateway or not decision:
            raise unittest.SkipTest('explicit pinned public gateway/decision proto paths required')
        cls.schemas={'gateway_proto':gateway,'decision_proto':decision}
        base.Transport.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):
        base.Transport.tearDownClass.__func__(cls)
    async def asyncSetUp(self):
        await base.Transport.asyncSetUp(self)
        self.wire=hooks.Wire(self.schemas,base.m.read_private)
        self.peer=Peer(self.wire)
        self.echo.service=self.peer.service
    async def asyncTearDown(self):
        await base.Transport.asyncTearDown(self)
    auth=base.Transport.auth
    refused=base.Transport.refused

    async def configure(self,mode,initially_armed=None):
        await self.channel.close()
        await self.tap.close()
        spec=next(iter(self.config['upstreams'].values()))
        names=[hooks.ISSUE,base.METHOD] if mode=='issue_cookie_b' else [hooks.PROJECT,hooks.OBSERVE]
        self.config['upstreams']={name:dict(spec) for name in names}
        self.config['qualification']={'mode':mode,'schemas':self.schemas}
        if initially_armed is not None:
            self.config['qualification']['initially_armed']=initially_armed
        if mode=='issue_cookie_b':
            cookie=self.root/'cookie-b';cookie.write_bytes(b'actual-native-cookie-B-fixture');cookie.chmod(0o600)
            self.config['qualification']['cookie_b_file']=str(cookie)
        self.tap=base.m.Tap(self.config)
        await self.tap.start()
        self.channel=grpc.aio.secure_channel(self.config['listen'],grpc.ssl_channel_credentials(
            (self.root/'ca.pem').read_bytes(),(self.root/'peer.key').read_bytes(),(self.root/'peer.pem').read_bytes()),
            options=(('grpc.ssl_target_name_override','localhost'),('grpc.enable_retries',0)))

    async def test_prepare_actual_tls_has_no_rpc_and_is_one_shot(self):
        await self.configure('exact_pair_replay',False)
        result=await self.tap.prepare_replay_transport()
        self.assertTrue(result['ok']);self.assertTrue(result['prepared'])
        self.assertGreaterEqual(result['elapsed_boottime_ns'],0)
        self.assertEqual(self.peer.calls,[])
        self.assertEqual(self.tap.snapshot()['stages'][hooks.OBSERVE],{'received':0,'forwarded':0,'ok':0,'refused':0})
        self.assertTrue(self.tap.snapshot()['qualification']['replay_transport']['prepared'])
        self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'already_attempted')
        self.tap.arm()
        self.assertEqual(self.peer.calls,[])
        self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'armed')

    async def test_prepare_wrong_mode_and_transport_failure_never_succeed(self):
        from unittest.mock import patch
        await self.configure('issue_cookie_b',False)
        self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'not_configured')
        await self.configure('exact_pair_replay',False)
        class Unready:
            async def channel_ready(self):raise TimeoutError()
        self.tap.route_channels[hooks.OBSERVE]=Unready()
        self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'transport')
        self.assertFalse(self.tap.snapshot()['qualification']['replay_transport']['prepared'])
        self.assertEqual(self.peer.calls,[])
        self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'already_attempted')

    async def test_prepare_clock_reversal_never_reports_success(self):
        from unittest.mock import patch
        await self.configure('exact_pair_replay',False)
        with patch.object(base.m.time,'clock_gettime_ns',side_effect=[10,9]):
            self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'transport')
        self.assertEqual(self.peer.calls,[])
        self.assertFalse(self.tap.snapshot()['qualification']['replay_transport']['prepared'])
        await self.configure('exact_pair_replay',False)
        with patch.object(base.m.time,'clock_gettime_ns',side_effect=OSError('controlled clock failure')):
            self.assertEqual((await self.tap.prepare_replay_transport())['stage'],'transport')
        self.assertFalse(self.tap.snapshot()['qualification']['replay_transport']['prepared'])

    async def test_unarmed_actual_tls_controls_then_oneway_arm(self):
        await self.configure('issue_cookie_b',False)
        raw=self.issue().SerializeToString()
        call=self.channel.unary_unary(hooks.ISSUE)
        self.assertEqual(await call(raw,metadata=self.auth(),timeout=.8),raw)
        self.assertFalse(self.tap.snapshot()['qualification']['armed'])
        self.assertEqual(self.tap.arm(),{'ok':True,'op':'arm','armed':True})
        changed=await call(raw,metadata=self.auth(),timeout=.8)
        self.assertNotEqual(changed,raw)
        self.assertEqual(self.tap.arm(),{'ok':False,'op':'arm','stage':'already_armed'})
        self.assertTrue(self.tap.snapshot()['qualification']['armed'])
        self.assertEqual(self.tap.snapshot()['qualification']['counts']['cookie_substitutions'],1)

    async def test_through_replay_duration_includes_first_projection(self):
        await self.configure('exact_pair_replay')
        self.peer.first_delay=.025
        raw,_=self.pair()
        await self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8)
        last=self.tap.snapshot()['qualification']['last_replay']
        self.assertGreaterEqual(last['through_replay_elapsed_boottime_ns'],20_000_000)
        self.assertGreaterEqual(last['through_replay_elapsed_boottime_ns'],last['elapsed_boottime_ns'])

    async def test_actual_transport_cancellation_keeps_partial_progress_without_success(self):
        await self.configure('exact_pair_replay')
        self.peer.after_entered=asyncio.Event()
        raw,_=self.pair()
        pending=self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8)
        await asyncio.wait_for(self.peer.after_entered.wait(),.5)
        pending.cancel()
        with self.assertRaises(asyncio.CancelledError):await pending
        for _ in range(20):
            if self.tap.hooks.progress['cancelled']:break
            await asyncio.sleep(.005)
        state=self.tap.snapshot()['qualification'];progress=state['progress']
        self.assertTrue(progress['cancelled']);self.assertEqual(progress['stage'],'pum_after')
        self.assertEqual(progress['replay_rpc_code'],'UNAVAILABLE')
        self.assertGreater(progress['first_output_remaining_ms'],0)
        self.assertGreater(progress['pum_before_remaining_ms'],0)
        self.assertGreaterEqual(progress['through_replay_elapsed_boottime_ns'],progress['first_project_elapsed_boottime_ns'])
        self.assertGreaterEqual(progress['elapsed_boottime_ns'],progress['through_replay_elapsed_boottime_ns'])
        self.assertEqual(state['counts']['control_sequence_complete'],0);self.assertIsNone(state['last_replay'])
        self.assertEqual(self.tap.snapshot()['stages'][hooks.PROJECT]['ok'],0)

    async def test_default_armed_and_invalid_startup_flag(self):
        await self.configure('issue_cookie_b')
        self.assertTrue(self.tap.hooks.armed)
        self.assertFalse(self.tap.hooks.arm())
        for bad in (0,1,'false',None):
            config=dict(self.config['qualification'],initially_armed=bad)
            with self.assertRaises(ValueError):hooks.Hooks(config,self.config['upstreams'],base.m.read_private)

    async def test_unarmed_inflight_project_not_changed_by_later_arm(self):
        await self.configure('exact_pair_replay',False)
        original=self.tap.call
        entered=asyncio.Event();release=asyncio.Event()
        async def delayed(name,raw,context):
            if name==hooks.PROJECT:
                entered.set();await release.wait()
            return await original(name,raw,context)
        self.tap.call=delayed
        raw,_=self.pair()
        pending=self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8)
        await asyncio.wait_for(entered.wait(),.5)
        self.assertTrue(self.tap.arm()['ok']);release.set();await pending
        self.assertEqual(self.tap.snapshot()['qualification']['counts']['replay_attempts'],0)

    def issue(self):
        request=self.wire.issue(service='orders',audience='orders-api')
        request.verification.request_id=7
        for name,value in [('cookie',b'other=x; __Host-hopae=native-cookie-A; tail=y'),
                           ('x-forwarded-host',b'app.example.test'),('user-agent',b'owned-agent')]:
            request.verification.headers.add(name=name,value=value)
        request.final_request.binding_contract=2
        request.final_request.method='POST'
        request.final_request.target='/effect?x=%2F'
        request.final_request.entity_sha256=b'x'*32
        request.final_request.entity_length=123
        request.final_request.route_id='owned-route'
        return request

    def pair(self):
        query=self.wire.query(request_id=19)
        query.request.request_id=7
        query.request.receipt=b'opaque-auth-fixture-not-a-proof'
        query.request.request_sha256=b'x'*32
        query.permit.request_id=7
        query.permit.receipt=b'opaque-permit-fixture-not-a-proof'
        query.permit.binding.authority_epoch='pobs1:'+'1'*32+':owned'
        query.permit.binding.policy_revision=1
        query.permit.binding.network_revision=2
        query.permit.binding.route_revision=3
        query.permit.binding.plan_revision=4
        raw_query=query.SerializeToString()
        return self.wire.project(request_id=19,permission_contract=4,permission_query=raw_query).SerializeToString(),raw_query

    async def test_cookie_b_changes_only_one_native_cookie_and_preserves_metadata(self):
        await self.configure('issue_cookie_b')
        original=self.issue()
        raw=original.SerializeToString()+b'\x98\x06\x01'  # Unknown DTO field must survive too.
        original=self.wire.issue.FromString(raw)
        verify=b'opaque-early-Verify-untouched'
        self.assertEqual(await self.channel.unary_unary(base.METHOD)(verify,metadata=self.auth(),timeout=.8),verify)
        reply=await self.channel.unary_unary(hooks.ISSUE)(raw,metadata=self.auth(),timeout=.8)
        changed=self.wire.issue.FromString(reply)
        self.assertEqual(changed.verification.headers[0].value,b'other=x; __Host-hopae=actual-native-cookie-B-fixture; tail=y')
        changed.verification.headers[0].value=original.verification.headers[0].value
        self.assertEqual(changed,original)
        stats=self.tap.snapshot()['qualification']
        self.assertEqual(stats['counts']['cookie_substitutions'],1)
        self.assertNotIn('native-cookie',json.dumps(stats))

    async def test_duplicate_missing_native_cookie_and_malformed_message_never_forward(self):
        await self.configure('issue_cookie_b')
        variants=[]
        request=self.issue(); request.verification.headers.add(name='Cookie',value=b'__Host-hopae=other'); variants.append(request.SerializeToString())
        request=self.issue(); request.verification.headers[0].value=b'other=x'; variants.append(request.SerializeToString())
        request=self.issue(); request.verification.headers[0].value=b'__Host-hopae=a; __Host-hopae=b'; variants.append(request.SerializeToString())
        request=self.issue(); request.verification.headers[0].value=b'__Host-hopae=actual-native-cookie-B-fixture'; variants.append(request.SerializeToString())
        variants.append(b'\xff')
        for raw in variants:
            await self.refused(self.channel.unary_unary(hooks.ISSUE)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.peer.calls,[])

    async def test_exact_query_replay_controls_and_single_original_reply(self):
        await self.configure('exact_pair_replay')
        raw,query=self.pair()
        reply=await self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8)
        self.assertEqual(self.wire.output.FromString(reply).header_value,b'opaque-output-fixture')
        self.assertEqual(self.peer.calls,[(hooks.PROJECT,raw),(hooks.OBSERVE,query),(hooks.PROJECT,raw),(hooks.OBSERVE,query)])
        stats=self.tap.snapshot()['qualification']
        self.assertEqual(stats['counts']['control_sequence_complete'],1)
        self.assertTrue(stats['requires_runner_query_budget_check'])
        self.assertGreaterEqual(stats['last_replay']['elapsed_boottime_ns'],0)
        self.assertNotIn('opaque-',json.dumps(stats))

    async def test_transport_tls_or_arbitrary_unavailable_is_not_replay_success(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        for detail in ['connection reset','TLS failure','upstream refused']:
            self.peer.calls.clear();self.peer.replay_detail=detail
            await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_second_success_and_wrong_denial_code_refuse(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        for code in [None,grpc.StatusCode.PERMISSION_DENIED]:
            self.peer.calls.clear();self.peer.replay_code=code
            await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_owner_control_receipt_revision_ttl_and_budget_failures_refuse(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        for name,value in [('receipt_sha256',b'z'*32),('request_id',20),('cache_ttl_ms',1),('remaining_ms',0),('route_revision',99),('clock_domain','pobs1:'+'2'*32+':other')]:
            self.peer.calls.clear()
            self.peer.report_change=lambda report,count,n=name,v=value:setattr(report,n,v)
            await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_late_owner_budget_increase_and_clock_reversal_refuse(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        for field,value in [('remaining_ms',898),('proof_remaining_ms',999),('owner_now_ms',0)]:
            self.peer.calls.clear()
            self.peer.report_change=lambda report,count,n=field,v=value:setattr(report,n,v) if count==2 else None
            await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_original_output_budget_and_deadline_are_not_renewed(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        self.peer.output_budget=10
        self.peer.delay=.03
        await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.peer.calls.clear();self.peer.output_budget=900;self.peer.delay=.1
        await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.02),{grpc.StatusCode.DEADLINE_EXCEEDED})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_after_control_withdrawal_and_cancellation_suppress_first_reply(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        self.peer.report_change=lambda report,count:setattr(report,'remaining_ms',0) if count==2 else None
        await self.refused(self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8),{grpc.StatusCode.FAILED_PRECONDITION})
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)
        self.peer.calls.clear();self.peer.report_change=None;self.peer.delay=.3
        call=self.channel.unary_unary(hooks.PROJECT)(raw,metadata=self.auth(),timeout=.8)
        for _ in range(200):
            if sum(name==hooks.PROJECT for name,_ in self.peer.calls)==2:break
            await asyncio.sleep(.001)
        else:self.fail('replay did not reach owned peer')
        call.cancel()
        with self.assertRaises(asyncio.CancelledError):await call
        for _ in range(200):
            if not self.tap.inflight:break
            await asyncio.sleep(.001)
        self.assertEqual(self.tap.inflight,0)
        self.assertEqual(self.tap.hooks.counts['control_sequence_complete'],0)

    async def test_wrong_query_contract_and_correlations_refuse(self):
        await self.configure('exact_pair_replay')
        raw,_=self.pair()
        message=self.wire.project.FromString(raw)
        for field,value in [('permission_contract',3),('request_id',20),('permission_query',b'bad')]:
            invalid=self.wire.project();invalid.CopyFrom(message);setattr(invalid,field,value)
            with self.assertRaises(Exception):self.wire.pair(invalid.SerializeToString())
        with self.assertRaises(ValueError):hooks.Wire({'gateway_proto':self.schemas['decision_proto'],'decision_proto':self.schemas['decision_proto']},base.m.read_private)


if __name__=='__main__': unittest.main()
