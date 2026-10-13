# ADR 0012: Independent distributed runtime authorities

Status: required direction; distributed implementation and qualification pending.
Supersedes ADR 0010's embedded-only Pumgye runtime and Hangang-owned policy store.

Hopae, Sumunjang and Pumgye must each be independently deployable servers. Hangang
is the native authentication/enforcement gateway and unified administrative host.
Logical integration does not require a shared process or shared multi-writer DB.

Hopae owns multi-source authentication, lifecycle and credential translation.
Sumunjang owns network/IP evidence. Pumgye owns policy publication, authorization
matrices and decision evaluation. Each authority owns its persistence, revision,
audit and health. Hangang delegates administration through scoped authenticated
contracts rather than owning their business policy schemas.

Remote peers require authenticated TLS (mTLS or equivalent bounded service
identity), fixed endpoint configuration and preserved source/evidence provenance.
Current loopback-only HOP1/HGD1 and the embedded Pumgye core do not by themselves
satisfy this remote-server requirement. Keep codecs/core libraries reusable, but
implement first-class authenticated remote transports and standalone Pumgye.

Decision paths reuse connections, bound queues/concurrency/deadlines, support
batching/pipelining and immutable compiled snapshots. Avoid per-request analytics
writes and unnecessary JSON/database work. Optional authorization caches remain
strictly bounded to 1–5 seconds. Replicas need explicit publication/revocation
leases, minimum accepted revisions and expiry behavior; failed/stale authorities
cannot silently authorize. Circuit breakers and node failover preserve authority,
service/tenant scope and request correlation.

Acceptance: three actual separate processes; remote-authentication and spoof tests;
policy CAS/revocation across replicas; mixed authentication and service-specific
credential rendering; native/HTTP parity; health/admin integration; sustained
10k/100k decision throughput and end-to-end measurements with documented fixtures,
latency, saturation and failure behavior. Standalone microbenchmarks cannot establish
whole-system throughput. Preserve the working integration during migration.
