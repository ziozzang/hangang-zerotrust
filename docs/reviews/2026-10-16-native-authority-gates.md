# Native Human ownership and Kubernetes API source gates — 2026-10-16

[한국어](../ko/2026-10-16-native-authority-gates.md)

These are reviewed **public source** changes. They do not replace the operating Hangang0.3.10/Hopae0.0.10/Pumgye0.1.8 releases or enable a Kubernetes authorizer.

| Component | Merged source | Exact qualification |
|---|---|---|
| Hopae | `1fb5db3ba2eaa107b44a0159a0b08cecd341a9d6` | 1,080 passed /42 existing ignored; strict workspace all-target/all-feature Clippy; independent review |
| Hangang | `d422c1cb8af5799d143abc4db450e6a2ce27c4c9` | 1,321 passed /58 existing ignored; 45 browser cases; strict Clippy; independent review |
| Pumgye | `b184bdd2bbbfd8879deb7359724f430ad003e951` | default126 /all-features135 passed, no failures or ignores; both strict Clippy configurations; independent review |

## Implemented boundaries

Hopae prepares actual DB provider rows, durable incarnations and configuration generation in one read transaction, compiles those same rows and retains exact native application publication ownership. OIDC and LDAP require an actually usable compiled adapter. Provider/configuration changes, material ABA and cross-Store/Registry use refuse additive ownership; ordinary authentication remains unchanged. A deterministic actual SQLite overlap test reproduced a missing final retirement observation, then passed after the final Acquire check. Pre-fix and final logs remain separate. This is not a Human session capability, remote-directory live-status guarantee or finished in-memory authentication hot path.

Hangang understands the new Pumgye policy context and preserves mapping/catalog data. The console offers explicit API-service creation, AAL0 defaults and typed `k8sapi:` assignments, rejects inappropriate network/Workload assignment kinds and retains raw draft edits. Local HTTP route validation rejects API-only policies. Browser cases use the compiled UI with an owned mock API; they are not a deployed API-authorizer test. Native policy round-trip and ordinary route-denial tests exercise the real pinned core.

Pumgye now has an actual default-off, fixed-cluster SAR listener using verified mTLS, exact client leaf fingerprint and a distinct per-request bearer. A dedicated bounded HTTP/1 driver reuses a TLS connection, evaluates mapping and grants on one native View and checks the original BOOTTIME budget/source/current owner below TLS during output. It retains the old response owner until complete TLS flush. Header/body framing is restrictive, errors never echo request claims, and unrecognized/unavailable authorization returns explicit Deny.

Actual local TLS and child-process main-listener tests passed Allow→Deny→Allow on one connection with native policy CAS, including HTTP/1 without ALPN. Deterministic pending-flush tests accept plaintext, queue a second request, then withdraw/stop/cancel: additional raw output remains zero and the second evaluator does not run. Tests also cover raw scalar/vectored/flush/shutdown refusal, irreversible retirement and owned task cancellation. This observes socket handoff boundaries; it cannot recall kernel-accepted bytes or already admitted Kubernetes effects. Controlled source-expiry checks are at the native capture boundary, not an actual same-socket source-expiry fixture.

## Next required gates

- Complete actual Engine-owned Human capture from real login/factor verification, exact handle/session/user/provider/factor/application state and original admission; then public Human RPC/SDK and typed Pumgye/Hangang enforcement. Current parsed session input lacks a final body/header digest; no empty-body assumption may substitute for actual future wire binding.
- Build versioned release candidates preserving existing observed-authentication production features. A default-feature-only Pumgye raw would omit existing observed permit RPCs and must not replace the current production binary.
- Qualify a disposable API-server/etcd with exact verified images, ordinary requester, explicit authorization cache disablement and failurePolicy Deny. Do not alter the existing primary authorizer. Use DB-native Pumgye policy initially to avoid a circular RBAC-import/webhook dependency. Revalidate and take cold/off-host backups before cluster changes; clean only owned UIDs.
- Qualify exact static artifacts, integrated console and real API-server behavior before signing/publication/internal adoption. Persistent H2, header-parser optimization, throughput, distributed memory snapshots/followers, lifecycle/recovery and the remaining original objective stay open.

Private evidence manifests: `/tmp/hopae-human-provider-registry-evidence.json`, `/tmp/hangang-kubernetes-api-console-evidence.json`, `/tmp/pumgye-sar-listener-evidence.json`. No keys, operational configuration or real account identities are reproduced.
