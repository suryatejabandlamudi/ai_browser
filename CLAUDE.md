# CLAUDE.md - AI Browser Project Guidance

This file provides guidance to Claude Code when working with this AI browser project.

## Project Overview

**IMPORTANT**: This project is building a **real AI browser** (custom Chromium fork), not just a browser extension. The browser extension in `/extension/` was created for testing and learning purposes only.

### Core Objective
Build a privacy-first AI browser similar to Perplexity Comet but using local LLMs instead of cloud services:
- **Real Browser**: Custom Chromium fork with native AI integration
- **Local AI**: GPT-OSS 20B running via Ollama (no cloud dependencies)
- **Privacy-First**: All AI processing happens locally on user's machine
- **Agent-Driven**: AI can read pages, understand content, and perform browser actions

### Technical Approach
Following BrowserOS methodology:
1. **Chromium Source**: Download and build custom Chromium (~55GB, 4-6 hours)
2. **Patch System**: Apply patches to Chromium source (like BrowserOS does)
3. **AI Integration**: Connect to local FastAPI backend with GPT-OSS 20B
4. **Native APIs**: Add browser APIs for AI page interaction
5. **Sidebar UI**: Built-in AI chat interface in browser

## Current Project Status

### ✅ Completed Foundation  
- **Development Environment**: Conda environment `ai_browser_env` with Python 3.13
- **AI Integration**: Ollama + GPT-OSS 20B model **VERIFIED WORKING** 
- **Backend Systems**: Complete FastAPI server with 25+ API endpoints **FUNCTIONAL**
- **Core Components**: All major systems implemented and tested
- **Browser Extension**: Chrome extension prototype with AI integration **WORKING**
- **Architecture Analysis**: BrowserOS study completed, insights integrated
- **Documentation**: Complete setup guides (SETUP.md, ARCHITECTURE_UPDATE.md)

### ✅ Major Features Implemented (Recent Session)
- **Advanced Task Classification** (`task_classifier.py`) - Intent analysis with complexity detection
- **Visual Element Highlighting** (`visual_highlighter.py`) - DOM overlay system with CSS-based highlighting  
- **Intelligent Form Processing** (`form_intelligence.py`) - AI-powered form analysis and auto-fill
- **Cross-Tab Context Memory** (`context_memory.py`) - SQLite-based persistent memory system
- **Screenshot & OCR Integration** (`visual_processor.py`) - Multi-engine OCR support
- **Enhanced Browser Automation** (`browser_agent.py`) - Multi-step workflows with validation
- **Comprehensive API Layer** (`main.py`) - RESTful + WebSocket endpoints for all functionality
- **Structured Tool System** (`tools/`) - 33+ browser automation tools with proper orchestration

### 🔄 Current Technical Status (VERIFIED)
**✅ Working Systems**:
- FastAPI server starts successfully on http://127.0.0.1:8000
- Ollama integration **CONFIRMED WORKING** with GPT-OSS 20B (tested)
- All core modules import and instantiate correctly  
- Chrome extension loads and can communicate with backend
- Health check endpoint returns full system status
- AI chat endpoint responds with GPT-OSS 20B

**✅ Dependencies Installed**:
```bash
# Core dependencies working:
aiosqlite==0.21.0, beautifulsoup4==4.13.4, readability-lxml==0.8.4.1
fastapi, uvicorn, aiohttp, structlog, pydantic, websockets
```

**⚠️ Needs Integration Testing**:
- End-to-end: Extension → Backend → AI → Browser action flow
- Multi-step task execution with actual page interaction
- Real-world form filling and automation workflows
- Cross-tab memory persistence across sessions
- Error recovery and retry mechanisms in practice

### 📋 Immediate Next Steps (High Priority)
1. **Test Complete Integration** - Load extension, test full AI→Browser automation
2. **Verify Real Page Interaction** - Clicking, typing, form filling on live sites
3. **Test Multi-Step Workflows** - Complex task execution with error handling
4. **Performance Validation** - Response times, memory usage, model inference speed
5. **Extension→Backend Communication** - WebSocket streaming, real-time updates

