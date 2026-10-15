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

## Shared-runtime package revision qualification

The actual browser/world fixture also passes with static nonroot images from
Hopae 6eb07d3, Sumunjang 5de28f3 and Pumgye 200ed48, all pinning runtime
819177c (0.1.2). Static native and gRPC local four-process chains passed before
packaging; image archive checksums matched on transfer and images were imported
on both test nodes. The Kubernetes fixture completed with exit zero and removed
its owned namespace while retaining synthetic PVs under the existing Retain policy.
Scope includes the selected gRPC data plane, management mTLS, independent browser
logins/stale-publication refusal, profile revocation/restoration and Hopae Pod
replacement, Pumgye durable revocation/Pod replacement, Hangang state persistence
and network authority outage. Existing ingress regression and operator services
remain healthy. This qualifies these package revisions on the test cluster; it is
not production adoption, all native protocol deployment modes or full-stack performance.

## Service-only composition qualification

`--composition --observed --credential-projection` adds an independent owned HTTPS
authentication relay Pod: four decision-service Pods, one relay and one counted
test-backend Pod (six Pods total).
`--composition-mode all` is the default; `any` is explicit. The fixed Hopae profile
declares local API-key and HTTPS-relay slots and exact Service identity relationships.
A namespace-owned CA is mounted as `api_relay.ca_file`; the relay uses its exact
Service DNS certificate. TLS/hostname verification stays enabled. Its Secret
environment contains only the two remote credentials and fixture control token;
Hopae receives only its local credentials, not the remote provider credential.

Requests use `Hopae-Compose` with bounded envelope payloads. The supplied independent
receipt probe must support the fixed `credential_scheme=hopae_compose` config and
read the payload from the credential environment, preserving Bearer as the default
for existing modes. Actual issue, independent observation, consuming refresh and
final checks remain mandatory. The fixture checks missing factors, presented invalid
factors, conflicting successful identities, relay circuit opening and explicit
source Pod replacement recovery. Every refusal preserves the backend count;
successful backend responses contain only the separate origin credential, never
either provider credential, the composite envelope or native caller key.

This is Service composition at AAL0. It does not qualify Human MFA or Workload
composition, local-account recovery, streaming or arbitrary deployment topologies.
The default mode keeps its four production owners and does not create relay
credentials, the relay Pod or composition configuration.

The composition circuit gate runs before disruptive source withdrawal/UID repinning.
A dedicated diagnostic probe requires the exact native IssueServiceObserved
provider-unavailable status, with one observed controlled relay call for each of
three denials. A fourth native call must refuse without a relay call; the complete
gateway path must also refuse without backend dispatch. TLS-name, invalid clock-rate
configuration and caller failures must fail the probe and never count as provider
denials. Peer recovery alone cannot bypass the open circuit. This denial diagnostic
grants no receipt or time capability; the ordinary successful probe still uses the
actual SDK issue/observe/refresh/check sequence.

## Opt-in embedded Pumgye responsive UI gate

`--pumgye-responsive` requires the actual browser probe and adds trusted
`pumgyeResponsive=true` to its private configuration. After the existing real policy
load and publication checks, it sets a390px viewport and verifies no document
horizontal overflow, positive main-panel padding, form controls and table wrappers
within the viewport, visible source summary, and keyboard horizontal scrolling of
the named authorization region. Table cells/actions may scroll within their wrapper;
they need not all remain inside the viewport simultaneously. The probe then restores
a1280px desktop viewport and preserves every subsequent functional gate. This is
opt-in for the exact new embedded UI candidate; existing037/default runs do not gain
new CSS assertions or time-budget changes.
