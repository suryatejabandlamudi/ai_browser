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
- Development environment with conda, Python 3.13
- Ollama + GPT-OSS 20B model installed and tested
- FastAPI backend with AI client, browser agent, content extractor
- Comprehensive architecture documentation
- BrowserOS study completed - learned their patch-based approach
- depot_tools installed for Chromium development
- Browser extension prototype (for testing only)

### 🔄 Currently In Progress  
- Chromium source checkout (started, ~32GB downloaded so far)
- This is a long-running background process (4-6 hours total)

### 📋 Next Steps
1. Complete Chromium source checkout
2. Study BrowserOS patches in detail
3. Create custom patches for our GPT-OSS integration
4. Build custom Chromium browser with AI sidebar
5. Test end-to-end AI browser workflows

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
1. **Use BrowserOS patches as reference** - don't reinvent the wheel
2. **Replace their AI backends** with our Ollama + GPT-OSS integration
3. **Simplify initially** - start with basic chat, add features incrementally
4. **Local-first design** - no cloud API calls, everything local

## Directory Structure

```
ai_browser/
├── ARCHITECTURE.md         # System design (REAL BROWSER focus)
├── DEVELOPMENT_PLAN.md     # Implementation timeline
├── CLAUDE.md              # This guidance file
├── STATUS.md              # Current progress
├── backend/               # FastAPI + AI integration
│   ├── main.py           # FastAPI server
│   ├── ai_client.py      # Ollama GPT-OSS client
│   ├── browser_agent.py  # Browser automation logic
│   ├── content_extractor.py # Page content processing
│   ├── depot_tools/      # Chromium build tools (submodule)
│   ├── chromium/         # Chromium source (downloading...)
│   └── BrowserOS/        # BrowserOS reference (for patches)
├── extension/            # Browser extension (TESTING ONLY)
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

### Status Check Commands
```bash
# Check Chromium download progress
cd backend/chromium && du -sh .

# Check if download is complete (~55GB expected)
ls -la src/  # Should exist when complete

# Test our backend is working
cd ../.. && conda activate ai_browser_env && python -m backend.main
```

## Important Notes

- **Real Browser Goal**: Custom Chromium application, not Chrome extension
- **Local AI Only**: GPT-OSS 20B via Ollama, no cloud dependencies  
- **Reference Implementation**: BrowserOS patches provide the roadmap
- **Long Download**: Chromium source is ~55GB, takes 4-6 hours
- **Build Requirements**: Xcode, 16GB+ RAM, 100GB+ free disk space

Remember: We're building the next-generation privacy-first AI browser!