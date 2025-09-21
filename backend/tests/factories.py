"""Test factories and fixtures for backend unit/integration tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from .support import ensure_test_stubs

ensure_test_stubs()

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if "aiohttp" not in sys.modules:
    aiohttp_stub = types.SimpleNamespace(
        ClientSession=object,
        ClientTimeout=object,
        TCPConnector=object
    )
    sys.modules["aiohttp"] = aiohttp_stub

if "aiosqlite" not in sys.modules:
    class _AsyncDummy:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._rows: list = []

        async def __aenter__(self) -> "_AsyncDummy":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def execute(self, *args: Any, **kwargs: Any) -> None:
            return None

        async def fetchall(self) -> list:
            return list(self._rows)

        async def commit(self) -> None:
            return None

    sys.modules["aiosqlite"] = types.SimpleNamespace(connect=lambda *args, **kwargs: _AsyncDummy())


class FakeAIClient:
    async def chat(self, message: str, context: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - simple stub
        return {
            "response": "Sure, click the Login button to continue",
            "usage": {"tokens": 42}
        }


class PassthroughContentExtractor:
    async def extract_main_content(self, content: str, url: str) -> str:
        return content


@asynccontextmanager
async def patch_backend_dependencies(main_module):
    """Context manager that swaps backend globals for deterministic tests."""
    original_ai_client = main_module.ai_client
    original_content_extractor = main_module.content_extractor
    original_enhanced_agent = main_module.enhanced_agent
    original_browser_agent = main_module.browser_agent

    from backend.browser_agent import BrowserAgent
    from backend.action_pipeline import set_default_action_parser

    try:
        main_module.ai_client = FakeAIClient()
        main_module.content_extractor = PassthroughContentExtractor()
        main_module.enhanced_agent = None

        browser_agent = BrowserAgent()
        main_module.browser_agent = browser_agent
        set_default_action_parser(browser_agent)

        yield

    finally:
        main_module.ai_client = original_ai_client
        main_module.content_extractor = original_content_extractor
        main_module.enhanced_agent = original_enhanced_agent
        main_module.browser_agent = original_browser_agent
        set_default_action_parser(original_browser_agent)
