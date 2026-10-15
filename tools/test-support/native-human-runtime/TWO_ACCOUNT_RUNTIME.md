# Two-account OIDC and fixed-scope adapter

`two_account_runtime.py` is an additive owned test adapter. The historical qualified `runtime_fixture.py` remains byte-identical. It reuses that helper's actual HTTP portal cookie handling, native TOTP enrollment/step-up, logout, private atomic file publication and exact child cleanup. Its separate startup constructs the fixed source configuration before launching the external actual Hop binary. It never creates sessions, primary/factor SQL rows, receipts, permissions or SDK Observations itself.

```sh
python3 tools/test-support/native-human-runtime/two_account_runtime.py \
  --binary /private/exact-qualified-hopae --directory /tmp/new-owned-human \
  --ready /tmp/new-owned-human/ready.json --source-scopes-json /private/server-fixed-scopes.json
```

The scope file is server-owned startup metadata, not request input. It is read/validated once before startup and contains1..16 native Source scope objects: `service`, `audience`, `application`, `route`, positive safe-integer `route_revision`, nonzero lowercase64hex `destination_sha256`, positive safe-integer `header_revision`, lowercase fixed `headers` and `reserved_headers`, `maximum_entity_bytes`0..16MiB. Unknown keys, duplicate canonical bound scopes, invalid/reserved headers and more than one actual application refuse. Multiple explicitly fixed destinations/routes are permitted by the adapter; the actual qualified Hop Source must independently accept them. Do not infer that the older b08 runtime supports the new H4 multi-destination contract. The adapter does not enable H4 or provide projection receiver/secrets configuration yet.

The actual application uses `app.example.test`; portal is `auth.example.test`, native source revision7 and issuer `native-human`. Source scopes must match the actual Root route/configrevision/selected origin hash and fixed header policy. The helper's native login context retains IP192.0.2.10 and no user agent. Root must establish that exact trusted client context or use a separately reviewed adaptation; caller forwarding headers are not proof.

The owned loopback OIDC issuer produces distinct RS256 subjects for accounts `a` and `b`. Account selection is only a qualification interaction at that owned issuer's `/authorize` endpoint; production Hop still verifies actual signed issuer/audience/nonce and S256 PKCE before creating native primary provenance. Authorization codes are single-use. These synthetic accounts are not privileged native principals or client-authoritative Human subject strings. Canonical `human1` values must be obtained from actual public SDK Issue+independent Observe, never derived by this tool.

Ready is private0600 and includes the original transport/key metadata, `scope` (first SDK-shaped scope), `scopes` (all SDK-shaped scopes), `accounts=["a","b"]`, and `cookies={"a":{"1":private_path},"b":{"1":private_path}}`. Ready appears only after both real portal AAL1 logins. stdin commands:

```json
{"op":"login","account":"a","aal":2}
{"op":"revoke","account":"a","aal":2}
{"op":"shutdown"}
```

`login` returns only cookie path and safe account/AAL metadata. Each account keeps its own native TOTP enrollment seed and Browser session. AAL2 uses the actual portal and may wait for the next30second TOTP counter; give fixture-control IPC a bounded65second timeout, without extending native proof/query budgets. `revoke` uses the actual portal logout for the selected saved Browser session. No grant is created by login; Pum grants must be owning management bootstrap/CAS over observed canonical subjects. Keep stdin open; EOF, SIGTERM or observed parent death triggers exact owned child cleanup. Preserve private evidence, never print cookies, tokens, keys or OTP seeds.

```sh
python3 -m unittest discover -s tools/test-support/native-human-runtime -p 'test_two_account_runtime.py' -v
```

Current qualification is seven Python tests: actual owned OIDC signed-token separation/nonce/signature, single-use code/PKCE refusal, scope bounds/duplicates/reservations, account-specific seed separation, and configuration-only mocked process startup proving prepared scopes reach the emitted native config. No actual Hop binary was run for this adapter. The configuration test is not native authentication evidence. Actual two-account portal/TOTP→H2/H3/H4→Root/backend execution remains required once the qualified H4 binary/config interface is available. Existing single-account helper/provider qualification does not automatically transfer to this new adapter.

[한국어](TWO_ACCOUNT_RUNTIME.ko.md)
