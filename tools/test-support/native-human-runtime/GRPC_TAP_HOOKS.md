# Explicit Human qualification hooks (phase 2)

These optional modes extend the [raw transport](GRPC_TAP.md) only for a controlled
local security test. They are not production forwarding, authentication, proof
validation, SDK observations or grant constructors. With `qualification` absent,
the original transport remains unchanged. The actual four-core A/B and replay
gates still require qualified public H4/Root binaries and unified SDK pins.

Add exactly one `qualification` object to the existing private tap configuration:

```json
{
  "qualification": {
    "mode": "issue_cookie_b",
    "schemas": {
      "gateway_proto": "/private/public-source/gateway.proto",
      "decision_proto": "/private/public-source/decision.proto"
    },
    "cookie_b_file": "/private/owned/actual-native-cookie-b"
  }
}
```

Both schema files are read once with bounds and matched to immutable public source:

- Hop `b08e105666de99f2ae957cff16ca9f3c75d3f7c5`,
  `crates/hopae-grpc/proto/gateway.proto`, SHA256
  `745a367111a0e9cb963dca8461841dd26bdbdea4cefafb502f9a5096f21c388c`.
- Pum `f6fb7d9a7e92b615d3c2525999b55a66e7a491ac`,
  `crates/pumgye-grpc/proto/decision.proto`, SHA256
  `df2ed98f9c9b5df451874f93ab91b11d2e83b4583f4618613f40729db3e4539b`.

An existing grpcio-tools/protobuf environment compiles those snapshots into a
private temporary descriptor set, then uses a private DescriptorPool. The directory
is removed before serving. No generated Python modules, SDK capability factories,
network downloads, installation or signer exist. The existing phase1 message and
inflight bounds apply; this is a <=32KiB test subset of Source's128KiB allowance.

## `issue_cookie_b`

Only HumanAuthenticationReceipts/IssueObserved is mutated. The0600 file contains
the actual native `__Host-hopae` cookie VALUE produced by the owned B portal session,
without a cookie name, newline or JSON encoding (maximum4096 bytes). It is read once.
Exactly one case-insensitive Cookie header and exactly one case-sensitive native
cookie are required. Missing/duplicate/empty or already-B native cookie refuses.
Other cookies, headers, original native context, request IDs, fixed scope and final
body metadata remain unchanged; DTO unknown fields survive. Early Verify and all
other methods are forwarded unchanged. No cookie value is printed or persisted.
This is an explicit malicious-authenticated-peer fixture, never a production option.

The runner must establish BOTH actual A/B accounts and grants independently, verify
distinct canonical subjects, and prove A/A and B/B controls. Changing only a
metadata label or using an ungranted B cannot qualify the intended lineage test.

## `exact_pair_replay`

Use `{"mode":"exact_pair_replay","schemas":{...}}` with no cookie field. Configure
both fixed HumanObservedCredentialProjection/Project and direct actual Pum
HumanObservedProjectionPermits/Observe upstreams, with their own caller files and
mTLS trust. The latter must point directly to the actual owning Pum endpoint.

For each valid contract4 Project, the tap keeps the original first reply only in
bounded process memory, then before returning anything to Root:

1. sends the EXACT original `permission_query` bytes to actual Pum Observe;
2. replays the EXACT original Project bytes/IDs/query to actual Hop;
3. requires Unavailable with exact fixed detail `native Human projection refused`;
4. repeats actual Pum Observe with the original raw query;
5. checks correlation, receipt SHA, domain, revisions, TTL0, positive/nonincreasing
   budgets and a positive original output/deadline budget attenuated using native
   Linux BOOTTIME from before the FIRST Project call.

A second success, arbitrary Unavailable, TLS/transport error, wrong status/details,
failed/mismatched/expired control or expired deadline FAILS; no renewed proof or
second successful reply is returned. No retry is made. The sole original reply is
returned unchanged only after this sequence. Cancellation can discard a first
successful result and burn its pair, as with any lost response; it does not imply
rollback. Python drops references on completion/cleanup but does not promise memory
zeroization. Payloads/receipts/queries/output credentials are never logged or saved.

**The sequence alone is NOT a complete replay oracle.** Its safe snapshot reports
`requires_runner_query_budget_check: true`, replay elapsed BOOTTIME nanoseconds and
Pum before/after lower budgets; `control_sequence_complete` is not a grant or an
assertion about one SQL row. The actual runner MUST read the exact owned Hop startup
configuration and establish its original query-budget minimum, then conservatively
verify replay elapsed (including source/receiver rate margins) is strictly within
that bound. Do not supply a caller-asserted budget or infer it from proof lifetime.
If query expiry or transport timing cannot be excluded, mark the gate
inconclusive/FAIL; live signed proofs can outlive an individual query admission.
Also retain independent real owner controls and the actual Source pair-ledger tests.
The runner must hold the original Root request/route owner throughout this sequence.

