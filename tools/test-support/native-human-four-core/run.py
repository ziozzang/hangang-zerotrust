#!/usr/bin/env python3
"""Local actual four-core qualification: exact binaries, real owners, private IPC."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from supervisor import Supervisor, private, require
from bootstrap import NativeHop
from native_sum import NativeSum
from native_root import NativeRoot, source_scope
from backend import Backend
from pum_runtime import PumRuntime


def observe(binary, expected, ready, cookie, directory, account):
    require(hashlib.sha256(Path(binary).read_bytes()).hexdigest()==expected,'observer_hash')
    ready=json.loads(Path(ready).read_text())
    fields={'endpoint','server_name','ca','certificate','key','caller_file','public_key','issuer_ref','key_epoch','identity_authority','minimum_source_revision','minimum_application_generation','minimum_key_registry_revision','scope'}
    config={k:ready[k] for k in fields}
    config.update(cookie_file=str(cookie),source_error_ppm=500,receiver_error_ppm=500,frontend_url='https://app.example.test/effect',client_ip='192.0.2.10',method='POST',target='/effect',body='bootstrap',bound_headers=[{'name':'x-tenant','value':'bootstrap'}])
    config_path=directory/('seed-config-'+account+'.json');private(config_path,config)
    output=directory/('subject-'+account+'.json')
    log=directory/('observer-'+account+'-private.log')
    with log.open('xb') as stream:
        os.chmod(log,0o600)
        reply=subprocess.run([binary,str(config_path)],stdout=subprocess.PIPE,stderr=stream,timeout=15)
    require(reply.returncode==0 and len(reply.stdout)<=4096,'actual_sdk_observer')
    value=json.loads(reply.stdout)
    require(set(value)=={'contract','seed_only','issued','independently_observed','subject','aal','scope_sha256'},'observer_output_shape')
    require(value['contract']=='human-seed-observer-v1' and all(value[k] is True for k in ('seed_only','issued','independently_observed')),'observer_actual_evidence')
    private(output,value)
    subject=value['subject'];digest=value['scope_sha256']
    require(type(subject) is str and subject.startswith('human1:') and len(subject)==71 and all(c in '0123456789abcdef' for c in subject[7:]),'observer_subject')
    require(type(value['aal']) is int and value['aal'] in (1,2),'observer_aal')
    require(type(digest) is str and len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'observer_scope')
    return value


def run(args):
    entries=json.loads(Path(args.manifest).read_text())
    require(hashlib.sha256(Path(args.observer).read_bytes()).hexdigest()==args.observer_sha256,'observer_hash')
    supervisor=Supervisor(args.directory,entries)
    hop=None;backend=None;tap=None;phase='pki';error=None;facts={'manifest_sha256':hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),'binary_preflight':'binary-preflight.json','observer_sha256':args.observer_sha256};cleanup=[]
    try:
        tls=supervisor.pki()
        origin_secret=secrets.token_urlsafe(36)
        backend=Backend(supervisor.root/'backend',b'Bearer '+origin_secret.encode())
        scopes=[source_scope(backend.origin)]
        network=NativeSum(supervisor,tls['sumunjang'])
        hop_caller=secrets.token_urlsafe(36);pum_caller=secrets.token_urlsafe(36);route_caller=secrets.token_urlsafe(36)
        pum=PumRuntime(supervisor,tls['pumgye'],pum_caller)
        phase='hop_startup'
        hop=NativeHop(supervisor,tls['hopae'],scopes,pum.endpoint,pum.public_key,hop_caller,pum_caller,origin_secret)
        private(supervisor.root/'hop-ready.json',hop.metadata)
        phase='tap_startup'
        from tap_runtime import NativeTap
        tap_caller=secrets.token_urlsafe(36)
        private(supervisor.root/'pum-caller',pum_caller.encode())
        pum_transport=dict(tls['pumgye'],endpoint=pum.endpoint,caller_file=str(supervisor.root/'pum-caller'))
        tap=NativeTap(supervisor,tls['tap'],hop.metadata,tap_caller,args.tap_python,pum=pum_transport)
        phase='root_startup'
        root=NativeRoot(supervisor,tls['hangang'],backend.origin,tap.metadata,pum,network.ready,tap_caller,tap_caller,route_caller,decision_endpoint=tap.pum_metadata['endpoint'])
        phase='pum_startup'
        pum.start(hop.metadata,network.ready,root.route_transport,hop.metadata['scopes'],dict(tls['hopae'],address=hop.metadata['endpoint']),hop_caller,route_caller)
        phase='root_startup'
        root.start()
        phase='native_login'
        cookies={a:hop.login_account(a,1) for a in ('a','b')}
        phase='actual_sdk_observe'
        observations={a:observe(args.observer,args.observer_sha256,supervisor.root/'hop-ready.json',cookies[a],supervisor.root,a) for a in ('a','b')}
        require(observations['a']['subject']!=observations['b']['subject'],'native_account_separation')
        facts['seed_observations']=observations
        phase='native_policy_grant'
        pum.grant([v['subject'] for v in observations.values()],minimum_aal=1)
        facts['grant_revision']=pum.policy()['revision']
        phase='actual_http_positive'
        before=backend.snapshot();response=root.effect(cookies['a']);after=backend.snapshot()
        facts['first_http']=response
        facts['backend']={'request_delta':after['request_count']-before['request_count'],'effect_delta':after['effect_count']-before['effect_count'],'last_effect':after['last_effect']}
        require(response['status']==204,'first_http_status')
        require(facts['backend']['request_delta']==1 and facts['backend']['effect_delta']==1,'first_http_exact_effect')
        require(after['last_effect']['body_sha256']==hashlib.sha256(b'actual-human-effect').hexdigest(),'final_actual_body')
        require(not {'cookie','x-hopae-human-policy-subject','x-hopae-human-policy-issuer','x-forwarded-user','x-hopae-gateway-key'} & set(after['last_effect']['header_names']),'origin_identity_strip')
        if args.fresh_gates:
            phase='fresh_request_gates'
            from scenarios import run_fresh_gates, ScenarioFailure
            try:
                facts['fresh_gates']=run_fresh_gates(hop,pum,root,backend,network,observations['a']['subject'],cookies['a'],lambda cookie:observe(args.observer,args.observer_sha256,supervisor.root/'hop-ready.json',cookie,supervisor.root,'a-aal2'))
            except ScenarioFailure as failure:
                facts['fresh_gates']=failure.facts
                raise
        facts['passed']=True
    except BaseException as caught:
        error=caught
        facts.update(passed=False,failed_phase=phase,error_type=type(caught).__name__)
    finally:
        if tap is not None:
            try:facts['tap']=tap.snapshot()
            except BaseException:
                facts['tap_snapshot_failed']=True
                facts['passed']=False
                facts.setdefault('failed_phase','tap_snapshot')
        # Attempt each owned cleanup and preserve the primary gate failure.
        for name,close in [('cores',supervisor.close),('issuer',hop.close if hop else lambda:None),('backend',backend.close if backend else lambda:None)]:
            try:close()
            except BaseException:cleanup.append(name)
        facts['cleanup_failures']=cleanup
        if cleanup:facts['passed']=False
        private(supervisor.root/'RESULT.json',facts)
    return 0 if facts.get('passed') else 1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',required=True);parser.add_argument('--directory',required=True)
    parser.add_argument('--tap-python',required=True)
    parser.add_argument('--fresh-gates',action='store_true',help='actual fresh HTTP MFA/policy/network gates; no in-flight claim')
    parser.add_argument('--observer',required=True);parser.add_argument('--observer-sha256',required=True)
    args=parser.parse_args()
    os.umask(0o077)
    return run(args)

if __name__=='__main__':sys.exit(main())
