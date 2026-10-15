# Native Human proof → typed permission → final enforcement proposal

Status: **design for review; no Human wire/product activation**. English is normative;
[한국어](../ko/2026-10-16-human-native-wire-design.md). This preserves the broader
[provider completion objective](2026-10-15-provider-completion.md); it does not
close native local accounts, recovery, all-provider MFA or streaming revocation.
The older provider audit's lack of a production Any/All caller is historical:
current Service composition has actual fixed-slot orchestration, explicit identity
relationships and AAL0. It is not Human MFA.

## Exact evidence and insertion points

Sources inspected without Cargo, cluster or operating changes:

| Component / source | Current behavior to reuse; boundary still missing |
|---|---|
| ZT `735333800b114ca66685cb6eff29d28802e1253a` | This design's base; existing Service/Workload and provider objective records remain intact. |
| Hop `87d19a02ee162120eba55a341f9ceb1e02bd9aa5` | Private H0 reviewed source, full workspace 1111 passed/43 ignored, strict Clippy/fmt; actual owned OIDC and LDAP LDAPS/StartTLS + TOTP/Engine/current capture, actual CLI restart/material ledger checks. These are source/owned-fixture results, not public Human RPC or operating adoption. |
| Hop `src/verify/human.rs:171,191,287,379,387`; `src/verify/engine.rs:174,349` | Original admission, actual Store-backed Engine, exact HandleView/post-refresh expected identity, final native Allow only, private Checked/current fences. Existing parsed scope does **not** include the final entity/header digest. |
| Hop `src/session/service.rs:1463,1647,2003,2271`; `src/store/sqlite/{primary_owner,human_owner,material_owner}.rs` | Primary source captured before the exact adapter verifies; same create/reauth transaction records original provider/material/config provenance; TOTP preserves original primary generation; joined current check. Native SessionSeal/`issue_session` remains a legacy scenario-only signer, not the new observed source. |
| Hop `src/provider/registry.rs:182,223,356,394,442` | Same prepared DB rows/config/material ledger → actual compiled Registry and publication CAS; no stale/ABA overwrite. Optional dedicated `human_material_key_env` is source-incarnation material only. |
| Hop `crates/hopae-grpc/proto/gateway.proto`; `src/http/grpc_gateway.rs:1715-1746` | Existing typed Service/Workload RPCs and Workload record capture. Workload handler starts its attempt **after** tonic decoding. That is not evidence of a predecode Human admission boundary. |
| Hop SDK `request_binding.rs:23`; `workload_observed_client.rs:186,308,382,445,576,602` | Request v1 binds service/audience/method/target/entity hash, **not headers**. SDK fixed peers/pins, private clock observation, independent observe, consuming refresh and final check are reusable mechanics, not a Human capability by casting. |
| Pum `435f138927fa78a1256e8a29a442eba399b971b6`, `crates/pumgye-core/src/lib.rs:31,159,571,598`; `crates/pumgye-server/src/workload_observed_permit.rs:37` | Same compiled policy/View, typed Workload map, native Guard/route/plan/auth owners and BOOTTIME permit source. No Human map or typed Human source follows from generic receipt parsing. |
| Root `0b15bfb7f7d199b6b653cd5de567ccc667df7055`, `src/projection_entity.rs:42,157`; `src/projection_binding.rs:14,40`; `src/proxy.rs:3388-3455,3500-3562` | Private immutable complete transformed body after route/backend composition; route owner capture; native chain; last-write/transport gate. V1 digest excludes headers. Existing classes/defaults cannot imply Human. |

The sampled component worktrees were clean. These pinned references are inspection
anchors; a later implementation must repin exact compatible immutable dependencies
and qualify its own binaries. Public source is distinct from released/adopted runtime.

## 1. Request ownership before identity issuance

Root must create a new **private** `HumanPrepared` from the actual request after
route rewriting, Lua/body transformation, backend base-path composition and all
request-header transforms. Reuse the bounded body admission/semaphore and original
route lease; unknown/incomplete streaming entities, trailers or unsupported upgrades
refuse, never hash an invented empty body. The existing body limit is configurable
up to 16 MiB; Human must explicitly opt into a bounded limit, not silently raise it.
The prepared request cannot be mutated or cloned into an independently dispatchable
request after proof issue. Projected credentials are installed only at the designated
final step, outside the digest's input set.

