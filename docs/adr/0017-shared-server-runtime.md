# ADR 0017: Shared server runtime, independent domain cores

[한국어](../ko/0017-shared-server-runtime.md)

Status: accepted boundary; initial shared gRPC transport implemented in
[hangang-runtime](https://github.com/ziozzang/hangang-runtime), revision
81352ef. Pumgye and Sumunjang integration is being qualified; Hopae and Hangang
adoption remain open. This does not complete the integrated package.

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
