# Implementation backlog

[Roadmap](docs/ROADMAP.md) · [한국어](TODO.ko.md)

## Main integration
- [x] Guard menu package and native host broker using the existing Hangang authority; deployed console activation tracked below.
- [x] Qualify trusted plugin lifecycle, backend credential isolation, roles, revocation and audit.
- [x] Scoped Hopae delegated-management contract preserving grants/CSRF and actor identity.
- [x] Hopae user/session/event/status package, native style and host authentication with independent native Hopae grant/session checks.
- [x] HOP1 provider-independent native verify contract and real-session HTTP parity cases.
- [x] Authenticated bounded Hopae transport and Hangang persistent pool.
- [x] Native entry routing/result support for existing Hopae login/logout without required Lua scripts.
- [x] Qualified component releases: signed Hangang/Guard assets and checksummed Hopae assets.

- [x] Unified Hangang-authority Hopae console and explicitly mapped native SSO login ([ADR 0009](docs/adr/0009-console-authority-sso.md)).

## Design subtask
- [x] Architecture/ownership diagrams and English/Korean design documents.
- [x] Catalog, classification, integrated decision and exporter proposals.
- [ ] Owner review of class vocabulary, tenant/object evidence and downgrade workflow.
- [ ] Decide native protocol layout, exact delegation semantics and revocation guarantees.
- [ ] Classifier and integrated policy implementation/qualification.
- [ ] Exporter implementation, ClickHouse schemas, Prometheus and privacy/failure tests.
- [ ] Device/workload evidence ADR after environmental investigation.

Runtime implementation checkboxes require actual evidence, not design completion.

## Ontology and automated security hardening
- [x] Record Sillok/Jikji component selection and remediation design.
- [ ] Versioned bounded Sillok ontology adapter with provenance/tenant isolation.
- [ ] Jikji automation and semi-automation tool/approval integration.
- [ ] Scoped pentest job and normalized finding contracts.
- [ ] Guard mitigation and Hangang routing patch adapters with CAS/idempotency.
- [ ] Durable recovery, canary verification and conflict-safe rollback.
- [ ] Adversarial qualification and request-performance isolation.

## Observability / ontology / pentest feedback
- [x] Record the full observation-to-action-to-verification loop in English/Korean.
- [ ] Correlate bounded logs/traces/metrics and scoped pentest findings with provenance.
- [ ] Sillok fact/hypothesis/policy/applied-state/outcome distinctions and retraction.
- [ ] Jikji case lifecycle, evidence retrieval and bounded outcome reuse.
- [ ] Post-change pentest and normal-traffic regression checks with predeclared criteria.
- [ ] Feedback amplification, misleading success and cross-tenant adversarial tests.

- [x] Select Hearim as one intelligence/judgment backend and update diagrams.
- [ ] Bounded Jikji/Hearim adapter, provenance, error handling and calibration qualification.

## Integration evidence — 2026-10-12

