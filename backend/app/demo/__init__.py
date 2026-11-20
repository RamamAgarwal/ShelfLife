"""Demo mode: the real pipeline against simulated Bifrost, Tavily and web pages.

Turn it on with DEMO_MODE=true in .env. Nothing here needs keys or spends credits,
and demo checks are stored apart from real ones.
"""

from __future__ import annotations

import httpx

from app import config
from app.demo.simulator import SCENARIOS, Simulator

_simulator: Simulator | None = None


def active() -> bool:
    return config.get_settings().demo_mode


def activate() -> None:
    """Point every outgoing client at the simulator and fill in demo settings."""
    global _simulator
    from app import links, llm, search

    settings = config.get_settings()
    settings.bifrost_url = "http://bifrost.demo"
    settings.bifrost_vk = settings.bifrost_vk or "sk-bf-demo"
    settings.tavily_api_key = settings.tavily_api_key or "demo"
    settings.bifrost_setup_token = settings.bifrost_setup_token or "demo"
    settings.model_fast = settings.model_fast or "demo/fast"
    settings.model_strong = settings.model_strong or "demo/strong"
    settings.model_stale = settings.model_stale or "demo/old"
    settings.fallbacks_fast = settings.fallbacks_fast or "backup/fast"
    settings.fallbacks_strong = settings.fallbacks_strong or "backup/strong"
    settings.history_path = settings.history_path.with_name("history-demo.sqlite3")
    settings.search_cache_path = settings.search_cache_path.with_name("search-demo.sqlite3")
    _simulator = Simulator()
    transport = httpx.MockTransport(_simulator)
    llm._transport = transport
    search._transport = transport
    links._transport = transport
    # The simulator answers every request, so the public-address check would only
    # reject its invented hosts; real addresses are refused instead.
    links._public_only = False
    links._demo_suffix = ".example"


def scenarios() -> list[dict]:
    return SCENARIOS
