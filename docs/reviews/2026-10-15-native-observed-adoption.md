# Native observed consumer adoption

Status: Sol 6.1 source review and implementation handoff; not implemented consumer
behavior. Current source: Hopae `2a96303`, Pumgye `34d74b6`, Hangang `b41b492`.
[한국어](../ko/2026-10-15-native-observed-adoption.md)

## Next code boundary

The exact-pin SDK is a tested foundation, but neither production consumer can
use it directly. Pumgye receives an authenticated final-request digest, not HTTP
method/path/body bytes. Hangang already hashes its materialized final entity once.
Both handle dynamic verified service identities, while the exact client pins a
subject, profile/application generation and random source-process domain.
Creating a client from incoming context per request would promote input into trust
and discard connection reuse and lifecycle ownership.

Add a distinct server-compiled stable service trust policy and digest preparation
API while preserving exact mode. The persistent native client owns issuer/key/base
identity, allowed service/audience, revision floors, TLS endpoint, rates and its
private lifecycle seal. An issue intent binds the native final digest and headers.
An observation query freezes the supplied context only after structural/policy
checks and equality with the authenticated enforcement caller's expected digest.
Preparation grants nothing. Signature verification and the current fixed-owner
RPC must both succeed before creating private time evidence; reuse verified
immutable evidence rather than verifying it again in Pumgye.

## Process domains and local ownership

Operators configure stable trust, not random process domains. For a new operation,
learn the domain from the signed context and require the authenticated current-owner
report to match it exactly. New-process proofs can then work without configuration
edits; the owner refuses old-process proofs. Refresh never migrates a proof between
domains. This does not solve endpoint discovery or arbitrary replica balancing.
Do not infer replay-record deletion authority from seeing a new domain or refusal.

Use native owner/configuration-scoped registry floors; a single profile counter
must not conflate unrelated service identities. Capture one immutable trust/client
generation across awaits, retire it before replacement and recheck its active Arc
identity immediately before native authorization/signing/output. Point-in-time
observations remain distinct from revocation leases.

## Ordered implementation and acceptance

1. Add stable-policy/digest SDK support. Test multiple signed subjects and domains
   on one persistent client, fixed trust/scope/floor refusals, restart without
   operator edits, nonmigrating refresh, fresh IDs and retirement/cancellation.
2. Add a separate Pumgye observed authentication wrapper. It consumes verified
   identity and local time evidence without fake UTC or conversion to the old
   strict checked type. Keep permit issuance disabled for this branch initially.
3. Move prerequisites into Pumgye's local receiver domain, intersect remaining
   budgets, then sign permits in Pumgye's separate progressing source domain.
   Authentication lineage is not a permit clock. Add observed permit envelopes.
4. Change Hopae paired durable replay and final output together. Preserve atomic
   nonce reservation, registry checks, secret resolution, final fences and commit.
   Version strict/observed rows; clean observed records by receiver retention,
   never source expiry or receiver wall time. Define receiver restart explicitly.
5. Add observed output envelopes and Hangang conversion/final dispatch fences.
   Authentication, permit, output and receiver clocks remain distinct. Qualify
   independent offsets, asymmetric delays, suspend, races, cancellation, lost
   replies, restart/restore and actual final backend effects.

These stages precede signed rebuild, actual four-Pod Kubernetes/browser and
operating adoption. Existing strict paths remain separate throughout migration.
