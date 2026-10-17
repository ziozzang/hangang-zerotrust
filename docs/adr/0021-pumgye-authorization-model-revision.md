# ADR 0021: Pumgye authorization model revision

[한국어](../ko/0021-pumgye-authorization-model-revision.md)

Status: **Accepted as architecture — 2026-10-18**. No Pumgye, Hopae, Sumunjang or Hangang code, policy, image or
deployment is changed by this ADR. It revises the authorization *model* owned by
Pumgye ([ADR 0010](0010-pumgye-ownership.md)); the decision-core and snapshot
principles of [ADR 0013](0013-snapshot-membership-scaleout.md) and
[ADR 0016](0016-decision-core-metadata-adapters.md) remain in force. The
Kubernetes representation of this model is [ADR 0022](0022-kubernetes-native-world-package.md).
The decision event schema/exporter is ADR 0019 and the unified console is ADR 0020
(both being written in parallel); this ADR defines the explain API they consume.

Quality bar: the target is a commercial authorization product comparable to the
authorization layers of Okta/Auth0 FGA, Teleport and Cloudflare Access. Acceptance
criteria below are product gates, not proof-of-concept gates.

> Acceptance record (owner-directed resumption, 2026-10-18): adopt the stated
> ownership and bounded/fail-closed design. Implementation exists in varying
> unmerged review units; acceptance is not completion, release, deployment,
> retention-policy activation or a conformance claim. Context below is the
> historical design baseline. Open questions and phased acceptance gates remain
> explicit backlog; see [current roadmap](../ENTERPRISE_ROADMAP_2026-10-18.md).

## Context: verified defects in the current model

Source of truth for this section: Pumgye `849ca90` `crates/pumgye-core/src/lib.rs`
lines 14–137 (`Policy`, `Service`, `Resource`, `Role`, `Network`), role resolution
and compiler at lines 230–440, evaluation at lines 447–510, `docs/SERVER.md` and `docs/KUBERNETES.md`.

| # | Defect | Evidence |
| --- | --- | --- |
| D1 | Assignments are per individual subject ID only; no group subject. LDAP/OIDC groups cannot be used. | `Service.users/workload_users/human_users: BTreeMap<String, Vec<String>>`. Only the separate Kubernetes-API mapping (`kubernetes_authorization.rs`) has `required_groups`. Hopae lists `groups` as *later* (Hopae `docs/ARCHITECTURE.md`), and its LDAP document already states that groups need an explicit Pumgye mapping. |
| D2 | One concept, three subject maps. `users` accepts any `name()` string, so it mixes legacy human subjects, `s_` service principals and `k8sapi:` API subjects. | `users`, `workload_users` (`s_` + 48 hex), `human_users` (`human1:` + 64 hex). The kind-collision test in WORKLOAD_WORLD_QUALIFICATION.md exists precisely because the same `s_` string can appear in two maps with opposite rights. |
| D3 | Roles are defined inside each service; an identical "reader" role is repeated N times. | `Service.roles: BTreeMap<String, Role>`; `resolve_role` resolves inheritance only within one service. |
| D4 | Information classes appear on both roles and resources — RBAC plus an ad-hoc MLS — overlapping with the designed Catalog authority ([CATALOG.md](../CATALOG.md), ADR 0003). | `Role.information_classes`, `Resource.information_class`, one global 64-entry `information_classes` vocabulary used as an unordered bitset. |
| D5 | `networks` CIDR→role duplicates Sumunjang's ownership of IP sets: two components answer "is this IP allowed". | `Service.networks: Vec<Network{cidr, roles}>` compiled into a Pumgye `PrefixTrie`; Sumunjang owns allow/block/ASN pools in its own radix index (Sumunjang `docs/DESIGN.md`). |
| D6 | Assignments carry no expiry, reason, granter or approval; there is no explicit deny. | `Vec<String>` of role IDs; rights are only unioned (`Rights::union`). A more specific `guest` network entry is the only subtractive mechanism. |
| D7 | Orphaned assignments: deleting a Hopae subject leaves Pumgye rows; no reconciliation; the console can only show opaque hashes. | No Hopae lifecycle feed is consumed; subjects are hashes (`human1:`/`s_`). See also the H2a subject-lifecycle proposal ([ko](../ko/2026-10-16-human-subject-lifecycle.md)). |
| D8 | No administrative explain/dry-run. `POST /v1/decision` requires the *decision* credential and returns only `allow`, `reason`, `revision`. | Pumgye `docs/SERVER.md`. ADR 0019/0020 need a simulator. |
| D9 | AAL vocabulary is 0–3 in Pumgye, but Hopae issues only AAL1/AAL2 for humans and AAL0 for machines; AAL3 is being added by a separate passkey workstream. | `minimum_aal <= 3` in `resolve_role`; Hopae `sessions.aal` "1 or 2". |
| D10 | Hard limits of 64 permissions per service and 64 classes, 65,536 total assignments. | `vocabulary()` and `compile()` bounds. |

