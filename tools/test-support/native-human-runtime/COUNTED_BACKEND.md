# Owned counted HTTP backend

`counted_backend.py` is test support, not an authentication authority or a production service. It binds an ephemeral loopback HTTP port, records application request arrival separately from successful effect acceptance, and never records body content or header values. No Human proof, permission, session, or grant is constructed.

```sh
python3 tools/test-support/native-human-runtime/counted_backend.py \
  --directory /tmp/unique-owned-counter --ready /tmp/unique-owned-counter/ready.json \
  --credential-header x-owned-secret --credential-file /private/exact-header-bytes
```

The directory must not exist. The credential file contains exact bytes, without a trailing newline; it is never copied into evidence. Both credential arguments are optional together. Configured credentials must be unique and match in constant time. Ready/result JSON is published through a same-directory0600 temporary file, flush/fsync and atomic replace; directory permissions are0700. Ready contains `endpoint`, `effect_path=/effect`, `result_file`, `credential_header`, and `max_body_bytes`.

Keep stdin open. Send one bounded JSON line `{"op":"snapshot"}` for a safe JSON snapshot or `{"op":"shutdown"}` for graceful shutdown. EOF, SIGTERM/SIGINT or observed parent death also closes the owned listener. No HTTP control endpoint exists. The supervising runner must retain the exact child handle, wait for exit and preserve private evidence; SIGKILL cannot promise cleanup.

The fixed `/effect` path accepts POST/PUT/PATCH/DELETE/GET/HEAD/OPTIONS. Every parsed supported application request increments `request_count` before path/credential/body checks, including denied requests. Only a complete, bounded, correctly framed and credential-authorized `/effect` request increments `effect_count`. Use POST/PATCH as the actual side-effect gate; GET also counts so an unexpected origin dispatch is detected. GET/HEAD/OPTIONS may omit Content-Length for an empty body. Other methods require exactly one canonical Content-Length. Transfer-Encoding, Expect, duplicate lengths, truncated bodies and bodies over1MiB cannot increment effects. Connections close after one response;16 concurrent handlers and1second socket timeout bound the fixture. This is not a production HTTP parser.

A snapshot contains the two counters, last request method/safe path, and last accepted effect method, fixed path, actual body length/SHA256, sorted lowercase header names and credential-present/match booleans. Unknown targets are recorded as `[unrecognized]`; their query/path bytes are never persisted. Header values and body bytes never enter logs/results. Only the fixed path is preserved exactly, deliberately avoiding arbitrary secret-bearing URL logging. Counters are monotonic for the process lifetime; do not reset between a denial and its no-dispatch assertion.

```sh
python3 -m unittest discover -s tools/test-support/native-human-runtime -p 'test_*backend.py' -v
```

Tests use actual sockets for body hashing, denied/duplicate/truncated/oversized input, unknown-target privacy, concurrent counts, and a real child for readiness, snapshot and listener shutdown. The existing qualified `runtime_fixture.py` is unchanged. Two-account/provider/scope adaptation and actual four-core H4/Root execution are separate pending work; these tests do not establish Human end-to-end completion, distributed fences or throughput.

[한국어](COUNTED_BACKEND.ko.md)
