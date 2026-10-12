# Resource catalog and information classes

[한국어](ko/CATALOG.md) · [Index](README.md)

Status: draft schema 0.1.0. See `schemas/catalog.schema.json` and examples.

## Catalog identity

A resource has a stable opaque `resource_id`, an owning application, and an
owner responsible for its labels. A resource version belongs to an authority
and catalog revision. URL paths are bindings to resources, not their identities.
Changing a backend does not silently change a resource's classification. Renames,
removals and class downgrades require an explicit reviewed change.

Bindings identify Hangang route IDs and explicit actions. Host/path/method
resolution is owned by Hangang, using its canonical protected-namespace rules.
The catalog must not supply competing normalization rules. Overlapping bindings
with conflicting resources or actions fail compilation; traffic cannot choose
which catalog wins by path casing, escaping, duplicate headers or a Lua edit.

## Information classes

Initial vocabulary: `public`, `internal`, `confidential`, `restricted`. These are
sensitivity labels, not a trust score and not automatic access grants. The
vocabulary is versioned. Categories/compartments such as `pii` and `finance`
are independent dimensions; a single ordered rank cannot represent all policy.
A subject's entitlement and tenant relation remain separate from sensitivity.

Each resource definition includes:

- identity, owner and application;
- classification level, compartments and provenance;
- supported actions (`read`, `write`, `export`, etc.);
- tenant mode and object-authorization responsibilities;
- binding references and change review requirements.

The schema deliberately has no client-settable trust override. Request headers,
query parameters, unverified JWT fields and Lua output are untrusted inputs.
The server resolves labels from the active catalog and verified application
context. Missing classification is `unknown`, not `public`. The first compiler
rejects protected bindings without a valid resource definition.

## Action and object boundaries

HTTP method is one binding input, not the action itself: a POST can be a read,
and export may be much more sensitive than interactive viewing. Actions are
explicit per binding. One endpoint may have an action map, but the client cannot
select a weaker action by supplying a body field. Ambiguous action resolution
fails closed.

Static API classification sets a baseline. It cannot establish ownership of
`/documents/{id}`, tenant membership, row ACLs or the contents of a query result.
Applications enforce those rules using authoritative metadata. Avoid centrally
replicating millions of object records just to classify every gateway request.
For resources that require gateway object evidence, define a bounded lookup or
signed application assertion bound to issuer, audience, object, subject, action,
request identifier, validity and policy epoch. This assertion contract is a
future design gate; arbitrary application response headers are not enough.

A multi-class response inherits the strictest applicable constraints and all
relevant compartments. Derived data does not automatically become public.
Downgrading/redaction is an explicit approved transformation with evidence.
Masking obligations have to be supported by the application or an explicitly
configured bounded Hangang transformation; the gateway cannot safely redact an
arbitrary streaming representation by naming an obligation.

## Storage and publication

Start with bounded operator-owned definitions in Hangang's configuration
control plane. The compiler produces route/action indices and immutable labels.
The hot path does not query a catalog SQL database. Publish catalog + policy
references in one bundle under CAS and an authority epoch. Readers validate
schema support, digests, references, downgrade policy and size before activation.

Classification changes have semantic security effects. A reviewed proposal must
show affected routes/actions, new access possibilities and rollback compatibility.
Keep the actor, old/new hashes, justification and approval evidence. A rollback
is a new authoritative revision; never accept stale epoch replay as rollback.

## Open decisions

Who approves downgrades? Which workloads need compartments? How are dynamic
object assertions issued/revoked? Which tenant relationships can Hangang verify,
and which must remain application-only? These questions precede automatic
classification and integrated-engine production rollout.

## Importing API definitions

OpenAPI annotations such as `x-hangang-resource-id`,
`x-hangang-action` and `x-hangang-classification` can seed a catalog proposal.
An importer validates bounded document size, references, paths and extension
types. It does not execute plugins, follow arbitrary external references,
contact credential destinations from `servers`, deploy routes or publish label
downgrades. Ownership and route binding are confirmed before compilation.
Operator-reviewed catalog definitions remain authoritative; imported files are
inputs to the proposal workflow, not a second live policy writer.
