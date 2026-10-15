"""Phase-one unchanged PUBLIC raw forwarding tap: safe method/status counters."""
import hashlib
import json
import pathlib
import selectors
import time
import socket
import threading
from supervisor import private, require

TAP_SHA='e31c188d53d6f9301ab489eaa075bce140baa183fdd0a574d77d90bdfc105609'
HOOK_SHA='5c1d5a8a419f0378c4df09442bcb25cf4d96537e42b7cf1721225b77a7f42f17'
METHODS=('/hangang.hopae.v1.Authentication/Verify','/hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved','/hangang.hopae.v1.HumanAuthenticationReceipts/ObserveTime','/hangang.hopae.v1.HumanObservedCredentialProjection/Project')

PUM_METHODS=('/hangang.pumgye.v1.Authorization/Decide','/hangang.pumgye.v1.HumanResourceAuthorization/Decide','/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue')

class NativeTap:
    def __init__(self,supervisor,tls,hop,caller,interpreter,pum=None):
        self.lock=threading.Lock()
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
        self.methods=tuple(upstreams)
        cfg={'listen':self.address,'tls':{k:tls[k] for k in ('ca','certificate','key')},'inbound_caller_file':str(self.root/'inbound'),'upstreams':upstreams,'maximum_inflight':16}
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

    def _snapshot(self):
        self.process.stdin.write(b'{"op":"snapshot"}\n');self.process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            require(bool(selector.select(timeout=3)),'tap_snapshot_timeout')
            raw=self.process.stdout.readline(16385)
        require(len(raw)<=16384,'tap_snapshot_bound')
        value=json.loads(raw)
        require(set(value)=={'contract','inflight','stages'} and value['contract']=='qualification-grpc-tap-v1' and set(value['stages'])==set(self.methods),'tap_snapshot_shape')
        require(type(value['inflight']) is int and 0<=value['inflight']<=16,'tap_inflight_shape')
        for stage in value['stages'].values():
            require(set(stage)=={'received','forwarded','ok','refused'} and all(type(n) is int and 0<=n<=100000 for n in stage.values()),'tap_stage_shape')
        return value

# Lifecycle belongs exclusively to Supervisor; never terminate by process name.
