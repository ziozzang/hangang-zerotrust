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


## External API verifier relay — 2026-10-13

Hopae main includes an opt-in fixed-endpoint API verifier connector. It forwards the presented bearer credential to the configured verifier with service/IP context, validates the response audience, service principal and absolute expiry, and emits service-only AAL 0 evidence. Redirects, environment proxies, URL credentials/query strings and default private-network access are rejected. Response size, timeout and per-profile concurrency are bounded; cancellation and transport/semantic failures feed a process-local circuit. Invalid credentials return 401; verifier faults and open circuits return 503 with no session or local-key fallback.

All-target tests passed (395 library, 15 other integration and 363 scenario cases; 40 explicitly ignored scenarios), along with strict Clippy, formatting, documentation, boundary and scenario mapping checks. Cargo audit found no unaddressed vulnerability; its existing rustls-pemfile unmaintained warning remains. Actual debug and static Hopae/Hangang/Pumgye fixtures verified both local-key and external-verifier flows, scoped rights, revocation/restoration, credential consumption and circuit suppression. The verifier fixture is owned loopback infrastructure, not a production provider qualification or complete throughput benchmark.

The static relay-capable Hopae binary is deployed internally with private consistent backup and image rollback. Existing configuration remains unchanged; live service authorization, native transports, unified module/matrix views, SSO entry and logout isolation passed. The internal service probe still uses the local-key profile. External verifier activation is opt-in. Public multi-platform release, standard introspection adapters, upstream credential exchange, LDAP/local human authentication, database-owned profile publication and full lifecycle/scale qualification remain open. A separate independent adversarial review artifact for this connector is not yet recorded; automated gates alone do not establish completion of the full authentication gateway.


## Durable authentication profiles and console publication — 2026-10-13

Hopae now bootstraps reference-only authentication profiles into its own database once, then loads durable state into revisioned ArcSwap snapshots. Deletion survives restart with the original file present. Publication compiles first, performs revision CAS and administrator fencing inside the transaction and before commit, commits state/audit together and installs the snapshot without await. Dedicated blocking worker permits bound inspection/publication work even after caller cancellation. Secret references and private/verifier credential endpoint bindings require operator declarations. HTTP/HOP1 requests consume a single snapshot; removed bearer profiles cannot downgrade to browser sessions.

Console package 0.1.3 and the static Linux binary are internally deployed. A live Hangang browser inspected the profile and published identical configuration through its signed broker; the profile revision increased while routing revision/configuration and existing grants stayed unchanged. Anonymous denial, logout cleanup, API authentication, role matrix, all module menus, native transports and existing SSO regressions passed. Owned process restart and transactional rollback tests passed. All-target gates passed (400 library, 15 other integration, 365 scenario cases; 40 ignored); the existing unmaintained PEM parser warning remains. Private consistent backups and image/package rollback are retained.

This does not complete upstream credential translation, LDAP/local human authentication, composition, open-stream credential revocation, distributed followers/membership, comprehensive scale or public multi-platform releases. File-oriented preflight/secret-reference migration and persistence of connector circuit state still need work.


## LDAP direct-login source integration — 2026-10-13

Hopae now has TLS-only LDAP credential connectors, separate service/user binds,
immutable text/binary subject namespaces, explicit direct-result provenance,
process-local circuits and bounded password submission admission. Owned OpenLDAP
fixtures pass over LDAPS and mandatory StartTLS, including rejection of upgrade
failure without plaintext bind. Direct providers are represented separately from
OIDC in schema v4, snapshots and registry, and are included in normal/reauthentication
choosers. The portal prepares bound password forms and its POST handler requires
HTTPS, Origin/CSRF, unique bounded fields and attempt admission. Real-store tests
exercise challenge binding, credential failure, AAL 1 session/handoff, replay and
provider-disable/browser-binding refusal. No implicit email/MFA elevation is allowed.

Current all-target gates pass: 421 library, 15 other integration and 366 scenario
cases. One owned LDAP fixture and 40 scenario cases are explicitly ignored in that
run; the directory fixture is qualified separately. The existing unmaintained PEM
parser warning remains. Source changes are on Hopae main, but production LDAP
configuration remains gated and internal deployments still use their prior feature
image/schema. A v4 operational upgrade needs a consistent v3 backup for rollback.

Before LDAP activation, complete real-directory browser/gateway qualification,
hard BER response bounds, connector configuration/epoch fencing at commit, and
account/distributed admission and directory session revocation. Local passwords,
credential translation/composition, memory-session/distributed followers, full-stack
10k/100k throughput and public multi-platform releases also remain open. These source
and test results do not complete the overall zero-trust runtime goal.

## Internal deployment and dogfooding acceptance — 2026-10-13

Internal deployment and dogfooding are required for each completed runtime increment,
in addition to source tests and public publication. Use private consistent backups,
versioned artifacts, migration-aware rollback, and real Hangang request/console checks.
Keep credentials outside public evidence. GitHub Actions remain disabled by operator
choice; qualification and release builds run locally.