Sound properties that must be preserved: deterministic compiled evaluation over an
immutable `ArcSwap` snapshot; no request-time DB call; guest by default; Sumunjang
denial dominates; enforced-Guard requirement cannot be satisfied by observe/
unavailable evidence; unknown service/action/class denies; revision floors and
CAS publication; bitset hot path.

## Decision

Pumgye adopts a **principal / group / role-template / binding** model with
explicit deny, condition references to other owners' vocabularies, and
assignment lifecycle metadata. The compiled snapshot remains bitset based and
allocation-free on the hot path. Ownership is narrowed:

| Concept | Owner after this ADR | Pumgye holds |
| --- | --- | --- |
| Principal identifiers (human, service, workload) | Hopae | References only (opaque stable IDs) |
| Groups and memberships (local, LDAP `memberOf`, OIDC `groups` claim) | Hopae | Group references in bindings; a membership projection in the snapshot |
| Information class vocabulary and resource labels | Catalog (ADR 0003, CATALOG.md) | Per-template **clearance ceiling** only |
| Network zones (named prefix/ASN sets) | Sumunjang | Zone references in conditions and service ceilings |
| Role templates, service permission vocabularies, bindings, denies, access requests | Pumgye | Authoritative |
| Route → service/resource/action binding | Hangang (Catalog binding) | — |

### Data model sketch

Illustrative, version 2 of the policy document. Field names are normative intent;
the JSON schema is produced in P0 with valid and adversarial examples.

```text
Principal  = { kind: human | service | workload, ref: PrincipalRef }
PrincipalRef (Hopae-owned, opaque, never reused):
  human     "human1:<64 hex>"                 (existing HumanSubject form)
  service   "s_<48 hex>"                       (existing Service form)
  workload  "wk2:<64 hex>"  = H(issuer, cluster, namespace, serviceAccount name, serviceAccount UID)
            (new, ServiceAccount-scoped; Pod UID is an audit attribute only — see ADR 0022)
GroupRef  = "grp1:<26 crockford>"  Hopae-owned; carries source = local | ldap | oidc,
            source key (DN / claim value) is Hopae metadata, never in Pumgye.

RoleTemplate {
  id: "reader"                      // global namespace, versioned with the document
  permissions: ["read", "list"]     // abstract permission names
  inherits: [TemplateId]            // <= 8, acyclic
  clearance_ceiling: { level: "confidential", compartments: ["finance"] }
  minimum_aal: 0..3
  requestable: { approvers: [GroupRef], max_duration: "8h" } | null   // JIT (P2)
}

ServicePolicy {
  id: "orders"
  permissions: ["read","list","write","admin", ...]   // service vocabulary
  permission_map: { "<template permission>": "<service permission>" }  // default identity
  resources: catalog references (labels come from Catalog, not from here)
  network_ceiling: [ { zone: ZoneRef, max: TemplateId | "guest" } ]   // migrated `networks`
  require_guard: bool                                  // unchanged default true
  authorization_context: network_and_guard | kubernetes_api  // unchanged
}

Binding {
  id: "bnd_<ulid>", effect: allow | deny
  subjects: [Principal | GroupRef]          // 1..64
  role: TemplateId            (allow)       // deny uses `permissions` or `all`
  permissions: [..] | "all"   (deny)
  scope: { services: [ServiceId] | { selector: labels } | "all" }
  conditions: {
    zones: [ZoneRef] | "any",               // Sumunjang-owned names
    minimum_aal: 0..3,
    not_before, expires_at                  // RFC 3339, authority clock
  }
  metadata: {
    reason (required for allow in production mode), granted_by (authenticated
    actor, never client supplied), approval_ref (AccessRequest ID or external
    ticket reference), source: native | kubernetes:<uid> | jit:<request id>,
    created_at, revision
  }
}
```

