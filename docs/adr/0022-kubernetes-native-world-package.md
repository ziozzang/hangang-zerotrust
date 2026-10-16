# ADR 0022: Kubernetes-native Hangang World package

[한국어](../ko/0022-kubernetes-native-world-package.md)

Status: **proposed**. Supersedes in part [ADR 0015](0015-kubernetes-iam-authority.md)
(source-of-truth wording, authorization lease length in Kubernetes mode, workload
identity granularity, packaging sequence). ADR 0015's ownership rules, RBAC/IAM
semantics and safety invariants remain. Builds on [ADR 0013](0013-snapshot-membership-scaleout.md),
[ADR 0016](0016-decision-core-metadata-adapters.md) and the authorization model of
[ADR 0021](0021-pumgye-authorization-model-revision.md); decision events are ADR 0019
and the unified console is ADR 0020. No cluster, image, chart or production
configuration is changed by this ADR.

Quality bar: a commercial product installable and operable like production-grade
Kubernetes packages (Helm/OCI, signed images, upgrade/rollback, HA, backup) and
comparable in operator experience to Teleport or Cloudflare Zero Trust. Gates below
are product acceptance criteria, not proof-of-concept checks.

## Context: verified current state

Revisions read: Hangang (`hangang-console-plugins`) `d6cb223`, Hopae
(`hopae-hangang-integration`) `519aa58`, Sumunjang (`hangang-safe`) `1300ecb`,
Pumgye `849ca90`, this repository `447e1c9`.

**Packaging.** There is no installable package — no Helm chart or operator. The
only four-server Kubernetes run is the owned test generator
`tools/kubernetes_world_smoke.py` ([KUBERNETES_WORLD_QUALIFICATION.md](../KUBERNETES_WORLD_QUALIFICATION.md)
says "Do not treat this owned test generator as a production deployment bundle").
Fragments: Hangang kustomize (`deploy/kubernetes/deployment.yaml`: placeholder
`registry.example.invalid/hangang:REPLACE_ME`, `emptyDir`, `replicas: 1`); Pumgye
kustomize (`deploy/kubernetes/deployment.json`: `replicas: 1`, `Recreate`, PVC
`pumgye-state`); Sumunjang two YAML templates (`deploy/sumunjang-native-*.yaml`,
`REPLACE_WITH_QUALIFIED_NATIVE_AUTHORITY_IMAGE`, `emptyDir`); Hopae only
`deploy/compose.yaml`. Images are built locally and imported into nodes
([PACKAGING.md](../PACKAGING.md): "Local image creation does not publish a registry
image, sign a release"); Secrets are precreated; there is no cert-manager/SPIRE
integration or certificate rotation; every authority is a single-writer SQLite
replica. On the user's remote test cluster the operating gateway runs outside the
cluster on the host network (k3s-12 README: "hostnetwork를 보존").

**Hangang routing.** `src/ingress.rs` lines 86–87 and 190–191 set `pumgye: None`
and `pumgye_authority: None` for Ingress-generated routes; cached Ingresses keep only
spec, class annotation and status, other annotations are discarded
(`docs/KUBERNETES.md`). "Gateway API resources are not currently reconciled." The
shipped Service has no `type`, so it is ClusterIP with no `externalTrafficPolicy` or
PROXY protocol: Sumunjang IP rules would see SNAT'd addresses behind kube-proxy.
The controller's watch/ownership/status implementation is high quality (oldest-wins
host ownership, bounded caches, relist on 410, readiness by staleness).

**Sumunjang.** Kubernetes `NetworkPolicy`/selector semantics are compiled in
userspace (`crates/guard-core/src/network_policy.rs`, `selector.rs`) for read-only
diagnostics, "not promoted to runtime NetworkPolicy enforcement" (`docs/GRPC.md`).
If promoted, the gateway would be the only enforcement point (north-south), where
Pod-selector ingress rules are close to meaningless and east-west traffic is not
seen. The `SumunjangPolicy` CRD (`policy.hangang.dev/v1alpha1`) is one fixed-name
object fetched by GET every 500 ms with a one-second lease
(`crates/guard-server/src/kubernetes_authority.rs` line 375,
`docs/KUBERNETES_AUTHORITY.md`), with `x-kubernetes-preserve-unknown-fields`
schema, no watch and no status.

