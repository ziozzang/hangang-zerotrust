# Request binding v2: canonical pure codec

Status: reference contract and synthetic cross-language vectors, **not Human RPC,
identity evidence, permission, route activation or full-chain qualification**.
[한국어](../ko/2026-10-16-request-binding-v2.md).
Base ZT `0426f3b`. V1 component bytes and existing vectors are untouched.

The earlier Human design's nested length framing of numbers is superseded by the
following sole v2 encoding. All integers are unsigned big endian. LP32 is a four
byte length followed by exactly that many bytes. Hash the complete preimage with
SHA-256:

1. ASCII `hangang-zerotrust:credential-projection:request:v2` plus one NUL.
2. LP32(service), LP32(audience), LP32(route ID).
3. Route revision u64; destination-owner digest raw 32 bytes.
4. LP32(method), LP32(exact final origin-form target).
5. Actual complete entity byte length u64; SHA256(actual complete entity) raw32.
6. Header-policy revision u64; manifest slot count u16.
7. Each manifest slot in ascending ASCII name order: LP32(name), presence u8
   exactly 0 or 1; **only when present**, LP32(exact value bytes).

Absence emits no value length. Present-empty emits presence1 and LP32 length0.
The fixed manifest and explicit slots must match exactly: duplicate, omitted or
unknown slots refuse. Slot input order does not affect encoding. Other actual
request headers are outside this descriptor; they are not automatically errors
or claimed as bound. The reference accepts actual body bytes only, never a caller
hash/length shortcut. Complete-body limit is 16 MiB; an owning deployment can
require a smaller limit. Streaming/trailers require a separate contract.

Service/audience/route ID: 1..128 ASCII alphanumeric or `_.:-`. Revisions:
1..9007199254740991, rejecting booleans. Method: 1..32 uppercase ASCII letters or
hyphen. Target: 1..8192 ASCII graphic bytes, starts `/` but not `//`, no fragment,
backslash or malformed percent triplet. Do not normalize path/query/percent case.
Destination digest must be exactly32 bytes and nonzero; this is metadata validity,
never authentication or permission. No URL or backend ownership follows from it.

Manifest: 0..16 unique lowercase RFC token names, each1..128 bytes. Empty is valid
with a positive policy revision. Values: each0..1024 bytes, total<=8192. Reject
00..1f (including TAB) and7f; preserve80..ff exactly, without UTF8 decoding or
whitespace trimming. An absent value has no bytes.

Static forbidden names: authorization, proxy-authorization, proxy-authenticate,
www-authenticate, cookie, set-cookie, host, forwarded, connection, keep-alive,
content-length, transfer-encoding, te, trailer, upgrade, expect. Forbidden prefixes:
x-forwarded-, x-hopae-, x-hangang-, x-pumgye-, x-sumunjang-. Policy compilation also
accepts up to64 unique valid configured reserved names and refuses intersection:
actual route/projected-credential/caller/identity names MUST be included by the
integrator. A pure codec cannot discover custom credential names. These exclusions
do not authorize forwarding spoofed security headers; separate owners sanitize them.

`tools/request_binding_v2_reference.py` is the deterministic executable reference.
`fixtures/request-binding-v2.json` contains full expected preimage hex and digest,
actual body/destination hex, explicit absent/present slots, including empty body,
same-length body mutation, obs-text, maximum revisions and empty manifest. Fixtures
are synthetic reserved examples. Rust must consume these expected hashes rather
than regenerate expected values using itself. This is cross-language test input,
not yet a claim that a second implementation passed.

Run `python3 -m unittest discover -s tools -p test_request_binding_v2_reference.py -v`.
Eight tests cover independent mutations of every owner field/body, input ordering,
absence/empty distinction, unknown/duplicate/missing slots, static/custom security
names, every forbidden control byte, aggregate/body bounds and v1's fixed digest
`234488f459d8b3069a74d308d639fa9bfb402b12a9544a413c06c6136a8dab11`.

Integration remains responsible for same immutable transformed request, fixed
manifest revision/route/destination ownership, recomputation before dispatch,
original age/current owner fences, and native session authentication. No public
constructor in this reference yields a trusted observation or grant.
