# Qualification-only Workload stage diagnostics

Non200 protected HTTP responses are classified only by exact fixed proxy body bytes. Known failures produce a fixed enum; unknown bodies produce byte count and SHA256 only. Status/elapsed/failure facts are recorded before the subsequent backend counter read, so a diagnostic transport failure cannot erase an already received response. Success bodies are never included in facts. A timeout before an HTTP response remains unavailable response evidence.

The qualification tap retains the same pooled channels, admission, caller checks and one-second deadlines. Only generic Verify gains a private RAII diagnostic: cumulative ingress/admitted/upstream-completed/cancelled counts, bounded elapsed time, fixed stage and tonicCode names, and fixed reply status enum (all unknown statuses map to other). It never serializes request IDs, auth fields, provider subjects, reply headers/body, Status.message or details. Cancellation includes future drop and records whichever stage was pending; it does not prove the upstream executed or stopped. Events are capped at4096 per process, so absence after the cap is not proof of no call. Logs do not create auth/permission capability or alter proof budgets.

The diagnostic tests cover secret-bearing errors/replies, unknown status, admission rejection and aborted pending futures. No real cluster recovery or fullchain qualification follows from unit tests. Existing failed run1/run2 remain preserved. Direct newly opened SDK connection success does not qualify existing Root/tap channel recovery; no restoration assertion has been changed.

Diagnostic writes are fallible and errors are ignored, including during Drop. Each record is bounded below4096 bytes. Synchronous qualification-only logging adds I/O cost; these tests are not throughput qualification.

Frozen diagnostic tap: source640a3dd487d81d908e8caedfeeb830e15357df9d, rawSHA256775a14a97c3842a9161911e4f2168195d6e19d2dc62faaaf419d513da6740806. Runner-only pin updated; held public SDK probe source/hash remain unchanged. This pin is not proof of actual cluster qualification; old artifacts remain preserved.

The replay parser separately validates the exact Verify-stage keyset, enums and bounded integer types (booleans refused), saves these only as diagnostics, and excludes them from pair counts. Unknown or malformed events still fail. Run3 exposed the missing mixed-event parser compatibility before first Project; no product failure or replay pass is inferred. Frozen tap640 bytes are unchanged by this Python-only fix.