Add request binding **v2**, preserving v1 bytes and old Service/Workload semantics:

- domain `hangang-zerotrust:credential-projection:request:v2\0`;
- length-framed service, audience, route ID, positive route revision, canonical
  destination-owner SHA256, uppercase method, exact final origin-form target;
- transmitted entity length (u64 big endian) and SHA256 of complete transmitted bytes;
- positive fixed header-policy revision and every configured header slot sorted by
  lowercase name: name, one-byte presence marker, exact value bytes. Absence differs
  from present-empty. No trimming, percent/query normalization or unordered JSON.

The forthcoming coordinated **H1 canonical codec specification** is normative for
byte encoding and vectors; this chain design does not allocate a competing encoding.
The agreed shape is LP32 text, fixed big-endian u64 numbers, fixed32-byte destination,
entity-length BEu64 plus entity hash32, header-policy revision BEu64, slot-count
BEu16, then LP32 name + presence byte + LP32 value only when present. Header names
are lowercase RFC tchar,1..128 bytes; configured reserved credential names are an
explicit validator input. Reject all value CTLs including TAB and DEL, preserve
obs-text bytes. Limits remain16 slots,8192 total value bytes,1024 per value and
16MiB complete entity. The H1 specification and independent cross-language vectors
must settle all framing details before implementation; a raw hash/length-only
builder is not an authority-bearing Human API.

Use v1's bounded identifier/method/target validation. Destination SHA must match
Root's selected route reference and Pum's independently current route owner; it is
not a client-selected backend URL. Initial Human forbids method-changing transforms;
ordinary prefix/path/body rewrites must have an explicit owning route mapping to
Hop's public app scope and Pum's fixed resource/action/plan. Hop does not reexecute
Root Lua or pretend that a received hash proves which bytes a malicious PEP sent.

Header names are server-fixed, at most 16, total values at most 8192 bytes, each
value at most 1024 bytes; duplicates/control characters/unknown slots refuse.
Always exclude Authorization, Cookie, caller keys, projected credentials, identity/
assurance headers, Forwarded/X-Forwarded-*, Host, framing and hop-by-hop fields.
Content-Type/Content-Encoding or an application intent header may be explicitly
bound after transformation. Actual entity length owns framing. All excluded
security fields have separate fixed owner/caller/route controls and are stripped
or overwritten before upstream use; exclusion does not authorize client identity.
A header-policy change retires its prepared request/client/route owner.

The Human SDK exposes `prepare(scope, Request<Bytes>, TrustedNativeContext)` to
compute these hashes from complete bytes; **no public Human `prepare_issue_digest`
shortcut** in the initial API. A request builder/DTO/hash remains untrusted data,
not Human evidence. The trusted PEP is responsible for presenting the actual final
request; the source authenticates the native session independently. Root recomputes
and compares v2 immediately before dispatch, using the same immutable body.

Native context carries the original public URL/method, pinned app host/port/route,
actual edge client IP/UA and host-bound handle through the existing owning parser.
Final upstream target is distinct from original public app URL. Correlation of the
two is a fixed published route/scope contract, not arbitrary header promotion.
Root rebuilds native proxy context from trusted edge state, removes spoofed source
headers, and injects the caller credential only from its server configuration.

## 2. Proposed additive wire (numbers are proposals, not allocated production API)

Keep `hangang.hopae.v1`; add these declarations without altering old fields/RPCs:

```proto
service HumanAuthenticationReceipts {
  rpc IssueObserved(HumanReceiptRequest) returns (HumanReceiptObservedReply);
  rpc ObserveTime(HumanReceiptObservationRequest) returns (HumanReceiptTimeReply);
}
message HumanBoundHeader {
  string name = 1; bool present = 2; bytes value = 3;
}
message HumanFinalRequest {
  uint32 binding_contract = 1; // exactly 2
  string method = 2; string target = 3;
  bytes entity_sha256 = 4; uint64 entity_length = 5;
  string route_id = 6; uint64 route_revision = 7;
  bytes destination_sha256 = 8;
  uint64 header_policy_revision = 9;
  repeated HumanBoundHeader headers = 10;
}
message HumanReceiptRequest {
  VerifyRequest verification = 1; string service = 2; string audience = 3;
  HumanFinalRequest final_request = 4;
}
message HumanReceiptReply {
  uint64 request_id = 1; AuthenticationReceiptContext context = 2;
  bytes receipt = 3;
}
message HumanReceiptObservedReply {
  HumanReceiptReply receipt = 1; HumanReceiptTimeReply observation = 2;
}
message HumanReceiptObservationRequest {
  uint64 request_id = 1; AuthenticationReceiptContext context = 2;
  bytes receipt = 3; bytes request_sha256 = 4;
}
message HumanReceiptTimeReply {
  uint64 request_id = 1; uint64 owner_now_ms = 2;
  uint32 remaining_ms = 3; bytes receipt_sha256 = 4;
  string clock_domain = 5;
  uint64 source_revision = 6; uint64 application_generation = 7;
  uint64 key_registry_revision = 8; uint32 cache_ttl_ms = 9; // zero
}
service HumanObservedCredentialProjection {
  rpc Project(ProjectionRequest) returns (ObservedProjectionReply);
}
```

