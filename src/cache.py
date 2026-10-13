"""Simple LRU response cache for repeated questions."""
from collections import OrderedDict
import hashlib
import threading
from typing import Any, Dict, Optional

class ResponseCache:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()
    
    def _key(self, question: str) -> str:
        return hashlib.sha256(question.lower().strip().encode()).hexdigest()
    
    def get(self, question: str) -> Optional[Dict[str, Any]]:
        key = self._key(question)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        return None
    
    def set(self, question: str, response: Dict[str, Any]) -> None:
        key = self._key(question)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = response
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

response_cache = ResponseCache(max_size=100)
