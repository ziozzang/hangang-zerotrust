# Astra review and test queue

Status: active engineering queue, not release qualification. Korean companion:
[review queue](ko/ASTRA_REVIEW_QUEUE.md).

Review collection has concluded. No Astra reviewer is running; assignments below
are historical batches. Implementation now consumes the retained findings and
acceptance criteria. Unfinished follow-up drafts are not completed reviews.

The coordinator assigns bounded reviews to Astra, collects counterexamples and
tests, fixes confirmed defects, and assigns the next ready item. Reviews do not
replace executable acceptance evidence. Production edits and shared Cargo target
execution remain coordinated to avoid overlapping mutations.

## Running

| ID | Assignment | Expected evidence |
| --- | --- | --- |
| A1 | Authority-time source security, publication fences, clock changes and issuer restart | File-specific findings, counterexamples and deterministic regression designs |
| A2 | Public SDK adversarial clock-epoch and interval tests | Isolated integration test file; coordinator executes tests |
| A3 | Cross-component clock migration and durable replay safety | Hopae/Hangang/Pumgye integration map, failure cases and migration gates |

Initial A1 finding awaiting reproduction: a captured profile reader may be loaded
before an external clock call and checked after profile replacement. Confirm the
publication sequence and add a deterministic regression before claiming a fix.

## Ready follow-up work

1. Reproduce publication during final validation, then review equivalent fences
   for application, key registry, route, network and permission snapshots.
2. Review issuer restart and same-key multi-replica clock-domain separation;
   distinguish signer identity from exact issuing process ownership.
3. Review replay retention under shortened observations, renewal, backward and
   forward wall changes, durable restart and concurrent consumers.
4. Design independent-host observed-time client tests with asymmetric latency,
   fractional milliseconds, missing fields and explicit legacy refusal.
5. Review Pumgye permit observation and Hopae projection receiver migration:
   every deadline must remain in its owner's clock domain until converted.
6. Review authenticated connection pooling, cancellation, bounded concurrency
   and input limits for the new RPCs. Keep analytics off the decision path.
7. Define K3s functional acceptance cases for all four actual servers, including
   key withdrawal, policy/profile replacement and browser admin regression.

## Evidence and release boundary

The existing static four-server credential-projection fixture passed. The K3s
independent-host receipt client failed strict local-time verification despite a
valid signature. The observed-time source RPC and clock-domain changes are under
development; downstream adoption and complete K3s qualification remain open.
Draft releases must remain unpublished until corrected artifacts pass the full
functional gates. No performance claim follows from these reviews.

Review artifacts initially stay local and must be checked for sensitive details
before their findings are incorporated into repository documentation.

## First execution results

The durable [review record](reviews/2026-10-15-authority-time.md) consolidates
confirmed evidence, boundaries and proposed integration gates.

- A1 produced a source review and a deterministic native profile-publication
  regression patch. The coordinator applied a provisional final-check ordering
  correction; regression execution and final requalification are in progress.
- A2 delivered seven external SDK tests. All seven passed, including 400
  physical-time offset/phase/asymmetric-latency scenarios. These prove the tested
  numeric and cryptographic properties, not authenticated transport or replay
  consumption. A2 continues with an observed-RPC fault test plan.
- A3 identified a migration gate: receiver wall-forward cleanup can discard a
  nonce while its foreign source proof remains live. New relative observations
  can then re-admit it. Durable monotonic ownership, restart behavior and exact
  issuer-process affinity must be specified before changing replay admission.
- A1 continues with final-output cancellation/caller/publication interleavings;
  A3 continues with bounded issuer-affine and independent-receiver designs.

## Subsequent batches

- A1's final-output regression patch passed in the actual Hopae mTLS harness.
  Its resource review found late observed request-ID rejection; a new regression
  reproduced unnecessary authentication work. The observed-only early guard now
  passes. No new semaphore leak, secret metadata echo or downgrade fallback was
  established. Inherited protobuf decode amplification remains a separate review.
- A2 delivered four further native boundary tests: early ID rejection, metadata,
  capacity-one nested issuance/refresh and cancellation permit recovery. All four
  pass after the early-ID fix. A2 now designs explicit native caller roles.
