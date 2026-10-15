# Component image packaging

[한국어](ko/PACKAGING.md)

`tools/package_component.py` packages an explicitly qualified static ELF artifact
for Hangang, Hopae, Sumunjang or Pumgye. Build and functionally qualify the selected
source revision first. The tool requires its full Git revision and rejects a dynamic
loader. It builds from a private temporary directory containing only the executable
and Dockerfile. Configuration, databases, provider secrets and TLS material are
supplied separately at deployment; no source tree is copied into the image.

The image uses scratch, UID/GID 65532 and an executable entrypoint. The tool verifies
container startup with `--version`, a read-only filesystem, no network, no capabilities
and no-new-privileges. It reports the image ID and size. The source label is a declared
revision, not cryptographic provenance or proof that the caller built the supplied
bytes from that revision. Version startup alone is not functional qualification.

```sh
python3 tools/package_component.py --component hangang --binary /qualified/hangang --revision 0125779c1f807330544c466e8450aee10c7195ee
```

Local image creation does not publish a registry image, sign a release, deploy Pods,
prove Kubernetes source adapters or complete the Hangang World package. Actual
cluster acceptance must include all four independent services, mTLS Service DNS,
request enforcement, administrator delegation, persistence/restart and failure gates.

## Pumgye 0.1.4 qualification — 2026-10-15

Signed static source `89e5987cfee934f2fb6b9f007064bc6525999715` was independently
verified after release download, packaged as `hangang-world/pumgye:89e5987cfee9`
and imported into both remote K3s nodes after matching archive hashes. The owned
four-server fixture passed with Hangang 0.3.4, Hopae 0.0.6 and Sumunjang 0.3.4:
actual browser/module delegation, resource metadata CAS, immediate/persistent
revocation, Pod replacement, outage and refused backend non-dispatch. Existing
backup/off-host copy, DNS, Ready nodes and HTTPS services were preserved.

This fixture also verified a Hopae service receipt with the real Hangang client.
It does not activate Pumgye permit RPC, prove distributed receipt owner freshness
or exercise new optional durable trust resources in Kubernetes. Those remain
separate gates. Local 55-test/static mTLS qualification covered the new key/scope
floors and internal Pumgye 0.1.4 was deployed with DB-clone preflight and restart.
Malformed digest references are now refused before cluster operations.

## Signed native observation releases and internal adoption — 2026-10-15

