# Workload gateway adoption contract

Status: implementation contract, not a qualified Workload dispatch path. Operating
Hangang 0.3.8 is Service-only. Native Workload authentication and public SDK have
local integration evidence; authentication signatures do not grant permission.

## Explicit route selection

Add an explicit route-owned class with a backwards-compatible Service default.
Workload requires observed authentication, signed permission and observed output
configured together. Reject legacy UTC/strict combinations at compilation. Never
select class from a request header, receipt or denial; never fall back or retry a
different class/endpoint. Immutable route owners retain class, scope, pins, source
floors and transport identity. Replacing a route retires the old SDK owner.

## Typed authority and shared enforcement

Retain the public opaque Workload SDK PreparedRequest and Observation. A private
gateway enum can wrap Service/Workload, with typed issue/check/consuming refresh
branches. Shared verified context/digest/receipt accessors cannot mint authority
from numeric timestamps or convert Workload to Service. Workload is kind3/AAL0;
service, audience and final request hash must match before permission evaluation.

Select the dedicated Workload permission RPC from the configured class. Pumgye
uses workload_users from the same compiled policy/source view, without Service
grant fallback. Verify permit kind against the route-owned expectation, never the
response-selected kind; retain policy/network/route/plan floors and owner checks.

Select dedicated Workload output RPC and permission contract3. Bind the original
resource query and permit into the chain digest. Hopae uses the SAME atomic paired
replay ledger across classes/endpoints, with source/plan/secret checks around
callbacks and before disclosure. Endpoint changes cannot create replay namespaces.

Reuse bounded entity collection, hash preparation and below-TLS final raw transport
checks. Each stage contributes only conservative receiver-local deadlines: never
compare foreign absolute ticks or renew original authentication age by observing.
Original capture includes queue/connect/RPC/body/suspend. Long signed replay
retention remains distinct from short dispatch admission. Check authority and all
deadlines before installing secrets and again at final transport; no automatic
application retry after consumption or authority refusal.

## Required evidence

- Existing Service configuration serialization and native regressions remain;
  incomplete or strict/Workload combinations fail before runtime.
- Actual Workload RPC permits only mapped workloads. Service grants, wrong kind,
  AAL/scope/audience/hash/key/generation/owner refuse with zero backend effects.
- Delay/expiry, missing records, issuer replacement, grant deletion, same-content
  policy-owner replacement, plan/secret/route withdrawal and refresh races refuse
  without renewal or fallback. Same pair cannot replay across classes/endpoints.
- Frozen four-service K3s chain uses actual audience-bound ServiceAccount JWT and
  TokenReview through permission/output to a counted backend. Test UID/audience/
  cluster/Pod mismatches. Measure Kubernetes deletion/TokenReview propagation
  separately from the original one-second lifetime of already captured Hopae
  evidence. The latter is not a deletion-to-denial guarantee.
  Independent server instances in one OS process do not prove an OS restart.
- Preserve failed logs, qualify exact source/static artifacts, verify public assets,
  then adopt with private backup/preflight/rollback. Human, throughput, safe pooling,
  multi-host HA and restore fencing remain separate unfinished requirements.

[Korean companion](../ko/design/WORKLOAD_GATEWAY_ADOPTION.md).


Kubernetes documents a distinct pending-deletion token rule: authentication fails
at or after 60 seconds beyond deletionTimestamp; missing referenced objects or UID
mismatches also refuse. Test the actual cluster response rather than assuming its
latency. Fresh successful TokenReviews create fresh evidence, so limiting each
Hopae record to one second cannot bound upstream acceptance propagation.
Source: [Kubernetes ServiceAccount administration](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/#bound-service-account-tokens).