## Reproducible parser/TLS tests

Supply the two exact public source files; missing paths explicitly skip the hook
suite rather than substituting a schema. For example:

```sh
HUMAN_TAP_GATEWAY_PROTO=/private/public-source/gateway.proto \
HUMAN_TAP_DECISION_PROTO=/private/public-source/decision.proto \
/private/existing-grpc-env/bin/python -m unittest discover \
  -s tools/test-support/native-human-runtime -p 'test_grpc_tap*.py' -v
```

The owned TLS peer uses clearly labelled opaque non-proof fixture bytes to test
parser preservation, raw replay ordering, correlation, refusal classification,
original deadline/output attenuation and cancellation. It does not establish a
real Hop signature, H0 session, Human SDK observation, actual Pum permit, replay
nonce consumption or backend success. Those remain separate actual full-chain gates.

## One-way startup-armed control

Qualification configuration accepts optional `initially_armed` with a JSON boolean only. Omission defaults to `true`, preserving earlier mutation/replay behavior. `false` allows ordinary A/A and B/B controls before a later mutation/replay request. Schema/key/cookie files and all upstreams remain fixed and validated at startup; the actual private B cookie file must already exist. Arming never supplies a new cookie, key, endpoint, proof or mode.

Private stdin `{"op":"arm"}` returns `{"ok":true,"op":"arm","armed":true}` exactly once for configured unarmed Hooks. A second arm returns `{"ok":false,"op":"arm","stage":"already_armed"}`. With no configured Hooks it returns `{"ok":false,"op":"arm","stage":"not_configured"}`; it cannot create Hooks. Unknown commands/extra fields refuse; there is no disarm or reconfiguration command. Qualification snapshots add boolean `armed`. Each RPC captures whether Hooks were armed at handler entry before its first upstream await; arming later cannot turn an already unarmed in-flight Project into a replay. Future calls still retain original deadlines and no retries.

For exact-pair replay, safe `last_replay` also includes `through_replay_elapsed_boottime_ns`: local elapsed time from immediately before the FIRST Project RPC through the replay refusal, including the first Project and Pum-before observation. `elapsed_boottime_ns` remains the replay RPC duration alone. The full sequence still performs its existing output-budget/deadline check after Pum-after. These are local diagnostic durations, not fresh source leases or foreign absolute timestamps. The owning runner MUST conservatively charge through-replay duration against the actual configured original Hop query admission (including rates/quantization), and reject inconclusive/expired controls; a refused replay status alone is not a replay-ledger oracle.

The four-core `NativeTap` wrapper accepts optional fixed `qualification` startup metadata and exposes `.arm()`/`.snapshot()`. Exact replay additionally mounts direct actual Pum Human permit Observe on its fixed Pum outbound transport. Management HTTPS and actual Hop/Pum observers stay direct. Wrapper/source hashes must be refrozen together. Actual TLS tests cover default armed behavior, explicit unarmed controls then mutation, invalid flag types, duplicate arm, no-Hooks/unknown control refusal, and arming while an unarmed Project is in flight. IPC tests cover real child arm acknowledgements/snapshot/cleanup. These are transport/control tests, not fabricated native Human proof qualification.

## Partial replay progress on cancellation

Qualification snapshot `progress` is null before an armed Project or contains only safe fixed diagnostics: `stage` (`first_project`, `pum_before`, `replay`, `pum_after`, `complete`), `elapsed_boottime_ns`, `deadline_remaining_ms`, `first_project_elapsed_boottime_ns`, validated `first_output_remaining_ms`/`pum_before_remaining_ms`, `through_replay_elapsed_boottime_ns`, `cancelled`, fixed gRPC enum names `rpc_code`/`replay_rpc_code`, and `clock_failed`. Numeric samples may be null when unavailable. There are no payloads, subject/receipt IDs, credentials, body bytes, key values or foreign absolute timestamps.

Stage/time/deadline are sampled before each awaited operation; through-replay progress is retained BEFORE the Pum-after await. Cancellation updates only diagnostic fields and re-raises the same CancelledError. It never substitutes a reply, renews a query/source budget, retries, or marks a sequence complete. `last_replay` still exists only after the original full successful control sequence; partial progress is not replay qualification. Diagnostics describe the most recent controlled armed Project, so the owning runner must serialize qualification requests and preserve failed attempts separately. A transport test cancels at Pum-after and proves preserved progress, no successful response, no completed sequence and no `last_replay`.

This instrumentation does not prewarm channels or alter transport semantics. A future channel-readiness diagnostic, if separately approved, must not issue an RPC or renew proof/source state. An actual failed/incomplete run must remain failed until observed timings establish the cause; cold TLS is not inferred from counters alone.
