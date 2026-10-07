# VeriVote Five-Minute Demonstration

## 1. Establish the story

“VeriVote verifies the voter, protects ballot identity, records a tamper-evident
ledger, and lets Central detect failures across four administrative levels.”

## 2. Show the secure voter flow

- Scan Shlok's QR.
- Use the matching face.
- Move slightly when prompted to demonstrate liveness.
- Cast a ballot.
- Point out that the replicated private ballot uses a token hash rather than
  the voter's identity.

## 3. Show the Central dashboard

- Open Central security.
- Point out the role, MFA, ledger, synchronization, and alert cards.
- Open **DEMO LAB**.

## 4. Demonstrate an attack

- Click **RUN FULL SECURITY DEMO**.
- Explain that the Booth ledger is altered locally.
- Run the verification and show that Central reports the mismatch.
- Open **VIEW AUDIT LOG** and **EXPORT ADMIN AUDIT CSV**.

## 5. Recover

- Click **RESET DEMO ELECTION**.
- Run verification again and show the clean GENESIS state.
- Finish by showing the database backup control.
