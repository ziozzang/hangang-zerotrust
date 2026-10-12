# ADR 0008: bounded HOP1 verification and console delegation

Status: accepted and implemented in Hangang/Hopae PR #1; deployment and platform
qualification are tracked separately. [한국어](../ko/ADR_0008.md)

Choose HOP1 with a 16-byte magic/u64 request-ID/u32 payload-length header,
authenticated ID-zero handshake, strictly increasing positive IDs and bounded
binary header/body blocks. Fixed limits replace proposed message-type flags or
size negotiation in this first version. Hopae re-enters its existing HTTP verify
router; Hangang shares result/identity/cookie/terminal processing between transports.
No decision cache or fallback/retry after native failure is added.

[The native contract](https://github.com/ziozzang/hopae/blob/main/docs/HANGANG_NATIVE.md)
contains exact byte order, bounds, authentication and lifecycle behavior. Current
output preserves existing HTTP outcome/header semantics, including expiry where
present; a full integrated policy/session revision vector is future work.

Trusted console delegation uses a separate issuer/backend key, bounded HMAC actor
assertions, durable nonce replay admission and exact path/body/handle/client-context
binding. Native Hopae handle/grant/assurance/freshness/CSRF and transactional fences
remain authoritative. Browser mode combines Hangang console authority with an
independently valid native Hopae administrator session; it does not auto-grant
accounts or copy their database. Native login/logout providers remain in Hopae.

Alternatives rejected: a reused 24-byte IP frame for identity; duplicating the
provider engine in Hangang; automatic HTTP replay after native failure; trusting
unsigned actor headers; treating a model score or Hangang role as a Hopae grant.

Evidence: real-session HTTP/native parity and reserved-entry tests, codec bounds,
caller injection and ID replay rejection, pool cancellation/reconnect/saturation,
native result-processing tests, real provider-login delegated mutations and grant
revocation, durable nonce tests, actor audit and console lifecycle checks.
Separate services still cannot atomically revoke an already accepted operation.
End-to-end production throughput is not inferred from Guard transport benchmarks.

The later explicit unified authority/SSO mode is described in [ADR 0009](0009-console-authority-sso.md).