Group membership is supplied by Hopae as a **membership projection**: a revisioned,
signed export of `principal → [GroupRef]` restricted to groups referenced by the
current Pumgye document (the "relevant group vocabulary", which Pumgye publishes to
Hopae). Pumgye never reads LDAP or OIDC directly and never trusts group names from
request headers or tokens forwarded by Hangang.

### Evaluation semantics and precedence

Evaluation is total and ordered. The first terminal outcome wins; the reason code
is the stage that produced it (codes extend the existing `Decision` enum).

1. **Fences:** snapshot present and within its freshness bound (ADR 0022 for
   Kubernetes mode, ADR 0013 otherwise); request `minimum_revision` satisfied;
   membership and zone projections at or above the revisions the snapshot was
   compiled against. Otherwise `Unavailable` (503, never guest-to-allow).
2. **Context:** unknown service → `UnknownService`; context mismatch →
   `PermissionDenied` (unchanged).
3. **Sumunjang:** `Deny` → `GuardDenied`; `require_guard` and not `EnforcedAllow`
   → `GuardUnavailable` (unchanged; Sumunjang denial dominates everything).
4. **Catalog:** resolve resource/action → permission bit and the Catalog label
   (level, compartments). Unknown action → `PermissionDenied`; unknown or `unknown`
   class → `ClassDenied`.
5. **Principal:** resolve the authenticated principal (kind from Hopae typed
   evidence, never from the string prefix alone; a kind/prefix mismatch denies).
   No entry and no relevant group → `Guest`.
6. **Explicit deny:** any deny binding matching principal-or-group, service,
   permission, zone and validity window → `ExplicitDenied`. **Deny overrides any
   allow**, including allows from more specific scopes.
7. **Allow set:** union of allow bindings (direct and via groups) whose validity
   window contains authority time and whose zone condition intersects the request's
   zone set. Empty union → `Guest` (no grant) or `NetworkGuest` (grants exist but none
   match the zone).
8. **Network ceiling:** intersect with the service ceiling selected by the
   most-specific matching ceiling zone (preserving today's longest-prefix
   override, including a more specific `guest` ceiling). No matching ceiling →
   `NetworkGuest`. Ceilings can only reduce rights.
9. **Permission:** requested bit absent → `PermissionDenied`.
10. **Clearance:** resource level must be ≤ the maximum clearance ceiling among the
    *contributing* templates that grant the requested permission, and resource
    compartments ⊆ that template's compartments → else `ClassDenied`. Clearance is
    evaluated per granting template, not as an independent union of classes, so a
    `reader@public` plus `admin@internal` cannot yield `read@internal` unless the
    internal template itself grants `read`.
11. **Assurance:** presented AAL ≥ max(contributing template, binding condition,
    resource minimum) → else `AssuranceDenied` with the required AAL returned as an
    obligation so Hangang can trigger Hopae step-up.
12. `Allow`.

Properties: default deny; deny overrides allow; network and Guard can only
reduce rights; time-bound rights are checked against the authority's monotonic
clock mapped to wall time at compilation (ADR 0018 rules apply to cross-host
time); no evaluation step reads request headers, tokens or client-supplied classes.

### AAL alignment

AAL 0 = non-human (service/workload) evidence; AAL 1–3 follow NIST SP 800-63B
assurance levels as issued by Hopae. Hopae currently issues AAL1/AAL2; AAL3
(hardware-bound, phishing-resistant authenticator, verifier-impersonation
resistant) arrives with the passkey workstream. A binding/template/resource
requiring AAL3 before Hopae advertises AAL3 capability compiles with an
`UnsatisfiableAssurance` warning visible in status and explain output; it is never
downgraded. Hopae's capability advertisement is part of the membership projection
header. Human principals cannot satisfy AAL0-only machine bindings and vice versa:
bindings are kind-checked at compile time.

### Explicit deny and break-glass

Deny bindings support incident response ("deny `all` on `orders` for group X")
without editing grants. Emergency deny publication uses the ordinary CAS path but
is prioritized in snapshot distribution (ADR 0022 fast-path revocation). There is
no "break-glass allow" that bypasses deny; emergency access is a JIT grant with
approval and audit (P2).