### 📋 Phase 2: Production Readiness  
1. **ReAct Agent Orchestration** - Implement full Reason→Act→Observe loops
2. **Chromium Fork Migration** - Move from extension to native browser integration  
3. **BrowserOS-Style Patches** - Apply custom patches for deep AI integration
4. **Production Packaging** - Standalone application with installer

## Key Learnings from BrowserOS Analysis

### Architecture Insights
- **Dual Approach**: BrowserOS uses Chromium patches + browser extension
- **Patch System**: They modify Chromium source with ~30 patch files
- **Extension Integration**: Built-in extension provides AI functionality
- **API Layer**: Custom browserOS APIs for page interaction
- **Side Panel**: Native sidebar for AI chat interface

### Critical Files in BrowserOS
- `patches/nxtscape/browserOS-API.patch` - Main API additions (760+ lines)
- `patches/nxtscape/ai-chat-extension.patch` - Extension integration
- `patches/nxtscape/embed-third-party-llm-in-side-panel.patch` - UI integration
- `resources/files/ai_side_panel/` - Extension files
- `build/build.py` - Build automation

### Our Adaptation Strategy  
1. **Use BrowserOS agent architecture** - Adopt their sophisticated tool system and planning approach
2. **Replace cloud LLMs** with our local GPT-OSS 20B integration  
3. **Implement critical missing features** - See FEATURE_IMPLEMENTATION_PLAN.md for complete list
4. **Local-first design** - All AI processing stays on user's machine
5. **Better than cloud solutions** - No subscription fees, complete privacy, Apple Silicon optimization

### 🚨 CRITICAL DISCOVERY - Missing Features
**Our current extension is very basic compared to real AI browsers like BrowserOS and Comet.**

**What We Have**: Basic chat, simple actions, content extraction  
**What We Need**: Task classification, multi-step planning, streaming responses, accessibility tree integration, visual element highlighting, form intelligence, cross-tab memory, action validation, error recovery

**See FEATURE_IMPLEMENTATION_PLAN.md for comprehensive feature breakdown and implementation timeline.**

## Directory Structure (CURRENT)

```
ai_browser/
├── SETUP.md                    # Complete setup guide (CREATED)
├── ARCHITECTURE_UPDATE.md     # Enhanced architecture analysis (CREATED)  
├── FEATURE_IMPLEMENTATION_PLAN.md # Feature tracking with BrowserOS insights
├── CLAUDE.md                   # This guidance file (UPDATED)
├── backend/                    # FastAPI + AI integration (WORKING)
│   ├── main.py                 # FastAPI server (25+ endpoints, FUNCTIONAL)
│   ├── ai_client.py           # Ollama GPT-OSS client (TESTED)
│   ├── browser_agent.py       # Enhanced browser automation (WORKFLOWS)
│   ├── task_classifier.py     # Advanced task analysis (NEW)
│   ├── visual_highlighter.py  # DOM highlighting system (NEW)
│   ├── form_intelligence.py   # Form processing AI (NEW)
│   ├── context_memory.py      # Cross-tab memory (NEW)
│   ├── visual_processor.py    # Screenshots/OCR (NEW)
│   ├── accessibility_tree.py  # DOM semantic analysis (NEW)
│   ├── structured_agent.py    # Advanced agent orchestration (NEW)
│   ├── browser_agent_enhanced.py # Enhanced automation (NEW)
│   ├── content_extractor.py   # Page content processing (WORKING)
│   ├── content_extractor_minimal.py # Fallback extractor (NEW)
│   ├── tools/                 # Structured tool system (33+ tools)
│   │   ├── base_tool.py       # Tool interface
│   │   ├── navigation_tool.py # Navigation actions  
│   │   ├── interaction_tool.py # Click, type, form filling
│   │   ├── extraction_tool.py  # Content extraction
│   │   ├── visual_tool.py     # Visual processing
│   │   ├── accessibility_tool.py # Accessibility integration
│   │   └── wait_tool.py       # Timing and wait operations
│   ├── depot_tools/           # Chromium build tools
│   └── chromium/              # Chromium source (partial download)
├── extension/                 # Chrome extension (TESTING)
│   ├── manifest.json          # Extension config
│   ├── sidepanel.html         # AI chat interface
│   ├── sidepanel.js           # Frontend logic
│   ├── content.js             # Page interaction
│   ├── accessibility.js       # Accessibility integration (NEW)
│   └── background.js          # Extension background
└── README.md
```

