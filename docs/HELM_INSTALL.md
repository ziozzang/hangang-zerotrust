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
- **Live qualification.** The local cluster run covers the protected request chain, refusals, outages, upgrade and rollback; the ADR 0022 revocation SLO, 10-minute API outage, certificate rotation without restart and multi-node behaviour remain unqualified.

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

## Validation

```sh
python3 tools/helm/build_world_schema.py
python3 -m unittest tools/test_helm_charts.py
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py
```
