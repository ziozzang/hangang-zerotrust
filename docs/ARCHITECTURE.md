# Architecture

[한국어](ko/ARCHITECTURE.md) · [Index](README.md)

Status: proposed cross-component architecture, grounded in existing components.

## Ownership

| Domain | Writer / authority | Consumers |
| --- | --- | --- |
| Hosts, routes, listeners, upstreams, enforcement | Hangang | Console, compiled classifier |
| Providers, users, session validity, authentication strength | Hopae | Hangang and delegated console |
| IP pools, ASN/GeoIP, suspicion, network rules | Guard | Hangang and console |
| Classification vocabulary, resource labels and constraints | Catalog authority | Compiler, Hangang, applications |
| Resource access policy and obligation definitions | Policy authority | Integrated engine |
| Runtime decisions | Hangang enforcement | Applications and bounded telemetry |
| Telemetry projection | Exporter | Prometheus, ClickHouse, console |

A console is an interface to authorities, not a second writer to their tables.
The catalog does not rewrite routing/backends. Hopae does not become a routing
administrator; Guard does not become an account store. The exporter has no
policy mutation credential. Every field has one owning writer.

## Control plane

```mermaid
flowchart TB
  O[Operator / automation identity] --> UI[Hangang management console]
  UI --> CA[Catalog authority]
  UI --> PA[Policy authority]
  UI --> HA[Hopae management API]
  UI --> GA[Guard management API]
  CA & PA --> V[Schema, reference and security validation]
  V --> CO[Bounded compiler]
  CO --> BU[Authenticated compatible bundle]
  BU --> ST[Stage / compare-and-swap / atomic publish]
  ST --> SS[Immutable Hangang snapshot]
  ST --> J[Durable change journal]
```

The first implementation can reuse Hangang's configuration authority and CAS
for bounded catalog/policy definitions. A separate controller is justified when
approval, federation or independent compilation becomes necessary. Storage
location does not establish trust: issuers, schema versions, content hashes and
activation rules do. Catalog and policy updates publish as one compatible bundle.
A node must never combine a new policy with an incompatible old label set.

## Data plane

```mermaid
sequenceDiagram
  participant C as Client
  participant H as Hangang
  participant G as Guard
  participant I as Hopae
  participant D as Integrated engine
  participant A as Application
  C->>H: Request with untrusted credentials/metadata
  H->>H: Canonicalize, resolve protected namespace/resource/action
  H->>G: Authenticated bounded network query
  H->>I: Authenticated native identity/session verification
  G-->>H: Network decision/risk, revision and validity
  I-->>H: Verified identity/assurance, revision and validity
  H->>D: Server-built context and immutable catalog/policy snapshot
  D-->>H: Deny / challenge / allow with supported obligations
  H->>H: Enforce obligations and authority fences
  H->>A: Allowed request with authenticated scoped context
  A->>A: Tenant/row/object authorization and data obligations
  A-->>H: Response with trusted application evidence if required
  H-->>C: Protected response
```

Independent remote queries may run concurrently only after protected namespace
admission, bounded resource resolution and credential-source selection. Known
network denials can terminate early. A network allow never substitutes for
identity/resource authorization. Public resources need explicit anonymous policy;
`public` classification alone does not grant access.

The ordinary path uses immutable compiled structures. No ClickHouse write,
provider discovery or LLM invocation is implicit in every request. Hopae may
perform its own required provider/session checks under an explicit bounded
contract. Decision results carry freshness and policy provenance.

## Current versus planned

Implemented and merged: Hangang routing/resource primitives; trusted pinned
Guard/Hopae console packages and host broker; Hopae external providers, native
login/logout and scoped management delegation; authenticated HOP1 verification
with persistent native Hangang pools; Guard network rules/GeoIP and supervised
signed runtime updates. The deployed console now serves both native menus.
Planned: catalog/classification compiler, integrated multi-source resource
policy, ontology/automation adapters and unified observability exporter.
Device/posture federation remains an open design. No full-stack compliance claim
is made from this inventory.

References: [NIST architecture roles](https://pages.nist.gov/zero-trust-architecture/VolumeB/architecture.html),
[CISA maturity model](https://www.cisa.gov/sites/default/files/2023-04/zero_trust_maturity_model_v2_508.pdf).

## Ontology and remediation control plane

Sillok owns the zero-trust ontology projection and provenance; Jikji owns
automation workflow state. Scoped pentest evidence flows through Sillok and Jikji
to domain-authorized Guard changes and Hangang routing patches. Domain fact
ownership above remains unchanged. See [Automation](AUTOMATION.md) for scoped
automatic/approved execution, partial-failure recovery and CAS rollback.

## Hearim judgment backend

[Hearim (헤아림)](https://github.com/ziozzang/hearim) is selected as one of the
background intelligence/judgment backends used by Jikji. Its documented
`POST /v1/systemone` interface supports Choice / Score / Noul questions and
logprob-derived candidate distributions. This is judgment assistance, not the
resource-policy authority, an authenticated fact source or a replacement for
Sillok/Jikji. Other backends remain possible. Integration is planned.

An adapter must pin model/backend and rubric revisions, minimize evidence sent,
bound deadlines/concurrency and retain question/evidence digests and scoring
diagnostics. Probability and entropy confidence are not calibrated attack risk
or permission to apply a patch. Missing candidates/backend failures yield an
unavailable or review outcome; they cannot silently become an allow decision.
Domain authorization, CAS and audit remain mandatory for every actual change.
Qualification requires deterministic fixtures, malformed/unavailable results,
calibration evidence and tenant/privacy isolation. No per-request inference
dependency is introduced into ordinary enforcement.

Implementation update: trusted Guard/Hopae packages, signed scoped Hopae management delegation, HOP1 verification and native Hangang pools/entry result handling are merged. See [ADR 0008](adr/0008-hopae-native.md); ontology/classification/automation integration remains planned.
