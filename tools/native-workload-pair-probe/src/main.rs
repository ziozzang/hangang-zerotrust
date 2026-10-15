//! Public-wire qualification only; never mints production capabilities.
use base64::{Engine as _, engine::general_purpose::STANDARD};
use hopae_grpc::{
    receipt_time::ClockRates,
    request_binding, v1,
    workload_observed_client::{
        Client, EndpointConfig, Limits, WorkloadScope, WorkloadTrustPolicy,
    },
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};
use std::{
    io::{BufRead, Read as _, Write as _},
    sync::Arc,
    time::{Duration, Instant},
};
type Result<T> = std::result::Result<T, &'static str>;
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Settings {
    transport: String,
    address: String,
    tls: Tls,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Tls {
    server_name: String,
    ca: String,
    certificate: String,
    key: String,
}
fn one() -> u64 {
    1
}
#[derive(Default, Deserialize)]
#[serde(rename_all = "snake_case")]
enum CredentialScheme {
    #[default]
    Bearer,
}
impl CredentialScheme {
    fn header(&self, payload: &str) -> Vec<u8> {
        format!(
            "{} {payload}",
            match self {
                Self::Bearer => "Bearer",
            }
        )
        .into_bytes()
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    settings: Settings,
    #[serde(default)]
    credential_scheme: CredentialScheme,
    issuer_ref: String,
    key_epoch: u64,
    public_key: String,
    service: String,
    audience: String,
    identity_authority: String,
    source_ppm: u32,
    receiver_ppm: u32,
    #[serde(default = "one")]
    minimum_profile_revision: u64,
    #[serde(default = "one")]
    minimum_application_generation: u64,
    #[serde(default = "one")]
    minimum_key_registry_revision: u64,
    method: String,
    target: String,
    body: String,
    headers: Vec<[String; 2]>,
}
struct Held {
    context: v1::AuthenticationReceiptContext,
    receipt: zeroize::Zeroizing<Vec<u8>>,
    started: Instant,
}
struct Probe {
    config: Config,
    client: Client,
    independent: Client,
    headers: Vec<v1::Header>,
    digest: [u8; 32],
    held: Option<Held>,
}
fn read_file(path: &str) -> Result<Vec<u8>> {
    let metadata = std::fs::metadata(path).map_err(|_| "tls_file")?;
    if metadata.len() > 128 * 1024 || !metadata.is_file() {
        return Err("tls_file");
    }
    std::fs::read(path).map_err(|_| "tls_file")
}
fn clock() -> Result<Arc<hangang_runtime::time::ReceiverClock>> {
    let mut generation = [0; 16];
    std::fs::File::open("/dev/urandom")
        .and_then(|mut f| f.read_exact(&mut generation))
        .map_err(|_| "random")?;
    Ok(Arc::new(
        hangang_runtime::time::ReceiverClock::new(generation).map_err(|_| "receiver_clock")?,
    ))
}
impl Probe {
    fn new(config: Config) -> Result<Self> {
        if config.settings.transport != "grpc"
            || config.service != "orders"
            || config.audience != "orders-api"
            || config.identity_authority != "world1"
        {
            return Err("policy");
        }
        if config.body.len() > 1024 * 1024 || config.headers.len() > 31 {
            return Err("request_bounds");
        }
        let address = if config.settings.address.starts_with("https://") {
            config.settings.address.clone()
        } else if config.settings.address.contains("://") {
            return Err("endpoint");
        } else {
            format!("https://{}", config.settings.address)
        };
        let ca = read_file(&config.settings.tls.ca)?;
        let certificate = read_file(&config.settings.tls.certificate)?;
        let private_key = read_file(&config.settings.tls.key)?;
        let caller = std::env::var("OWNED_RECEIPT_CALLER").map_err(|_| "caller_environment")?;
        let credential =
            std::env::var("OWNED_RECEIPT_CREDENTIAL").map_err(|_| "credential_environment")?;
        if credential.is_empty()
            || credential.len() > 4096
            || !credential.bytes().all(|b| b.is_ascii_graphic())
        {
            return Err("credential_shape");
        }
        let public: [u8; 32] = STANDARD
            .decode(&config.public_key)
            .map_err(|_| "public_key")?
            .try_into()
            .map_err(|_| "public_key")?;
        let key = ed25519_dalek::VerifyingKey::from_bytes(&public).map_err(|_| "public_key")?;
        let make = || {
            Client::new_workload(
                EndpointConfig {
                    address: &address,
                    server_name: &config.settings.tls.server_name,
                    ca: &ca,
                    certificate: &certificate,
                    private_key: &private_key,
                    caller_key: &caller,
                },
                WorkloadTrustPolicy {
                    issuer_ref: config.issuer_ref.clone(),
                    key_epoch: config.key_epoch,
                    verifying_key: key,
                    identity_authority: config.identity_authority.clone(),
                    scopes: vec![WorkloadScope {
                        service: config.service.clone(),
                        audience: config.audience.clone(),
                    }],
                    minimum_profile_revision: config.minimum_profile_revision,
                    minimum_application_generation: config.minimum_application_generation,
                    minimum_key_registry_revision: config.minimum_key_registry_revision,
                },
                clock()?,
                ClockRates::new(config.source_ppm, config.receiver_ppm)
                    .map_err(|_| "clock_rates")?,
                Limits {
                    concurrent: 1,
                    timeout: Duration::from_secs(1),
                },
            )
            .map_err(|_| "native_client")
        };
        let client = make()?;
        let independent = make()?;
        let body_sha256: [u8; 32] = Sha256::digest(config.body.as_bytes()).into();
        let digest = request_binding::digest(&request_binding::Request {
            service: &config.service,
            audience: &config.audience,
            method: &config.method,
            target: &config.target,
            body_sha256: &body_sha256,
        })
        .map_err(|_| "request_binding")?;
        let mut headers = Vec::new();
        for [name, value] in &config.headers {
            if name.eq_ignore_ascii_case("authorization")
                || name.eq_ignore_ascii_case("x-hopae-gateway-key")
            {
                return Err("reserved_header");
            }
            if name.is_empty()
                || !name.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
                || value.bytes().any(|b| b == b'\r' || b == b'\n' || b == 0)
            {
                return Err("header_shape");
            }
            headers.push(v1::Header {
                name: name.clone(),
                value: value.as_bytes().to_vec(),
            });
        }
        headers.push(v1::Header {
            name: "authorization".into(),
            value: config.credential_scheme.header(&credential),
        });
        Ok(Self {
            config,
            client,
            independent,
            headers,
            digest,
            held: None,
        })
    }
    async fn issue(&self) -> Result<hopae_grpc::workload_observed_client::Observation> {
        let query = self
            .client
            .prepare_issue_digest(
                WorkloadScope {
                    service: self.config.service.clone(),
                    audience: self.config.audience.clone(),
                },
                self.digest,
                self.headers.clone(),
            )
            .map_err(|_| "prepare_issue")?;
        self.client.issue(query).await.map_err(|_| "issue")
    }
    async fn hold(&mut self) -> Result<serde_json::Value> {
        let started = Instant::now();
        let issue = self.issue().await?;
        self.client
            .check(&issue, issue.request())
            .map_err(|_| "hold_check")?;
        self.held = Some(Held {
            context: issue.context().clone(),
            receipt: zeroize::Zeroizing::new(issue.receipt().to_vec()),
            started,
        });
        Ok(serde_json::json!({"held":true,"authentication_only":true}))
    }
    async fn held_refuse(&self) -> Result<serde_json::Value> {
        let held = self.held.as_ref().ok_or("no_held_evidence")?;
        let query = self
            .independent
            .prepare_observation(held.context.clone(), self.digest)
            .map_err(|_| "held_prepare")?;
        if self.independent.observe(query, &held.receipt).await.is_ok() {
            return Err("held_unexpected_allow");
        }
        Ok(
            serde_json::json!({"held_refused":true,"elapsed_since_before_issue_ms":held.started.elapsed().as_millis(),"cause":"not_attributed; original1s expiry may independently explain refusal"}),
        )
    }
    async fn run(&self, allow: bool) -> Result<serde_json::Value> {
        let begun = Instant::now();
        let query = self
            .client
            .prepare_issue_digest(
                WorkloadScope {
                    service: self.config.service.clone(),
                    audience: self.config.audience.clone(),
                },
                self.digest,
                self.headers.clone(),
            )
            .map_err(|_| "prepare_issue")?;
        let issue = self.client.issue(query).await;
        if !allow {
            return match issue {
                Err(_) => Ok(
                    serde_json::json!({"contract":"hopae-workload-observed-sdk-v1","allowed":false,"expected_denial":true,"phase":"issue"}),
                ),
                Ok(_) => Err("unexpected_allow"),
            };
        }
        let issue = issue.map_err(|_| "issue")?;
        self.client
            .check(&issue, issue.request())
            .map_err(|_| "issue_check")?;
        let query = self
            .independent
            .prepare_observation(issue.context().clone(), self.digest)
            .map_err(|_| "prepare_independent_observation")?;
        let observed = self
            .independent
            .observe(query, issue.receipt())
            .await
            .map_err(|_| "independent_observe")?;
        self.independent
            .check(&observed, observed.request())
            .map_err(|_| "independent_check")?;
        // This consumes the existing observation; no independently renewed query.
        let refreshed = self
            .independent
            .refresh(observed)
            .await
            .map_err(|_| "consuming_refresh")?;
        self.independent
            .check(&refreshed, refreshed.request())
            .map_err(|_| "refresh_check")?;
        self.client
            .check(&issue, issue.request())
            .map_err(|_| "original_issue_final_check")?;
        let identity = refreshed.context().identity.as_ref().ok_or("identity")?;
        if identity.kind != 3 || identity.aal != 0 {
            return Err("workload_identity");
        }
        let epoch = hopae_grpc::workload_epoch::decode(
            refreshed.context().identity_authority_epoch.as_str(),
        )
        .map_err(|_| "signed_epoch")?;
        Ok(
            serde_json::json!({"contract":"hopae-workload-observed-sdk-v1","allowed":true,"subject_ref":identity.subject_ref,"kind":identity.kind,"aal":identity.aal,"issued":true,"independently_observed":true,"refreshed":true,"issuer_ref":self.config.issuer_ref,"key_epoch":self.config.key_epoch,"identity_authority":epoch.authority,"service":self.config.service,"audience":self.config.audience,"clock_domain":epoch.clock_domain,"profile_revision":epoch.profile_revision,"application_generation":epoch.application_generation,"key_registry_revision":refreshed.key_registry_revision(),"source_ppm":self.config.source_ppm,"receiver_ppm":self.config.receiver_ppm,"total_elapsed_ms":begun.elapsed().as_millis()}),
        )
    }
}
async fn execute() -> Result<()> {
    let path = std::env::args().nth(1).ok_or("config_path")?;
    let meta = std::fs::metadata(&path).map_err(|_| "config_read")?;
    if !meta.is_file() || meta.len() > 2 * 1024 * 1024 {
        return Err("config_bounds");
    }
    let bytes = std::fs::read(path).map_err(|_| "config_read")?;
    if bytes.len() > 2 * 1024 * 1024 {
        return Err("config_bounds");
    }
    let config: Config = serde_json::from_slice(&bytes).map_err(|_| "config_parse")?;
    let mut probe = Probe::new(config)?;
    let mut ran = false;
    for line in std::io::stdin().lock().lines() {
        let command = line.map_err(|_| "stdin")?;
        let command = command.trim();
        if command.is_empty() {
            continue;
        }
        if command == "hold" {
            println!("{}", probe.hold().await?);
            std::io::stdout().flush().map_err(|_| "stdout")?;
            ran = true;
            continue;
        }
        if command == "held-refuse" {
            println!("{}", probe.held_refuse().await?);
            std::io::stdout().flush().map_err(|_| "stdout")?;
            ran = true;
            continue;
        }
        let allow = match command {
            "allow" => true,
            "deny" => false,
            _ => return Err("command"),
        };
        let result = probe.run(allow).await?;
        println!("{}", result);
        std::io::stdout().flush().map_err(|_| "stdout")?;
        ran = true;
    }
    if !ran {
        println!("{}", probe.run(true).await?);
    }
    Ok(())
}
#[tokio::main]
async fn main() {
    if let Err(stage) = execute().await {
        println!(
            "{}",
            serde_json::json!({"contract":"hopae-workload-observed-sdk-v1","allowed":false,"probe_error":stage})
        );
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_scheme_defaults_and_unknown_schemes_refuse() {
        assert!(matches!(
            CredentialScheme::default(),
            CredentialScheme::Bearer
        ));
        assert!(serde_json::from_value::<CredentialScheme>(serde_json::json!("bearer")).is_ok());
        for value in [
            "hopae_compose",
            "Basic",
            "Hopae-Compose",
            "raw",
            "bearer secret",
            "x-forwarded-user",
        ] {
            assert!(serde_json::from_value::<CredentialScheme>(serde_json::json!(value)).is_err());
        }
        assert_eq!(
            CredentialScheme::Bearer.header("payload"),
            b"Bearer payload"
        );
    }
}
