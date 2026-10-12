# Implementation backlog

[Roadmap](docs/ROADMAP.md) · [한국어](TODO.ko.md)

## Main integration
- [x] Guard menu package and native host broker using the existing Hangang authority; deployed console activation tracked below.
- [x] Qualify trusted plugin lifecycle, backend credential isolation, roles, revocation and audit.
- [x] Scoped Hopae delegated-management contract preserving grants/CSRF and actor identity.
- [x] Hopae user/session/event/status package, native style and host authentication with independent native Hopae grant/session checks.
- [x] HOP1 provider-independent native verify contract and real-session HTTP parity cases.
- [x] Authenticated bounded Hopae transport and Hangang persistent pool.
- [x] Native entry routing/result support for existing Hopae login/logout without required Lua scripts.
- [x] Qualified component releases: signed Hangang/Guard assets and checksummed Hopae assets.

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

## Observability / ontology / pentest feedback
- [x] Record the full observation-to-action-to-verification loop in English/Korean.
- [ ] Correlate bounded logs/traces/metrics and scoped pentest findings with provenance.
- [ ] Sillok fact/hypothesis/policy/applied-state/outcome distinctions and retraction.
- [ ] Jikji case lifecycle, evidence retrieval and bounded outcome reuse.
- [ ] Post-change pentest and normal-traffic regression checks with predeclared criteria.
- [ ] Feedback amplification, misleading success and cross-tenant adversarial tests.

- [x] Select Hearim as one intelligence/judgment backend and update diagrams.
- [ ] Bounded Jikji/Hearim adapter, provenance, error handling and calibration qualification.

## Integration evidence — 2026-10-12

Merged [Hangang #1](https://github.com/ziozzang/hangang/pull/1),
[Hopae #1](https://github.com/ziozzang/hopae/pull/1), and
[Guard #1](https://github.com/ziozzang/hangang-guard/pull/1).

- Hangang: 1,229 all-target Rust tests passed (58 explicit ignores), plus new native proxy parity and signed assertion tests; strict Clippy and browser lifecycle/role tests passed.
- Hopae: 384 unit + 358 scenario tests passed (40 explicit ignores), 39 gateway cases passed; real provider/session/grant/delegation tests and strict Clippy passed.
- Guard: workspace and packaging tests passed; console generation reproduced the same manifest digest.
- Actual isolated console + Guard runtime and a signed Hopae fixture exercised both menus, target IDs, viewer denial, secret isolation and logout disposal.
- [x] Activate merged binaries/packages in the deployed console; live HTTPS menus, anonymous denial, native entry redirects, logout disposal and Guard signed update status verified.
- [x] Complete native platform qualification and publication: Hangang (5 targets), Guard (4), Hopae (4).

Published and deployed on 2026-10-13: [Hangang v0.3.1](https://github.com/ziozzang/hangang/releases/tag/v0.3.1), [Guard v0.3.1](https://github.com/ziozzang/hangang-guard/releases/tag/v0.3.1), [Hopae v0.0.2](https://github.com/ziozzang/hopae/releases/tag/v0.0.2). Hangang/Guard runtime signatures were verified before deployment; Hopae checksums were verified. Guard supervised signed updates are enabled. Hopae has no signed automatic updater.

- [ ] Measure end-to-end Hopae session throughput; transport qualification alone does not establish 100k QPS.
