# VeriVote

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
├── main.py
├── config.py
├── database.py
├── requirements.txt
├── README.md
│
├── setup_central_face.py
├── setup_central_2fa.py
├── reset_demo.py
├── generate_demo_qr.py
├── test_camera.py
├── test_level_tamper.py
│
├── data/
│   └── demo_voters.py
│
├── demo_qr_codes/
│
├── face_data/
│
├── models/
│   └── haarcascade_frontalface_default.xml
│
├── gui/
│   ├── login.py
│   ├── voter_verification.py
│   ├── biometric.py
│   ├── ballot.py
│   ├── result.py
│   ├── admin_login.py
│   ├── admin_face.py
│   ├── admin_2fa.py
│   └── admin_dashboards.py
│
├── services/
│   ├── biometric_service.py
│   ├── integrity_service.py
│   ├── voting_service.py
│   ├── notification_service.py
│   ├── admin_security.py
│   ├── admin_2fa.py
│   ├── sync_service.py
│   └── alert_service.py
│
└── utils/
    ├── security.py
    └── secret_storage.py
```

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
```

---

# 23. Environment Variables

Sensitive values should be stored outside the source code.

Current environment-variable names include:

```text
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
VERIVOTE_CENTRAL_TOTP_KEY
```

Do not commit actual values to GitHub.

The Central encryption key should remain outside the repository.

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

The `face_data/` directory is excluded from Git.

The face-recognition implementation is intended for the college prototype.

---

# 25. Central 2FA Enrollment

Central TOTP setup is intentionally separate from normal login.

The enrollment utility is:

```bash
python setup_central_2fa.py
```

The setup secret should only be handled during controlled enrollment.

Normal Central login does not display the secret.

---

# 26. Running the Application

Start VeriVote from the project root:

```bash
python main.py
```

The application provides:

```text
Voter Workflow
+
Administrative Workflow
```

The application should be run from the project root so the expected database, model, and local-data paths are available.

---

# 27. Demo Administrator Accounts

The prototype includes four demonstration administrator levels:

```text
BOOTH
ZONAL
DEPUTY
CENTRAL
```

The configured demonstration usernames are:

```text
booth01
zonal01
deputy01
central01
```

The demonstration passwords are defined in the project configuration and are intended only for the college prototype.

> Do not reuse demonstration credentials in a real system.

---

# 28. Demo Voter Data

The prototype contains demonstration voters associated with constituencies.

The current voter data is defined in:

```text
data/demo_voters.py
```

Example project identities include:

```text
647162579350
471099122860
777933171417
914353580104
```

The project also contains demo QR images and local face-reference images for testing.

Sensitive or personal-looking demonstration data should not be published unnecessarily.

---

# 29. Testing

## 29.1 Application Startup

Run:

```bash
python main.py
```

Verify that the GUI loads successfully.

---

## 29.2 Admin Dashboard Test

Verify each level:

```text
BOOTH   → Booth Dashboard
ZONAL   → Zonal Dashboard
DEPUTY  → Deputy Dashboard
CENTRAL → Password → Face → 2FA → Central Dashboard
```

---

## 29.3 Duplicate Voting Test

Use a voter who has not yet voted.

Expected:

```text
First vote
   ↓
SUCCESS
```

Then attempt a second vote using the same voter.

Expected:

```text
Second vote
   ↓
BLOCKED
```

The database should contain only one vote for that voter.

---

## 29.4 Database Constraint Test

The unique index should exist:

```text
idx_votes_one_vote_per_voter
```

It is created on:

```text
votes(voter_identity)
```

---

## 29.5 Ledger Integrity Test

The project can recalculate the vote hashes and verify the chain.

Expected healthy state:

```text
Ledger integrity → VALID
```

---

## 29.6 Four-Level Synchronization Test

After synchronization:

```text
BOOTH     → SYNCED
ZONAL     → SYNCED
DEPUTY    → SYNCED
CENTRAL   → SYNCED
```

---

## 29.7 Tamper Detection Test

Run:

```bash
python test_level_tamper.py
```

The test temporarily modifies a Booth checkpoint and checks whether the system flags the change.

Expected:

```text
BOOTH → TAMPERED / MISMATCH
```

The test restores the original Booth checkpoint after execution.

---

## 29.8 Central 2FA Test

Verify:

```text
Password ✓
Face     ✓
TOTP     ✓
```

Then verify that Central access is granted only after all required steps succeed.

---

# 30. Git and GitHub

