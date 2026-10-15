# H2a: source-owned Human subject and authority lifecycle

Status: **implementation proposal, not product code or Human RPC activation**.
[한국어](../ko/2026-10-16-human-subject-lifecycle.md). Base ZT
`c62cf69ccca3c8cc537e3233a0d7da1faf63e8d3`; Hop inspected at
`eefc358be73c71646abb53e5f6651698fe362392`. No Cargo/cluster/operating inspection.
This refines the provisional s_48 Human subject in the earlier wire design;
Service/Workload s_48 and legacy strict session-receipt behavior remain unchanged.

## Actual source facts

- `src/identity/types.rs:5`, `src/lib.rs:11`: UserId is a transparent String
  newtype with a permissive constructor, **not** a validated u_26 capability.
- `src/store/sqlite/directory.rs:128-181`, `src/crypto/mod.rs:261`: actual native
  creation mints u_ +26 Crockford symbols from128 random bits in its writer
  transaction. The user PK prevents collisions only while the row exists.
- `0002_m1_schema.sql:6-37`: users.user_id has no immutable-update or historical
  no-reuse guard. Identities use (provider_id,subject) → user_id FK. Production
  search found no hard-delete/reinsert API; no promise of nonreuse follows merely
  from that absence. Admin disable (`admin.rs:483-516`) increments authz_version
  and terminates sessions; enable is not creation of a different person.
- `identity/service.rs:145-248` resolves actual validated provider identities;
  equal email alone defaults to LinkRequired. `identity/linking.rs:55-107` permits
  automatic linking only with the explicit authoritative verified-email opt-in
  policy and authoritative existing owner. The observed production link_identity caller is authoritative opt-in AutoLinked
  apply. LinkRequired creates a pending transaction; no completed manual join
  caller was found in this inspection. Its complete authorized flow remains a
  separate acceptance gate; a subject helper cannot perform that join.
- H0 `verify/human.rs:52,108,379,387`, `sqlite/human_owner.rs:65` retains actual
  HandleView/current native user/session/provider/material/factor owners.
  `receipt_issuer.rs:482` legacy SessionSeal signer is not its public successor.
  Fixed receipt issuer_ref comes from native server configuration/key registry;
  caller fields are not authority configuration.

## Proposed canonical subject (review before implementation)

```
LP32(x) = u32be(byte_length(x)) || x
preimage = ASCII("hopae:native-human-subject:v1") || 0x00
        || LP32(fixed_receipt_issuer_ref_ASCII)
        || LP32(durable_authority_realm_raw32)
        || LP32(exact_native_user_id_UTF8)
subject = "human1:" || lowercase_hex(SHA256(preimage))
```

Output is exactly71 ASCII bytes; parser accepts exactly human1: followed by64
lowercase hex digits. No truncation, Unicode normalization, case folding, email,
provider username, or current session ID. Issuer reference is the existing bounded
1..128 ASCII identifier grammar; exact bytes/case matter. Realm is a nonzero
32-byte nonzero **public namespace**, persisted once in the authoritative Store;
its admin display is64 lowercase hex, not an operator/caller freeform realm.
User ID comes from the actual current Store row, nonempty <=256 UTF8 bytes,
without Unicode control characters (`char::is_control`, including NUL/C1). This does not assume UserId::new validated it.
Unqualifiable legacy rows remain ordinary-compatible but cannot issue Human proof.

The subject is a stable native **account principal**, not proof that two real-world
people are identical. Exact native authorized linking may associate multiple
provider identities with that account. A different native user always has another
subject, even if email/name/groups/provider subject look identical. There is no
merge-by-email helper or cross-authority subject matching. Hashing is public
pseudonymization, not encryption, anonymous identity or authentication.

Keep these OUT of subject preimage: signing key/epoch, caller/mTLS key, material
key, provider/material/config revision, factor enrollment/counter, AAL, user authz
revision, session cred_gen, process/BOOTTIME nonce. They affect current eligibility
and signed context, not a person's durable grant coordinate. User/session revisions
remain per-owner, never a global floor between users. AAL comes only from actual
qualified native factors. Same person can lose access without changing subject.

## Minimal durable ownership prerequisite

Parent-approved storage foundation, implementation progressing separately in
schema10; this document records its contract, **not a passing source claim**:

1. `human_authority_realm(singleton=1, realm TEXT64lowerhex)` is created once inside the
   atomic migration using lower(hex(randomblob(32))), with nonzero/exact-size/lowercase checks.
   Decode that canonical TEXT into raw32 bytes for the subject LP32 input.
   Realm is public namespace uniqueness data, not a secret, key or external fence;
   no claim about a cryptographic proof of incarnation follows from randomblob.
   Existing row is never regenerated. Immutable/anti-REPLACE guards refuse updates,
   duplicate singleton insertion and deletion. No issuer is stored or required
   here, and no caller/operator freeform realm overwrites it.
