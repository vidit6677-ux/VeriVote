# VeriVote threat model

VeriVote is an educational prototype, not a public-election system. This document records the security assumptions and the controls demonstrated by the project.

| Asset | Threat / attack vector | Impact | Existing control | Residual risk | Next mitigation |
|---|---|---|---|---|---|
| Vote ledger | Direct database modification, deletion, or insertion | Incorrect results or loss of evidence | SHA-256 hash chain, signed checkpoints, four-level comparison, tamper alerts | An attacker controlling the host may alter both data and local secrets | Use Ed25519 with private keys isolated from verification services and an external append-only audit store |
| Voter eligibility | Reuse of an identity or concurrent requests | Duplicate or unauthorized vote | Eligibility checks, `has_voted` constraint, atomic transaction, duplicate-vote tests | Compromised operator or host can bypass application code | Harden database access and add independent review |
| Administrator accounts | Password guessing or role confusion | Unauthorized administrative access | Salted PBKDF2 hashes, role matching, failed-attempt lockout, audit logs | Demo accounts and local storage are not production identity management | Use an external identity provider and managed secrets |
| Central administrator | Password-only API login compromise | High-privilege API takeover | Face verification and TOTP flow applies to the GUI; API JWT login is explicitly demo-only and password-based | API JWT login is not equivalent to GUI MFA | Require MFA/elevation for Central API operations and use hardware-backed MFA |
| TOTP secret | Database or filesystem disclosure | MFA bypass | Encrypted storage with external key configuration | Key rotation and provisioning are manual | Use a secrets manager or HSM |
| SMS notification | Provider outage or credential exposure | Missing notification or information disclosure | Notification is outside the vote commit path | External provider and phone data are third-party dependencies | Add delivery monitoring and minimize message content |
| Replication path | Partial failure after local vote commit | Administrative levels disagree | The local vote and durable outbox row commit atomically; security events and Central retry handle later failure | Outbox payloads are identity-linked and local to the demo host, not an independent queue | Use a transactional broker or PostgreSQL outbox with monitored workers |
| Ballot privacy | Linking a voter identity to a candidate | Loss of ballot secrecy | Optional tokenized ballot path separates the issuance mapping from the private ballot ledger | The issuance mapping and ballots are still on one host, and the legacy GUI/API path remains identity-linked | Migrate the GUI to tokenized ballots and use independent stores with controlled access |
| API abuse | Credential guessing, replay, or request flooding | Account compromise or service degradation | JWT expiry, RBAC, idempotency keys, and process-local rate limits | Rate limits are not shared across multiple instances | Use a shared gateway or Redis-backed limiter in deployment |

## Trust boundaries

1. The voter/GUI or API client is untrusted input.
2. FastAPI validates request shape, then delegates business rules to the existing service layer.
3. The service layer and SQLite databases are local trusted components for this prototype.
4. Integrity checkpoints provide evidence of disagreement between independent administrative levels; they do not make a compromised host trustworthy.

## Security verification demonstrated

- Invalid constituency requests are rejected before a vote is recorded.
- Missing voters return HTTP 404.
- Duplicate votes are rejected by the service and database constraints.
- Four-level replication and cleanup are covered by the end-to-end test.
- Checkpoint signatures and cross-level mismatches generate security events.
- Ed25519 checkpoint signatures are supported when separate per-level private/public keys are provisioned; HMAC-SHA-256 remains an explicit demo fallback.
- JWTs are short-lived and role-scoped; vote requests require an idempotency key to reject in-process replays.
