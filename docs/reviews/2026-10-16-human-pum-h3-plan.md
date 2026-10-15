# H3 queue: typed Human policy and native permission

Status: **read-only implementation checklist**, blocked on H2's verified subject
semantics. No Human policy field, evaluator, RPC or capability is implemented here.
[한국어](../ko/2026-10-16-human-pum-h3-plan.md). ZT base98874bc.
Pum runtime435f138927fa78a1256e8a29a442eba399b971b6 is the source anchor;
inspected checkoute253e37 has no core/server/protocol changes relative to435.
H1 pure v2 hashing is metadata only. H0 current native session is not yet a public
Human receipt. Neither can be cast into the Workload source owner.

## Exact insertion points

Paths below are relative to Pum. Line numbers refer to435:

| Source | Existing boundary | Additive H3 work |
|---|---|---|
| `crates/pumgye-core/src/lib.rs:25,159,286,301,326` | Service DTO, compiled maps, API-context validation, aggregate capacity, Workload compilation | Optional empty-skipped `human_users`, same compiled service/View and assignment limits; forbid Human assignments in KubernetesApi context. |
| same`:226,457,474` | Inherited role AAL and max(user/network/resource floor) evaluation | Preserve shared role/network/resource requirements; Human input accepts only actual verified AAL1/2, never AAL0/3. Do not globally cap existing Service metadata or reinterpret its API. |
| same`:410,560,581,598` | Fixed typed principal and scoped Workload resource evaluation | Add `Principal::Human` and explicit scoped Human evaluator selecting only human_users, same catalog/action/class and network/Guard logic. |
| `crates/pumgye-server/src/main.rs:286,324` | Typed preliminary Workload resource decision on captured View | Eventual fixed Human preliminary RPC adapter; query metadata is not authenticated Human evidence. Require service scope and valid assurance metadata; final permit still mandatory. |
| same`:935,1035`; `authentication_live_config.rs` | Explicit Workload activation/config startup owner installation | Separate opt-in Human owner with fixed peers/scopes/rates; no automatic activation from generic receipt kind or policy contents. |
| `authentication_workload_observed.rs:22,64,92,122,149,165,187` | Private SDK observation, configuration generation, current owner before/after callbacks | Separate private Human observation built only from future H2 public opaque SDK; fixed issuer/key/authority/scope, original age and current session/provider/material owner. No numeric constructor. |
| `observed_native.rs:6,12,22,28,33` | Exact Authority/View Arc bridge/current/source remaining | Reuse this bridge; no copied grants or second policy engine. |
| `workload_observed_permit.rs:148,207,268,300,365,390,440` | Prerequisite capture, plan AAL0, compiler decision, expiry anchoring, typed signing, post-sign owners, report | Separate Human service using actual auth AAL1/2 in plan and policy, fixed v2 request/route/destination; preserve all final original-deadline/current checks. |
| `permit_wire.rs:56,75,93`; `crates/pumgye-grpc/proto/*.proto:87` | Typed observed verify/sign and additive RPC separation | Dedicated Human Issue/Observe and kind1/AAL1-or2 checks. Allocate names/schema only after H2 fixed contract; preserve existing Service/Workload bytes. |

## Ordered implementation checklist

1. **Resolve H2 prerequisite before coding subject keys.** Specify stable subject
   namespace, exact issuer/realm/provider/session versus person identity semantics,
   collision-resistant derivation and withdrawal rules. Do not use mutable email,
   display name, caller-chosen realm or a Workload hash as Human identity. Require
   canonical vectors and actual H2 signed/opaque observation agreement.
2. **Pure core stage.** Add the optional independent map and compiled map; count it
   in the existing65536 aggregate assignment budget. Use the same role compiler,
   inherited entitlements, catalog class/action, scoped service equality and
   network intersection. Reject API-context Human assignments at compile time;
   ordinary Human evaluator must also refuse KubernetesApi at runtime. Old policy
   serialization stays byte-identical when map absent/empty.
