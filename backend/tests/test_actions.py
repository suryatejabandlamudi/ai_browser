import unittest

from .support import ensure_test_stubs

ensure_test_stubs()

from ..browser_agent import BrowserAgent
from ..action_pipeline import assemble_structured_actions, set_default_action_parser
from ..real_browser_agent import BeautifulSoup


class AssembleStructuredActionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent = BrowserAgent()
        set_default_action_parser(self.agent)
        self.sample_dom = """
            <html>
                <body>
                    <button id='login-btn' class='primary'>Login</button>
                    <form>
                        <input type='email' id='email-input' placeholder='Email address' />
                    </form>
                </body>
            </html>
        """

    async def asyncTearDown(self):
        set_default_action_parser(None)

    async def test_uses_real_browser_agent_execution(self):
        candidate_actions = [
            {
                "type": "click",
                "parameters": {"target": "login"},
                "reasoning": "Open the login flow"
            }
        ]

        results = await assemble_structured_actions(
            candidate_actions,
            ai_response_text="Click the login button",
            page_url="https://example.com",
            page_dom=self.sample_dom
        )

        self.assertTrue(results, "Expected at least one assembled action")
        action = results[0]
        self.assertEqual(action["type"], "CLICK")
        self.assertTrue(action["executable"])
        self.assertTrue(action.get("selector"))
        if BeautifulSoup:  # DOM-aware path uses bs4 for precise selector
            self.assertEqual(action.get("selector"), "#login-btn")
        self.assertEqual(action.get("reasoning"), "Open the login flow")

    async def test_parses_actions_when_none_supplied(self):
        response_text = "Please click the 'Sign In' button and then navigate to https://example.com/dashboard"

        results = await assemble_structured_actions(
            candidate_actions=None,
            ai_response_text=response_text,
            page_url="https://example.com",
            page_dom=self.sample_dom
        )

        action_types = {action["type"] for action in results}
        self.assertTrue({"CLICK", "NAVIGATE"} & action_types)
        self.assertTrue(
            any(action.get("selector") for action in results if action["type"] == "CLICK"),
            "Expected click actions to include a selector"
        )

    async def test_deduplicates_equivalent_entries(self):
        candidate_actions = [
            {"type": "click", "parameters": {"target": "submit"}},
            {"type": "CLICK", "parameters": {"target": "submit"}},
        ]

        results = await assemble_structured_actions(
            candidate_actions,
            ai_response_text="Click submit",
            page_url="https://example.com",
            page_dom=self.sample_dom
        )

        self.assertEqual(len(results), 1)
        action = results[0]
        self.assertEqual(action["type"], "CLICK")
        self.assertTrue(action.get("selector"))

    async def test_handles_empty_input(self):
        results = await assemble_structured_actions(
            candidate_actions=[],
            ai_response_text="No actionable instruction here.",
            page_url="https://example.com",
            page_dom=self.sample_dom
        )

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
