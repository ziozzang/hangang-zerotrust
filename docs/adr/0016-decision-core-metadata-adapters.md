# ADR 0016: Domain decision cores, metadata backbones and pluggable adapters

[한국어](../ko/0016-decision-core-metadata-adapters.md)

Status: accepted direction; generic metadata tables, Kubernetes inbound delegation
and DBMS enforcement adapters are not implemented. Current Pumgye service matrices,
Hopae authentication and Sumunjang network decisions provide the existing baseline.

## Decision ownership and storage

Hopae, Pumgye and Sumunjang are decision cores, not merely importers of another
system's permission model. Hangang, Kubernetes, DBMSs and other enforcement clients
query these cores through authenticated adapters. A backing database owns durable
metadata; each domain core validates, compiles and publishes its in-memory view.
Storage authority and decision authority are separate responsibilities. Selecting
Kubernetes resources as a storage/source mode does not replace domain decision
ownership with Kubernetes RBAC. Native semantics still constrain adapters.

The baseline is database metadata -> background validation/compilation -> immutable
memory snapshot -> decision -> enforcement. Sillok is an optional ontology connector,
not a required store, request dependency or synchronous permission oracle. Analytics,
LLMs and automation cannot write live permission tables without owner validation.

Metadata represents entities and relationships, including identity/provider links,
resource/action/role/class assignments, tenant scope, network sets and evidence,
source ownership, revisions, validity and revocation. This is a deterministic domain
model with ontology-like relationships, not an arbitrary graph traversal per request.
Each domain has a sole writer; do not share multi-writer business tables among cores.
Secrets are references, not credential values in metadata or adapter output.

| Owner | Logical metadata relations | Decision |
| --- | --- | --- |
| Hopae | identities, providers, credentials references, bindings, sessions, assurance | authenticated identity and bounded evidence |
| Pumgye | subjects, resources, actions, roles, assignments, classes, conditions, source bindings | permission for a typed resource/action/context |
| Sumunjang | network prefixes, network identities, risk facts, rules, scope, validity | network admission and risk evidence |
| Hangang | routes, enforcement references, adapter bindings | enforcement of authenticated core decisions |

Logical relations do not prescribe one shared physical SQL schema. Define migrations,
foreign references, tenant/domain ownership and transactional revision/outbox changes
before implementing each database backend. Snapshot builders read consistent commits,
apply deltas or rebuild off the request executor, and atomically replace complete
validated snapshots. Failed or partial candidates never become grants. Reconnects,
missed notifications and replica startup require revision/epoch reconciliation and
bounded freshness; a cache is not permission to serve stale authority indefinitely.

## Resource abstraction and adapters

Pumgye resources are not limited to route/service IDs. A catalog binding may identify
an API operation, Kubernetes object/subresource, database/schema/table, or another
explicitly supported resource type. Resource incarnation, tenant, action vocabulary,
class and required evidence are owner-defined. Names alone cannot survive object
replacement as identity. Existing HTTP-only draft catalog bindings and service-based
runtime policies must be versioned and extended; they do not already implement this.

An adapter translates authenticated platform context into a bounded typed request,
queries the owning core and enforces its response. Same-process integration may call
pure cores over immutable snapshots; distributed integration uses pooled authenticated
binary transport. Adapters declare supported resource types, actions and obligations,
trusted context sources, peer identity, source revision, capabilities and failure mode.
Unknown mappings, untrusted attributes and unsupported obligations deny. A plugin
cannot turn a client-supplied role/class/network claim into authenticated evidence.
Adapter ABI/version, bounded loading, isolation and lifecycle need explicit contracts.

Do not encode every resource as a guessed service ID or invent an IP to satisfy the
current protocol. Missing original client network context is explicit missing evidence.
A policy requiring it denies; another scope may explicitly select different evidence.
Row/column filters or masking need typed obligations and a capable database enforcer.
A boolean allow alone cannot claim those controls were applied.

## Kubernetes as a decision client

Inbound authentication can use Hopae through a TokenReview webhook adapter; inbound
API authorization can use Pumgye through a SubjectAccessReview webhook adapter.
Sumunjang supplies applicable network evidence; admission and CNI are distinct
integration points and cannot replace read authorization. Current outbound TokenReview
verification and RBAC collection are not these inbound webhook implementations.