The current internal Hangang/Hopae/Pumgye/Sumunjang services were checked again:
HTTPS service authentication, scoped method refusal, guest/invalid/spoofed identity
refusal, removal of upstream credentials, all three management menus, matrix loading,
SSO entry, logout and anonymous/origin isolation, and authenticated native HGD1 passed.
All three user services are active. These checks did not mutate routing or policy.
Hangang runs image `0.3.2-service-api-647c93b`; Hopae runs
`0.0.2-profile-console-9b307c0`. Later LDAP source is not deployed or enabled.

- [ ] Qualify and deploy the next Hopae snapshot with schema-v3 backup and tested
  schema-v4 restore rollback, then repeat service and console regressions.
- [ ] Complete real LDAP browser/gateway and revocation qualification plus hard BER
  bounds and commit fencing before enabling directory authentication internally.
- [ ] Sustain internal dogfooding and record failure/recovery, latency, memory and
  throughput before claiming production completion or public performance targets.

## Required second-factor and extensibility work — 2026-10-13

- [ ] Native TOTP compatible with Google Authenticator: verified enrollment, encrypted
  per-user seeds, recovery/removal, bounded attempts, atomic cross-process counter
  replay protection and clock rollback defense.
- [ ] Service-scoped step-up with browser/user/audience-bound single-use challenges;
  core-owned assurance and session/stream revocation, integrated Hangang management.
- [ ] External authentication/factor API adapters with authenticated bound responses,
  fixed egress, deadlines, circuits and no required-factor bypass.
- [ ] Capability-limited optional Lua extensions with CPU/memory/time limits, approved
  host calls and audited revisioned publication. Scripts cannot mint sessions or AAL.
- [ ] Algorithm/interoperability, lifecycle, concurrency, outage, sandbox and internal
  dogfooding qualification. These are design requirements, not existing MFA support.

The EN/KO contract is recorded in Hopae `docs/AUTH_GATEWAY.md` on main. LDAP nested
BER preflight and malicious TLS peers are qualified in source; internal activation
and full authentication gateway completion remain open.

## TOTP owner schema and deployment follow-up — 2026-10-13

Hopae main now includes schema v5 encrypted enrollment lifecycle and monotonic
counter consumption. Source tests qualify competing independent SQLite writers,
owner/revision refusal and revocation; the portal does not invoke these primitives.
Internal Hopae remains schema v3. The next upgrade/rollback qualification must
cover v3-to-v5 migration and restoration of a consistent v3 backup; image rollback
alone is insufficient. Complete challenge/session atomicity, enrollment/recovery/UI,
key management and real internal MFA dogfooding before marking OTP support complete.

## Actual internal owner migration evidence — 2026-10-13

Offline qualification against a consistent copy of the actual internal Hopae DB
passes v3→v5 migration, integrity and preservation of all 13 existing business tables.
Backup restoration reproduces v3 and original contents. The deployed old image's
isolated `admin list` opens restored v3 and refuses verified v5. WAL-safe SQLite backup
is required for every copy; copying just the main file can silently omit the upgrade.
Tools and EN/KO evidence are on Hopae main (`d876909`). This qualifies offline
migration/CLI rollback, not full application boot or operational deployment.
Production is unchanged. Next: build the candidate image, qualify full boot and existing
service/SSO/console flows, and perform migration-aware rollout with backup restoration.

## Latest internal Hopae rollout — 2026-10-13

Hopae is now deployed internally as `0.0.2-owner-v5-d876909` with actual schema v5.
A parallel candidate and consistent v3 backup preceded the upgrade. Live Hangang
HTTPS service authorization/denial/credential stripping, module menus, independent
Pumgye matrix, SSO entry/logout/origin isolation and native mTLS regressions passed.
Original configuration/provider selection is unchanged; private migration-aware rollback
material is retained. Earlier notes saying internal schema v3 describe prior state.

LDAP remains activation-gated; TOTP primitives/encrypted lifecycle/verification are
present in the image but enrollment/step-up routes are not implemented. The full
authentication gateway, factor/session atomicity, recovery/UI, distributed scaling,
full-stack performance and public multi-platform releases remain mandatory unfinished
work. Dogfooding now runs the latest validated runtime source.

## Initial TOTP portal source integration — 2026-10-13

Hopae main now connects keyring bootstrap, recent owner-session write fencing and
encrypted enrollment to EN/KO portal preparation/confirmation. An actual owned OIDC
process fixture verifies login, setup material, independent OTP calculation, confirmation,
Origin/CSRF/HTTP/anonymous/replay refusal, no seed in logs/refresh and unchanged AAL 1.
Full gates pass (443 library, 15 other integration, 367 scenarios; 41 ignored).
Chromium form testing confirmed same-origin referrer policy is necessary for exact
Origin checks; secrets remain in the creation body, never URLs.

