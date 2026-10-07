from database import add_demo_voter


DEMO_VOTERS = [
    {
        "identity": "647162579350",
        "name": "Shlok Jain",
        "constituency": "Nanded West",
        "phone": "+919860918447"
    },
    {
        "identity": "471099122860",
        "name": "Maheshwar Bang",
        "constituency": "Old Akola City",
        "phone": "+919423104234"
    },
    {
        "identity": "777933171417",
        "name": "Hiren Bhanushali",
        "constituency": "Nanded East",
        "phone": "+919307580487"
    },
    {
        "identity": "914353580104",
        "name": "Vidit Ramani",
        "constituency": "Akola",
        "phone": "+919518579722"
    }
]


def load_demo_voters():

    for voter in DEMO_VOTERS:

        add_demo_voter(
            voter["identity"],
            voter["name"],
            voter["constituency"],
            voter["phone"]
        )