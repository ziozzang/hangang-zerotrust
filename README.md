# Hangang Zero Trust

[한국어](README.ko.md) · [Design index](docs/README.md) · [Roadmap](docs/ROADMAP.md)

The architecture and contract repository for a zero-trust backbone built around
[Hangang](https://github.com/ziozzang/hangang),
[Hopae](https://github.com/ziozzang/hopae), and
[Guard](https://github.com/ziozzang/sumunjang).

Hangang enforces admission and resource policy. Hopae owns user identity,
sessions and external authentication providers. Sumunjang (the Guard component)
owns network controls and risk evidence. Pumgye owns deterministic service roles,
permissions, information classes and user/IP authorization matrices. The required
architecture deploys Hopae, Sumunjang and Pumgye as independent servers; Pumgye
core and server are separate crates. Earlier embedded enforcement remains the
qualified baseline while authenticated distributed integration is being built. Jangbu, existing Sacho, Sillok and Saheon observability/audit
integration remain design work, with Prometheus and ClickHouse connections.

**This repository contains design proposals, example contracts and validation,
not a shipped full-stack implementation.** Device and workload evidence needs
further design. Existing component capabilities and pending integration work
are tracked separately; a diagram is not a production assurance claim.

## System view

```mermaid
flowchart TB
  subgraph DP["Request enforcement"]
    C[Client] --> H[Hangang enforcement]
    H <-->|authenticated native calls| I[Hopae authentication gateway / sessions]
    I <-->|OIDC / Google / LDAP / API / local: mixed-auth design| P[Authentication sources]
    H <-->|authenticated native calls| G[Sumunjang: Guard network controls]
    H --> D[Pumgye authorization server: distributed integration pending]
    D --> CL[Compiled classification / catalog]
    V[Device / workload evidence: proposed] -.-> D
    H --> B[Application / resource]
  end
  subgraph CP["Configuration and management"]
    UI[Hangang console: Sumunjang / Hopae / Pumgye] --> A[Domain-owned management APIs]
    UI <-->|ID/PW or mapped SSO| CA[Hangang console account authority]
    CA <-->|live native SSO verification| I
    A -->|validated policy / catalog bundles| H
    A --> I
    A --> G
    A --> D
  end
  subgraph OP["Observability and security automation: planned integration"]
    E[Jangbu: bounded logs / traces] --> CH[ClickHouse logs / traces / events]
    M[Prometheus metrics] --> N[Evidence normalization / correlation]
    M --> SA[Sacho: existing monitoring / status / alerts]
    CH --> N
    PT[Authorized scoped pentest] --> N
    N --> S[Sillok ontology / provenance]
    S --> J[Jikji automatic / semi-automatic workflows]
    J <-->|bounded judgment / scoring| HE[Hearim: one intelligence backend]
    J <-->|bounded LLM requests| DG[Dorang: LLM Gateway]
    DG <-->|provider routing| LP[LLM providers / model endpoints]
    J --> K[Scope / authorization / revision validation]
    K -->|scoped changes| A
    R[Canary / post-change pentest / regression checks] -->|verified outcomes| N
  end
    H & I & G -->|audit evidence| AU[Saheon: audit / integrity / verification]
    AU -->|bounded evidence| S
  H & I & G -->|bounded logs / traces / events| E
  M -->|scrape| H & I & G & E
  H & G -->|applied changes| R
```

Request enforcement uses bounded native calls and compiled policy. Sillok and
Jikji operate on the control plane; ordinary requests do not wait for analytics,
ontology reasoning, LLM execution or pentesting. Domain APIs retain write authority.

## Security feedback loop

```mermaid
flowchart LR
  O[Logs / traces / metrics + scoped pentest] --> S[Sillok facts / relationships / evidence]
  S --> J[Jikji investigation / proposal]
  J <-->|judgment assistance| HE[Hearim / other backends]
  J <-->|LLM assistance| DG[Dorang: LLM Gateway]
  DG <-->|provider routing| LP[LLM providers / model endpoints]
  J --> V[Pre-authorized scope or reviewed approval + domain validation]
  V --> A[Guard mitigation / Hangang routing patch]
  A --> T[Canary + post-change pentest + normal-traffic checks]
  T --> R[Measured result / uncertainty / retain or CAS rollback]
  R -->|provenance and outcome reuse| S
```

Observe, propose, authorize, apply and verify are distinct stages. Pentest targets
and probe budgets remain explicitly scoped. Rollback preserves intervening changes;
verified outcomes become reusable evidence, not automatically authorized global rules.


Read [Architecture](docs/ARCHITECTURE.md),
[Catalog](docs/CATALOG.md), [Classification engine](docs/CLASSIFICATION.md),
[Integrated decisions](docs/DECISIONS.md), [Native identity integration](docs/IDENTITY.md),
[Console plugins](docs/CONSOLE.md), [Runtime protocols](docs/PROTOCOLS.md),
[Observability](docs/OBSERVABILITY.md), [Ontology and automation](docs/AUTOMATION.md),
[Feedback loop](docs/FEEDBACK_LOOP.md), and [Device/workload questions](docs/DEVICES.md).

## Validate the draft contracts

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
.venv/bin/python tools/validate_contracts.py
```

Schema validity is only one check. The validator also checks cross-document
references and rejects representative unsafe bundles. Authorization enforcement,
HTTP/native parity, revocation, parser and performance qualification remain
implementation gates. All examples use reserved domains and synthetic identities.

Sillok is the selected zero-trust ontology engine. Jikji is the main automatic
and semi-automatic orchestration engine. Scoped pentest evidence feeds Guard
mitigations and validated Hangang routing patches; see
[Ontology and security automation](docs/AUTOMATION.md). Integration is planned.

[Closed-loop design](docs/FEEDBACK_LOOP.md) connects logging, distributed tracing,
monitoring and scoped pentesting to ontology-backed action and verified outcome reuse.

## Dorang LLM gateway

[Dorang](https://github.com/ziozzang/dorang) is the LLM Gateway in the package
architecture. Jikji's LLM-assisted workflows use Dorang to reach model/provider
endpoints; Hearim remains a separate judgment backend. This integration is planned.
Dorang does not own resource authorization or policy publication. Model calls stay
on the bounded control plane, with identity, service permissions, evidence
minimization and audit enforced by the surrounding zero-trust components.

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

The embedded Hopae page can explicitly follow Hangang console authority, with a
Hopae SSO button below local account login. See [ADR 0009](docs/adr/0009-console-authority-sso.md)
for mapping, request/session checks and ownership boundaries.

[품계 / Pumgye ownership and implementation plan](docs/adr/0010-pumgye-ownership.md) · [한국어](docs/ko/0010-pumgye-ownership.md)

[Pumgye integration qualification](docs/PUMGYE_QUALIFICATION.md) · [한국어](docs/ko/PUMGYE_QUALIFICATION.md)
