# Device and workload evidence: open design

[한국어](ko/DEVICES.md) · [Index](README.md)

Status: intentionally unresolved. User requested further consideration; do not
silently add mandatory endpoint agents or fabricate compliant-device evidence.

## Separate identities

A user session is not a device identity. An IP address is not a managed device.
A workload certificate is not proof that a human user's device is healthy.
Treat device posture, workload identity, user identity and network risk as
independent facts from explicitly configured authorities.

Hangang has existing workload/mTLS-related primitives that can be reused after
compatibility review. A certificate proves possession of an accepted key and
identity binding under its issuer; it does not attest arbitrary hardware state,
patch level or uncompromised execution. Extend claims only with defined evidence.

## Candidate approaches

| Approach | Useful evidence | Questions |
| --- | --- | --- |
| Existing managed-device/MDM source | Enrollment, OS/security state | Freshness, BYOD coverage, privacy and offline behavior |
| Endpoint agent | Local posture measurements | Trust/attestation, signing, tamper resistance, update/maintenance |
| Workload issuer / mTLS identities | Service/instance identity | Trust domains, issuance, key rotation and revocation |
| Browser-bound key/session evidence | Limited device/session binding | Recovery, portability, phishing/resession semantics |

Decide supported environments and assurance requirements before choosing a new
service. Adapters may integrate existing sources rather than creating a duplicate
inventory/CA. Privacy-sensitive device identifiers need an explicit lifecycle.

## Minimum future contract

Issuer, audience, subject/device/workload binding, attestation kind, facts,
issued/expiry times, authority epoch, signature/verification method and revocation
reference. Restrict allowed claims per issuer. Define unknown/stale/conflicting
states and whether any claim can survive disconnected operation.

Policies that require verified posture deny when that evidence is unavailable.
Policies that do not require it can still operate on their declared facts.
Never convert "no agent installed" into "healthy" or elevate a cookie/header to
attested evidence. The draft catalog/policy does not yet define posture grants.

Open questions: human versus machine identity relations; tenant separation;
issuer federation; hardware-backed credentials; re-evaluation of live streams;
privacy/retention; offline operation; revocation propagation; operational costs;
and protocol/latency budgets. Resolve through an ADR and adversarial fixtures.
