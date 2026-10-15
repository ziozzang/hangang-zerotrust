# Native preliminary authentication timing follow-up

Status: Sol source review and proposed work, not implemented or physically qualified.
Astra remains stopped. This is separate from the preliminary/final identity-lineage
fix and does not expand its acceptance claims.

The generic native Verify path currently derives its fixed machine deadline from
`std::time::Instant`; renewable machine streams retain the same clock family.
Linux suspend can stop that clock. The final observed SDK chain separately uses
BOOTTIME and still fences backend dispatch; no bypass of that final gate was
established. Earlier no-Lua assertions apply to wrong kind, wrong AAL and a refused
preliminary permission query. They do not prove pre-Lua authentication expiry
through suspend, nor reversal of Lua effects after a later identity mismatch.

Required follow-up:

- Audit each producer of the TTL response: remaining original evidence versus a
  trusted legacy local cap. A missing TTL is not signed source freshness.
- Capture suspend-aware receiver time before the original Verify RPC. Apply the
  actual producer/receiver rate and quantum bounds; include all queue/transport
  time. Never compare absolute clocks from independent hosts or silently relabel
  the legacy TTL as an observed receipt.
- For renewal, require the previous deadline to remain live before and after the
  await and immediately before publishing a replacement. A new successful reply
  must never revive an expired previous stream. Clock failure retires authority.
- Use a private deterministic clock seam to test suspend, original RPC delay,
  source pause, expiry during renewal and failure before Lua/stream effects.
  Preserve platform support boundaries and identify physical tests separately.

This work does not implicitly authorize pooled observed transport, change source
proof durations, or establish VM clone/rollback safety. Exact APIs and default
legacy compatibility must be reviewed before implementation.
