# Hangang 0.3.10 final security candidate qualification — 2026-10-15

[한국어](../ko/2026-10-15-hangang-0310-final-security-qualification.md)

Public Hangang **v0.3.10** targets source
`e3fdd60ef5fc3066994dbb5d2c179b31200a1b56`. Publication and **backed-up gateway/console operating adoption are complete**. Earlier f45 and held97
results are historical, not substitutes for this final source/artifact. This
record adds final security and exact-candidate K3s evidence to the
[retained native qualification history](2026-10-15-workload-native-qualification.md).
It does not close the complete mixed-identity/provider objective.

## Exact source and published artifact boundary

The final source passed **1,320 workspace tests**, with **58 existing exclusions**,
strict workspace all-target/all-feature Clippy and formatting. Eight production
Linux amd64 musl executables were built and checked as static artifacts. Gateway
raw SHA-256 is:

`900f91cb49b5b424807bd44296a5c2a126292b2fdbd39c3772db2c6a91720efd`

The release has five files: gateway raw, its Ed25519 update manifest, release
public key, archive and checksum list. The archive contains all eight executables.
The gateway update manifest signs the gateway raw; it does **not** separately sign
every helper executable. The staged signed raw was verified to the exact digest
above. Publication does not itself establish deployment or an enabled route.

Private receipts: `/tmp/hangang-sacho-http2-final-source-checks.json`, frozen
`/tmp/hangang-sacho-http2-artifacts-e3fdd60/PROVENANCE.json`, signed stage
`/tmp/hangang-0310-signed-e3fdd60`, and
`/tmp/hangang-0310-signed-e3fdd60.verified.json`. No private keys, credentials,
configuration bodies or actual users are reproduced here.

## Compiled TLS and application acceptance

Identical frozen helpers first retained RED receipts against f45: normal selected
TLS statuses worked, but malformed trusted forwarding returned400 without HSTS.
The held97 binary passed HTTP/1 **16/16**, while actual HTTP/2 still reproduced
`h2`, `:authority` only, no Host, invalid XFF →400/no HSTS/origin0. These are
retained failures, not qualified final artifacts.

The exact final e3 binary passed **HTTP/1 16/16 and HTTP/2 4/4** with real OpenSSL
SAN certificates, explicit private CA and certificate/hostname verification. No
TLS verification bypass was used. Both configured test hosts received one exact
HSTS policy on200/401/403/404/502. Malformed forwarding400 responses carried HSTS
without reaching the counted origin. Unselected hosts and plaintext forged XFP
received no HSTS. Actual negotiated HTTP/2 `h2` covered authority-only success,
authority-only invalid XFF400 with HSTS, unrelated authority404 without HSTS and
conflicting Host400 without HSTS. Client URI/forwarded claims did not establish
TLS or select an unrelated domain policy. Domain response policies remain
explicit opt-in; no fleet-wide policy is implied.

Separate actual compiled Sacho+Hangang loopback qualification passed **24
combinations** of public/private visibility, authenticated account/group class
and forged identity-header vectors. Status/history/incidents/page checks used
Sacho-owned email membership; a forged groups header was not an authorization
source. This is fixed local-fixture acceptance, not proof of an operating Sacho
route or arbitrary account/group coverage.

Private receipts: `/tmp/sacho-compiled-hsts-e3-green.json`,
`/tmp/sacho-compiled-hsts-h2-e3-green.json`, their corresponding logs,
`/tmp/sacho-e3-isolated-regression.log` and its private result receipt. Prior
f45/97 RED JSON/logs remain preserved separately.

## Exact e3 actual K3s gates

Both actual runs completed with exit0 using these exact runtime sources:

| Component | Source |
|---|---|
| Hangang | `e3fdd60ef5fc3066994dbb5d2c179b31200a1b56` |
| Hopae | `848dc83540e1eb722ddd7e8d8820b07e11fa9d76` |
| Pumgye | `adaf985042b7af7b6aecc48cf34a02661abd4644` |
| Sumunjang | `d6fc1dec893df963c30f483ddf755421a98920b4` |

The Workload run exercised the real public SDK, verified bound ServiceAccount/Pod
subject kind3/AAL0, typed `workload_users`, dedicated preliminary resource metadata,
Pumgye permit, contract3 paired projection and final backend credential. Legacy
users grants could not substitute. Audience/claims/fixed-owner/realm failures,
reviewer-role withdrawal, durable owning profile CAS/readback/restoration, Hopae
replacement, Pod UID replacement with explicit new grant and ServiceAccount
withdrawal crossed their actual denial boundaries. Identical pair reuse was
refused before returning the first reply, with native auth/permit owner checks
before and after and backend exactly once. Flattened refusal is not SQL-row-
specific causal evidence.

