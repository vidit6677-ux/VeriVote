"""In-process idempotency guard for the academic API demo."""

import hashlib
import threading
import time


class ReplayGuard:
    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def claim(self, key: str, payload: str, operation: str) -> str:
        """Claim an idempotency key for one operation and payload.

        ``new`` accepts the request, ``duplicate`` means the same operation
        and payload were seen, and ``conflict`` prevents a key from being
        repurposed for a different payload.
        """
        fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        scoped_key = f"{operation}:{key}"
        now = time.monotonic()
        with self._lock:
            self._entries = {
                saved_key: value
                for saved_key, value in self._entries.items()
                if now - value[1] < self.ttl_seconds
            }
            previous = self._entries.get(scoped_key)
            if previous is not None:
                return "duplicate" if previous[0] == fingerprint else "conflict"
            self._entries[scoped_key] = (fingerprint, now)
            return "new"


vote_replay_guard = ReplayGuard()
