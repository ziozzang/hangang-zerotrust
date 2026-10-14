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

## Actual browser qualification

Optionally supply `--browser-probe` pointing to Hangang's
`web/tools/world_admin_browser.mjs` and `--node-binary` if Node is outside PATH.
Install the repository's Playwright dependency and Chromium before running it.
The probe reads a private temporary configuration file; credentials are not command
arguments, and failures redact them. It connects to the actual port-forwarded console
without intercepted API responses or a fixture UI server. It creates the first local
administrator, signs in with ID/password, publishes a guest assignment to the owning
Pumgye policy, loads the real Sumunjang menu, blocks/unblocks the owned peer, and
checks logout data clearing. The surrounding fixture then runs actual request
revocation, Pod replacement and outage acceptance before removing its namespace.

This proves the selected local administrator/Pumgye/Sumunjang browser flow. It does
not cover every Hopae management screen, federated console SSO, all providers or production
administrator rollout. Browser artifacts and credentials are not published.

## Hopae under the Hangang administrator session

`--hopae-plugin` adds the real digest-pinned Hopae console package and its separate
mTLS management Service. Hopae explicitly selects Hangang as its console authority.
The browser probe enters Hopae from the existing local Hangang administrator login
and reads its actual authentication profiles, without a second Hopae login.
It publishes a disabled profile configuration through the real editor, verifies
that the protected application returns 401 without increasing the backend call
count, replaces the actual Hopae Pod while leaving its bootstrap configuration
unchanged, verifies the persisted disabled configuration and 401, then restores
the original configuration and verifies 200. Reconnection may return 503; every
observed status must be 401 or 503 before restoration. The restart command is
restricted to the owned namespace and deployment/hopae; it uses the explicit
kubectl wrapper without passing credentials on the command line. These requests use
the fixture CA and real gateway; no API interception is used.
Every forwarded operation still carries a scoped signed assertion. The receiver
trusts its exact TCP peer only for a request with both server-authenticated mTLS
and completely validated delegation; global trusted proxy networks are unchanged.
Unsigned TLS requests keep the normal proxy/native authorization checks.
This qualifies remote management/profile reading and revocation/restoration, not federation login or every
provider/mutation screen. Native data-plane authentication remains Hopae owned.

## Concurrent administrator publication

The browser probe opens a separate browser context, signs in again with the actual
local administrator credentials and loads the original Hopae profile revision.
After the first session publishes revocation, the second submits its stale document
through the real editor. The real publication response must be 409, the UI must
display an error and retain its stale revision, and the protected request must
remain 401 without backend dispatch. No browser storage/session credentials or
API responses are injected. This gate checks lost-update prevention across console
delegation and the owning DB authority, not administrator-role isolation.
