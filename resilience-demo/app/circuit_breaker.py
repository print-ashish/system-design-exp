import asyncio
import time

from app.config import CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_OPEN_SECONDS
from app.metrics import metrics


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self) -> None:
        self.state = "closed"
        self.consecutive_failures = 0
        self.opened_at: float | None = None
        self._lock = asyncio.Lock()

    def reset(self) -> None:
        self.state = "closed"
        self.consecutive_failures = 0
        self.opened_at = None

    async def call(self, func):
        async with self._lock:
            if self.state == "open":
                if self.opened_at is not None and (
                    time.monotonic() - self.opened_at >= CIRCUIT_OPEN_SECONDS
                ):
                    self.state = "half_open"
                else:
                    await metrics.record_circuit_short_circuit()
                    raise CircuitOpenError("circuit is open")

        try:
            result = await func()
        except Exception:
            async with self._lock:
                self.consecutive_failures += 1
                if self.state == "half_open" or self.consecutive_failures >= CIRCUIT_FAILURE_THRESHOLD:
                    self.state = "open"
                    self.opened_at = time.monotonic()
            raise

        async with self._lock:
            self.consecutive_failures = 0
            if self.state == "half_open":
                self.state = "closed"
        return result


circuit_breaker = CircuitBreaker()
