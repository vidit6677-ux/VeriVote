from database import get_voter


def verify_voter(identity):

    voter = get_voter(identity)

    if voter is None:

        return {
            "success": False,
            "message": "Voter not found in database."
        }

    if not voter["eligible"]:

        return {
            "success": False,
            "message": "Voter is not eligible to vote."
        }

    if voter["has_voted"]:

        return {
            "success": False,
            "message": "This voter has already voted."
        }

    return {
        "success": True,

        "identity": voter["identity"],
        "name": voter["name"],
        "constituency": voter["constituency"],

        # Phone number
        "phone": voter["phone"],

        "eligible": voter["eligible"],
        "has_voted": voter["has_voted"],

        "message": "Voter authenticated successfully."
    }