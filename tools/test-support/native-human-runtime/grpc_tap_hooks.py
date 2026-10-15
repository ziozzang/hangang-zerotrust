"""Explicit qualification-only DTO hooks. No authentication/capability objects."""
import hashlib
import hmac
from pathlib import Path
import re
import tempfile
import time

import grpc
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from grpc_tools import protoc

ISSUE = '/hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved'
PROJECT = '/hangang.hopae.v1.HumanObservedCredentialProjection/Project'
OBSERVE = '/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe'
GATEWAY_SHA = '745a367111a0e9cb963dca8461841dd26bdbdea4cefafb502f9a5096f21c388c'
DECISION_SHA = 'df2ed98f9c9b5df451874f93ab91b11d2e83b4583f4618613f40729db3e4539b'


class Refused(Exception):
    pass


class Wire:
    def __init__(self, config, read):
        if set(config) != {'gateway_proto', 'decision_proto'}:
            raise ValueError('invalid schema configuration')
        with tempfile.TemporaryDirectory(prefix='owned-tap-schema-') as directory:
            root = Path(directory)
            for key, name, expected in [('gateway_proto','gateway.proto',GATEWAY_SHA),
                                        ('decision_proto','decision.proto',DECISION_SHA)]:
                data = read(config[key], 131072)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError('schema pin refused')
                (root/name).write_bytes(data)
            if protoc.main(['qualification-protoc', '-I'+directory, '--include_imports',
                            '--descriptor_set_out='+str(root/'wire.pb'),
                            str(root/'gateway.proto'), str(root/'decision.proto')]) != 0:
                raise ValueError('schema compilation refused')
            descriptor = descriptor_pb2.FileDescriptorSet.FromString(read(root/'wire.pb', 262144))
        pool = descriptor_pool.DescriptorPool()
        for item in descriptor.file:
            pool.Add(item)
        self.issue = message_factory.GetMessageClass(pool.FindMessageTypeByName('hangang.hopae.v1.HumanReceiptRequest'))
        self.project = message_factory.GetMessageClass(pool.FindMessageTypeByName('hangang.hopae.v1.ProjectionRequest'))
        self.output = message_factory.GetMessageClass(pool.FindMessageTypeByName('hangang.hopae.v1.ObservedProjectionReply'))
        self.query = message_factory.GetMessageClass(pool.FindMessageTypeByName('hangang.pumgye.v1.PermitValidationRequest'))
        self.report = message_factory.GetMessageClass(pool.FindMessageTypeByName('hangang.pumgye.v1.ObservedPermitTimeReply'))

    def replace_cookie(self, raw, cookie):
        message = self.issue.FromString(raw)
        if not message.HasField('verification') or not message.HasField('final_request'):
            raise Refused()
        headers = [h for h in message.verification.headers if h.name.lower() == 'cookie']
        if len(headers) != 1:
            raise Refused()
        header = headers[0]
        if any(c < 32 or c == 127 for c in header.value):
            raise Refused()
        parts = header.value.split(b';')
        positions = [i for i, part in enumerate(parts) if part.lstrip(b' ').startswith(b'__Host-hopae=')]
        if len(positions) != 1:
            raise Refused()
        index = positions[0]
        old_cookie = parts[index].lstrip(b' ').split(b'=',1)[1]
        if not old_cookie or hmac.compare_digest(old_cookie,cookie):
            raise Refused()
        prefix = parts[index][:-len(parts[index].lstrip(b' '))] if parts[index].startswith(b' ') else b''
        parts[index] = prefix + b'__Host-hopae=' + cookie
        header.value = b';'.join(parts)
        return message.SerializeToString()

    def pair(self, raw):
        project = self.project.FromString(raw)
        if not 1 <= project.request_id <= 9007199254740991 or project.permission_contract != 4 or not 1 <= len(project.permission_query) <= 8192:
            raise Refused()
        query = self.query.FromString(project.permission_query)
        if query.request_id != project.request_id or not query.HasField('request') or not query.HasField('permit') or not query.permit.HasField('binding') or not query.request.receipt or not query.permit.receipt:
            raise Refused()
        return project, query

    def current(self, raw, query):
        if len(raw) > 1024:
            raise Refused()
        report = self.report.FromString(raw)
        binding = query.permit.binding
        if report.request_id != query.request_id or report.cache_ttl_ms != 0 or not 0 < report.remaining_ms <= report.proof_remaining_ms <= 1000 or report.receipt_sha256 != hashlib.sha256(query.permit.receipt).digest() or report.clock_domain != binding.authority_epoch:
            raise Refused()
        if not re.fullmatch(r'pobs1:[0-9a-f]{32}:[A-Za-z0-9_.:-]{1,64}',report.clock_domain) or report.clock_domain.split(':',2)[1] == '0'*32:
            raise Refused()
        for name in ['policy_revision','network_revision','route_revision','plan_revision']:
            if getattr(report,name) != getattr(binding,name):
                raise Refused()
        return report


