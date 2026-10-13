# ADR 0013: In-memory authority snapshots and scale-out membership

Status: required direction; fleet/backbone implementation pending. Builds on
[ADR 0012](0012-independent-runtime.md). [한국어](../ko/0013-snapshot-membership-scaleout.md).

## Ownership and memory model

Hopae, Sumunjang and Pumgye each run independent replica sets. Ordinary verification
and decisions read immutable, compiled memory snapshots. The authority's database
backbone owns durable state and publication; nodes do not independently overwrite
one another's business DB. Keep Hopae identities/credentials/sessions, Sumunjang
network policy/evidence and Pumgye roles/classes/assignments in their own domains.
A shared DB infrastructure may host separate schemas/roles, not a shared multiwriter
user/network/authorization model.

Pumgye's local authority already commits policy/revision/audit in SQLite and swaps
an `ArcSwap` compiled view; HTTP and native decisions do not read that database.
This is not yet a fleet DB adapter or membership subscriber. Sumunjang's compiled
network view is an existing baseline. Hopae must add appropriate memory indexes
and invalidation for each verification path; current OIDC/session implementation
does not prove all authentication state is snapshot-backed.

A policy snapshot lasts until a valid replacement or its authority lease expires.
It is different from an individual decision cache, which may last only 1–5 seconds
and must bind authority epoch, revision, service, principal/evidence and request
scope. No expensive DB, ontology, LLM or analytics operation goes on the ordinary
hot path. Private credential material stays in protected domain storage; do not
broadcast raw API keys, passwords or provider/session secrets in public snapshots.
Hopae needs protected local verification indexes and explicit per-session/token
revocation generations/tombstones; policy snapshots alone do not revoke sessions.

## Durable publication and replica catch-up

1. The domain publication authority authenticates scope and performs bounded CAS.
2. A DB transaction commits the state, monotonically increasing revision, digest,
   audit receipt and change/outbox record together.
3. Replicas receive watch notifications, fetch authenticated domain state, validate
   epoch/revision/hash/schema, compile off the request executor and atomically swap.
4. Replicas acknowledge the compiled revision only after publication. Loading nodes
   cannot claim ready based solely on a DB connection or heartbeat.
5. A gap, overflow, unknown epoch or reconnect forces authoritative resynchronization.
   Notifications are hints; periodic watermark checks detect lost notifications.

Use a DB-backbone adapter rather than hard-coding one deployment. Start with local
single-owner storage; PostgreSQL CAS plus transactional outbox and authenticated
snapshot/change reads is a candidate distributed adapter. Transport/discovery
adapters can evolve without moving business authority into Hangang. No distributed
adapter is implemented by this ADR. Database failover must preserve authority epoch
and revision watermark; a restored or reinitialized authority needs fencing and
explicit reauthorization, never a silent revision reset.

## Membership separate from policy revision

Use a scoped membership authority with a generation and bounded lease. Its records
identify domain authority/epoch, node ID/incarnation, endpoint/protocol, TLS service
identity, capacity, readiness/compiled revision, health and lifecycle state.
The membership generation, policy revision and node incarnation are separate values.
A DNS result or a live socket is not membership, readiness or permission evidence.
[Draft membership schema](../../schemas/membership.schema.json) and
[synthetic snapshot](../../examples/membership.json) define the bounded full view.
They are metadata examples, not signed/live credentials.

- **Join:** register authenticated node -> bootstrap/catch up -> compile -> acquire
  valid membership/domain lease -> announce ready at the required revision.
- **Scale-out:** publish the new membership generation; subscribers validate it and
  create bounded pools only for ready, correctly scoped, authenticated endpoints.
- **Drain/scale-in:** stop assigning new work, withdraw from selection, close idle
  pooled connections and drain bounded in-flight work. Revoked identity or policy
  terminates affected work even while a graceful drain is otherwise allowed.
- **Unexpected loss:** heartbeat/lease expiry withdraws the node. Failure detection
  triggers a circuit, not an authorization fallback; a valid alternative must have
  the same authority scope/epoch and sufficient policy/revocation revision.
- **Restart:** the node gets a new incarnation, catches up and passes readiness again.
  Old pooled sessions cannot silently attach to the replacement incarnation.

Membership writes and watches require authenticated, scoped authority. Bind service
identities to allowed domain/tenant and endpoint constraints; a node may not register
an arbitrary auth relay target, downgrade to plaintext or advertise itself as admin.
Quarantined service identity needs explicit reapproval, separate from outage recovery.

## Hangang obligations

Hangang must consume authenticated membership full snapshots and bounded watch
changes, preserve a monotonic generation and resync on gaps. It maintains bounded
per-authority pools, updates selection after join/drain/remove, cancels queued work
for withdrawn nodes and never keeps sending new calls through retired pools.
Peer TLS identity, node incarnation and native capabilities must match the selected
record. Preserve request correlation, deadlines, minimum revisions and authority
scope through retries; do not replay a non-idempotent credential exchange or login
without an explicit idempotency contract.

Admission requires fresh domain evidence from sufficient-revision ready peers.
A successful connection handshake is not a permanent authorization lease. Initially
use a 1-second evidence/revocation freshness budget, configurable only within 1–5
seconds where service policy permits; protected streams/uploads require bounded
rechecks/expiry termination. Session/token revocation, network blocks and Pumgye
assignment/class changes have separately tracked domain revisions. No single
averaged trust score or node heartbeat can substitute for those proofs.

Control-plane partition permits only already verified snapshots/evidence within
valid leases. Once a required lease expires or a revision/epoch cannot be proven,
fail closed with a typed unavailable outcome. Negative/deny decisions may remain
conservative; unavailable must not become a guest-to-allow or undeclared provider
fallback. Capacity changes affect scheduling, not privilege.

The unified console should show each authority's desired/applied revisions, member
state/age, lease expiry, incarnation, lag, breaker, capacity and drain progress.
Management still delegates to the owning domain API with CAS and audit. Monitoring
(Sacho), durable telemetry (Jangbu), audit verification (Saheon) and ontology
(Sillok) observe the events; none becomes the membership or policy write authority.

## Acceptance gates

- Two or more replicas of each authority plus Hangang, tested as actual processes.
- Boot/catch-up, lost/duplicate/out-of-order watch events, snapshot corruption,
  rollback/reset, stale replica and revoked service-certificate rejection.
- Scale out/in, ready-before-catch-up rejection, bounded drain, crash/restart,
  incarnation mismatch, DB/control partition and lease-expiry behavior.
- Session/token/user disablement, IP block and role/class removal propagate within
  the documented budget, including open streams and live credential translations.
- Native/HTTP parity and final service credential isolation across retries/failover.
- Sustained 10k/100k complete decisions and end-to-end traffic with realistic policy
  cardinalities, node churn, saturation/backpressure and measured p99/tail latency.

A Pumgye microbenchmark, membership schema or local SQLite CAS test does not prove
these fleet guarantees. Implement and qualify the adapters and Hangang subscriber
before marking scale-out complete.
