"""Actual lineage/replay gates: no proof constructors or admission minting."""
import hashlib
import json
from pathlib import Path

VERIFY='/hangang.hopae.v1.Authentication/Verify'
ISSUE='/hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved'
PROJECT='/hangang.hopae.v1.HumanObservedCredentialProjection/Project'
PERMIT='/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue'
OBSERVE='/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe'
DECIDE='/hangang.pumgye.v1.HumanResourceAuthorization/Decide'

class PairFailure(RuntimeError):
    def __init__(self,facts):
        super().__init__('actual_pair_scenario_refused')
        self.facts=facts

def require(ok,stage):
    if not ok:raise RuntimeError(stage)

def effect(root,backend,cookie,label):
    body=('actual-pair-'+label).encode('ascii')
    before=backend.snapshot();response=root.effect(cookie,body=body);after=backend.snapshot()
    return {'stage':label,'response':response,'request_delta':after['request_count']-before['request_count'],'effect_delta':after['effect_count']-before['effect_count'],'expected_body_sha256':hashlib.sha256(body).hexdigest(),'last_effect':after['last_effect']}

def positive(entry):
    require(entry['response']['status']==204 and entry['request_delta']==1 and entry['effect_delta']==1,'positive_exact_effect')
    require(entry['last_effect']['body_sha256']==entry['expected_body_sha256'] and entry['last_effect']['credential_match'],'positive_actual_body_credential')
    require(not {'cookie','x-forwarded-user','x-hopae-human-policy-subject','x-hopae-human-policy-issuer','x-hopae-gateway-key'} & set(entry['last_effect']['header_names']),'positive_identity_strip')

def difference(after,before,method,field):
    value=after['stages'][method][field]-before['stages'][method][field]
    require(value>=0,'monotonic_stage_counter')
    return value

def run_lineage(tap,root,backend,cookies,observations):
    facts={'contract':'actual-native-human-lineage-v1','passed':False,'controls':[]}
    try:
        require(observations['a']['subject']!=observations['b']['subject'],'distinct_native_subjects')
        initial=tap.snapshot();require(initial['qualification']['armed'] is False,'controls_unarmed')
        for account in ('a','b'):
            entry=effect(root,backend,cookies[account],account+'-'+account)
            facts['controls'].append(entry);positive(entry)
        before=tap.snapshot();require(before['qualification']['armed'] is False,'controls_still_unarmed')
        require(before['qualification']['counts']['cookie_substitutions']==0,'controls_not_mutated')
        tap.arm()
        entry=effect(root,backend,cookies['a'],'a-b');facts['attack']=entry
        after=tap.snapshot();facts['tap_before']=before;facts['tap_after']=after
        require(entry['response']['status']==503 and entry['request_delta']==0 and entry['effect_delta']==0,'lineage_no_backend')
        for method in (VERIFY,ISSUE,DECIDE):
            require(difference(after,before,method,'ok')==1,'actual_native_control_success')
        for method in (PERMIT,PROJECT):
            require(difference(after,before,method,'received')==0,'lineage_before_permission_projection')
        require(after['qualification']['counts']['cookie_substitutions']==1 and after['qualification']['counts']['failed']==0,'one_actual_cookie_substitution')
        facts['passed']=True
    except BaseException as error:
        facts['error_type']=type(error).__name__
        raise PairFailure(facts) from error
    return facts

