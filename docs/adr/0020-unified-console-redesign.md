# ADR 0020: Unified zero-trust console redesign

[한국어](../ko/0020-unified-console-redesign.md)

Status: **Proposed**. Supersedes the per-component menu layout described in
[CONSOLE.md](../CONSOLE.md) and the navigation decision of the
[2026-10-15 admin UI review](../reviews/2026-10-15-admin-ui.md); keeps their trust,
broker, pinning, lifecycle and audit invariants. Depends on
[ADR 0019](0019-decision-events-exporter.md) for decision data.

## Context and quality bar

The target is a **commercial-grade administration product** comparable to the
Cloudflare Zero Trust, Okta, Teleport and Tailscale admin consoles. This ADR states
product requirements, not a minimal console; a page is not done until its
acceptance criteria below pass in EN and KO, light and dark, desktop and 390 px.

A review found the current console unacceptable against that bar:

- Navigation is split per component (Hopae, Sumunjang, Pumgye) instead of per
  operator task; investigating one refused request means three menus.
- Each plugin hand-rolls HTML/JS. Sumunjang translates English text into Korean
  after rendering with a `MutationObserver` dictionary, so unmapped strings leak;
  the host itself keys translations by English sentences.
- Raw JSON `<pre>` dumps, JSON textarea editing and snake_case field names are the
  primary UI; there is no search, filter, sort, pagination or detail page.
- Publishing has no structured diff, no impact preview, no confirmation and no
  reason. Audit is scattered; the host journal (`GET /v1/plugins/audit`) has no UI.
- Subjects appear as opaque hashes (`s_…`, `human1:…`) never resolved to Hopae
  identities; nothing cross-links (user → grants → decisions → network).
- Most importantly there is no cross-component decision log and no what-if policy
  simulator, which every benchmark product provides.

| Capability | Benchmark | Required here |
| --- | --- | --- |
| Access/decision log with per-stage reasons | Cloudflare Access logs, Okta System Log, Teleport audit | Decision log + request timeline (P0) |
| Policy simulation and test before publish | Okta Access Testing Tool, Tailscale ACL tests/preview | What-if panel, impact, CAS publish with reason (P1) |
| Resolved people, not IDs, with entity pages | All four | Entity routes + subject resolution (P0) |
| Unified admin audit with before/after | Okta, Teleport, Cloudflare audit logs | Unified audit (P0) |
| Consistent design system and localisation | All four | Host UI kit + key-based i18n (P0) |

## Decision

Rebuild the console around **operator tasks** with **eight sections**, shared
**entity routes**, a host-provided **UI kit**, **key-based i18n**, and a **plugin
contract v2** where domain packages contribute data providers and views into the
common sections instead of owning standalone pages. Ownership is unchanged: the
console is an interface to authorities, never a second writer (ARCHITECTURE.md).

## Information architecture

| # | Section | Route | Pages | Data owners |
| --- | --- | --- | --- | --- |
| 1 | Overview | `/overview` | Posture, KPIs, alerts, recent changes | All (read) |
| 2 | Access | `/access` | Decision log, request detail, simulator | Exporter (ADR 0019), Hangang explain |
| 3 | Identities | `/identities` | Users, user detail, sessions, providers, authentication profiles, credential projections | Hopae (+ Pumgye grants on detail) |
| 4 | Policies | `/policies` | Services & resources, roles & assignments, information classes, publications | Pumgye, catalog |
| 5 | Network | `/network` | Threat queue, blocks & allowlist, rules, ASN proposals, IP detail | Sumunjang |
| 6 | Devices & Workloads | `/workloads` | Workload principals, service accounts, mTLS identities, device posture (slot) | Hopae, Kubernetes source (ADR 0015) |
| 7 | Audit | `/audit` | Unified administrative audit | Host journal, Hangang accounts, Pumgye, Hopae, Sumunjang |
| 8 | System | `/system` | Components & versions, updates, GeoIP DB, sources & diagnostics, packages, console access, exporter | Host, all (status) |

Hangang routing/listener administration stays in its existing Gateway area beside
these sections; Zero Trust is the default landing area for security operators.

### Shared entity routes