Merged [Hangang #1](https://github.com/ziozzang/hangang/pull/1),
[Hopae #1](https://github.com/ziozzang/hopae/pull/1), and
[Guard #1](https://github.com/ziozzang/sumunjang/pull/1).

- Hangang: 1,229 all-target Rust tests passed (58 explicit ignores), plus new native proxy parity and signed assertion tests; strict Clippy and browser lifecycle/role tests passed.
- Hopae: 384 unit + 358 scenario tests passed (40 explicit ignores), 39 gateway cases passed; real provider/session/grant/delegation tests and strict Clippy passed.
- Guard: workspace and packaging tests passed; console generation reproduced the same manifest digest.
- Actual isolated console + Guard runtime and a signed Hopae fixture exercised both menus, target IDs, viewer denial, secret isolation and logout disposal.
- [x] Activate merged binaries/packages in the deployed console; live HTTPS menus, anonymous denial, native entry redirects, logout disposal and Guard signed update status verified.
- [x] Complete native platform qualification and publication: Hangang (5 targets), Guard (4), Hopae (4).

Published and deployed on 2026-10-13: [Hangang v0.3.1](https://github.com/ziozzang/hangang/releases/tag/v0.3.1), [Guard v0.3.1](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.1), [Hopae v0.0.2](https://github.com/ziozzang/hopae/releases/tag/v0.0.2). Hangang/Guard runtime signatures were verified before deployment; Hopae checksums were verified. Guard supervised signed updates are enabled. Hopae has no signed automatic updater.

- [ ] Measure end-to-end Hopae session throughput; transport qualification alone does not establish 100k QPS.

## Unified console / SSO evidence — 2026-10-13

Merged [Hangang #4](https://github.com/ziozzang/hangang/pull/4) and
[Hopae #2](https://github.com/ziozzang/hopae/pull/2). Deployed reviewed Linux
builds from these source trees and frozen Hopae console UI 0.1.2; this is a
post-release feature deployment, not a new signed cross-platform release.
The sole existing Hopae administrator is explicitly mapped to the sole existing
enabled Hangang administrator; no account/grant is created or altered.

- 89 Hangang admin API tests, private lease/native SSO tests and real Hangang broker smoke passed.
- Hopae: 384 unit tests and 359 scenarios passed (40 explicit ignores); unified/native authority regression, expiry, nonce replay and audit passed.
- Strict all-target Clippy and publication/boundary/documentation checks passed.
- Browser SSO placement, callback, viewer role/restoration and plugin role tests passed.
- Live HTTPS checks: ID/PW + SSO entry, Hangang-only Hopae status/users, secondary-login removal, logout cleanup, anonymous/origin/cookie/lease isolation and native provider entry redirect.
- Real Google login still requires the operator's provider interaction; automated login qualification uses the owned mock provider/session fixtures.

## Pumgye / Sumunjang integration

- [x] Component names and ownership accepted ([ADR 0010](docs/adr/0010-pumgye-ownership.md)).
- [x] Bounded embedded Pumgye policy compiler and adversarial tests.
- [x] Native Hangang policy publication, audit and console authorization matrix.
- [x] Protected-route Hopae identity + user/IP permissions + Sumunjang enforcement.
- [x] Cache, revocation, transport and browser qualification; reviewed deployment.
- [x] Record Jangbu / existing Sacho / Sillok as separate design responsibilities.

- [x] Record Saheon as the separate audit-system owner; runtime integration remains planned.

## Sumunjang executable transition

- [x] Primary `sumunjang` executable / version identity, legacy executable and signed asset compatibility.
- [x] Workspace / packaging / strict Clippy / real signed upgrade and rollback qualification.
- [x] Signature-verified Linux deployment and unified-console / SSO regression checks.
- [x] Four native platforms, public v0.3.2 release and live GitHub updater confirmation.

## Hopae authentication gateway

- [x] Record multi-source authentication / network evidence direction (ADR 0011).
- [ ] Common principal/evidence and connector contract; preserve multiple OIDC providers.
- [ ] LDAP and API auth relay adapters with bounded credential translation.
- [ ] Any/all/step-up composition, network principals and Pumgye kind constraints.
- [ ] Native/HTTP parity, unified management, failure/revocation/security qualification and deployment.

## Independent distributed runtimes

- [x] Required independent Hopae / Sumunjang / Pumgye ownership (ADR 0012).
- [ ] Standalone Pumgye authority, persistence/CAS and decision server.
- [ ] Authenticated remote HOP1/HGD1/Pumgye transport and scoped admin delegation.
- [ ] Replica revision/expiry/revocation and breaker/failover qualification.
- [ ] Three-process native integration and sustained/end-to-end throughput evidence.

### Sumunjang repository migration qualification (2026-10-13)

- [x] Public canonical repository: [ziozzang/sumunjang](https://github.com/ziozzang/sumunjang); Git remote, Hangang/Pumgye dependencies and documentation use that address.
- [x] [v0.3.3](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.3): four native targets qualified in [CI](https://github.com/ziozzang/sumunjang/actions/runs/38326599970); 22 published asset digests match staged bytes, with eight independently verified Ed25519 manifests.
- [x] Historical v0.3.2 manifest and binary downloaded from the moved repository retain the authentic old signed URL and match the pinned key, size and hash. Tests reject other repositories, tags and filenames.
- [x] Published Linux binary signature verified before installation; supervised canonical-repository updater reports enabled/up_to_date at v0.3.3; unified console and authenticated HGD1 regression checks pass.

Binaries through v0.3.2 require a one-time signature-verified v0.3.3 bootstrap because their pinned old GitHub API rejects redirects. See [migration guidance](https://github.com/ziozzang/sumunjang/blob/main/docs/UPDATES.md). This qualification does not complete the authentication-gateway or independent remote-runtime work above.

## Snapshot backbone and scale-out membership

- [x] Record memory-snapshot / domain DB-backbone / join-drain-remove contracts and Hangang subscriber duties (ADR 0013).
- [ ] Authenticated snapshot/outbox adapters for Hopae, Sumunjang and Pumgye; protected verification indexes and session/token revocation.
- [ ] Leased membership authority and Hangang watch/resync, bounded endpoint pools, incarnation/revision fencing and drain handling.
- [ ] Actual replica churn, partitions, lost notifications, stale proofs, session/network/role revocation and sustained end-to-end scale-out qualification.

## Independent Pumgye qualification and internal deployment — 2026-10-13

[Pumgye #1](https://github.com/ziozzang/pumgye/pull/1) separates the pure authorization core, bounded PPG1 codec, persistent mTLS client and independently owned SQLite-backed authority server. [Pumgye #2](https://github.com/ziozzang/pumgye/pull/2) adds the owned two-process Hangang qualification. [Hangang #7](https://github.com/ziozzang/hangang/pull/7) is merged: native remote decisions, owner-delegated policy/status/audit, authority-scope CAS, and stream retirement on policy changes or authority outage. The regression uses actual Hangang/Pumgye processes; Hopae and Sumunjang evidence sources in that regression are owned protocol fixtures, not full component processes.

The independent Pumgye server is running internally with required mTLS, separate decision/management credentials, an empty initial service matrix and policy revision 1. Deployed native PPG1 denied an unassigned service; missing client certificates were rejected. No user/service permissions were granted. Hangang 0.3.2 CLI and OpenAPI checks passed; its local static release build and gateway/console activation are still pending. GitHub Actions stays disabled at the owner's request to avoid CI costs.

Replica membership, fleet snapshots and full Hopae authentication-gateway connectors remain implementation work. This deployment does not establish those guarantees or whole-stack 100k QPS.