Human issue does not accept subject, AAL, generations, receipt, or a caller's
`request_sha256`; it recomputes v2 from the bounded descriptor and fixed header
policy. A descriptor's body hash is the authenticated PEP's attestation, not proof
of an identity or a source capability. The additive protocol/SDK candidate uses the existing 128 KiB frame ceiling
(existing Verify/header limits still apply), preserving valid native authentication
headers. Retained-record count and byte quotas remain configurable source-owner
limits; no fixed admission capacity of 64 is part of the wire contract.
Reject absent/duplicate/wrongly sized fields, all-zero hashes, invalid correlation,
unknown contract, extra header slots, and original/final scope mismatch before
Engine/signing. No body bytes, cookies or header values enter default Debug/error
logs; generated sensitive DTOs need explicit redacted Debug even in release.

Use existing receipt envelope/purpose, but signed kind **1 Human**, actual
handle-issued AAL1 or qualified native TOTP AAL2 only. Reject AAL0 and currently
unsupported AAL3, regardless of the generic receipt parser accepting Human1..3.
`identity.revision` = actual current user authz version;
`credential_generation` = actual current session credential generation after TOTP.
Neither equals the Service/Workload profile revision by assumption. These user/session
revisions are local to their own user/session: never apply a global user/session
revision floor across different subjects. Global monotonic floors cover only actual
source/app/key owners. Test high-revision user A followed by low-revision user B.

The former s_48 Human derivation is **superseded** by the reviewed
[H2a subject/lifecycle contract](2026-10-16-human-subject-lifecycle.md): human1:
plus full lowercase SHA256, bound to fixed source issuer, actual durable Store
realm and exact current native user ID. Caller email/realm/session/provider labels
cannot select that coordinate. Existing Service/Workload s_48 and legacy strict
session-receipt behavior remain unchanged. Account linking is only the actual
owning native identity policy; current revision/AAL/proof epochs remain separate.

Canonical epoch allocated by the protocol/SDK candidate (not production activation):
`hobs1:<32lowernonzero-process-nonce>:<authority>:s:<source-scope-revision>:a:<app-generation>`.
Reuse strict bounded re-encode validation (authority <=40, whole <=128, revisions
1..9007199254740991, no leading zeros); a separate Human parser rejects all Service/
Workload/legacy namespaces. `clock_domain` is exactly that nonce. Human
`source_revision` means the **actual Human scope publication**, sourced initially
from the owning durable config generation and exact prepared app Arc; it is not an
`authentication_gateway` Service profile or a session/user revision. Human source
startup must not require enabling Service profiles merely to build its runtime.

Pum additive RPC, same existing request/permit/report DTOs:

```proto
service HumanObservedProjectionPermits {
  rpc Issue(AuthenticatedResourceRequest) returns (ObservedProjectionPermitReply);
  rpc Observe(PermitValidationRequest) returns (ObservedPermitTimeReply);
}
```

Human Project accepts proposed `permission_contract = 4` only, containing the exact
bounded Pum PermitValidationRequest bytes; contracts1/2/3 retain their existing
meaning. Correlations are fresh per RPC and checked independently, including inner
permit request IDs. Output `chain_sha256` is SHA256 of those exact permission-query
bytes, not ad hoc reserialization. Existing output profile metadata is validated
against the Human source epoch's explicit scope revision. No UTC variant of Human
issue/project is introduced by this proposal.

## 3. Actual source capability and time, not DTO-to-Human conversion