| Route | Entity | Primary owner |
| --- | --- | --- |
| `/identities/users/:id` | Hopae user (stable opaque ID) | Hopae |
| `/identities/sessions/:id` | Hopae session | Hopae |
| `/policies/services/:id` | Pumgye service with resources/roles | Pumgye |
| `/policies/roles/:service/:role` | Role with permissions/classes/AAL | Pumgye |
| `/network/ip/:ip` and `/network/asn/:asn` | Address / ASN | Sumunjang |
| `/access/requests/:request_id` | Request decision timeline | Exporter |
| `/audit/events/:id` | Administrative audit record | Source authority |
| `/system/components/:id` | Component instance | Host |

Every reference rendered anywhere uses the kit's **entity link**: human label first,
opaque ID secondary (monospace, copy button), hover card with owner, status and
freshness. Links are deep-linkable, survive refresh and Back/Forward, and the
destination re-authorizes. **Subject resolution**: the host batches unresolved
subject references per view into a new Hopae `subjects/resolve` operation (≤100 IDs,
read-only, audited as a read) returning display name, principal kind, status and
provider. Unresolvable IDs show *Unknown subject* plus the ID, never a blank. Pseudo
references from ADR 0019 resolve only through `reveal` or forward lookup.

## Page specifications and acceptance criteria

Common page skeleton: breadcrumb, title, owner/description line, primary actions,
**authority strip** (owner, revision, freshness, read-only/unavailable state),
filters, content. Missing, zero, stale, disabled, read-only and unavailable are
visually and textually distinct. Every list: server-side search, filter, sort and
cursor pagination; URL holds the filter state; empty state explains why and what to
do; errors show the owner and a retry. p95 time to first rows ≤1 s on the local
store at 10M retained events; interaction latency ≤100 ms.

### 1. Overview

Elements: authority health cards (Hangang, Hopae, Sumunjang, Pumgye, exporter:
status, revision, last publish, freshness); decision KPIs for 1 h/24 h/7 d
(evaluated requests from metrics, deny rate, challenges, unavailable), top deny
reasons, top denied routes, top source ASNs; open threat queue and ASN proposals
count; recent administrative changes; exporter drops/lag.

Acceptance: every tile links to the pre-filtered list that produced it; numbers
state source and window and label sampled estimates; a failed source renders as
*unavailable* with owner, never as zero; no raw JSON; refresh ≤ every 30 s and
paused when hidden.

### 2. Access

**Decision log** (`/access/decisions`). Filter bar: time range (presets + absolute),
outcome, deciding stage, reason, route/service/resource, user (entity picker), IP or
prefix, ASN, country, principal kind, information class, revision. Columns: time,
outcome badge, user, route/service, deciding stage, reason (localized sentence),
source (ASN/country), revision. Saved views per console account; live tail (poll
≤5 s, bounded); CSV export (≤10k rows, pseudonymous unless revealed, audited).

Acceptance: filters combine and are reflected in the URL; `request_id` pasted in
global search opens the request; denied rows explain the reason in one localized
sentence; suppressed summaries show the count; disabled profile renders *Decision
events disabled* with a link to System; strict profile shows pseudonyms and offers
forward lookup from user detail.

**Request detail** (`/access/requests/:id`). Header: outcome, time, request
reference, route, service/resource/action. Stage timeline (network → identity →
authorization → enforcement) with verdict, reason, matched rules/roles as entity
links, revision and latency per stage; the deciding stage is highlighted with a
*Why* explanation. Revision vector shows *changed since* when current revisions
differ. Actions: *Re-run in simulator* (prefilled), *Open user*, *Open IP*, *Block
source* (opens the Network action with confirmation).

Acceptance: every Pumgye `Decision` variant and Sumunjang/Hopae verdict has a
dedicated localized explanation and remediation hint; stages not reached are shown
as *not evaluated* with the reason; simulation events are visibly marked.

**Simulator** (`/access/simulate`). Inputs: user (or anonymous), principal kind,
target (host + method + path, or service/resource/action), source IP, optional
hypothetical AAL/factors, policy source (published or a draft). Output: the same
stage timeline as request detail, labelled *simulation* with evaluated revisions.

Acceptance: results match enforcement for the same snapshot (contract test per
variant); never creates sessions, permits or changes; every run is audited.

### 3. Identities

