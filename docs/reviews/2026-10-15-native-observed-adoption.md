# Native observed consumer adoption

Status: implemented native consumers with final local signed-artifact qualification;
independent-host Kubernetes qualification is in progress. Current source: Hangang
`97419f3`, Hopae `bc5b2a4`, Pumgye runtime `4724962` (packaging `d207266`),
and subsequent Sumunjang `7bfd6c1`.
[한국어](../ko/2026-10-15-native-observed-adoption.md)

## Implementation update

The stable-policy/digest SDK is now implemented in Hopae `c7ddcf2` and the separate
Pumgye observed authentication adapter in `97bf852`. The adapter uses borrowed
ArcSwap generation checks, retires before publication, runs external callbacks
outside native guards and checks BOOTTIME after callbacks. Its 78-test feature
workspace, strict Clippy and default locked check pass. This is evidence-library
integration; no observed authorization endpoint or permit signing is activated.
The original next-boundary analysis below records why those interfaces exist.
Continue the ordered sequence from separate Pumgye prerequisite/permit clocks,
paired replay and output, followed by actual final enforcement qualification.

## Output-budget SDK and native integration in progress

Hopae SDK `e01c67e` adds `ClockRates::remaining_admission_until` and a read-only
observation registry generation accessor. The helper charges the complete RPC
against a before-send receiver anchor, accounts for independent quantization and
explicit oscillator bounds, rejects discontinuities/overflow, and returns only a
numeric lower expiry. It supplies neither authenticated evidence nor replay
retention. Native-client and default SDK suites and strict all-target/all-feature
Clippy pass. Runtime `bf3ba2c` adds a single-read, retirement-aware BOOTTIME tick
sample; its 35 tests, strict Clippy and musl library check pass.

Pumgye protocol `6b2b781` and Hopae protocol `4ffd3c5` expose separate observed
permit and output envelopes. Actual native authority, paired durable replay and
Hangang final dispatch implementations are being integrated and tested. These
protocol/SDK commits do not establish successful four-process, independent-host,
Kubernetes, browser, signed-release or operating deployment qualification.

## Original next code boundary

The exact-pin SDK is a tested foundation, but neither production consumer can
use it directly. Pumgye receives an authenticated final-request digest, not HTTP
method/path/body bytes. Hangang already hashes its materialized final entity once.
Both handle dynamic verified service identities, while the exact client pins a
subject, profile/application generation and random source-process domain.
Creating a client from incoming context per request would promote input into trust
and discard connection reuse and lifecycle ownership.

Add a distinct server-compiled stable service trust policy and digest preparation
API while preserving exact mode. The persistent native client owns issuer/key/base
identity, allowed service/audience, revision floors, TLS endpoint, rates and its
private lifecycle seal. An issue intent binds the native final digest and headers.
An observation query freezes the supplied context only after structural/policy
checks and equality with the authenticated enforcement caller's expected digest.
Preparation grants nothing. Signature verification and the current fixed-owner
RPC must both succeed before creating private time evidence; reuse verified
immutable evidence rather than verifying it again in Pumgye.

## Process domains and local ownership

Operators configure stable trust, not random process domains. For a new operation,
learn the domain from the signed context and require the authenticated current-owner
report to match it exactly. New-process proofs can then work without configuration
edits; the owner refuses old-process proofs. Refresh never migrates a proof between
domains. This does not solve endpoint discovery or arbitrary replica balancing.
Do not infer replay-record deletion authority from seeing a new domain or refusal.

Use native owner/configuration-scoped registry floors; a single profile counter
must not conflate unrelated service identities. Capture one immutable trust/client
generation across awaits, retire it before replacement and recheck its active Arc
identity immediately before native authorization/signing/output. Point-in-time
observations remain distinct from revocation leases.

## Ordered implementation and acceptance

1. Add stable-policy/digest SDK support. Test multiple signed subjects and domains
   on one persistent client, fixed trust/scope/floor refusals, restart without
   operator edits, nonmigrating refresh, fresh IDs and retirement/cancellation.
2. Add a separate Pumgye observed authentication wrapper. It consumes verified
   identity and local time evidence without fake UTC or conversion to the old
   strict checked type. Keep permit issuance disabled for this branch initially.
3. Move prerequisites into Pumgye's local receiver domain, intersect remaining
   budgets, then sign permits in Pumgye's separate progressing source domain.
   Authentication lineage is not a permit clock. Add observed permit envelopes.
4. Change Hopae paired durable replay and final output together. Preserve atomic
   nonce reservation, registry checks, secret resolution, final fences and commit.
   Version strict/observed rows; clean observed records by receiver retention,
   never source expiry or receiver wall time. Define receiver restart explicitly.
