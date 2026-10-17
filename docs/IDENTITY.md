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

## Console operator assurance

Status: implemented on branches (Hopae `feat/operator-aal`, ADR-0021, PR #18;
Hangang `feat/operator-aal`, PR #25); qualified locally in a real browser with a
virtual WebAuthn authenticator; not yet verified on a live gateway.

Console operators sign in through Hopae with a phishing-resistant factor. Hopae's
`console_operators` policy names the console's application and requires the
configured level (AAL 2 by default, AAL 3 with high-assurance keys) and the
`webauthn` factor on the whole console host, and a fresh passkey use
(`step_up_max_age_secs`) on the console's step-up path. Only a passkey meets or
refreshes these rules; TOTP, external factors and recovery codes do not. An
operator without a passkey is sent to add one before the first console grant; an
optional, dated enrollment grace admits operators with no passkey at all, never
on the step-up path.

Every allowed verify for the console application carries Hopae's operator
assertion (`x-hopae-operator-assertion`): the level, the latest second factor and
its time, high assurance, the policy and whether it is met, signed with Hopae's
dedicated Ed25519 key and valid for 60 seconds. The console pins only public keys,
by key id (the current and, during a rotation, the next), so it holds nothing that
could forge an assertion. The Hangang console verifies it on
every SSO request and enforces its own minimum: sign-in and reads need the policy
(optionally Hopae's grace for reads), every change needs it without grace, and
sensitive changes (publish, activate, factor reset, accounts, configuration)
need the factor used within the console's `sensitive_max_age_seconds`. A refusal
sends the operator through the gateway to the step-up path, where Hopae runs the
passkey ceremony; the console then signs in again with the rotated session. The
console header shows the operator's level and factor.

The Hangang local administrator sign-in remains the break-glass path. It is shown
as such in the header, every break-glass sign-in and change is recorded in the
console audit, and it can be disabled. Admissions are recorded by Hopae
(`operator.console_admitted`); SSO sign-ins, step-up refusals and SSO changes by
the console with the operator's level and factor.

Open: console audit in the durable Hangang account audit store; live-gateway
verification with hardware authenticators.