**Users** list: search by name/email/ID/provider server-side; filters status,
provider, principal kind, last sign-in; bulk disable with confirmation.
**User detail** (`/identities/users/:id`) tabs: Profile (status, providers, created,
last sign-in, AAL capability), Sessions (active sessions with AAL, factors, ASN,
age; terminate one/all), Access (Pumgye assignments per service with roles,
classes and effective permissions; *Check access* opens the simulator), Recent
decisions (from ADR 0019, filtered to the user), Authentication events (Hopae),
Audit (changes affecting this user). **Sessions**, **Providers**, **Authentication
profiles** (form editor + diff + publish) and **Credential projections** (ADR 0014,
same editor) complete the section.

Acceptance: a user is reachable from any decision, audit record or grant in one
click; disable and terminate require confirmation naming the user and a reason and
show the resulting state; Hopae-native versus Hangang-delegated authority mode is
visible; console accounts are not shown here (see System).

### 4. Policies

**Services & resources** catalog; **Roles & assignments** (who has which role on
which service, editable assignment table); **Information classes**; **Publications**
(history of revisions with actor, reason, diff, rollback as a new publication).
All editors use the **common policy editor**: structured form (no JSON textarea by
default) → validation by the owner → **structured diff** grouped by entity → **what-if**
(simulator cases + impact from ADR 0019 over a chosen window) → **CAS publish**
with base revision and mandatory reason → result with new revision.

Acceptance: a stale base revision yields a conflict view that preserves the draft
and shows the newer change; publish is disabled until validation passes; impact
changing ≥1 outcome or touching `restricted` requires typed confirmation of the
service name; drafts survive navigation, locale switch and refresh (ADM-01).

### 5. Network

**Threat queue** (Sumunjang candidates with evidence, approve/dismiss, bulk);
**Blocks & allowlist** (search, expiry, reason, owner, removal confirmation);
**Rules** (ordered rule table with mode observe/enforce, hit counts, Lua bodies in
the CodeMirror editor, validate before save, CAS revision per ADM-02); **ASN
proposals** (proposed ASN allow/deny with traffic evidence and impact); **IP detail**
(`/network/ip/:ip`: GeoIP/ASN, matching rules, blocks, threat candidates, recent
decisions for that address, actions).

Acceptance: observe-mode rules are visually distinct from enforcing ones; a block
from any page shows target, scope and expiry before confirmation; full-policy
replacement always carries the base revision.

### 6. Devices & Workloads

Workload principals and Kubernetes service-account bindings (ADR 0015), mTLS
identities and their projections, recent workload decisions. Device posture is an
open design (ADR 0005): the page shows *not configured* and never a healthy state.

Acceptance: workload subjects resolve like users; unknown device evidence is never
rendered as trusted.

### 7. Audit

One timeline federated by the host from: console account audit (Hangang), plugin
operation journal (`/v1/plugins/audit`), Pumgye publications (`/v1/audit`), Hopae
administrative events, Sumunjang policy changes (new read operation). Columns: time,
actor (console account and issuer), action, target entity link, outcome
(`committed`, `refused`, `uncertain`), reason, before/after hashes, operation ID.
Detail shows the structured diff when the source retains it.

Acceptance: per-source partial failures are labelled, never shown as no activity;
filters by actor, target, action, source, outcome; `uncertain` outcomes are
highlighted with guidance; no secrets or raw bodies; export is audited.

### 8. System

Components and versions, signed update status/check, GeoIP database, source
freshness and diagnostics, installed packages and manifest pins, console accounts
and roles, exporter and privacy profile status. **Raw JSON is available only here**,
read-only, behind a *View raw* disclosure for diagnostics.

Acceptance: version skew and stale sources are flagged; update actions require
confirmation with version and reason.

## Wireframes

Overview:

```
+--------------------------------------------------------------------------+
| Hangang ▸ Zero Trust ▸ Overview                  [24h ▾]  [⟳ 12s ago]   |
+-----------+-----------+-----------+-----------+-------------------------+
| Hangang ● | Hopae   ● | Sumunjang▲| Pumgye  ● | Exporter ●              |
| rev 268   | gen 5521  | rev 418   | rev 77    | drops 0 · lag 0.4s      |
| fresh 2s  | fresh 1s  | stale 95s | fresh 3s  | profile: standard       |
+-----------+-----------+-----------+-----------+-------------------------+
| Requests 4.2M   Denied 1.8% ▲0.3   Challenged 0.4%   Unavailable 0      |
| [ deny rate sparkline ......................................... ]     |
+-------------------------------+------------------------------------------+
| Top deny reasons              | Top denied routes                        |
| Class denied        1,204  →  | app-api  /api/reports/{id}   812  →      |
| Network denied        933  →  | admin    /console/*          301  →      |
+-------------------------------+------------------------------------------+
| Threat queue: 7 open  →       | Recent changes                           |
| ASN proposals: 2      →       | 09:02 kim  Pumgye rev 77 "add analyst" → |
+-------------------------------+------------------------------------------+
```

