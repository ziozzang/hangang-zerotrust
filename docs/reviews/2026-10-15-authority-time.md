# Authority-time review record

[한국어](../ko/2026-10-15-authority-time-review.md)

Status: source review, tested regressions and proposed integration design.
This record does not qualify a release. Three Astra reviewers worked on source
security, adversarial tests and cross-component integration. The coordinator
executes tests and owns production edits.

## Confirmed and tested

Hopae's final live-service check loaded a profile before an external clock call.
Publication during that call could replace the profile and restore a shared
availability flag; the saved old pointer then incorrectly matched the captured
profile. A deterministic test publishes through the actual native authority from
a one-shot clock callback. It fails with the previous ordering and passes when
the final profile is acquired after clock sampling. Both strict and observed
contracts are covered by the fixed test.

The projection output fence likewise sampled the external clock after activity,
caller and owner checks. The corrected order samples the clock, invokes the
caller check, accounts conservatively for callback elapsed time, then checks local
activity and owners. Deterministic activity/caller mutations during the clock call
pass refusal tests inside the actual Hopae mTLS harness. Its Pumgye peer remains
an explicit protocol mock; this is not four-server qualification.

Seven new external SDK tests pass. They cover canonical clock epochs at exact
size/revision limits, malformed encodings, signed authentication/permit binding
separation, 400 independent offset/phase/asymmetric-latency scenarios, hostile
reports/exchanges and all six ordering permutations of three revalidations.
They establish neither caller roles nor durable nonce consumption.

## Integration blockers

Hangang and Pumgye still use legacy local-wall checks. Foreign signed expiries
also appear in permit construction, live validation, projection admission and
final credential output. Updating issuance alone is insufficient. Keep the strict
path explicit until every observed-specific replacement exists; do not strip a
clock prefix and fall back to legacy semantics.

Admission and replay retention require separate types and clocks. Admission uses
the conservative lower bound; each proof retains its own full signed-lifetime
upper bound. Receiver wall-forward cleanup can delete a consumed nonce while its
source proof remains alive, and a fresh relative observation can then re-admit it.
A durable wall watermark alone does not close this migration hazard.

The preferred design under review uses receiver-owned monotonic retention,
versioned durable rows and explicit restart/domain rules. A narrow first topology
can colocate Hopae issuance and projection in the exact same process: restart
retires the old authentication clock domain, and permits remain bound to its exact
digest. Arbitrary replica routing, independently restarted receivers, snapshot
restore and independent multi-ledger consumption require additional fencing and
must not inherit that claim.

## Design and test queue

Introduce private native authentication/permit observations bound to the exact
request, configured client, signed digest, source domain and owner generations.
Keep signature evidence distinct from temporal admission. A public numeric report
cannot mint either capability. Projection output needs its own authenticated time
envelope and final local deadline at Hangang dispatch.

Next gates are Pumgye observed permit semantics; paired ledger and output migration;
complete Hangang adoption; and independent-host plus actual four-Pod/browser,
withdrawal, cancellation, restart and compatibility tests on exact artifacts.
Explicit caller roles are still absent from rotation-slot-only caller keys.
Observed epoch configuration eligibility also needs preflight: the 128-byte
format permits a base of at most 42 bytes at maximum revisions.

See the [active queue](../ASTRA_REVIEW_QUEUE.md) and
[draft ADR 0018](../adr/0018-authority-time-observations.md). Fleet restore and
throughput claims remain separate unfulfilled gates.
