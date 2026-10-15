"""Phase-one unchanged PUBLIC raw forwarding tap: safe method/status counters."""
import hashlib
import copy
import json
import pathlib
import selectors
import time
import socket
import threading
from supervisor import private, require

TAP_SHA='bd4e7d5baafa5075e5db73ba66386306a99720e3621b364673e6857f1166f0f1'
HOOK_SHA='6f3d789c83a1507b42b33729ba770debafcee45e2cbe87874323ea6bb423329d'
METHODS=('/hangang.hopae.v1.Authentication/Verify','/hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved','/hangang.hopae.v1.HumanAuthenticationReceipts/ObserveTime','/hangang.hopae.v1.HumanObservedCredentialProjection/Project')

PUM_METHODS=('/hangang.pumgye.v1.Authorization/Decide','/hangang.pumgye.v1.HumanResourceAuthorization/Decide','/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue')

class NativeTap:
    def __init__(self,supervisor,tls,hop,caller,interpreter,pum=None,qualification=None):
        self.lock=threading.Lock()
        self.qualification=copy.deepcopy(qualification)
        require(type(caller) is str and 32<=len(caller)<=256 and all(33<=ord(c)<=126 for c in caller),'tap_inbound_caller')
        outbound=pathlib.Path(hop['caller_file']).read_text()
        require(caller!=outbound,'tap_distinct_callers')
        self.root=supervisor.root/'tap';self.root.mkdir(mode=0o700)
        script=pathlib.Path(__file__).resolve().parents[1]/'native-human-runtime'/'grpc_tap.py'
        require(hashlib.sha256(script.with_name('grpc_tap_hooks.py').read_bytes()).hexdigest()==HOOK_SHA,'tap_hooks_source_hash')
        private(self.root/'inbound',caller.encode())
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        self.address='127.0.0.1:'+str(port)
        spec={k:hop[k] for k in ('server_name','ca','certificate','key','caller_file')};spec['endpoint']=hop['endpoint'].removeprefix('https://')
        upstreams={m:dict(spec) for m in METHODS}
        if pum is not None:
            pum_caller=pathlib.Path(pum['caller_file']).read_text()
            require(pum_caller!=caller and pum_caller!=outbound,'tap_distinct_pum_caller')
            pum_spec={k:pum[k] for k in ('server_name','ca','certificate','key','caller_file')};pum_spec['endpoint']=pum['endpoint'].removeprefix('https://')
            upstreams.update({m:dict(pum_spec) for m in PUM_METHODS})
            if qualification is not None and qualification.get('mode')=='exact_pair_replay':
                upstreams['/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe']=dict(pum_spec)
        self.methods=tuple(upstreams)
        cfg={'listen':self.address,'tls':{k:tls[k] for k in ('ca','certificate','key')},'inbound_caller_file':str(self.root/'inbound'),'upstreams':upstreams,'maximum_inflight':16}
        if qualification is not None:
            cfg['qualification']=copy.deepcopy(qualification)
        private(self.root/'config.json',cfg)
        self.process=supervisor.start_tap(interpreter,str(script),TAP_SHA,['--config',str(self.root/'config.json'),'--ready',str(self.root/'ready.json')],{})
        deadline=time.monotonic()+10
        while not (self.root/'ready.json').exists():
            require(self.process.poll() is None,'tap_startup_exit')
            require(time.monotonic()<deadline,'tap_readiness');time.sleep(.02)
        ready=json.loads((self.root/'ready.json').read_text())
        require(ready=={'contract':'qualification-grpc-tap-v1','endpoint':self.address},'tap_ready_shape')
        require(self.process.poll() is None,'tap_startup_exit')
        self.metadata=dict(hop,endpoint='https://'+self.address,caller_file=str(self.root/'inbound'))
        self.pum_metadata=None if pum is None else dict(pum,endpoint='https://'+self.address,caller_file=str(self.root/'inbound'))

    def snapshot(self):
        with self.lock:
            return self._snapshot()

    def arm(self):
        with self.lock:
            value=self._command(b'{"op":"arm"}\n')
            require(value=={'ok':True,'op':'arm','armed':True} or value in ({'ok':False,'op':'arm','stage':'not_configured'},{'ok':False,'op':'arm','stage':'already_armed'}),'tap_arm_shape')
            return value

    def _command(self,command):
        self.process.stdin.write(command);self.process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            require(bool(selector.select(timeout=3)),'tap_snapshot_timeout')
            raw=self.process.stdout.readline(16385)
        require(len(raw)<=16384,'tap_snapshot_bound')
        return json.loads(raw)

    def _snapshot(self):
        value=self._command(b'{"op":"snapshot"}\n')
        expected={'contract','inflight','stages'} | ({'qualification'} if self.qualification is not None else set())
        require(set(value)==expected and value['contract']=='qualification-grpc-tap-v1' and set(value['stages'])==set(self.methods),'tap_snapshot_shape')
        require(type(value['inflight']) is int and 0<=value['inflight']<=16,'tap_inflight_shape')
        for stage in value['stages'].values():
            require(set(stage)=={'received','forwarded','ok','refused'} and all(type(n) is int and 0<=n<=100000 for n in stage.values()),'tap_stage_shape')
        if self.qualification is not None:
            q=value['qualification']
            require(set(q)=={'mode','armed','counts','last_replay','requires_runner_query_budget_check'} and q['mode']==self.qualification['mode'] and type(q['armed']) is bool and q['requires_runner_query_budget_check']==(q['mode']=='exact_pair_replay'),'tap_qualification_shape')
            require(set(q['counts'])=={'cookie_substitutions','replay_attempts','replay_refused','pum_before','pum_after','control_sequence_complete','failed'} and all(type(n) is int and 0<=n<=100000 for n in q['counts'].values()),'tap_qualification_counts')
            last=q['last_replay']
            require(last is None or (type(last) is dict and set(last)=={'elapsed_boottime_ns','through_replay_elapsed_boottime_ns','pum_before_remaining_ms','pum_after_remaining_ms'} and all(type(n) is int and n>=0 for n in last.values())),'tap_replay_shape')
        return value

# Lifecycle belongs exclusively to Supervisor; never terminate by process name.