**Freshness.** Pumgye Kubernetes-authoritative mode withdraws availability before
each collection and expires the view one second after collection starts
(Pumgye `docs/KUBERNETES.md` ~line 182–209); Sumunjang's CRD source uses the same
one-second lease. An API-server blip, slow list or one invalid object therefore
becomes 503 for all protected traffic. Hangang's Ingress controller uses a 60 s
staleness threshold and keeps serving its last snapshot. Three components, three
freshness semantics.

**Workload identity.** Hopae's subject is a hash over namespace, ServiceAccount
name/UID and Pod name/UID; "another Pod of the same ServiceAccount receives another
subject, and recreated objects do not inherit this pinned grant" (Pumgye
`docs/KUBERNETES.md` ~lines 244–267). Grants do not survive a rollout. Hangang has a
separate static SPIFFE mTLS model (`docs/HTTP_WORKLOAD_MTLS.md`, `allowed_uri_sans`)
— two workload identity models.

**Hopae per-request API calls.** Every workload authentication performs TokenReview
plus partial-metadata GETs of the ServiceAccount and Pod (`src/auth_gateway/kubernetes.rs`
lines 367–395; `docs/KUBERNETES_WORKLOAD.md`: "There is no result cache: every
invocation contacts TokenReview"). Request rate is coupled to API-server capacity.

**SAR authorizer.** Pumgye's SubjectAccessReview server is qualified only against a
disposable API server whose only authorizer is Webhook/Deny
([KUBERNETES_SAR_QUALIFICATION.md](../KUBERNETES_SAR_QUALIFICATION.md)). In a real
cluster an in-cluster Pumgye authorizing the API server that schedules it is
circular, and behind RBAC (earlier allow wins) it adds little.

**Authority ambiguity.** ADR 0015 states both "Kubernetes must be usable as the
source of truth" and "Hangang World owns the domain contracts"; in practice each
component has a different source (Pumgye: RBAC mapping, Sumunjang: one custom
object, Hangang: Ingress, Hopae: configuration files). The user requirement is one
Hangang-integrated native Kubernetes package whose **Hangang World zero-trust
authority is the original domain source**.

**Keep:** fail-closed outcomes; UID/resourceVersion fencing; publish only after a
complete relist; Secret references, never inline secrets; nonroot scratch images
with read-only root and dropped capabilities; least-privilege RBAC; the Hangang
Ingress controller's watch/ownership quality; honest gateway-versus-CNI reporting.

## Decision 1 — authority: World objects are the source, Kubernetes is their store

- A single API group, **`world.hangang.dev`**, expresses the Hangang World domain.
  Name: Kubernetes requires a DNS-subdomain group under a domain the publisher
  controls; the project already uses `hangang.dev` (`policy.hangang.dev` for
  `SumunjangPolicy`). `world` names the domain authority rather than one component,
  so all four owners share one group and one versioning/conversion story, while
  each kind keeps one owning component. *Open item:* confirm registration control
  of `hangang.dev` before v1beta1; otherwise rename before any beta is published.
- In-cluster, **World CRDs are the domain source of truth.** Kubernetes provides
  storage (etcd), RBAC on who may edit, admission, watch and GitOps compatibility.
  Native Kubernetes objects (Namespace, ServiceAccount, Pod, Service, EndpointSlice,
  NetworkPolicy, RBAC) are **platform facts**, consumed but not domain authority.
  Kubernetes RBAC objects are never imported as application permissions (the
  existing mapping becomes an `observe`/import adapter, ADR 0021).
- Component databases become **materialized caches** of the compiled snapshots plus
  data that is not policy (Hopae users, credentials, sessions; audit spool). A
  native DB write to a domain owned by CRDs is refused (existing sole-writer marker).
- `WorldAuthority` (cluster-scoped singleton `default`) declares cluster identity,
  trust domain and per-domain mode `kubernetes | database | observe`.
- **Out-of-cluster deployments** (VMs, Docker, the current operating host) use
  `database` mode: the component DB is the source, and the same `world.hangang.dev`
  schemas are the import/export and GitOps format (`hangang-world apply` CLI talks
  to the domain management APIs with CAS). Precedence: exactly one authority per
  domain per World; never merged; switching mode is an explicit, audited migration
  (export → validate → freeze writer → import → flip marker), with rollback.
  Multi-cluster (P2): one source cluster per World; other clusters run the data
  plane and receive snapshots, they do not author policy.

## Decision 2 — CRD API (`world.hangang.dev/v1alpha1` → `v1beta1` → `v1`)

| Kind | Scope | Owner (compiles/validates) | Purpose |
| --- | --- | --- | --- |
| `WorldAuthority` | Cluster (singleton) | controller | cluster ID, trust domain, per-domain source mode, staleness bounds |
| `WorldIdentityProfile` | Namespaced | Hopae | authentication profile: OIDC/LDAP/local/API-key/Kubernetes-workload/SPIFFE providers by Secret reference, AAL policy, session policy |
| `IdentityGroupMapping` | Cluster | Hopae | maps LDAP `memberOf` DN / OIDC `groups` claim values to Hopae `GroupRef` |
| `AccessRoleTemplate` | Cluster | Pumgye | ADR 0021 role template (permissions, clearance ceiling, min AAL, requestable) |
| `AccessPolicy` | Namespaced | Pumgye | service permission vocabulary, permission map, Catalog resource refs, network ceiling by zone |
| `AccessBinding` | Namespaced | Pumgye | allow/deny binding; subjects `ServiceAccount{namespace,name[,uid]}`, `Group{ref}`, `Principal{kind,ref}`; conditions, expiry, reason |
| `CatalogResource` | Namespaced | Catalog | resource identity, actions, classification label (level, compartments), owner |
| `NetworkZone` | Cluster | Sumunjang | named prefix/ASN sets (replaces raw CIDRs in Pumgye) |
| `NetworkControl` | Namespaced/Cluster | Sumunjang | block/allow/risk rules, admission mode, east-west intent (replaces `SumunjangPolicy`) |
| `ProtectionPolicy` | Namespaced | Hangang | Gateway API **direct policy attachment** (`targetRefs` → `Gateway`/`HTTPRoute`/`GRPCRoute` section): identity profile, AccessPolicy, action mapping (method/path/RPC → action), network enforcement requirement, failure mode |

API rules (all kinds): structural schemas with no `x-kubernetes-preserve-unknown-fields`;
`maxLength`/`maxItems` on every string/list; CEL `x-kubernetes-validations` for
local invariants (e.g. deny bindings may not name a role; `expiresAt > notBefore`;
CIDR syntax with `isCIDR()`; AAL 0–3; guest cannot combine); `status` subresource
with `observedGeneration` and standard conditions `Accepted`, `ResolvedRefs`,
`Programmed`, `Ready` (Gateway API policy status conventions for `ProtectionPolicy`,
including `Conflicted`/`TargetNotFound`); `appliedRevision` and per-authority
acknowledgement in status; printer columns; short names; a `world` category.
Cross-object validation (references, escalation) is the controller's job and is
reflected in status — admission never depends on authority availability.

**Escalation control:** a ValidatingAdmissionPolicy (CEL `authorizer` library)
requires the requesting user to hold the custom verb `bind` on the referenced
`AccessRoleTemplate` to create an allow `AccessBinding`, and `escalate` to change a
template's permissions or clearance — the Kubernetes RBAC escalation model applied
to World objects. Namespace administrators may bind only templates they were
granted; cluster-scoped kinds are platform-admin only. Aggregated ClusterRoles
`world-admin`, `world-editor`, `world-viewer` ship with the chart.

**Versioning:** v1alpha1 may break; v1beta1 and later require a conversion webhook
(served by the controller, HA) and storage-version migration; removal of a served
version only after one minor release with deprecation warnings.

## Decision 3 — one controller, signed snapshots, bounded staleness

- **`hangang-world-controller`** (Deployment, 2+ replicas, leader election by
  `coordination.k8s.io` Lease) runs shared informers over World kinds and the platform
  facts it needs (Namespace, ServiceAccount, Pod metadata, Service, EndpointSlice,
  Gateway API kinds). It validates, resolves cross-references, compiles per-domain
  candidate snapshots (Hopae profiles/groups, Pumgye v2 document per ADR 0021,
  Sumunjang zones/controls, Hangang route/protection table), and writes status.
- Publication: complete relist/informer sync is required before the first
  publication (existing "publish only after complete relist" rule). Snapshots are
  versioned (monotonic revision + content digest + controller epoch), **signed** with
  a controller key (Ed25519, Secret managed by cert-manager or external KMS), and
  delivered over a mTLS subscription stream that each authority opens to the
  controller service (xDS-style: authority dials, controller pushes full snapshot
  then deltas; NACK with reason on validation failure). Authorities verify signature,
  epoch, revision monotonicity and schema version, compile off the request path,
  swap atomically and ACK; ACKs are reported in object status and console.
- **Data plane serves last-good with bounded staleness.** Each authority persists
  the last accepted signed snapshot locally and serves it while
  `age ≤ WorldAuthority.spec.maxSnapshotStaleness` (default 5 min, allowed 1–60 min).
  The controller sends a signed freshness heartbeat (every 10 s) that renews the
  age even when nothing changes. Beyond the bound: fail closed for protected
  traffic (`Unavailable`), with alerting well before. A new Pod without any snapshot
  is not Ready. Authorities hold **no API-server credentials** for policy (Hopae
  keeps a narrowly scoped one only if TokenReview fallback is enabled).
- **Fast-path revocation.** Revocations (binding deleted/denied, emergency deny,
  zone block, ServiceAccount/Pod deletion tombstones, Hopae subject disable) are
  delivered as priority deltas ahead of full recompiles. Product SLO, measured in
  qualification: p99 ≤ 2 s from API commit to enforcement on all Ready replicas
  while the control plane is healthy. Session/credential revocation inside Hopae
  and evidence leases (ADR 0013, `x-hopae-evidence-ttl-ms` ≤ 1 s) are unchanged.
- **Removed from the request path:** the one-second API-server observation leases
  of Pumgye and Sumunjang source modes, and the "withdraw before each collection"
  behavior. This supersedes ADR 0015's "authorization leases at most one second"
  for Kubernetes mode: policy freshness (minutes, explicitly bounded and visible)
  is separated from evidence/revocation freshness (seconds). Hangang's 60 s
  route-staleness readiness rule is aligned: all components report
  `snapshotAge`, `maxSnapshotStaleness` and `appliedRevision` identically.
- Security trade-off, accepted explicitly: during a control-plane partition a
  grant removed in the API may persist up to the staleness bound on partitioned
  replicas. Mitigations: emergency deny can also be pushed directly through the
  domain management API (audited, the controller reconciles it back into a CRD);
  the bound is operator-configurable down to 1 min; partition is alerted.

## Decision 4 — enforcement points

- **North-south: Hangang is a Gateway API implementation.** `GatewayClass`
  `controllerName: hangang.dev/gateway-controller`; reconcile `Gateway`,
  `HTTPRoute`, `GRPCRoute` (P1), `ReferenceGrant`, with Gateway API conformance
  (Core, then selected Extended features) as a release gate. `ProtectionPolicy`
  attaches authentication/authorization/network requirements to Gateway or route
  sections. A Gateway may declare `requireProtection` (via a Gateway-targeted
  `ProtectionPolicy` default): routes without an effective protection policy are
  then `Accepted=False` — never silently published unprotected (ADR 0015 rule).
- **Ingress** remains supported. *Amended 2026-10-17:* `ProtectionPolicy` may
  also target `networking.k8s.io/Ingress` as the supported transitional and
  compatibility path, because most existing clusters declare routes with Ingress.
  The same fail-closed rule applies: with `requireProtection`, an Ingress without
  exactly one effective policy is withheld (`ProtectionRequired`), multiple
  attached policies are refused (`Conflicted` — intentionally stricter than Gateway
  API oldest-wins so a newer, stricter policy is never silently ignored), and
  unresolved references are refused. Ingress without protection is published as
  `access_mode: public` only when `requireProtection` is off. An Ingress host that
  overlaps a protected Gateway listener host is rejected. Gateway API remains the
  primary model.
- **Client IP preservation is required** for any `ProtectionPolicy` that uses network
  conditions. Supported modes: Service `type: LoadBalancer|NodePort` with
  `externalTrafficPolicy: Local`; PROXY protocol v2 from an explicitly trusted LB
  CIDR list; `hostNetwork` DaemonSet for bare-metal edges (the current remote-host
  topology). Mode `none` makes zone-conditioned policies `Programmed=False` with
  reason `ClientAddressUnavailable`. The status condition `ClientAddressPreserved`
  is reported per Gateway.
- **East-west is delegated to the CNI.** Sumunjang is repositioned as (a) the
  north-south IP admission/risk engine at the gateway (unchanged), (b) a **generator**
  that compiles `NetworkControl` east-west intent into `NetworkPolicy`, or
  `CiliumNetworkPolicy`/AdminNetworkPolicy where the CNI supports them (capability
  detected and reported), as owned objects with `managed-by` labels, dry-run diff
  and drift correction, and (c) diagnostics: "would this flow be allowed by current
  NetworkPolicy" explanations. It stops aiming to enforce Pod-selector NetworkPolicy
  at the gateway. Without a supporting CNI, status says so; no enforcement is claimed.
- **Service-to-service L7 (P2, optional):** Hangang as a waypoint/sidecar proxy, or
  an Envoy `ext_authz` adapter for meshes (ADR 0016), using the same decision cores.

## Decision 5 — workload identity and inter-component trust

- **Workload subject = (cluster, namespace, ServiceAccount).** Pod name/UID become
  audit attributes only. Canonical form is the SPIFFE ID
  `spiffe://<trust-domain>/ns/<namespace>/sa/<serviceaccount>`; Hopae's principal
  `wk2:` (ADR 0021) is derived from issuer, cluster, namespace, ServiceAccount name
  and **UID**, so same-name ServiceAccount recreation yields a new principal.
  `AccessBinding` subjects name ServiceAccounts by name; the controller resolves the
  current UID, so intent survives recreation only for whoever can recreate it in that
  namespace (standard Kubernetes trust), while `uid` pins remain available.
- **Verification without per-request API calls:** projected ServiceAccount tokens
  with a dedicated audience (e.g. `world.hangang.dev/<cluster-id>`) and short
  lifetime (≥ 600 s, Kubernetes minimum) are verified **offline** against the
  cluster's OIDC discovery/JWKS (issuer pinned, JWKS cached with rotation and
  bounded refresh), checking audience, expiry, `kubernetes.io` Pod/ServiceAccount
  binding claims. Deletion is handled by controller tombstones: ServiceAccount/Pod
  deletion is pushed to Hopae as a revocation delta (fast path), and Hopae refuses
  tokens bound to tombstoned UIDs. TokenReview becomes an optional fallback with a
  short positive cache (≤ 10 s), not the default per request.
