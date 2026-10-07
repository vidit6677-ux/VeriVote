# VeriVote

## Enhanced demonstration build

This copy includes a Central-only **Demo Lab** for live demonstrations:

- Run integrity verification and refresh the dashboard.
- Inject a controlled Booth tamper and show the resulting alert.
- Export up to 1,000 administrator audit records as CSV.

Log in as the Central administrator and select **DEMO LAB** from the dashboard.
The original project copy remains unchanged.

For a guided walkthrough, see [USER_GUIDE.md](USER_GUIDE.md) and
[DEMO_SCRIPT.md](DEMO_SCRIPT.md). A Windows onedir build can be created with
`build_windows.ps1`.

To enroll multiple voter face samples, run:

```bash
python setup_voter_face.py <voter_identity>
```

Capture five samples while changing the angle or lighting slightly.

Face verification also requires a small head movement during the camera
check, which helps reject a static photograph in the demonstration workflow.

The voter GUI now uses the tokenized ballot path. Eligibility and the one-time
token are checked before casting, while the replicated ballot ledger stores a
one-way token hash instead of the voter's identity.

## Secure Polling Centre Voting System

VeriVote is a college project prototype that demonstrates a secure digital voting workflow using identity verification, eligibility checking, face verification, cryptographic vote integrity, role-based administration, multi-factor authentication, audit logging, synchronized administrative checkpoints, and tamper detection.

