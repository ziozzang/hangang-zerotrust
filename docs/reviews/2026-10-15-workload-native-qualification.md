# Native Workload qualification — 2026-10-15

Actual K3s run2 completed with exit0 using immutable staged static binaries:
Hangang `f45fe3e`, Hopae `848dc835`, Pumgye `adaf985`, Sumunjang `d6fc1dec`.
The helper was `504f5c3`. No candidate public release or operating replacement
is implied. Two K3s nodes share one physical host; this is not multi-host HA.

The actual public SDK verified a bound ServiceAccount/Pod identity, kind3/AAL0;
only its independently verified subject was granted in `workload_users`. The
real Hangang request used the dedicated Pumgye Workload metadata decision, native
permit and contract3 credential projection, then reached the backend. Identical
paired-proof replay was refused while preserving original timing and native owner
checks. Workload could not borrow legacy `users` rights. Missing/wrong-audience
and tampered credentials, fixed-authority mismatch and changed cluster realm
failed their expected boundaries without unauthorized backend delivery. Realm
changes and restoration used durable owning CAS plus exact readback.

Hopae Pod replacement allowed fresh proof and refused held old evidence on the
same public connection. Original one-second expiry can independently explain
the old-proof refusal: this does not isolate restart as its cause. Reviewer-role
withdrawal refused authentication; explicit restoration recovered. Replacement
Pod UID produced another verified subject, refused its predecessor's grant and
worked only after an explicit new grant. Pod and ServiceAccount withdrawal
refused authentication. Raw API TokenReview withdrawal was observed after about
36.2s and 10.9s respectively; propagation is distinct from the original maximum
one-second source-evidence lifetime. Restoration observed HTTP503/backend0 before
HTTP200/backend1 without changing any per-request budget.

An early read-only watcher captured all four cores, replay tap and echo Ready.
Their actual runtime imageIDs matched the exact expected per-node import manifest
digests. Pod API exposed manifest IDs, not independently inspected config IDs or
process UIDs. Core/tap declared nonroot UID65532, read-only root filesystem,
no privilege escalation and dropped capabilities were observed. Echo hardening
is not claimed.

Exact owned namespace/global resources were cleaned with UID preconditions. Both
nodes stayed Ready and all 12 baseline Pod UIDs were preserved. Existing Echo and
Ingress returned200; anonymous Headlamp API returned401. The fresh cold snapshot
and verified off-host copy remain preserved; no restore rehearsal was performed.

Run1 remains a failed qualification: bootstrap ConfigMap changes did not update
DB-owned profiles. Its partial positive chain evidence and unavailable running-core
attestation were not rewritten into passes. The repaired helper has 28 passing
pure tests covering stale/mismatched publication, readback, restoration and
lost-response reconciliation without blind mutation replay.

Remaining release gates include separate actual Service/composition and compiled
console/browser qualification of the exact candidates, signed public-asset round
trip and backed-up internal adoption. This run does not complete Human/MFA,
Workload administrator UX, inbound Kubernetes authentication/authorization webhooks,
external DBMS adapters, fleet/clone/rollback fencing or throughput qualification.
