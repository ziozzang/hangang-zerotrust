# ADR 0017: Shared server runtime, independent domain cores

[한국어](../ko/0017-shared-server-runtime.md)

Status: accepted boundary; initial shared gRPC transport implemented in
[hangang-runtime](https://github.com/ziozzang/hangang-runtime), revision
81352ef. Pumgye (878bd2a) and Sumunjang (65856ab) have adopted this transport
and passed local process qualification. Hopae (e1aead3) also adopts the runtime
for its additional gRPC verification endpoint. Hangang client adoption remains open. This does not complete the integrated package.

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
Hopae/Sumunjang gRPC clients, full actual gateway request-chain qualification,
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
mandatory Pumgye network evidence is unavailable on failure. Hopae client adoption,
full gateway request-chain and Kubernetes/production rollout remain unqualified.
