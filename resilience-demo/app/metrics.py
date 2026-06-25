import asyncio
from dataclasses import dataclass, field


@dataclass
class MetricsStore:
    api_requests: int = 0
    api_successes: int = 0
    api_failures: int = 0
    downstream_calls: int = 0
    downstream_successes: int = 0
    downstream_failures: int = 0
    retries_total: int = 0
    circuit_short_circuits: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def reset(self) -> None:
        async with self._lock:
            self.api_requests = 0
            self.api_successes = 0
            self.api_failures = 0
            self.downstream_calls = 0
            self.downstream_successes = 0
            self.downstream_failures = 0
            self.retries_total = 0
            self.circuit_short_circuits = 0

    async def record_api_request(self) -> None:
        async with self._lock:
            self.api_requests += 1

    async def record_api_success(self) -> None:
        async with self._lock:
            self.api_successes += 1

    async def record_api_failure(self) -> None:
        async with self._lock:
            self.api_failures += 1

    async def record_downstream_call(self) -> None:
        async with self._lock:
            self.downstream_calls += 1

    async def record_downstream_success(self) -> None:
        async with self._lock:
            self.downstream_successes += 1

    async def record_downstream_failure(self) -> None:
        async with self._lock:
            self.downstream_failures += 1

    async def record_retry(self) -> None:
        async with self._lock:
            self.retries_total += 1

    async def record_circuit_short_circuit(self) -> None:
        async with self._lock:
            self.circuit_short_circuits += 1

    async def snapshot(self, circuit_state: str, failure_rate: float) -> dict:
        async with self._lock:
            amplification = (
                round(self.downstream_calls / self.api_requests, 2)
                if self.api_requests
                else 0.0
            )
            return {
                "circuit_state": circuit_state,
                "failure_rate": failure_rate,
                "api_requests": self.api_requests,
                "api_successes": self.api_successes,
                "api_failures": self.api_failures,
                "downstream_calls": self.downstream_calls,
                "downstream_successes": self.downstream_successes,
                "downstream_failures": self.downstream_failures,
                "retries_total": self.retries_total,
                "circuit_short_circuits": self.circuit_short_circuits,
                "amplification_factor": amplification,
            }


metrics = MetricsStore()
