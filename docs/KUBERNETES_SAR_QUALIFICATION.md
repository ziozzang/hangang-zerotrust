# Disposable native SAR qualification harness

Current exact-candidate actual gate results: [0.3.11 / 0.1.9 qualification](QUALIFICATION_0311_019.md). Earlier preparation/status text below is historical; normative ownership and limits remain applicable.

Historical preparation status: implemented local fixture, unit-tested; final actual execution is recorded above.
`tools/kubernetes_sar_qualification.py` renders private material by default. Its
explicit `--execute` path creates a unique owned namespace atomically, a private
Secret, SAR Service, Pum Pod and disposable API-server/etcd Pod. It never changes
an existing master configuration or creates cluster RBAC/CRDs/PVs/host mounts.
All containers are non-root, drop capabilities, disallow privilege escalation,
and use no host network or service-account credential. Ephemeral data disappears
with the owned namespace. This is a functional fixture, not a deployment template.

## Source and image validation

Validated against Kubernetes checkout `98e9da3000734733127c8ac3bdb77b42ad61c31b`:
`staging/src/k8s.io/apiserver/pkg/apis/apiserver/v1/types.go:460` and
`validation/validation.go:660` define webhook cache switches, positive required
TTL fields, timeout, v1 review version and failure policy. Both caches are false;
TTLs are **1s**, not invalid zero. The only configured authorizer is Webhook/Deny.
Official [configuration reference](https://kubernetes.io/docs/reference/config-api/apiserver-config.v1/)
and [authorization reference](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
were checked. The private webhook kubeconfig uses fixed Service authority,
verified CA, exact client leaf pinned by Pum and a distinct Bearer token.

`tools/kubernetes_sar_images.json` records registry.k8s.io manifest API responses:
Kubernetes v1.37.1 and etcd3.7.0-0 (the checked upstream kubeadm default). Manifest bytes were hashed against returned
index digest, then linux/amd64 child manifest hashed against descriptor. The
index digest, platform digest, and eventual runtime imageID are DIFFERENT facts;
actual execution still must record imageIDs. Registry provenance URLs are in the
file. Pin child linux/amd64 digests for this fixture. No floating tag is accepted.
The API-server image config was inspected; explicit binary commands avoid entrypoint
ambiguity. This is not a claim that these images have run in the target cluster.

## Required external prerequisites before execution

1. Parent review and approval; fresh cold backup plus verified off-host copy.
   Private `--backup-evidence` JSON requires `cold_backup:true`, `completed_unix`
   within six hours, full `sha256`, `size_bytes`, and one local `offhost_archive`.
   The archive is fully hashed/size checked and tar-tested before any kubectl.
   `remote_verification` is a trusted parent receipt with `archive`, matching
   `sha256`/`size_bytes`, `tar_pass:true`, `cold_backup:true`, and fresh
   `verified_unix`. It represents already completed remote hash/tar verification,
   not cryptographic authority; no redundant second control-host copy is required.
   Backup creation/remote verification itself is outside this helper.
2. Qualified Pum0.1.9 immutable image with SAR support and preserved production
   `observed-authentication` feature. `--candidate-evidence` requires exact image,
   version, source40hex, binary_sha256, features and `sar_listener:true`; parent
   packaging must create it from actual qualification. This is provenance
   metadata, not a cryptographic attestation or new authentication capability.
   It also requires parent-reviewed `runtime_images` entries for `api`, `etcd`,
   `pumgye`, each with exact `image` specification and expected runtime `image_id`.
   Missing attestation fails before kubectl. Actual Pod spec and container status
   imageID must match before authorization tests and again after recovery; image
   ID formats are never assumed equivalent to OCI index/child digest.
   Pum management binds **127.0.0.1:8080**, accessible only by owned port-forward;
   the separate SAR8443 listener remains mandatory-mTLS on the Pod network.
3. Explicit kubectl wrapper path, OpenSSL, Python3, image pull/import availability,
   matching linux/amd64 scheduling and approved disk/memory capacity. No SSH or
   cluster preflight was run during local preparation. Run container help/version
   compatibility check before mutation if final upstream version differs.
4. Existing two-Ready-node and PodUID baseline. Helper preserves original PodUIDs,
   checks nodes afterward, and deletes only its created namespace using atomic
   UID/resourceVersion DeleteOptions; namespace replacement refuses cleanup.

Example CLI (substitute verified immutable references/evidence; private output
contains credentials, must not be uploaded):

```sh
python3 tools/kubernetes_sar_qualification.py \
  --api-image registry.k8s.io/kube-apiserver@sha256:<verified-amd64-digest> \
  --etcd-image registry.k8s.io/etcd@sha256:<verified-amd64-digest> \
  --pum-image <qualified-pum019-image>@sha256:<digest> \
  --output /private/new-owned-fixture
```

Render has no cluster access. Execution additionally requires `--execute`,
`--approval owned-disposable-only`, `--kubectl`, `--backup-evidence` and
`--candidate-evidence`. Never use an existing namespace. Primary failure and each cleanup/baseline failure are recorded separately; all
finalization steps are attempted and private result evidence is written even if
cleanup fails. Cleanup or baseline failure forbids a success result. No credential or raw
API object payload is printed. Private manifests contain keys; retain mode0700
output directories/0600 files, including process/port-forward logs.

## Exact ordered actual gate

Generate independent CA and fixed ordinary reader/unknown client certificates.
Only fixture bootstrap certificate has system:masters; ordinary tested identity
never does. Bootstrap creates the disposable inner Namespace/ConfigMap, then is
used only for independent backend-state readback (never an allow test identity).
No bootstrap/ordinary client keys or CA signing key are uploaded to the Pod.
Pum uses DB-native policy to avoid an RBAC-import/webhook circular source poll.

Ordinary actual API requests test named GET Allow; unknown identity and resource
Deny; exact named PATCH Allow and backend change; same native CAS grant removal
PATCH403 and unchanged backend; restoration PATCH Allow and change; AAL role and
resource classification denial/recovery. Pum Pod withdrawal must fail closed,
and a new original-policy Pod must recover without API-server replacement.

The implementation sends real requests to a disposable API-server configured for
v1 SubjectAccessReview. No fixture-generated SAR is substituted. However an
observed actual request envelope and a measured same-H1 webhook connection reuse
are **not yet captured** by this harness: do not claim either from config alone.
Pum's independent actual same-socket unit/CLI test is separate evidence. The
fixture does not claim source-lease expiry, TokenReview, four-core dispatch,
Human MFA, throughput, signed release or operating adoption.

## Local validation

`cd tools && python3 -m unittest -v test_kubernetes_sar_qualification` checks
fail-closed cache config, namespace-only nonprivileged objects, secret exclusion,
typed same-policy/no-network semantics, immutable references, atomic cleanup
preconditions/replacement refusal, and missing/stale backup rejection. No cluster
access occurs. Existing Service/Workload/default runners are unchanged.

Before owned cleanup, the finalizer collects private Pod status and bounded
per-container logs (last200 lines, at most64KiB) only for PodUIDs returned by this
run's create operations, after checking the original namespace UID. No Secret
API is called. Pod log APIs have no atomic UID precondition: the helper verifies
PodUID before/after log collection and discards bytes on replacement. Diagnostic
errors remain separate from the primary failure and never skip cleanup/baseline
checks. A diagnostic error prevents a success result. Startup/port-forward
budgets are unchanged; a slow startup produces preserved failure evidence rather
than silently broadening the qualification deadline.

## Preserved first real attempt and narrow image derivative

The first actual attempt did NOT qualify: API-server failed exec with EPERM;
separately kubectl port-forward refused a still-Pending Pod. The original evidence
and successful owned cleanup remain private; neither failure is reclassified as
a native authorization denial. The official pinned image's binary layer contains
`security.capability` (`cap_net_bind_service=ep`), confirmed from hashed OCI layer
bytes. Upstream Dockerfile explicitly applies it. `drop:ALL` prevents that file
capability from executing; no low port is needed by this fixture.

`tools/build_sar_apiserver_image.py` makes a qualification-only derivative from
that EXACT official child. It stages the verified binary bytes in a fresh plain
file (no capability attribute), overlays it in the same official base, and checks
final bytes/metadata and actual local nonroot/dropALL/no-new-privileges/read-only,
network-none `--version`. It adds no runtime capability, root or global setting.
The build emits private image/archive/config provenance; parent import must add
its actual immutable manifest `image` reference. `--api-derived-evidence` permits
only the fixed `docker.io/sar-qualification/kube-apiserver@sha256:...` namespace
AND exact reviewed official image/layer/binarySHA/capability-removal/version facts.
This is a packaging exception, not an arbitrary image bypass. Runtime imageID
attestation still applies separately; an image config digest is not an OCI
manifest digest. Official digests remain source provenance.

Before launching port-forward, the helper polls for Pod phase Running plus every
expected container Running. Readiness polling and forwarding share the ORIGINAL
10-second deadline. No unconditional startup sleep or deadline expansion was
introduced. Failure still invokes private diagnostic/owned cleanup finalization.

The second real attempt separately reached API-server startup but failed endpoint
reconciler validation of advertised127.0.0.1; no authorization assertion passed.
Upstream `pkg/controlplane/instance.go:354` validates PublicAddress before the
Kubernetes service controller starts. The fixture now advertises actual Pod IP
using downward API `POD_IP=status.podIP` and literal container argument
`--advertise-address=$(POD_IP)` (kubelet expansion, no shell/host network).
Explicit serving cert/key files remain unchanged: upstream secure serving skips
self-signed defaulting when files are provided. The existing127.0.0.1 SAN still
verifies the owned port-forward client; this does not claim direct Pod-IP TLS
verification or add that changing address to a pre-generated certificate.
Startup budgets/security restrictions are unchanged. Both prior failures and
owned cleanup evidence remain failures, distinct from native authorization denial.
