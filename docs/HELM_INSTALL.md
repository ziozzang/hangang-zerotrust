# Installing Hangang World with Helm

[한국어](ko/HELM_INSTALL.md) · [Design index](README.md) · [Chart reference](../charts/hangang-world/README.md)

This guide installs the integrated Hangang World package (ADR 0022 P0 packaging): Hangang, Hopae, Pumgye and Sumunjang from the `hangang-world` chart, and the `world.hangang.dev` CRDs from the `hangang-world-crds` chart. The charts are validated offline (`helm lint`, `helm template` across profiles, Kubernetes/cert-manager/Prometheus Operator schema validation and a render test); they were also installed and functionally qualified on a disposable local k3d cluster with locally built images ([qualification](#qualification--disposable-local-cluster-2026-10-17)); no production or registry-backed install exists yet. See [What still blocks a production install](#what-still-blocks-a-production-install).

## Prerequisites

- Kubernetes 1.27 or newer; a CNI that enforces NetworkPolicy (otherwise the policies are inert).
- cert-manager 1.12 or newer for `tls.mode: certManager` (or prepared TLS Secrets for `existingSecrets`).
- A load balancer that supports `externalTrafficPolicy: Local`, or one that sends PROXY protocol v2, if any `ProtectionPolicy` uses `network.enforcement: Required`.
- Component images published to a registry you trust, referenced **by digest**.
- Optional: Prometheus Operator for `monitoring.serviceMonitor`; PostgreSQL for Hopae with more than one replica.

## Install

1. Create the namespace and the credentials Secret. Use random values of at least 32 bytes and keep them out of version control:

   ```sh
   kubectl create namespace hangang-world
   kubectl -n hangang-world create secret generic hangang-world-credentials \
     --from-literal=hangang-admin-token="$(openssl rand -hex 32)" \
     --from-literal=hopae-gateway-key="$(openssl rand -hex 32)" \
     --from-literal=guard-collector-token="$(openssl rand -hex 32)" \
     --from-literal=guard-admin-token="$(openssl rand -hex 32)" \
     --from-literal=pumgye-decision-token="$(openssl rand -hex 32)" \
     --from-literal=pumgye-admin-token="$(openssl rand -hex 32)"
   ```

2. Install the CRD chart (cluster-scoped, once per cluster):

   ```sh
   helm upgrade --install world-crds charts/hangang-world-crds
   ```

3. Write a values file with your image digests, Hopae portal and applications, and the client address mode. Start from `charts/hangang-world/ci/minimal-values.yaml`; never put secret values in it.

4. Install the package:

   ```sh
   helm upgrade --install world charts/hangang-world -n hangang-world -f my-values.yaml
   helm test world -n hangang-world
   ```

5. Protect routes. With `requireProtection: true` (default) an Ingress of class `hangang` is published only when a `ProtectionPolicy` applies to it:

   ```sh
   kubectl -n shop apply -f protection-policy.yaml
   kubectl -n shop get protectionpolicies
   ```

## Choosing the client address mode

| Mode | Use when | Requirement |
| --- | --- | --- |
| `serviceLocal` | Cloud or MetalLB load balancer | `service.type` LoadBalancer or NodePort; traffic reaches only nodes with a ready gateway Pod |
| `proxyProtocol` | L4 load balancer that sends PROXY v2 | `proxyProtocolFrom` lists the load balancer source CIDRs only; keep kubelet probe sources out of it |
| `hostNetwork` | Bare-metal edge nodes | Gateway Pods bind host ports; NetworkPolicies do not apply to host-network Pods |
| `none` | Identity-only policies | Policies with `network.enforcement: Required` are withheld |

## Certificates

`tls.mode: certManager` issues one certificate per component with both server and client authentication, the Service DNS names (`<release>-hangang-world-<component>.<namespace>.svc[.cluster.local]`) and the SPIFFE URI SAN of its ServiceAccount. With an empty `issuerRef.name` the chart bootstraps a private CA in the namespace; production installs should point `issuerRef` at an Issuer or ClusterIssuer of their PKI that fills `ca.crt` (CA or Vault issuers do; ACME issuers do not and are unsuitable for internal mTLS). With `tls.mode: existingSecrets`, provide one `kubernetes.io/tls` Secret per component with `tls.crt`, `tls.key` and `ca.crt` and the same SANs and usages.

## Scaling and high availability

- Hangang is stateless in controller mode: raise `hangang.replicas`; a PodDisruptionBudget and topology spread are added automatically.
- Hopae stays at one SQLite replica: its PostgreSQL store is not released, and the chart refuses more than one SQLite replica.
- Pumgye and Sumunjang are single writers in this release; the schema caps them at one replica. Their state lives on a PVC that survives uninstall.

## Certificate rotation without restarts

Every component polls the **contents** of its certificate, key and CA files (no inotify, which is scarce on shared hosts) and swaps rotated material in atomically: new handshakes use the new certificate, established connections keep theirs, and invalid new files keep the previous certificate and raise an alert metric. The Secret is always mounted as a directory (never `subPath`), so the kubelet's atomic `..data` swap reaches the Pod; with cert-manager a renewal therefore needs no rollout.

| Component | Value (default) | What is reloaded |
| --- | --- | --- |
| Hangang | `hangang.tlsReloadSeconds` (10, 0 off) | admin listener; Hopae/Pumgye client identities; Sumunjang decision client |
| Hopae | `hopae.tlsReloadSeconds` (10, 0 off) → `reload.tls_interval_secs` | native and gRPC gateway listeners, admin listener, projection clients |
| Pumgye | `pumgye.tlsReloadSeconds` (10, 1–3600) → `--tls-reload-interval-secs` | management, PPG1 and gRPC listeners; outbound mTLS clients |
| Sumunjang | `sumunjang.tlsReloadSeconds` (10, 0 off) → `--tls-reload-seconds` | HGD1, gRPC and management listeners |

The worst-case delay after cert-manager writes the Secret is the kubelet's Secret volume sync (about a minute by default) plus one polling interval.

## Kubernetes staleness and readiness (Hangang)

`hangang.maxStalenessSeconds` (default 300, 60–3600, at least `staleSeconds`) is ADR 0022's bounded staleness: when the Kubernetes API cannot confirm the published snapshot for longer, protected routes answer `503` with `x-hangang-reason: kubernetes-authority-stale` and public routes keep serving the last-good snapshot. `hangang.readiness: snapshot` (default) keeps replicas ready while they serve an activated snapshot, so an API-server outage does not drain every gateway at once; `fresh` restores the earlier behaviour (not ready once a watch is stale).

## Hopae live configuration reconciliation

With `hopae.authentication.source: config`, Hopae polls its configuration file every `hopae.authentication.reloadIntervalMs` (default 1000; 0 off; 200–60000) and reconciles changed authentication profiles and projection plans without a restart; the chart therefore leaves `authentication_gateway` and `credential_projection` out of the Pod's `checksum/config`, so editing them in values updates the ConfigMap without a rollout, while every other Hopae key still rolls the Pod. The ConfigMap is mounted as a directory, never with `subPath`. **Propagation delay:** the kubelet refreshes ConfigMap volumes on its sync period plus cache TTL (about a minute by default), so a revocation in values takes effect after that delay plus one poll; when revocations must be faster, lower the kubelet's sync settings or revoke through the Hopae console in `store` mode.

## Monitoring and alerts

`monitoring.serviceMonitor.enabled` creates a Prometheus Operator ServiceMonitor for every component that serves `/metrics`:

- **Hangang:** the admin listener (TLS, needs `hangang.admin.exposeMetrics`), bearer = the admin token.
- **Pumgye:** the management listener 9084 over mutual TLS, bearer = `credentials.keys.pumgyeMetricsToken` (passed as `PUMGYE_METRICS_TOKEN`, opens only `/metrics`).
- **Sumunjang:** the management listener 9080 over mutual TLS (`--management-tls`), bearer = `credentials.keys.guardMetricsToken` (`HANGANG_GUARD_METRICS_TOKEN`). Its probes use the separate probe-only listener 9083 (`/readyz`, `/healthz`), which is not in the Service.
- **Hopae:** no ServiceMonitor; Hopae has no Prometheus endpoint yet (its counters are in-process only). Its certificate expiry is covered by the cert-manager rule.

Prometheus presents a client certificate to the mutual-TLS listeners: with cert-manager the chart issues `<release>-hangang-world-metrics-client` (client auth only, from the World issuer); with BYO certificates set `monitoring.serviceMonitor.clientCertificate.existingSecret`. The certificate grants nothing on its own; every scrape still needs the read-only bearer. Add the two metrics tokens (16–4096 visible ASCII characters, distinct from every other credential) to the credentials Secret before enabling the ServiceMonitors, and let the monitoring namespace in through `networkPolicy.metricsFrom`.

`monitoring.prometheusRule.enabled` adds the alerts recommended by each component's documentation:

| Alert | Expression (simplified) |
| --- | --- |
| `HangangProtectedRoutesFailClosed` (critical) | `hangang_kubernetes_protected_fail_closed == 1` |
| `HangangKubernetesSnapshotStale` | snapshot age above half of the bound |
| `HangangTLSReloadFailing`, `PumgyeTLSReloadFailing`, `SumunjangTLSReloadFailing` | rotated material rejected; previous certificate still served |
| `PumgyeCertificateExpiringSoon`, `SumunjangCertificateExpiringSoon`, `WorldCertificateExpiringSoon` | leaf (or cert-manager Certificate) expires within `certificateExpiryDays` (7) |
| `WorldCertificateNotReady` | a release Certificate not Ready for 15 minutes |
| `SumunjangCheckpointStale` | `sumunjang_checkpoint_age_seconds > checkpointAgeSeconds` (60) |
| `PumgyeHopaeFeedStale` | Pumgye's Hopae projection/lifecycle feed older than the projection's `max_staleness_secs` |
| `PumgyeDecisionsUnavailable`, `SumunjangDecisionsUnavailable` | share of decisions answered unavailable above `decisionUnavailableRatio` (1 %) over 10 minutes |
| `PumgyeUnavailable`, `SumunjangNotReady` (critical) | the decision service cannot answer |
| `HangangIngressesWithheld`, `PumgyeShadowMismatchUnexplained`, `SumunjangEvidenceDropped` | operational warnings |

The cert-manager rules need cert-manager's own metrics in Prometheus (`monitoring.prometheusRule.certManagerExpiry: false` to omit them).

## Upgrade and rollback

Hangang World follows N-1 compatibility (ADR 0022 Decision 6):

1. Back up every state PVC (Hopae, Pumgye, Sumunjang) with a crash-consistent snapshot or by scaling the component to zero and copying the volume. SQLite schema migrations are forward-only.
2. Upgrade `hangang-world-crds` first. CRD changes within a served version are additive only, so the running controller keeps working.
3. Upgrade `hangang-world` to the matching version. Stateless Deployments roll with `maxUnavailable: 0`; single writers use `Recreate`, so their APIs are briefly unavailable and the gateway fails closed for protected traffic during that window.
4. Watch readiness and `kubectl get protectionpolicies`; `helm test` must pass.

`helm rollback` to N-1 is supported within a minor series. A component that already migrated its database cannot run its previous version on that database: restore the PVC backup taken in step 1 before rolling back across a migration. Never roll the CRD chart back below the version the running controller requires. Skipping a minor version is not supported.

## Uninstall

`helm uninstall world` removes the workloads and keeps the PVCs (`helm.sh/resource-policy: keep`). `helm uninstall world-crds` keeps the CRDs and therefore every World object; delete them explicitly only if you mean to remove all ProtectionPolicies in the cluster.

## What still blocks a production install

- **Images.** No component image is published to a registry yet; the default repositories (`ghcr.io/ziozzang/…`) are placeholders until signed releases are pushed. `tools/package_component.py` builds the scratch images locally only.
- **Signing and provenance.** No cosign signature, SBOM or SLSA attestation exists, so admission verification (policy-controller, Kyverno) cannot be enforced yet.
- **Hangang version.** ProtectionPolicy support (Hangang PR #21) must be in the released Hangang image the digest points to.
- **Hopae PostgreSQL.** Hopae's PostgreSQL store is planned (Hopae ADR-0002, M2) but not released (Hopae 0.0.10 refuses `store.url_env`); the chart refuses `hopae.storage.backend: postgresql` until it ships, so Hopae runs as one SQLite replica.
- **Chart distribution.** The charts are not yet packaged, signed or pushed to an OCI registry.
- **Live qualification.** The local and remote runs cover the protected chain, revocation, a 10-minute API outage, certificate rotation and a node drain. The component fixes for certificate hot reload, bounded staleness and live Hopae reconciliation are in open component pull requests (Hangang #23, Pumgye #7, Hopae #14, Sumunjang `feat/asn-proposals`) and must be released before the digests can point at them.
- **Hopae metrics.** Hopae has no Prometheus endpoint, so it has no ServiceMonitor and only cert-manager covers its certificate expiry.

## Hopae authentication profiles (configuration-authoritative)

`hopae.authentication.source` defaults to `config`: the service authentication profiles (`hopae.config.authentication_gateway`) and the credential projection plan in values are authoritative. Every rollout reconciles Hopae's store to them through Hopae's CAS publication (audit row, `authentication.reconciled` event); an invalid file stops the start and leaves the store untouched, and console/API edits answer `409 config_authoritative`. This needs a Hopae build with configuration-authoritative profiles (Hopae PR #13). `store` keeps the earlier behaviour: values bootstrap an empty store only and later changes go through Hopae's owner API.

Migration from `store` to `config`: export the current profiles (`GET /v1/authentication/profiles` on the admin listener), put them into `hopae.config.authentication_gateway` (environment references only, never key material), back up the Hopae PVC, then `helm upgrade` with `hopae.authentication.source: config`. The first start publishes the file as the next revision; keys or profiles missing from values are removed at that moment. To go back, set `store`; the store keeps the last reconciled document.

## Hopae administration and Pumgye v2 owner inputs

`hopae.admin.enabled` binds Hopae's admin listener (8702) with mutual TLS behind a ClusterIP-only `<release>-hangang-world-hopae-admin` Service. Its server certificate is issued for the console host; clients present their own World component certificates. The NetworkPolicy admits only the Hangang console broker and Pumgye. The console origin (`admin.public_url`) defaults to that Service so in-cluster callers address the console host; the signed Hangang console delegation key comes from `hopae.admin.delegation.keySecret`.

Pumgye's policy model v2 reads Hopae's signed membership projection and subject lifecycle with a route-scoped, read-only service credential (Hopae `docs/SERVICE_CREDENTIALS.md`). Mint it inside the Hopae Pod, pinned to Pumgye's SPIFFE ID, store it in a Secret, then enable `pumgye.hopaeOwner`:

```sh
kubectl -n hangang-world exec deploy/world-hangang-world-hopae -- \
  hopae admin service-credentials create pumgye-v2 --preset pumgye-v2 \
  --client-san spiffe://cluster.local/ns/hangang-world/sa/world-hangang-world-pumgye \
  --config /config/hopae.json > pumgye-hopae.token
kubectl -n hangang-world create secret generic pumgye-hopae-service-credential \
  --from-file=hopae-service-token=pumgye-hopae.token
```

Offline qualification (Hopae `60b3a60` and PR #10 `b318922`, Pumgye `775e6b9`): both Hopae versions accept the rendered admin configuration; `admin.service_audience` requires the PR #10 build (`unknown key` before it). With the PR #10 build running the admin listener, the minted credential and Pumgye started with the rendered `--hopae-owner` file, the mTLS connection, SPIFFE pin and token were accepted and Hopae refused every call with `service_audience_mismatch`. The cause is that Pumgye's owner client does not send `X-Hopae-Audience` yet. That is a Pumgye prerequisite for this path: until it ships, Pumgye fails closed on owner inputs after `max_staleness_secs`. The Hangang console plugin binding (plugin assets and `--admin-plugins`) is not packaged yet.

## Qualification — disposable local cluster (2026-10-17)

Source revisions: Hangang `a8e15e6` (ProtectionPolicy, PR #21), Hopae `60b3a60`
(`integrate/identity-platform`, reports 0.0.10), Pumgye `775e6b9`
(`feat/model-v2-p0`), Sumunjang `321eb6d` (`feat/console-api-gaps`). Each was built
as a static debug binary and packaged `FROM scratch` (UID 65532) locally; no image
was pushed to a registry.

**Configuration preflight with the real binaries.** The chart-rendered files were
fed to each component: Hangang loaded and validated the generated protection
settings (minimal and HA profiles, including PROXY v2) before contacting the API;
`hopae --check` accepted the generated configuration (`config ok`); `sumunjang
--check` accepted the bootstrap policy and TLS layout; Pumgye started with the
generated bootstrap policy and mTLS files and answered `/-/ready` 200. Findings
fixed in the chart: Hopae 0.0.10 refuses `store.url_env`, so
`hopae.storage.backend: postgresql` now fails at render time and the HA profile
keeps Hopae on one SQLite replica; identity profiles now request
`x-hopae-service-id`, use Hopae's 500 ms verify budget and strip Hopae session
cookies upstream.

**Cluster run.** A disposable k3d cluster `hangang-world-qual` (k3s v1.31.4, own
Docker network, its own kubeconfig file, kube-router NetworkPolicy enforcement),
cert-manager v1.15.3, `hangang-world-crds` and `hangang-world` with the
`certManager` bootstrap CA, `kubernetesTls`, `serviceLocal` client address,
`requireProtection: true` and network enforcement `Required`. A busybox backend
behind Ingress `orders` (ProtectionPolicy: Hopae service API key, Pumgye
`db:orders` GET→select, POST→update) and Ingress `bare` without a policy.

| Check | Result |
| --- | --- |
| ProtectionPolicy status | `Accepted`, `ResolvedRefs`, `Programmed`, `ClientAddressPreserved` all `True` |
| GET with the service key (Hopae → Sumunjang → Pumgye) | 200, backend reached |
| No credential / unknown key | 401, backend not reached |
| POST (action not granted by Pumgye) | 403, backend not reached |
| Client IP blocked in Sumunjang, then unblocked | 403, then 200 |
| Pumgye, Sumunjang, Hopae scaled to zero (each) | 503 fail-closed, no dispatch; 200 after recovery |
| Ingress without a policy | withheld (no route, no certificate); reported `ProtectionRequired` |
| ProtectionPolicy deleted, then re-applied | Ingress withheld, then 200 again |
| NetworkPolicy from an ordinary Pod to Hopae, Pumgye, Sumunjang | refused |
| `helm test` | Succeeded |
| `kubectl rollout restart` of the gateway (2 replicas), 60 requests | 60/60 OK |
| `helm upgrade` (all Pods replaced), 120 requests | 115 OK, 5 × 503 while the single Hopae Pod was recreated |
| `helm rollback` to the previous revision, 120 requests | 116 OK, 4 × 503 (same cause) |

Observations: images must be referenced by digest; in a registry-less cluster the
imported image needed a `repo@digest` reference in containerd, which a registry
pull creates automatically. Hopae authentication profiles are bootstrapped from
the configuration only into an empty database; changing them later through values
does not apply (Hopae then refused to start until the stored document was
replaced). Change them through Hopae's owner API. Single-writer restarts make
protected traffic fail closed for a few seconds, as designed. The cluster, all
built and pulled images and the build directories were removed afterwards.

## Qualification — remote k3s gates (2026-10-17)

The remaining ADR 0022 gates ran on the user-designated remote k3s test cluster (2 nodes, k3s v1.37.1) with owner approval, after a fresh cold backup whose remote and off-host copies matched in size, full SHA-256 and archive listing. Images: Hangang `a8e15e6` (PR #21), Hopae local merge of `integrate/identity-platform` + #10 + #13, Pumgye `00f0d00`, Sumunjang `321eb6d`, static builds loaded into both nodes without a registry. cert-manager v1.15.3 was installed temporarily; the CRD chart ran with `rbac.aggregatedRoles=false`.

| Gate | Result |
| --- | --- |
| Pumgye grant revoke/restore, 20 cycles, 70–90 ms probe | first refusal/allow after the commit: p50 0.03 s, max 0.05 s; no inconsistent sample later than 0.2 s |
| Sumunjang block/unblock of the client, 20 cycles | p50 0.02 s, max 0.05 s; refused requests never reached the backend |
| Hopae key revocation in `authentication.source: config` (values change + rollout) | first 401 4.8 s after `helm upgrade` started, 503 (fail-closed) while the single Hopae Pod was recreated; restore 3.7 s. This is a rollout, not a live revocation path, and misses the 2 s target |
| API server paused 600 s | data plane served 8005/8005 requests; gateways reported not ready after the 60 s staleness bound and authoritative again 7 s after the API returned; 4 requests (about 0.2 s) failed right after the API returned; nodes Ready within 5 s; pre-existing Pods unchanged |
| cert-manager forced renewal of all component certificates | new certificates reached the Pod volumes; Hopae (8703), Pumgye (9084/9087) and Sumunjang (9080/9082) kept serving the previous certificate for 5+ minutes; traffic stayed 2443/2443 OK; a rollout restart was needed to serve the new certificate |
| Drain of the second node with the gateway PDB | one eviction refused by the PDB, 410/410 requests OK, gateways rescheduled; uncordoned |
| `helm test` | Succeeded |

Defects recorded per component: **Hangang** keeps serving last-good indefinitely during an API outage (readiness is withdrawn after 60 s) instead of failing closed beyond ADR 0022's bounded staleness, and dropped 4 requests at API recovery; reload of its client certificates was not observable. **Hopae**, **Pumgye** and **Sumunjang** do not reload rotated certificates without a restart. **Hopae** declarative revocation is rollout-bound; the merged #10+#13 tree needs the conflict resolution and the event-count tests (46→47, 52→53) updated. cert-manager's cainjector crash-looped briefly after the API returned and recovered. All created objects, images and namespaces were removed; nodes, CRDs, RBAC, webhooks, ingress classes, PV list and HTTP checks matched the pre-run baseline, and pre-existing Pods kept their UIDs and restart counts.


## Qualification — certificate rotation re-run (2026-10-17)

Gate 3 was repeated on the same remote k3s test cluster with the component fixes, after a fresh cold backup (3,824,806,818 bytes) whose remote and off-host copies matched in size, full SHA-256 and archive listing. Images: Hangang `229b85b` (PR #23), Hopae `be56e61` (local merge of `integrate/identity-platform` + #14), Pumgye `a135176` (PR #7), Sumunjang `400acea` (`feat/asn-proposals`); chart `466c1b9` with the default 10 s TLS polling and `hangang.admin.exposeMetrics`.

| Check | Result |
| --- | --- |
| Forced cert-manager renewal of the four component certificates (revision 2) | every listener served the new serial within about 2 minutes, with no restart (same Pods, restart count 0) |
| Hangang admin listener 9000, 3 replicas | new serial 12–32 s after renewal; logs `TLS listener certificate reloaded serial=…` and `TLS client material reloaded` for `upstream-client` and `guard-decision`; `hangang_tls_reloads_total` 1 per material, failing 0 |
| Hopae gRPC gateway 8703 | new serial; `TLS material reloaded name="grpc_gateway"` |
| Pumgye 9084 / 9085 / 9087 | new serial on all three; `tls_reloaded` per listener; `pumgye_tls_reloads_total` 1, failing 0 |
| Sumunjang 9080 / 9081 / 9082 | new serial on all three; `sumunjang_tls_reloads_total` 1, failures 0; HTTP `/readyz` and `/healthz` probes on 9083 |
| Protected traffic during the rotation | 2028/2028 requests 200 |
| `helm test` | Succeeded |

The run was cleaned up to the pre-run baseline (nodes, CRDs, RBAC, webhooks, ingress classes, namespaces, the 285 PVs and HTTP checks identical; pre-existing Pods kept their UIDs and restart counts). The older off-host backup copy was removed after the new one verified. One Hangang follow-up was fixed on PR #23: a dynamic public listener no longer reports a reload metric. A plain-HTTP `401` seen through `kubectl port-forward` to the Hangang admin port was a measurement artefact: the workstation already published an unrelated plaintext gateway on `0.0.0.0:49000`, so kubectl bound only `[::1]:49000` and the IPv4 probe reached that local service, not the Pod. Hangang's TLS admin listener never answers plaintext, also from loopback and under `--supervised` (regression test in Hangang PR #23). As defence in depth the chart now serves the admin API over TLS even when it stays on loopback, so no container in the Pod network namespace can reach a plaintext administration endpoint.

## Validation

```sh
python3 tools/helm/build_world_schema.py
python3 -m unittest tools/test_helm_charts.py
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py
```
