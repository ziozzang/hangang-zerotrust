# Offline Hop state preparation and schema10 rollback

`tools/hopae_state_rollout.py` prepares private offline evidence and separate state
copies. It does not stop Docker/systemd, deploy a binary, replace a mount, or
activate Human authentication. The operator must stop the sole Hop owner and
exclude concurrent provider/admin CLI maintenance first. Linux `flock` on the
existing `state_dir/hopae.lock` matches Hop's actual instance lock. A free lock
is a local coordination observation, not distributed fencing or clone protection.

Hop uses `state_dir/hopae.db` unless `store.path` selects another file inside the
configured state directory. The tool maps that relative path to the supplied host
volume. External databases, symlinks, hard links, special files, oversized files
(over1GiB), and inventories over10000 entries refuse. Every state file is copied;
SQLite databases use the backup API including committed WAL content and integrity
checks, producing standalone DELETE-journal copies. Original DB/WAL and all other
file hashes, sizes, inode/device/ownership/modes are checked again before success.
SQLite SHM reader marks can change due to the backup itself: their content is not
business data and is excluded from source hashing; their metadata remains checked.
SHM/WAL files are not substituted for a standalone database backup. Empty state
directories are retained. Backup file hashes are portable across inode changes.

## Preparation

These are command templates, not commands already executed against operations.
Use fresh private output paths outside the source volume. Do not print the
configuration, environment files, receipts, keys, or private logs.

```sh
umask 077
python3 tools/hopae_state_rollout.py prepare \
  --state-dir /private/host-volume/state \
  --config /private/hopae.json \
  --private-file /private/service.env \
  --private-file /private/external-tls-key.pem \
  --output /private/backup-before-0011
```

All state contents and the exact configuration are captured. `--private-file` is
repeatable: explicitly enumerate ALL external companion files required to recover
TLS, TOTP encryption, session/receipt signing, dedicated Human material keys and
caller identities. Environment values are never automatically captured or emitted.
The manifest privately maps numbered companion copies to original paths. A secret
manager recovery procedure is still required for keys not stored in files. The
operator must verify this inventory before migration; the tool cannot infer all
indirect environment/file references. Outputs are0700 directories/0600 files.
Stdout contains only operation/success or a fixed refusal code; failed preparation
removes its own newly-created partial output and never overwrites an existing path.

The bundle is not cryptographically authenticated against a privileged administrator
rewriting both manifest and files. Preserve its digest/off-host copy through the
existing trusted backup mechanism. Storage must support SQLite and local advisory
locks; arbitrary network filesystem semantics are not qualified.

## Offline candidate qualification

```sh
python3 tools/hopae_state_rollout.py shadow \
  --backup /private/backup-before-0011 \
  --candidate /private/exact-frozen-hopae \
  --sha256 EXACT_64_LOWER_HEX_BINARY_SHA \
  --output /private/shadow-0011
```

Requires Linux `unshare --user --map-root-user --net` support; failure refuses.
The exact hashed candidate runs fixed `--config <private-shadow-config> --check`
and `--config <private-shadow-config> providers import`, each with a60s timeout,
in separate new network namespaces without external networking. No arbitrary
command, shell, server startup, or production listener is supported. State and
store paths are rewritten to the separate clone; the original bundle stays intact.
Provide the required approved service environment by inheritance, without logging
its values. Other config references remain unchanged; explicit companion copies are
recovery material, not automatic remapping of arbitrary configuration paths.

The actual Hop provider-import CLI uses `Store::open`, performs real migration and
preserves DB-authoritative provider import semantics. This may update the SHADOW
provider rows; it is not a read-only command. Success requires schema_migrations
MAX(version)==10 and integrity checks. Its private0600 logs can contain provider
identifiers and must not be published. This proves offline configuration checking
and actual store migration only. It does not compile all serving Registry owners,
resolve all Human material successfully, test native login, or prove service health.
A separate isolated serving/authentication/artifact gate is mandatory before rollout.

## Stateful rollback preparation

