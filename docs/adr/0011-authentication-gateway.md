# ADR 0011: Hopae as an authentication gateway

Status: accepted direction; connector/composition implementation pending.

## Scope

Hopae is an authentication gateway for people, services, workloads and external
identities. Multiple Google/OIDC issuers, LDAP directories, API authentication
relays and trusted network evidence must coexist. Its current registry supports
multiple OIDC providers; LDAP, API relay and network composition are not implemented.
ProviderKind declarations alone are not implementation evidence.

## Ownership and common evidence

Connectors own protocol verification and preserve provider/issuer, subject,
principal kind, realm, verification method, freshness, assurance semantics and
provenance. Hopae composes verified evidence into a bounded authentication result.
Sumunjang supplies IP/CIDR/network admission and risk evidence; trusted source IP
comes from Hangang transport/edge context. Network evidence is an authentication
input, not a client header claim. Pumgye owns service permissions and information
classes. Hangang enforces the final request decision.

External subjects are namespaced by provider/issuer and realm. Matching email,
username or directory display name does not silently merge identities. Linking
requires verified authority and an explicit policy or approved account-link flow.
Machine credentials do not invent human MFA levels. Network-only authentication
can identify an explicitly configured network principal; it does not imply a
human identity or an unrestricted internal-user grant. Service policy must declare
which principal/evidence kinds it accepts; defaults remain guest/no permission.

## Composition

Support explicit `any`, `all` and step-up chains with configured connector IDs,
credential sources and bounded deadlines. Examples: LDAP plus required network
scope; Google or partner OIDC; service API credential plus network enforcement.
Alternatives must be declared, not a silent fallback after a failed mandatory
factor. Conflicting verified subjects, issuers or realms fail closed unless a
predeclared verified relationship explains their combination. Unknown evidence,
missing mandatory factors, stale proofs and partial backend failure cannot create
an allow. Keep revocation, audit and original verification provenance.

The existing browser redirect/callback Provider trait cannot alone represent
LDAP bind, token introspection, API relay or network proofs. Introduce a common
connector/evidence contract with browser and direct-credential adapters. Preserve
existing OIDC transaction/nonce/session protections through an adapter.

## API authentication relay and translation

Operators bind each relay to fixed trusted endpoints, inbound credential formats,
claim mappings, issuer namespaces and intended applications. Verification can use
an external API auth service, bearer-token introspection or a directory adapter.
Translation may issue or inject a destination-specific credential only for the
configured audience and permitted service path. Never let the caller choose an
arbitrary relay destination or copy a credential to unrelated backends. Bound
responses, concurrency and timeouts; restrict TLS/redirects and redact secrets.
Keep incoming credentials, verified identity and outgoing credentials distinct.
Only an authorized upstream request receives translated credentials; browser
responses, caches, logs, traces and ontology records must not expose them.

## Implementation procedure and acceptance gates

1. Define bounded evidence/principal schemas and connector health/capabilities.
2. Adapt existing multi-OIDC providers without weakening issuer/nonce/PKCE/session checks.
3. Implement API relay and LDAP connectors, fixed endpoint validation and secret references.
4. Add network evidence and deterministic any/all/step-up composition.
5. Extend native HOP1/HTTP contracts and Pumgye principal-kind gates consistently.
6. Add unified administration for connectors, chains, mappings, health and audit.
7. Qualify mixed external identities, subject conflicts, partial failures, revocation,
   injection, credential isolation, HTTP/native parity and bounded performance.
8. Merge, publish and deploy only implemented/tested behavior; record remaining design work.

Jangbu/Sacho/Sillok/Saheon remain separately scoped observability/ontology/audit
integration designs. Models cannot produce authenticated evidence or grant rights.

Reference contracts: [OAuth token introspection (RFC 7662)](https://www.rfc-editor.org/rfc/rfc7662), [token exchange (RFC 8693)](https://www.rfc-editor.org/rfc/rfc8693), and [LDAP authentication (RFC 4513)](https://www.rfc-editor.org/rfc/rfc4513). These are design references; protocol support requires implementation evidence.
