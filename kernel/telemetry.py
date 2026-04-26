"""AgentOS Kernel — Telemetry Bus

OS-level observability primitive. Every LLM call, tool call, and
memory access emits a structured TelemetryEvent onto the bus.

Design:
  - Pure data, zero natural language
  - Ring buffer in memory (bounded, no disk I/O)
  - Scheduler consumes events for model health scoring
  - Apps can query their own events for app-level evaluation
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)

# Maximum events retained in the ring buffer
_MAX_EVENTS = 10000


@dataclass
class TelemetryEvent:
    """A single telemetry data point — pure structured data."""
    timestamp: float
    event_type: str        # "llm_call" | "tool_call" | "memory_read" | "memory_write"
    app_name: str          # Which App produced this event
    model_alias: str = ""  # Which model was used (if applicable)
    provider: str = ""     # Which provider served the request
    latency_ms: float = 0.0
    token_input: int = 0
    token_output: int = 0
    success: bool = True
    error_type: str = ""   # e.g. "429", "timeout", "connection_error"
    cost: float = 0.0


@dataclass
class ModelStats:
    """Aggregated statistics for a single model."""
    model_alias: str
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_failure_time: float = 0.0
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.success_count / self.total_calls

    @property
    def is_healthy(self) -> bool:
        """Model is healthy if it hasn't failed 3+ times in a row."""
        return self.consecutive_failures < 3


class TelemetryBus:
    """OS-level telemetry ring buffer + model stats aggregator."""

    def __init__(self, max_events: int = _MAX_EVENTS):
        self._events: deque[TelemetryEvent] = deque(maxlen=max_events)
        self._model_stats: dict[str, ModelStats] = {}

    def emit(self, event: TelemetryEvent) -> None:
        """Record an event and update aggregated stats."""
        self._events.append(event)

        # Update model stats if this is an LLM call
        if event.event_type == "llm_call" and event.model_alias:
            stats = self._model_stats.setdefault(
                event.model_alias, ModelStats(model_alias=event.model_alias)
            )
            stats.total_calls += 1
            stats.total_tokens += event.token_input + event.token_output
            stats.total_cost += event.cost

            if event.success:
                stats.success_count += 1
                stats.consecutive_failures = 0
                # Running average for latency
                n = stats.success_count
                stats.avg_latency_ms = (
                    stats.avg_latency_ms * (n - 1) + event.latency_ms
                ) / n
            else:
                stats.failure_count += 1
                stats.consecutive_failures += 1
                stats.last_failure_time = event.timestamp

        if not event.success:
            logger.warning(
                f"📊 [Telemetry] {event.event_type} FAIL: "
                f"app={event.app_name} model={event.model_alias} "
                f"error={event.error_type}"
            )

    def emit_llm_call(
        self, app_name: str, model_alias: str, provider: str,
        latency_ms: float, token_input: int, token_output: int,
        success: bool, error_type: str = "", cost: float = 0.0
    ) -> None:
        """Convenience wrapper for LLM call events."""
        self.emit(TelemetryEvent(
            timestamp=time.time(),
            event_type="llm_call",
            app_name=app_name,
            model_alias=model_alias,
            provider=provider,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            success=success,
            error_type=error_type,
            cost=cost,
        ))

    def get_model_stats(self, model_alias: str) -> Optional[ModelStats]:
        """Get aggregated stats for a specific model."""
        return self._model_stats.get(model_alias)

    def get_all_model_stats(self) -> dict[str, ModelStats]:
        """Get stats for all known models."""
        return dict(self._model_stats)

    def query(
        self, app_name: str = None, event_type: str = None,
        since: float = None, limit: int = 100
    ) -> list[TelemetryEvent]:
        """Query events with optional filters."""
        results = []
        for event in reversed(self._events):
            if app_name and event.app_name != app_name:
                continue
            if event_type and event.event_type != event_type:
                continue
            if since and event.timestamp < since:
                break  # Events are chronological, stop early
            results.append(event)
            if len(results) >= limit:
                break
        return list(reversed(results))

# Global OS-level Telemetry Bus Singleton
global_telemetry = TelemetryBus()
