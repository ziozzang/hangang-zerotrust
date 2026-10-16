# Unified Hangang console and trusted plugins

[한국어](ko/CONSOLE.md) · [Index](README.md)

Status: Guard import/registry prototype; production integration and Hopae
management delegation require qualification. Merely routing a hostname to the
old console does not install a plugin or create a menu entry.

Redesign: [ADR 0020](adr/0020-unified-console-redesign.md) (proposed) replaces the
per-component menus with task-oriented sections, entity routes, a host UI kit,
key-based i18n and plugin contract v2, keeping the trust/broker/pinning model
below. Decision log and simulator data come from [ADR 0019](adr/0019-decision-events-exporter.md).

## User-facing contract

Guard and Hopae appear as native sidebar entries/submenus in Hangang. The console
uses one shell, navigation, theme and language system. Signing in again inside a
plugin is not the intended workflow. A plugin keeps its own domain views, not a
second complete management shell in an iframe.

The installed package has a manifest, module entry, bounded assets, hashes and
an explicit API operation list. Hangang serves verified immutable copies under
`/ui/plugins/<id>/...`; the host imports the same-origin entry with `import()`.
The module receives a root element, a constrained API broker, locale, cancellation
signal and lifecycle callbacks. No backend URL, service token or raw management
session is intentionally passed as context data.

## Trust and lifecycle

Imported same-origin JavaScript is trusted console code with console privileges;
an API broker is not a JavaScript sandbox. Packages require operator-reviewed
installation and a pinned manifest digest. Pin each asset, reject path traversal,
symlinks/unsafe files, cap sizes, and snapshot assets at startup. Arbitrary remote
JavaScript URLs and trust-on-first-use are out of scope. Future automatic package
updates require independent signing and compatibility rules.

Discover menus only after authentication. Mount when opened; pause pollers on
navigation; preserve drafts when returning; abort requests and dispose the view
on logout/role loss. Every async result is bound to a session generation. An old
import/error callback cannot remove or repaint a newer session's view. Limit DOM
rows, API replies, poll frequency and live subscriptions. Render untrusted strings
with text nodes. Preserve the host CSP without unsafe-eval or arbitrary inline code.

## Management API

The browser calls `/v1/plugins/<id>/<operation>`. The host authenticates the actor,
authorizes the registered operation, rejects unregistered methods/paths, bounds
body/time/concurrency and forwards only the configured service credential to the
fixed backend. Client forwarding/identity headers are stripped. Role checks are
server-side; disabled buttons are not authorization.

Initial Guard prototype is administrator-only. Viewer/fine-grained plugin grants
need an explicit operation policy, including read-like POSTs such as inspection.
Do not classify writes simply by GET versus POST. Collector/query endpoints are
not exposed through an admin plugin route by default.

Native embedding in Hangang can reuse its account authority directly. A bounded
console adapter can serve new assets/plugins over an existing Hangang admin API
and revalidate actors through its native identity endpoint; this avoids restarting
the data-plane process and avoids a duplicate account database. General Hangang
API calls still reach the original native authority. Both paths need end-to-end
role/revocation tests; the adapter is a separate managed runtime, not a new user
source of truth.

## Operator assurance and break-glass

Console operators authenticate through Hopae with a passkey (or AAL 3), proven to
the console by Hopae's signed operator assertion and refreshed for sensitive
changes; the header shows the operator's level and factor; the local administrator
sign-in is an audited, disableable break-glass path. See
[IDENTITY](IDENTITY.md#console-operator-assurance).

## Audit and pending Hopae work

Write intent and outcome records bind actual actor, plugin, operation and body
hash. Never journal raw passwords, sessions, cookie values or provider tokens.
An uncertain remote mutation is not automatically retried. Host journaling does
not replace domain audit in Hopae/Guard. Restricted delegation should carry
issuer/audience/actor/action and request binding, with explicit revocation behavior.

Hopae currently enforces console handles, grants and CSRF; a generic Guard bearer
adapter must not silently bypass this. Design a scoped delegated-management
endpoint/provider in Hopae, then build native user/session/event views against it.
