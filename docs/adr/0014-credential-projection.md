# ADR 0014: Service credential projection after authorization

Status: proposed design; no projection endpoint or wire format is implemented.

Structural prototype: [request schema](../../schemas/projection_request.schema.json),
[synthetic request](../../examples/projection_request.json) and
[validator](../../tools/validate_contracts.py). The validator binds request/decision
to separately supplied native context, caps lifetime at one second and all native
identity/network/plan/decision deadlines, and rejects consumed nonce pairs. Its
fixtures include jointly forged subject values, forbidden caller authority fields,
changed scopes, stale revisions and expiry. These checks are executable contract
tests, not signature authentication, a live revocation store, an atomic replay
ledger or credential issuance. The request digest is supplied from native context;
canonical request hashing and authenticated receipt verification still need runtime
implementation. Historical fixture timestamps are never live credential leases.

Hopae source `1322163` now implements the digest primitive: domain
`hangang-zerotrust:credential-projection:request:v1` plus NUL, then SHA-256 over
u32 big-endian length-prefixed service, audience, method, exact origin-form target
and complete entity SHA-256. Encoding/query order are preserved. Native tests
and an independent Python vector agree for `ab`, `c`, `GET`, `/private?x=1`, empty
entity: `234488f459d8b3069a74d308d639fa9bfb402b12a9544a413c06c6136a8dab11`.
Two tests and fmt/clippy/boundary/docs checks pass. Routing integration, receipt
authentication and issuance remain unfinished; no deployment behavior changes.

Hopae `8b4d0ce` adds a source-only Ed25519 receipt primitive: 146 bytes,
authentication/permit purposes, domain-separated exact-byte signatures, native
binding, issuer-supplied nonce and at most a one-second lease. Strict verification
rejects weak keys, byte tampering, wrong key/purpose/binding, size and time errors.
The authenticated wrapper cannot be constructed, cloned or serialized by consumers.
Two crypto tests and fmt/clippy/boundary/scoped-audit/docs checks pass. Nonces must
come from native CSPRNG issuance; recipient keys must be authority/purpose scoped.
Canonical chain binding, key registries, rollback-resistant clocks, live revocation,
atomic nonce consumption, Pumgye signer integration and credential issuance are still
required. Stateless signature acceptance can repeat; it is not replay protection.

Current evidence: Hopae returns verified identity through its auth-proxy response.
Hangang copies configured response headers before evaluating Pumgye permission.
Returning an upstream secret through this existing path would release it before
authorization. Explicit mixed-token routing unwraps inbound credentials only;
it does not implement outbound credential translation.

The proposed sequence is:

1. Hopae authenticates the human/service/workload and issues a short, opaque
   authentication receipt. Sumunjang supplies revisioned network evidence.
2. Hangang resolves the native route/catalog classification and requests Pumgye's
   decision for the exact principal, service, resource and action.
3. After permit, Hangang requests projection from Hopae with the authentication
   receipt and a verifiable Pumgye decision receipt. Guest/deny/error never reaches
   secret resolution. Receipt signing/channel binding needs a separate executable
   contract; trusting a caller-supplied `allowed:true` is insufficient.
4. Hopae rechecks identity freshness/revocation, policy/route revisions, requested
   audience, approved credential reference and receipt replay state. A native
   transaction/admission fence owns issuance; Lua cannot mint receipts or grants.
5. Hangang installs the result only into the bound upstream request after stripping
   client authentication headers. Route rematch, redirects, stale state or failed
   revalidation discard the result. Secrets never enter ordinary auth-response
   headers, browser responses, module RPCs, telemetry or decision caches.

Projection plans cover verified identity headers, audience-bound short JWTs,
approved bearer references, request-bound HMAC and workload mTLS. Each plan fixes
target audience, methods, header allowlist, maximum assurance/privileges and secret
references in native configuration. Cross-provider canonical identity linking is
explicit; a new token cannot increase source identity assurance. Pumgye retains
authorization, Hopae identity/issuance, Sumunjang network control and Hangang
routing/enforcement. No shared multi-writer business schema is introduced.

Issuance is bounded by the earliest identity, network, permission and plan expiry,
with a proposed decision lease no longer than one second. Credential lifetime and
connection lifetime are separate: changed policy or revoked identity must also
terminate affected streams. Snapshot epochs/membership prevent stale replicas
issuing credentials. An unavailable signer/provider fails closed with bounded
concurrency/timeouts and circuit breaking, without connector fallback.

