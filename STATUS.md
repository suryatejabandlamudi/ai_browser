# Project Status

## Current Reality
- Backend chat endpoint returns text responses only; action parsing is deliberately disabled and workflow APIs still 501, so automation is not wired up (`backend/main.py:400`, `backend/main.py:650`).
- Browser agent generates generic selectors from keywords instead of inspecting the live DOM, making extension-executed actions unreliable (`backend/real_browser_agent.py:82-167`).
- Extension infers actions from free-form LLM text and depends on `/api/action`, which currently cannot bridge context, so side panel automation rarely succeeds (`extension/sidepanel.js:492-610`, `extension/background.js:86-149`).
- Custom Chromium build pipeline has never completed: patches fail, `gn` is missing, and build logs end with "Chrome binary not found" despite success banners (`logs/chromium_build.log:13`, `logs/chromium_build.log:49`, `logs/ai_browser_build.log:11495`).
- Repository contains compiled `__pycache__` files and large build logs under version control, and a partially-synced Chromium tree sits unstaged at `backend/chromium/build/src`.

## Pending Tasks (Next to Close)
| Priority | Area | Task | Evidence/Notes |
| --- | --- | --- | --- |
| P0 | Backend ↔ Extension | Reinstate structured action parsing and deliver executable steps to the extension instead of returning text-only chat responses. | `backend/main.py:400` comment removes action parsing; extension waits for `actions` list. |
| P0 | Backend Automation | Replace placeholder workflow endpoints with real orchestration or remove them until implemented to avoid 501 responses. | `backend/main.py:650-742`.
| P0 | Build System | Restore the Chromium toolchain (install `gn`/`autoninja`), fix the AI patch series, and prove a successful build before advertising a custom browser. | `logs/chromium_build.log`, `logs/ai_browser_build.log`.
| P1 | Automation Reliability | Give the browser agent real DOM grounding (page structure inspection or extension telemetry) instead of static selector heuristics. | `backend/real_browser_agent.py:82-167` relies on keyword guesses. |
| P1 | Extension UX | Stop guessing automation intents from prose; accept explicit tool responses or add UI affordances so users confirm before executing actions. | `extension/sidepanel.js:528-576`.
| P1 | Test Coverage | Add an end-to-end test (missing `test_ai_browser_integration.py`) that exercises chat, action routing, and extension messaging. | Referenced in docs/BUILD_GUIDE but absent in tree. |
| P1 | Documentation | Bring README/AI_BROWSER_READY in line with reality; they currently claim "100% working" despite disabled automation. | `AI_BROWSER_READY.md`, `README.md` statements vs code/logs. |
| P2 | Repo Hygiene | Purge tracked `__pycache__` directories, large log files, and add ignore rules so future commits stay clean. | `backend/__pycache__/...`, `logs/*.log` tracked in Git. |
| P2 | Build Scripts | Make launch scripts resilient (e.g., fix `while true do` syntax in `AI_BROWSER_FINAL.sh`) and ensure monitoring actually runs. | `AI_BROWSER_FINAL.sh:136`. |
| P2 | Dependency Handling | Document and validate optional modules (vector DB, multimodal); fail gracefully when extras are missing. | Imports guarded by `try/except` in `backend/main.py:38-86` currently just log warnings. |

## Immediate Next Steps
1. Align backend and extension by delivering actionable plans (P0).
2. Stabilize the build story or de-emphasize the Chromium fork until reproducible (P0).
3. Decide on automation UX approach, then backfill tests and docs accordingly (P1).

_Last updated: Sat Sep 20 19:46:59 PDT 2025_
