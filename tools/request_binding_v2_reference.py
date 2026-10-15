"""Pure reference metadata codec; no authentication or permission capability."""
import hashlib
import re
import struct

DOMAIN = b'hangang-zerotrust:credential-projection:request:v2\0'
SAFE = 9007199254740991
FORBIDDEN = set('authorization proxy-authorization proxy-authenticate www-authenticate cookie set-cookie host forwarded connection keep-alive content-length transfer-encoding te trailer upgrade expect'.split())
PREFIXES = ('x-forwarded-', 'x-hopae-', 'x-hangang-', 'x-pumgye-', 'x-sumunjang-')
NAME = re.compile(r"[!#$%&'*+.^_`|~0-9a-z-]{1,128}\Z")
ID = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')

def require(ok):
    if not ok:
        raise ValueError('invalid binding metadata')

def lp(value):
    return struct.pack('>I', len(value)) + value

def revision(value):
    require(type(value) is int and 1 <= value <= SAFE)
    return struct.pack('>Q', value)

def encode(request, manifest, slots, reserved=()):
    """Actual bytes required: no digest-only or entity-length input exists."""
    names = list(manifest)
    reserved = list(reserved)
    require(len(names) <= 16 and len(reserved) <= 64)
    require(all(type(n) is str and NAME.fullmatch(n) for n in names + reserved))
    require(len(set(names)) == len(names) and len(set(reserved)) == len(reserved))
    require(not any(n in FORBIDDEN or n.startswith(PREFIXES) or n in reserved for n in names))
    require(len(slots) == len(names))
    values = {}
    for name, value in slots:
        require(name in names and name not in values)
        require(value is None or type(value) is bytes)
        if value is not None:
            require(len(value) <= 1024 and not any(b < 32 or b == 127 for b in value))
        values[name] = value
    require(sum(len(v) for v in values.values() if v is not None) <= 8192)
    fields = []
    for key in ('service', 'audience', 'route_id'):
        value = request[key]
        require(type(value) is str and ID.fullmatch(value))
        fields.append(lp(value.encode('ascii')))
    fields.append(revision(request['route_revision']))
    dest = request['destination']
    require(type(dest) is bytes and len(dest) == 32 and any(dest))
    fields.append(dest)
    method, target, body = request['method'], request['target'], request['body']
    require(type(method) is str and re.fullmatch('[A-Z-]{1,32}', method))
    require(type(target) is str and 1 <= len(target) <= 8192 and target.startswith('/') and not target.startswith('//'))
    require(all(33 <= ord(c) <= 126 and c not in '#\\' for c in target))
    require(not re.search(r'%(?![0-9a-fA-F]{2})', target))
    require(type(body) is bytes and len(body) <= 16 * 1024 * 1024)
    fields += [lp(method.encode('ascii')), lp(target.encode('ascii')), struct.pack('>Q', len(body)), hashlib.sha256(body).digest(), revision(request['header_policy_revision']), struct.pack('>H', len(names))]
    for name in sorted(names):
        value = values[name]
        fields += [lp(name.encode('ascii')), bytes([value is not None])]
        if value is not None:
            fields.append(lp(value))
    return DOMAIN + b''.join(fields)

def digest(request, manifest, slots, reserved=()):
    return hashlib.sha256(encode(request, manifest, slots, reserved)).hexdigest()
