import unittest

from .support import ensure_test_stubs

ensure_test_stubs()

from .factories import patch_backend_dependencies

try:
    from backend import main  # type: ignore
except ImportError:
    main = None

FASTAPI_AVAILABLE = main is not None


@unittest.skipUnless('FASTAPI_AVAILABLE' in globals() and FASTAPI_AVAILABLE, "FastAPI not installed")
class ChatEndpointTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._patch_ctx = patch_backend_dependencies(main)
        await self._patch_ctx.__aenter__()

    async def asyncTearDown(self):
        await self._patch_ctx.__aexit__(None, None, None)

    async def test_chat_returns_structured_actions_with_dom(self):
        sample_dom = """
            <html>
                <body>
                    <button id='login-btn' class='primary'>Login</button>
                </body>
            </html>
        """

        request = main.ChatRequest(
            message="log me in",
            page_url="https://example.com",
            page_content=sample_dom
        )

        response = await main.chat_with_ai(request)

        self.assertTrue(response.actions, "Expected actions from chat endpoint")
        action = response.actions[0]
        self.assertEqual(action["type"], "CLICK")
        self.assertTrue(action.get("selector"))

    async def test_chat_without_dom_still_returns_text(self):
        request = main.ChatRequest(
            message="just talk",
            page_url="https://example.com",
            page_content=None
        )

        response = await main.chat_with_ai(request)
        self.assertIsInstance(response.response, str)


if __name__ == "__main__":
    unittest.main()
