# Hopae0.0.10 / Pumgye0.1.8 adoption — 2026-10-15

Both Linux amd64 musl releases are public and internally installed.

| Component | Release target | Runtime build | Raw SHA256 |
| --- | --- | --- | --- |
| Hopae0.0.10 | b9b2a9a88de5c713c3f4acaf74de9d507db6fb39 | 848dc83540e1eb722ddd7e8d8820b07e11fa9d76 | 8c2308ce07cc66a35f7d619e7ade1a3f31855df0d0b4bc709bbaf1bef08b59de |
| Pumgye0.1.8 | 8a37f25ea0dce4bcec2988f1de8fe5cac2043038 | adaf985042b7af7b6aecc48cf34a02661abd4644 | cc9ff90f8f29159f0c1adf3d8a80e324d4a81469f4ee6b9a3a9b27e45a1174bf |

Hopae's target differs only in external plugin/generator packaging; Pumgye's in
documentation/packaging helper. Rust and lock sources match their builds. Later
Human provider-owner schema7 and Kubernetes API context/mapping groundwork on main
are outside these releases and were not adopted.

Each release has five assets. Draft and public downloads match every staged byte,
including pinned Ed25519 signature, version/target/URL/hash/size, static raw and
archive contents. Anonymous raw-asset endpoints return200; tags resolve to the
exact targets above.

- [Hopae release](https://github.com/ziozzang/hopae/releases/tag/v0.0.10)
- [Pumgye release](https://github.com/ziozzang/pumgye/releases/tag/v0.1.8)
- [Actual K3s qualification and retained failures](2026-10-15-workload-native-qualification.md)

Pumgye installation followed private binary/unit/environment/SQLite/policy backup
and isolated DB-clone preflight. Policy stayed byte-equivalent through replacement
and another service restart; live mTLS management and native unknown-service
refusal passed. The first preflight failed before service mutation because GitHub
raw downloads lacked executable mode. Setting mode755 changed no signed bytes; a
new run passed. The original failure and backup remain preserved.

Hopae installation followed read-only configuration preflight and private consistent
SQLite/state/image/configuration/environment backups. Users, identities, sessions,
grants, MFA, providers, apps and durable profile authority remained intact. Live
HTTP/HOP1 mTLS expired/invalid refusal and another container restart passed. The
running executable matched the public signed raw.

A fresh operating system-administrator browser found all19 entries and opened
Hopae, Sumunjang and Pumgye without page/module/global errors. Sacho and the console
returned200. Hangang remains0.3.9 and Sumunjang0.3.6; external plugin replacement
and Hangang0.3.10 security qualification are pending. New Workload enforcement is
opt-in, not automatically enabled on existing operating routes. This is component
adoption, not complete Human/K8s-webhook/DBMS/throughput or whole-goal acceptance.
