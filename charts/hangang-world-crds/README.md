# hangang-world-crds Helm chart

[한국어](README.ko.md) · [Install guide](../../docs/HELM_INSTALL.md)

CustomResourceDefinitions of the `world.hangang.dev` API group and the aggregated ClusterRoles of ADR 0022, kept separate from [`hangang-world`](../hangang-world) because Helm never upgrades a chart's `crds/` directory. The CRDs are ordinary templates here, so `helm upgrade` updates them; both charts move in lockstep versions. Install or upgrade this chart first.

| Object | Notes |
| --- | --- |
| `protectionpolicies.world.hangang.dev` (v1alpha1) | Structural schema, CEL rules, status subresource; same definition as Hangang `deploy/kubernetes/crds` |
| `world-admin` | Full control of World objects; aggregates into `admin` |
| `world-editor` | Create and change World objects (not their status); aggregates into `edit` |
| `world-viewer` | Read World objects and status; aggregates into `view` |

| Key | Default | Meaning |
| --- | --- | --- |
| `keep` | `true` | `helm.sh/resource-policy: keep` on CRDs: uninstalling never deletes World objects |
| `protectionPolicy.enabled` | `true` | Install the ProtectionPolicy CRD |
| `rbac.aggregatedRoles` | `true` | Install the aggregated roles |

Do not install these roles together with the kustomize `deploy/kubernetes/crds` of the Hangang repository; use one source.
