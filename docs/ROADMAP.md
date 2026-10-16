# Roadmap and delivery gates

[한국어](ko/ROADMAP.md) · [Index](README.md)

## Main integration track

1. Guard is a real Hangang sidebar menu, with the existing operator authority;
   use native embedding or a bounded adapter over the deployed admin API.
   Gate: real domain/browser flow, no second login, roles/revocation, audit and
   stale-result cleanup; preserve running data-plane routes.
2. Hopae is a native management menu, using an explicit scoped delegation API
   that respects Hopae grants/CSRF. Gate: users/session/events/status operations
   and real-actor audit; no service-key bypass of provider/user policy.
3. Hopae native protocol/client plus native Hangang login/logout integration.
   Gate: HTTP/native parity, bounded parsing, service authentication, expiry,
   revocation, cancellation, pooling, provider failure and realistic load.
4. Publish compatible versions after native build/security/integration review;
   signed activation follows component update mechanisms. No debug binary is
   substituted for the production routing process to demonstrate a menu.

## Cross-component design subtask

A. Catalog vocabulary, resource/action bindings, authoritative label sources,
   schema/reference validation and downgrade workflow.
B. Deterministic classification compiler/resolver and shadow evaluation.
C. Typed integrated policy evaluator with revision/freshness/obligation contracts.
D. Exporter with Prometheus metrics, ClickHouse events, bounded replay and audit.
E. Device/workload design only after environmental/assurance questions are resolved.
F. Unified console: [ADR 0019](adr/0019-decision-events-exporter.md) decision events
   and explain APIs, then [ADR 0020](adr/0020-unified-console-redesign.md) task-oriented
   console (P0 decision log, request detail, unified audit, UI kit; P1 policy editor
   with simulator; P2 charts/ASN workflows). Gate: per-page acceptance criteria in
   EN/KO, light/dark, desktop/390 px, plus D1 overhead and privacy qualification.

```mermaid
flowchart LR
  C[Catalog schema] --> CL[Classification compiler]
  CL --> P[Integrated engine]
  I[Identity contracts] --> P
  G[Network contracts] --> P
  P --> H[Hangang enforcement qualification]
  E[Exporter design] --> O[Operational evidence]
  H --> O
  D[Device/workload ADR — open] -.-> P
```

## Concrete next deliverables

- Native plugin manifest/API/lifecycle specification and adversarial fixtures.
- Hopae delegated-administration ADR and scope/actor/CSRF compatibility tests.
- Provider-independent verify contract and golden HTTP/native corpus.
- Reserved native auth facade with return-target/logout-scope tests.
- Catalog + policy + bundle schemas, valid and rejected examples.
- Classification resolver prototype, resource binding collision tests and measured
  compile/lookup limits.
- Exporter event schema and sink-spool/privacy/failure qualification.
- Integrated policy decision matrix and traceable publication/rollback journal.

## Performance acceptance

10,000 and 100,000 decisions/sec are qualification targets. Report achieved
throughput, workload, CPU/RSS, p50/p95/p99, error/drop counts and revocation lag.
Measure each component and the full path; distinguish warm/cold session work,
provider interaction, TLS, saturation and concurrent durable admin changes.
Telemetry/classification must have explicit overhead budgets. No target is
considered achieved by transport-only counters without authorization semantics.

## Status rules

Record planned → designed → prototype → security reviewed → qualified → released
→ operationally observed. Record actual evidence and unresolved defects. Do not
mark a milestone complete because a document or route placeholder exists.