- **Or SPIFFE X.509-SVIDs** issued by SPIRE or cert-manager `csi-driver-spiffe`. Hangang's
  existing workload mTLS (`allowed_uri_sans`) maps the verified URI SAN to the
  **same** workload principal. One identity model, two credential formats.
- **Inter-component mTLS** (Hangang ↔ Hopae/Pumgye/Sumunjang decision and management
  channels, controller ↔ authorities) uses cert-manager `Certificate` resources
  (chart-provided `Issuer` from a CA Secret or external issuer), SPIFFE URI SANs per
  component, short duration (default 30 d, renew at 2/3) and hot reload in every
  component without restart. `tls.mode: external` supports pre-provisioned Secrets
  with the same reload requirement.

## Decision 6 — packaging, HA, upgrade, backup

- **Charts:** `hangang-world` (all four components + controller, toggles per
  component) and `hangang-world-crds` (CRDs, lockstep versions; separate because Helm
  does not upgrade `crds/`), published as **OCI** artifacts and signed. A
  `values.schema.json` validates values; incompatible or incomplete settings fail
  `helm install` (ADR 0015 settings requirement).
- **Images:** multi-arch (amd64/arm64), static nonroot scratch (existing practice),
  published to an OCI registry, **pinned by digest** in chart values, cosign-signed
  with SBOM (SPDX) and SLSA provenance attestations; documented admission
  verification (sigstore policy-controller or Kyverno example).
