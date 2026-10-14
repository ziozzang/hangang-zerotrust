# Four-service Kubernetes functional qualification

[한국어](ko/KUBERNETES_WORLD_QUALIFICATION.md)

`tools/kubernetes_world_smoke.py` creates a uniquely owned namespace with independent
Hangang, Hopae, Sumunjang and Pumgye Deployments/PVCs, plus a counting test backend.
Supply an explicit kubectl wrapper, qualified preloaded component images, Hopae's
owned configuration fixture, the digest-pinned Sumunjang console package and a pinned Node-capable echo image. The tool never
uses the default kubeconfig and never recreates the cluster. It creates synthetic
credentials and one-day TLS material, submits Secrets over stdin and removes only
its own namespace. Cluster Retain policy preserves synthetic test PVs.

The four core containers run as UID/GID 65532 with read-only root filesystems,
dropped capabilities and no service-account token mount. Decision calls use mTLS
and Kubernetes Service DNS. Each authority has its own single-writer SQLite PVC;
this is not multi-replica database distribution. Pumgye management is HTTPS/mTLS.
Hangang management remains loopback-only and is accessed through authenticated
kubectl port-forwarding. Sumunjang management is mandatory mTLS HTTPS, delegated
through a digest-pinned real console plugin and its scoped administrator credential.
No plaintext management Service is exposed. Guard signal submission is not configured.

Hangang's Docker connection state and SQL configuration live on its PVC. A nonroot
init container prepares a 0700 private administrator directory and 0600 SQLite
files after fsGroup processing; the administrator protection checks remain enabled.
Sumunjang uses first-start-only `--bootstrap-policy` rather than restarting with
an explicit policy override. Readiness for most components checks the listener;
the actual protected requests are the stronger functional acceptance condition.

The fixture checks real protected HTTPS requests, verified service identity and
credential consumption, method/guest denial, delegated Pumgye policy CAS and
immediate revocation, revocation across a Pumgye Pod replacement, restoration,
plugin discovery and delegated Sumunjang management reads/mutations over mTLS,
Hangang Pod replacement with private administrator state, network block changes
and Sumunjang scale-to-zero fail-closed. Every refused request must leave the
actual backend call count unchanged. It uses gRPC for all three decision exchanges.

This qualifies a selected API-service request chain running in Kubernetes. It does
not qualify Kubernetes inbound TokenReview/SubjectAccessReview delegation, all
metadata source modes, generic resource adapters, the full browser administrator
console/provider suite, runtime signal submission, HA, full channel/credential
lifecycle, production rollout or performance. Those remain gates of the full goal.
Do not treat this owned test generator as a production deployment bundle.
