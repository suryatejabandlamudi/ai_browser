import unittest

from .support import ensure_test_stubs

ensure_test_stubs()

from backend.real_browser_agent import RealBrowserAgent, BeautifulSoup
from backend.action_pipeline import assemble_structured_actions, set_default_action_parser
from backend.browser_agent import BrowserAgent

import asyncio

try:
    import requests
except Exception:  # pragma: no cover - network-less environments
    requests = None


@unittest.skipUnless(requests is not None, "requests dependency unavailable")
class RealPageSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent = BrowserAgent()
        set_default_action_parser(self.agent)
        self.real_agent = RealBrowserAgent()

    async def asyncTearDown(self):
        set_default_action_parser(None)

    async def test_example_com_link_selector(self):
        try:
            resp = requests.get("https://example.com", timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - flaky network
            self.skipTest(f"Network request failed: {exc}")

        html = resp.text
        candidate_actions = [
            {
                "type": "click",
                "parameters": {"target": "More information link"},
                "reasoning": "Follow the documentation link"
            }
        ]

        results = await assemble_structured_actions(
            candidate_actions,
            ai_response_text="Click the more information link.",
            page_url="https://example.com",
            page_dom=html
        )

        self.assertTrue(results, "Expected at least one action for example.com")
        selector = results[0].get("selector")
        self.assertTrue(selector, "Selector should not be empty")
        if BeautifulSoup:
            self.assertIn("a", selector)

    async def test_httpbin_form_email_selector(self):
        try:
            resp = requests.get("https://httpbin.org/forms/post", timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - flaky network
            self.skipTest(f"Network request failed: {exc}")

        html = resp.text
        candidate_actions = [
            {
                "type": "type",
                "parameters": {"target": "email", "text": "test@example.com"},
                "reasoning": "Fill in the email field"
            }
        ]

        results = await assemble_structured_actions(
            candidate_actions,
            ai_response_text="Type the email address in the email field.",
            page_url="https://httpbin.org/forms/post",
            page_dom=html
        )

        self.assertTrue(results, "Expected type action for httpbin form")
        selector = results[0].get("selector")
        self.assertTrue(selector, "Selector should not be empty for form input")
        if BeautifulSoup:
            self.assertIn("input", selector)

    async def test_bootstrap_modal_button_selector(self):
        try:
            resp = requests.get("https://getbootstrap.com/docs/5.0/components/modal/", timeout=10)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - flaky network
            self.skipTest(f"Network request failed: {exc}")

        html = resp.text
        candidate_actions = [
            {
                "type": "click",
                "parameters": {"target": "Launch demo modal"},
                "reasoning": "Open the modal dialog"
            }
        ]

        results = await assemble_structured_actions(
            candidate_actions,
            ai_response_text="Click the Launch demo modal button.",
            page_url="https://getbootstrap.com/docs/5.0/components/modal/",
            page_dom=html
        )

        self.assertTrue(results, "Expected click action for bootstrap modal page")
        selector = results[0].get("selector")
        self.assertTrue(selector, "Selector should not be empty for modal button")
        if BeautifulSoup:
            self.assertIn("button", selector)


if __name__ == "__main__":
    unittest.main()
