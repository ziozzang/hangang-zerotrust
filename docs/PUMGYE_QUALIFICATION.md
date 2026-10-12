# Pumgye / Sumunjang / Hopae integration qualification

Verified Linux deployment: 2026-10-13. Integration source is merged in
[Hangang #5](https://github.com/ziozzang/hangang/pull/5),
[Guard #2](https://github.com/ziozzang/hangang-guard/pull/2) and
[Hopae #3](https://github.com/ziozzang/hopae/pull/3).
[Pumgye](https://github.com/ziozzang/pumgye) is public.

## Requirement evidence

| Requirement | Evidence |
| --- | --- |
| Deterministic bounded manager | `pumgye-core` compiler, immutable bitsets, Guard arena prefix trie; adversarial core tests |
| Service/user/IP matrix and class/assurance | Core regression cases; native Hangang Pumgye menu; browser user/CIDR assignment and publication |
| Guest and method denial after login | Hangang native resource tests; owned deployed-binary HOP1/HGD1 smoke |
| Network evidence inside authorization | Fresh authenticated Sumunjang evidence; mandatory observe/unavailable refusal, explicit deny dominance; cache/fail-open tests |
| Header and namespace boundaries | Native identity/AAL checks; spoof rejection; resource/canonical-path and downgrade regression tests |
| Durable administrator publication | Existing Hangang config authority, If-Match CAS, bounded validation and audit; 89 admin API tests; stale publication refusal |
| Revocation | Real static binary test publishes revoked user rights, terminates an active stream within 1.5 seconds and refuses later access |
| Unified management and SSO | Live HTTPS Pumgye/Sumunjang/Hopae menus, existing SSO/provider entry, delegated Hopae status/users and logout cleanup |
| Logging/ontology/audit designs | English/Korean ADR 0010 and README diagrams: Jangbu, existing Sacho, Sillok, Saheon; Jikji/Hearim remain control-plane integrations |
| Reviewed deployment | Secret scan, strict all-target Clippy, frozen source builds, sandbox check, private rollback snapshots and live verification |

Validation passed: 595 Hangang library tests (13 explicit ignores), 89 admin API,
12 resource-policy and 6 configuration-boundary tests; 8 browser cases. Pumgye
core tests passed. Release-binary native SSO smoke and Pumgye native enforcement /
CAS / streaming-revocation smoke passed. The Pumgye smoke is reproducible with
`python3 tools/hangang_smoke.py --gateway-binary /path/to/hangang` in its repository.

The first activation failed external readiness because the collector environment
reference was not explicitly aligned with the gateway default. Automatic rollback
restored the previous deployment. An explicit credential reference fixed deployment;
subsequent live menu, SSO and HGD1 checks passed. No production account, service grant,
network role or enforcement-mode change was created by activation. Existing Guard
policy remains observe; explicitly protected Pumgye services requiring Guard cannot
accept observe as authorization.

This is a reviewed post-release Linux feature deployment, not a new signed multi-
platform release. The feature's platform CI is tracked separately. Existing signed
release/update identifiers remain compatible. End-to-end 100k HTTP QPS and continuous
provider-session revocation during long streams are not claimed. Long streams are
conservatively retired on any configuration publication. Logging/ontology/audit
runtime integrations remain future work by the user's scoped instruction.
