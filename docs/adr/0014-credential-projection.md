# ADR 0014: Service credential projection after authorization

Status: proposed runtime integration. Hopae implements source-only receipt crypto,
key ownership and atomic chain admission; no projection endpoint is activated.

Structural prototype: [request schema](../../schemas/projection_request.schema.json),
[synthetic request](../../examples/projection_request.json) and
[validator](../../tools/validate_contracts.py). The validator binds request/decision
to separately supplied native context, caps lifetime at one second and all native
identity/network/plan/decision deadlines, and rejects consumed nonce pairs. Its
fixtures include jointly forged subject values, forbidden caller authority fields,
changed scopes, stale revisions and expiry. These checks are executable contract
tests, not signature authentication, a live revocation store, an atomic replay
ledger or credential issuance. The request digest is supplied from native context;
canonical request hashing and authenticated receipt verification have Hopae library
implementations below, but still need native request/endpoint integration. Historical fixture timestamps are never live credential leases.

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

Hopae `5a6befb` repeats the durable registry revision check after caller work and the final authorization guard, immediately before expiry validation and commit. A regression mutates the registry within owner work and confirms that registry, nonce and work all roll back; a valid retry succeeds. Fifteen receipt tests and fmt/clippy/boundary/docs checks pass. Credential endpoint activation and distributed qualification remain pending; production is unchanged.

Hopae `21dba4c` adds authenticated projection chain admission. Native identity epoch, subject/kind/AAL, identity revision/credential generation, service/audience/request digest must agree across separately purpose-verified receipts; the permit binds SHA-256 of the complete signed authentication receipt. Private non-Clone admissions consume both nonces with owner work in one SQLite transaction. A used second nonce or either expired receipt rolls back the first and all work. Four adversarial tests cover correctly signed conflicting contexts, chain-hash mismatch, earlier authentication expiry, second-nonce rollback and eight independent concurrent connections with one complete commit. All 44 authentication-gateway tests and fmt/clippy/boundary/docs checks pass. The native guard must still inspect live identity/policy/network/plan ownership; this is source-only admission, not credential issuance, endpoint activation, distributed qualification or a throughput claim.

Hopae `849d5e1` adds the source-only native projector for fixed identity headers and bearer references. At most 128 unique service/audience plans fix resource/action, minimum AAL and secret references. Admission captures signed permission scope, plan revision and the intersection of receipt validity. Plan mismatch precedes vault resolution; native synchronous bounded local resolution occurs inside paired consumption after the initial guard. Malformed tokens fail closed; final revocation/expiry/registry failure rolls back both nonces and zeroizes discarded output. Non-Clone/non-Debug/non-serializable output converts to sensitive fixed headers only for the bound service/audience/request and time. Five new tests and all 49 authentication-gateway tests plus fmt/clippy/boundary/docs checks pass. This does not activate an endpoint or ordinary auth response credential delivery. Management publication, native signing/transport, issuance audit/outbox, Hangang final enforcement and stream revocation, JWT/HMAC/mTLS and distributed/full-stack performance remain required. Production is unchanged.

Hopae `5baa048` adds a durable reference-only projection plan owner: revision CAS, digest, disabled tombstone and publication audit commit together, with actor guards before writes and before commit plus a final document-byte fence. The compiled Arc is prepared before commit and immediately installed into shared readers. Retained readers compare exact current DB document bytes before/after paired admission using a cached statement and borrowed row bytes, avoiding request-path JSON decoding/plan compilation/document allocation. Old snapshots fail after durable disable/replacement, and reenable requires a newly versioned signed permit. Five new tests and all 54 authentication-gateway tests plus fmt/clippy/boundary/docs checks pass. Bootstrap/readiness, delegated administrator endpoints/UI, issuance audit/outbox and transport integration remain pending; DB-backed admission does not prove distributed membership or target throughput. Production is unchanged.

Hopae `e61a347` integrates plan ownership into application startup and protected administration. Reference-only startup declarations constrain service/audience/resource/action, credential capability/reference and assurance floors; only an absent DB owner row imports revision-one bootstrap. Durable enabled state must still fit declared capabilities, and tombstones remain disabled across restart. Protected GET/PUT and signed Hangang GET/publish translation reuse native role/CSRF/replay/final actor fences. Real HTTP process tests qualify viewer/CSRF refusal, required revision, undeclared capabilities, stale writes, disable/reenable across restart; delegated tests qualify replay and native grant revocation. All-target tests pass: 898 passed, 42 ignored, plus fmt/clippy/boundary/docs/scenario coverage. Dependency audit passes under the existing verification-only RSA exception and rustls-pemfile unmaintained warning. This activates source plan administration, not a projection transport/issuer endpoint or upstream credential delivery. Hangang module UI, signer/key management, issuance audit/outbox, enforcement/stream revocation and distributed/performance qualification remain pending. Public immutable release assets and production images are unchanged.

