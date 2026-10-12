# Implementation backlog

[Roadmap](docs/ROADMAP.md) · [한국어](TODO.ko.md)

## Main integration
- [ ] Guard menu in the actual deployed Hangang console, using its existing authority.
- [ ] Qualify trusted plugin lifecycle, backend credential isolation, roles, revocation and audit.
- [ ] Scoped Hopae delegated-management contract preserving grants/CSRF and actor identity.
- [ ] Hopae user/session/event/status menu, native console style and shared authentication.
- [ ] Provider-independent native verify request/result contract and HTTP parity corpus.
- [ ] Authenticated bounded Hopae transport and Hangang persistent pool.
- [ ] Native Hangang login/logout facade without required Lua scripts.
- [ ] Signed compatible component qualification and release.

## Design subtask
- [x] Architecture/ownership diagrams and English/Korean design documents.
- [x] Catalog, classification, integrated decision and exporter proposals.
- [ ] Owner review of class vocabulary, tenant/object evidence and downgrade workflow.
- [ ] Decide native protocol layout, exact delegation semantics and revocation guarantees.
- [ ] Classifier and integrated policy implementation/qualification.
- [ ] Exporter implementation, ClickHouse schemas, Prometheus and privacy/failure tests.
- [ ] Device/workload evidence ADR after environmental investigation.

Runtime implementation checkboxes require actual evidence, not design completion.

## Ontology and automated security hardening
- [x] Record Sillok/Jikji component selection and remediation design.
- [ ] Versioned bounded Sillok ontology adapter with provenance/tenant isolation.
- [ ] Jikji automation and semi-automation tool/approval integration.
- [ ] Scoped pentest job and normalized finding contracts.
- [ ] Guard mitigation and Hangang routing patch adapters with CAS/idempotency.
- [ ] Durable recovery, canary verification and conflict-safe rollback.
- [ ] Adversarial qualification and request-performance isolation.