Authorizer order and failure policy are part of enforcement. An earlier RBAC Allow
can bypass a later webhook; protected scopes need qualified ordering and explicit
failure denial. Short or disabled API-server decision caches must preserve revocation
requirements. The webhook does not automatically receive original client IP; do not
substitute the API-server peer IP or trust unsigned user.extra values. Prevent callback
loops between Hopae token verification and an API-server token webhook. Qualify control
plane bootstrap/recovery independently before changing an existing cluster's flags.

References: [Kubernetes authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/),
[webhook authorization](https://kubernetes.io/docs/reference/access-authn-authz/webhook/),
[token authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/).

## PostgreSQL and other DBMS clients

PostgreSQL can be the metadata backbone and independently an enforcement target.
For the latter, investigate Hopae-backed OAuth validator modules for connection
identity, Pumgye-backed executor/utility hooks for object/action controls, and native
GRANT/RLS or a qualified extension for table/row/column obligations. Sumunjang's
connection evidence remains separate from a database role. A protocol proxy is an
alternative adapter, not proof that all SQL execution is intercepted.

Do not query a remote core once per row. Compile accepted filters into native database
plans/policies and authorize at the appropriate statement/transaction boundary.
Prepared statements, role changes, pooling, functions, views, DDL, COPY and policy
revocation during long transactions need explicit qualification. Native PostgreSQL
superuser/BYPASSRLS and owner behavior must be included in the enforcement scope.
An adapter cannot silently widen permissions that native database controls refuse.
No PostgreSQL plugin or inbound database enforcement is shipped by this ADR.

References: [PostgreSQL OAuth validator design](https://www.postgresql.org/docs/18/oauth-validator-design.html),
[row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html),
[executor permission hooks](https://github.com/postgres/postgres/blob/master/src/include/executor/executor.h).
Pin and qualify supported DBMS major versions rather than assuming a stable hook ABI.

## Additional gRPC transport

gRPC is an additional typed transport over the same domain decision cores and
snapshots, alongside HOP1/PPG1/HGD1 and same-process calls. It is not implemented
by this ADR. Define versioned protobuf services for authentication, authorization
and network evidence, with bounded messages, explicit unavailable/deny/allow states,
trusted caller/evidence binding, minimum revisions and expiry. Unspecified/default
fields cannot become permission. Keep management and policy publication separate.

Use reused HTTP/2 channels, mTLS, per-method caller authorization, enforced deadlines,
cancellation, bounded concurrent streams and message/decompression limits. No request
SQL lookup or extra policy engine. Retry only qualified idempotent queries within the
original deadline; outage must not cause replay storms or stale cached grants. Compare
native and gRPC results against the same immutable snapshot, including denied and
missing evidence cases, and measure framing/adapter overhead separately.

Kubernetes Pods can call gRPC through Services. API-server authentication and
authorization webhooks still use HTTP/JSON TokenReview/SubjectAccessReview and need
an adapter; gRPC alone is not that integration. An Envoy-compatible ext_authz service
is a separate proposed adapter with explicit header/context trust and failure denial.
Do not label a custom protobuf API as Envoy compatible without protocol qualification.

References: [gRPC performance](https://grpc.io/docs/guides/performance/),
[deadlines](https://grpc.io/docs/guides/deadlines/),
[Envoy external authorization](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/ext_authz/v3/ext_authz.proto.html).

## Performance and acceptance

Preserve the fast path: no request-time database/ontology/analytics call, no policy
compilation, generic graph traversal or JSON/SQL parsing in the core. Use compiled
IDs/bitsets, bounded prefix/index lookup, immutable snapshot loads and existing pooled
binary mTLS. Plugin translation is bounded and excludes management writes. Revisions,
expiry and failure fences are required even when minimizing allocations and copies.
Metadata caches and short decision leases are different; cached metadata is validated
by source freshness, while reusable decisions remain constrained by evidence and
revocation deadlines. Near-zero overhead is an optimization target, not a measured
claim from a schema or microbenchmark. Functional qualification comes first here.

Acceptance requires a published typed resource/adapter contract, database commit and
snapshot recovery tests, real inbound Kubernetes decisions, and real DBMS enforcement
including denial, replacement, source outage and revocation. Measure adapter overhead,
allocations, core latency, pooled RPC and whole request latency separately under the
original throughput targets. Existing HTTP/native qualification cannot substitute for
Kubernetes API or PostgreSQL enforcement qualification.
