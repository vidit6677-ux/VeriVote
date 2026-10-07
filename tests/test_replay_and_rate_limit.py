from api.rate_limit import RateLimiter
from api.replay import ReplayGuard


def test_replay_guard_distinguishes_duplicate_and_payload_conflict():
    guard = ReplayGuard()

    assert guard.claim("request-key-1", '{"candidate":"A"}', "vote") == "new"
    assert guard.claim("request-key-1", '{"candidate":"A"}', "vote") == "duplicate"
    assert guard.claim("request-key-1", '{"candidate":"B"}', "vote") == "conflict"


def test_rate_limiter_allows_under_limit_and_isolates_clients():
    limiter = RateLimiter(limit=2, window_seconds=60)

    assert limiter.allow("client-a")
    assert limiter.allow("client-a")
    assert not limiter.allow("client-a")
    assert limiter.allow("client-b")
