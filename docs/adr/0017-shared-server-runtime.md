# ADR 0017: Shared server runtime, independent domain cores

[한국어](../ko/0017-shared-server-runtime.md)

Status: accepted boundary; initial shared gRPC transport implemented in
[hangang-runtime](https://github.com/ziozzang/hangang-runtime), revision
81352ef. Pumgye (878bd2a) and Sumunjang (65856ab) have adopted this transport
and passed local process qualification. Hopae (e1aead3) also adopts the runtime
for its additional gRPC verification endpoint. All three additional gRPC gateway clients are now implemented and locally qualified.
Full request-chain, Kubernetes and production adoption remain open. This does not complete the integrated package.

Share server infrastructure rather than independently reproducing transport and
lifecycle behavior in every module. Keep provider/session ownership in Hopae,
authorization metadata in Pumgye, network policy in Sumunjang, and routing/enforcement
in Hangang. Their pure decision cores must not depend on HTTP or gRPC.

The initial library owns bounded TLS file loading, mandatory client certificates,
connection admission, TCP_NODELAY, gRPC stream/header bounds and request timeout.
Domain handlers own credential roles, message limits, global admission and decision
semantics. They query their existing in-memory snapshots without request-time SQL.
The current request timeout does not preempt blocking domain work; handlers must
remain bounded and cooperative.

Future shared facilities include native connection handling, shutdown/drain,
supervision and inherited listeners, health/telemetry hooks, and background snapshot
publication primitives. Domain persistence transactions, provider I/O, policy
compilation and source freshness rules remain domain owned. Generic infrastructure
must not silently authorize on missing data or stale snapshots.

Use pinned revisions across repositories, qualify each consumer independently and
keep independently scalable server processes. Transport parity, supervisor listener
handover and actual Kubernetes tests are adoption gates, not consequences of code
reuse. No shared multi-writer business schema is introduced.

## Default linkage and deployment

The shared server runtime is a Rust library compiled and statically linked into
each component executable. Independent Hopae, Sumunjang, Pumgye and Hangang
processes remain separately deployable and scalable; reuse introduces no additional
request-path service or network hop. Pin the library revision and qualify each
consumer before releasing its rebuilt executable. Linux releases default to musl
and must pass the existing no-ELF-interpreter artifact checks.

Dynamic shared-library loading is not the default extension mechanism. Provider
adapters and Lua policy extensions remain domain-owned and do not change this
linkage boundary. Static linkage does not imply constant policy: database-backed
in-memory snapshots and supported runtime configuration remain dynamic.

## Local qualification evidence

Pumgye: 17 server tests, strict workspace Clippy, actual gRPC/native mTLS requests,
credential isolation, bounded decoding and immediate policy revocation.
Sumunjang: 35 distinct server tests (also run through its compatibility binary),
strict workspace Clippy, actual gRPC/native mTLS parity, malformed and oversized
input rejection, revision fence, same-channel policy changes and supervised HUP
listener handover. Signed updater regression also passed upgrade, policy retention,
readiness rollback, tamper rejection and cancellation. These are local owned fixtures;
they do not prove actual Kubernetes gRPC deployment or production rollout.

Hopae e1aead3: actual mTLS gRPC calls through the existing authentication pipeline
qualified authenticated session allow, HTTP status/reason parity, immediate session
termination on the same channel, wrong/duplicate caller credentials, injected credential
headers and client-certificate refusal. Configuration tests cover mandatory mTLS,
caller authentication and distinct listeners. Full all-features tests: 914 passed,
42 existing environment-dependent cases ignored; strict all-target/all-feature Clippy
and EN/KO documentation checks passed. The administrator status reports the bound
gRPC address. Container build inputs now include protoc, schema and vendored LDAP;
that container build and actual Kubernetes rollout are not yet qualified.

Hangang 59e531d adds an optional Pumgye gRPC decision client selected by
`pumgye_authority.transport=grpc` (native remains default). The actual owning-server
fixture proves mTLS calls, administrator-role refusal, server-name mismatch refusal,
guest/all-permission denial, same-channel policy revocation and monotonic revision
fencing. Seven focused authority/response tests, 34 configuration tests, strict
all-target Clippy and documentation/publication checks passed. Global admission,
whole-batch deadline, decoding limits and coherent batch revisions are enforced.
At that stage, Hopae/Sumunjang gRPC clients and full actual gateway request-chain qualification,
credential/channel lifecycle qualification and Kubernetes/production adoption remain
open; this is not proof of complete gRPC application proxy support.

Hangang 42cc000 adds the Sumunjang gRPC client, selected by
`--guard-decision-grpc` at the configured decision address with mandatory mTLS.
Owned actual-server qualification (Sumunjang tool 83092e6) proves enforced
allow/deny, same-channel block removal/restoration, administrator-role refusal,
server-name mismatch, no HTTP fallback and cancellation, alongside native parity
and supervised listener handover. Twenty-two guard tests passed (one existing
ignored), plus strict Clippy and documentation/publication checks. Admission and
fresh mandatory authorization evidence now share a monotonic observed revision,
preventing stale replies from rolling back newer evidence across HTTP signals and
native/gRPC queries. Optional admission still follows its configured failure policy;
mandatory Pumgye network evidence is unavailable on failure. At that stage, Hopae client adoption,
full gateway request-chain and Kubernetes/production rollout remain unqualified.

Hangang 0125779 adds the Hopae gRPC client through a provider-independent pinned
`hopae-grpc` crate (Hopae contract extraction 7b5a8b8). Hopae scenario 9469182 invokes
the actual gateway client against its owned session engine: authenticated allow,
wrong caller key, server-name mismatch and same-channel session termination passed.
Five client tests, 34 configuration tests, an actual HOP1 proxy regression, strict
all-target Clippy and EN/KO documentation/publication checks passed. Existing
verification status, repeated cookies, identity and terminal response handling are
reused, with no HTTP/native fallback or decision caching. Console SSO still uses
HOP1. Full actual gateway chain, channel/credential lifecycle, Kubernetes and
production rollout remain unqualified; the overall goal remains incomplete.

## Actual four-process request-chain qualification

Hopae tool 6107b4c qualifies actual Hangang, Hopae, Sumunjang and Pumgye processes
through an HTTPS protected application route, over both mTLS HOP1/PPG1/HGD1 and
all-three gRPC decision exchanges. Scope: native API-key or external API relay
service identities, network evidence, service/IP/class/method permissions,
guest/invalid credential denial, audience isolation, credential consumption,
permission revocation/restoration, network block changes and authority outages.
Every refused request must leave the actual application backend call count unchanged.
Sumunjang outage/reconnection and Pumgye restart are exercised; revoked permissions
cannot be resurrected by unchanged bootstrap grants. The gRPC durable-restart case
also confirms Hopae profile tombstones survive actual restart. External verifier
variants for both transports prove an open circuit suppresses additional calls.
The existing three-process fixture also passed as a compatibility regression.

This closes the selected local API-service request-chain gate, not all identity
flows, all stream modes, generic metadata adapters, actual Kubernetes deployment,
production release/rollout or fleet performance. Console/UI and Kubernetes package
qualification remain separate work. No benchmark was run in this functional phase.

## Shared management TLS and console delegation

Runtime 039166b (0.1.1) adds the common mandatory-client-certificate TLS parser and
a bounded HTTP/1.1 HTTPS management lifecycle. Sumunjang 7851660 adds
`--management-tls` using its decision identity/CA, preserving collector/admin roles
and supervised listener handover. Pumgye 6708e1d and Hopae 6411523 reuse the same
parser for their existing transports; domain handlers and Pumgye peer audit identity
remain owned by their modules. Qualified: Sumunjang 35 tests and actual HTTPS/gRPC
fixture including role/certificate refusal and HUP; Pumgye 17 tests plus actual
HTTP/PPG1/gRPC revocation/recovery fixture; Hopae 14 native scenarios (one existing
ignored). Strict Clippy passed for each consumer.

Hangang 8c1c78d adds per-plugin mTLS identities/private CA roots, fixed DNS/SNI
validation and independent client pools. Six plugin tests, strict Clippy and an
actual Hangang console API -> independent Sumunjang HTTPS read/mutation fixture
passed. Assets remain digest pinned, operations audited and TLS paths/credentials
excluded from browser discovery. These latest management changes have not yet
been deployed/qualified in Kubernetes or production, and the full browser/provider
administrator suite remains open.

Hopae ee94562 adds optional `listen.admin_tls` through shared bounded HTTPS.
Runtime ba1a06c preserves actual TCP ConnectInfo and injects authenticated TLS peer
evidence only after a client certificate is present on the accepted TLS connection.
Hopae signed delegation accepts loopback or that server-provided evidence; HTTP
headers cannot forge it, and existing signatures/session/grant/assurance checks
remain required. Actual local mTLS tests qualify certificate refusal, native login
denial and shutdown; configuration and transport-forgery tests plus existing signed
actor scenarios pass. Full all-features tests: 917 passed, 42 existing cases ignored;
strict Clippy/documentation/publication checks passed. Remote delegated mTLS in
Kubernetes, Hopae browser management and federated console SSO are not yet qualified.

## Common engine boundary and extraction order

The common server engine is `hangang-runtime`, consumed as a library by separate
server binaries. Hangang remains the routing/enforcement gateway; the runtime is
not a fifth policy authority or a requirement to colocate the four servers.

| Layer | Owner | Sharing boundary |
| --- | --- | --- |
| Transport and process infrastructure | hangang-runtime | TLS, connection/stream admission, deadlines, cancellation, draining and listener lifecycle |
| Protocol contracts | Each domain's contract crate | Versioned codecs and typed messages; transport does not interpret allow/deny |
| Authentication | Hopae | Providers, credential translation, sessions, MFA and authentication circuits |
| Network evidence | Sumunjang | IP indexes, GeoIP, scoring, rules and network revision semantics |
| Authorization | Pumgye | Resource/action metadata, grants and authorization decisions |
| Routing and enforcement | Hangang | Request context, decision composition and upstream dispatch |

Common snapshot infrastructure may eventually provide atomic publication, generation
tracking and notification. Each domain still owns validation, DB transactions,
source leases, revocation and persistence. A common snapshot container must not
imply common policy schemas or a shared multi-writer database. Separate processes
retain independent quotas, failure isolation and horizontal scaling.

Extract in small stages: retain the qualified TLS/gRPC/management HTTPS base; next
compare the existing native accept loops and extract only equivalent connection,
cancellation and drain behavior behind domain-owned codecs. Then qualify inherited
listeners/supervision and reusable health/metrics hooks. Do not force Hangang's
application proxy into the decision-server request model. Configured limits remain
explicit per listener; generic defaults are not performance qualification.

For every extraction, retain real native/gRPC parity, malformed-input and role
refusal, same-channel revocation, restart persistence and outage refusal checks.
Run the owning consumers and actual Kubernetes request chain before rollout.
The selected four-process chain and Kubernetes console paths have passed separate
qualification; native lifecycle extraction, all provider flows and production
adoption remain open. See the current
[Kubernetes qualification record](../KUBERNETES_WORLD_QUALIFICATION.md) for scope.

## Shared connection ownership

Runtime 819177c (0.1.2) extracts `serve_connections`: nonzero bounded TCP
admission, actual peer addresses, TCP_NODELAY and owned connection tasks. Shutdown
drains for the caller-selected duration, then aborts and joins remaining tasks;
cancelling the owner aborts its JoinSet rather than detaching handlers. A socket
setup error rejects that socket without terminating the listener. Management HTTPS
uses this primitive with its existing 2,048 capacity and 5-second drain. Domain
handlers keep TLS/ALPN, credentials, framing and connection lifetimes.

Actual socket tests qualify capacity held until disconnect, capacity reuse, deadline
shutdown and owning-task cancellation; runtime tests and strict Clippy pass. Hopae 6eb07d3
adopts the same primitive for HOP1 with its existing 256 capacity and zero drain.
Hopae qualification: five actual management TLS/lifecycle tests; 917 all-features
tests passed, 42 existing cases ignored, including real HOP1/gRPC mTLS, session
revocation and certificate refusal; strict all-target/all-feature Clippy passed.
Both actual four-process request chains (mTLS HOP1/PPG1/HGD1 and gRPC) also pass,
including durable profile/permission revocation, actual owner restart and refused
backend non-dispatch. This new extraction has not yet been packaged or deployed in Kubernetes/production.
Pumgye/Sumunjang native adoption and inherited-listener gates remain open.

Pumgye 200ed48 adopts shared connection ownership for native PPG1 and management/
readiness listeners, preserving capacities 4,096/2,048 and existing protocol/TLS
handlers. Its listener futures retain their existing lifetime; owner cancellation
now aborts connection tasks. This is not a new OS-signal drain implementation.
An actual authenticated native socket test verifies owner cancellation closes the
connection. All 18 server tests (25 workspace tests), strict workspace Clippy,
actual HTTP/PPG1/gRPC mTLS role/certificate refusal, revision/CAS/revocation/
persistence checks and both four-process durable-restart request chains pass.
The first Python wire invocation lacked grpc; the existing qualification virtual
environment completed the same checks. New packaging/Kubernetes/production and
Sumunjang adoption remain open.

Sumunjang 5de28f3 adopts shared connection ownership for HGD1 and updates the
management HTTPS runtime pin. Its 256 connection quota, zero drain, loopback-only
plaintext, mTLS/ALPN and domain decisions remain unchanged. Qualified: 35 distinct
server tests plus workspace/update regressions, strict all-target workspace Clippy,
actual HTTPS management/gRPC/native role/certificate refusal, revision fencing,
same-channel updates, owning Hangang console read/mutation and supervised HUP
listener handover. The extraction initially left a test-only import in production
scope; moving it into the test module restored the strict gate. With all three
new domain-server binaries, both native and gRPC four-process durable-restart
chains pass. Latest images/Kubernetes/production adoption remain separate gates.

## Signed release staging

Sumunjang release tooling 2777b9e adds musl target preparation with distinct
linux-musl archive names, preserving complete target triples in both canonical
and compatibility signed manifests. Six release contract tests pass, including
GNU/musl archive coexistence. The qualified Linux amd64 musl artifacts were signed
with the existing pinned key and independently verified with OpenSSL; payload
version/target/download URL/size/digest and all checksums match. Seven assets are
uploaded to the v0.3.4 draft. GNU updater-target qualification and operational
rollout remain pending; the draft is not a published release. Other platform staging
support does not imply platform qualification. GitHub Actions remains disabled.

## Static Linux distribution default

User direction supersedes the earlier GNU release-preparation gate: Linux server
distribution defaults to static musl. Sumunjang 0c565c7 changes the release tool
default to x86_64-unknown-linux-musl and rejects an ELF interpreter before creating
or signing musl assets. Seven contract tests pass; real default preparation
reproduces all seven independently verified draft assets byte for byte. The GNU
compatibility build/check completed, but those binaries are not release assets.
Existing GNU installations require a one-time verified musl migration; thereafter
update discovery uses the actual compiled musl target. Never relabel a binary or
rewrite a signed target to evade target validation. Operational migration and
release publication remain open. This direction applies to Linux; other operating
system builds retain their separate platform qualification requirements.

## Sumunjang static publication and internal adoption

[Sumunjang v0.3.4](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.4)
is published at 352e707 with seven Linux amd64 musl assets. This revision enables
the previously excluded musl supervisor target only after the actual static
signed-update fixture passes upgrade, policy retention, readiness rollback, tamper
refusal, cancellation and HUP. ARM64 musl remains excluded from activation.
Workspace/server regressions and strict Clippy pass. Both final signed artifacts
were independently verified against the existing key and all uploaded assets
match after download. The tag points to the exact qualified source revision.

The internal network authority migrated from its GNU binary to the verified
static artifact with private executable/SQL/configuration rollback backups and
live read-only configuration preflight. Policy snapshots remained unchanged;
actual native mTLS and supervised HUP passed, and the running ELF has no
interpreter. After publication the real administrator update-check request reports
`up_to_date`; domain requests remain healthy. This proves the selected internal
Sumunjang rollout, not all-component release completion, every source/provider
flow, fleet update adoption or whole-stack throughput.

## Pumgye static release and internal adoption

[Pumgye v0.1.0](https://github.com/ziozzang/pumgye/releases/tag/v0.1.0) is
published at d51a8e8 with five Linux amd64 musl assets and its independent pinned
Ed25519 identity. Private signing material remains outside the repository and
assets. Release preparation checks static ELF, version and signing identity,
independently verifies the actual signature with OpenSSL, and binds the payload
to the artifact; five tests cover real signature acceptance, artifact/signature
tampering, checksum path escape and dynamic-loader refusal. All five uploaded
assets match after download and their signature/checksums verify against the
repository pin. This provides verified installation, not an automatic updater.

The internal Pumgye authority migrated from GNU to the verified static executable
after private binary/configuration/SQLite online backups. A separately owned
DB-clone process first proved exact policy equality and actual management/native
mTLS with unknown-service denial. The live service then passed the same checks
and a second restart, retained its durable policy, and has no ELF interpreter.
Live Hangang console delegation reads the identical policy after migration.
This selected rollout does not complete generic metadata adapters, fleet/update
automation, all identities or the overall goal.

## Hopae signed static release preparation

Hopae c5e148d defaults release preparation to Linux amd64 musl and rejects an
ELF interpreter before staging. Signing requires the existing repository pin,
checks identity/output separation before writing, and independently verifies the
actual Ed25519 signature with OpenSSL without a Python cryptography dependency.
Six tests cover actual signature/payload binding, forged signatures, dynamic-loader
refusal, wrong signing identity, private-seed/output separation and existing-output
preservation. Boundary, EN/KO documentation and publication checks pass.

The five current Linux amd64 assets are signed with the unchanged Hopae identity.
The candidate is byte-identical to the previously qualified static Kubernetes
image executable. Its read-only preflight against the actual internal configuration,
environment and database exits zero with no production replacement. DB-clone
lifecycle, provider/session continuity, operational rollout and refreshing the
existing multi-platform draft remain open. Older draft platforms must not be
reported as current-source qualified merely because their version string matches.

## Hopae publication and static operational continuity

[Hopae v0.0.4](https://github.com/ziozzang/hopae/releases/tag/v0.0.4) is
published at 6dccf80 with five Linux amd64 static signed assets. The existing
v0.0.3 tag pointed to older source; it was not rewritten or published. Its draft
assets were restored from the archived originals. Version 0.0.4 passes 917
all-features tests (42 existing ignored), strict Clippy, release boundary tests,
both static four-process native/gRPC chains and downloaded signature/checksum
verification. The new tag points to the qualified source commit.

Actual owner DB clones preserve users, identities, sessions/handles, grants, MFA,
logical provider/app records and profile configuration. An initial positive probe
failed in the old binary because the existing credential had expired against the
engine's millisecond clock. Production expiry was not extended. Only in separate
clones, a fresh declared credential was published through the actual signed
administrator API: HTTP/HOP1 mTLS allow, invalid/expired refusal and withdrawal
passed for both old and candidate engines. Original logical profile contents were
restored; the expected publication revisions/audits changed only in those clones.
This does not claim a fresh interactive login to every real external provider.

The internal container now runs the exact signed v0.0.4 executable. Private
configuration/environment/SQLite rollback backups, preserved logical owner data,
actual expired/invalid HTTP/native refusal, static ELF/digest, same credentials/
UID/network, restart and live Hangang delegated profile reads pass. The first
replacement rolled back on an overly strict environment-list order comparison;
name/value mapping comparison proves no environment value changed.

The actual Kubernetes/browser fixture also passes using Hopae 6dccf80, Sumunjang
352e707 and Pumgye d51a8e8 images: scoped request enforcement, administrator
publication/CAS conflicts, revocation and owning-Pod replacement, persisted state,
backend non-dispatch and authority outage. Archive checksums matched before use,
both nodes imported the artifacts, owned namespace cleanup completed and existing
ingress/node checks remain healthy. General metadata adapters, all identity/source
flows, automatic Hopae/Pumgye updates and full-stack throughput remain open.

## Hangang v0.3.3 static preparation

Hangang 519a1e5 prepares v0.3.3 with Linux amd64 musl as the release default.
Staging rejects an ELF interpreter in any of the eight included executables,
not only the gateway. Five release contract tests, 922 documentation links,
all-target Rust regressions and strict Clippy pass. All eight actual optimized
executables are static. Both actual four-process native/gRPC durable-restart
chains pass with the new gateway and published authority binaries. Five release
assets use the existing pinned signature identity; independent OpenSSL verification
checks signature, version/target/URL binding and all checksums. New gateway
Kubernetes/browser package qualification, operational rollout and publication
remain separate gates. Existing release tags have not been rewritten.

Hangang 519a1e5 also passes the actual Kubernetes/browser fixture with published
Hopae 6dccf80, Sumunjang 352e707 and Pumgye d51a8e8 images. Archive checksums
match on transfer, both nodes import the image, and owning namespace cleanup
completes. Scope includes actual administrator bootstrap/login, delegated policy
publication/CAS, authentication revocation/restoration and Pod persistence,
required-authority outages and refused backend non-dispatch. Existing ingress,
DNS and both nodes remain healthy. Read-only Docker preflight with the actual
operational mounts/environment/arguments exits zero. Five signed assets are
uploaded to the new v0.3.3 draft and independently verify after download.
This does not yet qualify operational replacement or published release adoption.

## Hangang static operational release

[Hangang v0.3.3](https://github.com/ziozzang/hangang/releases/tag/v0.3.3) is
published at 519a1e5 with five signed Linux amd64 assets. The internal gateway
container uses the exact verified static executable with unchanged credentials,
UID and host networking. Private image/compose/configuration/SQL rollback backups
and the configured drain window are retained. Management socket readiness/status,
refusal routing, normalized complete configuration and artifact digest/ELF checks
pass. The first replacement automatically rolled back on the raw configuration
comparison: new serialization adds default native transport selectors. An isolated
owner starts after moving its TCP/additional HTTP listeners to owned ports, and
only those two documented native defaults are normalized for the production
comparison; every other configuration change still fails acceptance.

The existing protected local demonstration returns 503 on both old and new
engines with the network authority in observe mode. This is not an upgrade
regression or a successful authenticated application-flow claim. Required enforced
network evidence and operator permission-policy qualification remain open; the
upgrade does not silently widen admission or renew expired credentials. The
current gateway deployment and publication do not complete all auxiliary console
process upgrades, generic metadata/fleet work, all identity flows or performance.

## Subsequent operational and Kubernetes qualification

Pumgye v0.1.1 (da45832) adds SIGTERM/SIGINT admission stop, five-second
HTTP/native task draining and a six-second overall bound including gRPC graceful
shutdown. Its actual process SIGTERM and in-flight HTTP response tests pass.
Hopae v0.0.5 (8ce0b8a) adds administrator-only service connector circuit/capacity
observations, with no credential or destination metadata; 919 all-feature tests
pass, with 42 existing ignored. Both releases use independently verified signed
static Linux amd64 artifacts and are adopted internally with private rollback
backups, exact durable state preservation, authenticated reads/refusals and restart.

The maintained remote Kubernetes world fixture passed again with Hangang
519a1e5, Hopae 8ce0b8a, Sumunjang 352e707 and Pumgye da45832. Actual Chromium
operator login, delegated management, immediate/durable authentication and
permission revocation, stale operator CAS refusal, Pod replacement, backend
non-dispatch on refusal and network authority outage passed. The owned namespace
was removed; Retain storage and previous node backup/off-host copy are preserved.
These are functional gates, not throughput qualification, full provider
interoperability, in-flight gRPC shutdown, projection RPC activation, inbound
Kubernetes authorization webhook or fleet snapshot replication completion.

## Native resource gates: candidate Kubernetes qualification

Hangang 4186b5f and Pumgye 2f6101cb296d add owner-managed resource/action
classification, mandatory native service binding and gateway resource dispatch.
The new statically built candidates passed the actual four-process mTLS gRPC
chain and remote Kubernetes package with published Hopae 8ce0b8a99391 and
Sumunjang 352e707674f2. Chromium verifies the integrated resource catalog and
owner policy publication; owner class/AAL/service reassignment, catalog deletion,
revocation, Pod replacement and network outage refuse upstream dispatch.
Existing node backup/off-host checksums and nodes/DNS/Ingress were preserved.
The owned test namespace was removed; synthetic Retain PVs remain.

The first run stopped on a diagnostic counter read timeout. Only idempotent
counter reads now retry transport errors under bounded time; protected requests
are never replayed. The passing run needed no retry. These candidates are not
new signed releases or operating migrations. Signed permission/projection receipts,
full provider coverage, fleet replication and throughput remain separate gates.

## Pumgye resource authority release

[Pumgye v0.1.3](https://github.com/ziozzang/pumgye/releases/tag/v0.1.3) is
published at b8e972b with five static Linux amd64 signed assets. Workspace tests
(36), strict Clippy, five release boundary tests, the exact signed resource
API/CAS/restart fixture, independent OpenSSL verification and downloaded asset
identity passed. Internal adoption preserved policy exactly after a real-DB-clone
preflight and private rollback backup; management/native mTLS and a second durable
restart passed. Hangang 0.3.4 source preparation at bd2bdfc passed all-target
regression (1,266 passed, 58 ignored) and Clippy; its complete static package build,
signed publication and operating migration remain pending. This does not complete
provider/fleet/projection or automatic-update requirements.
