"""
Real Browser Agent - Generates executable actions for the Chrome extension.
"""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

try:  # Optional dependency used for DOM-aware selector generation
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover - exercised only when bs4 missing
    BeautifulSoup = None

DOM_STOP_WORDS = {
    'button', 'link', 'field', 'input', 'click', 'type', 'the', 'a', 'an',
    'please', 'press', 'submit', 'navigate', 'scroll', 'and', 'to', 'box'
}


class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    WAIT = "wait"


class RealBrowserAgent:
    """Browser agent that generates executable browser actions for the extension."""

    def __init__(self) -> None:
        self.action_handlers = {
            ActionType.CLICK.value: self._handle_click,
            ActionType.TYPE.value: self._handle_type,
            ActionType.NAVIGATE.value: self._handle_navigate,
            ActionType.SCROLL.value: self._handle_scroll,
            ActionType.WAIT.value: self._handle_wait,
        }

    async def execute_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an executable action payload for the Chrome extension."""
        try:
            logger.info(
                "Preparing real browser action",
                action_type=action_type,
                parameters=parameters,
                url=page_url,
                has_dom=bool(page_dom),
            )

            if action_type not in self.action_handlers:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}",
                    "data": None,
                }

            handler = self.action_handlers[action_type]
            result = await handler(parameters, page_url, page_dom)

            logger.info(
                "Real action prepared",
                action_type=action_type,
                success=result.get("success", False),
                executable=result.get("data", {}).get("executable", False),
            )
            return result

        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.error("Real action preparation failed", action_type=action_type, error=str(exc))
            return {
                "success": False,
                "message": f"Action preparation failed: {exc}",
                "data": None,
            }

    async def _handle_click(
        self,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str],
    ) -> Dict[str, Any]:
        target = parameters.get("target", "")
        if not target:
            return {
                "success": False,
                "message": "No target specified for click action",
                "data": None,
            }

        selector, analysis = self._find_element_selector(target, page_dom)
        if not selector:
            return {
                "success": False,
                "message": "Unable to locate target element for click",
                "data": {
                    "type": "CLICK",
                    "target_description": target,
                    "executable": False,
                    "analysis": analysis,
                },
            }

        return {
            "success": True,
            "message": f"Real click action ready for: {target}",
            "data": {
                "type": "CLICK",
                "selector": selector,
                "target_description": target,
                "executable": True,
                "analysis": analysis,
                "action_id": f"click_{hash(selector)}_{int(asyncio.get_event_loop().time())}",
            },
        }

    async def _handle_type(
        self,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str],
    ) -> Dict[str, Any]:
        text = parameters.get("text", "")
        target = parameters.get("target", "")

        if not text:
            return {
                "success": False,
                "message": "No text specified for type action",
                "data": None,
            }

        selector, analysis = self._find_input_selector(target, page_dom)
        if not selector:
            return {
                "success": False,
                "message": "Unable to locate input field for typing",
                "data": {
                    "type": "TYPE",
                    "target_description": target,
                    "text": text,
                    "executable": False,
                    "analysis": analysis,
                },
            }

        return {
            "success": True,
            "message": f"Real type action ready: '{text}'",
            "data": {
                "type": "TYPE",
                "selector": selector,
                "text": text,
                "target_description": target,
                "executable": True,
                "analysis": analysis,
                "action_id": f"type_{hash(selector + text)}_{int(asyncio.get_event_loop().time())}",
            },
        }

    async def _handle_navigate(
        self,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str],
    ) -> Dict[str, Any]:
        url = parameters.get("url", "")
        if not url:
            return {
                "success": False,
                "message": "No URL specified for navigate action",
                "data": None,
            }

        if not url.startswith(("http://", "https://")):
            if url.startswith("//"):
                url = "https:" + url
            elif not url.startswith("/"):
                url = "https://" + url

        return {
            "success": True,
            "message": f"Real navigation action ready: {url}",
            "data": {
                "type": "NAVIGATE",
                "url": url,
                "executable": True,
                "analysis": {"strategy": "normalize_url", "confidence": 0.9},
                "action_id": f"nav_{hash(url)}_{int(asyncio.get_event_loop().time())}",
            },
        }

    async def _handle_scroll(
        self,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str],
    ) -> Dict[str, Any]:
        direction = parameters.get("direction", "down")
        amount = parameters.get("amount", 500)

        return {
            "success": True,
            "message": f"Real scroll action ready: {direction} by {amount}px",
            "data": {
                "type": "SCROLL",
                "direction": direction,
                "amount": amount,
                "executable": True,
                "analysis": {"strategy": "scroll", "confidence": 0.6},
                "action_id": f"scroll_{direction}_{int(asyncio.get_event_loop().time())}",
            },
        }

    async def _handle_wait(
        self,
        parameters: Dict[str, Any],
        page_url: str,
        page_dom: Optional[str],
    ) -> Dict[str, Any]:
        duration = parameters.get("duration", 1000)
        return {
            "success": True,
            "message": f"Real wait action ready: {duration}ms",
            "data": {
                "type": "WAIT",
                "duration": duration,
                "executable": True,
                "analysis": {"strategy": "wait", "confidence": 0.5},
                "action_id": f"wait_{duration}_{int(asyncio.get_event_loop().time())}",
            },
        }

    # ------------------------------------------------------------------
    # Selector helpers
    # ------------------------------------------------------------------

    def _find_element_selector(
        self,
        target: str,
        page_dom: Optional[str],
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        if page_dom and BeautifulSoup:
            selector, metadata = self._find_selector_from_dom(
                target,
                page_dom,
                candidate_tags=("button", "a", "input", "div", "span"),
                preferred_roles={"button", "link"},
            )
            if selector:
                return selector, metadata
        elif page_dom and not BeautifulSoup:
            logger.debug("bs4 not available; using heuristic click selector", target=target)

        selector = self._legacy_click_selector(target)
        return selector, {"strategy": "heuristic", "confidence": 0.3, "keywords": self._keywords(target)}

    def _find_input_selector(
        self,
        target: str,
        page_dom: Optional[str],
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        if page_dom and BeautifulSoup:
            selector, metadata = self._find_selector_from_dom(
                target,
                page_dom,
                candidate_tags=("input", "textarea", "select"),
                preferred_roles={"textbox", "combobox", "searchbox"},
            )
            if selector:
                return selector, metadata
        elif page_dom and not BeautifulSoup:
            logger.debug("bs4 not available; using heuristic input selector", target=target)

        selector = self._legacy_input_selector(target)
        return selector, {"strategy": "heuristic", "confidence": 0.25, "keywords": self._keywords(target)}

    def _find_selector_from_dom(
        self,
        target: str,
        page_dom: str,
        *,
        candidate_tags: Tuple[str, ...],
        preferred_roles: Optional[set] = None,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        if not BeautifulSoup:
            return None, {"strategy": "dom", "confidence": 0.0, "reason": "bs4_missing"}

        soup = BeautifulSoup(page_dom, "html.parser")
        keywords = self._keywords(target)
        if not keywords:
            return None, {"strategy": "dom", "confidence": 0.0, "reason": "no_keywords"}

        best_element = None
        best_score = 0.0
        best_details: Dict[str, Any] = {}

        for element in soup.find_all(candidate_tags):
            score, details = self._score_element(element, keywords, preferred_roles)
            if score > best_score:
                best_score = score
                best_element = element
                best_details = details

        if not best_element or best_score <= 0:
            return None, {
                "strategy": "dom",
                "confidence": 0.0,
                "keywords": keywords,
                "reason": "no_match",
            }

        selector = self._build_css_selector(best_element)
        if not selector:
            return None, {
                "strategy": "dom",
                "confidence": 0.0,
                "keywords": keywords,
                "reason": "no_selector",
            }

        metadata = {
            "strategy": "dom",
            "confidence": min(0.95, 0.4 + (best_score / (len(keywords) or 1)) * 0.2),
            "matched_text": best_details.get("matched_text"),
            "matched_attributes": best_details.get("matched_attributes"),
            "tag": best_element.name,
            "id": best_element.get("id"),
            "classes": best_element.get("class"),
        }
        return selector, metadata

    def _score_element(
        self,
        element,
        keywords: List[str],
        preferred_roles: Optional[set],
    ) -> Tuple[float, Dict[str, Any]]:
        score = 0.0
        matched_attrs: Dict[str, str] = {}

        text = (element.get_text(strip=True) or "").lower()
        attrs = {
            "aria-label": (element.get("aria-label") or "").lower(),
            "title": (element.get("title") or "").lower(),
            "placeholder": (element.get("placeholder") or "").lower(),
            "value": (element.get("value") or "").lower(),
            "name": (element.get("name") or "").lower(),
            "id": (element.get("id") or "").lower(),
            "data-testid": (element.get("data-testid") or "").lower(),
            "href": (element.get("href") or "").lower(),
            "type": (element.get("type") or "").lower(),
        }
        classes = [cls.lower() for cls in element.get("class", []) if isinstance(cls, str)]

        role = element.get("role")
        if preferred_roles and role and role.lower() in preferred_roles:
            score += 2.0
            matched_attrs["role"] = role

        for keyword in keywords:
            if keyword in text:
                score += 3.0
                matched_attrs["text"] = text[:120]

            for attr_name, attr_value in attrs.items():
                if keyword and attr_value and keyword in attr_value:
                    score += 2.5
                    matched_attrs[attr_name] = attr_value[:120]

            for cls in classes:
                if keyword in cls:
                    score += 1.5
                    matched_attrs.setdefault("class", cls)

        if element.name in {"button", "a", "input"}:
            score += 0.5

        if element.name == "input" and attrs.get("type") in {"submit", "button"}:
            score += 1.0

        details = {
            "matched_attributes": matched_attrs,
            "matched_text": text[:120] if text else None,
        }
        return score, details

    def _build_css_selector(self, element) -> Optional[str]:
        tag = element.name or "div"

        def valid(value: Optional[str]) -> bool:
            return bool(value and all(ch not in value for ch in ('"', "'", "\n")))

        element_id = element.get("id")
        if valid(element_id):
            return f"#{element_id}"

        for attr in ("data-testid", "data-test", "aria-label", "name", "title", "value"):
            attr_value = element.get(attr)
            if valid(attr_value):
                return f"{tag}[{attr}='{attr_value}']"

        classes = [cls for cls in element.get("class", []) if isinstance(cls, str) and cls and cls.isidentifier()]
        if classes:
            return f"{tag}." + ".".join(classes[:3])

        if tag == "input" and valid(element.get("type")):
            return f"input[type='{element['type']}']"

        if tag == "a" and element.get("href"):
            return "a[href]"

        return tag

    def _legacy_click_selector(self, target: str) -> str:
        target_lower = target.lower()
        if "login" in target_lower:
            return "button[id*='login'], button[name*='login'], [data-testid*='login'], [aria-label*='login'], a[href*='login']"
        if "search" in target_lower:
            return "button[type='submit'], input[type='submit'], [aria-label*='search'], button[class*='search'], [data-testid*='search']"
        if "submit" in target_lower:
            return "button[type='submit'], input[type='submit'], [aria-label*='submit'], [data-testid*='submit']"
        if "next" in target_lower:
            return "button[class*='next'], [aria-label*='next'], [data-testid*='next']"
        return "button, a, [role='button'], [onclick], [data-action], [data-testid]"

    def _legacy_input_selector(self, target: str) -> str:
        target_lower = target.lower()
        if "email" in target_lower:
            return "input[type='email'], input[name*='email'], input[aria-label*='email'], input[placeholder*='email'], #email, .email"
        if "password" in target_lower:
            return "input[type='password'], input[name*='password'], input[aria-label*='password'], input[placeholder*='password'], #password"
        if "search" in target_lower:
            return "input[type='search'], input[name*='search'], input[placeholder*='search'], #search, .search-field, [role='searchbox']"
        if "username" in target_lower or "user" in target_lower:
            return "input[name*='user'], input[placeholder*='user'], #username, .username"
        if "phone" in target_lower or "tel" in target_lower:
            return "input[type='tel'], input[name*='phone'], input[placeholder*='phone'], #phone, .phone-field"
        if "message" in target_lower or "comment" in target_lower:
            return "textarea, input[name*='message'], input[placeholder*='message'], #message, .message-field, [role='textbox']"
        clean_target = target.replace(' ', '_').lower()
        return f"input[name*='{clean_target}'], input[placeholder*='{clean_target}'], textarea[name*='{clean_target}'], [data-testid*='{clean_target}']"

    def _keywords(self, phrase: str) -> List[str]:
        candidates: List[str] = []
        for raw in phrase.lower().replace('-', ' ').split():
            stripped = ''.join(ch for ch in raw if ch.isalnum())
            if not stripped or stripped in DOM_STOP_WORDS:
                continue
            candidates.append(stripped)
        return candidates or [phrase.lower().strip()]


# Global instance
real_browser_agent = RealBrowserAgent()
