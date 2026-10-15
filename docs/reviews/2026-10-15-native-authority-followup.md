# Native authority follow-up — 2026-10-15

[한국어](../ko/2026-10-15-native-authority-followup.md)

## Operating console packages

Sumunjang [console-plugin-v0.1.4](https://github.com/ziozzang/sumunjang/releases/tag/console-plugin-v0.1.4) targets `d314d873a27d52d4a5fec981182f8118daeaf1f3`. Its three draft/public assets matched byte-for-byte; the latest server release remains v0.3.6. Hopae UI 0.1.6 matches the package in public Hopae v0.0.10. Operating Hangang 0.3.10 now pins these exact immutable plugin packages. Backend bindings, runtime arguments/unit/environment, core binary and backend policy/profile documents are unchanged. Private registry backup and preflight preceded installation.

The first installation attempt restored the previous registry after a verifier incorrectly compared dynamic systemd execution timestamps/PIDs. The corrected verifier compares the stable unit definition and actual process arguments; a separate retry passed. The failed attempt remains recorded.

Actual operating browser checks passed for both installed packages: EN/KO rendered text changes while preserving plugin DOM roots, Back/Forward navigation, 390px document width without overflow, no page errors, GET-only plugin backend requests and logout disposal. This used an owned administrator session; it does not qualify every real external-provider login or reproduce the earlier operator-specific SSO symptom.

Private receipts: `/tmp/console-plugin-014-016-final-handoff.json`, `/tmp/console-plugin-014-016-upgrade-result.json`, `/tmp/console-plugin-014-016-browser-result.json`, and `/tmp/sumunjang-plugin-014-publication/release-roundtrip.json`. Browser artifacts are private. No credentials or deployment configuration are reproduced here.

## Merged source prerequisites, separate from deployed runtimes

Hopae `bc64e41` atomically records exact native TOTP establishing provenance and refuses legacy fabricated linkage. Final workspace1,071 passed/42 existing ignores and strict Clippy passed; independent review found no blocking vector in this bounded prerequisite. An initial existing Workload SDK test refusal remains unexplained and retained; isolated, serial and final two-thread acceptance do not establish its cause. This schema8 source is not part of operating v0.0.10 and is not a Human observed capability.

Pumgye `e28d483` adds a private v1 SubjectAccessReview decoder: original-byte size/depth bounds, duplicate decoded JSON key rejection throughout, exact identity/attribute conversion into the existing core, explicit unsupported-input Deny, and fixed response constants without request reflection. Default116/all-features125 tests and both strict Clippy checks passed. Tests include same-core grant withdrawal. The fixture is derived from public upstream Go schema tags, not a captured API-server request. No listener, caller authentication, cluster selection, pooling policy or final transport freshness guarantee is activated.

Next implementation boundaries are exact compiled-provider ownership for native Human capture, then real Engine/current-owner/clock integration; and an authenticated SAR server using one captured native View and reviewed final response fences with reusable connections. Remaining providers, lifecycle/recovery, memory-backed replicas, long-lived revocation and measured throughput remain open. The full objective is active.
