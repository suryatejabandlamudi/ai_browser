import unittest

from .support import ensure_test_stubs

ensure_test_stubs()

from ..browser_agent import BrowserAgent


class BrowserAgentWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_and_execute_workflow(self):
        agent = BrowserAgent()
        actions = [
            {"type": "navigate", "parameters": {"url": "https://example.com"}},
            {"type": "click", "parameters": {"target": "submit"}},
        ]

        workflow_id = await agent.create_workflow(
            name="smoke",
            actions=actions,
            user_intent="test",
            page_url="https://example.com"
        )

        pre_status = agent.get_workflow_status(workflow_id)
        self.assertTrue(pre_status["success"])
        self.assertEqual(pre_status["data"]["status"], "pending")
        self.assertEqual(len(pre_status["data"]["steps"]), len(actions))

        execution = await agent.execute_workflow(workflow_id)
        self.assertTrue(execution["success"])
        self.assertEqual(execution["data"]["status"], "completed")
        self.assertEqual(execution["data"]["steps_completed"], len(actions))

        history_entry = next((w for w in agent.workflow_history if w.id == workflow_id), None)
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.status, "completed")

    async def test_pause_and_resume_workflow(self):
        agent = BrowserAgent()
        actions = [
            {"type": "navigate", "parameters": {"url": "https://example.com"}},
        ]

        workflow_id = await agent.create_workflow(
            name="pause-test",
            actions=actions
        )

        pause_result = agent.pause_workflow(workflow_id)
        self.assertTrue(pause_result["success"])
        self.assertEqual(pause_result["data"]["status"], "paused")

        resume_result = agent.resume_workflow(workflow_id)
        self.assertTrue(resume_result["success"])
        self.assertEqual(resume_result["data"]["status"], "executing")

    async def test_get_workflow_status_unknown_workflow(self):
        agent = BrowserAgent()
        status = agent.get_workflow_status("missing")
        self.assertFalse(status["success"])
        self.assertIsNone(status["data"])


if __name__ == "__main__":
    unittest.main()