The repository is hosted on GitHub:

```text
https://github.com/vidit6677-ux/VeriVote
```

The project uses Git for version control.

Recommended development flow:

```text
Change Code
    ↓
Run Tests
    ↓
git status
    ↓
git add .
    ↓
git commit
    ↓
git push
```

Security-sensitive files should remain excluded through `.gitignore`.

The following should not be committed:

```text
verivote.db
face_data/
.env
TOTP encryption keys
Twilio authentication tokens
Other private secrets
```

---

# 31. Security and Privacy Notes

The repository should not contain:

```text
Database files
Biometric reference files
Authentication secrets
Twilio credentials
Central encryption keys
Private environment files
```

The project uses environment variables for external secrets.

The Central TOTP encryption key is intended to remain outside the repository.

Demo QR and voter data should be treated as project data rather than public production data.

---

# 32. Limitations

VeriVote is a college project prototype.

## Face Verification

The face-verification component uses laptop-camera computer vision and is intended to demonstrate the concept.

It should not be treated as production-grade biometric authentication.

## Hash Chain

The vote hash chain provides tamper evidence.

It does not by itself physically prevent database deletion or compromise.

## SQLite

SQLite is convenient for a classroom prototype.

A production election system would require hardened infrastructure and a much larger security architecture.

## Secret Management

The project demonstrates encrypted secret storage and environment-based key handling.

A production deployment would require stronger key lifecycle management, secure provisioning, rotation, access control, and potentially hardware-backed key storage.

---

# 33. Development Roadmap

The project is being developed through the following phases:

```text
Phase 1
Four-Level Admin Dashboards

Phase 2
Role-Based Admin Authentication

Phase 3
Central Enhanced Security

Phase 4
Three-Way has_voted Protection

Phase 5
Vote Ledger Integrity

Phase 6
Four-Level Synchronization

Phase 7
Cross-Level Tamper Detection

Phase 8
Audit Logs + Security Alerts

Phase 9
GUI Integration

Phase 10
End-to-End Security Testing
```

The development approach is to complete and test one security layer before adding the next.

---

# 34. Project Status

Current implemented prototype components include:

```text
✓ Voter verification
✓ QR / identity verification
✓ Eligibility checks
✓ Constituency validation
✓ Face verification
✓ Ballot workflow
✓ Vote hashing
✓ Hash-chain ledger
✓ SMS notification
✓ Three-way vote protection
✓ Booth dashboard
✓ Zonal dashboard
✓ Deputy dashboard
✓ Central dashboard
✓ Role-based admin authentication
✓ Password hashing
✓ Admin lockout
✓ Central face authentication
✓ Central TOTP 2FA
✓ Encrypted Central TOTP storage
✓ Admin audit logging
✓ Security event logging
✓ Integrity checkpoints
✓ Four-level synchronization backend
✓ Cross-level tamper detection test
```

---

# 35. Academic Demonstration

The project can be demonstrated through the following sequence.

## Demonstration 1 — Normal Voting

```text
QR
 ↓
Eligibility
 ↓
Face
 ↓
Ballot
 ↓
Vote
 ↓
Ledger
 ↓
has_voted = 1
 ↓
SMS
```

## Demonstration 2 — Duplicate Vote Prevention

```text
First Vote
    ↓
Accepted

Second Attempt
    ↓
Blocked
```

## Demonstration 3 — Central Security

```text
Central Login
    ↓
Password
    ↓
Face
    ↓
TOTP
    ↓
Central Dashboard
```

## Demonstration 4 — Four-Level Synchronization

```text
BOOTH     ✓
ZONAL     ✓
DEPUTY    ✓
CENTRAL   ✓
```

## Demonstration 5 — Tamper Detection

```text
Modify Booth Checkpoint
        ↓
Integrity Verification
        ↓
Booth Flagged
        ↓
Higher-Level Alert
        ↓
Central Sees Security Event
```

---

# Final Note

VeriVote demonstrates how multiple security mechanisms can be combined in a controlled academic prototype:

```text
Identity Verification
        +
Face Verification
        +
Role-Based Access
        +
Multi-Factor Authentication
        +
Database Constraints
        +
Atomic Transactions
        +
Cryptographic Hashing
        +
Integrity Checkpoints
        +
Tamper Detection
        +
Audit Logging
        +
Security Alerts
```

The project should be presented as a **defense-in-depth, tamper-evident prototype**, not as an unbreakable or production-ready election system.
