# Owned native Human runtime fixture

This helper runs an external production Hop binary, an owned OIDC issuer or TLS OpenLDAP directory, and actual portal login, application handoff, TOTP enrollment/step-up and logout. It never constructs native primary sessions, proof records or SDK Observations through SQL/private constructors. A consumer must use the public SDK against its real mTLS Human RPC.

This is a local qualification tool, not a deployment template or a complete Human projection/Root dispatch test. Its OIDC issuer performs real RSA JWT signing, nonce and S256 PKCE exchanges on loopback. LDAP uses LDAPS or mandatory StartTLS and an owned directory. Native receipt lifetime remains the original bounded1s; waiting for the next TOTP counter does not extend a proof.

## Requirements

Use Linux, Python3 with `cryptography`, OpenSSL and a qualified production Hop executable. Human Source/RPC/scope support is present in Hop source `b08e105666de99f2ae957cff16ca9f3c75d3f7c5`; an executable's displayed0.0.10 version alone does not establish that capability. The consumer must retain/verify its exact source and binary SHA. Build without test hooks. No operating configuration, DB, token or directory should be supplied.

For LDAP, Docker must already contain the owned image `hopae/owned-openldap:bookworm`; the helper never pulls it. Build that local fixture image from the matching Hop checkout with `docker build -t hopae/owned-openldap:bookworm tests/fixtures/ldap`. See [Hop's LDAP fixture source](https://github.com/ziozzang/hopae/tree/b08e105666de99f2ae957cff16ca9f3c75d3f7c5/tests/fixtures/ldap). Random owned container names and loopback ports use the existing fixture's host-network arrangement; this is not a production container isolation recommendation.

## Run and private IPC

```sh
fixture_root="$(mktemp -d)"
python3 tools/test-support/native-human-runtime/runtime_fixture.py \
  --binary "$OWNED_HOPAE_BINARY" --provider oidc \
  --directory "$fixture_root/runtime" --ready "$fixture_root/ready.json"
```

`--directory` must not exist and is created0700. `--provider ldap` creates its own directory container; `--ldap-starttls` chooses mandatory StartTLS. The optional external-owned-directory interface uses `OWNED_LDAP_CONFIG` JSON plus `OWNED_LDAP_BIND_KEY` and `OWNED_LDAP_USER_PASSWORD` environment references, scoped to this helper process. Never log their values.

Ready JSON is atomically published0600 only after a native AAL1 login and application handoff. It contains endpoint/server_name, CA and dual serverAuth/clientAuth peer certificate/key paths, caller_file, signing public key hex, fixed issuer/key/authority floors, exact HumanScope metadata and a private cookie1 file path. The consumer verifies its expected binary SHA and obtains the stable subject from an actual public SDK Observation before publishing an owning Pum `human_users` grant. It must not derive or manufacture an Observation/subject from this metadata.

The fixed fixture scope is service orders, audience orders-api, application app, route owned-route revision11, destination byte0x12 repeated32, header policy13, no bound header slots and x-owned-secret reserved. Actual SDK request data is GET /data with body bytes `body`. Verification headers describe https://app.example.test/data, clientIP192.0.2.10, no User-Agent and route owned-route. The ready destination digest is a32-element byte array. These are reserved synthetic fixtures, not operating bindings.

Send bounded JSON lines to stdin and read safe JSON replies from stdout:

- `{"op":"login","aal":1}`: fresh actual primary login/handoff; updates cookie-1.
- `{"op":"login","aal":2}`: actual primary login, native TOTP enrollment if necessary, step-up/handoff; updates cookie-2. Allow65s for the fixture operation: it may wait until the next30s counter to avoid replay. Proof timing bounds are unchanged.
- `{"op":"revoke","aal":1}` (or2): native portal logout for that browser's current session. Old cookies remain privately available for rejection tests. Restoring access means a fresh login, not reviving a terminated session.
- `{"op":"shutdown"}`: terminate/wait for the exact owned Hop child and remove the exact owned LDAP container.

Replies expose ok/op, plus aal/cookie_file for login. No cookie, bearer, key, TOTP seed, header, proof or context payload appears on stdout. Private config/body diagnostics can contain enrollment data and must remain0600 in their0700 directory. SIGTERM invokes cleanup; loss of the owning parent PID triggers the same path. Consumers should request shutdown or SIGTERM and wait before escalation. SIGKILL is not a cleanup guarantee. Evidence directories are retained deliberately.

## Tests and claim limits

```sh
python3 -m unittest discover -s tools/test-support/native-human-runtime \
  -p test_runtime_fixture.py -v
```

Three deterministic tests cover ready-file invisibility before complete publication, replacement retaining old complete JSON and failure preserving old data/removing pending files. Private writes use exclusive0600 same-directory temporary files, flush/fsync and atomic replacement. This prevents the previously observed ready.exists/read-EOF race without retrying authentication or weakening timing.

The independently executed native qualification used owned OIDC, LDAPS and mandatory StartTLS login/TOTP through the public Human SDK and actual Pum Authority/DB policy CAS. Network/route/plan were authenticated fixture peers in that gate. This source helper alone proves neither SDK/Pum acceptance nor full paired projection/Root/backend effects, actual external IdP behavior, atomic distributed revocation or throughput. A real consumer must execute those separate gates and retain exact hashes and failure evidence.

### Actual public SDK → native Pum consumer

From a Pum checkout containing public source `f6fb7d9a7e92b615d3c2525999b55a66e7a491ac`, set the absolute path to this repository's copied helper and the exact qualified Hop binary, then run the explicitly ignored native test:

```sh
OWNED_HUMAN_RUNTIME_FIXTURE=/absolute/zerotrust/tools/test-support/native-human-runtime/runtime_fixture.py \
OWNED_HOPAE_BINARY=/absolute/qualified/hopae \
OWNED_HUMAN_PROVIDER=oidc \
cargo test --locked -p pumgye-server --features observed-authentication \
  --test human_observed_permit actual_native_hop_sdk_to_pum_authority_human_permit \
  -- --ignored --test-threads=1
```

Repeat with `OWNED_HUMAN_PROVIDER=ldap`; mandatory StartTLS additionally sets `OWNED_HUMAN_LDAP_STARTTLS=1`. These are explicit separate functional runs, not authentication retries. The consumer preserves private evidence, independently obtains the SDK subject before Pum grant publication, checks actual AAL/plan/policy CAS and confirms native logout refusal while the original proof budget is still live. It does not restore a terminated session or qualify Human projection/Root output.
