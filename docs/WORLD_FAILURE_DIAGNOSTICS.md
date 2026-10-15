# Owned world failure diagnostics

The actual world runner captures its created namespace UID, Pod UIDs, phase and whitelisted container state/lastState/restart count/image IDs before cleanup. It reads bounded current and previous per-container logs only after confirming the captured Pod UID, with known fixture tokens/private keys and JWTs redacted; it does not read Secret/config/env objects. A replacement or missing Pod/log remains unavailable evidence. The API has no UID-preconditioned log request, so a concurrent replacement after the final read remains a diagnostic race; these logs are not authorization evidence.

Cleanup attempts port forwards, namespace and created CRD independently, and records baseline node UID/readiness and existing Pod UID/phase checks even after qualification failure. An original exception is retained if cleanup or evidence writing also fails. A cleanup/baseline failure after otherwise successful qualification fails the run. Baseline checks are a point-in-time comparison, not proof of unchanged workload data or container health; synthetic Retain PVs follow existing semantics. Log capture is best effort, not complete history.

This changes diagnostics only: protected application requests are never replayed and assertions, selectors, proof budgets and operation timeouts stay unchanged. Pure fault-injection tests verify exception precedence, cleanup completion, namespace UID refusal, previous-log capture, redaction and baseline failure. No actual cluster gate is claimed by these tests.

Log bytes are discarded if post-read namespace or Pod UID differs. Non-Workload namespace deletion uses atomic UID and resourceVersion preconditions. Every owned forward process is attempted despite an earlier termination error.
