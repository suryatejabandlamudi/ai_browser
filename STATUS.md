# Project Status

## Current Reality
- Backend chat endpoints now emit structured action payloads backed by DOM-aware selector generation, reducing blind guesses; smoke tests across example.com/httpbin/bootstrap confirm selectors show up (`backend/action_pipeline.py:28`, `backend/real_browser_agent.py:48`, extension/sidepanel.js:195`).
- Browser agent generates generic selectors from keywords instead of inspecting the live DOM, making extension-executed actions unreliable (`backend/real_browser_agent.py:82-167`).
- Extension now prioritizes structured actions from the backend but still falls back to keyword inference when none are supplied, so non-grounded automation can leak through — real browser validation remains todo (`extension/sidepanel.js:277-563`).
- Custom Chromium build pipeline has never completed: patches fail, `gn` is missing, and build logs end with "Chrome binary not found" despite success banners (`logs/chromium_build.log:13`, `logs/chromium_build.log:49`, `logs/ai_browser_build.log:11495`).
- Repository contains compiled `__pycache__` files and large build logs under version control, and a partially-synced Chromium tree sits unstaged at `backend/chromium/build/src`.

## Pending Tasks (Next to Close)
| Priority | Area | Task | Evidence/Notes |
| --- | --- | --- | --- |
| P0 | Backend ↔ Extension | Run an end-to-end browser session (extension + backend) against dynamic sites to verify selectors and feed findings back into DOM extraction. | `backend/tests/test_smoke_real_page.py`, `extension/sidepanel.js:439`.
| P0 | Backend Automation | Replace inline stubs with FastAPI `TestClient` fixtures in the integration suite so we exercise response serialization and metadata handling. | `backend/tests/factories.py`, `backend/tests/test_integration_chat.py`.
| P0 | Build System | Restore the Chromium toolchain (install `gn`/`autoninja`), fix the AI patch series, and prove a successful build before advertising a custom browser. | `logs/chromium_build.log`, `logs/ai_browser_build.log`.
| P1 | Automation Reliability | Give the browser agent real DOM grounding (page structure inspection or extension telemetry) instead of static selector heuristics. | `backend/real_browser_agent.py:82-167` relies on keyword guesses. |
| P1 | Extension UX | Stop guessing automation intents from prose; accept explicit tool responses or add UI affordances so users confirm before executing actions. | `extension/sidepanel.js:528-576`.
| P1 | Test Coverage | Add an end-to-end test (missing `test_ai_browser_integration.py`) that exercises chat, action routing, and extension messaging. | Referenced in docs/BUILD_GUIDE but absent in tree. |
| P1 | Documentation | Bring README/AI_BROWSER_READY in line with reality; they currently claim "100% working" despite disabled automation. | `AI_BROWSER_READY.md`, `README.md` statements vs code/logs. |
| P2 | Repo Hygiene | Purge tracked `__pycache__` directories, large log files, and add ignore rules so future commits stay clean. | `backend/__pycache__/...`, `logs/*.log` tracked in Git. |
| P2 | Build Scripts | Make launch scripts resilient (e.g., fix `while true do` syntax in `AI_BROWSER_FINAL.sh`) and ensure monitoring actually runs. | `AI_BROWSER_FINAL.sh:136`. |
| P2 | Dependency Handling | Document and validate optional modules (vector DB, multimodal); fail gracefully when extras are missing. | Imports guarded by `try/except` in `backend/main.py:38-86` currently just log warnings. |

## Immediate Next Steps
1. Dry-run extension automation against a representative site to verify selectors and fill any gaps surfaced by the new tests (P0).
2. Stabilize the build story or de-emphasize the Chromium fork until reproducible (P0).
3. Decide on automation UX approach, then backfill tests and docs accordingly (P1).

_Last updated: Sun Sep 21 08:45:29  2025
