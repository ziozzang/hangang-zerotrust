//! Qualification-only relay: no mint API, no production capability constructors.
use base64::{Engine as _, engine::general_purpose::STANDARD};
use hopae_grpc::v1 as h;
use prost::Message as _;
use pumgye_grpc::v1 as p;
use serde::Deserialize;
use sha2::{Digest as _, Sha256};
use std::{
    io::Read as _,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::sync::Semaphore;
use tonic::{
    Request, Response, Status,
    transport::{
        Certificate, Channel, ClientTlsConfig, Endpoint, Identity, Server, ServerTlsConfig,
    },
};
use zeroize::Zeroize as _;
// Diagnostic counters are not proof or request identifiers. Output is capped for
// this owned qualification process; payloads and Status messages never enter it.
static VERIFY_INGRESS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static VERIFY_ADMITTED: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static VERIFY_UPSTREAM: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static VERIFY_CANCELLED: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static VERIFY_LOGS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
fn increment(counter: &std::sync::atomic::AtomicU64) -> u64 {
    counter
        .fetch_update(
            std::sync::atomic::Ordering::Relaxed,
            std::sync::atomic::Ordering::Relaxed,
            |value| Some(value.saturating_add(1)),
        )
        .expect("infallible saturating counter")
}
struct VerifyDiagnostic {
    begun: Instant,
    stage: &'static str,
    code: &'static str,
    reply: &'static str,
    completed: bool,
}
impl VerifyDiagnostic {
    fn ingress() -> Self {
        increment(&VERIFY_INGRESS);
        Self {
            begun: Instant::now(),
            stage: "ingress",
            code: "cancelled",
            reply: "none",
            completed: false,
        }
    }
    fn admitted(&mut self) {
        increment(&VERIFY_ADMITTED);
        self.stage = "upstream_pending";
    }
    fn admission_refused(&mut self, code: tonic::Code) {
        self.stage = "admission_refused";
        self.code = code_name(code);
        self.completed = true;
    }
    fn upstream(&mut self, result: &Result<Response<h::VerifyReply>, Status>) {
        increment(&VERIFY_UPSTREAM);
        self.stage = "upstream_completed";
        self.code = result
            .as_ref()
            .map_or_else(|e| code_name(e.code()), |_| "ok");
        self.reply = result
            .as_ref()
            .map_or("none", |r| reply_status(r.get_ref().status));
        self.completed = true;
    }
    fn facts(&self) -> serde_json::Value {
        use std::sync::atomic::Ordering::Relaxed;
        serde_json::json!({"event":"workload_verify_stage", "stage":self.stage,
            "tonic_code":self.code, "reply_status":self.reply,
            "elapsed_ms":self.begun.elapsed().as_millis().min(60_000) as u64,
            "ingress_count":VERIFY_INGRESS.load(Relaxed),"admitted_count":VERIFY_ADMITTED.load(Relaxed),
            "upstream_completed_count":VERIFY_UPSTREAM.load(Relaxed),"cancelled_count":VERIFY_CANCELLED.load(Relaxed)})
    }
}
impl Drop for VerifyDiagnostic {
    fn drop(&mut self) {
        if !self.completed {
            increment(&VERIFY_CANCELLED);
        }
        if increment(&VERIFY_LOGS) < 4096 {
            write_diagnostic(&mut std::io::stdout().lock(), &self.facts());
        }
    }
}
fn write_diagnostic(writer: &mut impl std::io::Write, facts: &serde_json::Value) {
    if let Ok(mut bytes) = serde_json::to_vec(facts)
        && bytes.len() < 4096
    {
        bytes.push(b'\n');
        // Drop must not panic or alter the RPC result when stdout is closed.
        let _ = writer.write_all(&bytes);
    }
}
fn reply_status(status: u32) -> &'static str {
    match status {
        200 => "200",
        400 => "400",
        401 => "401",
        403 => "403",
        429 => "429",
        503 => "503",
        _ => "other",
    }
}
fn code_name(code: tonic::Code) -> &'static str {
    match code {
        tonic::Code::Ok => "ok",
        tonic::Code::Cancelled => "cancelled",
        tonic::Code::Unknown => "unknown",
        tonic::Code::InvalidArgument => "invalid_argument",
        tonic::Code::DeadlineExceeded => "deadline_exceeded",
        tonic::Code::NotFound => "not_found",
        tonic::Code::AlreadyExists => "already_exists",
        tonic::Code::PermissionDenied => "permission_denied",
        tonic::Code::ResourceExhausted => "resource_exhausted",
        tonic::Code::FailedPrecondition => "failed_precondition",
        tonic::Code::Aborted => "aborted",
        tonic::Code::OutOfRange => "out_of_range",
        tonic::Code::Unimplemented => "unimplemented",
        tonic::Code::Internal => "internal",
        tonic::Code::Unavailable => "unavailable",
        tonic::Code::DataLoss => "data_loss",
        tonic::Code::Unauthenticated => "unauthenticated",
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Peer {
    address: String,
    server_name: String,
    ca: String,
    certificate: String,
    key: String,
    caller_env: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    listen: std::net::SocketAddr,
    certificate: String,
    key: String,
    client_ca: String,
    caller_env: String,
    hop: Peer,
    pum: Peer,
    hop_source_ppm: u32,
    pum_source_ppm: u32,
    receiver_ppm: u32,
}
#[derive(Clone)]
struct Tap {
    hop: Channel,
    pum: Channel,
    incoming: [u8; 32],
    hop_caller: tonic::metadata::MetadataValue<tonic::metadata::Ascii>,
    pum_caller: tonic::metadata::MetadataValue<tonic::metadata::Ascii>,
    capacity: Arc<Semaphore>,
    clock: Arc<hangang_runtime::time::ReceiverClock>,
    hop_rates: Arc<hopae_grpc::receipt_time::ClockRates>,
    pum_rates: Arc<hopae_grpc::receipt_time::ClockRates>,
}
fn file(path: &str) -> Result<Vec<u8>, &'static str> {
    let m = std::fs::metadata(path).map_err(|_| "file")?;
    if !m.is_file() || m.len() > 131072 {
        return Err("file_bounds");
    };
    std::fs::read(path).map_err(|_| "file")
}
fn caller(
    env: &str,
) -> Result<tonic::metadata::MetadataValue<tonic::metadata::Ascii>, &'static str> {
    let value = std::env::var(env).map_err(|_| "caller_environment")?;
    if value.is_empty() || value.len() > 4096 || !value.bytes().all(|b| b.is_ascii_graphic()) {
        return Err("caller_shape");
    }
    format!("Bearer {value}")
        .parse()
        .map_err(|_| "caller_shape")
}