- **HA and state — decision:** SQLite single-writer is retained **only** for
  single-replica `database` mode (development, small installs). HA uses
  **PostgreSQL** (external, or CloudNativePG when opted in) implementing ADR 0013's
  CAS + transactional outbox adapter for data that is not CRD-owned: Hopae users,
  credential references, groups, sessions; Pumgye/Sumunjang in `database` mode;
  audit spool. In Kubernetes mode Pumgye and Sumunjang hold no authoritative DB;
  they are stateless replicas (N ≥ 2) of signed snapshots. Hangang data-plane
  replicas are stateless; console administration uses Hopae SSO (ADR 0009) with a
  bootstrap local admin only. The controller is active/standby via Lease. Leader
  election for the authorities themselves is not needed because they do not write
  policy in Kubernetes mode.
- **Availability defaults:** PodDisruptionBudgets, topology spread, anti-affinity,
  `maxUnavailable: 0`/`maxSurge: 1`, readiness gated on applied snapshot revision,
  graceful drain (ADR 0013), resource requests/limits, priority class option,
  NetworkPolicies for the World namespace itself, ServiceMonitor/PrometheusRule.
- **Upgrade/rollback:** N-1 compatibility for snapshot schema, wire protocols and DB
  schema (expand/contract migrations as Helm pre-upgrade Jobs; contract only one
  release later); controller emits the highest snapshot schema all connected
  authorities accept; `helm rollback` to N-1 supported and tested; CRD changes only
  additive within a served version.
