"""Circuit breaker, request pacer, and in-memory cache for Google Patents Web Gateway."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    CLOSED = "CLOSED"          # Normal operation: requests go to web gateway
    OPEN = "OPEN"              # Throttled/503: fast-fallback, cooldown active
    HALF_OPEN = "HALF_OPEN"    # Cooldown passed: probing canary request


class CircuitBreaker:
    """Manages circuit breaker state, request pacing, and LRU cache for patents.google.com."""

    def __init__(
        self,
        failure_threshold: int = 1,
        cooldown_seconds: float = 15.0,
        max_cooldown_seconds: float = 60.0,
        backoff_factor: float = 1.5,
        request_spacing_seconds: float = 0.3,
    ):
        self.failure_threshold = failure_threshold
        self.initial_cooldown = cooldown_seconds
        self.current_cooldown = cooldown_seconds
        self.max_cooldown = max_cooldown_seconds
        self.backoff_factor = backoff_factor
        self.request_spacing = request_spacing_seconds

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl = 600.0  # 10 minute cache TTL

    async def pace_request(self) -> None:
        """Enforces a minimum spacing between consecutive outbound requests to avoid burst rate limits."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.request_spacing:
                wait_time = self.request_spacing - elapsed
                await asyncio.sleep(wait_time)
            self.last_request_time = time.time()

    def get_cached(self, key: str) -> Optional[Any]:
        """Retrieves a non-expired cached response."""
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
            del self._cache[key]
        return None

    def set_cached(self, key: str, val: Any) -> None:
        """Stores a response in the in-memory cache."""
        if len(self._cache) > 500:
            self._cache.clear()
        self._cache[key] = (time.time(), val)

    def can_attempt(self) -> Tuple[bool, str, float]:
        """Checks if a request can be attempted against the web gateway.

        Returns:
            Tuple of (can_attempt: bool, state_name: str, cooldown_remaining: float).
        """
        now = time.time()
        if self.state == CircuitBreakerState.CLOSED:
            return True, self.state, 0.0

        cooldown_remaining = (self.last_failure_time + self.current_cooldown) - now
        if cooldown_remaining <= 0:
            self.state = CircuitBreakerState.HALF_OPEN
            logger.info("Circuit breaker transitioned to HALF_OPEN (probing canary request).")
            return True, self.state, 0.0

        return False, self.state, round(cooldown_remaining, 1)

    def record_success(self) -> None:
        """Called when a request to web gateway succeeds with 200 OK."""
        if self.state != CircuitBreakerState.CLOSED:
            logger.info(f"Circuit breaker recovered! Resetting to CLOSED. Cooldown reset to {self.initial_cooldown}s.")
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.current_cooldown = self.initial_cooldown

    def record_failure(self, status_code: int = 503) -> None:
        """Called when a request returns 503 or network error."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.current_cooldown = min(self.current_cooldown * self.backoff_factor, self.max_cooldown)
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker canary probe failed (HTTP {status_code}). Backing off: cooldown increased to {self.current_cooldown}s."
            )
        elif self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker tripped to OPEN due to HTTP {status_code}. Cooldown: {self.current_cooldown}s."
            )

    def get_status(self) -> Dict[str, Any]:
        """Returns the current diagnostic status of the circuit breaker."""
        can_try, state, remaining = self.can_attempt()
        return {
            "circuit_state": state,
            "can_attempt_web_gateway": can_try,
            "cooldown_remaining_seconds": remaining,
            "total_cached_queries": len(self._cache),
            "failure_count": self.failure_count,
        }
