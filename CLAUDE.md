# CLAUDE.md - AI Browser Project Guidance

This file provides guidance to Claude Code when working with this AI browser project.

## 🎯 Project Mission

**Build a privacy-first AI browser extension with local AI capabilities.**

### Current Reality (August 2025)
This is a **sophisticated AI browser extension prototype** with local AI capabilities:
- **Local AI Processing**: GPT-OSS 20B via Ollama (confirmed working, 2-3s responses, not 10-15s as docs claim)
- **Privacy Advantage**: 100% local processing, no data sent to cloud services
- **Extension Architecture**: Chrome extension with comprehensive FastAPI backend
- **Development Stage**: Advanced prototype with comprehensive tool system but unverified end-to-end automation

### Honest Status vs Perplexity Comet
| Feature | Perplexity Comet | Our Current State | Implementation Gap |
|---------|------------------|-----------------|------------------|
| **Browser Type** | Custom Chromium build | Chrome extension only | ❌ Major - 130GB Chromium source exists but never built |
| **AI Search Engine** | Built-in AI search as default | Regular browser search + AI chat | ❌ No search engine integration |
| **Sidebar AI Assistant** | Full agentic task automation | Advanced planning system, execution unverified | 🟡 14 tools exist, real-world reliability unknown |
| **Task Automation** | Restaurant booking, email sending | Complex multi-step framework exists | 🟡 Sophisticated code, practical results untested |
| **Gmail/Calendar Integration** | Deep native integration | None | ❌ Major missing feature |
| **Multi-LLM Support** | GPT-4, Claude, Gemini, Grok | Local GPT-OSS 20B only | ❌ Single model limitation |
| **Context Management** | Smart tab/session handling | Advanced context system implemented | 🟡 Code sophisticated, functionality unverified |
| **Performance** | Fast cloud inference | Actually 2-3s local inference | ✅ Better than claimed in docs |
| **Ad Blocking** | Built-in ad blocking | None | ❌ Not implemented |
| **Cross-Platform** | Windows/Mac/Mobile planned | Chrome extension only | ❌ Platform limitation |
| **Privacy** | Cloud processing | 100% Local processing | ✅ **Major advantage** |
| **Cost** | $20/month subscription | Free after setup | ✅ **Major advantage** |
| **Offline Capability** | Requires internet | Works offline | ✅ **Advantage** |

## 📁 Repository Structure & What Actually Works

```
ai_browser/
├── CLAUDE.md                    # This guidance file ✅ UPDATED WITH REALITY
├── backend/                     # Python backend system
│   ├── main.py                  # FastAPI server ✅ WORKING (30+ endpoints confirmed)
│   ├── ai_client.py             # Ollama integration ✅ WORKING (2-3s responses)
│   ├── browser_agent.py         # Action execution ❌ SYNTAX ERROR (line 343)
│   ├── real_browser_agent.py    # Alternative agent ✅ WORKING 
│   ├── tools/                   # Tool framework ✅ SOPHISTICATED (14 tools registered)
│   ├── chromium/                # Chromium source ✅ 130GB EXISTS (never built)
│   ├── requirements.txt         # Dependencies ✅ WORKING (some optional missing)
│   └── [various modules]        # 130+ Python files ✅ COMPREHENSIVE ARCHITECTURE
│
├── extension/                   # Chrome extension
│   ├── manifest.json            # Extension config ✅ MANIFEST V3 COMPLIANT
│   ├── sidepanel.html/js        # AI chat UI ✅ COMPLETE INTERFACE
│   ├── background.js            # Backend communication ✅ COMPREHENSIVE FEATURES
│   └── content.js               # Page interaction ✅ DOM AUTOMATION READY
│
└── [essential docs only]        # Cleaned up - removed misleading docs
```

## 🚨 **ACTUAL CURRENT STATUS** (August 2025)

### ✅ What Actually WORKS (Verified by Testing)
- **FastAPI Backend**: Runs and responds properly (tested health checks, AI chat)
- **AI Integration**: GPT-OSS 20B working via Ollama (2-3s responses confirmed)
- **Tool Registration**: 14 sophisticated tools registered and available
- **Chrome Extension**: Complete UI with WebSocket + HTTP communication
- **Database**: SQLite database (20KB) with actual cached data
- **9/10 Core Modules**: Import successfully (only browser_agent.py has syntax error)

### 🟡 What Exists But Is UNVERIFIED in Real-World Use
- **Browser Automation**: Comprehensive click/type/navigate framework exists, effectiveness unknown
- **Multi-Step Planning**: Sophisticated rolling-horizon planning system, execution results unclear  
- **Visual Highlighting**: DOM manipulation code present, practical reliability unknown
- **Form Processing**: Intelligent form analysis tools, real website compatibility unclear
- **Task Classification**: Advanced task analysis system, accuracy on real tasks unknown
- **Memory System**: Cross-tab context management implemented, persistence reliability unclear

### ❌ What's Missing or Broken
- **browser_agent.py**: Syntax error at line 343 (indentation issue)
- **Advanced AI Features**: Missing numpy, PIL, pytesseract dependencies  
- **Custom Browser**: 130GB Chromium source exists but NEVER compiled into working browser
- **Native Integration**: Still just Chrome extension, not native browser features
- **Distribution Packages**: Build scripts exist but no actual installers created
- **End-to-End Testing**: No verification of complete user workflows

### 🔍 Critical Unknowns Requiring Testing
- Does the extension actually load and work in Chrome?
- Can it successfully automate real websites (Amazon, Gmail, etc.)?
- How reliable is multi-step task execution?
- Does the sophisticated planning system work in practice?
- What's the success rate for complex automation tasks?