- **Backup/restore:** CRDs via GitOps or Velero; PostgreSQL PITR; controller signing
  key, CA and Secrets backup; documented restore runbook with revision/epoch fencing
  (a restored controller starts a new epoch; authorities refuse lower revisions of the
  old epoch without explicit operator reauthorization, ADR 0013).

## Stop / deprecate

| Stop | Replacement |
| --- | --- |
| Pod-UID-bound workload identity as the grant subject | ServiceAccount-level `wk2:`/SPIFFE principal; Pod UID audit-only |
| One-second API-server polling leases (Pumgye RBAC source, Sumunjang `SumunjangPolicy` GET every 500 ms) | Controller informers + signed snapshots + bounded staleness + fast revocation |
| Per-request TokenReview + Pod/SA GET in Hopae | Offline JWKS verification + tombstones; TokenReview optional fallback with cache |
| NetworkPolicy enforcement ambitions at the gateway | CNI policy generation + diagnostics |
| `SumunjangPolicy` fixed-name schemaless CRD | `NetworkZone`/`NetworkControl` structural CRDs (migration tool) |
| Kubernetes RBAC → application permission mapping as authority | `AccessBinding`; RBAC import is observe-only |
| Pumgye SAR authorizer in the package | **Deferred**; code kept, excluded from chart until an out-of-cluster/managed authorizer topology is designed |
| Test generator as deployment path | Helm chart; generator becomes a qualification harness over the chart |