## Development Rules

### Critical Guidelines
1. **Focus on REAL BROWSER** - not extension development
2. **Wait for Chromium source** - can't proceed with browser patches until download completes
3. **Study BrowserOS patches** - learn from their implementation
4. **Local-first everything** - no cloud dependencies
5. **Document progress** - update STATUS.md and push code regularly

### What NOT to do
- Don't spend time on browser extension features (it's just for testing)
- Don't implement cloud AI integrations
- Don't proceed with Chromium patches until source download is complete
- Don't create new architecture - follow the BrowserOS approach

### Development Workflow
1. **Work on backend/AI integration** while Chromium downloads
2. **Study BrowserOS patches** in detail
3. **Plan patch modifications** for our GPT-OSS integration  
4. **Test with extension** for rapid prototyping
5. **Apply to Chromium** once source is ready

## Technical Stack (REAL BROWSER)

### Browser Core
- **Base**: Chromium (latest stable, ~55GB source)
- **Patches**: Custom patches (based on BrowserOS approach)
- **Build**: depot_tools + GN + Ninja
- **Platform**: macOS (Apple Silicon optimized)

### AI Integration  
- **Model**: GPT-OSS 20B via Ollama (local)
- **Backend**: Python FastAPI (already built)
- **APIs**: Custom Chromium APIs for page access
- **UI**: Native sidebar (built into browser)

### Key Differences from BrowserOS
- **Local LLM**: Ollama instead of cloud APIs
- **Model**: GPT-OSS 20B instead of OpenAI/Claude
- **Privacy**: 100% local processing
- **Integration**: Direct FastAPI backend connection

## Error Prevention

### Common Mistakes to Avoid
1. **Confusing extension with real browser** - extension is just for testing
2. **Proceeding without Chromium source** - can't patch what we don't have
3. **Ignoring BrowserOS patches** - they solved the integration challenges
4. **Cloud AI integration** - everything must be local
5. **Not documenting progress** - update files and push regularly

### Success Metrics
- [ ] Chromium source fully downloaded and buildable
- [ ] Custom patches applied successfully  
- [ ] AI sidebar appears in custom browser
- [ ] GPT-OSS responds via browser interface
- [ ] Page content extraction working
- [ ] Basic browser automation functional

## Next Session Preparation

### Before Next Session
1. **Let Chromium download complete** (check `backend/chromium/` size ~55GB)
2. **Have fast internet** for any additional downloads
3. **Ensure system can compile** (16GB+ RAM, Xcode tools)
4. **Study BrowserOS patches** if time permits

### Status Check Commands (UPDATED)
```bash
# Activate environment
conda activate ai_browser_env

# Check system status
cd /Users/suryatejabandlamudi/personal_projects/apple/ai_browser/backend

# Test backend server (WORKING)
python main.py  # Should start on http://127.0.0.1:8000

# Test AI integration (VERIFIED WORKING) 
curl http://localhost:11434/api/tags  # Should show gpt-oss:20b model

# Health check (FUNCTIONAL)
curl http://localhost:8000/health  # Should return all systems status

# Test AI chat (WORKING)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test message"}'

# Check Chromium download progress (if running)
cd chromium && du -sh .  # Current status varies
```

## Important Notes

- **Real Browser Goal**: Custom Chromium application, not Chrome extension
- **Local AI Only**: GPT-OSS 20B via Ollama, no cloud dependencies  
- **Reference Implementation**: BrowserOS patches provide the roadmap
- **Long Download**: Chromium source is ~55GB, takes 4-6 hours
- **Build Requirements**: Xcode, 16GB+ RAM, 100GB+ free disk space

Remember: We're building the next-generation privacy-first AI browser!