def query_budget_gate(config_path,expected_startup_sha256,elapsed_ns):
    """Conservative elapsed upper bound; never constructs authority/deadlines.

    Config is the actual immutable Hop startup file. Native admission tick
    endpoints quantize milliseconds and remaining_at subtracts another one;
    local elapsed measurement is raw nanoseconds. Charge TWO full milliseconds.
    Refuse
    near/at the original399ms limit; no caller/proof TTL replaces this budget.
    """
    raw=Path(config_path).read_bytes()
    require(type(expected_startup_sha256) is str and hashlib.sha256(raw).hexdigest()==expected_startup_sha256,'actual_startup_config_hash')
    config=json.loads(raw)
    budget=config['gateway']['verify_budget_ms']
    require(type(budget) is int and budget==400,'actual_default_query_budget')
    rates=config['projection_receiver']['observed_clock_rates']
    require(set(rates)=={'source_ppm','receiver_ppm'},'actual_receiver_rates')
    source=rates['source_ppm'];receiver=rates['receiver_ppm']
    require(type(source) is int and type(receiver) is int and source==500 and receiver==500,'actual_fixed_clock_rates')
    require(type(elapsed_ns) is int and 0<=elapsed_ns<=1000000000,'elapsed_boottime_bound')
    denominator=(1000000-receiver)*1000000
    numerator=elapsed_ns*(1000000+source)
    upper_ms=(numerator+denominator-1)//denominator+2
    limit_ms=min(budget,1000)-1
    return {'startup_config_sha256':expected_startup_sha256,'configured_verify_budget_ms':budget,'original_admission_limit_ms':limit_ms,'source_ppm':source,'receiver_ppm':receiver,'through_replay_boottime_ns':elapsed_ns,'conservative_elapsed_upper_ms':upper_ms,'quantization_charge_ms':2,'query_expiry_excluded':upper_ms<limit_ms}

def run_replay(tap,root,backend,cookie,hop_config,expected_startup_sha256,prepare_transport=False):
    facts={'contract':'actual-native-human-pair-replay-v1','passed':False}
    try:
        require(tap.snapshot()['qualification']['armed'] is False,'replay_control_unarmed')
        entry=effect(root,backend,cookie,'unarmed');facts['control']=entry;positive(entry)
        before=tap.snapshot();require(before['qualification']['counts']['replay_attempts']==0,'no_control_replay')
        if prepare_transport:
            require(before['qualification']['armed'] is False,'prepare_before_arm')
            require(all(type(v) is int and v==0 for v in before['stages'][OBSERVE].values()),'prepare_observe_rpc_zero_before')
            ack=tap.prepare_replay_transport();facts['transport_preparation']=ack
            require(ack.get('ok') is True and ack.get('prepared') is True and type(ack.get('elapsed_boottime_ns')) is int,'prepare_transport_success')
            prepared=tap.snapshot();facts['transport_preparation_snapshot']=prepared
            require(prepared['qualification']['replay_transport']=={'prepared':True,'elapsed_boottime_ns':ack['elapsed_boottime_ns']},'prepare_snapshot_matches_ack')
            require(prepared['qualification']['armed'] is False,'prepare_keeps_unarmed')
            require(all(type(v) is int and v==0 for v in prepared['stages'][OBSERVE].values()),'prepare_observe_rpc_zero_after')
            require(prepared['qualification']['counts']['replay_attempts']==0,'prepare_no_replay')
            before=prepared
        tap.arm()
        entry=effect(root,backend,cookie,'armed');facts['armed']=entry
        after=tap.snapshot();facts['tap_before']=before;facts['tap_after']=after
        positive(entry)
        qualification=after['qualification'];counts=qualification['counts']
        require(qualification['armed'] is True and qualification['requires_runner_query_budget_check'] is True,'replay_explicit_state')
        for name in ('replay_attempts','replay_refused','pum_before','pum_after','control_sequence_complete'):
            require(counts[name]==1,'one_exact_replay_sequence')
        require(counts['failed']==0 and counts['cookie_substitutions']==0,'no_replay_hook_failure')
        gate=query_budget_gate(hop_config,expected_startup_sha256,qualification['last_replay']['through_replay_elapsed_boottime_ns']);facts['query_budget']=gate
        if not gate['query_expiry_excluded']:
            facts['inconclusive']=True
            raise RuntimeError('original_query_expiry_not_excluded')
        for method in (ISSUE,PERMIT,PROJECT):
            require(difference(after,before,method,'ok')==1,'one_original_request_chain')
        facts['passed']=True
    except BaseException as error:
        facts['error_type']=type(error).__name__
        raise PairFailure(facts) from error
    return facts
