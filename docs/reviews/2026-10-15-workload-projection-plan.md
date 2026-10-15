# Typed native Workload projection — implementation proposal

Status: proposed; native policy implementation started, full chain unimplemented.
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
