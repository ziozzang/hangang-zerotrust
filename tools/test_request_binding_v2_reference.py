import copy
import hashlib
import json
from pathlib import Path
import unittest
from request_binding_v2_reference import encode, digest, SAFE

BASE = dict(service='orders', audience='orders-api', route_id='orders-route', route_revision=1, destination=bytes(range(32)), method='POST', target='/base/orders?q=%2F&q=2', body=b'{"a":1}', header_policy_revision=1)
MANIFEST = ['x-order-intent', 'content-type']
SLOTS = [('content-type', b'application/json'), ('x-order-intent', None)]

def vectors():
    cases = []
    for name, body, value in [('absent', b'{"a":1}', None), ('empty', b'{"a":1}', b''), ('actual-empty-body', b'', None), ('same-length-mutated-body', b'{"a":2}', None), ('opaque-header-bytes', b'\x00\xff', b'\x80\xff'), ('max-revisions', b'body', b'intent')]:
        r = dict(BASE, body=body)
        if name == 'max-revisions':
            r.update(route_revision=SAFE, header_policy_revision=SAFE)
        slots = [('x-order-intent', value), SLOTS[0]]
        raw = encode(r, MANIFEST, slots)
        cases.append(dict(name=name, request={k:(v.hex() if isinstance(v, bytes) else v) for k,v in r.items()}, manifest=MANIFEST, slots=[dict(name=k, value_hex=None if v is None else v.hex()) for k,v in slots], encoding_hex=raw.hex(), sha256=hashlib.sha256(raw).hexdigest()))
    r = dict(BASE, body=b'')
    raw = encode(r, [], [])
    cases.append(dict(name='empty-manifest', request={k:(v.hex() if isinstance(v, bytes) else v) for k,v in r.items()}, manifest=[], slots=[], encoding_hex=raw.hex(), sha256=hashlib.sha256(raw).hexdigest()))
    return dict(format='human-request-binding-v2-reference-1', byte_fields=['destination','body'], vectors=cases)

class Contract(unittest.TestCase):
    def test_frozen_vectors(self):
        self.assertEqual(json.loads((Path(__file__).parents[1]/'fixtures/request-binding-v2.json').read_text()), vectors())
    def test_order_and_presence(self):
        self.assertEqual(encode(BASE, MANIFEST, SLOTS), encode(BASE, MANIFEST[::-1], SLOTS[::-1]))
        self.assertNotEqual(digest(BASE, MANIFEST, SLOTS), digest(BASE, MANIFEST, [SLOTS[0], ('x-order-intent', b'')]))
    def test_every_owner_field_and_actual_body_changes(self):
        original = digest(BASE, MANIFEST, SLOTS)
        for key, value in dict(service='other', audience='other', route_id='other', route_revision=2, destination=b'x'*32, method='PUT', target='/base/orders?q=%2f&q=2', body=b'{"a":2}', header_policy_revision=2).items():
            with self.subTest(key=key):
                self.assertNotEqual(original, digest(dict(BASE, **{key:value}), MANIFEST, SLOTS))
    def test_refuse_ambiguous_slots_and_security_headers(self):
        for manifest, slots, reserved in [(['content-type'], [], []), (MANIFEST, [SLOTS[0], SLOTS[0]], []), (['authorization'], [('authorization', b'x')], []), (['x-forwarded-email'], [('x-forwarded-email', b'x')], []), (['x-credential'], [('x-credential', b'x')], ['x-credential']), (['Content-Type'], [('Content-Type', b'x')], []), (MANIFEST, [SLOTS[0], ('unknown', None)], [])]:
            with self.assertRaises(ValueError): encode(BASE, manifest, slots, reserved)
    def test_all_control_bytes_and_size_limits(self):
        for value in [bytes([i]) for i in list(range(32))+[127]] + [b'a'*1025]:
            with self.assertRaises(ValueError): encode(BASE, ['x-intent'], [('x-intent', value)])
        with self.assertRaises(ValueError): encode(BASE, ['x'+str(i) for i in range(9)], [('x'+str(i), b'a'*1024) for i in range(9)])
        with self.assertRaises(ValueError): encode(dict(BASE, body=b'a'*(16*1024*1024+1)), [], [])
    def test_invalid_reference_revision_target_and_no_digest_shortcut(self):
        for key, values in dict(route_revision=[0, SAFE+1, True], header_policy_revision=[0,-1], destination=[bytes(32), b'x'], target=['//evil.example/','/x#y','/x%','/x\\y','/x\r'], body=['caller-digest']).items():
            for value in values:
                with self.assertRaises(ValueError): encode(dict(BASE, **{key:value}), [], [])
    def test_exact_boundaries_and_field_framing(self):
        names = ['x'+str(i) for i in range(16)]
        encode(BASE, names, [(n, None) for n in names])
        with self.assertRaises(ValueError): encode(BASE, names+['extra'], [(n, None) for n in names+['extra']])
        eight = names[:8]
        encode(BASE, eight, [(n, b'a'*1024) for n in eight])
        with self.assertRaises(ValueError): encode(BASE, names[:9], [(n, b'a'*1024) for n in eight]+[(names[8], b'a')])
        punctuation = "!#$%&'*+.^_`|~"
        encode(BASE, [punctuation], [(punctuation, b'\x80\xff')])
        encode(BASE, ['a'*128], [('a'*128, None)], ['r'+str(i) for i in range(64)])
        with self.assertRaises(ValueError): encode(BASE, ['a'*129], [('a'*129, None)])
        with self.assertRaises(ValueError): encode(BASE, [], [], ['r'+str(i) for i in range(65)])
        encode(dict(BASE, body=b'a'*(16*1024*1024)), [], [])
        self.assertNotEqual(digest(dict(BASE, service='ab', audience='c'), [], []), digest(dict(BASE, service='a', audience='bc'), [], []))

    def test_v1_fixed_vector_unchanged(self):
        fields=[b'ab',b'c',b'GET',b'/private?x=1',hashlib.sha256(b'').digest()]
        raw=b'hangang-zerotrust:credential-projection:request:v1\0'+b''.join(len(v).to_bytes(4,'big')+v for v in fields)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'234488f459d8b3069a74d308d639fa9bfb402b12a9544a413c06c6136a8dab11')

if __name__ == '__main__': unittest.main()
