# ADR 0010: Pumgye authorization and component ownership

Status: accepted design; runtime implementation and qualification pending.

## Decision

Pumgye (품계) is the deterministic authorization manager. Hopae establishes
identity and owns providers, users and sessions. Sumunjang (수문장), the new
component name for Guard, supplies network admission and IP risk evidence.
Hangang enforces the combined decision and hosts administration.

Pumgye owns service-scoped roles, permissions, information classes and the
user/network authorization matrix. Its compiled core is embedded in Hangang.
Hangang's revisioned configuration authority publishes policy; no shared,
multi-writer Hopae or Guard user database is introduced.

An authenticated user without a service assignment is guest and has no rights.
Authorization requires the requested permissions and class in both the user
assignment and the trusted source-network assignment. IP rights cannot upgrade
user rights. Longest-prefix matching selects a network assignment; a more
specific guest assignment overrides a broader allow. Missing evidence, unknown
services/actions/classes and invalid policies deny access. Sumunjang denial
always dominates. A gate requiring Sumunjang enforcement cannot accept observe
mode, unavailable evidence or fail-open transport behavior as authorization.

The service, action and information class come from protected route policy.
Subject evidence comes from authenticated Hopae verification; source IP comes
from Hangang's trusted transport/edge context. Browser, Lua and origin headers
cannot establish these facts. Authentication success alone does not grant access.

## Implementation procedure

1. Build a bounded Rust policy compiler and immutable Pumgye evaluator. Validate
   references, role inheritance, class vocabulary and document size before publish.
2. Integrate policy with native Hangang configuration, CAS, audit and existing
   administrator authorization. Add a service/user/IP matrix to the console.
3. Attach decisions to protected resource namespaces. Preserve canonical-path,
   downgrade, header isolation and revocation fences. Authorize before serving
   cached content; terminate affected streams when policy is revoked.
4. Qualify guest denial, service separation, read/write permissions, information
   classes, IPv4/IPv6 prefix overrides, stale policy, unavailable/denying network
   evidence, spoofed headers and administrator/viewer separation.
5. Review, merge and deploy tested builds; verify through actual HTTP/native
   and browser paths. Do not claim 100k end-to-end QPS from core microbenchmarks.

Existing authentication-only routes remain explicitly distinguishable from new
Pumgye-protected routes. No broad production grant or automatic blocking policy
is inferred from deployment. Guard identifiers, protocol magic, release names
and updater URLs remain compatible during the Sumunjang branding transition.

## Observability components: design scope

Jangbu (장부) is the separate logging and tracing collection/storage/search
module, with ClickHouse and bounded exporters. Prometheus provides metrics.
Saheon (사헌) owns the audit system: authorization changes, access decisions,
administrator actions and integrity/verification views. Domain authorities still
record changes atomically; Saheon receives bounded audit evidence without becoming
a policy writer or introducing synchronous analytics writes on request paths.
Sacho (사초) already exists and is reserved for monitoring, status and alerts;
it is not assigned ClickHouse log storage or recreated by this project.
Sillok (실록) builds facts, relationships and provenance from correlated evidence.
Jikji orchestrates reviewed or pre-authorized actions, with Hearim as judgment
assistance. Applied state and verification outcomes return through Jangbu into
Sillok. None of these components grants Pumgye rights or synchronously blocks
ordinary requests while writing analytics. Their integration remains design work.