A Human-only ingress layer must sample private BOOTTIME admission **before tonic
body decode, caller checks, parser work or queues** and carry that same object in a
server-owned Rust extension. Acquire bounded admission before buffering. Path
selection never grants a class; mTLS peer plus existing caller-key checks still
control the method. Failed clock capture refuses this additive method without
breaking ordinary/non-Linux paths. Missing ingress extension refuses; do not
resample inside `exchange_human`, gateway or Engine. A test must pause predecode
and show the original age was consumed. Existing Workload after-decode capture is
not silently claimed to satisfy this new requirement.

Private insertion interfaces (not public SDK constructors):

1. `Pipeline::exchange_human(VerifyRequest, IngressAdmission, OwnedHumanScope)`
   reuses the actual native parser/caller checks and internal Capture extension.
2. Actual Engine final Allow → H0 `Checked`, preserving exact post-refresh state.
   Consume it via private `bind_final(OwnedFinalBinding)` → `BoundHuman`; reject
   any parsed scope mismatch. Retain only bounded original scope/handle digest,
   not raw session cookies; add a private retained-scope current-check entry.
3. Human issuer takes only `BoundHuman`, not `Identity`, SessionSeal, signature
   evidence plus numbers, response headers or callback booleans. Current-check
   original provider/material/config/session/user/handle/factor/app and signer
   registry before sign and after all signing/allocation/callback/await work.
4. A bounded issuer-owned record maps exact signed receipt SHA256 to original
   BoundHuman, context/digest, original admission, current signing/publication
   owners and clock domain. Record miss/capacity/retirement refuses; no live-record
   eviction, wall-clock reconstruction, or reissue-on-miss.

Proposed record limits: configurable count up to4096, default1024, and an independently
accounted32MiB retained-allocation budget (including variable native facts/header
capacity), with bounded sharded lookup/pruning. Reserve count/bytes before retaining
a record, refuse oversize/capacity instead of evicting a still-live source, and
release exactly once on retirement/expiry. A numerical record ID/size budget cannot
construct a source capability. Throughput/size limits require measured qualification.

Original maximum is **strictly below one second**, including conservative tick
quantization, and no later than original H0 session/handle/factor freshness. Signed
source expiry is within this original same-domain deadline. ObserveTime is also the
authenticated **current/revocation endpoint**: verify exact signature/context/hash,
find the issuing record, then perform actual joined current owner checks. Existing
native logout/admin session/user/factor/provider publications revoke the underlying
owners; Pum/Root cannot mutate those authorities through a proof API. Observation
or refresh never logs in, reauthenticates, touches a lifetime forward, substitutes a
new record or recovers a retired one. Return floor(actual remaining Duration) after
final work; cache TTL0 is not a revocation lease.

All clock conversion is owner-relative: explicit source/receiver error ppm, client
exchange anchor before RPC, conservative transit/rounding subtraction, original
BOOTTIME generation. No cross-clock expiry minimum, receiver UTC cleanup, arbitrary
time grace, EQUAL-rate fallback for remote peers, or numerical deadline constructor
as an authenticated source. Clock failure/reversal/suspend retires/refuses as in
H0. Local equal-rate use is justified only for the same actual clock/backend owner.

The issuer record is intentionally process-affine. Restart/replica miss refuses
old proof even if signing key/DB config are unchanged. A still-valid durable native
session may obtain a **new** proof through actual Engine capture after unchanged
material restart; that does not revive an old proof. Fixed peers/affinity must be
explicit; an arbitrary load-balancer replica may not reconstruct a missing record.

SDK module proposal `human_observed_client`: fixed mTLS endpoint/pins, canonical
hobs1 policy, allowed service/audience/app/route/header contract and minimum source/
app/key-registry floors, explicit rates; `Client::new_human`, `prepare`, `issue`,
`prepare_observation` + independent `observe`, consuming `refresh`, `check` and
retention queries. Observation fields are private, tied to exact prepared request,
client owner, verified signature/hash/context/source-clock exchange, and original
record-backed report. A public wire report or SignatureEvidence plus arbitrary
runtime bounds cannot construct one. Refresh can only shrink admission and grow
upper retention; final client ownership/floor checks follow clock callbacks.

## 4. Typed Pum policy and atomic Hop projection

