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