async fn connect(p: &Peer) -> Result<Channel, &'static str> {
    if !p.address.starts_with("https://") {
        return Err("https_required");
    };
    Endpoint::from_shared(p.address.clone())
        .map_err(|_| "endpoint")?
        .tls_config(
            ClientTlsConfig::new()
                .domain_name(&p.server_name)
                .ca_certificate(Certificate::from_pem(file(&p.ca)?))
                .identity(Identity::from_pem(file(&p.certificate)?, file(&p.key)?)),
        )
        .map_err(|_| "tls")?
        .connect_timeout(Duration::from_secs(1))
        .timeout(Duration::from_secs(1))
        .connect()
        .await
        .map_err(|_| "connect")
}
fn request<T>(
    value: T,
    caller: &tonic::metadata::MetadataValue<tonic::metadata::Ascii>,
) -> Request<T> {
    let mut r = Request::new(value);
    r.set_timeout(Duration::from_secs(1));
    r.metadata_mut().insert("authorization", caller.clone());
    r
}
impl Tap {
    fn admit<T>(&self, r: &Request<T>) -> Result<tokio::sync::OwnedSemaphorePermit, Status> {
        let mut values = r.metadata().get_all("authorization").iter();
        let valid = values
            .next()
            .is_some_and(|v| <[u8; 32]>::from(Sha256::digest(v.as_bytes())) == self.incoming)
            && values.next().is_none();
        if !valid {
            return Err(Status::unauthenticated("fixture caller required"));
        }
        self.capacity
            .clone()
            .try_acquire_owned()
            .map_err(|_| Status::resource_exhausted("fixture capacity"))
    }
    async fn owners(&self, q: &p::PermitValidationRequest) -> Result<u64, Status> {
        let auth = q
            .request
            .as_ref()
            .ok_or_else(|| Status::invalid_argument("auth absent"))?;
        let permit = q
            .permit
            .as_ref()
            .ok_or_else(|| Status::invalid_argument("permit absent"))?;
        let context = auth
            .context
            .as_ref()
            .ok_or_else(|| Status::invalid_argument("context absent"))?;
        if context
            .identity
            .as_ref()
            .is_none_or(|i| i.kind != 3 || i.aal != 0)
        {
            return Err(Status::invalid_argument("workload required"));
        }
        let before = self
            .clock
            .begin_exchange()
            .map_err(|_| Status::unavailable("receiver clock"))?;
        let a =
            h::workload_authentication_receipts_client::WorkloadAuthenticationReceiptsClient::new(
                self.hop.clone(),
            )
            .max_decoding_message_size(4096)
            .observe_time(request(
                h::WorkloadReceiptObservationRequest {
                    request_id: q.request_id,
                    context: Some(context.clone()),
                    receipt: auth.receipt.clone(),
                    request_sha256: auth.request_sha256.clone(),
                },
                &self.hop_caller,
            ))
            .await?
            .into_inner();
        let sample = self
            .clock
            .finish_exchange(before)
            .map_err(|_| Status::unavailable("receiver clock"))?;
        let auth_until = self.lower(a.remaining_ms, &sample, &self.hop_rates)?;
        if a.request_id != q.request_id
            || a.remaining_ms == 0
            || a.remaining_ms > 1000
            || a.cache_ttl_ms != 0
            || a.receipt_sha256 != Sha256::digest(&auth.receipt).as_slice()
        {
            return Err(Status::unavailable("auth owner not current"));
        }
        let before = self
            .clock
            .begin_exchange()
            .map_err(|_| Status::unavailable("receiver clock"))?;
        let b=p::workload_observed_projection_permits_client::WorkloadObservedProjectionPermitsClient::new(self.pum.clone()).max_decoding_message_size(4096)
   .observe(request(q.clone(),&self.pum_caller)).await?.into_inner();
        let sample = self
            .clock
            .finish_exchange(before)
            .map_err(|_| Status::unavailable("receiver clock"))?;
        let permit_until = self.lower(b.remaining_ms, &sample, &self.pum_rates)?;
        let binding = permit
            .binding
            .as_ref()
            .ok_or_else(|| Status::invalid_argument("binding absent"))?;
        if b.request_id != q.request_id
            || b.remaining_ms == 0
            || b.remaining_ms > 1000
            || b.cache_ttl_ms != 0
            || b.receipt_sha256 != Sha256::digest(&permit.receipt).as_slice()
            || b.clock_domain != binding.authority_epoch
            || b.policy_revision != binding.policy_revision
            || b.network_revision != binding.network_revision
            || b.route_revision != binding.route_revision
            || b.plan_revision != binding.plan_revision
        {
            return Err(Status::unavailable("permit owner not current"));
        }
        let until = auth_until.min(permit_until);
        self.current(until)?;
        Ok(until)
    }
    fn current(&self, until: u64) -> Result<(), Status> {
        if self
            .clock
            .sample_ticks()
            .map_err(|_| Status::unavailable("receiver clock"))?
            >= until
        {
            return Err(Status::unavailable("original observation budget expired"));
        };
        Ok(())
    }
    fn lower(
        &self,
        remaining: u32,
        sample: &hangang_runtime::time::ExchangeSample,
        rates: &hopae_grpc::receipt_time::ClockRates,
    ) -> Result<u64, Status> {
        rates
            .remaining_admission_until(
                remaining,
                &hopae_grpc::receipt_time::Exchange {
                    before_ms: sample.before_ticks(),
                    after_ms: sample.after_ticks(),
                    elapsed_ms: sample.elapsed_ms(),
                },
            )
            .map_err(|_| Status::unavailable("observation budget"))
    }
}
#[tonic::async_trait]
impl h::authentication_server::Authentication for Tap {
    async fn verify(
        &self,
        r: Request<h::VerifyRequest>,
    ) -> Result<Response<h::VerifyReply>, Status> {
        let mut diagnostic = VerifyDiagnostic::ingress();
        let _permit = match self.admit(&r) {
            Ok(permit) => permit,
            Err(error) => {
                diagnostic.admission_refused(error.code());
                return Err(error);
            }
        };
        diagnostic.admitted();
        let result = h::authentication_client::AuthenticationClient::new(self.hop.clone())
            .max_encoding_message_size(16384)
            .max_decoding_message_size(8192)
            .verify(request(r.into_inner(), &self.hop_caller))
            .await;
        diagnostic.upstream(&result);
        result
    }
}
#[tonic::async_trait]
impl h::workload_authentication_receipts_server::WorkloadAuthenticationReceipts for Tap {
    async fn issue_observed(
        &self,
        r: Request<h::WorkloadReceiptRequest>,
    ) -> Result<Response<h::WorkloadReceiptObservedReply>, Status> {
        let _permit = self.admit(&r)?;
        h::workload_authentication_receipts_client::WorkloadAuthenticationReceiptsClient::new(
            self.hop.clone(),
        )
        .max_encoding_message_size(16384)
        .max_decoding_message_size(8192)
        .issue_observed(request(r.into_inner(), &self.hop_caller))
        .await
    }
    async fn observe_time(
        &self,
        r: Request<h::WorkloadReceiptObservationRequest>,
    ) -> Result<Response<h::WorkloadReceiptTimeReply>, Status> {
        let _permit = self.admit(&r)?;
        h::workload_authentication_receipts_client::WorkloadAuthenticationReceiptsClient::new(
            self.hop.clone(),
        )
        .max_encoding_message_size(8192)
        .max_decoding_message_size(4096)
        .observe_time(request(r.into_inner(), &self.hop_caller))
        .await
    }
}
fn checked_pair(r: &h::ProjectionRequest) -> Result<p::PermitValidationRequest, Status> {
    if r.permission_contract != 3 || r.request_id == 0 || r.permission_query.len() > 8192 {
        return Err(Status::invalid_argument("contract3 bounds"));
    };
    let q = p::PermitValidationRequest::decode(r.permission_query.as_slice())
        .map_err(|_| Status::invalid_argument("pair encoding"))?;
    if q.request_id != r.request_id {
        return Err(Status::invalid_argument("correlation"));
    };
    Ok(q)
}
#[tonic::async_trait]
impl h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjection
    for Tap
{
    async fn project(
        &self,
        r: Request<h::ProjectionRequest>,
    ) -> Result<Response<h::ObservedProjectionReply>, Status> {
        let _permit = self.admit(&r)?;
        let begun = Instant::now();
        let original = r.into_inner();
        let q = checked_pair(&original)?;
        let hash: [u8; 32] = Sha256::digest(&original.permission_query).into();
        let mut hop=h::workload_observed_credential_projection_client::WorkloadObservedCredentialProjectionClient::new(self.hop.clone()).max_encoding_message_size(8448).max_decoding_message_size(8192);
        let mut first = hop
            .project(request(original.clone(), &self.hop_caller))
            .await?;
        // Secret never enters evidence/logs; on any failed qualification erase this copy.
        let result = async {
            if first.get_ref().request_id != original.request_id
                || first.get_ref().chain_sha256 != hash
                || first.get_ref().header_value.is_empty()
            {
                return Err(Status::unavailable("first reply binding"));
            }
            let original_until = self.owners(&q).await?;
            let replay = hop.project(request(original, &self.hop_caller)).await;
            let code = match replay {
                Ok(mut r) => {
                    r.get_mut().header_value.zeroize();
                    return Err(Status::unavailable("replay credential emitted"));
                }
                Err(s) => s.code(),
            };
            // Actual Hop intentionally flattens native ledger/source refusal to Unavailable.
            if code != tonic::Code::Unavailable {
                return Err(Status::unavailable("unexpected replay status"));
            }
            self.current(original_until)?;
            self.owners(&q).await?;
            self.current(original_until)?;
            Ok(())
        }
        .await;
        if let Err(e) = result {
            first.get_mut().header_value.zeroize();
            println!(
                "{}",
                serde_json::json!({"event":"workload_pair_replay","passed":false,"stage":"post_first_validation","elapsed_ms":begun.elapsed().as_millis()})
            );
            return Err(e);
        }
        println!(
            "{}",
            serde_json::json!({"event":"workload_pair_replay","passed":true,"query_sha256_base64":STANDARD.encode(hash),"replay_status":"Unavailable","auth_and_permit_owner_checks":"before_and_after_replay","original_first_reply_returned_unchanged":true,"elapsed_ms":begun.elapsed().as_millis(),"cause":"native refusal consistent with shared replay ledger; flattened status alone is not row-specific evidence"})
        );
        // Do not renew/change owner_now or remaining. Root must charge the whole RPC delay.
        Ok(first)
    }
}
async fn execute() -> Result<(), &'static str> {
    let path = std::env::args().nth(1).ok_or("config_path")?;
    let c: Config = serde_json::from_slice(&file(&path)?).map_err(|_| "config")?;
    let incoming = caller(&c.caller_env)?;
    let mut generation = [0; 16];
    std::fs::File::open("/dev/urandom")
        .and_then(|mut f| f.read_exact(&mut generation))
        .map_err(|_| "random")?;
    let tap = Tap {
        hop: connect(&c.hop).await?,
        pum: connect(&c.pum).await?,
        incoming: Sha256::digest(incoming.as_bytes()).into(),
        hop_caller: caller(&c.hop.caller_env)?,
        pum_caller: caller(&c.pum.caller_env)?,
        capacity: Arc::new(Semaphore::new(1)),
        clock: Arc::new(
            hangang_runtime::time::ReceiverClock::new(generation).map_err(|_| "clock")?,
        ),
        hop_rates: Arc::new(
            hopae_grpc::receipt_time::ClockRates::new(c.hop_source_ppm, c.receiver_ppm)
                .map_err(|_| "rates")?,
        ),
        pum_rates: Arc::new(
            hopae_grpc::receipt_time::ClockRates::new(c.pum_source_ppm, c.receiver_ppm)
                .map_err(|_| "rates")?,
        ),
    };
    let tls = ServerTlsConfig::new()
        .identity(Identity::from_pem(file(&c.certificate)?, file(&c.key)?))
        .client_ca_root(Certificate::from_pem(file(&c.client_ca)?));
    Server::builder().tls_config(tls).map_err(|_|"server_tls")?.add_service(h::authentication_server::AuthenticationServer::new(tap.clone()).max_decoding_message_size(16384).max_encoding_message_size(8192)).add_service(h::workload_authentication_receipts_server::WorkloadAuthenticationReceiptsServer::new(tap.clone()).max_decoding_message_size(16384).max_encoding_message_size(8192)).add_service(h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjectionServer::new(tap).max_decoding_message_size(8448).max_encoding_message_size(8192)).serve_with_shutdown(c.listen,async{let _=tokio::signal::ctrl_c().await;}).await.map_err(|_|"serve")
}
#[tokio::main]
async fn main() {
    if let Err(stage) = execute().await {
        println!("{}", serde_json::json!({"probe_error":stage}));
        std::process::exit(1)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn wrapper_bounds_and_exact_raw_bytes() {
        let q = p::PermitValidationRequest {
            request_id: 7,
            request: None,
            permit: None,
        };
        let mut bytes = q.encode_to_vec();
        bytes.extend_from_slice(&[0xA0, 0x06, 1]);
        let r = h::ProjectionRequest {
            request_id: 7,
            permission_contract: 3,
            permission_query: bytes.clone(),
        };
        assert_eq!(checked_pair(&r).unwrap().request_id, 7);
        assert_eq!(r.permission_query, bytes);
        for (id, contract, n) in [(0, 3, 1), (8, 3, 1), (7, 2, 1), (7, 3, 8193)] {
            let mut bad = r.clone();
            bad.request_id = id;
            bad.permission_contract = contract;
            if n > 8192 {
                bad.permission_query = vec![0; n]
            };
            assert!(checked_pair(&bad).is_err());
        }
    }
    #[test]
    fn fixed_https_and_config_unknown_fields() {
        assert!(
            serde_json::from_str::<Config>(r#"{"listen":"127.0.0.1:1","unknown":true}"#).is_err()
        );
    }
}
#[cfg(test)]
mod rpc_tests {
    use super::*;
    use std::sync::{
        Mutex,
        atomic::{AtomicUsize, Ordering},
    };
    #[derive(Clone)]
    struct PeerFixture {
        calls: Arc<AtomicUsize>,
        queries: Arc<Mutex<Vec<Vec<u8>>>>,
        replay_allows: bool,
        owner_remaining: u32,
    }
    #[tonic::async_trait]
    impl h::workload_authentication_receipts_server::WorkloadAuthenticationReceipts for PeerFixture {
        async fn issue_observed(
            &self,
            _: Request<h::WorkloadReceiptRequest>,
        ) -> Result<Response<h::WorkloadReceiptObservedReply>, Status> {
            Err(Status::unimplemented("fixture"))
        }
        async fn observe_time(
            &self,
            r: Request<h::WorkloadReceiptObservationRequest>,
        ) -> Result<Response<h::WorkloadReceiptTimeReply>, Status> {
            let q = r.into_inner();
            Ok(Response::new(h::WorkloadReceiptTimeReply {
                request_id: q.request_id,
                remaining_ms: self.owner_remaining,
                receipt_sha256: Sha256::digest(&q.receipt).to_vec(),
                ..Default::default()
            }))
        }
    }
    #[tonic::async_trait]
    impl p::workload_observed_projection_permits_server::WorkloadObservedProjectionPermits
        for PeerFixture
    {
        async fn issue(
            &self,
            _: Request<p::AuthenticatedResourceRequest>,
        ) -> Result<Response<p::ObservedProjectionPermitReply>, Status> {
            Err(Status::unimplemented("fixture"))
        }
        async fn observe(
            &self,
            r: Request<p::PermitValidationRequest>,
        ) -> Result<Response<p::ObservedPermitTimeReply>, Status> {
            let q = r.into_inner();
            Ok(Response::new(p::ObservedPermitTimeReply {
                request_id: q.request_id,
                remaining_ms: self.owner_remaining,
                proof_remaining_ms: 900,
                receipt_sha256: Sha256::digest(&q.permit.unwrap().receipt).to_vec(),
                clock_domain: "fixture".into(),
                ..Default::default()
            }))
        }
    }
    #[tonic::async_trait]
    impl h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjection
        for PeerFixture
    {
        async fn project(
            &self,
            r: Request<h::ProjectionRequest>,
        ) -> Result<Response<h::ObservedProjectionReply>, Status> {
            let q = r.into_inner();
            self.queries.lock().unwrap().push(q.encode_to_vec());
            let n = self.calls.fetch_add(1, Ordering::SeqCst);
            if n > 0 && !self.replay_allows {
                return Err(Status::unavailable("fixture replay"));
            };
            Ok(Response::new(h::ObservedProjectionReply {
                request_id: q.request_id,
                chain_sha256: Sha256::digest(&q.permission_query).to_vec(),
                header_value: b"owned-fixture-only".to_vec(),
                remaining_ms: 800,
                ..Default::default()
            }))
        }
    }
    async fn scenario(
        replay_allows: bool,
        owner_remaining: u32,
    ) -> (
        Result<Response<h::ObservedProjectionReply>, Status>,
        Arc<AtomicUsize>,
        Arc<Mutex<Vec<Vec<u8>>>>,
    ) {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let calls = Arc::new(AtomicUsize::new(0));
        let queries = Arc::new(Mutex::new(Vec::new()));
        let f = PeerFixture {
            calls: calls.clone(),
            queries: queries.clone(),
            replay_allows,
            owner_remaining,
        };
        let task=tokio::spawn(Server::builder().add_service(h::workload_authentication_receipts_server::WorkloadAuthenticationReceiptsServer::new(f.clone())).add_service(p::workload_observed_projection_permits_server::WorkloadObservedProjectionPermitsServer::new(f.clone())).add_service(h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjectionServer::new(f)).serve_with_incoming(tokio_stream::wrappers::TcpListenerStream::new(listener)));
        let ch = Endpoint::from_shared(format!("http://{address}"))
            .unwrap()
            .connect()
            .await
            .unwrap();
        let token = "Bearer owned"
            .parse::<tonic::metadata::MetadataValue<tonic::metadata::Ascii>>()
            .unwrap();
        let tap = Tap {
            hop: ch.clone(),
            pum: ch,
            incoming: Sha256::digest(token.as_bytes()).into(),
            hop_caller: token.clone(),
            pum_caller: token.clone(),
            capacity: Arc::new(Semaphore::new(1)),
            clock: Arc::new(hangang_runtime::time::ReceiverClock::new([1; 16]).unwrap()),
            hop_rates: Arc::new(hopae_grpc::receipt_time::ClockRates::new(500, 500).unwrap()),
            pum_rates: Arc::new(hopae_grpc::receipt_time::ClockRates::new(500, 500).unwrap()),
        };
        let pair = p::PermitValidationRequest {
            request_id: 7,
            request: Some(p::AuthenticatedResourceRequest {
                context: Some(h::AuthenticationReceiptContext {
                    identity: Some(h::ReceiptIdentity {
                        kind: 3,
                        aal: 0,
                        ..Default::default()
                    }),
                    ..Default::default()
                }),
                receipt: vec![1; 32],
                ..Default::default()
            }),
            permit: Some(p::ProjectionPermitReply {
                binding: Some(p::PermitBinding {
                    authority_epoch: "fixture".into(),
                    ..Default::default()
                }),
                receipt: vec![2; 32],
                ..Default::default()
            }),
        };
        let mut bytes = pair.encode_to_vec();
        bytes.extend_from_slice(&[0xA0, 0x06, 1]);
        let r = h::ProjectionRequest {
            request_id: 7,
            permission_contract: 3,
            permission_query: bytes,
        };
        let bad = request(r.clone(), &"Bearer wrong".parse().unwrap());
        assert_eq!(h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjection::project(&tap,bad).await.unwrap_err().code(),tonic::Code::Unauthenticated);
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        let result=h::workload_observed_credential_projection_server::WorkloadObservedCredentialProjection::project(&tap,request(r,&token)).await;
        task.abort();
        (result, calls, queries)
    }
    #[tokio::test]
    async fn actual_typed_peer_replay_exact_pair_and_preserve_first_reply() {
        let (r, c, q) = scenario(false, 900).await;
        assert_eq!(r.unwrap().into_inner().header_value, b"owned-fixture-only");
        assert_eq!(c.load(Ordering::SeqCst), 2);
        let q = q.lock().unwrap();
        assert_eq!(q[0], q[1]);
    }
    #[tokio::test]
    async fn replay_success_and_expired_owner_do_not_return_first_secret() {
        let (r, c, _) = scenario(true, 900).await;
        assert!(r.is_err());
        assert_eq!(c.load(Ordering::SeqCst), 2);
        let (r, c, _) = scenario(false, 0).await;
        assert!(r.is_err());
        assert_eq!(c.load(Ordering::SeqCst), 1);
    }
}

#[cfg(test)]
mod verify_diagnostic_tests {
    use super::*;
    #[test]
    fn upstream_diagnostic_never_serializes_status_message_details_or_body() {
        let mut d = VerifyDiagnostic::ingress();
        d.admitted();
        d.upstream(&Err(Status::with_details(
            tonic::Code::Unavailable,
            "reserved-secret",
            vec![1, 2, 3].into(),
        )));
        let text = d.facts().to_string();
        assert!(!text.contains("reserved-secret"));
        assert!(!text.contains("details"));
        assert_eq!(d.facts()["tonic_code"], "unavailable");
        d.upstream(&Ok(Response::new(h::VerifyReply {
            status: 987654,
            body: b"reserved-secret".to_vec(),
            ..Default::default()
        })));
        assert_eq!(d.facts()["reply_status"], "other");
        assert!(!d.facts().to_string().contains("987654"));
        assert!(!d.facts().to_string().contains("reserved-secret"));
    }
    #[test]
    fn broken_writer_is_ignored_and_records_are_bounded() {
        struct Broken;
        impl std::io::Write for Broken {
            fn write(&mut self, _: &[u8]) -> std::io::Result<usize> {
                Err(std::io::ErrorKind::BrokenPipe.into())
            }
            fn flush(&mut self) -> std::io::Result<()> {
                Ok(())
            }
        }
        let d = VerifyDiagnostic::ingress();
        write_diagnostic(&mut Broken, &d.facts());
        let mut bytes = Vec::new();
        write_diagnostic(&mut bytes, &d.facts());
        assert!(bytes.len() < 4096 && bytes.ends_with(b"\n"));
        let before = bytes.len();
        write_diagnostic(
            &mut bytes,
            &serde_json::json!({"oversize": "x".repeat(5000)}),
        );
        assert_eq!(bytes.len(), before);
    }
    #[test]
    fn admission_refusal_has_no_upstream_reply() {
        let mut d = VerifyDiagnostic::ingress();
        d.admission_refused(tonic::Code::Unauthenticated);
        assert_eq!(d.facts()["stage"], "admission_refused");
        assert_eq!(d.facts()["reply_status"], "none");
        assert_eq!(d.facts()["tonic_code"], "unauthenticated");
    }
    #[tokio::test]
    async fn aborted_pending_verify_future_is_observable() {
        use std::sync::atomic::Ordering::Relaxed;
        let before = VERIFY_CANCELLED.load(Relaxed);
        let (tx, rx) = tokio::sync::oneshot::channel();
        let task = tokio::spawn(async move {
            let mut d = VerifyDiagnostic::ingress();
            d.admitted();
            tx.send(()).unwrap();
            std::future::pending::<()>().await;
            drop(d);
        });
        rx.await.unwrap();
        task.abort();
        assert!(task.await.unwrap_err().is_cancelled());
        assert!(VERIFY_CANCELLED.load(Relaxed) > before);
    }
}