2. `human_user_ids(user_id TEXT PRIMARY KEY)` is an append-only reservation
   set with no cascading FK. Seed existing live IDs in the same migration; AFTER
   users INSERT reserves the new ID atomically. BEFORE users INSERT rejects ANY
   already reserved ID, including REPLACE/UPSERT reuse; BEFORE UPDATE OF user_id
   rejects changing identity. User DELETE need not mutate the reservation: it
   remains forever. Current actual user-row existence decides liveness. Ledger
   deletion/key mutation/replacement is forbidden. Failed writes roll back both
   new user and reservation; FK-blocked deletes cannot partially retire anything.

The reservation set must cover actual insert/import/test-hook paths, not only
Directory.create_user. No new hard-delete API is needed. Existing arbitrary UserId
strings remain untouched; format documentation is not constructor validation.
Current native create_user is the only production users INSERT found; hooks/upsert
fixtures need audit rather than exemptions. A native random collision with an old
reservation fails atomically instead of inheriting grants. Never evict reservations
for capacity or introduce an arbitrary ordinary-account limit in this prerequisite;
existing Store/disk failure stays fail-closed, and growth policy needs separate review.

Validate schema/guards/reservations on reopen, before treating them as authority;
missing guards must not be silently repaired. Backfilling living user IDs is identity
infrastructure, **not** primary/factor proof backfill. Pre-install deleted-ID history
is unknown; no human1 grants/proofs existed then, so do not auto-convert old raw-user/
s_48 grants. Privileged SQL can drop guards/copy histories; these are supported
owning-Store lifecycle invariants, not tamper-proof storage.

Realm startup storage applies without requiring receipt_issuer or Service profiles.
H0's same joined current transaction reads it and includes exact realm in its retained
Current equality. Issuer binding/canonical derivation remain a later H2 owner step:
only when configured, prepare fixed actual native receipt issuer_ref + exact opened
Store/realm, preserving ordinary OIDC/H0 when no Human issuer is configured. No
second free-floating realm cache or caller realm constructor. Existing user IDs
that fail the proposed bounded qualification remain ordinary-compatible; source
proof refuses instead of silently remapping them.

First version has no realm replacement/rename API. An issuer-ref change is a
separate configured identity-namespace change (and source-policy/current-proof
fence), not signing-key rotation; it produces different subjects and requires
explicit policy migration. Restoring the same issuer/realm/user deterministically
restores the same account coordinate, not an old issued proof. A future new-realm
migration needs explicit source cutover/regrant/retirement design, never a config
A→B→A overwrite of stored realm. Display labels are independent of realm bytes.

## Production interfaces and current checks

Only private source code prepares `PreparedHumanAuthority` from the actual Store
realm and fixed configured issuer; it retains opened-Store identity and exact immutable
row, not just public strings. A private `CurrentHumanUser` is obtained from the
actual H0 joined current check, including live user, matching append-only user-ID reservation,
exact handle/session and original owner facts. Derive `HumanSubject` only from that
pair, with issuer/store match; reject caller UserId/realm/Identity constructors.
A public parser may validate human1 syntax only, and a fixture hash algorithm is
mere data. Neither returns native evidence, clock observation, AAL or grant.

Add the authority/ledger comparison to the existing bounded current transaction,
not a new async SQL call under paired replay writer. Retain the same exact row
comparison in the eventual connection-scoped paired checker. A valid namespace
row alone never qualifies a legacy primary/factor/session. Store/source record
retirement and original BOOTTIME budget still apply before sign/observe/final
output; stable subject is not a cached lifetime or remote-revocation lease.

Pum's forthcoming `human_users` must parse human1 separately from Service/Workload
s_48 and use only the typed Human evaluator. Existing users/workload_users are not
fallbacks even with equal bytes. A source-backed admin user selector can expose
the canonical Human reference after actual authorized Hop lookup; never derive it
from client email or accept a caller's realm as publication authority. SDK receives
the signed opaque subject and checks source class/issuer/context/current report;
it does not reconstruct a grant from a user's subject calculation.

## Required invariants and acceptance