Decision log list:

```
+--------------------------------------------------------------------------+
| Access ▸ Decision log                         [Saved views ▾] [Export]   |
| [Last 24h ▾] [Outcome: Deny ×] [Stage ▾] [Service: reports ×] [User ▾]   |
| [Search request ref, user, IP, ASN ...........................] [Live ○] |
+-------+--------+--------------+----------------+-----------+------------+
| Time  | Result | User         | Route          | Stage     | Reason     |
+-------+--------+--------------+----------------+-----------+------------+
| 09:12 | DENY   | Kim Analyst  | reports /api/… | Authz     | Class      |
|       |        | sub~7HC2…    | GET            | Pumgye 77 | restricted |
| 09:11 | DENY   | Unknown      | admin /console | Network   | Blocked    |
|       |        | anonymous    | POST           | Sumun 418 | ASN 64511  |
| 09:10 | ALLOW* | Lee Ops      | app /          | —         | —          |
+-------+--------+--------------+----------------+-----------+------------+
| * sampled allow (1%)                       ‹ Prev   1–50 of ~1,204  Next › |
+--------------------------------------------------------------------------+
```

Request detail timeline:

```
+--------------------------------------------------------------------------+
| Access ▸ Requests ▸ hg-7f3a9c2e41d08b65                [Re-run in sim]   |
| DENY 403 · 2026-10-16 09:12:44 · GET app.example.test /api/reports/{id}  |
| Service reports · resource report · action read                         |
+--------------------------------------------------------------------------+
| ● Network    ALLOW (enforce)  rule asn-allow-corp  rev 418    41 µs      |
|   AS64500 · KR · ip~4MZQ… [Reveal] [Open IP]                            |
| ● Identity   AUTHENTICATED    Kim Analyst (human) via oidc-corp          |
|   AAL1 · federated · session ses~K93T…  gen 5521               183 µs   |
| ✖ Authz      CLASS DENIED     role analyst → class restricted needs AAL2 |
|   Why: role "analyst" lacks class "restricted". Pumgye rev 77    22 µs   |
|   Fix: grant class, or require step-up.  [Open role] [Simulate change]   |
| ○ Enforce    REFUSED          no obligations · fence ok · Hangang 268    |
+--------------------------------------------------------------------------+
| Revisions: hangang 268 · sumunjang 418 · hopae 5521 · pumgye 77 (now 78!)|
+--------------------------------------------------------------------------+
```

User detail:

```
+--------------------------------------------------------------------------+
| Identities ▸ Users ▸ Kim Analyst                [Disable] [End sessions] |
| ● Active · human · oidc-corp · u_example (copy) · last sign-in 08:55     |
| [Profile] [Sessions 2] [Access] [Decisions] [Auth events] [Audit]        |
+--------------------------------------------------------------------------+
| Access (Pumgye rev 77)                               [Check access ▸]    |
| Service   | Roles            | Classes              | Min AAL | Source   |
| reports   | analyst →        | internal             | 1       | Pumgye   |
| billing   | viewer →         | internal             | 1       | K8s (ro) |
+--------------------------------------------------------------------------+
| Recent decisions (24h)                                 [Open in log ▸]   |
| 09:12 DENY  reports GET /api/reports/{id}  Class denied        →         |
| 08:57 ALLOW reports GET /api/reports       —                   →         |
+--------------------------------------------------------------------------+
```

Policy publish diff:

