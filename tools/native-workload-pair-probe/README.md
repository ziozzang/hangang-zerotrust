# Public Workload qualification tools (not production)

This additive crate leaves `../native-workload-probe` and its frozen faa10e binary unchanged. It uses immutable public Hop SDK4ea3e147 and Pum protocolac47d448. It exposes no capability constructor, route mint/export API, permission decision API or production configuration.

## Held authentication binary

`observed-workload-pair-probe <private-config.json>` accepts the original auth probe config and commands `allow`, `deny`, `hold`, `held-refuse` on stdin. `hold` obtains a public SDK observation and stores its exact context/receipt in process memory; `held-refuse` independently observes that same evidence. It emits safe metadata only. Its stored receipt buffer is Zeroizing; other RPC/context/credential copies use ordinary memory. No full memory erasure guarantee is made.

A refusal after a Kubernetes Pod restart may merely reflect the ORIGINAL maximum1second expiry. Output deliberately does not attribute the cause to restart/withdrawal. Fresh authentication is not substituted for held evidence. `allow` checks issue→independentobserve→consumingrefresh→original/currentchecks using the public opaque SDK. Authentication proof is not permission.

## Request-owned pair replay tap

`workload-replay-tap <private-config.json>` terminates authenticated mTLS, forwarding `Authentication.Verify`, Workload IssueObserved/ObserveTime, and Workload contract3 Project to ONE fixed HTTPS Hop peer. Pum/plan observers must still use real Hop directly. Root's Hop peer explicitly points at this qualification-only tap; it is NOT enabled by default anywhere.

Inside Project: forward the original typed request once; after first real Hop success, observe the SAME auth/permit owners, replay the exact same request ID/contract/permission_query bytes, require real Hop `Unavailable`, observe those owners again, and only then return the original first reply unchanged. Root is still awaiting Project and owns its native route Capture throughout. No private route reference is minted or exported. Pre-RPC BOOTTIME anchors and shared SDK rate/quantum conversion bound every owner observation; the original pre-replay lower deadline remains required after subsequent observations. No source renewal or TTL enlargement occurs. Root must charge the whole added RPC delay; this intentionally slow qualification path may fail the original budget and is not a production performance path.

The actual Hop handler flattens replay/source failures to `Unavailable`. Successful before/after owner observations plus an identical refused pair are evidence consistent with paired replay enforcement; the status alone does not identify a particular SQL row. The tool does NOT claim row-specific diagnostics, remote revocation leases, or a fresh original lifetime.

Configuration (reserved examples only; credentials/certificates supplied by owned runner):

```json
{
  "listen":"0.0.0.0:8443",
  "certificate":"/tls/tls.crt","key":"/tls/tls.key","client_ca":"/tls/ca.crt",
  "caller_env":"OWNED_TAP_CALLER",
  "hop":{"address":"https://hop.example.test:8443","server_name":"hop.example.test","ca":"/tls/ca.crt","certificate":"/tls/tls.crt","key":"/tls/tls.key","caller_env":"OWNED_RECEIPT_CALLER"},
  "pum":{"address":"https://pum.example.test:8443","server_name":"pum.example.test","ca":"/tls/ca.crt","certificate":"/tls/tls.crt","key":"/tls/tls.key","caller_env":"OWNED_PUM_CALLER"},
  "hop_source_ppm":500,"pum_source_ppm":500,"receiver_ppm":500
}
```

Admission is1concurrent operation; inbound generated-message limits and outbound limits are fixed. Incoming duplicate/wrong authorization is refused; server mTLS requires the configured client CA; outbound transport rejects non-HTTPS. Upstream messages/secret/header values never enter logs. Secret output is erased on failed qualification where owned by the tap; ordinary transport copies are not guaranteed erased. Added observation RPCs have fixed1second timeouts, but original admission is never renewed by them.

Validation here: unit plus loopback generated typed-RPC peers test exact payload replay (including unknown query fields), caller refusal before upstream calls, unchanged successful first reply, replay-success rejection, and expired-owner suppression. Loopback peer tests are plaintext test fixtures, NOT actual cryptographic/native production qualification. Actual core/TokenReview/Pum compiler/Root dispatch/backend connection gates remain pending final Root0.3.10 artifacts and are parent-owned. No cluster, SSH, release, signing or deployment is performed by these tools.