- A3 delivered a bounded issuer-affine replay design. Source virtual time and
  stable receiver retention time must remain separate even in the same process.
  A3 now inventories minimal shared static types and compatible migration APIs.
- The source milestone passed 968 workspace tests with 42 existing exclusions
  and strict all-target Clippy before the additional four boundary tests. Source
  is committed; release assets and operating deployments remain unchanged.

Historical next assignments were shared gRPC decode resource limits (A1), native
caller roles (A2), and shared static observed-evidence/ledger interfaces (A3).
Astra collection has ended; none of these agents remains assigned.

## Reusable implementation handoff

Completed source milestones: Hopae `cde8416` separates signature evidence, adds
explicit oscillator-rate arithmetic and early gRPC metadata authentication;
Pumgye `f1ce600` and Sumunjang `d1e6caf` add the same predecode caller boundary.
Their complete workspaces pass 987/75/131 tests respectively (Hopae has 42
existing exclusions), with strict all-target Clippy. The Sumunjang count includes
both binary names. Runtime `ed2eee4` provides instance-bound BOOTTIME exchange,
deadline/retention and elapsed-stamp infrastructure: 24 tests, strict Clippy and
musl target compilation pass. Consumer/source-suspend adoption remains open.

The [administrator review](reviews/2026-10-15-admin-ui.md) consolidates three
complementary reviews and tasks ADM-01 through ADM-09. Follow-up navigation,
write-safety and visual-specification drafts were interrupted before being saved;
use the original reviews' actionable criteria rather than claiming those drafts
exist. Implementation of draft protection, policy CAS and footer placement is
underway. Findings and prototypes are not deployed UI fixes.

Ready subsequent work, in order:

1. Adopt the implemented observed-client evidence into native authorization,
   permit/output and paired-ledger paths (ADR 0018). Resolve digest-only callers,
   verified dynamic identities and process-domain bootstrap without per-request
   channels, incoming owner pins, fake UTC or mode fallback.
2. Qualify actual owners and independent management-host/four-Pod Kubernetes paths,
   withdrawal/restart/failure, browser delegation and exact signed rebuilds.
3. Continue remaining ADM criteria for deterministic menu, layout, routing,
   localization and accessibility using the retained plans.
4. Qualify resource budgets and requested throughput separately; unary ingress
   source adoption is not a measured performance result.

For each queued implementation, recheck actual source, retain its acceptance
criteria and record commit/test evidence. Reuse completed reviews rather than
requesting the same analysis again.


Post-reset Sol implementation evidence: Hangang `b81a310` preserves Pumgye drafts
and plugin footer/heading placement and tests delegated CAS forwarding; workspace
and strict Clippy pass (14 Pumgye and 6 focused UI browser cases previously passed).
Sumunjang `10eab03` adds epoch/revision policy-document CAS and uncertainty-safe
editors; 18 focused policy tests, both mocked Chromium suites and reproducible
plugin generation pass. Hopae `ce4d27f` adopts suspend-inclusive source proof age
and protects editor drafts/acknowledgements: 992 workspace tests pass with 42
existing exclusions, strict Clippy and 35 mocked Chromium cases pass. Its initial
unrestricted suite hit an existing storage-budget timing assertion; the isolated
case and complete rerun with four test threads passed. No time-limit assertion
was weakened. These source commits are not rebuilt release artifacts or deployed
K3s qualification. Consumer time migration and shared ingress limits remain open.


Subsequent implementation: shared unary ingress is committed and tested in runtime
`0cdbd166` and all four components (Hangang `b41b492`, Pumgye `34d74b6`, Sumunjang
`1f73a18`, Hopae `2a96303`). See ADR 0017 for exact evidence and limits. Hopae's
optional native client supports independent initial proof observation, fresh
per-RPC correlation and per-client retirement. A read-only Sol follow-up maps its
remaining native consumer gaps; no further Astra review has been requested.

Current next boundary: [native consumer adoption](reviews/2026-10-15-native-observed-adoption.md), a Sol review of the implemented exact SDK and actual production query shapes.