This is initial registration, not OTP sign-in/step-up. QR/mobile scan, full browser UI,
account/distributed admission, recent-auth refresh/cancel/removal/recovery UX, atomic
challenge/session elevation, Hangang navigation and operational MFA rollout remain open.
Current internal image is still owner-v5-d876909 with no keyring/enrollment enabled.

## External second-factor boundary — 2026-10-13

Hopae now has a dedicated external-factor response validator and an English/Korean
[extension design](https://github.com/ziozzang/hopae/blob/main/docs/SECOND_FACTOR_EXTENSIONS.md).
It binds evidence to the server-owned challenge, user, session, exact service/factor,
configuration revision and credential generation; bounds body/time; rejects extra
assurance/permission fields; distinguishes context-valid rejection from malformed
responses. Parsed evidence cannot issue a session or choose AAL. The native core
retains authority over factor independence, replay consumption and final elevation.

Native TOTP enrollment is implemented in source. External MFA API transport,
durable proof/challenge consumption, atomic OTP/session step-up, Lua host functions,
recovery and Hangang navigation remain required implementation work. The existing
service API relay remains AAL 0 and must never be counted as human MFA. Network/IP
conditions constrain authentication but do not alone satisfy a second factor.
Internal image and login policy are unchanged by this source change.

Validation: Hopae serial full gates passed with 828 tests (446 library, 15 other
integration, 367 scenarios), 41 ignored, plus formatting, clippy, boundary, docs,
scenario coverage and dependency audit under the existing scoped advisory policy.
Cross-component contract validation passes six schemas and 21 adversarial/privacy
cases. This is source validation, not an operational external-MFA rollout.

## Atomic native TOTP completion — 2026-10-13

Hopae now implements a native service/owner-storage transaction that verifies a
real TOTP code and atomically consumes a bound `stepup` transaction plus the
revision-fenced counter, records the factor, raises session/portal AAL, advances
credential generation, revokes all prior handles and pending handoffs, and
inserts the new portal handle plus exact-target elevated handoff. Primary
provider authentication time is preserved. Required audit/outbox writes share
the transaction. Native factor actors now also fence stored provider kind/config
changes between authorization and final owner commit.

Tests cover the success state, one concurrent winner and rollback on invalid
code/audit/challenge/target/generation/handle/provider/state/expiry/enrollment.
Browser step-up creation, CSRF/both browser bindings, live application-policy
and publication-epoch checks, recovery/navigation and operational MFA activation
remain mandatory. This primitive is not an enabled browser endpoint. Source
schema remains v5; the internal owner-v5-d876909 image is unchanged.

Validation: full serial Hopae gates pass 831 tests (449 library, 15 other
integration, 367 scenarios), 41 ignored; fmt/clippy/boundary/docs/scenario coverage
and dependency audit pass under the existing scoped advisory policy. Cross-component
contract validation passes six schemas and 21 adversarial/privacy cases.

## Request step-up enforcement — 2026-10-13

Hopae's session request engine now applies configured canonical-path assurance
rules rather than using them only to disable caching. AAL 2 requires actual
second-factor evidence and both session/issued-handle levels; factor freshness
uses the latest satisfaction time. Missing/number-only/OIDC-only, expired/future
OTP and older issued handles are refused. Fresh OTP can satisfy factor freshness
independently of an old primary authentication time. Nonmatching paths retain
ordinary authentication. Browser completion remains unfinished: documents fail
closed with 403 and API/session requests return 401 `step_up_required` without
clearing the handle or minting an unsupported challenge.

The shared HTTP/HOP1 service authentication pipeline also checks the current app
snapshot after credential authentication. AAL 0 API keys/relays cannot satisfy a
matching human assurance rule or authenticate into a disabled/unknown app.
This closes an authentication-profile bypass; it does not replace independent
Pumgye service permission enforcement. HTTP/native parity, uppercase/encoded
prefixes, unchanged nonmatching paths and profile revocation fallback refusal
are covered. Browser step-up bootstrap/completion, live policy publication epoch
fencing and operational MFA activation remain mandatory.

The native admin adapter preserves `aal_insufficient` response/metric/required
audit classification for engine step-up refusal. Prefix matching avoids per-rule
lowercase string allocation while preserving segment/UTF-8 behavior. Full serial
Hopae gates pass 832 tests (449 library, 15 other integration, 368 scenarios),
41 ignored, with formatting/clippy/boundary/docs/scenario coverage and the existing
scoped dependency advisory policy. Contract validation passes six schemas and
21 adversarial/privacy cases. Internal deployment is unchanged.

## Durable portal step-up binding — 2026-10-13

Hopae's native service/owner store now binds a live step-up challenge to the
portal-cookie digest, exact portal handle, same session/current request IP,
credential generation and active TOTP enrollment ID/revision. Application
binding must exist and OAuth/reauthentication metadata must be absent. For
stepup only, the existing pending-identity column carries native context.
Identical live refresh is idempotent; cookie/handle/IP transfer or stale
session/enrollment context cannot replace the binding. Required audit/outbox
failure rolls back binding. Final OTP elevation rechecks portal proof, recorded
context and current actor IP before consuming challenge/counter or issuing
credentials. Real service/SQLite cases cover binding, rollback/retry, transfer,
stale contexts and final-commit refusal.

This remains native service/storage work. Browser challenge creation, portal
page/CSRF, app return-target and publication-epoch fencing, recovery/navigation
and operational MFA activation remain mandatory. No browser step-up route is
enabled and the internally deployed image is unchanged. Source schema remains v5.

Validation: serial Hopae full gates pass 835 tests (452 library, 15 other
integration, 368 scenarios), 41 ignored; formatting, clippy, boundary, docs,
scenario coverage and dependency audit pass under the existing scoped advisory
policy. Cross-component contracts pass six schemas and 21 adversarial/privacy
cases. This is native service/storage qualification, not browser completion.

## Native browser OTP source workflow — 2026-10-13

Hopae now connects configured TOTP keys to capped document step-up, recent
first-factor reauthentication, EN/KO portal setup guidance/code form, distinct
Origin/CSRF binding to transaction+portal cookie+handle, same-user/current-target
validation and atomic proof/challenge consumption, credential rotation and
AAL 2 application handoff. Unenrolled users get setup/continue links; enrollment
alone stays AAL 1. Ordinary login/provider entry refuses step-up transactions.
AAL 1 primary-freshness rules reauthenticate instead of entering an OTP loop.
The native portal always supplies configuration generation, checked against
persisted owner metadata under the writer lock and retained in challenge context.

An owned OIDC/actual-process HTTP browser-client fixture qualifies registration,
unregistered guidance, new OTP, protected AAL 2 access, Origin/cross-purpose/
anonymous/duplicate-query/wrong-entry refusal, old-handle denial and replay.
This is not Chromium/mobile or production-user qualification. Full serial gates
pass 837 tests (453 library, 15 other integration, 369 scenarios), 41 ignored;
formatting/clippy/boundary/docs/scenario coverage and the existing scoped advisory
policy pass. Cross-component contract validation remains six schemas and
21 adversarial/privacy cases.

Recovery/cancel/removal/navigation, account/distributed admission, key lifecycle,
real browser/mobile qualification, external MFA API/Lua connectors and operational
MFA rollout remain mandatory. The internal owner-v5-d876909 image is unchanged;
source schema remains v5. The broader gateway/distribution/performance/release goal
is still incomplete.

## Chromium CSP fix and internal native-MFA rollout — 2026-10-13

Actual Chromium qualification found the self-only form CSP blocked the
post-OTP application handoff despite successful owner completion. Hopae now
adds only the live-validated application origin to the step-up GET form CSP.
The reusable browser tool runs against a private loopback candidate/owner-state
copy, with an owned first-factor session fixture, real browser Origin/cookies/
redirects and native handoff. Corrected static candidate passes enrollment,
step-up/handoff and previous-handle refusal; this is not real Google-user login.
Full serial gates still pass 837 tests, 41 ignored; HTTP and pooled mTLS HOP1
candidate service acceptance/guest/invalid-credential refusal pass.

The internal image is now `0.0.2-native-mfa-791719a` with schema v5 and a private
optional TOTP keyring. Existing providers/service assurance rules are unchanged;
no fixture users/sessions entered production. Live API matrix/denial/credential
stripping, all module menus/Pumgye matrix, SSO/logout/origin isolation and native
mTLS regressions pass. Consistent owner/delegation backups and prior image,
configuration and secret files are retained privately for rollback.

Recovery/key lifecycle/account/fleet admission/navigation, real production-user
MFA, external MFA API/Lua, distributed memory followers, stream revocation,
full-stack 10k/100k performance and public releases remain required unfinished
work. Earlier internal image notes record prior stages; the full goal stays active.

## LDAP credential decoder and dispatch hardening — 2026-10-14

Hopae's credential-only ldap3 fork now gates response semantics before upstream
infallible parsers: message/result/entry/referral/control shape, integer bounds,
UTF-8 and control Boolean lengths. Binary attribute values and the AD outer-OID
workaround remain supported. Each single response is matched to its request
operation; wrong search result kinds become I/O errors. Credential searches
are capped at eight response frames before enqueueing, independent of a server
size-limit hint (512 KiB maximum queued wire payload per operation at the existing
64 KiB frame cap; parser/connection overhead is additional).

Six vendored tests cover valid/malformed downstream parsing and deterministic
wire mutations. The owned directory fixture passes real LDAPS and mandatory
StartTLS plus peers holding connections open after empty/malformed/control/
wrong-operation responses or nine search entries without completion; client
closure and unavailable classification occur within one second. This is not a
complete generic LDAP/control/GSSAPI review. Runtime configuration remains
activation-gated until actual LDAP browser/session/revocation qualification.
The internal native-MFA image is unchanged by this source-only work.

Validation: full serial Hopae gates pass 837 tests, 41 ignored, and the existing
scoped audit policy. The first full run saw one 503 in the owned OTP bootstrap;
the isolated test and complete rerun passed. Failure diagnostics now include only
the public refusal reason. Its cause is not established and the intermittent
condition remains a qualification issue to investigate, not a performance pass.
Cross-component validation passes six schemas and 21 adversarial/privacy cases.

## MFA extensibility requirement — 2026-10-14

Hopae must support Google Authenticator-compatible TOTP and external authentication
API verification, with native lifecycle authority and constrained Lua extensions.
Google Authenticator generates a local TOTP code; Google OIDC authenticates the
first factor and is a separate integration. Native six-digit SHA-1/30-second TOTP
exists. External factor parsing exists, but HTTPS execution, durable single-use
proof consumption and Lua host functions are not enabled yet.

- [ ] Implement configured external HTTPS factor connectors with bounded pools,
  deadlines, admission and per-configuration circuits; no caller-selected endpoint.
- [ ] Consume challenge/proof once in the owner transaction with revision fences,
  session elevation, previous-handle revocation, handoff and audit/outbox together.
- [ ] Embed constrained Lua orchestration with approved host calls and immutable
  configuration snapshots; enforce memory/instruction/time/concurrency limits.
- [ ] Qualify replay, cross-user/service evidence, disable/revision races,
  verifier outage/cancellation and sandbox escapes before operational enablement.

Existing service API relay results at AAL 0 cannot become human MFA evidence.
The implementation contract is Hopae's SECOND_FACTOR_EXTENSIONS document.

## LDAP source activation and owned runtime qualification — 2026-10-14

Hopae now accepts OIDC and typed LDAP providers together in source configuration.
The owned OpenLDAP fixture exercises an actual Hopae process over LDAPS and
mandatory StartTLS: chooser, password form Origin enforcement, failed-password
no-session/no-identity checks, session issuance, application-bound handoff,
password reauthentication, previous-handle refusal and local user disable.
The password form CSP permits only the validated application origin; reauth
records a password factor instead of incorrectly recording an OIDC factor.

Full serial gates pass 837 tests, 42 ignored. The owned LDAP runtime test is
explicitly invoked separately for each TLS mode; it requires its isolated fixture.
This supersedes the source configuration activation rejection in earlier notes.
Actual Chromium LDAP login, external directory-account revocation, secret/CA
publication epochs and distributed lifecycle qualification remain unfinished.
The deployed native-MFA image remains unchanged; no operational LDAP is configured.

## External MFA HTTPS transport implementation — 2026-10-14

Hopae now has a native external-factor HTTPS connector primitive. It binds the
configured factor/revision and exact challenge/user/session/service/generation,
uses an operator credential reference, enforces 1–1000 ms total deadlines and
8 KiB declared/streamed reply limits, and admits 64 exchanges per connector
without waiting. The dedicated pool caps idle connections at 64 per origin
for 30 seconds. HTTP, redirects and environment proxies are refused; private
HTTPS destinations require explicit opt-in, with CA/server-name verification
retained. Resolved verifier secrets and custom CA contents fence connector reuse.

Owned TLS tests exercise accept/reject, actual connection reuse, wrong CA,
context/assurance injection, malformed replies, chunked/header limits while the
server holds the stream open, body timeouts, admission, cancellation, circuit
recovery and clock rollback. Context-valid rejection is healthy; bare HTTP denial
or malformed evidence is a verifier fault. Three faults open a 30-second circuit.

The connector returns parsed evidence only. It is not enabled in portal/provider
configuration, cannot grant assurance, and has no replay cache. Durable proof and
challenge consumption, native owner elevation, runtime snapshot publication,
process-wide admission and constrained Lua host calls remain required. Earlier
notes saying external HTTPS execution is absent now describe historical state;
operational external MFA remains unimplemented. The deployed image is unchanged.

Validation: full serial Hopae gates pass 841 tests, 42 ignored, including the four
owned HTTPS transport tests; fmt/clippy/boundaries/docs/scenario coverage and the
existing scoped dependency audit pass. Cross-component contracts pass six schemas
and 21 adversarial/privacy cases. No public release or operational external MFA
activation is claimed by this source-only step.

## Native external MFA owner completion — 2026-10-14

Hopae's HTTPS connector now returns an opaque, nonserializable transport receipt.
A native service binds the transaction to the actor, portal cookie/handle,
credential generation and published verifier authority before the exchange;
it derives user/session/service from owner state and sends a transaction digest.
The owner rechecks all context and consumes the challenge and hashed proof in
one transaction with AAL 2, credential rotation, old handle/code revocation,
new portal handle/exact-target handoff and required audit/outbox. Native `external`
factor records preserve primary authentication time and count for step-up.
Receipt wall expiry and monotonic deadline are checked before mutation and commit.

Schema v6 adds revisioned approved/disabled authorities, an indexed factor/session
mapping, permanent scoped proof hashes and a guarded capacity counter. Native
publication changes or disable revoke sessions elevated by the affected factor
without scanning every session JSON. Revisions and published global epochs cannot move backward or reuse
changed resolved secret/CA material. Proofs survive owner reopen/session cleanup.
The ledger cap is 1,000,000; full capacity fails closed and no automatic replay
history deletion exists. Safe archival/retirement and capacity telemetry remain.

Actual owned TLS-to-owner tests cover elevation and handoff, concurrent and
cross-session single-use proofs, reopen persistence, authority disable and 24
refusal/rollback cases including user/provider/config changes, cross-context,
application/browser bindings, wall/monotonic expiry, audit and capacity.
Foundation tests refuse missing guard/structure and corrupt counter state.
These are native service/SQLite-owner tests, not browser external MFA or replay
qualification across independent follower databases.

Operational runtime remains schema v5 and the native-MFA image is unchanged.
The v6 source migration requires consistent pre-upgrade owner/delegation backups;
v5 binaries cannot reopen v6 state. Root config/snapshot publication, service
factor selection/enrollment, UI/CSRF/rate controls, process-wide admission, Lua,
fleet performance/lifecycle, public release and deployment remain unfinished.
Earlier notes describing absent durable external completion are historical;
the full integration objective remains active.

Validation: final serial Hopae gates pass 846 tests, 42 ignored, including native
TLS-to-owner completion/persistence/races and v6 foundation qualification. The
legacy event-count/table-catalog expectations were updated for the new required
event and v6 tables. Owned LDAP LDAPS/mandatory-StartTLS runtime qualification
also passes on v6 source. Cross-component validation passes six schemas and 21
adversarial/privacy cases. Public release and operational v6 activation remain open.

## Atomic external MFA registry reconciliation — 2026-10-14

Hopae's immutable registry now publishes its complete approved desired set in one
owner write. A durable publication revision fences stale/concurrent snapshots;
changed individual factor publication advances the same revision. Global config
epoch checks remain separate. Omitted enabled authorities become revisioned
disable tombstones and related elevated sessions/handles/codes are revoked using
the indexed mapping. Repeated omission retains an existing tombstone revision.
Proof hashes and capacity history remain intact.

Owned TLS-to-owner tests cover a single concurrent winner, removal/revocation,
proof retention, a stale snapshot after an individual change, invalid epoch,
late per-factor conflict and final audit failure. Failed publication rolls back
new rows, tombstones, session revocations, audit and the publication revision.
The registry must be activated in memory only after publication succeeds.
Root/portal wiring, Lua, follower propagation and operational release/deploy are
still open; the deployed schema-v5 image is unchanged.

Validation: full serial Hopae gates pass 851 tests, 42 ignored, including registry
and complete-publication tests; fmt/clippy/boundaries/docs/scenario coverage and
the existing scoped dependency audit pass. Cross-component validation passes six
schemas and 21 adversarial/privacy cases. This remains source-only publication
work, with root activation, browser qualification and public deployment pending.

## External MFA startup configuration and activation — 2026-10-14

Hopae now parses `external_verifiers` as a strict reference-only root setting,
validates capacity/duplicates/HTTPS/revision/deadline and requires authenticated
gateway callers. Credentials and CA/client configuration compile before state
creation/migration/listeners. Startup publishes the full desired set under the
current owner epoch and snapshot revision before installing its Services registry.
An empty set reconciles removed authorities on restart. Invalid material and
publication conflicts refuse startup, with redacted material diagnostics.

`factor.registry_published` is a separate required atomic event, preserving the
meaning of application `config.loaded`; 33 event kinds include 28 required and
five diagnostic kinds. Owned real-process qualification proves configured
startup publication and removal/restart disable without remote verifier calls.
Unit tests cover missing material before state creation, duplicates, caller
authentication and secret redaction. This supersedes missing-root-wiring notes.

The browser chooser/response forms, external enrollment, Lua, live reconfiguration
and distributed rollout remain open. TOTP assurance behavior is unchanged; this
setting alone does not enable external browser MFA. Operational schema-v5 image
is unchanged and public release/deployment remain part of the active full goal.

Validation: final serial Hopae gates pass 854 tests, 42 ignored; fmt/clippy,
boundary/docs/scenario checks and the existing scoped audit pass. Startup smoke
now accounts for the separate required registry event. Individual authority
publication uses `factor.authority_published`, keeping `config.loaded` specific
to the application. Cross-component checks pass six schemas and 21 cases.

## Native external MFA browser forms — 2026-10-14

Configured external verifiers now enable native document step-up and appear in
an authenticated owner-context chooser alongside optional TOTP. Selection binds
the approved factor to the challenge. `/stepup/external` has a response form and
POST using a distinct CSRF purpose bound to transaction/portal cookie/handle/
factor, exact Origin and HTTPS, strict four-field input, 4096-byte response cap
and shared IP admission. It cannot select backend URLs or claim user/role/AAL.
Failure does not trigger a weaker-provider fallback.

The adapter verifies before generating replacement credentials; TOTP and external
paths share the issuance helper. Native completion accepts a recent nonfuture
creation timestamp across a second boundary, with matching handle activity/code
creation and existing actor/proof wall/monotonic/pre-commit fences. Verifier
requests include server-owned verification_started_at to bound proof expiry.

The owned OIDC/HTTPS real-process HTTP client test covers first-factor login,
chooser/form, no backend call for Origin/CSRF/additional-field failures, typed
rejection, cross-user/assurance injection refusal, successful elevated handoff,
protected request and old-handle refusal. Timing tests cover boundary/stale/future
issuance. This is not Chromium or an operational organization's account test.
Actual-browser/fleet/performance/deployment, service-specific factor eligibility,
external enrollment/recovery, account admission and Lua remain required work.
Internal v5 is unchanged; historical missing-form notes are superseded in source.

Validation: full serial Hopae gates pass 856 tests, 42 ignored, including the
owned first-factor/HTTPS/form/handoff path and timestamp-boundary qualification.
Fmt/clippy/boundaries/docs/scenario coverage and the existing scoped dependency
audit pass. Cross-component validation passes six schemas and 21 privacy/
adversarial cases. No production external MFA or Chromium qualification is claimed.

## Actual Chromium external MFA and TOTP coexistence — 2026-10-14

The public browser qualifier now accepts an external factor mode with unique
configured loopback HTTPS verifier/candidate-owned CA guards. The default TOTP
mode explicitly selects TOTP when an external chooser appears. On a private
online owner/delegation copy migrated to schema v6, actual Chromium passes
external chooser/form, real HTTPS verifier exchange, AAL-2 cross-origin handoff
and old-handle refusal. The same running candidate passes TOTP enrollment,
selection alongside external MFA, elevated handoff and old-handle refusal.

The qualifier preserves browser Origin/cookies/CSP and distinct Set-Cookie via
CDP mapping of HTTPS browser origins to loopback portal/gateway HTTP. This is
not public-portal TLS or real Google first-factor qualification: first-factor
sessions are owned fixtures on the private copy. The candidate uses a development
binary. Both modes pass again after the external loopback/CA guard was added;
syntax and staged documentation checks pass. Screenshots before sensitive input
and sanitized phase reports are private. Candidate processes stopped and its
copied environment file was removed. No fixture user/session entered production.

Live state remains schema v5 and the existing native-MFA image. Release artifact,
upgrade/rollback qualification, operational/fleet/performance rollout, organization
accounts, service-specific eligibility, enrollment/recovery/account limits and Lua
remain unfinished under the full active goal. Earlier missing-Chromium notes now
describe historical source stages; no production external MFA pass is claimed.

## Static v6 qualification and internal dogfooding deployment — 2026-10-14

The optimized x86_64 musl static-pie release candidate passes Chromium external
MFA/TOTP coexistence, old-handle refusal and HTTP/pooled mTLS HOP1 valid service
acceptance plus guest/bad-credential refusal on a private owner-state copy.
Offline static qualification preserves all old table digests/counts across v5→v6,
restores an identical v5 backup, and the actual old binary refuses v6 without DB
changes and boots restored v5 with matching original private configuration/env.
Explicit expected schema flags reject a no-op qualifier; its input stays v5.

Internal Hopae is now `0.0.2-zerotrust-v6-c776cde`, schema v6. Existing config,
secret files, keys and assurance rules are preserved; no external verifier or
fixture users/sessions entered production. Consistent stopped owner/delegation
v5 backups, original configuration/secret files and old image remain private.
The first deployment stopped at a wrong image-variable preflight assumption and
restored healthy v5 before new-image migration. Corrected HOPAE_TAG preflight
runs before service stop; the second deployment and live API/matrix/credential
stripping/module menus/Pumgye/SSO/logout/origin/native regressions pass. Health
is 200 and the authoritative running image/database confirm v6.

The minimum unrelated config failed the restored authentication-profile check;
matching copied config and environment completed rollback boot qualification.
This is not full-stack 10k/100k throughput, follower/fleet or production-user MFA
qualification. Public signed releases/assets, broader provider/identity gateway
mixing, Lua, enrollment/recovery/account limits, memory followers and existing
stream revocation remain required. Earlier internal-v5 notes are historical and
the complete original goal remains active.

## Authentication extension completion — 2026-10-14

- [x] Native RFC 6238 TOTP compatible with Google Authenticator and equivalent apps; external HTTPS second-factor verification with atomic single-use completion. Source and private candidate qualification exist; production external factors remain unconfigured.
- [ ] Complete operator/user enrollment, reset, recovery and service-specific factor eligibility with audited changes and account-level admission limits.
- [ ] Embed a bounded Lua runtime for approved authentication connector orchestration. Apply this extension contract to first-factor authentication, step-up and service-specific credential translation, not only OTP verification.
- [ ] Keep connector destinations, secret references, TLS policy, factor independence and maximum assurance in native revisioned configuration. Scripts receive minimal typed context and opaque connector references; they cannot assign permissions/AAL or write sessions.
- [ ] Enforce memory/instruction/wall-time/concurrency budgets, cancellation and circuit breaking. Distinguish valid credential rejection from provider failure; neither script failure nor provider outage enables weaker authentication automatically.
- [ ] Test mixed-provider flows, challenge/proof replay, publication during in-flight authentication, sandbox escape attempts, secret leakage and Hangang auth-proxy denial. No OTP/proof decision cache may bypass single-use owner commits.

Pumgye owns authorization decisions; Sumunjang contributes network evidence;
Hopae validates identity and authentication evidence and issues credentials.
Lua support above is required implementation work, not a released capability.

## Hopae 0.0.3 signed staging and internal deployment — 2026-10-14

Annotated `v0.0.3` points to `c56ac4a`; public main includes the later fixture
fix `37dcb46`. A GitHub release draft
holds 11 assets for Linux AMD64/ARM64 and macOS ARM64. Pinned Ed25519 signatures,
tamper rejection, checksums, archive/binary equality and downloaded-asset equality
pass. Linux source gates pass 856 tests with 42 ignored; optimized AMD64 and
QEMU ARM64 candidates pass actual Chromium external/TOTP, HTTP and pooled mTLS
HOP1 parity on private owner-state copies.

macOS ARM64 native tests finish with 848 passing, 8 failing and 42 ignored:
Linux `/proc`/`/dev/full` assumptions, alternate loopback binding, external
verifier fixture readiness and reproducible HTTP connection reset need resolution.
Intel macOS cross-build completes; execution qualification remains unavailable.
Neither macOS qualification nor a stable 0.0.3 release is complete.

Internal Hopae now runs `0.0.3-zerotrust-v6-c56ac4a` with schema v6. Consistent
stopped owner/delegation v6 backups and the previous image are retained;
configuration/keys are preserved. Live service matrix/API/credential stripping,
module menus, Pumgye, SSO/logout/Origin/native regressions pass. Production
external verifiers remain unconfigured. GitHub Actions remain disabled.

The external-verifier readiness failure was traced to Python HTTPServer's
startup `getfqdn()` blocking on macOS. The owned fixture now binds loopback
without DNS; the complete owned OIDC/external HTTPS browser-form scenario
passes on Linux and native macOS ARM64. Other macOS failures remain open;
this fixture-only change does not alter the tagged release binary or deployment.

## Native macOS security qualification recovered — 2026-10-14

Hopae main `cfa106e` makes RSS measurement native on macOS, replaces Linux-only
failed stdout with a closed-peer socket and accepts a reset only after a complete,
unambiguously framed HTTP response. A framing adversarial test retains truncation,
missing-length and conflicting-header failures. Provisioned `127.0.0.2` allows
the same peer-isolation assertions; the temporary alias is removed after the run.
Linux gates and native macOS ARM64 suites each pass 860 tests, 42 ignored, zero
failures. All original eight macOS failures are resolved. Release Rust sources,
dependencies/templates/vendor remain identical to `v0.0.3`; assets/deployment
are unchanged. Intel macOS execution qualification is still pending; the release
remains a draft. Lua and the rest of the full integration goal remain open.

## Embedded Lua eligibility source — 2026-10-14

Hopae main `1341bae` embeds vendored Lua 5.4.9 through mlua 0.12.2 and connects
optional `external_verifiers[].eligibility_lua` to native HTTPS factor verification.
The script sees only owner service/connector/subject identifiers in a fresh VM;
standard libraries, secrets, network/filesystem, session writes and grant/AAL
authority are unavailable. Strict boolean false rejects without upstream calls;
errors fail closed; true still requires transport-authenticated bound proof and
native atomic completion. Limits: source 16 KiB, heap 256 KiB, at most 20,100
instructions, total evaluation five milliseconds and 64 calls per connector.
The script participates in the revisioned authority fingerprint; omitted scripts
preserve existing serialized binding material.

Linux gates pass 863 tests, 42 ignored, including hostile execution, sandbox
capabilities, syntax/startup configuration and real owned HTTPS denial/proof
validation. Source-only qualification does not prove optimized artifacts, macOS
native Lua execution, browser Lua behavior or deployment. Existing 0.0.3 tag,
draft assets and internal image remain unchanged. Full Lua connector orchestration,
first-factor integration, credential translation, service enrollment/recovery,
global/account admission and the remaining distributed/performance goal stay open.
