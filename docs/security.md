# VeriVote security model

VeriVote is a security-focused academic prototype. Its controls demonstrate engineering techniques; they do not make the system suitable for a public election.

## Integrity and authenticity

- SHA-256 creates vote, checkpoint, and hash-chain digests.
- HMAC-SHA-256 is retained only as an explicit demo fallback.
- Ed25519 signatures can be enabled per administrative level with separate private/public keys.
- The four-level checkpoints and tamper alerts are tamper-evident, not tamper-proof.

## Authentication and authorization

- Admin passwords use the existing salted PBKDF2 implementation.
- JWTs are short-lived and issuer-validated.
- RBAC restricts Central integrity and recovery operations.
- Central additionally uses face verification and TOTP in the GUI workflow.
- The Central API login is a password-to-JWT demo path; it does **not** perform
  GUI face/TOTP MFA and must not be represented as equivalent Central MFA.
- Failed admin authentication is subject to lockout and audit logging.

## Replay and abuse controls

- Sensitive vote operations require an idempotency key bound to the request payload.
- Reusing a key with the same payload returns HTTP 409; reusing it with a
  different payload returns a distinct HTTP 409 conflict.
- Sensitive API paths have a process-local rate limiter.
- These controls are not distributed across multiple API instances; production deployment needs Redis or an API gateway.

## Privacy

The tokenized ballot path separates the eligibility-to-token mapping from the private ballot table and stores only a hash of the one-time token with the ballot. Both mappings currently share a local SQLite host, so a privileged host/database operator may still correlate issuance and ballot timing. The legacy GUI/`POST /votes` path remains identity-linked for compatibility and must not be described as full ballot secrecy.

## Availability and recovery

The local vote and its durable replication-outbox row commit in one SQLite transaction. Central can retry failed four-level replication. The outbox contains identity-linked replication payloads and, together with the four SQLite files, remains on one host in the demo; these are not independent physical trust domains.

## Trust boundaries

The client, camera, QR input, API request, local host, database files, signing keys, and external SMS provider have different trust assumptions. A compromised host can undermine local controls; managed keys, independent storage, external identity, monitoring, and formal review are required for a production system.