class Hooks:
    def __init__(self, config, methods, read):
        mode = config.get('mode')
        expected = {'mode','schemas','cookie_b_file'} if mode == 'issue_cookie_b' else {'mode','schemas'}
        if mode not in {'issue_cookie_b','exact_pair_replay'} or set(config) != expected:
            raise ValueError('invalid qualification mode')
        if mode == 'issue_cookie_b' and ISSUE not in methods:
            raise ValueError('Issue route required')
        if mode == 'exact_pair_replay' and not {PROJECT,OBSERVE} <= set(methods):
            raise ValueError('Project and direct Pum Observe routes required')
        self.mode = mode
        self.wire = Wire(config['schemas'],read)
        self.cookie = None
        if mode == 'issue_cookie_b':
            self.cookie = read(config['cookie_b_file'],4096,secret=True)
            if not self.cookie or any(c < 33 or c > 126 or c in b'";,\\' for c in self.cookie):
                raise ValueError('invalid native cookie value')
        if mode == 'exact_pair_replay' and not hasattr(time,'CLOCK_BOOTTIME'):
            raise ValueError('native BOOTTIME required')
        self.counts = {'cookie_substitutions':0,'replay_attempts':0,'replay_refused':0,'pum_before':0,'pum_after':0,'control_sequence_complete':0,'failed':0}
        self.last_replay = None

    def now(self):
        return time.clock_gettime_ns(time.CLOCK_BOOTTIME)

    def snapshot(self):
        return {'mode':self.mode,'counts':dict(self.counts),'last_replay':self.last_replay,
                'requires_runner_query_budget_check':self.mode == 'exact_pair_replay'}

    def mutate(self, name, raw):
        if self.mode == 'exact_pair_replay' and name == PROJECT:
            self.last_replay = None
            self.wire.pair(raw)  # Validate framing; forward the ORIGINAL bytes.
        if self.mode == 'issue_cookie_b' and name == ISSUE:
            raw = self.wire.replace_cookie(raw,self.cookie)
            self.counts['cookie_substitutions'] += 1
        return raw

    async def replay(self, raw, reply, started, call, context):
        project, query = self.wire.pair(raw)
        output = self.wire.output.FromString(reply)
        if output.request_id != project.request_id or output.cache_ttl_ms or not 0 < output.remaining_ms <= 1000 or output.chain_sha256 != hashlib.sha256(project.permission_query).digest() or output.request_sha256 != query.request.request_sha256:
            raise Refused()
        before = self.wire.current(await call(OBSERVE,project.permission_query,context),query)
        self.counts['pum_before'] += 1
        self.counts['replay_attempts'] += 1
        replay_started = self.now()
        try:
            await call(PROJECT,raw,context)
        except grpc.aio.AioRpcError as error:
            if error.code() != grpc.StatusCode.UNAVAILABLE or error.details() != 'native Human projection refused':
                raise Refused() from None
        else:
            raise Refused()
        replay_elapsed = self.now()-replay_started
        if replay_elapsed < 0:
            raise Refused()
        self.counts['replay_refused'] += 1
        after = self.wire.current(await call(OBSERVE,project.permission_query,context),query)
        self.counts['pum_after'] += 1
        if after.owner_now_ms < before.owner_now_ms or after.remaining_ms > before.remaining_ms or after.proof_remaining_ms > before.proof_remaining_ms:
            raise Refused()
        # Conservative local attenuation from before the FIRST projection RPC;
        # never use a new reply deadline, renewal or remote absolute expiry.
        elapsed = self.now()-started
        if context.time_remaining() is None or context.time_remaining() <= 0 or elapsed < 0 or elapsed >= output.remaining_ms*1000000:
            raise Refused()
        self.last_replay = {'elapsed_boottime_ns':replay_elapsed,
                            'pum_before_remaining_ms':before.remaining_ms,
                            'pum_after_remaining_ms':after.remaining_ms}
        self.counts['control_sequence_complete'] += 1
        return reply
