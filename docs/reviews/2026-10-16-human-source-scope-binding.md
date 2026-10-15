# Native Human source scope binding

Status: implementation candidate under qualification, not a production Human
endpoint or full-chain qualification. [한국어](../ko/2026-10-16-human-source-scope-binding.md).
This extends the [Human wire design](2026-10-16-human-native-wire-design.md).

A service/audience and opaque final-request digest do not tell an independent
observer which configured application, route or header manifest the source used.
The global Human source revision can cover several sibling scopes. A consumer
must not infer the selected scope from a caller-supplied resource or route label.

Add `bytes scope_sha256 = 10` to `HumanReceiptTimeReply`. The native source takes
this value from the exact compiled scope retained with its actual Engine-produced
record. ObserveTime verifies the exact proof, context and request digest and
rechecks current owners before reporting it. This is authenticated source-report
metadata over the fixed mTLS connection; the hash alone is not authentication,
a receipt, a permission, or signature-only reconstruction of a source record.
Existing Service/Workload messages and request-binding codecs are unchanged.

The fingerprint is SHA256 of this concatenation:

1. `hopae:native-human-scope:v1` followed by a NUL byte.
2. LP32(service), LP32(audience), LP32(application ID), LP32(route ID).
3. Big-endian u64 route revision, raw 32-byte destination fingerprint.
4. Big-endian u64 header-policy revision and u16 bound-header count.
5. LP32 of each configured bound-header name, sorted in ascending ASCII order.

LP32 is a big-endian u32 byte length followed by exact UTF-8 bytes. Identifiers
use the native bounded ASCII grammar; revisions are positive safe integers,
destination is nonzero, and the existing H1 header-policy validator rejects
invalid, duplicate and credential-reserved slots. Additional reserved-name filters
and entity caps do not alter an identical allowed slot manifest; they remain
mandatory validation. No body bytes, header values or cookie enter this hash.
The [independent vector](../../fixtures/human-scope-v1.json) records the full
preimage and digest. Source and SDK compute configuration fingerprints once,
not for every observation.

The SDK must require exactly 32 report bytes matching a configured Human scope
and the proof context's service/audience. Issuance must match the *specific*
prepared scope even if other trusted sibling scopes exist. Observe-only
preparation remains untrusted data until an actual authenticated source report.
Only then may an opaque Observation expose a reference to its validated immutable
configured scope. Consuming refresh must retain that exact fingerprint. Missing,
zero, wrong, sibling-app/route/destination/header fingerprints must refuse.

Pumgye uses the validated scope with its actual native route/plan owners, rather
than fabricating body bytes or treating the incoming digest as source evidence.
Actual OIDC/LDAP/TOTP through the real generated mTLS service and public opaque
SDK, including scope-substitution negatives, remains a required H2/H3 gate.
Metadata codec vectors and mock report fixtures do not close that gate.