Add optional `human_users` to the **same** policy/CAS API/compiler/View and total
assignment bounds, omit empty map in legacy serialization. Add `Principal::Human`
and a native Human-only evaluator; never fall back to users or workload_users.
Same subject in all three maps is independently managed. Explicit guest remains
non-permissive; unknown/missing/failed publication refuses. Existing Kubernetes v1/
v2 mapping meanings do not acquire Human grants; a later Human mapping requires
its own explicit native identity source, not auto-conversion of RBAC usernames.

Rights stay conjunctive: typed Human roles AND network/Guard rights AND resource
permission AND classification AND maximum required minimum-AAL. Assurance comes
only from the checked Human proof, never a role's requested level, group membership,
network match, summed factors or max of Service/Workload branches. Resource/class/
action must match native route/plan owners. Pum's actual publication, Guard/route/
plan observations and Hop Human SDK current-check remain current before signing
and emission. Policy/role/class/assignment deletion or source replacement retires
retained candidates. No exporter/analytics write is on the request path.

Pum Human OwnerSlot is fixed at startup, never selected by request context. Reuse
observed permit protocol: its own `pobs1` BOOTTIME domain, full signed
`proof_remaining_ms` for upper replay retention and shorter `remaining_ms` for
admission. Live policy DB/Kubernetes publication keeps the actual immutable View;
no detached copied policy or caller-selected auth/Guard/route/plan endpoint.

Hop Human projection needs a **class-specific** private fence around the shared
paired core, not a cast of Workload Record. Async H0 current checks cannot run while
a SQLite writer/ledger mutex is held. Extract the same bounded durable comparison
into a private connection-scoped checker, with opaque retained expected facts and
pre-sampled native time, to use inside the actual **same Store** paired transaction.
Do current checks before/after remote Pum observation; inside the paired transaction
check Human current rows/material/factor, signer registry, route/plan/application/
caller/config publication and original BOOTTIME. No await/network/env/CA/user clock
callback under that writer. Only the already prepared local vault mechanism may
resolve the final secret inside the admission transaction; no arbitrary resolver
callback or new network lookup is introduced. Recheck pure/time/native facts after
secret work before commit. Share the real single owner DB, not attached foreign
business schemas or a parallel replay store.

Authentication and permission nonces are consumed **atomically in the existing
canonical ledger**. No principal/mode/endpoint/contract prefix creates a second
chance. Keep full independently verified signed proof upper lifetimes on the stable
receiver BOOTTIME generation; original record eligibility is separate. Unknown
receiver generations remain tombstones with conservative capacity refusal, never
receiver-UTC cleanup or time-grace reset. Rollback/cancellation before commit cannot
partially consume one nonce or release a credential; cancellation/lost response
after commit burns both and cannot disclose a retry copy. Key-registry checks and
transaction rollback semantics remain intact.

Human output finishing must be async where necessary: after commit, repeat actual
H0 current read before reply, then only native BOOTTIME/pure publication checks
after the last callback/allocation. A failure may burn nonces and discard/zeroize
the secret. Output has its **own** bounded clock domain, exact chain/request/RPC
hashes and actual remaining Duration floor after all work. No raw min of auth/Pum
absolute expiries. These are point-in-time fences, not remote atomic revocation.

## 5. Root enforcement and browser/admin scope

Add explicit server-configured authentication class Human with actual implementation,
not a request header/enum-only claim. Preserve Service/Workload/default paths. Root
uses the new Human prepared request/client, typed Pum endpoint and contract4 output;
checks exact pins/kind/epoch/AAL/request/chain/correlation/revisions/cacheTTL0 and
route/plan/source ownership. Cross-class fallback after denial/unavailability is
forbidden. Actor class, service scope and backend credential remain distinct.

After immutable preparation there are no unbound request transforms. Before first
upstream bytes, repeat digest/header/destination match, remaining original age and
route/auth/network/permission/output transport guards, including delayed connect,
pool reuse and HTTP/2 stream creation. Hold the existing final guard through actual
write, not merely response-header construction. On any refusal the counted backend
stays0. Only the configured projected credential reaches a successful backend1;
strip caller keys, original auth credentials, Hop cookie names (default
`__Host-hopae`, `__Host-hopae_bind`, `__Host-hopae_portal`), envelopes/proofs and
spoofed identity fields. Preserve unrelated application cookies only under an
explicit safe policy. No secret/header/body in browser/log diagnostics.

