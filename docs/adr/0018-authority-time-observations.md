# ADR 0018 — Authority-relative time observations

[한국어](../ko/0018-authority-time-observations.md)

Status: draft; shared numeric core implemented, wire/native integration not
implemented. Publication gate for native cross-host receipts.

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

A native client captures local wall and monotonic time before and after the RPC.
Its private observation binds the exact immutable request and configured client
identity. A frame from a request-selected endpoint, script, ordinary auth response
or caller-supplied allow/time value cannot construct it. Enforce mTLS/caller roles,
correlation, digest/generation equality, size/admission/deadline bounds and local
clock-reversal rejection before exposing the observation.

If the owner reports remaining lifetime R, convert it into a local interval:

- Earliest expiry: local RPC start + R - one millisecond of sampling uncertainty. Final admission uses this lower bound,
  intersected with every previously accepted bound and original lifetime budget.
- Latest expiry: local RPC finish + the full signed receipt remaining lifetime
  in the owner clock domain + one millisecond. Replay rows remain until at least this
  upper bound, using monotonic and durable rollback protection. Expiring replay
  state at the admission lower bound could admit the same still-live nonce again.
  A shorter prerequisite observation must not shorten original nonce retention:
  a later live query could still accept the same signed proof.

Independent fractional clock phases require outward rounding: subtract one tick
from admission and add one to retention. This is no acceptance grace. Reject an
observation that leaves no positive admission interval.

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

Test positive/negative clock offsets, changing RPC latency, wall reversal, signed
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
permission. Native RPC fields/owner guards, independent-client adoption, paired
ledger retention and final-output integration remain unimplemented for this
contract. Draft releases and the cross-host Kubernetes gate remain open.
