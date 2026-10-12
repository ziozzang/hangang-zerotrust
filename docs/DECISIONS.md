# Integrated decision engine

[한국어](ko/DECISIONS.md) · [Index](README.md)

Status: proposed. Examples are reference contracts, not production decisions.

## Facts and authorities

The engine consumes authenticated facts, not a blended universal trust score:
Hopae subject/session/assurance; Guard network risk and explicit deny/allow;
catalog resource labels/action/tenant requirements; optional device/workload
facts from a configured authority; and the active policy bundle. Each fact has
issuer, audience, revision, timestamps/validity and verified provenance where
applicable. Request context is constructed by Hangang after canonical admission.

The default protected decision is deny. Allow requires all required evidence,
a matching explicit grant and enforceable obligations. Explicit denies win over
grants within a policy scope. Guard's network allowlist removes network blocking
for the intended scope; it does not authorize a subject or override catalog
restrictions. `public` classification requires an explicit anonymous grant.

## Pipeline

Resolve resource/action → validate source/freshness → apply explicit denials →
validate identity/session/assurance → match resource/tenant/entitlement conditions
→ compute obligations → check enforcement support → issue bounded decision.

Outcomes: `allow`, `deny`, `challenge`, `unavailable`. `challenge` asks for a
specific supported authentication step; it is not a partial allow. `unavailable`
is a dependency failure, not proof that a user is unauthorized. Hangang maps
results under explicit route failure policy; protected routes fail closed.

An allow includes decision ID, resource/action, principal binding, policy and
catalog revisions, identity/network revisions, supported obligations and
`valid_until`. The validity is the minimum of all required facts, session/token
expiry and policy constraints. The enforcement point terminates or revalidates
long-lived work on expiry/revocation/policy change; initial admission is not a
perpetual lease for a stream or upload.

## Policy format

Start with typed, bounded conditions and explicit resource/action scopes.
Entitlements, tenant relationships, authentication strength, required fact
sources and network suspicion are separate fields. Reject unknown operators,
unknown obligation kinds and conflicting catalog references at compile time.
Use a pure Rust evaluator over an immutable compiled snapshot. Lua can remain
an optional bounded control-plane compiler; login/logout and fundamental
identity contracts are native features, not scripts an operator must reproduce.

The draft `policy.schema.json` shows a deliberately small subset. It does not
pretend to cover arbitrary SQL-like expressions, deny-rule conflicts or dynamic
object assertions. Expanding the language requires an ADR and adversarial cases.

## Revisions, cache and revocation

Use an authority epoch + monotonic revision for bundles. A decision binds to the
compatible catalog/policy pair, identity/session epoch and Guard revision. A
counter alone is not globally unique after reinstallation. Subscribers retire
old grants when authority changes. Rollback is an authenticated new publication.

Guard IP-result caching remains optional, normally off, and strictly 1–5 seconds
when enabled. It cannot be reused as a cache for integrated principal/resource
decisions. Combined caches default off; if introduced, keys bind subject,
session, issuer, tenant, resource, action, context, all relevant revisions and
validity. An invalidation/expiry event fences cached grants and pooled operations.
Connection authentication does not cache per-request authorization.

## Obligations and application boundary

Examples: require tenant/row authorization; disallow export; require bounded
field masking; strip specified upstream cookies; suppress sensitive response
logging; attach authenticated scoped context. Enforcement capability is declared
and versioned. Unsupported obligations cannot be silently ignored. Application
object checks remain required where the gateway lacks authoritative metadata.

Admin RPC and a separate policy DB are not one transaction. Recheck authority
before dispatch and disclosure; an already accepted remote mutation may finish
after revocation. Journal attempts/outcomes, identify uncertain results, and do
not retry mutations automatically. Stronger cross-service fencing requires a
separately designed grant/commit protocol and cannot be claimed from HTTP proxying.