Keep native interactive login/step-up on its existing portal/Verify contract. A
preliminary redirect/step-up or unauthenticated request is not an issuable final
Allow. Root may forward the existing authenticated native login response for a
navigation, then issue only on the subsequent real final request. Human RPC failure
must not invent a login URL or replay a non-idempotent request after TOTP. JSON/API
requests receive safe login/step-up refusal, not silent interactive retry.

Admin UI adds a distinct Human assignment kind/map through the owning Pum CAS,
with independent same-subject rows and existing draft/role/logout/generation/mobile
fences. Show real source-supported native SSO buttons and LDAP password/TOTP flows;
never label API key/relay composition as MFA or display unsupported Google forced
reauth as usable. A UI minimum-AAL control requests policy only; it does not prove
factor completion. Recovery/local accounts/provider linking remain their own queues.

## 6. Explicit activation, schema and key lifecycle proposal

These are **proposed fragments, not currently loadable Human configuration**.
Existing unknown-key validators must continue refusing them until implemented.
Add `receipt_issuer.human_receipts`; preserve absent-field serialization/defaults:

```json
{
  "human_material_key_env": "EXAMPLE_HUMAN_MATERIAL_KEY",
  "receipt_issuer": {
    "human_receipts": {
      "authority": "workforce-v1",
      "scopes": [{
        "service": "orders", "audience": "orders-api", "app_id": "orders-web",
        "realm": "staff-v1", "route_ids": ["orders-route"],
        "binding_contract": 2,
        "header_policy": {"revision": 1, "names": ["content-type", "x-order-intent"]}
      }],
      "maximum_records": 1024, "maximum_retained_bytes": 33554432
    }
  }
}
```

The fragment omits the already required receipt signing/transport configuration;
never substitute material key for `receipt_issuer.seed_env`. Allow a Human-only
issuer with no dummy Service profiles/scopes: adjust source-specific readiness and
validation coherently, while a source-less empty issuer remains invalid. Existing
Service RPC scope admission must not inherit Human declarations. The provisional scope `realm` label in this fragment does not select a Human subject
namespace: H2a supersedes that formula with the actual immutable Store realm.
The native subject uses fixed issuer_ref and actual current user ID; provider
issuer/provenance is checked independently. No client picks
realm, profile revision, minimum assurance or server peer.

Pum: proposed `--human-observed-permits --human-authentication-live <reference-file>`
under the existing observed-authentication production feature; require trust, permit
signer, Guard/network, route and projection-plan owners, with no verify-off fallback.
The new live file reuses fixed `issuer_ref/address/server_name/ca/certificate/key/
token_env/observed_clock_rates{source_ppm,receiver_ppm}` shape, creates only a Human
OwnerSlot and pins hobs1 scope/app/key floors. Add strict key allowlists and preserve
Service/Workload CLI/config parsing. Policy `human_users` is keyed by the canonical
opaque Human subject; trusted UI lookup must derive it from Hop's actual user owner,
not client email. Until that owner-backed selector exists, require explicit opaque
subject entry with clear provenance, never auto-map old `users` entries.

Root: explicit `routes[].native_resource.observed.authentication_class="human"`,
existing issuer/purpose-specific permit pins, `identity_authority="workforce-v1"`,
minimum_profile/application/key floors and source_error_ppm/receiver_error_ppm are
required. Add a server-fixed `native_resource.human_binding` contract2/header-policy
revision/names that must match Hop scope and actual route publication. Existing
maximum_body_bytes/body_timeout_ms and final-header limits remain enforced. Configure
fixed mTLS Hop/Pum/Guard peers and plan/resource bindings as in existing observed
routes. Missing dependencies/unsupported class/nonmatching manifest refuse validation
or activation; an absent Human option preserves defaults. Example ppm values are
operator error bounds, not universal constants inferred from one passing fixture.

H0 schema9/material owners are the prerequisite; proof records are ephemeral, while
the existing durable paired ledger remains authoritative. A new SQL schema migration
is needed only if implementation adds persisted source/record metadata: it must have
strict inventory/guards/backups and no legacy-proof backfill. Material-key rotation,
receipt signing-key epoch/public trust rotation, caller/mTLS rotation, and TOTP
keyring/enrollment lifecycle are independent. Test each removal/restore/ABA and failed
publication; no key reused merely because it is already available. Publish source,
SDK/proto and typed consumers first with Human disabled, then qualify explicit owned
routes, then perform a separate verified publication/adoption step under existing authorization. Do not mutate existing signed
artifacts or claim current operating deployments run Human from source merge alone.

