# Architecture decisions

All decisions below are **proposed** for the full-stack implementation. They record
user direction and engineering invariants; implementation requires the roadmap gates.

| ADR | Decision |
| --- | --- |
| 0001 | One field authority per domain; reuse identity through delegation, not shared business schemas |
| 0002 | Provider logic remains in Hopae; native entry/transport/lifecycle support belongs in Hangang |
| 0003 | Server-authoritative catalog labels precede integrated resource decisions |
| 0004 | Telemetry exporter is independent; Prometheus metrics and ClickHouse events have different semantics |
| 0005 | Device/workload evidence remains open; unknown cannot become trusted |
| 0006 | Trusted same-origin console packages are pinned imports, not an untrusted-code sandbox |

Alternatives rejected: provider clients in Hangang; arbitrary runtime UI imports;
client-authoritative information grades; one averaged trust score; analytics writes
on every admission; copying session/user data into the network service; and
claiming global atomic revocation from separate DBs and a proxy.

Consequences: more explicit contracts and validation, independent runtime failures,
consistent responsibility boundaries, and measurable native integration. Revisit
an ADR when a requirement or evidence changes, preserving the migration rationale.

Accepted component selection: Sillok for zero-trust ontology; Jikji for main
automatic/semi-automatic orchestration. Proposed integration ADR 0007:
[scoped pentest-to-Guard-to-Hangang remediation](../AUTOMATION.md).

[ADR 0008: implemented HOP1 and console delegation](0008-hopae-native.md).

[ADR 0013: required snapshot backbone and scale-out membership](0013-snapshot-membership-scaleout.md).

[ADR 0014: proposed credential projection after authorization](0014-credential-projection.md)
([한국어](../ko/0014-credential-projection.md)).

[ADR 0015: Kubernetes and IAM authoritative sources](0015-kubernetes-iam-authority.md) ([한국어](../ko/0015-kubernetes-iam-authority.md)).

[ADR 0016: decision cores and metadata adapters](0016-decision-core-metadata-adapters.md) ([한국어](../ko/0016-decision-core-metadata-adapters.md)).

[ADR 0018: draft authority-relative time observations](0018-authority-time-observations.md) ([한국어](../ko/0018-authority-time-observations.md)).
