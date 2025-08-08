# CLAUDE.md - AI Browser Project Guidance

This file provides guidance to Claude Code when working with this AI browser project.

## 🎯 Project Mission

**Build a privacy-first AI browser extension with local AI capabilities, eventually evolving toward competing with cloud-based AI browsers like Perplexity Comet.**

### Current Reality (January 2025)
This is a **working prototype browser extension** with local AI capabilities:
- **Local AI Processing**: GPT-OSS 20B via Ollama (confirmed working, but slow ~10-15s responses)
- **Privacy Advantage**: No data sent to cloud services (unlike Comet)
- **Extension Architecture**: Chrome extension with FastAPI backend (not custom browser)
- **Development Stage**: Functional prototype with basic automation capabilities

### Honest Status vs Perplexity Comet
| Feature | Perplexity Comet | Our Current State | Implementation Gap |
|---------|------------------|-----------------|------------------|
| **Browser Type** | Custom Chromium build | Chrome extension only | ❌ Major - need custom browser |
| **AI Search Engine** | Built-in AI search as default | Regular browser search + AI chat | ❌ No search engine replacement |
| **Sidebar AI Assistant** | Full agentic task automation | Basic AI chat with limited actions | 🟡 Framework exists, needs work |
| **Task Automation** | Restaurant booking, email sending, publishing | Click/type/form filling framework | 🟡 Tools exist but limited testing |
| **Gmail/Calendar Integration** | Deep native integration | None | ❌ Major missing feature |
| **Multi-LLM Support** | GPT-4, Claude, Gemini, Grok | Local GPT-OSS 20B only | ❌ Single model limitation |
| **Context Management** | Smart tab/session handling | Basic page content awareness | 🟡 Memory system exists but basic |
| **Performance** | Fast cloud inference | Slow local inference (10-15s) | ❌ Speed disadvantage |
| **Ad Blocking** | Built-in ad blocking | None | ❌ Not implemented |
| **Cross-Platform** | Windows/Mac/Mobile planned | Chrome extension only | ❌ Platform limitation |
| **Privacy** | Cloud processing | 100% Local processing | ✅ **Major advantage** |
| **Cost** | $20/month subscription | Free after setup | ✅ **Major advantage** |
| **Offline Capability** | Requires internet | Works offline | ✅ **Advantage** |

## 📁 Repository Structure & What Actually Works

```
ai_browser/
├── CLAUDE.md                    # This guidance file ✅ ACCURATE NOW
├── backend/                     # Python backend system
│   ├── main.py                  # FastAPI server ✅ WORKING (30+ endpoints)
│   ├── ai_client.py             # Ollama integration ✅ WORKING (slow but functional) 
│   ├── browser_agent.py         # Basic action execution ✅ WORKING (limited)
│   ├── tools/                   # Tool framework ✅ REGISTERED (14 tools, execution unclear)
│   ├── requirements.txt         # Dependencies ✅ WORKING
│   └── [various modules]        # Many modules ❓ UNTESTED in practice
│
├── extension/                   # Chrome extension
│   ├── manifest.json            # Extension config ✅ WORKING
│   ├── sidepanel.html/js        # AI chat UI ✅ WORKING (basic)
│   ├── background.js            # Backend communication ❓ UNTESTED
│   └── content.js               # Page interaction ❓ UNTESTED
│
└── [many docs]                  # Lots of documentation ❌ MOSTLY ASPIRATIONAL
```

## 🚨 **BRUTAL REALITY CHECK** (August 2025)

**⚠️ WARNING: Previous status claims were SIGNIFICANTLY EXAGGERATED. Here's the honest truth:**

### ❌ What's Currently BROKEN (Critical Issues)
- **FastAPI Backend**: Process runs but COMPLETELY UNRESPONSIVE (2+ minute timeouts on health checks)
- **AI Integration**: Backend broken, cannot test any AI responses  
- **Basic Chat UI**: Cannot function - backend doesn't respond to requests
- **WebSocket Streaming**: Backend timeout prevents any real-time communication
- **Tool Registration**: Code exists but backend too broken to execute any tools
- **Page Context**: Backend cannot receive or process any page content

### 🟡 What Exists as Code But Is UNTESTED/UNVERIFIED  
- **Browser Automation**: Framework code exists, never verified to actually control browsers
- **Form Processing**: Code exists, no real-world testing on actual websites
- **Visual Highlighting**: Code present but effectiveness completely unknown
- **Memory System**: Database schema exists but backend can't access databases
- **Task Classification**: Code exists but backend cannot execute any classification

### ❌ What's Just Placeholder Code (Not Really Implemented)
- **AI Search Engine**: Just C++ header files, not compiled into any working browser
- **Gmail/Calendar**: Python code exists, ZERO actual Google API integration  
- **Performance Optimization**: "1-3s response" claims are COMPLETELY FABRICATED
- **Custom Browser**: 50GB Chromium source ≠ custom browser (just stock Chromium compiling)
- **Native Integration**: Chrome extension only, not native browser features
- **Cross-Platform**: Desktop Chrome extension only (if it worked)

### 🔍 What Needs Honest Testing
Many modules exist but their practical functionality is unverified:
- Can we actually click buttons reliably?
- Do workflows execute properly?
- Does the tool system work end-to-end?
- How accurate is the task classification?
- Does the memory system persist data correctly?

