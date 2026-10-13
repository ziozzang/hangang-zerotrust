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

The independent Pumgye server is running internally with required mTLS, separate decision/management credentials, an empty initial service matrix and policy revision 1. Deployed native PPG1 denied an unassigned service; missing client certificates were rejected. No user/service permissions were granted. Hangang 0.3.2 CLI and OpenAPI checks passed. The local static build passed gateway (10 cases), UDP lifecycle, supervised restart, Lua syscall isolation and the actual Hangang/Pumgye mTLS regression. The binary was signed with the existing pinned key, independently verified with OpenSSL and deployed to the internal gateway together with the updated console. Live HTTPS proved the independent policy/status/audit view, all three menus, existing ID/PW + Hopae SSO entry, anonymous/origin rejection and logout cleanup without configuration mutations. Cross-platform 0.3.2 release publication remains pending. GitHub Actions stays disabled at the owner's request to avoid CI costs.

Replica membership, fleet snapshots and full Hopae authentication-gateway connectors remain implementation work. This deployment does not establish those guarantees or whole-stack 100k QPS.

## Hopae remote transport and internal dogfooding — 2026-10-13

Hopae main includes bounded OIDC-origin circuits and an authenticated remote mTLS HOP1 listener. Hangang main includes explicit-CA/server-name/client-certificate validation, fixed-address persistent HOP1 pools and the same transport for console SSO. The local static binaries exercised actual Hangang/Hopae processes over mTLS: anonymous login redirects, missing-client-certificate rejection, wrong server identity/configuration recovery, spoofed identity isolation and authority-outage 503. This fixture does not exercise a successful external login or establish authenticated throughput. Existing native-session scenarios cover revocation on an established mTLS connection.

Internally deployed the qualified Linux builds and converted all 11 existing Hopae native routes plus console SSO to mTLS with a dedicated Hopae CA. Existing provider configuration, identity mappings, grants and service permissions remain intact. Live HTTPS browser checks passed SSO entry, unified Hopae/Pumgye/Sumunjang menus, role/origin isolation and logout cleanup. A deployment-script null-route failure rolled back successfully before the corrected activation. Consistent SQLite backup and rollback files remain private. This is a feature deployment after the existing releases, not a new cross-platform public release. Hangang Actions remains disabled; integration merges skip CI costs. LDAP/local/API/network connectors, credential translation, remote Sumunjang transport and fleet/session-memory qualification remain open.

## Sumunjang native mTLS internal rollout — 2026-10-13

Sumunjang main prepares version 0.3.4 with a required-client-certificate HGD1 remote listener, scoped collector authentication, ALPN, bounded handshakes/lifetime and a total partial-frame deadline. Hangang main adds fixed-address explicit-CA/name/client-certificate validation in its persistent Guard pool. The actual two-process qualification passed allow, immediate manual IP deny/removal, wrong-name failure/recovery and outage fail-closed with the locally built binaries. Workspace tests, strict Clippy and Hangang library/console/CLI tests passed.

Internally installed the pinned-signature/hash-verified Sumunjang 0.3.4 GNU and Hangang static binaries, with a dedicated Sumunjang CA and mTLS native query connection. Existing observe policy, collector/admin credentials and provider/user/service assignments remain unchanged. Live HTTPS verified all three menus, Pumgye lookup, Hopae SSO entry and logout; the deployed HGD1 handshake/query passed with certificate/name validation, and missing client certificates were rejected. Consistent database backup and rollback material remain private.

Public cross-platform 0.3.4 assets are not published yet. The supervised updater is enabled and currently rejects the older public 0.3.3 release rather than downgrading the internally installed 0.3.4 binary. Full authentication connector/translation/lifecycle and end-to-end scale qualification remain open; native transport tests are not proof of full-stack 100k QPS.

## Service API authorization and internal dogfooding — 2026-10-13

Hopae main now authenticates service-scoped API credentials with compiled in-memory SHA-256 indexes and IPv4/IPv6 prefix trees; the environment reference, realm, host/port audience and bounded expiry are configured explicitly. A missing credential may use the existing session engine only when enabled; a presented invalid credential never downgrades to a valid browser session. Service identities remain separate from human identities and carry AAL 0 plus an authenticated service audience. Hangang main requires an enforced Pumgye gate, exact audience, explicit subject rights, method/class/network eligibility and an explicitly allowed AAL 0 role. Credentials are consumed before policy/transforms and stripped again before upstream dispatch.

The owned three-process fixture passed with actual debug and locally built static binaries over mTLS HOP1/PPG1, including durable rights revocation/restoration, guest denial, network/class/human-assurance rejection, service audience isolation and Pumgye-outage failure. Guard is not included in that fixture. Qualified builds are deployed internally with one new generated service-only probe credential and a read-only Pumgye grant, preserving prior identities/services/grants. Native TLS ingress checks passed real service authentication, unknown/invalid/spoofed-identity/method denial and no upstream Authorization credential. Browser verification passed the populated service matrix, unified module menus, existing SSO and logout cleanup.

The internal probe requires an explicit named HTTPS listener scope. Its network policy allows the designated private network and loopback; public DNS hairpin traffic outside that policy is deliberately denied. Consistent backups, credentials and the reusable private check remain outside public repositories. This deployment is not a new public cross-platform release. File-owned API profiles still require restart for changes; database publication, management, credential rotation/translation, streaming credential revocation, LDAP/local passwords/remote API relay and complete scale qualification remain open.
