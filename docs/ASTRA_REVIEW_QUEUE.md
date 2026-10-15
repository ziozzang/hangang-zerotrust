# Astra review and test queue

Status: active engineering queue, not release qualification. Korean companion:
[review queue](ko/ASTRA_REVIEW_QUEUE.md).

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
