"""Settings flags."""

from __future__ import annotations

from app.core.config import Settings


def test_ask_agent_enabled_defaults_true(monkeypatch):
    monkeypatch.delenv("ASK_AGENT_ENABLED", raising=False)
    assert Settings(_env_file=None).ask_agent_enabled is True


def test_ask_agent_enabled_reads_env(monkeypatch):
    monkeypatch.setenv("ASK_AGENT_ENABLED", "false")
    assert Settings(_env_file=None).ask_agent_enabled is False
