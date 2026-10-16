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
- Add `tools/test_helm_charts.py` (offline lint/render/invariant/refusal tests,
  optional kubeconform validation) and the EN/KO install guide.
