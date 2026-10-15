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


## Subsequent Service and installed-console gates

The same frozen f45/848/adaf/d6fc candidates passed local observed All, strict All
and legacy bearer regression. A separate actual K3s non-composition Service run
passed the embedded administrator/browser, native Sum source, withdrawal and
restart gates. Five Ready core/echo runtime imageIDs matched their approved
per-node imports. The actual All-composition rerun also passed its native SDK,
HTTPS relay circuit and embedded browser gates, including installed Hopae0.1.6
and Sumunjang plugin0.1.4 live EN/KO draft/node preservation without extra owner
requests. Host-owned navigation and 390px layout passed. Cleanup preserved all
12 baseline Pod UIDs and removed the exact created namespace/CRD.

The first All browser run failed because the expected Sum plugin child was absent.
Native authentication/SDK/circuit gates had already passed. The original helper
did not retain enough safe mount-error metadata to identify the cause. The rerun
used additional path/status/timing and alert-hash diagnostics without intercepted
API responses, relaxed selectors or proof budgets. Its success does not explain
the original failure. Both records are retained. Neither run qualifies standalone
hangang-console SSO or every administrator/error/locale/in-flight state.

A subsequent status-page pentest exposed an additional Hangang TLS400/HSTS edge.
The operating gateway now has a narrow two-host HSTS configuration, but that
source fix introduces a new candidate that needs its own full source/static and
exact-binary acceptance. These f45 results must not be presented as the final
security candidate's completed release/adoption gates.
