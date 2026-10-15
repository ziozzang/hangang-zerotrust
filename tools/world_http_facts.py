"""Qualification-only nonreflecting HTTP failure facts; successful bodies omitted."""
import hashlib

FIXED_BODIES = {
    b'authorization refused': 'authorization_refused',
    b'Pumgye authority unavailable': 'pumgye_authority_unavailable',
    b'resource permission denied': 'resource_permission_denied',
    b'route authorization retired': 'route_authorization_retired',
    b'Workload resource authority requires typed remote decision': 'workload_typed_authority_required',
    b'native resource authority unavailable': 'native_resource_authority_unavailable',
    b'native dispatch expired': 'native_dispatch_expired',
}


def failure_body_facts(status, body):
    if status == 200:
        return {}
    code = FIXED_BODIES.get(body)
    return {'failure_code': code} if code else {'failure_code': 'other', 'failure_body_bytes': len(body), 'failure_body_sha256': hashlib.sha256(body).hexdigest()}


def response_facts(status, body, at_ms, elapsed_ms):
    return {'at_unix_ms': at_ms, 'status': status, 'elapsed_ms': elapsed_ms, 'backend_delta': None, **failure_body_facts(status, body)}