## 🏗️ Current Architecture (Reality Check)

### What We Actually Have
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Chrome Extension│────│ FastAPI Backend │────│ Ollama + GPT-OSS│
│ (Complete UI)   │    │ (Comprehensive) │    │ (Fast & local)  │
│                 │    │                 │    │                 │
│ • Side Panel    │    │ • 30+ Endpoints │    │ • 2-3s responses │
│ • WebSocket     │    │ • 14 Tools      │    │ • 100% Privacy  │
│ • DOM Control   │    │ • Planning AI   │    │ • 13GB Model    │
│ • Page Analysis │    │ • Multi-Step    │    │ • Offline Ready │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### What We Could Build (With Chromium Source)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Custom Chromium │────│ Native AI APIs  │────│ Same AI System │
│ (130GB Source)  │    │ (Browser APIs)  │    │ (Already Works) │
│                 │    │                 │    │                 │
│ • AI Search     │    │ • Native Panel  │    │ • GPT-OSS 20B   │
│ • Native UI     │    │ • Direct DOM    │    │ • Local Vector │
│ • Ad Blocking   │    │ • Browser APIs  │    │ • Multi-Modal   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
   ↑ 3-6 hours build      ↑ Patches ready     ↑ Backend ready
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
# ✅ CONFIRMED: Starts in <5s, health check returns proper JSON
```

### Test AI Integration  
```bash
# This works fast (2-3 seconds, not 10-15s as claimed):
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "page_url": "https://example.com"}'
# ✅ CONFIRMED: GPT-OSS 20B responds with proper JSON
```

### Test Browser Extension
```bash
# 1. Open Chrome → chrome://extensions/
# 2. Enable "Developer mode" (toggle top right)
# 3. Click "Load unpacked" 
# 4. Select the ai_browser/extension/ folder
# 5. Look for AI Browser icon in extensions
# ❓ UNTESTED: Extension loading and side panel functionality
```

### Fix Critical Issues
```bash
# Fix browser_agent.py syntax error
cd backend
# Line 343: remove incorrect indentation causing import failure

# Install missing advanced AI dependencies  
pip install numpy sentence-transformers faiss-cpu Pillow pytesseract
# Enables vector search, multimodal AI, OCR features
```

## 🎯 Development Priorities 

### Immediate Fixes (30 minutes) 🚨
1. **Fix browser_agent.py**: Remove syntax error at line 343
2. **Test Chrome Extension**: Load in browser and verify basic functionality  
3. **Install Dependencies**: Add numpy, PIL, pytesseract for advanced features
4. **End-to-End Test**: Verify extension → backend → AI communication

### Short Term (1-2 days) ⚡
1. **Real-World Testing**: Test automation on actual websites (Amazon, Gmail, etc.)
2. **Reliability Assessment**: Measure success rates for multi-step tasks
3. **Performance Analysis**: Profile actual response times and bottlenecks
4. **Extension Polish**: Fix any UI/UX issues discovered in testing

### Medium Term (1-2 weeks) 🔧  
1. **Custom Browser Build**: Use 130GB Chromium source + patches to create native browser
2. **Advanced AI Features**: Implement missing vector search, multimodal capabilities
3. **Distribution System**: Create actual installers for macOS/Windows/Linux
4. **Integration Testing**: Comprehensive end-to-end workflow validation

### Long Term Goals 🚀
1. **Search Engine Integration**: Replace default search with AI-powered version
2. **Gmail/Calendar Integration**: Add productivity automation features  
3. **Multi-Model Support**: Expand beyond GPT-OSS 20B to other local models
4. **Mobile Extension**: Adapt for mobile browsers

## 📚 Documentation Status

### ✅ Accurate Documentation (Updated)
- **CLAUDE.md** (this file) - Updated with verified reality
- **REALITY_CHECK.md** - Honest working vs non-working assessment
- **requirements.txt** - Verified dependency list
- **SETUP.md** - Basic setup instructions
- **Extension files** - Working Chrome extension code

### ❌ Removed Misleading Documentation  
Deleted files containing false claims:
- **README.md** - Claimed "production ready" with distribution packages
- **ACCOMPLISHMENTS.md** - Claimed completed features that don't exist
- **VERIFIED_STATUS.md** - False verification claims
- **AI_BROWSER_COMPETITIVE_STRATEGY.md** - Aspirational strategy vs reality
- **Archive folder** - Contained outdated, misleading information

## 🚨 Critical Reality Check

### What Actually Works (Verified)
- ✅ **FastAPI backend** - 30+ endpoints, 2-3s responses
- ✅ **AI integration** - GPT-OSS 20B via Ollama working locally
- ✅ **Comprehensive architecture** - 130+ Python files, sophisticated design
- ✅ **Chrome extension** - Complete UI with WebSocket communication
- ✅ **Tool framework** - 14 registered tools with advanced planning

### Major Gaps Requiring Work
- 🐛 **browser_agent.py** - Syntax error preventing import
- ❓ **Real-world testing** - Unknown reliability on actual websites  
- ❌ **Custom browser** - 130GB source exists but never built
- ❌ **Advanced AI** - Missing dependencies for vector/multimodal features
- ❌ **Distribution** - No actual installers, just build scripts

### Bottom Line Assessment
**This is a sophisticated AI browser extension prototype that's more advanced than typical hobby projects but less functional than claimed in documentation. The foundation is solid and the architecture is impressive, but practical deployment requires additional work.**

---

**Current Status**: Advanced prototype with working local AI integration. Needs testing, bug fixes, and honest validation of automation capabilities.

**Last Updated**: August 2025  
**Honest Assessment**: Sophisticated foundation, unverified automation, significant potential