### Assignment lifecycle and JIT access

- `expires_at` / `not_before` are enforced in the hot path by a single integer
  comparison against the snapshot's authority-time base; the compiler also
  schedules a recompile at the next expiry boundary so expired entries are removed
  and status reflects it. A binding without `expires_at` is permanent and must have
  a reason in production mode.
- `granted_by` is the authenticated administrator identity from the publication
  transport (today: client-certificate fingerprint; after ADR 0009/0020: the
  delegated Hangang console actor). It is never accepted from the document body.
- **JIT access requests (P2):** `AccessRequest {requester, template, scope,
  duration ≤ template.max_duration, justification}` → approval by a member of
  `requestable.approvers` (requester cannot self-approve; two-person rule optional)
  → Pumgye creates a time-bound binding with `source: jit:<id>` and `approval_ref`.
  Expiry, revocation and every state transition are audited (ADR 0019 events).
- **Access reviews (P2):** periodic certification campaigns over bindings
  (keep/revoke), using the "who-can"/"what-can" queries below.

### Orphan reconciliation and display names

Hopae publishes a subject lifecycle feed (`created`, `disabled`, `enabled`,
`deleted`, `merged{from,to}`) with a monotonic revision through its outbox
(ADR 0013), plus group lifecycle and membership changes. Pumgye consumes it:

- `deleted`: bindings whose only subject is the deleted principal become
  **orphaned** — excluded from compilation immediately, retained read-only for the
  audit retention period, shown as orphaned in the console, purgeable by an admin.
- `disabled`: Hopae already refuses authentication; Pumgye marks the binding
  `subject_disabled` (no rights change needed, shown in reviews).
- `merged`: never auto-transfers rights; produces a review item.
- Lost events are detected by watermark comparison and a periodic full reconcile
  (bounded, off the request path). Unresolvable references fail publication of new
  bindings (`ResolvedRefs=False`), never silently accept them.

Pumgye stores no names or e-mail addresses. The console resolves display names
through a batched Hopae directory lookup with the administrator's delegated
authority; principals the administrator may not view render as opaque IDs.

### Administrative explain and simulation API

A separate administrative API (admin mTLS / delegated console actor; never the
decision credential) on the same compiled core:

- `POST /v2/admin/explain` — input: principal (or hypothetical principal with
  explicit groups), service, resource+action or permission, IP or zone set, AAL,
  simulated Guard evidence, snapshot selector (`current` | revision | candidate ID).
  Output: the `Decision`, reason code, required obligations, and an **ordered stage
  trace**: for each stage of the evaluation list above, the input, the matched
  binding/template/ceiling/deny IDs with provenance (source, revision, granted_by),
  and the outcome.
- `POST /v2/admin/candidates` + `POST /v2/admin/candidates/{id}/diff` — compile an
  unpublished document and return the set of (principal, service, permission)
  rights that change versus the current snapshot, bounded and paginated.
- `GET /v2/admin/who-can?service&permission[&zone]` and
  `GET /v2/admin/what-can?principal` — reverse and forward effective-rights queries
  for reviews.

Implementation rule: explain uses **the same evaluation function**, generic over a
trace sink. The production path is instantiated with a zero-sized `NoTrace` sink
so the trace compiles away; explain uses a bounded `VecTrace`. Parity tests
compare explain decisions with PPG1/HTTP/gRPC decisions over the same corpus.
Explain requests are rate-limited, audited and never cached as permits.

### Compiled snapshot impact

The hot path stays allocation-free, lock-free and DB-free:

- Templates are resolved at compile time into per-service permission bitsets via
  `permission_map`. Per-service vocabulary grows from `u64` to a fixed
  `[u64; 4]` (256 permissions); the hot path still tests one word.
- Principal lookup: one `HashMap<PrincipalRef, PrincipalEntry>` per snapshot
  (instead of three maps per service). `PrincipalEntry` holds a contiguous slice
  range into a flat `Vec<GrantEntry>` and a `GroupMask` (`[u64; 4]`, up to 256
  policy-relevant groups per snapshot shard).
- `GrantEntry { service: u16, allow: PermMask, deny: PermMask, zones: ZoneMask(u64),
  clearance: (level u8, compartments u64), min_aal: u8, valid: (u64, u64) }` —
  `Copy`, fixed size; evaluation iterates a bounded slice (≤ 64 entries per
  principal per service after compile-time merging) and the group entries for set
  bits of the mask (≤ 256, typically few).
