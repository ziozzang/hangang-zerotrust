# Native identity integration and provider boundary

[한국어](ko/IDENTITY.md) · [Index](README.md)

Status: accepted ownership direction; endpoint/fast-transport contracts proposed.

## What stays in Hopae

Google/OIDC and other provider protocols, discovery and provider secrets,
authorization-code exchange, token validation, provider-specific callbacks,
OAuth state/nonce/PKCE, user directory, application authentication policy,
identity/session creation, step-up, grants, expiry and revocation. These remain
in the external Hopae runtime. Moving them into Hangang duplicates security
state and puts provider outages/code in the routing process.

## What becomes native in Hangang

A first-class Hopae client and route binding; verified client/request context;
authenticated persistent transports; native login/logout entry points; safe
redirect/return-target routing; controlled forwarding of Hopae cookie updates;
identity header stripping/reassertion; session/authority fences for live work;
and unified console integration. Shared provider-independent contracts/codecs
can be libraries. Importing a contract does not import provider credentials.

The operator should not have to implement login/logout or trusted metadata
construction in Lua. Optional Lua policy configuration does not become the
security boundary for a native identity operation.

## Proposed native facade

`/.hangang/auth/login` and `/.hangang/auth/logout` are provisional names; reserve
and validate the namespace before implementation. Each is bound to an explicit
Hopae application/portal/issuer configured by the operator. Never derive a
credential destination from an arbitrary query string or Host header.

Login: canonicalize the original protected resource → validate return target
against the registered application → send/redirect to Hopae's native login flow
→ let Hopae complete provider interaction and session binding → resume only at
an approved application target. Hangang does not exchange an OIDC code, generate
provider state, validate a provider token, or invent a user session.

Logout is a state-changing operation and needs a native CSRF/origin contract,
not an unauthenticated GET with ambient cookies. Hopae revokes the applicable
session and issues cookie clearing/rotation. Hangang fences matching local grants
and live work. Global upstream-provider logout is provider-dependent and cannot
be promised by clearing an application cookie. Document exact logout scope.

## Fast verification

Hopae's native transport must enter the same verification engine as HTTP:
application/host binding, gateway identity, handle/token validation, assurance,
limits, freshness, deny/redirect behavior and safe output headers. No shortcut
may skip engine checks merely because a connection was previously authenticated.
Guard framing can inform pooling and lifecycle; identity inputs require a bounded
variable payload and different message semantics. See PROTOCOLS.md.

## Delegated management

Hangang console login proves a management actor to the configured authority.
Hopae still owns the policy deciding which actors may administer its users and
sessions. A dedicated issuer/audience/action-scoped delegation contract must map
an authenticated operator to a Hopae management grant. Do not forward client
`X-User` headers or replace Hopae's cookie/grant/CSRF rules with an unrestricted
backend service key. Administrative identity and end-user identity are distinct.

An adapter may reuse existing Hangang account sessions without opening their DB.
It must verify those sessions on each management request, recheck before writes
and disclosures, drop stale UI results after logout, preserve the actual actor
in audit, and keep service credentials out of browser discovery/storage.

The native application login/logout facade is distinct from console operator
login/logout. The existing Hangang administrator account API continues to own
its own operator sessions. A console extension does not automatically turn an
end-user Hopae session into a Hangang administrator. Attribute/role mappings
require explicit issuer and management-grant policy.

Native entry integration uses Hopae’s existing `/_hopae/login` and `/_hopae/logout` contracts. Provider/session logic and logout confirmation remain in Hopae.
