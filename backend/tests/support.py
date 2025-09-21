"""Test utilities for backend unit tests."""

from __future__ import annotations

import sys
import types
from typing import Any


def ensure_structlog_stub() -> None:
    """Provide a lightweight structlog replacement when the real package is unavailable."""
    if "structlog" in sys.modules:
        return

    class _StubLogger:
        def __getattr__(self, name: str):  # type: ignore[override]
            def _noop(*_args: Any, **_kwargs: Any) -> Any:
                return None

            return _noop

        def __call__(self, *_args: Any, **_kwargs: Any) -> "_StubLogger":
            return self

    def _get_logger(*_args: Any, **_kwargs: Any) -> _StubLogger:
        return _StubLogger()

    class _LoggerFactory:
        def __call__(self, *_args: Any, **_kwargs: Any) -> _StubLogger:
            return _StubLogger()

    stdlib_ns = types.SimpleNamespace(
        filter_by_level=lambda *args, **kwargs: None,
        add_logger_name=lambda *args, **kwargs: None,
        add_log_level=lambda *args, **kwargs: None,
        LoggerFactory=_LoggerFactory,
        BoundLogger=_StubLogger,
    )

    processors_ns = types.SimpleNamespace(
        TimeStamper=lambda fmt=None: (lambda *args, **kwargs: None)
    )

    dev_ns = types.SimpleNamespace(
        ConsoleRenderer=lambda *args, **kwargs: None
    )

    structlog_stub = types.SimpleNamespace(
        get_logger=_get_logger,
        stdlib=stdlib_ns,
        processors=processors_ns,
        dev=dev_ns,
        configure=lambda **kwargs: None,
    )

    sys.modules["structlog"] = structlog_stub


def ensure_uvicorn_stub() -> None:
    if "uvicorn" in sys.modules:
        return

    uvicorn_stub = types.SimpleNamespace(run=lambda *args, **kwargs: None)
    sys.modules["uvicorn"] = uvicorn_stub


def ensure_test_stubs() -> None:
    ensure_structlog_stub()
    ensure_uvicorn_stub()


__all__ = ["ensure_structlog_stub", "ensure_uvicorn_stub", "ensure_test_stubs"]
