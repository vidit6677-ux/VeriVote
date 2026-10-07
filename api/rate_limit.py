"""Small process-local abuse limiter for the academic deployment."""

import threading
import time


class RateLimiter:
    def __init__(self, limit=60, window_seconds=60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self._lock:
            recent = [stamp for stamp in self._hits.get(key, []) if now - stamp < self.window_seconds]
            if len(recent) >= self.limit:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            return True


sensitive_rate_limiter = RateLimiter()
