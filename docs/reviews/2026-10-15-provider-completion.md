# Hopae provider completion evidence

Status: Sol 6.1 read-only source audit, not a new passing test run or operating
qualification. Source baseline: Hopae `2a96303`; later time-client work does not
complete the provider requirements below.
[한국어](../ko/2026-10-15-provider-completion.md)

## Implemented boundaries to reuse

The provider registry dispatches OIDC and LDAP. Google has a real preset, while
its forced reauthentication capability is explicitly unsupported. Owned OIDC
scenarios and LDAP TLS/StartTLS fixtures exercise protocol behavior; enum variants
alone do not establish a local-password, email-link or generic OAuth2 provider.
Native password submission authenticates against LDAP, not a self-owned password
database (`src/provider/registry.rs`, `src/provider/ldap.rs`).

Service profiles implement local API keys, remote API verification, Kubernetes
TokenReview, network constraints and explicit prefix routing. Existing tests cover
credential isolation, expiry/scope, network restrictions, publication races and
retained open circuits. The bounded Any/All helper in `src/auth_gateway/mod.rs`
has no production orchestration caller. Prefix routing and network constraints
must not be presented as arbitrary mixed-provider composition.

TOTP enrollment/confirmation/removal and encrypted keys, owner-bound single-use
step-up, external HTTPS MFA and browser/native completion have concrete source
and owned-fixture tests. Lua is bounded boolean eligibility over verified identity;
it does not orchestrate arbitrary connector calls or export secrets. Native
transport, Pumgye service mapping and guest denial already exist and should be
reused rather than reimplemented.

## Open completion work

- Connect actual mixed-provider composition and explicit identity relationships,
  keeping principal/service separation and the shortest budget. Establish the
  self-owned human credential provider/lifecycle scope; current LDAP login is not
  evidence of local account/password support.
- Complete verified human/workload as well as service identity through signed
  permission, paired replay, service credential conversion and final dispatch.
  Projection libraries and service/AAL0 fixtures alone do not prove that scope.
- Complete audited factor/account replacement and recovery, single-use recovery
  assurance, and service-scoped enrollment/admission. Existing TOTP success does
  not close lost-factor recovery.
- Extend bounded connector orchestration where required by the approved extension
  design; retain native authority over identity, assurance, session and grants.
- Implement/qualify external-directory withdrawal of already-issued sessions and
  generation/provider withdrawal for long-lived streams. Reused-channel profile
  refusal is already tested and is a different requirement.
- Qualify actual provider/browser interactions, full-chain withdrawal and denied
  backend effects, exact signed artifacts, Kubernetes and explicitly configured
  operating routes. Real Google-user interaction and full-chain throughput are
  distinct gates from owned mock-provider and component throughput tests.

Do not add unrelated SAML, nested-group or introspection work merely because a
provider name exists. Retain the original full mixed-identity scope without
counting design, source tests, release artifacts and enabled deployment as equal.