An older binary must never open schema10. Stop the new owner and exclude CLI
writers. The parent deployment supervisor must retain a stopped-state seal at its
agreed reversible boundary BEFORE admitting new traffic/mutations:

```sh
python3 tools/hopae_state_rollout.py seal \
  --state-dir /private/host-volume/state --output /private/stopped-state-seal.json
python3 tools/hopae_state_rollout.py restore \
  --backup /private/backup-before-0011 \
  --current-state-dir /private/host-volume/state \
  --current-seal /private/stopped-state-seal.json \
  --output /private/prepared-old-state
```

Restore verifies the current stopped owner lock and EXACT seal inventory before
and after preparing a separate old-state/config/companion-file directory. It never
overwrites the current state/config or launches the old binary. Changed data,
new sessions/revocations, a live owner, tampered backup, or an existing destination
refuses. A newly-generated seal is not evidence that no prior post-migration writes
occurred: the deployment supervisor must preserve the correct earlier seal and
reconcile intervening mutations. Do not reseal to bypass a refusal. Restoring an old
backup after accepted new writes loses those writes and requires an explicit safe
operational reconciliation; it is not an automatic fallback.

The remaining reviewed Docker stop/mount cutover, original UID/GID/modes, external
companion-file restoration and old-image startup belong to the deployment helper.
Keep the migrated directory quarantined, restore the complete old state and exact
matching config/keys as one operational unit, and start exactly one owner. Verify
the old binary/config and ordinary authentication after cutover. Do not merge DBs,
copy only a realm, delete tombstones/replay rows, or run backup clones concurrently.
Arbitrary live VM/DB clones and rollback tampering need external fencing and are
unsupported by this local helper.

## Verification evidence

```sh
python3 -m unittest discover -s tools -p test_hopae_state_rollout.py
HOPAE_ROLLOUT_OLD_BINARY=/private/exact-old-hopae \
HOPAE_ROLLOUT_CANDIDATE=/private/exact-new-hopae \
python3 -m unittest discover -s tools -p test_hopae_state_rollout.py
```

The optional native case copies the old immutable binary into a fresh fixture,
creates a real old-schema store, migrates only a shadow with the actual candidate
in a new network namespace, checks schema10 and prepares old-schema restoration.
Without both explicit binary paths it skips clearly. SQLite fixtures separately
cover WAL, live-process locks, source changes, destination/tamper/link refusal,
private permissions, portable bundle hashes, sealed-current rollback and redacted
CLI errors. Mocked candidate tests validate invocation/failure handling only;
they do not substitute for actual native migration or serving gates.

SQLite backup checks a10s monotonic deadline between128-page steps, with100ms busy timeout and50ms busy polling. Busy writer refusal is separately tested; this does not authorize concurrent CLI maintenance.

## Exact isolation and final cutover boundary

User/network namespaces do not isolate the filesystem. Only the fixed trusted Hop
CLI is executed, with the clone's explicit state/store paths; other trusted config
references still address the host filesystem. This is not a sandbox for an arbitrary
candidate binary. Verify the candidate's signed provenance first. `--private-file`
arguments must be absolute canonical paths (relative paths refuse); source/config
CLI paths are made absolute and symlinks anywhere in their path refuse.

The configuration's container `state_dir` is intentionally NOT required to equal
`--state-dir`: the latter is the explicitly supplied host backing volume. Only the
configured DB path relative to the configured state directory is transplanted.
The operator must verify this host-volume/container mapping from actual mounts;
the helper does not discover Docker mounts.

The stopped-state seal covers ONLY current state-directory contents. It does not
seal the current external configuration, external key/CA/env files, image, compose
or runtime environment. The backup separately captures original config and explicit
companion files, but the final operational supervisor MUST bind and recheck those
live external inputs and the mount/image/UID mapping against its own reviewed
cutover receipt. A valid state seal alone never authorizes applying old external
files or starting an old binary. This helper intentionally prepares a separate
restore directory while that complete cutover guard remains an operations gate.