```
+--------------------------------------------------------------------------+
| Policies ▸ reports ▸ Publish                 base rev 77 → new rev 78    |
+--------------------------------------------------------------------------+
| Changes (3)                                                              |
|  Role analyst      + class restricted                                    |
|                    ~ minimum AAL  1 → 2                                  |
|  Assignment        + Lee Ops → role analyst                              |
+--------------------------------------------------------------------------+
| What-if (last 7 days, 1,204 denies + sampled allows)                     |
|  deny → allow   812  e.g. Kim Analyst GET /api/reports/{id}   [view]     |
|  allow → deny    46* e.g. Park Dev (AAL1) GET /api/reports    [view]     |
|  * estimate from 1% sampled allows                                       |
|  Test cases: 5/5 pass                               [Add test case]      |
+--------------------------------------------------------------------------+
| Reason (required): [Grant analysts restricted reports with step-up ....] |
| Type service name to confirm: [reports   ]                               |
|                                      [Cancel]  [Publish revision 78]     |
+--------------------------------------------------------------------------+
```

## Design principles

1. **No raw JSON by default.** Forms, tables and structured diffs; JSON only in
   System diagnostics. Field labels come from message keys, never snake_case.
2. **Destructive or security-reducing actions** (disable, terminate, block, delete,
   publish, mode enforce→observe) confirm with the target's name, the effect, and a
   required reason that is written to audit.
3. **State-appropriate actions only.** Disabled users show *Enable*, not *Disable*;
   read-only sources show why they are read-only instead of disabled buttons.
4. **Explain denials.** Every deny shows which authority decided, why, and a fix.
5. **Truthful state.** Freshness, revision and uncertainty are always visible;
   unknown never renders as healthy, zero or allowed.
6. **People over IDs.** Resolved labels first; IDs secondary and copyable.
7. **Everything links.** Each entity reference is an entity link.
8. **Responsive and accessible.** At 390 px tables become card lists, filters move
   into a sheet, timelines stack; only code editors and diffs scroll horizontally.
   WCAG 2.2 AA: keyboard reachable, visible focus, labelled controls, `aria-live`
   for async results, colour never the sole signal, reduced-motion support.

## Shared UI kit

The host ships a versioned vanilla ES module set, `@hangang/console-ui` (served at
`/ui/kit/1/`, part of the host build and its pinned assets), and passes it to mounts
as `context.ui`; packages never import kit URLs directly, so kit and host versions
cannot skew. Components:

- **DataTable** with server-side search/filter/sort/cursor pagination, column
  chooser, row selection, bulk actions, card layout at 390 px, URL state sync.
- **FilterBar**, time-range picker, saved views.
- **EntityLink** and hover card; **SubjectResolver** batching.
- **StatusBadge**, **FreshnessBadge**, **AuthorityStrip**.
- **Form controls** generated from a field schema with labels/help from message
  keys, validation messages from the owner, and draft persistence (ADM-01).
- **CodeEditor** wrapping the existing CodeMirror build (`web/lua-editor.js`).
- **StructuredDiff** (entity-grouped add/remove/change) and text diff.
- **WhatIfPanel** and **StageTimeline** (shared by request detail and simulator).
- **Charts** (sparkline, time series, bar) following the host token palette.
- **ConfirmDialog** with target name echo, effect summary and required reason.
- **EmptyState**, **ErrorState** (owner + retry), **UncertainOutcome** banner.

All components render untrusted strings as text nodes, respect the host CSP (no
`unsafe-eval`, no inline scripts) and use River theme tokens.

## Internationalisation

- Packages ship message catalogs `messages/en.json` and `messages/ko.json`, keyed
  (`guard.rules.mode.observe`), with ICU-style plural/select parameters. The host
  exposes `context.t(key, params)` and re-renders on locale change via the existing
  `onLocaleChange` contract without losing drafts.
- **Post-hoc DOM translation is banned**: no `MutationObserver` or text-matching
  dictionaries. The host migrates its own English-sentence-keyed dictionaries
  (`web/locales/ko-*.js`) to keys.
- Missing keys fall back to English, are counted, and fail CI. A lint rule rejects
  string literals passed to `textContent`, `innerHTML`, `title`, `placeholder` and
  `aria-*`, and checks that EN and KO catalogs have identical key sets.
- Reason codes (ADR 0019) and field names have registered keys in both languages.

## Plugin contract v2

Plugins become **domain data providers plus views mounted into common sections**.
The trust model is unchanged: operator-reviewed packages, manifest SHA-256 pins,
hashed bounded assets, same-origin `import()` of trusted code (not a sandbox), the
host API broker with an explicit operation allowlist, actor revalidation, service
credentials kept server-side, private mutation audit, session-generation fencing.

