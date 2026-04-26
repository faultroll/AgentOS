"""AgentOS Kernel — Compute Scheduler

Multi-model scheduling. Treats N available models as N CPU cores.
Selects the best model for each request based on:
  1. Capability matching (tags)
  2. Health status (from telemetry)
  3. Priority ordering
  4. Cost tier

The Scheduler DECIDES. The Router EXECUTES.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from kernel.telemetry import TelemetryBus

logger = logging.getLogger(__name__)

# Cooldown period (seconds) before retrying a failed model
_FAILURE_COOLDOWN = 60.0


@dataclass
class ModelProfile:
    """Capability profile for a registered model."""
    alias: str               # e.g. "qwen/qwen3-coder:free"
    provider: str            # e.g. "openrouter"
    tags: set[str] = field(default_factory=lambda: {"general"})
    cost_tier: str = "free"  # "free" | "paid"
    priority: int = 100      # Lower = higher priority


class ComputeScheduler:
    """OS-level compute scheduler — selects models for requests."""

    def __init__(self, telemetry: TelemetryBus):
        self._telemetry = telemetry
        self._models: dict[str, ModelProfile] = {}

    def register_model(self, profile: ModelProfile) -> None:
        """Register a model in the scheduling pool."""
        self._models[profile.alias] = profile
        logger.info(
            f"⚙️ [Scheduler] Registered model: {profile.alias} "
            f"(provider={profile.provider}, tags={profile.tags}, "
            f"tier={profile.cost_tier}, priority={profile.priority})"
        )

    def register_from_config(self, router_config: dict, router_models: list) -> None:
        """
        Bulk-register models from the existing config.py format.
        Auto-assigns priorities from list ordering.
        """
        for idx, alias in enumerate(router_models):
            provider = router_config.get(alias, "unknown")
            tags = _infer_tags(alias)
            cost_tier = "free" if ":free" in alias or provider in ("local_engine", "ollama") else "paid"
            self.register_model(ModelProfile(
                alias=alias,
                provider=provider,
                tags=tags,
                cost_tier=cost_tier,
                priority=idx * 10,
            ))

    def select_model(
        self,
        preferred_tags: set[str] = None,
        force_model: str = None,
        cost_limit: str = "free",
    ) -> list[str]:
        """
        Return an ordered list of models to try, best-first.

        Strategy:
          1. If force_model is valid and healthy → put it first
          2. Filter by cost_limit
          3. Score remaining by: tag_match + health + priority
          4. Exclude models in cooldown
        """
        now = time.time()
        candidates = []

        for alias, profile in self._models.items():
            # Cost filter
            if cost_limit == "free" and profile.cost_tier == "paid":
                continue

            # Health check via telemetry
            stats = self._telemetry.get_model_stats(alias)
            if stats and not stats.is_healthy:
                # Check cooldown
                if now - stats.last_failure_time < _FAILURE_COOLDOWN:
                    logger.debug(f"⏳ [Scheduler] {alias} in cooldown, skipping")
                    continue

            # Score calculation
            score = 1000 - profile.priority  # Base: priority (lower priority = higher score)
            if preferred_tags and profile.tags & preferred_tags:
                score += 500  # Tag match bonus
            if stats:
                score += int(stats.success_rate * 100)  # Health bonus
                if stats.avg_latency_ms > 0:
                    score -= min(int(stats.avg_latency_ms / 100), 200)  # Latency penalty

            candidates.append((alias, score))

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        result = [alias for alias, _ in candidates]

        # If force_model is specified and valid, ensure it's first
        if force_model and force_model in self._models:
            if force_model in result:
                result.remove(force_model)
            result.insert(0, force_model)
        elif force_model:
            logger.warning(
                f"🛡️ [Scheduler] Rejected unregistered model: {force_model}"
            )

        return result


def _infer_tags(alias: str) -> set[str]:
    """Infer capability tags from model alias naming conventions."""
    tags = {"general"}
    lower = alias.lower()
    if "coder" in lower or "code" in lower:
        tags.add("coding")
    if "instruct" in lower:
        tags.add("instruction")
    if "chat" in lower:
        tags.add("chat")
    if "preview" in lower:
        tags.add("reasoning")
    if "nemotron" in lower:
        tags.add("reasoning")
    if "gemma" in lower:
        tags.add("chat")
    if "architect" in lower or "local" in lower:
        tags.add("reasoning")
    return tags