> **Academic Project Notice:** VeriVote is an educational prototype for college demonstration. It is not intended for deployment in a real public election.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objectives](#2-objectives)
3. [System Architecture](#3-system-architecture)
4. [Voter Workflow](#4-voter-workflow)
5. [Four-Level Administrative Architecture](#5-four-level-administrative-architecture)
6. [Booth Dashboard](#6-booth-dashboard)
7. [Zonal Dashboard](#7-zonal-dashboard)
8. [Deputy Dashboard](#8-deputy-dashboard)
9. [Central Dashboard](#9-central-dashboard)
10. [Central Security](#10-central-security)
11. [Three-Way `has_voted` Protection](#11-three-way-has_voted-protection)
12. [Vote Ledger and Hash Chain](#12-vote-ledger-and-hash-chain)
13. [Four-Level Synchronization](#13-four-level-synchronization)
14. [Tamper Detection](#14-tamper-detection)
15. [Security Alerts](#15-security-alerts)
16. [Audit Logging](#16-audit-logging)
17. [Authentication Model](#17-authentication-model)
18. [Central TOTP 2FA](#18-central-totp-2fa)
19. [Central TOTP Secret Protection](#19-central-totp-secret-protection)
20. [Technology Stack](#20-technology-stack)
21. [Project Structure](#21-project-structure)
22. [Installation](#22-installation)
23. [Environment Variables](#23-environment-variables)
24. [Central Face Enrollment](#24-central-face-enrollment)
25. [Central 2FA Enrollment](#25-central-2fa-enrollment)
26. [Running the Application](#26-running-the-application)
27. [Demo Administrator Accounts](#27-demo-administrator-accounts)
28. [Demo Voter Data](#28-demo-voter-data)
29. [Testing](#29-testing)
30. [Git and GitHub](#30-git-and-github)
31. [Security and Privacy Notes](#31-security-and-privacy-notes)
32. [Limitations](#32-limitations)
33. [Development Roadmap](#33-development-roadmap)
34. [Project Status](#34-project-status)
35. [Academic Demonstration](#35-academic-demonstration)

---

# 1. Project Overview

VeriVote provides a controlled polling-centre workflow with a separate administrative security layer.

### Voter side

```text
QR / Identity Verification
          ↓
Eligibility Check
          ↓
Constituency Validation
          ↓
Face Verification
          ↓
Ballot
          ↓
Vote Recording
          ↓
Hash-Based Ledger
          ↓
Mark Voter as Voted
          ↓
SMS Notification
```

### Administrative side

```text
                  CENTRAL
                     ↓
                  DEPUTY
                     ↓
                   ZONAL
                     ↓
                   BOOTH
```

The administrative system uses role-specific dashboards and permissions.

---

# 2. Objectives

The main objectives of the VeriVote project are to demonstrate:

- Secure voter verification
- Face-based identity verification
- Prevention of duplicate voting
- Transaction-safe vote recording
- Cryptographic vote integrity
- Tamper-evident ledger design
- Role-based administrative access
- Stronger Central administrator authentication
- Multi-factor authentication
- Cross-level integrity monitoring
- Security event detection
- Administrative audit logging

---

# 3. System Architecture

The project is divided into three major layers.

## Voter Layer

```text
Identity / QR
     ↓
Eligibility
     ↓
Face Verification
     ↓
Ballot
     ↓
Vote
```

## Security Layer

```text
Database Constraints
        +
Atomic Transactions
        +
Hash Chain
        +
Integrity Checkpoints
        +
Tamper Detection
```

## Administrative Layer

```text
BOOTH
  ↓
ZONAL
  ↓
DEPUTY
  ↓
CENTRAL
```

Central acts as the highest-security administrative layer in the prototype.

---

# 4. Voter Workflow

The normal voter flow is:

```text
Polling Centre Login
        ↓
QR / Identity Verification
        ↓
Voter Lookup
        ↓
Eligibility Check
        ↓
Already Voted Check
        ↓
Face Verification
        ↓
Constituency Check
        ↓
Ballot
        ↓
Vote Confirmation
        ↓
Secure Vote Transaction
        ↓
Ledger Update
        ↓
SMS Notification
```

The candidate name is not intended to be included in the SMS confirmation content used by the current project.

---

# 5. Four-Level Administrative Architecture

VeriVote uses four distinct administrative levels:

```text
                 CENTRAL
                    │
                  DEPUTY
                    │
                   ZONAL
                    │
                  BOOTH
```

Each level has:

- Its own login role
- A dedicated dashboard
- Role-specific responsibilities
- Appropriate visibility into lower-level activity
- Access restrictions

The hierarchy is designed so that higher levels can monitor lower levels without giving every level unrestricted administrative authority.

---

# 6. Booth Dashboard

The Booth dashboard is intended for local polling operations.

Typical responsibilities:

- Voter verification
- Face verification
- Ballot access
- Vote recording
- Local ledger verification
- Booth activity monitoring
- Local security status

The Booth role has the most limited administrative scope.

---

# 7. Zonal Dashboard

The Zonal dashboard supervises Booth-level operations.

Typical responsibilities:

- Monitor assigned Booth activity
- Review Booth statistics
- Review security status
- Review local integrity results
- Review lower-level security alerts
- Review synchronization status

---

# 8. Deputy Dashboard

The Deputy dashboard provides broader oversight across Zones.

Typical responsibilities:

- Monitor assigned Zones
- Review Zonal activity
- Review regional statistics
- Review ledger integrity
- Review security events
- Review synchronization status
- Observe lower-level anomalies

---

# 9. Central Dashboard

The Central dashboard is the highest-security administrative dashboard.

Central is intended to provide system-wide visibility into:

- All four administrative levels
- System integrity
- Ledger integrity
- Synchronization state
- Security alerts
- Administrative authentication status
- Audit activity
- Cross-level tamper detection

Central authentication is stronger than the lower administrative levels.

---

# 10. Central Security

Central uses defense-in-depth rather than relying on a single control.

### Central authentication

```text
Username
   ↓
Password
   ↓
Face Verification
   ↓
TOTP 2FA
   ↓
Central Dashboard
```

### Central security controls

- Password authentication
- Salted password hashing
- Failed-attempt tracking
- Temporary account lockout
- Face verification
- TOTP-based 2FA
- Encrypted TOTP secret storage
- Role-based authorization
- Session timeout
- Administrative audit logging
- Security event logging
- Ledger integrity verification
- Four-level synchronization monitoring
- Cross-level tamper detection

The goal is to make Central the most protected administrative level of the prototype.

---

# 11. Three-Way `has_voted` Protection

VeriVote uses three separate protections for the vote-status state.

```text
1. Application Check
        ↓
   Has this voter already voted?

2. Database Constraint
        ↓
   Only ONE vote allowed per voter

3. Atomic Transaction
        ↓
   Save vote + mark voter as voted
   happen together
```

## 11.1 Application Check

Before a ballot can be accessed, the application checks:

```text
has_voted == 0
```

If:

```text
has_voted == 1
```

the voter is blocked.

The project also performs a final voter-state check inside the transaction.

## 11.2 Database Constraint

The `votes` table uses a unique index on:

```text
voter_identity
```

The index used by the project is:

```text
idx_votes_one_vote_per_voter
```

This prevents multiple vote rows for the same voter identity at the database level.

## 11.3 Atomic Transaction

The vote is stored and the voter is marked as voted using the same database transaction.

```text
BEGIN
   ↓
Save Vote
   +
Set has_voted = 1
   +
Write Audit Record
   ↓
COMMIT
```

If the transaction fails:

```text
ROLLBACK
```

This is intended to prevent partial state changes.

---

# 12. Vote Ledger and Hash Chain

Every recorded vote contains information used to construct a SHA-256 hash.

The new hash includes the previous hash.

Conceptually:

```text
Vote 1
  ↓
Hash 1
  ↓
Vote 2
  ↓
Hash 2
  ↓
Vote 3
  ↓
Hash 3
```

The ledger verification process checks:

- Previous-hash links
- Stored vote hashes
- Hash recalculation
- Broken links
- Unexpected changes
- Missing records

This makes the ledger **tamper-evident**.

> A hash chain does not physically make a database undeletable. It provides evidence that the ledger state has changed or become inconsistent.

---

# 13. Four-Level Synchronization

The four administrative levels maintain integrity checkpoints:

```text
BOOTH
ZONAL
DEPUTY
CENTRAL
```

A checkpoint can contain:

```text
Level
Last Vote ID
Ledger Hash
Previous Checkpoint Hash
Checkpoint Hash
Signature
Timestamp
```

The intended state is:

```text
BOOTH     → Vote 25 → ABC123
ZONAL     → Vote 25 → ABC123
DEPUTY    → Vote 25 → ABC123
CENTRAL   → Vote 25 → ABC123
```

When all values agree, the four levels are synchronized.

---

# 14. Tamper Detection

The system is designed to detect mismatches between levels and between a checkpoint and the current ledger.

Example:

```text
BOOTH     → Hash XYZ999   ← mismatch
ZONAL     → Hash ABC123
DEPUTY    → Hash ABC123
CENTRAL   → Hash ABC123
```

Possible causes detected by the system include:

- Invalid checkpoint signature
- Ledger hash mismatch
- Vote-ID mismatch
- Stale checkpoint
- Missing checkpoint

The higher administrative levels can see lower-level security events.

Example:

```text
Booth anomaly
      ↓
Zonal alert
      ↓
Deputy alert
      ↓
Central alert
```

---

# 15. Security Alerts

Security events can include:

- Failed administrator login
- Face verification failure
- TOTP failure
- Integrity mismatch
- Invalid checkpoint signature
- Ledger hash mismatch
- Synchronization failure
- Cross-level mismatch
- Other administrative security events

Alerts are stored as security events and displayed according to administrative visibility.

---

# 16. Audit Logging

Administrative security actions are recorded in an audit log.

Example events:

```text
Administrator Login
Failed Login
Face Authentication
2FA Authentication
2FA Setup
Security Verification
Integrity Verification
Synchronization Event
Security Failure
```

A typical audit record contains:

```text
Username
Role
Action
Details
Status
Timestamp
```

This provides traceability for security-sensitive administrative actions.

---

# 17. Authentication Model

The project uses different authentication strength according to administrative level.

### Booth

```text
Username
+
Password
```

### Zonal

```text
Username
+
Password
```

### Deputy

```text
Username
+
Password
```

### Central

```text
Username
+
Password
+
Face Verification
+
TOTP 2FA
```

The Central account also has stronger lockout and security monitoring controls.

---

# 18. Central TOTP 2FA

Central uses time-based one-time passwords.

Normal Central login does not display the TOTP setup secret.

The login flow is:

```text
Password
   ↓
Face
   ↓
Enter current 6-digit OTP
   ↓
Central Dashboard
```

The code rotates periodically through the TOTP mechanism.

The authenticator secret should be treated as sensitive authentication material.

---

# 19. Central TOTP Secret Protection

The Central TOTP secret is stored separately from the normal login interface.

The intended storage model is:

```text
SQLite
   ↓
Encrypted TOTP Secret
```

The encryption key is held outside the database using the environment variable:

```text
VERIVOTE_CENTRAL_TOTP_KEY
```

The key should not be committed to GitHub.

The normal Central login screen does not display the TOTP setup key.

---

# 20. Technology Stack

The prototype uses:

- Python
- Tkinter
- SQLite
- FastAPI + Uvicorn
- Pydantic request validation
- Pytest + HTTPX API tests
- GitHub Actions CI
- Docker / Docker Compose
- OpenCV
- OpenCV Contrib
- LBPH Face Recognizer
- PyOTP
- Cryptography / Fernet
- Twilio

---

# 21. Project Structure

```text
VeriVote/
│
├── api/                         # FastAPI transport and API controls
│   ├── main.py
│   ├── rate_limit.py
│   ├── replay.py
│   └── security.py
├── data/
│   └── demo_voters.py
├── docs/                        # Security, threat-model, migration notes
│   ├── postgresql-migration.md
│   ├── security.md
│   └── threat-model.md
├── gui/                         # Existing Tkinter workflow and dashboards
├── services/                    # Domain, cryptography, replication services
│   ├── crypto_service.py
│   ├── four_level_sync.py
│   ├── integrity_service.py
│   ├── privacy_service.py
│   ├── replication_service.py
│   └── voting_service.py
├── tests/                       # Automated API, crypto, replay/rate tests
│   ├── test_api.py
│   ├── test_crypto.py
│   └── test_replay_and_rate_limit.py
├── utils/
│   ├── secret_storage.py
│   └── security.py
├── .github/workflows/ci.yml
├── .dockerignore
├── .env.example
├── .gitattributes
├── .gitignore
├── config.py
├── database.py
├── docker-compose.yml
├── Dockerfile
├── main.py
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── reset_demo.py
├── setup_central_2fa.py
├── setup_central_face.py
├── test_end_to_end_vote.py
├── test_four_db_sync.py
└── test_level_tamper.py
```

Runtime SQLite databases, biometric material, `.env`, test caches, and
`work/` are intentionally excluded from version control.

---

# 22. Installation

Clone the repository:

```bash
git clone https://github.com/vidit6677-ux/VeriVote.git
```

Enter the project:

```bash
cd VeriVote
```

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

Important packages include:

```text
opencv-contrib-python
twilio
pyotp
cryptography
fastapi
uvicorn
PyJWT
```

---

# 23. Environment Variables

Sensitive values should be stored outside the source code.

Current environment-variable names include:

```text
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
VERIVOTE_JWT_SECRET
VERIVOTE_CENTRAL_TOTP_KEY
VERIVOTE_BOOTH_SIGNING_KEY
VERIVOTE_ZONAL_SIGNING_KEY
VERIVOTE_DEPUTY_SIGNING_KEY
VERIVOTE_CENTRAL_SIGNING_KEY
VERIVOTE_<LEVEL>_ED25519_PRIVATE_KEY
VERIVOTE_<LEVEL>_ED25519_PUBLIC_KEY
```

Do not commit actual values to GitHub. Use `.env.example` as the variable-name
template. The checked-in defaults are for the academic demo only; production
deployments must provide externally managed secrets.

---

# 24. Central Face Enrollment

The Central administrator reference face can be enrolled using:

```bash
python setup_central_face.py
```

The local reference is stored as:

```text
face_data/central_admin.jpg
```

The `face_data/` directory is excluded from Git. The face-recognition
implementation is intended for the college prototype.

---

# 25. Central 2FA Enrollment

Central TOTP setup is intentionally separate from normal login.

The enrollment utility is:

```bash
python setup_central_2fa.py
```

The setup secret should only be handled during controlled enrollment. Normal
Central GUI login does not display the secret.

---

# 26. Running the Application

Start VeriVote from the project root:

```bash
python main.py
```

## FastAPI backend

Start the API with:

```bash
python -m uvicorn api.main:app --reload
```

Useful endpoints:

```text
GET  /health                       Liveness check
GET  /ready                        Database readiness check
GET  /docs                         Interactive OpenAPI documentation
POST /auth/login                   Issue a short-lived role-scoped JWT
GET  /voters/{identity}            Read a voter record
POST /votes                        Authenticated, idempotent legacy vote
POST /ballots/issue                Issue a one-time tokenized ballot
POST /ballots/cast                 Submit a tokenized ballot
GET  /integrity/status             Central-only four-level integrity summary
POST /integrity/replication/retry  Central-only retry of queued replication
```

The API delegates vote decisions to `services.voting_service.cast_vote`; it
does not duplicate voting rules. Voter, vote, and integrity endpoints require
a bearer token. Vote submissions require an `Idempotency-Key` with 8–128
letters, digits, `.`, `_`, `:`, or `-`; same-payload reuse and different-payload
reuse both return HTTP 409 with distinct reasons.

**Central API boundary:** the API's Central password-to-JWT login is a
demo-only path and does not execute the GUI's face and TOTP MFA steps. It must
not be described as MFA-equivalent Central access.

If a local vote commits, its `replication_outbox` row commits in the same
transaction. Four-level replication is then attempted; Central can retry a
pending job if that step fails. The outbox is identity-linked and local to this
prototype host.

The tokenized ballot path separates the eligibility-to-token mapping from
`private_ballots`, but both are currently local SQLite data stores. The legacy
GUI and `/votes` endpoint remain identity-linked compatibility paths and do not
provide ballot secrecy.

The enhanced GUI uses the tokenized path and replicates anonymous ballot rows
to all four level databases. The eligibility-to-token mapping remains local to
the polling-centre host and should be separated into an independent service
for production deployment.

Central API login requires an OTP when `VERIVOTE_DEMO_MODE=false`. Central can
query filtered audit records through `GET /admin/audit`, and the Central Demo
Lab can create consistent SQLite backups.

Stable `/api/v1` aliases are available for health, authentication, voter, vote,
and integrity endpoints. The SQLite-to-PostgreSQL boundary and migration
sequence are documented in `docs/postgresql-migration.md`; PostgreSQL is not
implemented or claimed as complete.

## Cryptographic model

SHA-256 hashes use fixed-order, length-delimited UTF-8 fields for votes and
checkpoint material. Passwords use PBKDF2-HMAC-SHA256, not plain SHA-256.
Checkpoints use HMAC-SHA-256 only as an explicit demo fallback; Ed25519 is used
when a level has both configured private and public keys.

For a containerized API demo:

```bash
copy .env.example .env
docker compose up --build
```

---

# 27. Demo Administrator Accounts

The prototype includes four demonstration administrator levels:

```text
BOOTH
ZONAL
DEPUTY
CENTRAL
```

The demonstration credentials are defined in project configuration and are for
the college prototype only. Do not reuse them in a real system.

---

# 28. Demo Voter Data

Demo voters are defined in `data/demo_voters.py`. Demo QR images and local
face references are testing material and should not be published unnecessarily.

---

# 29. Testing

Run the repeatable regression suite:

```bash
python -m pytest tests -q
```

The suite covers API authentication/RBAC, vote validation, four-level integrity
endpoint wiring, crypto primitives, idempotency conflicts, and rate-limiter
behaviour.

Run the additional project verification scripts:

```bash
python test_four_db_sync.py
python test_end_to_end_vote.py
python test_level_tamper.py
```

GitHub Actions installs the development dependencies and enforces compilation,
tests, Bandit, Ruff, and pip-audit on pushes and pull requests.

---

# 30. Git and GitHub

Security-sensitive files must remain excluded through `.gitignore`, including
database files, biometric reference files, `.env`, tokens, keys, test caches,
and temporary work products.

---

# 31. Security and Privacy Notes

The threat model and residual risks are documented in `docs/threat-model.md`.
VeriVote is a defense-in-depth, tamper-evident academic prototype, not a
production-ready election system.

---

# 32. Limitations

SQLite, local biometric processing, demo credentials, process-local replay and
rate controls, a local token issuance mapping, and a local replication outbox
are intentionally limited to a classroom prototype. Production deployment
would require independent infrastructure, external identity/MFA, managed key
storage, a shared rate-limit/replay store, external audit storage, and formal
security review.

---

# 33. Development Roadmap

Future production work includes PostgreSQL migration, independent identity and
MFA, managed secrets, external audit storage, distributed replay/rate controls,
deployment hardening, and formal review.

---

# 34. Project Status

Implemented prototype components include voter verification, duplicate-vote
protection, hash-chain integrity, four-level synchronization and tamper checks,
admin roles, GUI Central face/TOTP workflow, JWT/RBAC API controls, tokenized
ballot support, transactional replication recovery, automated tests, CI,
Docker, and security documentation.

---

# 35. Academic Demonstration

Use the GUI to demonstrate the voter and Central GUI MFA flows, then use the
test commands above to demonstrate replication and tamper detection. Present
the system as a controlled academic prototype.