Manifest additions (`api_version: 2`):

```json
{
  "id": "guard", "api_version": 2, "kit": "1",
  "messages": {"en": "messages/en.json", "ko": "messages/ko.json"},
  "contributes": {
    "pages": [{"section": "network", "id": "rules", "route": "/network/rules",
               "title": "guard.rules.title", "module": "views/rules.js",
               "operations": ["rules:GET", "rules:PUT", "rules/validate:POST"],
               "permission": "network:write"}],
    "entities": [{"type": "ip", "route": "/network/ip/:ip", "module": "views/ip.js"}],
    "overview_cards": [{"id": "threat-queue", "module": "cards/threats.js"}],
    "decision_stage": {"stage": "network", "module": "stages/network.js"},
    "audit_source": {"operation": "audit/query:POST"},
    "search": {"operation": "search:POST", "types": ["ip", "asn", "rule"]}
  },
  "routes": [{"path": "rules", "method": "GET", "mutation": false}]
}
```

- The host owns the section, route, breadcrumb, title, authority strip and
  permission check; a page module exports `mount(context)` as today, receiving
  `root`, `signal`, `api`, `locale`, `onLocaleChange`, plus `ui`, `t`, `navigate`,
  `link(entity)` and `params`.
- Console permissions become scoped (`decisions:read`, `decisions:reveal`,
  `decisions:trace`, `policy:write`, `network:write`, `identity:write`,
  `audit:read`, `system:admin`), enforced server-side per operation; viewer access
  requires explicit per-operation policy as CONSOLE.md already requires.
- **Migration.** The host loads v1 and v2 packages side by side; a v1 package keeps
  its current single-menu mount under a *Legacy* group with a deprecation notice.
  Guard and Hopae ship v2 packages split into section pages; v1 support is removed
  one minor release after both v2 packages are qualified.
- **Pumgye** moves from embedded host code (`web/pumgye.js`) to a `pumgye` v2 package
  with its own backend binding through the same broker, signature and pinning.

## Phased plan

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| P0 | UI kit, key-based i18n + lint, plugin contract v2 loader, IA shell and entity routes, subject resolution, ADR 0019 D1, Decision log, Request detail, unified Audit, Overview (health + deny KPIs), System | Acceptance criteria for those pages pass in EN/KO, light/dark, desktop/390 px, keyboard-only; zero untranslated literals; no JSON outside System; Playwright suites on real packages with reserved fixture data |
| P1 | Common policy editor with structured diff, simulator, impact and CAS publish with reason for Pumgye, Sumunjang rules and Hopae profiles; Identities and Network pages in v2; Pumgye package | Explain parity tests per `Decision` variant; stale-revision conflict tests; impact estimates labelled; every publish audited with reason and diff |
| P2 | Charts and trends, ASN proposal workflow, saved views, trace sessions, Devices & Workloads, CSV export | Chart accessibility (table alternative), bounded exports audited, workload resolution |

## Alternatives considered

- **Polish each plugin in place.** Rejected: keeps component-shaped navigation and
  no cross-component data; fails the benchmark tasks.
- **Adopt a SPA framework (React/Vue) with a bundler.** Rejected for now: the
  trusted-loader, CSP and pinning model and existing vanilla host favour a vanilla
  ES kit; revisit if the kit proves insufficient.
- **Iframe-isolated plugins.** Rejected: cannot share navigation, entity links or
  kit, and is not a security boundary for same-origin trusted code anyway.
- **Console-side computation of combined allow.** Rejected: decisions come only from
  authority explain APIs.

## Consequences

- Operators work by task with linked entities, explained denials, simulation before
  publication and one audit trail.
- All three packages and the host must be rewritten against the kit and v2 contract;
  this is a substantial multi-release program with UI qualification gates.
- New owner APIs are required: Hopae `subjects/resolve` and authentication explain,
  Pumgye `/v1/explain` and batch explain, Sumunjang candidate lookup and audit query.

## Open questions

1. Console permission model storage and migration from current admin/viewer roles.
2. Whether saved views and per-user preferences belong in the host account store.
3. Multi-tenant scoping of sections and entity routes.
4. Whether the simulator should become an API for CI policy tests (Tailscale-style).
