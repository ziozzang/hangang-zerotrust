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
- Qualify the remaining ADR 0022 gates on the remote k3s test cluster after a
  verified off-host backup: revocation latency (Pumgye/Sumunjang p99 ≤ 0.05 s),
  10-minute API pause, cert-manager rotation (no live reload in Hopae, Pumgye,
  Sumunjang) and a PDB-guarded node drain; full cleanup to baseline.
- Wire the component live-reload and observability knobs: Hangang
  `maxStalenessSeconds` (ADR 0022 bounded staleness), `readiness`
  (`snapshot`/`fresh`) and `tlsReloadSeconds`; Hopae `tlsReloadSeconds`
  (`reload.tls_interval_secs`) and `authentication.reloadIntervalMs`, with
  profile and projection edits excluded from the rollout checksum and the
  ConfigMap mounted as a directory; Pumgye and Sumunjang TLS polling;
  Sumunjang HTTP readiness/liveness probes on a probe-only listener.
  ServiceMonitors for Hangang, Pumgye and Sumunjang (mutual TLS with a
  chart-issued scrape client certificate and read-only metrics tokens from
  the credentials Secret; Hopae has no `/metrics`), metrics NetworkPolicy
  rules, and an optional PrometheusRule with the documented alerts.
- Re-qualify certificate rotation on the remote k3s cluster with the
  component fixes: after a forced cert-manager renewal Hangang, Hopae,
  Pumgye and Sumunjang served the new serial within about 2 minutes without
  restarts; 2028/2028 protected requests succeeded; cleaned up to baseline.
- Serve the Hangang administration API over TLS also when it stays on
  loopback, so sidecars and debug containers in the Pod network namespace
  never see a plaintext administration endpoint.
- Add the Hopae ServiceMonitor (admin listener, mutual TLS, `hsc1` `metrics`
  service credential; Hopae PR #19) and Hopae alerts; optional console
  operator assurance: Hopae `console_operators` (PR #18) with an Ed25519
  seed Secret, and the Hangang console adapter sidecar (`hangang-console`,
  Hangang PR #25) reaching the admin API over TLS (`--upstream-ca`), with
  Hopae SSO over HOP1 mTLS, `operator_policy` pinning the assertion public
  keys (rotation via `nextKey`), `--disable-local-login`, the operator audit
  store and `--audit-log`. All off by default.
- Add `tools/test_helm_charts.py` (offline lint/render/invariant/refusal tests,
  optional kubeconform validation) and the EN/KO install guide.
