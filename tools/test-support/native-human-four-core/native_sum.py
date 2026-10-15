"""Actual Sum bootstrap using the qualified helper's native management API."""
import ipaddress
import pathlib
import secrets
import ssl
import time
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'native-human-runtime'))
import sum_runtime as qualified
from supervisor import private, require

class NativeSum(qualified.Fixture):
    def __init__(self, supervisor, tls, client_ip='192.0.2.10'):
        self.root=supervisor.root/'sum';self.root.mkdir(mode=0o700)
        self.channel=None;self.log=None
        self.ip=str(ipaddress.ip_address(client_ip));self.network=self.ip+('/32' if ':' not in self.ip else '/128')
        self.tls=tls;self.admin=secrets.token_hex(32);self.collector=secrets.token_hex(32)
        private(self.root/'collector',self.collector.encode())
        self.http,self.native,self.transport=qualified.port(),qualified.port(),qualified.port()
        private(self.root/'bootstrap.json',{'mode':'enforce','allow':[self.network],'auto_block':False})
        argv=[supervisor.entries['sumunjang']['binary'],'--bootstrap-policy',str(self.root/'bootstrap.json'),'--supervised','--listen',f'127.0.0.1:{self.http}','--database',str(self.root/'authority.sqlite3'),'--decision-listen',f'127.0.0.1:{self.native}','--grpc-listen',f'127.0.0.1:{self.transport}','--decision-tls-cert',tls['certificate'],'--decision-tls-key',tls['key'],'--decision-client-ca',tls['ca'],'--management-tls']
        self.process=supervisor.start('sumunjang',argv,{'HANGANG_GUARD_ADMIN_TOKEN':self.admin,'HANGANG_GUARD_COLLECTOR_TOKEN':self.collector})
        self.context=ssl.create_default_context(cafile=tls['ca']);self.context.load_cert_chain(tls['certificate'],tls['key'])
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            require(self.process.poll() is None,'sum_startup_exit')
            try:
                if self.management('/healthz',token=False)[0]==200:break
            except OSError:pass
            time.sleep(.05)
        else:raise RuntimeError('sum_readiness')
        self.ready=dict(tls,endpoint=f'https://127.0.0.1:{self.transport}',collector_file=str(self.root/'collector'),client_ip=self.ip,http_url=f'https://127.0.0.1:{self.http}')

    def close(self):
        # Exact process/group belongs to Supervisor, no duplicate/name cleanup.
        pass
