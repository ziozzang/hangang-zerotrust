# Design index

[한국어](ko/README.md) · [Project](../README.md)

[Paused implementation handoff — 2026-10-16](HANDOFF_2026-10-16.md) — verified state, remaining gates and resume order.

| Document | Scope |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | Ownership, control/data planes and trust boundaries |
| [Catalog](CATALOG.md) | Resource identifiers, information classes, authoritative labels |
| [Classification](CLASSIFICATION.md) | Deterministic classification, content-analysis candidates |
| [Decisions](DECISIONS.md) | Composition, revisions, failure behavior, obligations |
| [Identity](IDENTITY.md) | Native login/logout, external providers and session revocation |
| [Console](CONSOLE.md) | Native menus, trusted imports and delegated administration |
| [Protocols](PROTOCOLS.md) | Persistent native transports and qualification |
| [Observability](OBSERVABILITY.md) | Prometheus, ClickHouse, exporter and audit integrity |
| [Devices](DEVICES.md) | Open device/workload evidence design |
| [Threat model](THREAT_MODEL.md) | Attacks, bounds and adversarial qualification |
| [Roadmap](ROADMAP.md) | Dependencies, deliverables and acceptance gates |
| [ADRs](adr/README.md) | Proposed architectural decisions |

Draft schemas are under `schemas/`, synthetic examples under `examples/`.

| [Ontology and automation](AUTOMATION.md) | Sillok, Jikji, pentest evidence and guarded routing patches |

[Observability, ontology and pentest feedback loop](FEEDBACK_LOOP.md) — evidence, action and verified outcome reuse.

[Snapshot backbone and scale-out membership](adr/0013-snapshot-membership-scaleout.md) — domain snapshots, leased join/drain/remove and Hangang subscriptions.

[Kubernetes and IAM authority](adr/0015-kubernetes-iam-authority.md) — all four components, source-of-truth modes, RBAC and workload identity.

[Decision cores and metadata adapters](adr/0016-decision-core-metadata-adapters.md) — typed resources, DB backbones and optional plugins.

[Pumgye authorization model revision (proposed ADR 0021)](adr/0021-pumgye-authorization-model-revision.md) — principals, groups, role templates, deny, network zones, explain API.

[Kubernetes-native Hangang World package (proposed ADR 0022)](adr/0022-kubernetes-native-world-package.md) — World CRDs, controller, Gateway API, workload identity, Helm/HA.

- [Public-SDK Workload qualification probe](../tools/native-workload-probe/README.md) — authentication only; real full-chain gates remain.

[Workload K3s qualification preparation](WORKLOAD_WORLD_QUALIFICATION.md) — opt-in native orchestration and pure tests; live execution remains unqualified and requires reviewed exact artifacts.

[Native request-path accounting and snapshots](reviews/2026-10-16-native-hotpath-snapshot-design.md) — proposed source ownership, durable replay and measurement gates.