- Zone set: one Sumunjang-owned prefix trie lookup per request produces a
  `ZoneMask` and the ceiling winner; it replaces today's per-service `PrefixTrie`
  and `hosts` map, so cost is unchanged or lower.
- Bounds (P0 product limits, validated at compile): 1,048,576 principals with
  direct bindings; 65,536 groups (256 relevant per service); 4,096 services;
  1,024 templates; 1,048,576 bindings; 64 zones per service ceiling; snapshot
  compile ≤ 2 s and ≤ 1 GiB RSS at limits on the reference 8-core host, measured
  and published before GA. Incremental compilation (per-service shards) is a P1
  optimization if the full compile exceeds budget.
- Existing performance evidence (138–142k single decisions/s, Pumgye `0409a7a`)
  is the regression floor: v2 must stay within 10% at equal cardinality.

### Wire and transport compatibility

PPG1/HTTP/gRPC request shape is unchanged in P0: subject string, IP, permission,
class, AAL, Guard evidence. Principal kind is taken from Hopae typed evidence that
Hangang already carries; the class field becomes advisory and must equal the
Catalog label or the request is refused (no client-authoritative classification).
Reply codes are extended (`ExplicitDenied`, `Unavailable`) with older peers
receiving the nearest existing deny code. A PPG2 frame adding zone mask and
required-AAL obligation is P1 and negotiated by ALPN.

### Compatibility with Kubernetes authoritative mode

In Kubernetes mode (ADR 0022) the same model is expressed as `AccessRoleTemplate`,
`AccessPolicy` and `AccessBinding` objects in `world.hangang.dev`, with subjects
`ServiceAccount{namespace,name}`, `Group{ref}` and `Principal{kind,ref}`. The
world controller compiles those objects into the identical v2 document; Pumgye
accepts it as a signed snapshot and rejects native writes (existing sole-writer
marker semantics). The current explicit RBAC-to-application mapping
(`kubernetes_authorization` / `--kubernetes-*` source) is retained as an
`observe`/import adapter only; Kubernetes RBAC is not the application authority.
The `kubernetes_api` authorization context and SAR server are unchanged and
deferred (ADR 0022).

## Migration from policy version 1

A deterministic converter (`pumgye migrate v1-to-v2`) produces a v2 document plus
proposals for other owners, and a report. Cutover is gated by shadow evaluation.

1. **Roles → templates:** each `service.roles[r]` becomes template `<service>.<r>`;
   structurally identical roles across services are reported as merge candidates
   (`reader`), merged only by administrator confirmation.
2. **Subjects:** `human_users` → `human`; `workload_users` → `workload` (legacy
   Pod-bound form, see step 5); `users` entries are classified by Hopae lookup:
   `s_` registered service → `service`; `human1:` → `human`; `k8sapi:` stays in the
   `kubernetes_api` context; anything unresolved is reported and **not migrated**
   (fail closed). The kind-collision case (same `s_` in two maps) becomes two
   bindings with different kinds, preserving today's separation.
3. **Networks → zones + ceilings:** each `networks[i]` CIDR becomes a Sumunjang
   zone proposal `legacy.<service>.<n>` (submitted to Sumunjang, the owner) and a
   `network_ceiling` entry with the role mapped to its template. Longest-prefix
   override semantics are preserved by the ceiling rule.
4. **Classes:** `information_classes` → Catalog vocabulary proposal;
   `resources[].information_class` → Catalog labels. A role's class set becomes a
   clearance ceiling only if it is downward closed in the Catalog order; otherwise
   the converter emits a compartment proposal or a review item. No silent widening.
5. **Pod-bound workload grants:** subjects derived from Pod UID are mapped to the
   ServiceAccount-scoped `wk2:` principal **only** when the administrator confirms
   the namespace/ServiceAccount (from the existing workload mapping file); otherwise
   they are kept as legacy entries that expire with the Pod and are flagged deprecated.
6. **Shadow and cutover:** run v2 in observe mode beside v1 on live traffic and on a
   generated corpus (every principal × service × permission × ceiling zone ×
   class × AAL boundary). Cutover requires zero unexplained mismatches over a
   7-day window (or the operator-approved window) and an explicit approval record.
   Rollback = republish v1 document (kept for 90 days) with a higher revision.