Required adversarial qualification before implementation is activated:

| Input/change | Required outcome |
| --- | --- |
| Guest or forged permit | No secret lookup or projection |
| Replayed receipt | No second issuance |
| Changed host/service/method/path | Reject audience/request mismatch |
| Revocation or revision change between permit and issuance | Reject stale authorization |
| Client Authorization or protected identity header | Strip; never merge |
| Lua-selected URL, key or assurance | Reject undeclared capability |
| Redirect or reused upstream connection to another audience | Discard credential |
| HMAC upload exceeds buffering budget | Explicit bounded streaming design or refusal |
| Signer outage, cancelled call, expired decision | No credential, no weaker fallback |

Open work: receipt schema and cryptographic verifier, dedicated native protocol
phase, owner publication/rotation APIs, delegated management UI, stream revocation
and full-stack 10k/100k-QPS qualification. Existing gates validate existing contracts;
they do not prove this proposed mechanism.

Hopae `535dc57` implements canonical receipt bindings for signer/key epoch, identity authority epoch, canonical namespaced principal/kind/AAL, identity revision/credential generation and service/audience/request digest. Permit adds the signed authentication receipt hash, decision/resource/action and Pumgye authority/catalog/policy/network/route/plan revisions. Authentication does not assert another domain's policy/network state. Three tests include independent Python vectors and actual Ed25519 rejection after identity epoch, plan revision or authentication-chain changes. Signing endpoints, verified owner-derived inputs, key registries and atomic revocation/replay remain required; these library primitives are not deployed credential issuance.

Hopae `fc49a8a` adds immutable receiver key selection by native authority, purpose and key epoch, followed by canonical binding and strict signature verification. In-memory transitions retain removal floors and historical public-material ownership, refusing stale epochs, resurrection and moving retired authentication material to another authority/purpose. State is bounded (64 active entries, 128 floors, 256 historical public values), and key lookup does not allocate an issuer string. Two tests and fmt/clippy/boundary/docs checks pass. Restart-safe DB floors, authoritative publication/atomic activation, clock/replay/revocation and live endpoints remain required; a fresh registry cannot reconstruct missing history.

Hopae `eac5d78` adds native owner persistence of the public registry, removal floors and material history in existing SQLite meta state. Publication uses revision CAS, caller authorization before writing and before commit, and one transaction for state plus reference-only audit. Loading validates bounded snapshot relationships and a trusted minimum revision; ordinary restart retains removal fences. Five registry/store tests cover restart, stale publication, late revocation, malformed state and audit failure rollback. No production DB, signer private material or deployment was changed. Atomic snapshot installation/endpoints still need integration; older whole-DB restore requires an external revision/authority-epoch floor. DB persistence alone cannot prove restore freshness or consume receipt nonces.

Hopae `762353c` links the durable key owner to shared ArcSwap verifiers. Exclusive mutable owner publication serializes commit/install; allocation occurs before commit and successful commit immediately installs the prepared Arc. Failed publication preserves live state. Verification returns a non-Clone receipt tagged with the captured registry revision; local pointer-current checks invalidate old tags after publication. Eleven receipt tests pass, including actual signed key removal, shared-reader update and restart rejection. This is a library integration, not deployed endpoint activation. Issuance must still recheck the durable revision atomically with nonce consumption; the local check cannot close a later race or replace distributed membership/follower fences.

Hopae `96f9d85` adds a source-only atomic consumption helper for opaque checked receipts. Immediate owner transactions recheck registry revision, native time and authorization, record the authority/purpose/nonce hash once and commit associated DB work together. Operation failure or expiry during work rolls back both. A persisted clock floor and monotonic duration fence protect cleanup/rollback cases; ordered meta expiry indexes collect at most 128 pairs per call with a one-million active cap. Twelve receipt tests and fmt/clippy/boundary/docs checks pass. Callbacks must not expose credentials or irreversible network effects before commit. Receipt endpoint wiring, distributed restore floors and end-to-end throughput remain unimplemented/unqualified; production state is unchanged.

Hopae `6aa88d8` qualifies consumption across eight independent SQLite connections: one synchronized consumer commits and associated owner-work count is exactly one. Reopening the DB refuses reuse. Final actor revocation rolls back both nonce and work, allowing a later authorized retry. Fourteen receipt tests and fmt/clippy/boundary/docs checks pass. This is adversarial transaction qualification, not an active issuance endpoint, distributed membership guarantee or throughput benchmark; production remains unchanged.
