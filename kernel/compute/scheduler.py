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
    context_window: int = 8192  # [NEW] Default 8k


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

    def register_from_config(self, router_config: dict, router_models: list, model_metadata: dict = None) -> None:
        """
        Bulk-register models from the existing config.py format.
        Uses [NEW] model_metadata for enriched profiles.
        """
        for idx, alias in enumerate(router_models):
            provider = router_config.get(alias, "unknown")
            
            # Use explicit metadata if available, otherwise infer
            meta = model_metadata.get(alias, {}) if model_metadata else {}
            
            tags = meta.get("tags", _infer_tags(alias))
            cost_tier = meta.get("cost_tier", "free")
            context_window = meta.get("context_window", 8192)
            
            self.register_model(ModelProfile(
                alias=alias,
                provider=provider,
                tags=tags,
                cost_tier=cost_tier,
                priority=idx * 10,
                context_window=context_window
            ))

    def select_model(
        self,
        preferred_tags: set[str] = None,
        force_model: str = None,
        cost_limit: str = "free",
        strategy: str = "priority",
        estimated_tokens: int = 0,  # [NEW] Task size sensing
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
            if cost_limit == "free" and profile.cost_tier != "free":
                continue
            if cost_limit == "paid" and profile.cost_tier not in ("free", "paid"):
                continue

            # Health check via telemetry
            stats = self._telemetry.get_model_stats(alias)
            if stats and not stats.is_healthy:
                # Check cooldown
                if now - stats.last_failure_time < _FAILURE_COOLDOWN:
                    logger.debug(f"⏳ [Scheduler] {alias} in cooldown, skipping")
                    continue

            # Score calculation
            if strategy == "cost":
                # Higher score for lower cost
                cost_map = {"free": 2000, "paid": 1000, "premium": 0}
                score = cost_map.get(profile.cost_tier, 0)
                score -= profile.priority / 100  # Priority as tiebreaker
            else:
                # Default: priority-first
                score = 1000 - profile.priority
            
            # Physical Capacity Sensing
            # [REFINED] WE NO LONGER FILTER. We just penalize small cores.
            # If the task size is known and exceeds current core's capacity, lower its priority.
            if estimated_tokens > 0 and estimated_tokens > profile.context_window:
                score -= 2000  # Strong penalty to push it to the end of the line
            elif estimated_tokens > 0 and estimated_tokens > profile.context_window * 0.8:
                score -= 500   # Near limit warning (internal to scheduler ranking)

            if preferred_tags and profile.tags & preferred_tags:
                score += 500  # Tag match bonus
            
            if stats:
                score += int(stats.success_rate * 100)  # Health bonus
                if stats.avg_latency_ms > 0:
                    if strategy == "latency":
                        score -= int(stats.avg_latency_ms)  # Heavy penalty for latency
                    else:
                        score -= min(int(stats.avg_latency_ms / 100), 200)

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


    def get_model_profile(self, alias: str) -> Optional[ModelProfile]:
        """Return the profile for a specific model, if it exists."""
        return self._models.get(alias)

    def list_models_by_tag(self, tag: str) -> list[str]:
        """Return all model aliases that have the specified tag."""
        return [alias for alias, p in self._models.items() if tag in p.tags]


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