## 7. Ordered implementation and RED/GREEN acceptance

| Stage | Required result and adversarial evidence before next stage |
|---|---|
| H1 contract/preparation | Pure v2 vectors in SDK/Root/Hop: nonempty and actual empty bodies, same-length mutation, post-transform bytes, absent/empty/duplicate/reordered headers, path/query/base-path/destination/method changes. RED: old v1 fails to bind a header. No legacy vectors changed. Predecode pause/suspend consumes original age. |
| H2 source + SDK | Actual native OIDC discovery/JWKS/nonce/PKCE and LDAP LDAPS/mandatory StartTLS login → real TOTP → Engine Allow → Issue → independent Observe → consuming refresh/check. Legacy/external-only AAL2 cannot fabricate TOTP; AAL3/Service/Workload DTO rejected. Wrong caller/IP/UA/host/route/handle, key/issuer/app/material/provider/config/primary/factor/user withdraw at each await/sign/emission; queued cancellation/deadline/clock failure; no renewed age. Missing record/restart/other replica/capacity fails. |
| H3 typed Pum | Same subject in users/workload_users/human_users independent allow/delete; guest/unknown/role/class/resource/action/network/Guard denial and minimumAAL1/2/3. Human AAL1 cannot satisfy2, actual TOTP2 can, no supported3. Current policy/source/route/plan withdrawal after positive capture refuses. Real CAS stale/response-lost/readback restoration, no force overwrite. |
| H4 paired output | Actual auth+permit pair against real SQLite/vault: concurrent same pair one winner; mixed old/new contracts/class attempts cannot double-consume; one-nonce collision; failure before/after secret and commit; cancellation, lost response, restart, unknown-generation retention/capacity; key removal; post-allocation/current-read retirement; output rounding/transit. RED old detached signer/numeric bounds cannot create Human source. |
| H5 exact chain/browser | Independent public SDK + real Hop/Pum/Guard/Root and counted backend: positive OIDC/LDAP/TOTP Human chain backend1; all class/AAL/guest/classification/request/header/destination/revoke/replay/cancel/delayed-connect negatives backend0. Browser native SSO/login/TOTP/logout and scoped admin CAS/drafts/locale/mobile; service Any/All and native/default Workload regressions. No transport failure counted as expected policy deny. |
| H6 candidate/adoption | Exact immutable dependency pins, full workspace/default/feature tests + strict Clippy, production-feature static binaries/hashes, independent review, local four-service fixture then explicit K3s independent-host/SDK/browser. Sign/publish/adopt through a separate verified publication/adoption step under existing authorization, with matching source/artifact receipts. Installing a binary is not enabling/qualifying a Human route. |

No broad completion assertion from H0 or this document. Async source-backed immutable
memory snapshots/follower membership and throughput are a later explicit correctness+
performance gate; do not replace current SQL with a TTL-only cache. Keep future
provider-specific external-factor provenance, multi-issuer identity relationships,
Human/Service/Workload mixed actor relationships, native local accounts and credential
replacement/recovery, account/directory withdrawal, Google capability limits and
long-lived stream reauthorization in the objective. Any/All must retain original
branch budgets/snapshots/circuits and reject supplied-invalid/ambiguous identities;
additional factors cannot add/max assurance without a verified native factor contract.

## Review decisions still required before product edits

Parent accepts additive v2/header limits for the H1 pure codec only, without Human
route/RPC activation. Independent cross-language vectors precede source integration.
Remaining review: hobs1 scope-revision semantics and contract4 allocation; confirm fixed original→final route mapping and destination owner wire;
review predecode tonic integration and private same-Store transaction checker;
approve subject realm lifecycle and bounded record capacity. Revalidate existing
receipt format/retention upper bounds and source-affine topology; do not enable
arbitrary cross-host source failover, hot DB rollback, backup/VM-clone protection or
instant external directory/account revocation by implication. The optional Human
material key, receipt signing keys, transport/caller keys and TOTP encryption keys
remain four separately operated lifecycles. Cold restore must restart source runtime
and preserve authoritative replay evidence; arbitrary independently cloned live
owners/ledgers need external fencing and are unsupported here.

[Source scope binding addendum](2026-10-16-human-source-scope-binding.md): mandatory authenticated scope fingerprint in Human time reports; implementation qualification is pending.