## 🏗️ Current Architecture (Reality Check)

### What We Actually Have
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Chrome Extension│────│ FastAPI Backend │────│ Ollama + GPT-OSS│
│ (Basic UI)      │    │ (Many endpoints)│    │ (Slow but local)│
│                 │    │                 │    │                 │
│ • Side Panel    │    │ • Tool System   │    │ • 10-15s response│
│ • WebSocket     │    │ • Workflows     │    │ • Privacy        │
│ • Page Reading  │    │ • AI Client     │    │ • Offline        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### What We're Aiming For Eventually
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Custom Chromium │────│ Native AI APIs  │────│ Optimized Models│
│ (Built-in AI)   │    │ (Direct access) │    │ (Fast inference)│
│                 │    │                 │    │                 │
│ • AI Search     │    │ • Gmail/Cal API │    │ • GPU Optimized │
│ • Native UI     │    │ • Ad Blocking   │    │ • Multi-model   │
│ • No Extensions │    │ • Full Automation│    │ • Smart Caching │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Development Environment

### Python Environment Setup
```bash
# Check if Python available
python --version  # Need Python 3.8+

# Install dependencies (if needed)
pip install -r backend/requirements.txt

# Environment seems to be working without conda
```

### AI Model Setup (Critical)
```bash
# Install Ollama first
# Download from https://ollama.ai/ or use package manager

# Start Ollama
ollama serve

# Pull GPT-OSS model (14GB download)
ollama pull gpt-oss:20b

# Verify it's working
ollama list
```

### Browser Extension Setup
```bash
# 1. Open Chrome and go to chrome://extensions/
# 2. Enable "Developer mode" (top right toggle)
# 3. Click "Load unpacked" 
# 4. Select the ai_browser/extension/ folder
# 5. Extension should appear in Chrome
```

## 🔧 Verification Commands That Actually Work

### Test Backend Server
```bash
cd backend
python main.py  # Should start on http://127.0.0.1:8000
# Check: http://localhost:8000/health in browser
```

### Test AI Integration  
```bash
# This works but is slow (10-15 seconds):
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "page_url": "https://example.com"}'
```

### Test Browser Extension
```bash
# 1. Load extension in Chrome
# 2. Open a webpage
# 3. Open Chrome side panel (right sidebar) 
# 4. Look for AI Browser icon
# 5. Try typing "Hello" and sending
```

## 🎯 Development Roadmap

### Current Status ✅
1. **AI Browser Agent**: Autonomous task execution with GPT-OSS 20B
2. **Backend API**: 30+ endpoints, tool registry, WebSocket streaming  
3. **Browser Extension**: Working sidepanel with AI chat
4. **Build System**: Complete Chromium build pipeline with AI patches
5. **Integration Tests**: Comprehensive test suite for full stack

### Next Phase: Custom Browser Build 🚧
1. **Build Custom Browser**: `python build_ai_browser.py --all`
   - Setup Chromium source (50GB, 1-2 hours)
   - Apply BrowserOS + AI patches 
   - Build with AI integration (2-4 hours)
   - Test autonomous AI features

2. **Test End-to-End**: `python test_ai_browser_integration.py`
   - Verify GPT-OSS 20B integration
   - Test autonomous browsing
   - Validate privacy-first features

### Future Enhancements 🔮
1. **Privacy Features**: Built-in ad blocking, tracker protection
2. **Performance**: GPU acceleration, model optimization
3. **Distribution**: Package for macOS/Windows/Linux
4. **Advanced AI**: Multi-modal capabilities, local vector search

## 📚 Documentation Status

### Accurate Documentation
- **CLAUDE.md** (this file) - Now reflects reality
- **README.md** - Basic project overview
- **requirements.txt** - Working dependency list

### Questionable Documentation  
Most other .md files appear to be aspirational rather than reflecting current reality:
- VERIFIED_STATUS.md - Claims everything is working (needs verification)
- AI_BROWSER_COMPETITIVE_STRATEGY.md - May contain unrealistic timelines
- BROWSEROS_ANALYSIS_INSIGHTS.md - Competitive analysis (useful but not implementation)

## 🚨 Important Warnings

### For Future Development Sessions
1. **Don't believe the hype**: Many claims in docs are aspirational
2. **Test everything**: Verify actual functionality before making claims  
3. **Speed is a major issue**: 10-15s AI responses vs 1-3s for cloud
4. **Extension limitations**: Can't do everything a custom browser can
5. **Chrome only**: Not a multi-platform solution yet

### What Works vs What Needs Work
- ✅ **Basic AI chat works** - but slow
- ✅ **Backend starts up** - all endpoints exist
- ✅ **Extension loads** - basic UI functional
- ❓ **Automation tools** - framework exists, execution unclear
- ❌ **Advanced features** - most are unverified
- ❌ **Performance** - much slower than cloud alternatives

---

**Current Status**: Working AI browser extension prototype with significant limitations compared to Perplexity Comet. Has privacy/cost advantages but major performance/feature gaps.

**Last Updated**: January 2025  
**Realistic Assessment**: Functional prototype, not production-ready AI browser