5. Add observed output envelopes and Hangang conversion/final dispatch fences.
   Authentication, permit, output and receiver clocks remain distinct. Qualify
   independent offsets, asymmetric delays, suspend, races, cancellation, lost
   replies, restart/restore and actual final backend effects.

These stages precede signed rebuild, actual four-Pod Kubernetes/browser and
operating adoption. Existing strict paths remain separate throughout migration.

## Actual four-process functional result

Pumgye native authority `080e304` and Hopae native replay/projection `274a661`
are published. Hopae `bc5b2a4` adds the repeatable observed four-process smoke.
An actual Hangang/Hopae/Pumgye/Sumunjang run over mTLS gRPC passed final credential
transformation, exact final path/body, wrong issuer/key/audience refusal without
backend effects, wrong route/plan peer or caller refusal, guest/network/permission
isolation, durable policy and identity revocation across real restarts, receiver
key retirement and configuration recovery. This used a development Hangang binary
before its final transport-fence changes; it is not final artifact qualification.

The first run found a real Hopae configuration-loader allowlist omission; the fix
and actual file-loader regression are included in the published native commit.
Further independent Sol review identified two Hangang boundaries still being
corrected: proof expiry during asynchronous backend connection/write, and the
route-reference source's original suspend-inclusive lifetime. A timeout around
Hyper alone cannot fence detached writes; a source lifetime measured only by
Instant cannot be repaired by a remote BOOTTIME conversion. Final native transport,
independent-host, restore/clone, Kubernetes/browser and signed release gates remain
open. No throughput or operating-adoption claim follows from this functional run.

## Final native source and signed local qualification

Hangang `97419f3` fences actual backend transport writes below TLS, including
vectored writes, flush and shutdown, with irreversible refusal. Observed requests
disable canceled-request retry. Original route lifetime uses suspend-inclusive
BOOTTIME; native owner/configuration retirement is checked at the actual transport.
The complete workspace passed 1,309 tests (58 ignored), strict Clippy and focused
late transport/route tests. A delayed real TLS connection emitted zero HTTP bytes
after expiry or route retirement. Already accepted kernel bytes cannot be recalled.

Pumgye `4724962` applies the same BOOTTIME source lifetime to every Kubernetes
decision path and readiness/status. Each authenticated completed source capture
seals its lifetime once; rereading cannot renew it. Failed/backward clocks latch
refusal, and delayed concurrent reads cannot spuriously retire a healthy source.
Default 68 and observed-feature 73 tests plus strict Clippy pass.

All eight Hangang executables and the Hopae/Pumgye native servers were rebuilt as
static musl binaries. Pinned Ed25519 manifests, exact sizes/SHA-256, archive contents
and absence of ELF interpreter were independently verified. The exact signed three
new candidates plus retained published Sumunjang 0.3.5 passed the real four-process
observed chain. A separate final-source run also passed external authentication API
relay and circuit breaking. Final Hangang browser regression and local console SSO
smoke pass; the latter uses a fixture identity peer and does not establish provider
login qualification. Release publication and operating adoption remain separate.

The final exact-candidate K3s run completed successfully: actual four-Pod final
credential output, independent management-host SDK issue/observation/consuming
refresh, real browser administrator bootstrap/login/module menus, profile CAS
conflict and durable revocation, catalog class/AAL/service withdrawal, policy and
gateway Pod replacement, credential isolation, refused-request zero backend effects
and network-authority outage. The owned namespace was removed; existing workloads
were preserved. The two nodes share one physical host; this is not HA qualification.

Test maintenance corrected two mismatches: use the published Sumunjang plugin
with its matching published binary; check the current draft status and actual POST
CAS/revision instead of a static initial revision label. Control-plane port-forward
setup has a longer bound for the lossy management link, without changing proof
budgets. After gateway replacement, fresh diagnostic GETs may return 503 while
dependencies reconnect; each refusal must still have zero backend effects and
recovery is bounded. No application transport automatic retry was added.

Independent new Sumunjang source `60f19a5` separately passed a real API-server
CRD/RBAC/projected-token/native mTLS decision/update/withdrawal/restart/UID-pin
qualification. This is a later source candidate, not the retained published
Sumunjang binary in the four-service run. Its full-chain and signed release gates
remain separate. Safe observed connection pooling and throughput remain open.

## Published artifacts and internal adoption