## Alternatives considered

- **Cedar as the core engine.** Attractive: Rust, formally analysable, forbid-overrides-permit,
  ABAC. Rejected for the gateway hot path: per-request entity construction and policy
  interpretation allocate and scale with policy count, which conflicts with the
  bitset/100k-decisions-per-second design and ADR 0016's "no generic interpretation
  on the hot path". Adopted ideas: deny-overrides semantics, schema validation,
  analysis. Kept open: Cedar export for offline verification of compiled policies (P2).
- **OpenFGA / Zanzibar-style ReBAC.** Excellent for object-level sharing
  (document/folder/tenant graphs) with consistency tokens. Rejected as the core:
  checks are graph traversals over a tuple store, requiring a datastore round trip or
  large caches and Zookie-like consistency; our decision is coarse
  (service × role × zone × class × AAL) at gateway rate. ReBAC remains a candidate
  application-level adapter behind ADR 0016's typed resource contract.
- **OPA/Rego.** General purpose, widely deployed, but evaluation cost and memory are
  policy-dependent and non-deterministic in bounds; rejected for the core, acceptable
  for admission-time validation if ever needed.
- **Keep v1 and add a group map.** Minimal change, but leaves D2–D7 and the ownership
  overlaps with Catalog and Sumunjang. Rejected.
- **Pumgye owns groups.** Would make Pumgye a second directory with its own
  lifecycle and LDAP/OIDC connectors. Rejected: identity and groups are Hopae's
  (ADR 0001/0002).
- **Sumunjang returns zone membership in its evidence instead of Pumgye importing
  zone definitions.** Removes the second evaluator but couples PPG and HGD wire
  revisions and does not help services with `require_guard=false`. Deferred to the
  PPG2/HGD revision (P1 evaluation); P0 imports the Sumunjang-owned zone snapshot
  read-only, so there is still one *owner* of IP sets.

## Phased plan and acceptance criteria

**P0 — model and core (blocking ADR 0022 P0):**
- v2 schema, valid/adversarial examples, compiler, evaluator with deny/groups/
  templates/zones/clearance/validity, explain (`NoTrace`/`VecTrace` parity),
  candidate diff, v1→v2 converter and shadow mode.
- Hopae: membership projection + subject lifecycle feed (local groups, LDAP
  `memberOf`, OIDC `groups` claim mapping), relevant-group vocabulary input.
- Sumunjang: `NetworkZone` ownership and zone snapshot export.
- Gates: property tests (deny monotonicity, ceiling-only-reduces, no rights
  without binding, kind isolation, expiry), adversarial fixtures (group spoofing
  via header, orphan, AAL3 unsatisfiable, class header mismatch), v1/v2 shadow
  parity on the existing qualification corpus, performance within 10% of
  `0409a7a` at equal cardinality and the published bound measurements, real
  four-component request chain on the remote k3s (ADR 0022 gates).

**P1 — operations:**
- Console (ADR 0020) binding editor with impact diff, who-can/what-can,
  orphan/disabled views, display-name resolution; decision events with stage
  trace sampling (ADR 0019).
- PPG2 (zone mask, AAL obligation), incremental compile, reason-required policy.
- Gates: browser qualification of edit → diff → publish → explain; audit
  completeness; revocation of a group membership in Hopae removes access within
  the ADR 0022 revocation SLO.

**P2 — governance:**
- JIT access requests with approval policies, access review campaigns, Cedar
  export verification, ReBAC adapter evaluation.
- Gates: approval separation (no self-approval), expiry enforcement under clock
  tests (ADR 0018), campaign evidence export.

GA requires P0 and P1 gates passed on the released, signed artifacts, documented
upgrade from v1 with rollback, and backup/restore of policy and audit.

## Consequences

Positive: one principal model, group-based administration, reusable roles,
single owners for classes and network sets, auditable assignment lifecycle,
deny for incident response, explainability required by the console and exporter.
Costs: Hopae must ship groups, membership projection and lifecycle feed; Sumunjang
must ship zones; a v2 schema and converter; cross-owner revision fences add
`Unavailable` cases that must be monitored. The converter can refuse ambiguous v1
documents, which requires administrator work before cutover.