The held old-proof restart refusal can also be explained by its original1s
expiry; it does not isolate restart as the cause. Raw TokenReview propagation
was about40.53s for Pod withdrawal and10.77s for ServiceAccount withdrawal,
separate from original maximum1s source-evidence lifetime. Restoration included
an HTTP503/backend0 observation before HTTP200/backend1, without relaxing any
per-request budget. A running-Pod attestation succeeded with no reported problems;
it records selected runtime imageIDs/Pod fields, not a functional grant by itself
or an independent process/config-ID attestation.

The separate **Service Any** run used native Sumunjang policy source and fixed
local-key/HTTPS-verifier slots with explicit verified identity relationships.
It passed actual issue/independent Observe/consuming refresh, missing/invalid/
ambiguous-factor denial, secret isolation, actual relay outage/circuit retention,
authority withdrawal and replacement. Only the separate origin bearer was
materialized. This remains Service/AAL0, not Human MFA or Human/Workload composition.

The same run passed the **actual compiled host and installed packages**: EN/KO
locale changes retained draft/DOM without extra owner requests; host-owned menu
order, three Pumgye section addresses and Back/Forward; uninstalled-destination
refusal; 390px bounded panels/forms/table wrappers and keyboard-scrollable region;
read-only native-source controls; stale-admin CAS conflict/profile revocation,
authenticated mTLS delegation and actual owning policy/source mutations. Source
RBAC withdrawal, checkpoint/authority replacement, source deletion/UID replacement
and explicit repin recovered only under fresh authenticated state. Refused
operations had no unauthorized backend effect.

Logs report owned namespace cleanup and exact created global-resource/CRD UID
cleanup. Synthetic Retain PVs remain intentionally. The two K3s nodes share one
physical host: this is actual functional qualification, **not multi-host HA or
throughput certification**. Preserved cold/off-host backup evidence is not a
restore rehearsal.

Private receipts: `/tmp/workload-world-e3-run1.log`, running attestation and pair/
held receipts; `/tmp/hangang-0310-e3-any-browser.log`; prepared command manifests
and capability/image-import evidence. Prepared manifests with initial `NOT RUN`
or unqualified markers were not rewritten into completion attestations: terminal
exit0 and completed run logs are the execution evidence. No cluster/private
configuration payload is copied into this public record.

## Operating adoption and final read-only checks

Gateway and console rollout completed with exit0 and separate success receipts,
using the same final e3 source and gateway raw digest above. Gateway preparation
included private configuration/SQL/image rollback backup and configured drain;
postchecks retained exact routing configuration and credential/UID/network
boundaries. The first gateway preflight encountered a permissions error before
mutation; the retained retry made executable permissions appropriate without
changing binary bytes and then passed. Rollout scripts evolved during early
launch, so no frozen executed-script checksum claim is made.

Actual post-adoption verified-TLS checks passed **16 cases** across the two
configured hosts: HTTP/1 and HTTP/2 200/401/404, malformed forwarding400 with HSTS,
and plaintext HTTP308 without HSTS. This establishes the observed operating
HSTS boundary, not every request variant or future configuration.

The final read-only K3s baseline check passed: both nodes Ready, all12 original
Pod UIDs preserved, no extra Pods, owned test namespaces or test CRDs remaining;
existing HTTP probes retained their expected results. Any browser evidence relies
on the completed execution log: its additional evidence directory was empty,
so screenshots or traces are not claimed. Synthetic Retain volumes remain.

Private receipts: `/tmp/hangang-0310-gateway-rollout-success.json`,
`/tmp/hangang-0310-console-rollout-success.json`,
`/tmp/sacho-post0310-live-verification.json` and
`/tmp/hangang-0310-e3-post-k3s-baseline.json`. Public details omit private backup
paths and operating configuration/credential payloads.

## Retained unknowns and remaining objective

The earlier All-composition browser failure (missing expected Sum plugin child)
remains unexplained: insufficient safe mount metadata was retained in that first
run. Later All diagnostic rerun and final e3 Any acceptance do not retrospectively
explain or turn it into a pass. The earlier Workload ConfigMap-vs-durable-profile
failure likewise remains a failed run; corrected owning CAS/readback has separate
acceptance. See the linked historical record.

Standalone console SSO, every admin/error/locale/in-flight state, real Google-user
provider interactions, Human observed/MFA full chain, self-owned account/recovery,
Human/Workload mixed composition, long-lived stream withdrawal, inbound Kubernetes
webhook and external DBMS adapters, clone/rollback/fleet fencing and measured
throughput remain separate work. Public Hop provider-owner source and uncommitted
TOTP provenance groundwork are not present in the qualified848 runtime by
implication. None of this record claims the whole original goal is complete.