[Hangang 0.3.6](https://github.com/ziozzang/hangang/releases/tag/v0.3.6),
[Hopae 0.0.8](https://github.com/ziozzang/hopae/releases/tag/v0.0.8) and
[Pumgye 0.1.7](https://github.com/ziozzang/pumgye/releases/tag/v0.1.7) are published.
The previous drafts were privately preserved before replacement. All five assets
per release were re-downloaded, independently signature/checksum verified and
compared with anonymous public downloads. Raw x86_64 musl executable SHA-256:

| Component | SHA-256 |
| --- | --- |
| Hangang | `28cdb570f4677eac52270d76033426fb4fa4dd37c9fe01a67aa96a8a151a1ace` |
| Hopae | `3e091d0a62b20a69eee2d532addf20a361127868def6de8f52cc5d850946a9c1` |
| Pumgye | `054249265e0eec9bbfae3e3fe93c3074648e511f2082ebc88a016e0365e9b598` |

Internal Hopae/Pumgye and Hangang gateway/console now run these releases. Private
rollback backups, configuration and owner-data preservation, exact running binary
hashes, management/native refusal checks and durable restarts were verified.
Existing routes retain their configured modes; installing binaries does not
automatically enable an unconfigured observed projection route or an external
provider. The subsequently qualified Sumunjang 0.3.6 is now separately published and adopted.
The earlier retained-0.3.5 result remains historical evidence for that exact set.

## Subsequent Sumunjang source candidate

The source/readiness candidate `aa43aa7` passed an actual scratch-image four-service
run with the independent observed SDK and browser: operator CRD block/unblock
changes final 403/200, manual mutations refuse, RBAC withdrawal and checkpoint Pod
replacement produce 503 without backend dispatch, replacement UID/config-only
repinning refuse, explicit repin/new Pod recovers, and final process outage refuses.
Created namespace and CRD were removed with UID/resourceVersion delete preconditions.
The global CRD test assumes no concurrent source operator.

A separate default-DB run of that new candidate found a console input-lock
regression when initial unknown authority becomes disabled. The canonical dashboard
and generated plugin were subsequently fixed. Because the dashboard is embedded,
a new exact static binary and both source/default qualifications were required.
The previous staged 0.3.6 candidate is explicitly not for publication. The published/operating Sumunjang 0.3.5 was preserved during that failed candidate.

## Final Sumunjang 0.3.6 publication and adoption

[Sumunjang 0.3.6](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.6)
is published at `7bfd6c1`, with runtime/embedded UI build inputs from `d6fc1de`.
The exact final canonical binary is
`25a197f1c39bddf63fe4c168294536475ed2b4ba2aa16bcbe7ee4ac2dfec8654`.
The alias is
`328ef91a0d95ba0c47d004b0a7c0559331a0edd37b107ea4335bd9a70db71957`.
All seven assets matched the qualified stage after draft and anonymous public
downloads; both raw signatures preserve the pinned release key, and all three
archive executable hashes and final console/deployment/docs content were checked.

The final scratch image and matching final plugin passed both native-source and
ordinary DB four-service/independent SDK/browser runs. Source mode additionally
qualified scratch HTTPGet readiness, operator-owned CRD changes, manual-write
refusal, RBAC withdrawal, persistent-checkpoint replacement refusal, source UID
replacement and explicit repin recovery. Both owned namespaces and the exact
created CRD were removed. Existing workloads and node readiness were preserved.

Internal server and immutable pinned plugin adoption are complete. Private
binary/SQL/configuration rollback backups, unchanged policy, native mTLS, supervised
HUP and all module management reads passed. A copied-file permission rejection
restored the previous console configuration; corrected private package permissions
and configuration preflight then passed before successful adoption. The source
mode remains opt-in; ordinary DB management remains editable.

## Subsequent Hangang 0.3.7 publication and adoption

[Hangang 0.3.7](https://github.com/ziozzang/hangang/releases/tag/v0.3.7) is published
at `15dadfa`; runtime build inputs are `58a7f64`, followed only by a browser-test
change. Its raw static SHA-256 is
`03473e142fbcf4fb24663f58d07c6babebb944eb86f180bf3b88ef026abc46cb`.
All five assets matched the signed frozen stage after draft and anonymous public
downloads; independent verification covered the pinned signature and all eight
archive executables. Internal gateway and console replacement passed private
rollback backups, configuration preflight, preserved configuration/credentials,
exact running hashes, management/refusal routing, module discovery and owning
Pumgye policy reads.

The classic network cache now charges positive TTL from its original Linux
BOOTTIME query capture and binds cached evidence to the source owner and generation.
Cache hits do not renew that capture. A valid zero-TTL point-in-time decision remains
usable once without cache or reusable proof; this is not a universal legacy final
socket fence. Existing observed final transport enforcement remains required.

Workspace qualification passed 1,312 tests with 58 ignored and strict Clippy.
An initial unrelated Lua timing failure and unchanged serial/full rechecks are
retained. The first actual K3s run also failed: a post-profile-restoration request
returned 503; a guard transport-query warning was observed but root cause remains
unconfirmed. The browser helper now checks backend effects before status assertions
and gives restoration a bounded 200/503 availability window; each request and proof
retains its original budget. The second exact-artifact run exited zero, including
native-source authority, independent SDK, browser/CAS, replacement/withdrawal,
readiness and non-dispatch gates. Its restore attempt returned 200 directly; it
does not reproduce or establish the cause of the earlier 503. Both owned namespaces
and the exact created CRD were removed, both nodes were Ready, and synthetic Retain
PVs were preserved under cluster policy. This single-host cluster establishes no HA.

## Hopae 0.0.9 composition publication and internal adoption

[Hopae 0.0.9](https://github.com/ziozzang/hopae/releases/tag/v0.0.9) is published
at `8c06a90`. Runtime source is `c97113e`, with fixture-only `1fd8f3e` and subsequent
release-guide packaging. Its exact static SHA-256 is
`db994813667c6ff6850234e68c369344dd03eadd3511c5d728f77a280921683a`.
All five assets matched the frozen signed stage after draft and anonymous public
downloads; independent verification covered signature, raw identity and every
archive executable/guide/plugin byte. English/Korean authentication configuration
guides are included.

All/Any Service/AAL0 API-key plus HTTPS-relay composition, explicit identity
mapping, presented-credential isolation and original source budget passed local
native tests. Production verifier CA snapshots are bounded and bind connector
ownership; custom roots are additive, with no hostname/certificate bypass.
Workspace qualification passed 1,017 tests, with 42 existing exclusions, and strict
Clippy. Actual Kubernetes All mode and ordinary Bearer mode both exited zero with
independent SDK/browser/native permission/output/source-withdrawal gates. Four
core services, a separate HTTPS verifier and a counted backend were used. Circuit
qualification requires exact provider-unavailable native RPC responses and actual
relay call counts; a generic HTTP 503 does not establish which authority refused.
Owned namespaces/created CRD were cleaned, both nodes were Ready and existing
workload identities/artifacts were preserved. Any mode with the new Hangang 0.3.8
candidate remains a subsequent gate, not part of this completed All/default result.

Initial browser credential-format, unexplained startup, catalog-restoration and
circuit-test assumption failures are retained. A later pass does not explain the
unconfirmed startup/availability observations. No original source/request budget
or automatic application retry was relaxed.

Internal adoption passed a read-only/no-network configuration preflight, private
binary/configuration/SQLite rollback backups, unchanged users/providers/sessions/
grants/MFA/profile authority/environment, native mTLS/HTTP expired-credential
refusal, exact installed hash and durable restart. An initial preflight CLI argument
placement error stopped before any operating mutation; corrected preflight and
rollout then passed. Existing operating profiles remain unchanged; installing this
release does not activate composition or complete Human/Workload projection.


## Hangang 0.3.8 responsive console publication and adoption

[Hangang 0.3.8](https://github.com/ziozzang/hangang/releases/tag/v0.3.8) is published
at runtime/build source `c5610e08d7b03b26f81ada309456de914d87ffb5`. Subsequent
`b88f7b7` only merges the qualified browser helper. The raw gateway SHA-256 is
`4e7c2815eed3a744abe8a4ba62aa8cd28abf3467b3b5668e600d9a4db5aa4288`.
All five draft and anonymous public assets equal the frozen stage. Independent
verification covers the pinned Ed25519 gateway manifest and exact hashes of all
eight static archive executables; it does not imply separate manifest signatures
for every helper binary.

Workspace qualification passed 1,312 tests with 58 existing exclusions and strict
Clippy; 33 selected UI regressions cover existing behavior and responsive layout.
Exact-artifact local observed/strict composition and Bearer regressions pass. Actual
K3s Any composition passes with both Sumunjang native CRD source and normal DB
source, including independent observed SDK, circuit recovery, CAS/revocation,
Pod replacement, non-dispatch and the new embedded 390px UI. Both nodes remained
Ready, all 12 pre-existing Pod UIDs were preserved and owned namespaces/created CRD
were removed; synthetic Retain PVs remain under cluster policy. Earlier startup/
restoration observations remain recorded and do not gain an explanation from these
passes. No Human/Workload, HA or throughput qualification is claimed.

The console and gateway are internally adopted with private binary/unit/config/SQL/
image backups, read-only preflight, configured gateway drain, exact running hashes,
unchanged credentials/UID/network/routing and module/policy read acceptance. A fresh
system-administrator browser opens Pumgye, Sumunjang and Hopae without page/module/
global errors. All three pages fit a 390px viewport; Pumgye previously expanded to
619px. Wide tables retain scoped scrolling. The focused layout and completed-operation
reference fixes do not complete the broader ADM-03/04/06/07/08/09 acceptance work.
