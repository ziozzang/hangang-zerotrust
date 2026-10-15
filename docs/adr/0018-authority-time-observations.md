# ADR 0018 — Authority-relative time observations

[한국어](../ko/0018-authority-time-observations.md)

Status: draft; shared numeric core implemented, source-side observed RPC prototype
under development. Native client/permit/replay integration is not implemented.
Publication gate for native cross-host receipts. See the
[Astra review record](../reviews/2026-10-15-authority-time.md).

## Evidence and problem

The signed 0.3.6/0.0.8/0.1.7 static candidates pass the local four-server fixture.
An owned Kubernetes run also delivered the separate origin bearer through all
four Pods. Its independent receipt client, running on the management host, failed.
A diagnostic using the same fixed mTLS authority and public pin observed a valid
signature/scope with issued time 4 ms after local receipt arrival. Strict local
wall-time validation refused it. A second signed check at the issued instant was
for diagnosis only: it granted no access and emitted no receipt or credentials.
Both runs remain failed overall qualifications. No release publication or operating
replacement follows from the positive Pod-only subset.

Absolute milliseconds from different clock domains cannot safely be compared as
if they shared a clock. An arbitrary grace period can extend authority; delaying
all requests also conflicts with the fast path. Keep signed canonical timestamps
and owner clock-rollback protection, but model transport evidence explicitly.

## Proposed contract

An authenticated fixed-owner response reports its own current time and bounded
remaining lifetime, correlated to the exact request and receipt digest, authority
purpose/key/identity epoch, exact issuing clock-domain identity and captured
current native owner generation. A logical issuer alias shared by replicas is not
a clock domain. Native routing must reach the issuing domain or use an explicitly
authenticated conversion; follower-local wall time must not silently replace it. The owner
must validate its own receipt, live state and final guards before reporting it.
Remaining lifetime is positive, at most 1,000 ms and never exceeds any prerequisite
observation or signed lifetime. It is no cache lease or renewal.

A native client captures its own suspend-inclusive monotonic time before and after the RPC.
Its private observation binds the exact immutable request and configured client
identity. A frame from a request-selected endpoint, script, ordinary auth response
or caller-supplied allow/time value cannot construct it. Enforce mTLS/caller roles,
correlation, digest/generation equality, size/admission/deadline bounds and local
monotonic-clock error rejection before exposing the observation. All observed
receiver admission and replay-retention coordinates use this same fixed-origin
axis. Receiver UTC is not an input, so wall steps cannot move expiry or cleanup.
No per-request wall-continuity lock or epoch is required. Legacy strict UTC
verification and source-owned UTC credential budgets remain separate.

Under an explicit equal-rate clock assumption, if the owner reports remaining
lifetime R, convert it into a local interval:

- Earliest expiry: local RPC start + R - one millisecond of sampling uncertainty. Final admission uses this lower bound,
  intersected with every previously accepted bound and original lifetime budget.
- Latest expiry: local RPC finish + the full signed receipt remaining lifetime
  in the owner clock domain + one millisecond. Replay rows remain until at least this
  upper bound, with generation-tagged durable restart rules. Expiring replay
  state at the admission lower bound could admit the same still-live nonce again.
  A shorter prerequisite observation must not shorten original nonce retention:
  a later live query could still accept the same signed proof.

Independent fractional clock phases require outward rounding: subtract one tick
from admission and add one to retention. This is no acceptance grace. Reject an
observation that leaves no positive admission interval.

Quantization does not bound oscillator error. With independent source/receiver
error limits `p_s` and `p_r` in parts per million, require both below `10^6` and
use checked rational arithmetic:

- Admission delta: `floor((R_short - 1) * (10^6 - p_r) / (10^6 + p_s))`.
- Retention delta: `ceil(R_signed * (10^6 + p_r) / (10^6 - p_s)) + 1`.

Native adapters must establish their supported clock-rate model. Only admission
shrinks; retaining tombstones longer is not acceptance grace. Neither formula
proves arbitrary rate drift, source suspension/restore or uninterrupted source
progress. Linux receiver infrastructure uses `CLOCK_BOOTTIME` to include host
suspend and refuses unsupported/read-failed clocks without `Instant` fallback.
Final boundaries must check that clock even when an async timeout has not fired.
Source issuer progression and original proof age must also include suspend,
including time spent awaiting authentication; their adoption remains open.

Account for elapsed time without a new per-request SQL read or an unbounded queue.
Do not refresh the interval while reusing an earlier proof. Re-query the native
owner when current state is required; each new result intersects accepted bounds.
An unavailable/incompatible peer refuses without fallback or widening policy.

