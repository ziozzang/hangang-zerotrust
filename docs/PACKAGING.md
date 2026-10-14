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
The new off-host copy is being completed separately; no completed-copy claim
is made here.

The new Kubernetes endpoint step proves positive combined admission only.
Receipt-specific withdrawal/outage was qualified in the local static three-
authority fixture, not repeated through this Kubernetes endpoint step. Hangang
production dispatch integration, signed permit/projection and fleet/restore
fences remain open. Existing remote operating services were preserved.
