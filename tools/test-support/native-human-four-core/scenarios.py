"""Fresh-request gates over already-running real owners; never proof constructors.
These scenarios do not prove in-flight withdrawal or reinterpret expiry as revocation.
"""
import hashlib


class ScenarioFailure(RuntimeError):
    def __init__(self, facts):
        super().__init__('fresh_request_scenario_refused')
        self.facts = facts


def run_fresh_gates(hop, pum, root, backend, network, subject, cookie_aal1, observe_aal2):
    """observe_aal2(cookiefile) must invoke the reviewed actual public SDK tool.

    Caller persists returned facts (or ScenarioFailure.facts) privately. AAL2
    login can wait a TOTP counter; control time is distinct from proof budgets.
    All tested HTTP requests acquire fresh proofs through the actual Root.
    """
    facts = {'contract': 'native-human-fresh-request-gates-v1', 'passed': False,
             'in_flight_withdrawal_proved': False, 'checks': [], 'cleanup_failures': []}
    stage = 'aal2_policy'
    failed = None

    def effect(label, cookie, allowed):
        body = ('actual-human-'+label).encode('ascii')
        before = backend.snapshot()
        response = root.effect(cookie, body=body)
        after = backend.snapshot()
        entry = {'stage': label, 'status': response['status'],
                 'request_delta': after['request_count']-before['request_count'],
                 'effect_delta': after['effect_count']-before['effect_count']}
        facts['checks'].append(entry) # Preserve status/deltas BEFORE asserting.
        if allowed:
            expected = hashlib.sha256(body).hexdigest()
            if response['status'] != 204 or entry['request_delta'] != 1 or entry['effect_delta'] != 1 or after['last_effect']['body_sha256'] != expected:
                raise RuntimeError('positive_oracle')
            if not after['last_effect'].get('credential_match'):
                raise RuntimeError('credential_oracle')
        elif response['status'] != 403 or entry['request_delta'] != 0 or entry['effect_delta'] != 0:
            raise RuntimeError('denial_oracle')

    def network_floor(aal):
        document = pum.policy()
        networks = document['policy']['services']['orders']['networks']
        if len(networks) != 1:
            raise RuntimeError('fixed_network_scope')
        networks[0]['roles'] = ['reader'+str(aal)]
        return pum.publish(document)

    try:
        stage = 'network_aal2_floor_denies_aal1'
        network_floor(2)
        effect(stage, cookie_aal1, False)
        stage = 'network_aal1_floor_restores_aal1'
        network_floor(1)
        effect(stage, cookie_aal1, True)
        # Test AAL1 while its actual primary session still exists, BEFORE new TOTP login.
        changed = pum.grant([subject], minimum_aal=2)
        facts['aal2_policy_revision'] = changed['revision']
        stage = 'aal1_denied_by_role2'
        effect(stage, cookie_aal1, False)
        stage = 'actual_native_totp_login'
        cookie2 = hop.login_account('a', 2)
        stage = 'actual_sdk_aal2_observe'
        observed = observe_aal2(cookie2)
        if observed['subject'] != subject or type(observed['aal']) is not int or observed['aal'] != 2 or observed.get('issued') is not True or observed.get('independently_observed') is not True:
            raise RuntimeError('actual_aal2_observer')
        facts['aal2_scope_sha256'] = observed['scope_sha256']
        stage = 'aal2_positive'
        effect(stage, cookie2, True)
        stage = 'network_aal2_floor_allows_aal2'
        network_floor(2)
        effect(stage, cookie2, True)
        network_floor(1)
        stage = 'human_policy_withdraw'
        facts['withdraw_revision'] = pum.withdraw([subject])['revision']
        effect(stage, cookie2, False)
        stage = 'human_policy_restore'
        facts['restore_revision'] = pum.grant([subject], minimum_aal=2)['revision']
        effect(stage, cookie2, True)
        stage = 'actual_sum_deny'
        network.cas(True) # Actual management CAS + block; empty allow is NOT deny-all.
        effect(stage, cookie2, False)
        stage = 'actual_sum_restore'
        network.cas(False)
        effect(stage, cookie2, True)
        facts['passed'] = True
    except BaseException as error:
        failed = error
        facts.update(failed_stage=stage, error_type=type(error).__name__)
        # Restore the scenario's declared role2/allow baseline without masking failure.
        for name, restore in [('policy', lambda: pum.grant([subject], minimum_aal=2)),
                              ('network_floor', lambda: network_floor(1)),
                              ('network', lambda: network.cas(False))]:
            try:
                restore()
            except BaseException:
                facts['cleanup_failures'].append(name)
    if failed is not None or facts['cleanup_failures']:
        raise ScenarioFailure(facts) from failed
    return facts