## Changes requiring implementation and review

- Add explicit time observations to issuance and live-validation contracts and
  their bounded SDK clients. Keep legacy strict primitives explicit; no silent
  reinterpretation of absent new fields.
- Separate cryptographic structure/signature/binding evidence from temporal
  admission. Signature success alone must never become a permission or secret.
- Verify an owner's own signed timestamps in its clock domain. Cross-purpose
  authentication/permit composition uses authenticated local intervals and the
  signed authentication digest, not arithmetic between foreign absolute clocks.
- Update final-output guards and paired transactional replay retention together.
  Preserve key/plan/profile/application/caller retirement and cancellation fences.
- Share the native time-envelope rules in static libraries, with component-owned
  state and independent servers. No shared mutable authorization business schema.

## Required qualification

Test positive/negative source offsets, changing RPC latency, source wall reversal,
receiver wall steps without deadline/cleanup movement, suspend, rate error, signed
expiry overflow, missing/forged/mismatched observations, generation retirement,
request/client swaps, cancellation and already accepted shorter deadlines. Prove
no permission extension and no replay gap between lower/upper expiry bounds.
Run the independent management-host receipt client and actual four-Pod final
credential path, browser/module delegation, withdrawal/restart/failure tests and
existing-mode compatibility. Rebuild and verify exact signed artifacts before
publishing or deployment. Fleet restore and 10k/100k throughput remain separate
unfulfilled gates.

## Numeric core implementation evidence

The source `hopae-grpc::receipt_time` helper checks exact verified receipt hashes,
issuer-domain lifetime, bounded local samples, overflow/expiry and clock
discontinuities. It intersects admission and retains the later replay ceiling.
SDK 21 tests pass, including 2,601 asymmetric-latency and 405 fractional-phase/
offset samples. Crucially retention uses the full signed remaining lifetime,
not the shorter prerequisite report. The arithmetic has no per-call allocation,
SQL or network work. The corrected complete workspace passes 958 tests with
42 existing exclusions. Strict all-target Clippy passes. The source foundation
is Hopae `7cd9c65`; it is not part of the frozen draft release assets.

This helper is numeric evidence only, not an authenticated observation or a
permission. Subsequent Hopae source adds explicit owner RPCs and native guards,
signature-only evidence and independent clock-rate arithmetic (`cde8416`). Runtime
`ed2eee4` adds BOOTTIME instance-bound deadlines/retention and elapsed stamps.
Hopae `ce4d27f` adopts suspend-inclusive source/proof budgeting, including age
before provider authentication. Hopae `2a96303` adds optional fixed-owner native client evidence: issue, initial
observation of externally issued proofs and consuming refresh. It authenticates
mTLS and caller metadata, pins exact source context, uses fresh correlations and
BOOTTIME bounds, and retires in-flight admission without deleting retention.
Generated mTLS fixture tests pass, including independent receivers and hostile
responses; it is not the deployed Hopae owner. Native authorization/permit
consumers, paired ledger retention and final output have not adopted the contract.
Consumer adoption must also handle authenticated digest-only requests, dynamically
verified identities and process-domain bootstrap without creating a channel per
request or trusting incoming owner pins.
Draft releases and the cross-host Kubernetes gate remain open.


## Stable native trust and adapter evidence

Hopae `c7ddcf2` adds stable server-compiled trust and digest-oriented preparations
without constructing a transport from incoming context. Signed dynamic identity
and source domain must match the fixed current owner. Pumgye `97bf852` compiles
its immutable trust into a separate observed authentication adapter, with borrowed
ArcSwap generation checks, serialized retire-before-publish and final time checks
after external callbacks. It does not activate an observed endpoint or signing.

Hopae `d828830` tests the SDK against actual receipt/profile/application/key owners
over mTLS, including independent observation/refresh and key withdrawal while
local evidence remains unexpired. Only its permission peer is mocked. The complete
workspace passes 995 tests with 42 existing exclusions, strict Clippy and SDK musl
compilation; Pumgye's feature workspace passes 78, strict Clippy and default locked
check. The SQLite async-deadline test race was fixed separately in `2e22240`, with
bounded worker observation, real interruption/rollback/restoration and 10 stress
repetitions; request budgets and production scheduling were not changed.

Next is distinct Pumgye prerequisite/permit source time, observed envelopes, paired
replay/output and final dispatch. No release artifact, four-owner Kubernetes path
or operating route is qualified by the adapter/library evidence above.
