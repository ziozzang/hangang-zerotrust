# Installing Hangang World with Helm

[한국어](ko/HELM_INSTALL.md) · [Design index](README.md) · [Chart reference](../charts/hangang-world/README.md)

This guide installs the integrated Hangang World package (ADR 0022 P0 packaging): Hangang, Hopae, Pumgye and Sumunjang from the `hangang-world` chart, and the `world.hangang.dev` CRDs from the `hangang-world-crds` chart. The charts are validated offline (`helm lint`, `helm template` across profiles, Kubernetes/cert-manager/Prometheus Operator schema validation and a render test); they have **not** been installed on a cluster yet. See [What still blocks a production install](#what-still-blocks-a-production-install).

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
- Hopae scales with `hopae.storage.backend: postgresql`, `global.ha.backend: postgresql` and a Secret with the connection URL. The chart refuses more than one SQLite replica.
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
- **Hopae PostgreSQL.** Hopae's PostgreSQL store is planned (Hopae ADR-0002, M2) but not released; the HA profile renders the documented configuration and will fail Hopae's configuration check until it ships.
- **Chart distribution.** The charts are not yet packaged, signed or pushed to an OCI registry.
- **Live qualification.** The ADR 0022 functional gates (protected request chain, revocation SLO, API outage, certificate rotation) have not been run against the chart; certificate rotation needs each component to reload its files without restart.

## Validation

```sh
python3 tools/helm/build_world_schema.py
python3 -m unittest tools/test_helm_charts.py
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py
```