| Operation | Stable subject / current eligibility expectation |
|---|---|
| Same Store reopen, signing-key epoch rotation, caller-key rotation | Same subject for same issuer/realm/user; old proof/current-key behavior checked independently. |
| Provider reauth/material/CA/key change and A→B→A | Same account subject after legitimate actual reauth; old primary/capture refuses, no material-based new grant ID. |
| Email/name/groups update, user disable/enable | Subject unchanged. authz/current-session revocation applies; disable terminates sessions, enable does not revive them. |
| Native authorized identity link | Same subject only after actual join to that same account; separate/default-conflict accounts remain different. |
| Delete then same email/name/provider re-registration | New user ID and subject. Former ledger ID never reusable. |
| Change user_id, REPLACE/UPSERT reuse, ledger delete/replacement | Refuse and roll back; no grant inheritance or partial reservation changes. |
| Different issuer / fresh authority realm | Different subject; startup namespace mismatch refuses rather than silently rebinding. |
| Public DTO with human1 text, fake UserId/realm/AAL | Syntax/data only, no native source/grant. |

Before source merge: independent literal preimage/hash vectors below, LP32 field
ambiguity and UTF8 byte distinctions, actual SQLite create/noop/reopen/rollback/
FK-failure/delete-recreate/REPLACE/UPSERT/guard corruption tests, actual native
OIDC/LDAP+authorized linking/TOTP H0 source-derived subject, legacy unqualified and
cross-Store refusal. Count key/provider material changes separately from subject
stability. Existing Service/Workload/v1 codec and ordinary native behavior regressions
remain required. No actual code/test pass is asserted by this design.

## Restore, replica and external-provider limits

The realm survives legitimate backup/restore and native user grants retain their
coordinates when the same authoritative dataset is restored. It does not prove the
restore is current: old tombstones/authz/replay state may be missing. Cold restore
must restart issuer runtime to rotate process proof domain, preserve authoritative
replay/user-owner history and use a reviewed restore/fencing procedure. Restoring a
snapshot predating user retirement can revive old data; unsupported arbitrary rollback
cannot be repaired by random namespace claims. Same live realm/key/DB cloned into
independent owners is indistinguishable without external fenced incarnation/shared
linearizable authority. No automatic realm rotation to hide this boundary, nor
blanket restart grant invalidation.

The current source is a single-Store authoritative service, not a qualified replicated
identity database. Future backbone replication must preserve one authority realm,
user-ID history, monotonic current publication and membership fencing. Independent
new Stores initialize new realms even with identical issuer labels/user strings.
Explicit external OIDC issuer/subject trust and LDAP immutable subject semantics
remain provider responsibilities verified by actual adapters/material owners;
same email across issuers is not universal person identity. Google forced reauth,
remote account/directory withdrawal, native local password/recovery and full Human
RPC/SDK/Pum/Root chain stay in the broader queue.

## Literal design vectors (synthetic; not authentication evidence)

Algorithm above was evaluated independently with Python hashlib/struct during
design. This is not an implemented production encoder or test qualification.
Realm hex is decoded to raw32 before LP32; user bytes are exact UTF8.

| Case | Issuer | Realm hex | User ID | Expected subject |
|---|---|---|---|---|
| base | `example-hopae` | `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `u_00000000000000000000000000` | `human1:0489407b9305f47f90756344cdc79c83eddc7b5e292ac82fa88f74c5edbbca9d` |
| new-user | `example-hopae` | `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `u_00000000000000000000000001` | `human1:696883e7a2e271635372616065fd28217bb8783d2ee39869c5497600e7f72cd5` |
| new-realm | `example-hopae` | `0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20` | `u_00000000000000000000000000` | `human1:8cd1b766b0715ec32316f226cd62782f8d4c65669e35f31b343ed0b4118f3cc8` |
| new-issuer | `example-hopae-2` | `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `u_00000000000000000000000000` | `human1:15af33af0b77291201d4f871374084e5e7c3bf5456a341da1df344f5ddeee521` |
| utf8-precomposed | `example-hopae` | `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `u_é` | `human1:c44e971ce61fddd4ec1e107e88c81033badd19ee737eba9d042886f8e999d6a8` |
| utf8-decomposed | `example-hopae` | `000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f` | `u_é` | `human1:c4fe4b7022c8d0a54654f4809dd8f094a95fef4132535ff539e1e622520bb637` |

Base full preimage hex:

```text
686f7061653a6e61746976652d68756d616e2d7375626a6563743a7631000000000d6578616d706c652d686f70616500000020000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f0000001c755f3030303030303030303030303030303030303030303030303030
```

Mutating email/AAL/session/provider/material/signing/caller key is intentionally
not an input to this encoder; lifecycle tests must prove current-owner refusal
where appropriate rather than merely assert hash equality with identical arguments.
