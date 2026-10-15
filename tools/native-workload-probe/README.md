# Native Workload authentication qualification probe

This management-host tool uses the public Hopae Workload SDK at an immutable Git
revision. It verifies issue, independent observation and consuming refresh through
the fixed authenticated mTLS Workload RPC. It grants no resource permission and
performs no gateway dispatch. Actual native-source execution remains a required
qualification gate; building this tool does not establish it.

Build with `cargo build --locked --manifest-path tools/native-workload-probe/Cargo.toml`.
The generated private configuration supplies fixed endpoint/TLS file references,
issuer/public pin, scope, revision floors, rate assumptions and request binding.
Fixture scope is orders/orders-api and identity authority world1. Credentials are
read only from OWNED_RECEIPT_CALLER and OWNED_RECEIPT_CREDENTIAL; do not put their
values on a command line or in public configuration. Only the Bearer scheme is
accepted; arbitrary authorization/header schemes are rejected.

Run the executable with the private configuration filename. Stdin commands `allow`
and `deny` request expected outcomes. A positive JSON result includes the verified
Workload subject (kind3/AAL0); compare this with the expected bound Kubernetes
identity before publishing grants to the owning Pumgye API. A negative result
means the opaque SDK refused Issue; it does not identify which upstream authority
caused the refusal. Pair it with actual authority and backend-effect evidence.

Unit scheme validation and strict Clippy pass. Real Kubernetes TokenReview,
permission, shared replay ledger and final gateway transport are separate gates.
