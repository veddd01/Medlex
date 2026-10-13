"""Simple in-memory rate limiter for /ask endpoint."""
import time
import threading
from collections import defaultdict
from functools import wraps
from flask import request, jsonify

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            # Clean old entries
            self._requests[key] = [
                t for t in self._requests[key]
                if now - t < self.window_seconds
            ]
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True
    
    def limit(self, key_func=None):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                key = key_func() if key_func else request.remote_addr
                if not self.is_allowed(key):
                    return jsonify({"error": "Rate limit exceeded. Please wait before making more requests."}), 429
                return f(*args, **kwargs)
            return wrapper
        return decorator

rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
