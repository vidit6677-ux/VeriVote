# VeriVote Enhanced - Operator Guide

## Start the application

```powershell
python main.py
```

The default polling-centre credentials are shown in the application README.

## Configure Google Authenticator

On the first Central login, select **SET UP GOOGLE AUTHENTICATOR**. Add the
displayed setup key to Google Authenticator, then enter the current six-digit
code. The application does not generate or display a substitute demo code.

## Demonstrate a voter

1. Log in to the polling terminal.
2. Scan a QR image from `demo_qr_codes`.
3. Verify the matching face. During verification, move your head slightly.
4. Select one candidate and confirm the ballot.
5. Show the anonymous ballot receipt and four-level replication result.

## Demonstrate security monitoring

1. Open the Admin Security Portal.
2. Sign in as Central.
3. Open **DEMO LAB**.
4. Select **RUN FULL SECURITY DEMO**.
5. Show the Central alert and integrity mismatch.
6. Use **RESET DEMO ELECTION** to restore the clean state.

## Useful controls

- **VIEW AUDIT LOG**: inspect administrator events.
- **EXPORT ADMIN AUDIT CSV**: save an audit report.
- **BACK UP DATABASES**: create consistent local SQLite backups.
- `python setup_voter_face.py <identity>`: enroll five face samples.

## Windows executable

Run `build_windows.ps1` from PowerShell. If PyInstaller is not installed:

```powershell
.\build_windows.ps1 -InstallPyInstaller
```

The executable is written to `dist\VeriVote\VeriVote.exe`.
