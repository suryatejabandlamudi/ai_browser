"""Utilities for converting raw or free-form AI suggestions into structured actions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

import structlog

from .real_browser_agent import real_browser_agent

logger = structlog.get_logger(__name__)


_DefaultParser = Any
__default_action_parser: Optional[_DefaultParser] = None


def set_default_action_parser(parser: Optional[_DefaultParser]) -> None:
    """Configure the parser used when candidate actions are missing."""
    global __default_action_parser
    __default_action_parser = parser


def get_default_action_parser() -> Optional[_DefaultParser]:
    return __default_action_parser


async def assemble_structured_actions(
    candidate_actions: Optional[Sequence[Dict[str, Any]]],
    ai_response_text: str,
    page_url: Optional[str] = None,
    *,
    parser: Optional[_DefaultParser] = None,
    page_dom: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Transform raw action candidates into extension-ready automation steps."""

    parser = parser or get_default_action_parser()

    actions_to_process: List[Dict[str, Any]] = []
    if candidate_actions:
        actions_to_process.extend(
            [action for action in candidate_actions if isinstance(action, dict)]
        )

    if not actions_to_process and parser is not None:
        try:
            parsed_actions = await parser.parse_actions(ai_response_text)
            actions_to_process.extend(parsed_actions)
        except Exception as parse_error:  # pragma: no cover - defensive logging
            logger.warning(
                "Failed to parse actions from AI response",
                error=str(parse_error)
            )

    structured_actions: List[Dict[str, Any]] = []
    seen_signatures = set()

    for raw_action in actions_to_process:
        try:
            action_type = (raw_action.get("type") or raw_action.get("action") or "").strip().lower()
        except AttributeError:
            continue

        if not action_type:
            continue

        parameters: Dict[str, Any] = {}
        if isinstance(raw_action.get("parameters"), dict):
            parameters.update({
                key: value
                for key, value in raw_action["parameters"].items()
                if value not in (None, "")
            })

        for field, param_key in (
            ("selector", "target"),
            ("target", "target"),
            ("text", "text"),
            ("url", "url"),
            ("direction", "direction"),
            ("amount", "amount"),
            ("value", "text"),
        ):
            value = raw_action.get(field)
            if value not in (None, "") and param_key not in parameters:
                parameters[param_key] = value

        try:
            execution_result = await real_browser_agent.execute_action(
                action_type,
                parameters,
                page_url or "",
                page_dom=page_dom,
            )
        except Exception as execution_error:  # pragma: no cover - defensive logging
            logger.warning(
                "Real browser agent failed to prepare action",
                action_type=action_type,
                error=str(execution_error)
            )
            execution_result = {"success": False, "data": None, "message": str(execution_error)}

        payload: Optional[Dict[str, Any]] = None
        if execution_result.get("success") and execution_result.get("data"):
            payload = execution_result["data"].copy()
            payload.setdefault("executable", True)
        else:
            payload = {
                "type": action_type.upper(),
                "executable": bool(
                    raw_action.get("selector")
                    or raw_action.get("url")
                    or raw_action.get("text")
                ),
                "parameters": parameters or None,
                "message": execution_result.get("message")
            }

        if not payload:
            continue

        payload.setdefault("type", action_type.upper())

        if payload.get("selector") in (None, ""):
            if parameters.get("selector"):
                payload["selector"] = parameters.get("selector")
            elif parameters.get("target"):
                payload["selector"] = parameters.get("target")

        if payload.get("text") in (None, "") and parameters.get("text"):
            payload["text"] = parameters.get("text")

        if payload.get("url") in (None, "") and parameters.get("url"):
            payload["url"] = parameters.get("url")

        for field in ("selector", "text", "url", "direction", "amount"):
            value = raw_action.get(field)
            if value not in (None, ""):
                payload[field] = value

        if raw_action.get("reasoning"):
            payload["reasoning"] = raw_action["reasoning"]

        signature = (
            payload.get("type"),
            payload.get("selector"),
            payload.get("text"),
            payload.get("url")
        )

        if signature in seen_signatures:
            continue

        seen_signatures.add(signature)
        structured_actions.append(payload)

    return structured_actions


__all__ = ["assemble_structured_actions", "set_default_action_parser", "get_default_action_parser"]