[Pumgye 0.1.5](https://github.com/ziozzang/pumgye/releases/tag/v0.1.5),
[Hopae 0.0.7](https://github.com/ziozzang/hopae/releases/tag/v0.0.7) and
[Sumunjang 0.3.5](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.5)
were published as Linux amd64 static musl artifacts. Exact newly versioned
three-authority endpoint tests passed; every downloaded asset matched its
prepared source bytes and pinned signature/version/target/URL bindings.

Internal adoption passed actual DB/configuration preflight, private consistent
backups, exact policy and protected identity-data preservation, native mTLS
refusal and restart. Sumunjang supervised worker handover passed and existing
observe mode remains. All three operating executable versions were verified;
Hangang console HTTPS still returns 200. Native issuer/trust/live resources
remain unconfigured in the existing environment, so this adoption does not
activate the new receipt-backed decision path or add grants. The actual path
was qualified only in owned isolated static processes.

Kubernetes combined-endpoint qualification, Hangang request dispatch, signed
permit/route/projection owners, fleet/restore floors and full objective completion
remain open. Existing signed release assets are immutable; no Actions were enabled.

## Native observation Kubernetes endpoint — 2026-10-15

The owned four-server world fixture passed with exact signed Hangang 0.3.4,
Pumgye 0.1.5, Hopae 0.0.7 and Sumunjang 0.3.5 artifacts. The new
`--authenticated-client` option requires receipt issuance and resource catalog
qualification, injects explicit public trust/mTLS resources into Pumgye, and
verifies an actual authenticated resource Allow in the Pod using Hopae live
receipt validation and Sumunjang Enforce queries over mTLS Service DNS.
The local static qualification client also verifies Pumgye’s mTLS HTTPS response.

The existing real browser/module delegation, policy/catalog CAS, ordinary
request revocation/restoration, Pod replacement, failure/no-backend-dispatch
and logout gates passed. Owned namespace was removed; synthetic Retain PVs
were preserved. A fresh cold backup passed archive integrity before testing;
cluster/authentication-container restart and existing DNS/Ingress were checked.
The original off-host transfer subsequently completed: its entire SHA-256
matched the complete remote archive. Both private full backups are retained;
the failed auxiliary tail transfer was not used as evidence.

The new Kubernetes endpoint step proves positive combined admission only.
Receipt-specific withdrawal/outage was qualified in the local static three-
authority fixture, not repeated through this Kubernetes endpoint step. Hangang
production dispatch integration, signed permit/projection and fleet/restore
fences remain open. Existing remote operating services were preserved.

## Native final dispatch: static candidate Kubernetes qualification

Hangang df5ce039a21582928fc0845f88ed2d90bc8740ed (0.3.5) and Pumgye
609e552604d693fc3ac5410a4ef593463200b25b (0.1.6) signed static candidates
passed the actual backed-up Kubernetes package with published Hopae 0.0.7 and
Sumunjang 0.3.5. New image archive transfer hashes matched and both nodes imported
them. `--native-resource` activates actual final gateway dispatch over Service
DNS/mTLS, with a composed backend base path and nonempty entity assertion.
The real browser verifies unified operator login/module administration, signed
delegation, policy/catalog CAS and profile revocation. Native receipt/combined
endpoint, guest/method/permission/class/assurance/service refusal, immediate and
durable revocation, PVC/authority/gateway Pod replacement and network outage pass;
refusals do not reach the backend. Owned namespaces are removed, Retain data and
existing nodes/DNS/Ingress are preserved.

Initial runs exposed a counting-origin fixture that discarded bodies, then a
previously built qualification client refusal. The origin now collects the
complete entity; the client was rebuilt from current Pumgye source. The complete
run exits zero. The old client's exact internal refusal is not established, and
the initial logs remain private. A fresh cold backup passed archive/hash and
restart checks. Its off-host transfer subsequently completed; full-file SHA-256 matches the
complete remote archive, and the prior verified off-host backup is preserved. This is candidate
functional qualification, not new public release or operating migration, full
streaming/projection/fleet completion or throughput proof.

## Native final dispatch release and internal adoption — 2026-10-15

[Hangang 0.3.5](https://github.com/ziozzang/hangang/releases/tag/v0.3.5)
and [Pumgye 0.1.6](https://github.com/ziozzang/pumgye/releases/tag/v0.1.6)
are public, with five signed Linux amd64 musl assets each. Downloaded assets
match staged bytes; independent signature, public-pin, exact version/target/URL,
hash and static ELF checks pass. Hangang's archive contains the eight qualified
executables. These releases use the exact source revisions qualified above.

Internal Pumgye adoption passes DB-clone preflight, exact policy preservation,
mTLS management/native missing-service denial and a second durable restart.
Downloaded executables need their execute bit restored before preflight; this
initial failure occurred before operational replacement. Gateway adoption passes
read-only configuration preflight, private SQL/config/image backups, configured
drain, exact running artifact, unchanged routing/credentials/UID/network and
unknown-host refusal. Console adoption verifies archive equality, private
binary/unit/database backups, preflight, unchanged configuration/module discovery
and delegated Pumgye catalog reads. An initial console precheck ran during the
gateway drain and refused before replacement; the subsequent sequential attempt
passed after gateway health recovered.

Actual HTTPS Chromium checks pass all three unified module menus, Pumgye matrix
and source summary, delegated Hopae status/users, existing ID/PW plus SSO entry,
provider-portal redirect, logout cleanup, anonymous/cross-origin refusal and no
configuration mutations. This qualifies SSO entry, not completed external login.
Existing observe policy, identities and permissions are preserved. Receipt
issuer/trust/live operating resources remain unconfigured: the new native route's
positive enforcement is qualified in the owned local/Kubernetes fixtures, not
activated for existing operating services. Signed permission/projection/replay,
full provider/fleet/streaming and throughput gates remain open.


## Native credential projection candidates — 2026-10-15

Hangang 0.3.6 (`87f11fe`), Hopae 0.0.8 (`25aca97`) and Pumgye 0.1.7
(`28f0c1a`) have independently verified Linux amd64 static signed assets in
GitHub draft releases. Every downloaded asset matches its prepared bytes; all
eight Hangang archive executables are static and match the build. Exact static
four-server final credential delivery and durable withdrawal/restart checks pass.
The retained Sumunjang 0.3.5 image also matches its pinned signed executable.

The extended `--credential-projection` Kubernetes fixture adds the native Hangang
route-owner Service, independent permit signing, live owner queries and declared
Hopae origin capability over mTLS Service DNS. It requires `--native-resource`,
`--resource-catalog` and `--receipt-client`. The separate `--authenticated-client`
fixture has no native route reference and must be qualified in its existing mode,
not silently substituted for a route-bound call.

A fresh cold backup and complete independently matching off-host SHA-256 were
verified, and all prior cluster workloads recovered. Both candidate Kubernetes
runs passed initial real four-Pod origin credential delivery, then failed the
independent management-host receipt client before browser/policy/restart gates.
Diagnostic-only verification found a valid signature and scope but issued time
4 ms after local arrival. No clock grace or access-policy widening was added.
See [draft ADR 0018](adr/0018-authority-time-observations.md) for admission lower
bounds and replay-retention upper bounds across clock domains.

These are failed overall Kubernetes qualifications. Drafts remain unpublished and
operating versions unchanged. Cross-host temporal admission, complete Kubernetes/
browser regression, fleet restore and throughput remain open. Owned namespaces
were removed; both nodes, DNS, prior Ingress 100/100 and existing operating
services remain available. A source diagnostic example (`d04b8bd`) emits only
booleans and timing deltas and never releases a receipt or credential.