Keep: fail-closed outcomes, UID/resourceVersion fencing, publish after complete relist,
Secret references, nonroot scratch images, least-privilege RBAC, Hangang Ingress watch/
ownership logic (reused for Gateway API), honest gateway-vs-CNI reporting.

## Phased plan

**P0 — installable, functional, single cluster.**
CRDs v1alpha1 with CEL/status; controller with informers, signed snapshot
distribution, bounded staleness and fast revocation; Pumgye v2 (ADR 0021 P0);
Sumunjang zones/controls; Hopae offline JWKS workload verification and tombstones;
Hangang Gateway API (HTTPRoute) + `ProtectionPolicy` + client IP preservation modes;
cert-manager mTLS with hot reload; Helm charts, digest-pinned signed images; SQLite
single-replica mode and PostgreSQL mode for Hopae.

**P1 — production operations.**
HA everywhere (PostgreSQL for all DB modes, N ≥ 2 replicas, PDBs), upgrade/rollback
automation, conversion webhook and v1beta1, NetworkPolicy/Cilium generation, SPIFFE
SVID support, GRPCRoute, console (ADR 0020) for World objects with GitOps-aware
read-only modes, decision events (ADR 0019), backup/restore runbook, Gateway API
conformance report.

**P2 — scale and breadth.**
Multi-cluster World, waypoint/ext_authz east-west L7, JIT access (ADR 0021),
SAR authorizer redesign, load qualification at 10k/100k.

## Migration from the current qualified state

1. Export current native policies (Pumgye v1, Sumunjang policy, Hopae profiles,
   Hangang routes) with `hangang-world export` into World objects; Pumgye v1 goes
   through the ADR 0021 converter. Review reports; nothing is applied automatically.
2. Install CRDs and the controller in `observe` mode: compiles and diffs against the
   running native authorities, publishes nothing. Gate: zero unexplained diffs.
