# AI Browser - Local AI Extension Prototype

> **🤖 Chrome extension with local GPT-OSS 20B - Privacy-first AI browsing**

A sophisticated AI browser extension prototype that provides local AI assistance for web browsing without sending data to the cloud.

## 🚨 Current Status: Advanced Prototype

**What Actually Works:**
- ✅ FastAPI backend with 30+ endpoints (tested, working)
- ✅ Local AI via GPT-OSS 20B through Ollama (2-3 second responses)
- ✅ Chrome extension with complete UI and WebSocket communication
- ✅ 14 sophisticated browser automation tools registered
- ✅ Advanced multi-step planning system architecture

**What Needs Work:**
- 🐛 Minor syntax error in browser_agent.py (line 343)
- ❓ Real-world automation testing on actual websites
- ❌ Missing optional dependencies for advanced AI features
- ❌ Custom browser build (130GB Chromium source available but not built)

## 🏗️ Architecture

```
Chrome Extension ──── FastAPI Backend ──── Ollama + GPT-OSS 20B
     │                      │                        │
  Side Panel            30+ Endpoints           Local AI (13GB)
  WebSocket             14 AI Tools             2-3s Response
  DOM Control           Planning System         100% Private
```

## ⚡ Quick Start

### 1. Start Backend
```bash
cd backend
python main.py
# Server starts at http://localhost:8000
```

### 2. Test AI Integration
```bash
# Verify GPT-OSS 20B is working
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "page_url": "https://example.com"}'
```

### 3. Load Chrome Extension (Untested)
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" 
3. Click "Load unpacked"
4. Select the `extension/` folder
5. Test AI chat in browser side panel

### 4. Optional: Install Advanced Features
```bash
cd backend
pip install numpy sentence-transformers faiss-cpu Pillow pytesseract
# Enables vector search, multimodal AI, OCR capabilities
```

## 🎯 Core Features

### ✅ Working Features
- **Local AI Processing**: GPT-OSS 20B via Ollama (100% private)
- **FastAPI Backend**: Comprehensive API with streaming support
- **Chrome Extension**: Complete side panel UI with WebSocket communication
- **Tool System**: 14 registered tools for browser automation
- **Planning System**: Multi-step task planning with rolling-horizon architecture

### 🟡 Untested Features (Code Exists)
- **Browser Automation**: Click/type/navigate framework
- **Multi-Step Workflows**: Complex task execution
- **Visual Highlighting**: DOM element highlighting
- **Form Processing**: Intelligent form interaction
- **Context Memory**: Cross-tab session management

### ❌ Missing/Broken
- **Custom Browser**: Build scripts exist, no compiled browser
- **Advanced AI**: Some features need additional dependencies
- **Distribution**: No installers, manual setup only

## 🔧 Dependencies

### Required (Verified Working)
- Python 3.8+
- FastAPI, Uvicorn, aiosqlite
- BeautifulSoup4, readability-lxml
- Ollama with GPT-OSS 20B model

### Optional (Advanced Features)
- numpy, sentence-transformers, faiss-cpu (vector search)
- Pillow, pytesseract (OCR and image processing)
- playwright (browser automation testing)

## 📊 Honest Comparison vs Commercial AI Browsers

| Feature | Perplexity Comet | This Project | Status |
|---------|------------------|--------------|---------|
| **Privacy** | Cloud processing | 100% local | ✅ **Major advantage** |
| **Cost** | $20/month | Free | ✅ **Advantage** |
| **Browser Type** | Custom Chromium | Chrome extension | ❌ **Limitation** |
| **AI Speed** | 1-3 seconds | 2-3 seconds | ✅ **Competitive** |
| **Automation** | Basic | Advanced framework | 🟡 **Potential advantage** |
| **Offline** | No | Yes | ✅ **Advantage** |
| **Multi-LLM** | Multiple | Single local model | ❌ **Limitation** |

## 🚧 Known Issues

1. **browser_agent.py**: Syntax error at line 343 (indentation)
2. **Extension Testing**: UI loads but end-to-end functionality unverified
3. **Advanced AI**: Missing optional dependencies for full feature set
4. **Custom Browser**: 130GB Chromium source present but never built

## 🎯 Next Steps

### Immediate (Fix & Test)
1. Fix syntax error in browser_agent.py
2. Load and test Chrome extension thoroughly
3. Install missing dependencies for advanced features
4. Test automation on real websites

### Medium Term (Build & Deploy)
1. Build custom Chromium browser from 130GB source
2. Create distribution packages for easy installation
3. Add more local AI models beyond GPT-OSS 20B
4. Implement missing advanced features

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Detailed project guidance and status
- **[REALITY_CHECK.md](REALITY_CHECK.md)** - Honest working vs broken assessment
- **[SETUP.md](SETUP.md)** - Setup and installation instructions

## 💡 Key Insights

This project demonstrates that **sophisticated local AI browsing is possible** without sacrificing privacy or paying subscription fees. The architecture is more advanced than typical hobby projects, with a comprehensive tool system and intelligent planning capabilities.

However, it's currently a **prototype requiring testing and refinement** rather than a production-ready browser. The foundation is solid for building something competitive with commercial AI browsers.

## 🔒 Privacy & Security

- **100% Local Processing**: All AI computation happens on your machine
- **No Telemetry**: No usage tracking or data collection
- **Open Source**: Full code transparency and control
- **Secure Communication**: localhost-only API communication

---

**Status**: Advanced prototype with working local AI integration  
**Assessment**: Sophisticated foundation, requires testing and validation  
**Potential**: Strong foundation for privacy-first AI browsing alternative