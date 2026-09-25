"""Privacy-aware one-time ballot token workflow."""

from database import cast_private_ballot, issue_ballot_token


def issue_one_time_ballot(voter_identity, constituency):
    return issue_ballot_token(voter_identity, constituency)


def submit_tokenized_ballot(token, candidate):
    return cast_private_ballot(token, candidate)