Hopae `1319351` adds console package 0.1.5 projection administration: text-only scope/AAL/reference summary, viewer-disabled editing, conflict-preserving JSON editor, automatic next configuration revision and explicit null disable. Manifest GET/publish capabilities are pinned with asset hashes. Actual Chromium EN/admin and KO/viewer tests cover hostile text, parse refusal, conflict retention, publication/disable and existing profile regression. Internal dogfooding now runs that static source image and pinned package. Optimized copied-DB bootstrap/readback, HTTP/pooled-mTLS and Chromium MFA/TOTP, live API/matrix/module/SSO/native regressions and actual live Hangang profile/projection tabs pass. Existing production config/keys are preserved, projection remains unconfigured/disabled, and live browser checks perform no publication and preserve owner documents/revisions. Consistent stopped owner/delegation backups, prior image and registry backup remain available. Rust sources match the 898-pass/42-ignored qualified update. Administration UI/runtime integration is now exercised internally; native receipt issuance/transport, final upstream enforcement/stream revocation, issuance audit/outbox and distributed/full-stack performance remain pending. Immutable tagged release assets are unchanged.

Hopae `1f486ea` connects human verify-engine output to source-only authentication receipt issuance. A private non-Clone/non-serde seal binds original service/user/session/provider/auth-time/expiry/AAL/generations and verification time; altered public fields cannot be signed. A fixed authentication signer pins public material/issuer/key/identity epoch and up to 128 declared service/audience pairs. Native clock/RNG, initial/final owner guards, a verification-age/identity deadline ceiling of one second, monotonic duration and process-local clock watermark fence issuance. Compiled scope lookup borrows keys and output shares immutable metadata through Arc. A real SQLite engine scenario verifies signatures and rejects mutated identity/service, undeclared audience, wrong pin, final refusal, work-time expiry and rollback. All-target gates pass 899 tests (42 ignored), followed by the issuer scenario and all-target static checks after final metadata-sharing refinement; docs/scenario coverage and scoped dependency audit pass under existing exceptions/warning. Ordinary gateway wire behavior and deployed image remain unchanged. Native adapter must derive exact request context and recheck path assurance/live owners. Durable signer/key publication, restart/distributed floors, service/workload issuance, RPC activation and end-to-end enforcement/performance remain pending; authentication signing is not a permission grant.

Hopae `ec1ed5d` adds profile-owned service authentication receipts. Opaque non-Clone/non-serde proof captures the native owner revision after key/relay verification; issuance fixes Service/AAL0, configured service/audience and evidence/verification expiry ceiling, using profile revision for identity/credential generation and a service-separated epoch. Canonical subject hashing is shared with gateway rendering, preserving local/relay namespaces. Three tests qualify signatures, expiry, namespace, false MFA rejection, scope/kind refusal, revocation/final guard/clock rollback; workload/network issuance is unsupported. Live guards must recheck profile/key/app/path/network ownership and credential material rotation must advance the profile generation. A discovered ordinary-auth race is also fixed: a shared atomic publication fence spans DB publication through prepared snapshot installation, and gateway checks captured/current Arc identity after remote verification. Failed publication restores old availability. Controlled HTTP/native tests revoke a paused verifier's profile and require 503 without user headers. All native gates pass 904 tests (42 ignored), with static/docs/scenario checks and scoped audit under existing exceptions/warning. Receipt RPC, durable signing/key management, distributed floors and end-to-end enforcement/performance remain pending; the revocation fix applies independently to existing service authentication.

Internal rollout update (2026-10-14): Hopae image `0.0.3-service-fence-ec1ed5d` is active on schema v6. Configuration and keys were preserved; stopped owner/delegation backups and the previous image remain available. Optimized private-owner mixed-auth/Lua/MFA/TOTP qualification and live console/native smoke passed. Native gates: 904 passed, 42 ignored, with the existing scoped RSA exception and rustls-pemfile warning. Production profiles remain native-only; projection is disabled and receipt issuing RPC is not activated. No production credential revocation was performed for the race test.