3. **Per-user assurance policy.** Reuse assigned roles' minimum_aal as the initial
   per-user scope mechanism: a Human user's assigned roles determine their floor,
   combined with network and resource floors. A service-wide floor must not raise
   unrelated users. Shared role aggregation is conservative maximum, not proof of
   MFA. A role/resource requiring3 remains unsatisfiable by initial Human AAL<=2;
   do not weaken existing requirements to make a request pass. If product requires
   a separate assignment override, design that DTO explicitly before implementing.
4. **Trusted owner stage, after H2.** Actual private SDK observation only; signed
   proof alone is not permission. Strict kind1, actual AAL1/2, fixed app/realm/scope,
   request v2 and destination/header policy revisions, receipt hash and original
   nonrenewable owner age must match. Logout/revoke/disable/factor/provider/material
   changes must retire or shorten observation through the native current owner;
   no caller assertion of assurance or reconstructed UTC lease.
5. **Native permit stage.** Capture same exact View, actual Sum network evidence,
   fixed route and exact AAL plan, evaluate Human map, reobserve owners/refresh auth,
   sign typed permit, then repeat post-sign owner/current/time fences. Anchor every
   converted remaining budget before callbacks; BOOTTIME failure/reversal retires
   source, same publication cannot renew. Keep full signed proof retention distinct
   from prerequisite-shortened admission. No fake Guard EnforcedAllow.
6. **Protocol/integration stage.** Add bounded authenticated ingress path/budgets,
   predecode/hostile body tests, explicit CLI/config owner failure matrix, private
   Human client adapter and contract4 output on SAME paired ledger. Root must use
   route-owned class and bind preliminary identity to final opaque principal;
   no endpoint selected by raw headers. Human end-to-end is a separate later gate.

## Required meaningful gates

- Deliberately colliding raw-label injections must fail the correct class namespace
  validator. Independently canonicalize the same underlying identity label for each
  class and assign disjoint roles: each fixed evaluator selects only its map. Where
  legacy users accepts either canonical string, its grants still cannot supply a
  typed-map fallback. Deleting a Human grant never falls back in either direction.
  Do not require a valid Human string to pass the Workload parser. Unknown Human,
  invalid H2 subject and class/service/action/resource mismatches deny; no mutation
  of shared View or second compiler.
- Two Human users on the same service/resource/network: only one assigned MFA role;
  AAL1 allows the first and denies the second, actual AAL2 permits the second.
  AAL0/3 never qualify; body/header claims cannot elevate. Resource/network floor2
  and class/network-deny remain effective. Required3 stays denied.
- API-context Human assignment compile failure and Human evaluation refusal even
  when a matching API mapping/legacy users grant exists. No fabricated IP/Guard.
- Old defaults/v1 mapping output and Service/Workload vectors byte-identical;
  nonempty new maps rejected by old-template conversion rather than hidden grants.
- Actual H2 owner fixture: logout, session revoke, disable, factor removal/MFA
  downgrade, provider/material withdrawal and owner replacement around every
  callback/signing boundary; grant deletion on same Authority publication and
  captured old View cannot authorize. Restart claims must distinguish durable
  session revalidation from an old process-private observation.
- Exact v2 request/body/header/destination mutation refuses, native plan AAL mismatch
  refuses, signed kind collision refuses. Expiry/suspend/read-error/callback-delay
  tests retain original source deadline. Observe miss/withdraw refuses, never
  reconstructs permission from signed proof alone.
- Whole default/observed workspace regressions and strict Clippy, then actual
  authenticated RPC→public Human SDK→Pum→same Hop ledger→Root backend counter.
  No full-chain claim from pure compiler tests or synthetic signer fixtures.

This checklist does not implement directory watching, native local account recovery,
all-provider MFA, distributed desired-material authority, external DBMS followers,
or measured100k throughput. They remain full-objective work rather than exclusions.
