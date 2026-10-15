# Qualification-only raw gRPC tap: phase 1

`grpc_tap.py` is a local test transport, not an authentication source, signer,
capability constructor or production proxy. Phase 1 forwards unchanged unary raw
bytes to fixed owned loopback endpoints and records stage counts. No protobuf
payload is decoded, logged or persisted. Explicit optional DTO mutation/replay sequences are documented in [phase2](GRPC_TAP_HOOKS.md); they are disabled by default. Actual owner/proof/full-chain qualification remains separate.

Use an existing Python environment containing grpcio (qualified here with 1.84.0).
No Cargo, dependency installation, cluster or operating-service mutation is needed.

```sh
/private/existing-grpc-env/bin/python grpc_tap.py \
  --config /private/owned/config.json --ready /private/owned/ready.json
```

Keep the directory0700 and configuration/caller/key files0600. Config has exactly:

```json
{
  "listen": "127.0.0.1:41001",
  "tls": {"ca":"/private/owned/ca.pem", "certificate":"/private/owned/server.pem", "key":"/private/owned/server.key"},
  "inbound_caller_file": "/private/owned/inbound-caller",
  "maximum_inflight": 8,
  "upstreams": {
    "/hangang.hopae.v1.Authentication/Verify": {
      "endpoint":"127.0.0.1:41002", "server_name":"localhost",
      "ca":"/private/owned/upstream-ca.pem", "certificate":"/private/owned/client.pem",
      "key":"/private/owned/client.key", "caller_file":"/private/owned/outbound-caller"
    }
  }
}
```

Caller files contain only 32–256 ASCII graphic bytes, no newline or Bearer prefix;
inbound/outbound values must differ. The configuration owns routing and TLS trust.
The peer cannot supply endpoint, credentials, method selection outside the fixed
allowlist or metadata to relay. Both legs use verified TLS; incoming client
certificates are mandatory. Separate PKIs/certificates can be configured per leg.
Server-name verification is fixed to the owned localhost SAN. Addresses must be
explicit numeric loopback host:port; no remote DNS or environment proxy is used.

Allowed fixed methods and maximum decoded raw payload bytes:

- `hangang.hopae.v1.Authentication/Verify`: 32768.
- `hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved`: 32768.
- `hangang.hopae.v1.HumanAuthenticationReceipts/ObserveTime`: 4096.
- `hangang.hopae.v1.HumanObservedCredentialProjection/Project`: 8448.
- `hangang.pumgye.v1.HumanObservedProjectionPermits/Observe`: 8192.

Only configured members mount. The transport receive allocation ceiling is64KiB;
exact lower method caps are checked before any upstream call. This is bounded raw
transport coverage, not an auth-before-body-poll/production protobuf validation
claim. Replies are bounded at32KiB. Counts may exclude failures rejected by gRPC
before handler entry. An explicit finite original deadline is mandatory; forwarded
timeout is its remaining duration capped at one second. There is no renewal or
retry. Cancellation cancels the pending upstream await and releases capacity.
Upstream errors retain their status code but use fixed redacted details.

Readiness is atomically published0600. JSON-line stdin accepts only
`{"op":"snapshot"}` (safe per-method received/forwarded/ok/refused and inflight
counts) or `{"op":"shutdown"}`. EOF and SIGTERM close the owned server/channels.
No raw cookies, caller credentials, receipts, query bytes or output credential are
printed. Do not interpret counters as authorization/proof authority.

Run focused real TLS transport tests:

```sh
/private/existing-grpc-env/bin/python -m unittest discover \
  -s tools/test-support/native-human-runtime -p test_grpc_tap.py -v
```

The owned echo peer proves transport behavior only. It does not simulate a Human
grant or count as real Hop/Pum/Root evidence. Before actual A/B substitution or
in-flight replay, implement explicit bounded modes using actual generated wire
schema, retain original deadlines and correlate actual Pum Observe controls while
the original Root request/route owner remains live. Never synthesize proof or
create a second Source/nonce ledger. Final public H4 and unified SDK pins remain
prerequisites for that separate full-chain gate.

Parent PID changes are checked every200ms and use the same cleanup path even when inherited stdin remains open. An owned launcher-exit test keeps the pipe open and verifies the child stops and its listener can be rebound. Method caps intentionally cover a test subset (32KiB maximum), narrower than the Source's128KiB frame allowance; this does not qualify all Source request sizes.
