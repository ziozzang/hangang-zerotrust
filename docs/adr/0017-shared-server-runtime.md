# ADR 0017: Shared server runtime, independent domain cores

[한국어](../ko/0017-shared-server-runtime.md)

Status: accepted boundary; initial shared gRPC transport implemented in
[hangang-runtime](https://github.com/ziozzang/hangang-runtime), revision
81352ef. Pumgye (878bd2a) and Sumunjang (65856ab) have adopted this transport
and passed local process qualification. Hopae (e1aead3) also adopts the runtime
for its additional gRPC verification endpoint. All three additional gRPC gateway clients are now implemented and locally qualified.
Full request-chain, Kubernetes and production adoption remain open. This does not complete the integrated package.

Share server infrastructure rather than independently reproducing transport and
lifecycle behavior in every module. Keep provider/session ownership in Hopae,
authorization metadata in Pumgye, network policy in Sumunjang, and routing/enforcement
in Hangang. Their pure decision cores must not depend on HTTP or gRPC.

The initial library owns bounded TLS file loading, mandatory client certificates,
connection admission, TCP_NODELAY, gRPC stream/header bounds and request timeout.
Domain handlers own credential roles, message limits, global admission and decision
semantics. They query their existing in-memory snapshots without request-time SQL.
The current request timeout does not preempt blocking domain work; handlers must
remain bounded and cooperative.

Future shared facilities include native connection handling, shutdown/drain,
supervision and inherited listeners, health/telemetry hooks, and background snapshot
publication primitives. Domain persistence transactions, provider I/O, policy
compilation and source freshness rules remain domain owned. Generic infrastructure
must not silently authorize on missing data or stale snapshots.

Use pinned revisions across repositories, qualify each consumer independently and
keep independently scalable server processes. Transport parity, supervisor listener
handover and actual Kubernetes tests are adoption gates, not consequences of code
reuse. No shared multi-writer business schema is introduced.

## Local qualification evidence

Pumgye: 17 server tests, strict workspace Clippy, actual gRPC/native mTLS requests,
credential isolation, bounded decoding and immediate policy revocation.
Sumunjang: 35 distinct server tests (also run through its compatibility binary),
strict workspace Clippy, actual gRPC/native mTLS parity, malformed and oversized
input rejection, revision fence, same-channel policy changes and supervised HUP
listener handover. Signed updater regression also passed upgrade, policy retention,
readiness rollback, tamper rejection and cancellation. These are local owned fixtures;
they do not prove actual Kubernetes gRPC deployment or production rollout.

Hopae e1aead3: actual mTLS gRPC calls through the existing authentication pipeline
qualified authenticated session allow, HTTP status/reason parity, immediate session
termination on the same channel, wrong/duplicate caller credentials, injected credential
headers and client-certificate refusal. Configuration tests cover mandatory mTLS,
caller authentication and distinct listeners. Full all-features tests: 914 passed,
42 existing environment-dependent cases ignored; strict all-target/all-feature Clippy
and EN/KO documentation checks passed. The administrator status reports the bound
gRPC address. Container build inputs now include protoc, schema and vendored LDAP;
that container build and actual Kubernetes rollout are not yet qualified.

Hangang 59e531d adds an optional Pumgye gRPC decision client selected by
`pumgye_authority.transport=grpc` (native remains default). The actual owning-server
fixture proves mTLS calls, administrator-role refusal, server-name mismatch refusal,
guest/all-permission denial, same-channel policy revocation and monotonic revision
fencing. Seven focused authority/response tests, 34 configuration tests, strict
all-target Clippy and documentation/publication checks passed. Global admission,
whole-batch deadline, decoding limits and coherent batch revisions are enforced.
At that stage, Hopae/Sumunjang gRPC clients and full actual gateway request-chain qualification,
credential/channel lifecycle qualification and Kubernetes/production adoption remain
open; this is not proof of complete gRPC application proxy support.

Hangang 42cc000 adds the Sumunjang gRPC client, selected by
`--guard-decision-grpc` at the configured decision address with mandatory mTLS.
Owned actual-server qualification (Sumunjang tool 83092e6) proves enforced
allow/deny, same-channel block removal/restoration, administrator-role refusal,
server-name mismatch, no HTTP fallback and cancellation, alongside native parity
and supervised listener handover. Twenty-two guard tests passed (one existing
ignored), plus strict Clippy and documentation/publication checks. Admission and
fresh mandatory authorization evidence now share a monotonic observed revision,
preventing stale replies from rolling back newer evidence across HTTP signals and
native/gRPC queries. Optional admission still follows its configured failure policy;
mandatory Pumgye network evidence is unavailable on failure. At that stage, Hopae client adoption,
full gateway request-chain and Kubernetes/production rollout remain unqualified.

Hangang 0125779 adds the Hopae gRPC client through a provider-independent pinned
`hopae-grpc` crate (Hopae contract extraction 7b5a8b8). Hopae scenario 9469182 invokes
the actual gateway client against its owned session engine: authenticated allow,
wrong caller key, server-name mismatch and same-channel session termination passed.
Five client tests, 34 configuration tests, an actual HOP1 proxy regression, strict
all-target Clippy and EN/KO documentation/publication checks passed. Existing
verification status, repeated cookies, identity and terminal response handling are
reused, with no HTTP/native fallback or decision caching. Console SSO still uses
HOP1. Full actual gateway chain, channel/credential lifecycle, Kubernetes and
production rollout remain unqualified; the overall goal remains incomplete.

## Actual four-process request-chain qualification

Hopae tool 6107b4c qualifies actual Hangang, Hopae, Sumunjang and Pumgye processes
through an HTTPS protected application route, over both mTLS HOP1/PPG1/HGD1 and
all-three gRPC decision exchanges. Scope: native API-key or external API relay
service identities, network evidence, service/IP/class/method permissions,
guest/invalid credential denial, audience isolation, credential consumption,
permission revocation/restoration, network block changes and authority outages.
Every refused request must leave the actual application backend call count unchanged.
Sumunjang outage/reconnection and Pumgye restart are exercised; revoked permissions
cannot be resurrected by unchanged bootstrap grants. The gRPC durable-restart case
also confirms Hopae profile tombstones survive actual restart. External verifier
variants for both transports prove an open circuit suppresses additional calls.
The existing three-process fixture also passed as a compatibility regression.

This closes the selected local API-service request-chain gate, not all identity
flows, all stream modes, generic metadata adapters, actual Kubernetes deployment,
production release/rollout or fleet performance. Console/UI and Kubernetes package
qualification remain separate work. No benchmark was run in this functional phase.

## Shared management TLS and console delegation

Runtime 039166b (0.1.1) adds the common mandatory-client-certificate TLS parser and
a bounded HTTP/1.1 HTTPS management lifecycle. Sumunjang 7851660 adds
`--management-tls` using its decision identity/CA, preserving collector/admin roles
and supervised listener handover. Pumgye 6708e1d and Hopae 6411523 reuse the same
parser for their existing transports; domain handlers and Pumgye peer audit identity
remain owned by their modules. Qualified: Sumunjang 35 tests and actual HTTPS/gRPC
fixture including role/certificate refusal and HUP; Pumgye 17 tests plus actual
HTTP/PPG1/gRPC revocation/recovery fixture; Hopae 14 native scenarios (one existing
ignored). Strict Clippy passed for each consumer.

Hangang 8c1c78d adds per-plugin mTLS identities/private CA roots, fixed DNS/SNI
validation and independent client pools. Six plugin tests, strict Clippy and an
actual Hangang console API -> independent Sumunjang HTTPS read/mutation fixture
passed. Assets remain digest pinned, operations audited and TLS paths/credentials
excluded from browser discovery. These latest management changes have not yet
been deployed/qualified in Kubernetes or production, and the full browser/provider
administrator suite remains open.

Hopae ee94562 adds optional `listen.admin_tls` through shared bounded HTTPS.
Runtime ba1a06c preserves actual TCP ConnectInfo and injects authenticated TLS peer
evidence only after a client certificate is present on the accepted TLS connection.
Hopae signed delegation accepts loopback or that server-provided evidence; HTTP
headers cannot forge it, and existing signatures/session/grant/assurance checks
remain required. Actual local mTLS tests qualify certificate refusal, native login
denial and shutdown; configuration and transport-forgery tests plus existing signed
actor scenarios pass. Full all-features tests: 917 passed, 42 existing cases ignored;
strict Clippy/documentation/publication checks passed. Remote delegated mTLS in
Kubernetes, Hopae browser management and federated console SSO are not yet qualified.

## Common engine boundary and extraction order

The common server engine is `hangang-runtime`, consumed as a library by separate
server binaries. Hangang remains the routing/enforcement gateway; the runtime is
not a fifth policy authority or a requirement to colocate the four servers.

| Layer | Owner | Sharing boundary |
| --- | --- | --- |
| Transport and process infrastructure | hangang-runtime | TLS, connection/stream admission, deadlines, cancellation, draining and listener lifecycle |
| Protocol contracts | Each domain's contract crate | Versioned codecs and typed messages; transport does not interpret allow/deny |
| Authentication | Hopae | Providers, credential translation, sessions, MFA and authentication circuits |
| Network evidence | Sumunjang | IP indexes, GeoIP, scoring, rules and network revision semantics |
| Authorization | Pumgye | Resource/action metadata, grants and authorization decisions |
| Routing and enforcement | Hangang | Request context, decision composition and upstream dispatch |

Common snapshot infrastructure may eventually provide atomic publication, generation
tracking and notification. Each domain still owns validation, DB transactions,
source leases, revocation and persistence. A common snapshot container must not
imply common policy schemas or a shared multi-writer database. Separate processes
retain independent quotas, failure isolation and horizontal scaling.

Extract in small stages: retain the qualified TLS/gRPC/management HTTPS base; next
compare the existing native accept loops and extract only equivalent connection,
cancellation and drain behavior behind domain-owned codecs. Then qualify inherited
listeners/supervision and reusable health/metrics hooks. Do not force Hangang's
application proxy into the decision-server request model. Configured limits remain
explicit per listener; generic defaults are not performance qualification.

For every extraction, retain real native/gRPC parity, malformed-input and role
refusal, same-channel revocation, restart persistence and outage refusal checks.
Run the owning consumers and actual Kubernetes request chain before rollout.
The selected four-process chain and Kubernetes console paths have passed separate
qualification; native lifecycle extraction, all provider flows and production
adoption remain open. See the current
[Kubernetes qualification record](../KUBERNETES_WORLD_QUALIFICATION.md) for scope.
