# Repository instructions

This repository is the cross-component design authority. Keep English primary
and update the corresponding Korean document when a design changes. Distinguish
implemented component behavior, prototypes, accepted design, and open decisions.
Never copy deployment tokens, private keys, real users, operational configurations
or host inventories into examples. Use reserved example domains/IP ranges.

Keep user/provider/session ownership in Hopae, network ownership in Guard, routing
and enforcement ownership in Hangang. Do not introduce shared multi-writer business
schemas, client-authoritative classification, or an exporter that can change policy.
Protect ordinary request processing from synchronous analytics writes. Test contracts
and adversarial examples whenever schemas or normative invariants change.
