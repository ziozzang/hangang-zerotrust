# Changelog

[Project overview](README.md) · [Design index](docs/README.md)

## Unreleased

- Add the `hangang-world` Helm chart (ADR 0022 P0 packaging): Hangang (Ingress
  controller with ProtectionPolicy enforcement), Hopae, Pumgye and Sumunjang as
  one package with a strict generated `values.schema.json`, digest-pinned
  images, hardened Pods, Secret references only, cert-manager or
  bring-your-own mutual TLS with SPIFFE URI SANs, least-privilege RBAC,
  default-deny NetworkPolicies, client address preservation
  (`externalTrafficPolicy: Local`, PROXY v2, host network), PVCs kept on
  uninstall, an HA guard (replicas > 1 only on PostgreSQL), PDBs, optional
  ServiceMonitor, `helm test` and NOTES.
- Add the `hangang-world-crds` chart with the ProtectionPolicy CRD and the
  aggregated `world-admin`/`world-editor`/`world-viewer` roles.
- Qualify the package with the real component binaries (configuration
  preflight) and on a disposable local k3d cluster: protected request chain,
  401/403 refusals, Sumunjang block, component outages fail closed, withheld
  unprotected Ingress, NetworkPolicies, `helm test`, rollout restart, upgrade
  and rollback. Refuse `hopae.storage.backend: postgresql` until Hopae ships
  its PostgreSQL store; identity profiles request `x-hopae-service-id`, use
  Hopae's 500 ms verify budget and strip Hopae session cookies.
- Add `hopae.admin` (admin mTLS listener on a ClusterIP-only Service, own
  server certificate via cert-manager or BYO, delegation key Secret,
  NetworkPolicy admitting only Hangang and Pumgye) and `pumgye.hopaeOwner`
  (Pumgye v2 `--hopae-owner` over the admin listener with its SPIFFE-pinned
  certificate and an `hsc1` service credential). Qualified offline against
  Hopae `60b3a60`/PR #10 and Pumgye `775e6b9`; Pumgye must still send
  `X-Hopae-Audience`.
- Add `tools/test_helm_charts.py` (offline lint/render/invariant/refusal tests,
  optional kubeconform validation) and the EN/KO install guide.
