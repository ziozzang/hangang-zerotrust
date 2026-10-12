# Native runtime protocols

[한국어](ko/PROTOCOLS.md) · [Index](README.md)

Status: Guard transport exists; Hopae fast transport is proposed and must be
qualified against its existing HTTP verification engine.

## Shared principles

Both runtimes remain separate services. Hangang uses bounded persistent pools,
once-per-connection service authentication, explicit versions and message types,
request identifiers, deadlines, admission limits and deterministic cleanup.
Remote deployment requires authenticated transport (for example mTLS) and
service identity. Initial loopback IPC does not establish trust in arbitrary
processes running on the same machine: use separate least-privilege credentials.

A pooled connection is authenticated, not an authorization lease for every
future request. Every identity/network decision uses current required evidence.
No response may be associated with another request ID. Late replies, cancellation,
partial frames and reader ownership are part of the protocol, not implementation
accidents. Credential rotation, authority restart and shutdown retire connections.

## Guard

Keep its current fixed 24-byte IP decision frames and HTTP signal/admin path.
The transport carries the narrow query it was designed for. Preserve explicit
deny versus dependency failure. Optional IP caching is off by default and only
1–5 seconds when enabled. Existing benchmark results are for documented Guard
transport workloads, not a blanket full-stack or identity-verification SLA.

## Hopae proposal

Identity verification includes application/host, method/path, verified client
address/scheme, configured cookie/authorization inputs and required request
metadata. A 24-byte IP frame cannot express that. Start with a bounded, versioned
variable-payload protocol rather than disguising identity as an IP query.

Provisional framing: fixed header with magic/version, message type, flags,
request ID and payload length; bounded authentication handshake; bounded verify
request and result; a negotiated request/response size ceiling; no unbounded
header map or provider blob. Exact field layout and encoding require an ADR
before interoperability code. Prototype JSON payloads can establish semantics;
compact typed encoding is a measured optimization, not an authority change.

Serialize only protocol-approved fields. Treat duplicate/ambiguous credentials
exactly as HTTP. Host/application binding and trusted client context must not be
lost when replacing forwarded HTTP headers. A result includes outcome, approved
identity/output headers or native redirect/challenge, policy/session revision and
validity. Hopae cookies remain governed by its native flow and integrity rules.

## Implementation sequence

1. Extract provider-independent request/result contracts.
2. Create HTTP/native golden fixtures that enter one Hopae verify engine.
3. Implement authenticated bounded framing and cancellation.
4. Implement Hangang pooled client and native login/logout integration.
5. Qualify parser/security parity, revocation and provider/session failure cases.
6. Profile and optimize encoding/pools without relaxing checks.

## Qualification matrix

Measure HTTP and native transport independently, then the complete gateway path:
valid/invalid/expired sessions; JWT validation where applicable; unknown handles;
step-up/challenge; cold/rotating/revoked identities; large approved inputs; negative
lookups; concurrent admin changes; backend saturation; token/key rotation; restart;
malformed frames; zero/truncated/excess lengths; wrong request IDs and replay.

Separate warm local verification from provider login/callback traffic. A provider
round trip cannot be equated to a local decision lookup. Report achieved QPS,
error counts, CPU/RSS, p50/p95/p99 and workload conditions for 10k and 100k targets.
No success claim is justified by a synthetic allow-only loop or cached identities
that no longer satisfy the revocation contract.
