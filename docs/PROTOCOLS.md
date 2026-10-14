# Native runtime protocols

[한국어](ko/PROTOCOLS.md) · [Index](README.md)

Status: Guard transport exists; HOP1 Hopae transport and the Hangang pool are
implemented with HTTP/session parity tests. Production throughput qualification
and future integrated-decision revision contracts remain separate gates.

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

## Hopae design history

Identity verification includes application/host, method/path, verified client
address/scheme, configured cookie/authorization inputs and required request
metadata. A 24-byte IP frame cannot express that. Start with a bounded, versioned
variable-payload protocol rather than disguising identity as an IP query.

The initial proposal (superseded by ADR 0008): fixed header with magic/version, message type, flags,
request ID and payload length; bounded authentication handshake; bounded verify
request and result; a negotiated request/response size ceiling; no unbounded
header map or provider blob. Exact field layout and encoding require an ADR
before interoperability code. The implemented choice is binary HOP1 below. Prototype JSON payloads can establish semantics;
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

## Implemented HOP1 integration

[Hopae native contract](https://github.com/ziozzang/hopae/blob/main/docs/HANGANG_NATIVE.md)
and [Hangang pool/console contract](https://github.com/ziozzang/hangang/blob/main/docs/CONSOLE_PLUGINS.md)
now define the implemented HOP1 layout and supersede provisional Hopae framing
choices above. HOP1 has a 16-byte magic/u64-ID/u32-length header and bounded raw
header/result payloads. Caller authentication is per connection and rechecked by
the existing router per request. Real-session parity, cancellation and replay
tests qualify semantics; they do not certify production identity throughput.

## Additional gRPC adapter direction

[ADR 0016](adr/0016-decision-core-metadata-adapters.md) adds gRPC as a proposed
versioned typed transport over existing decision cores. Reused channels, bounded
messages/deadlines, mTLS and native/gRPC semantic parity are required. Kubernetes
API-server webhooks need HTTP/JSON translation; Envoy ext_authz requires a separate
qualified adapter. No gRPC server or plugin is shipped by this design update.

## Qualified native authority observations

The additional gRPC transports are implemented; current ownership and rollout
evidence is tracked in [ADR 0017](adr/0017-shared-server-runtime.md). Pumgye now
has a typed `AuthenticatedResourceAuthorization/Decide` endpoint that shares
Hopae's canonical protobuf receipt context, rather than carrying JSON context
bytes. It queries actual Hopae and Sumunjang owners before returning a zero-TTL
resource decision. The maintained local fixture qualifies the actual Hangang
clients against the three authority processes over persistent mTLS channels,
including identity/network withdrawal and restoration, outage and trust refusal.

Hangang's authority runtime accepts a route-owned resource/method scope, IP,
final request digest and opaque checked service receipt; identity, AAL and network
verdicts are not caller-supplied in this endpoint. Its direct Hopae validation
client rechecks the exact receipt with the owning issuer. Both results are
observations, not signed permission or projection permits. The new typed client
path remains unreleased and is not wired into operating gateway dispatch.

Dispatch integration must bind the final origin-form target after backend URI
composition and the transformed entity, retain route/configuration ownership,
consume service credentials, and refuse stale owners before upstream effects.
Cache hits and retry paths also need the same authorization contract; ordinary
pre-transform auth-proxy verification cannot substitute for final request binding.
Static packaging, the new typed endpoint's Kubernetes qualification and signed
permit/projection/replay gates remain open.
