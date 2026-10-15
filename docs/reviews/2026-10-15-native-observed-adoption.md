# Native observed consumer adoption

Status: implemented native consumers with final local signed-artifact qualification;
independent-host Kubernetes qualification is in progress. Current source: Hangang
`97419f3`, Hopae `bc5b2a4`, Pumgye runtime `4724962` (packaging `d207266`).
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

The first actual K3s run already passed final credential transformation across the
four Pods and the independent management-host native SDK's issue, independent
observation and consuming refresh. The remaining console, mutation, revocation and
restart checks are still under investigation; this is not a complete Kubernetes
qualification result. Safe observed connection pooling and throughput remain open.
