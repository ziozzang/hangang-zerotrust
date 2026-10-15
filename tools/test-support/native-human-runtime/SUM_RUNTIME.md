# Actual Sum network authority fixture

`sum_runtime.py` launches an owned production Sum process with a fresh SQLite database, enforce bootstrap and actual mandatory-mTLS `Network/Check`. It is not a network proof peer. No Cargo, internet, cluster or operating service is needed. The default required binary SHA is the immutable public Sum0.3.6 roundtrip raw `25a197f1c39bddf63fe4c168294536475ed2b4ba2aa16bcbe7ee4ac2dfec8654`; an explicit different expected SHA is test-owner configuration, never version-string trust.

Use an existing Python environment containing grpcio/grpcio-tools. The local authoritative Sum checkout supplies `crates/guard-grpc/proto/network.proto`; its expected SHA is pinned to `5723fa6c5616b229679b9c7b26c5da5e994b300f4d98a542f91d4cb0fba6cecf`. Stubs are generated only inside the private fixture directory. No dependency installation occurs.

```sh
/private/existing-grpc-env/bin/python tools/test-support/native-human-runtime/sum_runtime.py \
  --binary /private/verified-sumunjang --sum-source /private/authoritative-sum-checkout \
  --directory /tmp/new-owned-sum --ready /tmp/new-owned-sum/ready.json \
  --client-ip 192.0.2.10
```

The root must not exist. Its mode is0700 and umask077 protects DB/logs/credentials. All listeners bind127.0.0.1 ephemeral ports. The supervisor is a new owned process group; shutdown sends SIGTERM, waits, and uses a group-specific kill only if the exact retained owned process fails to exit. No process-name killing or operating tokens are used. TLS and admin/collector credentials are newly generated; no privileged service configuration is copied. Ready is atomic0600 and contains actual gRPC HTTPS endpoint, TLS path/name metadata, private collector-file path, exact client IP and binary/proto hashes. It contains no credential values.

To share a harness CA, supply `--tls-json` with EXACT keys `ca`, `server_certificate`, `server_key`, `certificate`, `key`, `server_name`. Values are private file paths except fixed `server_name=localhost`. Server identity must include localhost and127.0.0.1 SAN; client identity must allow clientAuth, and server identity serverAuth. The existing Human fixture dual-use peer certificate can satisfy this test boundary. Actual TLS verifies the supplied chain/name; a JSON label does not grant trust. Pum network-live uses ready.endpoint/ca/certificate/key and the private collector credential. Actual Root trusted clientIP must agree with the configured network; never fabricate Sum Enforce evidence.

Keep stdin open and send bounded JSON lines:

- `{"op":"check"}` returns only actual verdict/mode/revision/TTL and safe status.
- `{"op":"deny"}` uses actual management `/v1/policy/document` CAS to clear the allow exception, then actual `/v1/blocks` to block the client network, and checks the real gRPC endpoint.
- `{"op":"restore"}` CAS-restores the original exact IP allow entry and removes the fixture block, then checks gRPC.
- `{"op":"block"}`/`{"op":"unblock"}` manipulate only the owned native block. Allow exceptions may take precedence, so these operations alone are not promised to deny an allowlisted IP.
- `{"op":"shutdown"}` exits and cleans up. EOF/SIGTERM/parent-death also shuts down the owned process.

Policy CAS and block mutation are separate real native management operations, not an atomic combined transaction. The fixture does not mislabel empty allow as deny-all, or invent a `deny` policy field. Restoring policy does not erase unrelated engine state. These operations are serialized by fixture control; no proof TTL or source clock is renewed. Sum block expiry remains the native block policy contract, not an observed authentication budget.

Actual qualification (explicit opt-in):

```sh
OWNED_SUM_BINARY=/private/verified-sumunjang OWNED_SUM_SOURCE=/private/sum-checkout \
 /private/existing-grpc-env/bin/python -m unittest discover \
 -s tools/test-support/native-human-runtime -p test_sum_runtime.py -v
```

Set `OWNED_SUM_SHARED_TLS=1` on that command to exercise `--tls-json` with separately generated owned shared CA/dual-purpose leaf before fixture startup; it also tests a client leaf signed by another CA. This shared-material branch passed against the exact public0.3.6 binary, including allow/deny/restore and cleanup. These are fresh fixture keys, never operating identities.

The real process test proves enforced Allow→native CAS/block Deny→stale CAS409 remains denied→CAS/unblock Allow, increasing native snapshot revisions, wrong/admin caller refusal, missing-client-certificate refusal and closed-listener cleanup. It records only safe private RESULT facts. Pure tests cover private ready publication and binary mismatch refusal before spawn. It does not establish Human H4/Root full-chain dispatch, Kubernetes source mode, suspend guarantees of every legacy path, distributed DBMS, atomic remote withdrawal or throughput. Existing single-account helper bytes remain unchanged.

[한국어](SUM_RUNTIME.ko.md)
