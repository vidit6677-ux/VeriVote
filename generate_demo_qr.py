import qrcode
import os

DEMO_VOTERS = [
    {
        "identity": "647162579350",
        "name": "Shlok Jain",
        "constituency": "Nanded West"
    },
    {
        "identity": "471099122860",
        "name": "Maheshwar Bang",
        "constituency": "Old Akola City"
    },
    {
        "identity": "777933171417",
        "name": "Hiren Bhanushali",
        "constituency": "Nanded East"
    },
    {
        "identity": "914353580104",
        "name": "Vidit Ramani",
        "constituency": "Akola"
    }
]

os.makedirs("demo_qr_codes", exist_ok=True)

for voter in DEMO_VOTERS:

    qr = qrcode.make(voter["identity"])

    filename = (
        voter["name"]
        .replace(" ", "_")
        + ".png"
    )

    filepath = os.path.join(
        "demo_qr_codes",
        filename
    )

    qr.save(filepath)

    print(f"QR created for {voter['name']}")
    print(f"Identity: {voter['identity']}")
    print(f"Constituency: {voter['constituency']}")
    print(f"Saved: {filepath}")
    print("-" * 50)

print("All demo QR codes generated successfully.")