3. Switch one domain at a time to `kubernetes` mode with the writer-marker flip;
   keep the prior DB snapshot for rollback.
4. Replace Pod-bound workload grants by ServiceAccount bindings after confirmation;
   retire `SumunjangPolicy` after `NetworkZone`/`NetworkControl` parity.
5. Move the north-south entry to the Hangang Gateway with client IP preservation;
   the external host-network gateway remains until the in-cluster Gateway passes the
   functional gates, then is retired or becomes a `hostNetwork` Gateway instance.

## Qualification gates

Order: **functional first** on the user-designated remote k3s cluster; **before any
cluster mutation take a fresh cold backup and verify its integrity** (hash/tar
validation, off-host copy) per ADR 0015; preserve existing workloads, DNS and the
operating gateway; owned namespaces only; documented cleanup and rollback. **No load
benchmarks until the functional gates pass.**

P0 functional acceptance (all must pass on released signed artifacts installed by
the chart, not by the test generator):

- `helm install` from the OCI chart with documented values on a clean namespace
  reaches Ready; invalid values fail before any object is created; `helm uninstall`
  leaves CRDs/data per documented policy.
- Protected HTTPRoute request passes Hopae identity, Sumunjang admission and Pumgye
  authorization with real client IP; anonymous, guest, spoofed headers, wrong
  audience/issuer token, wrong ServiceAccount, deny binding and blocked zone are
  refused without backend dispatch; an HTTPRoute without protection under a
  `requireProtection` Gateway is not programmed.
- Rollout of a workload Deployment keeps its access (ServiceAccount identity);
  ServiceAccount deletion/recreation follows the documented rule; Pod deletion revokes
  its token within the revocation SLO.
- Revocation SLO p99 ≤ 2 s for binding deletion, emergency deny, zone block, group
  removal (measured on a functional sample, all Ready replicas).
- API server unavailable for 10 min (with default 5 min bound: verify serving through
  the bound, then fail-closed after it, then recovery); controller killed (standby
  takes over, no data-plane impact); one invalid object (status shows rejection,
  others unaffected, no 503).
- Certificate rotation with no restart and no failed requests; signing key rotation.
- Status: every World object shows `observedGeneration`, conditions and applied
  revision; console shows source, freshness and ACKs.

P1 acceptance additionally: upgrade N-1 → N and `helm rollback` with continuous
functional probes showing no protected-request failures beyond documented drain;
PostgreSQL failover; backup/restore drill into a fresh namespace reproducing
revisions and refusing a stale epoch; generated NetworkPolicies enforced by the
cluster CNI (actual CNI test, reported separately from gateway enforcement); Gateway
API core conformance.

Then load qualification (ADR 0013/0015 targets) on the full chain.

## Alternatives considered

- **One CRD group per component** (`pumgye.hangang.dev`, …). Mirrors code ownership
  but fragments versioning, RBAC aggregation and the console; rejected — ownership is
  per kind, not per group.
- **Each authority watches the API server itself.** No central controller, but every
  component needs API credentials, re-implements relist/fencing, and cross-domain
  references (route → policy → zone) cannot be validated coherently. Rejected.
- **Operator (OLM-style) instead of Helm.** The controller is already an operator for
  World objects; install/upgrade via Helm OCI is the most common distribution channel.
  An OperatorHub bundle can be added later.
- **Keep one-second leases.** Strongest staleness guarantee, but converts any
  control-plane hiccup into a full outage; commercial control planes (xDS, OPA bundles)
  serve last-known-good with bounded staleness. Rejected for Kubernetes mode.
- **Istio/Linkerd as the enforcement layer.** Strong east-west, but adds a mesh
  dependency; supported later via ext_authz/waypoint, not required.
- **In-cluster SAR authorizer now.** Circular bootstrap and low value behind RBAC;
  deferred.

## Consequences

One installable, upgradable, signed package with a clear source of truth and
uniform freshness semantics; enforcement claims match actual enforcement points;
workload grants survive rollouts. Costs: a new controller and CRD API to maintain,
Gateway API conformance work, PostgreSQL adapters (ADR 0013), Hopae JWKS/tombstone
work, and an explicitly accepted bounded-staleness window during control-plane
partitions.
