# Typed native Workload projection — implementation proposal

Status: protocol/source-owner proposal; native policy stage C merged, full chain unimplemented.
Existing qualified Service projection does not establish Workload or Human support.

A real Hopae TokenReview result must remain Workload/AAL0 through an additive
Workload receipt RPC, an opaque SDK observation, Pumgye's actual compiled resource
policy, paired Hopae output and Hangang's final transport gate. Caller headers may
select neither identity class nor assurance. Existing Service endpoints, trust and
default activation keep their current semantics.

The initial design uses a dedicated canonical `wobs1` owner epoch binding process,
authority, profile and application generations. Workload endpoints reject Service
and Human epochs. An issuer-owned bounded record binds the exact signed receipt to
the original pre-TokenReview BOOTTIME capture. The first proof has at most one second
of nonrenewable validity: observing it may shorten that original lifetime, never
refresh authentication or reconstruct a new deadline from caller milliseconds.
External Pod deletion is subject to the actual TokenReview observation and this
short remaining lifetime; instantaneous external revocation is not promised.

Pumgye adds optional `workload_users` to the same policy snapshot, compiler and View.
Its typed workload evaluator selects only that map; existing Service/legacy queries
select only `users`. Equal subject bytes do not cross-authorize. Resource/action,
role inheritance, classification, assurance and enforced network conditions remain
conjunctive. Kubernetes mapping v1 retains its semantics; explicit v2 can produce
these typed workload grants. Kubernetes RBAC does not itself manufacture an Allow.

New workload output endpoints must share the existing atomic paired replay ledger.
A different RPC or contract number must never make a consumed nonce unused. Human
requires an independent native session/handle/user/factor owner, verified AAL and
withdrawal checks; neither API credential composition nor Workload authentication
is Human MFA.

Completion requires actual pod-bound TokenReview, typed resource Allow and Deny,
independent SDK, four services and a counted backend. Wrong audience/identity,
source withdrawal, original-age expiry, restart, replay and final-write retirement
must refuse without backend effects. Service regressions must continue to pass.
Protocol canonicalization, record retention/capacity and source mapping compatibility
remain under independent review before activation. No new release is claimed here.

## Review clarifications before protocol activation

The observation clock domain must equal the epoch's 32-character process nonce,
not the full epoch string or an independently generated domain. The canonical
parser must re-encode byte-for-byte, including colon-bearing authority values.
Missing original-proof records refuse; signature validity, UTC expiry, profile
currency or incoming remaining-time fields cannot reconstruct a lost capability.
Capacity exhaustion refuses issuance rather than evicting a still-admissible owner.

Original-proof admission records and durable paired replay evidence have separate
lifetimes. Expiring the one-second original capability must not shorten retention
of a consumed signed authentication/permission nonce. Replay retention follows the
full signed proof bounds; source observation never extends them. Signed receipt
expiry and initial original-budget limits must be reviewed together before coding.

Mapping v2 candidates explicitly report their mapping version and each outcome's
principal class. V1 serialization remains unchanged. Neither a v1 candidate nor a
legacy subject assignment may silently acquire typed Workload authority.

## Native policy stage C merged

Pumgye source `a45b37b` adds the optional typed map and Workload/AAL0 scoped
resource evaluator to the same compiled policy. Both directions of class fallback
are refused. Mapping v2 reports typed outcome metadata; actual old-release/new-build
v1 diagnostic output is byte-identical. Actual native source installation tests
cover original expiry, same-lifetime reinstall refusal, fresh View retirement of
old captures and revision advance after typed grant deletion.

The entire workspace passed 90 default tests and 95 observed-feature tests, with
strict all-target Clippy in both configurations. This source is merged to main;
published Pumgye 0.1.7 and its operating artifact are unchanged. New receipt RPCs,
opaque Workload SDK, TokenReview source owner, signed permits and paired output are
still required before any full-chain Workload deployment claim.

## Hot-path record complexity

Policy snapshots are immutable and published on configuration changes. Per-request
proof records have a different update rate: insertion must not clone and republish
the whole live record map. Use bounded sharded lookup or an equivalent structure
with approximately constant-time insertion/lookup, bounded cleanup work and explicit
capacity admission. No provider call, signing callback or await may run under a
record-table lock. Capacity pressure refuses rather than evicting an admissible
proof. This is a design requirement, not a measured throughput result.
