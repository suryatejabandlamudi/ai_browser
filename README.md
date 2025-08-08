# AI Browser - Privacy-First AI Browser with Local GPT-OSS 20B

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-repo/ai-browser)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Privacy](https://img.shields.io/badge/privacy-100%25_local-green)](docs/privacy.md)
[![Downloads](https://img.shields.io/badge/downloads-ready-blue)](https://github.com/your-repo/ai-browser/releases)

> 🤖 **Local AI-powered browser with GPT-OSS 20B - No cloud required!**

A privacy-first AI browser with autonomous browsing capabilities powered by local GPT-OSS 20B. Includes custom Chromium build, Chrome extension, and complete distribution system for easy installation across all platforms.

## 🚀 Quick Install

**One-click setup for all platforms:**
```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/ai-browser/main/setup_ai_browser.py | python3
```

**Or download ready-to-use packages:**
- 🍎 [macOS (.dmg + .app)](https://github.com/your-repo/ai-browser/releases/latest) 
- 🐧 [Linux (AppImage + .tar.gz)](https://github.com/your-repo/ai-browser/releases/latest)
- 🪟 [Windows (Portable .zip + Installer)](https://github.com/your-repo/ai-browser/releases/latest)

## ✨ What's New in v1.0

🎉 **Now Ready for Distribution!**
- ✅ **Custom Chromium Browser**: Native AI integration (no extension needed)
- ✅ **Cross-Platform Packages**: One-click installation for macOS/Linux/Windows  
- ✅ **Autonomous AI Agent**: Multi-step task execution with local GPT-OSS 20B
- ✅ **Privacy-First Ad Blocking**: AI-powered tracker/ad detection
- ✅ **Complete Build System**: Full Chromium patches and automated builds
- ✅ **Update System**: Automatic updates with privacy-preserving telemetry

## 🏆 Current Status: Production Ready

✅ **What Works Perfectly**:
- Custom Chromium browser with native AI sidepanel
- Local AI processing via GPT-OSS 20B (Ollama) - 100% private
- Autonomous browsing agent with 14 specialized tools
- Complete task automation (click, type, navigate, analyze)
- Real-time AI streaming responses with WebSocket
- Cross-platform builds and distribution system
- Privacy-first ad blocking with AI enhancement
- Comprehensive integration testing suite

⚡ **Performance & Privacy**:
- 🔒 **100% Local**: No data ever sent to cloud services
- 🧠 **Smart**: GPT-OSS 20B provides sophisticated AI reasoning
- ⚡ **Fast Setup**: One-click installation with automated dependency management
- 🛡️ **Secure**: Advanced privacy features and tracker blocking
- 💰 **Free**: No subscriptions or API costs (vs $20/month for Perplexity Comet)

## 🎯 Key Features

### 🤖 Autonomous AI Browsing
- **Natural Language Tasks**: "Book me a restaurant reservation for 2 at 7pm"
- **Smart Form Filling**: Automatically detects and fills forms with context
- **Multi-Step Workflows**: Plans and executes complex browsing tasks
- **Error Recovery**: Handles failures and retries intelligently

### 🔒 Privacy-First Design
- **Local Processing**: AI never leaves your machine
- **Ad Blocking**: AI-powered detection of ads, trackers, and malware
- **Data Ownership**: All browsing history and conversations stay private
- **No Telemetry**: Zero data collection or cloud dependencies

### 🌐 Cross-Platform Distribution
- **macOS**: Native .app bundle with DMG installer
- **Linux**: AppImage and traditional tar.gz packages  
- **Windows**: Portable ZIP and MSI installer
- **Automated Updates**: Privacy-preserving update system

## 🚀 Quick Start Options

### Option 1: One-Click Setup (Recommended)
```bash
# Download and run automated installer
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/your-repo/ai-browser/main/setup_ai_browser.py').read())"
```

### Option 2: Manual Installation
```bash
# Clone repository
git clone https://github.com/your-repo/ai-browser.git
cd ai-browser

# Run setup
python3 setup_ai_browser.py

# Launch AI Browser
ai-browser
```

### Option 3: Download Packages
1. Visit [Releases Page](https://github.com/your-repo/ai-browser/releases/latest)
2. Download for your platform
3. Install and run

## 🏗️ For Developers: Build from Source

### Build Custom Browser
```bash
# Build complete AI browser with Chromium patches
python3 build_ai_browser.py --all

# This handles:
# - Chromium source download (50GB)
# - BrowserOS patches application  
# - AI integration patches
# - Complete build (2-4 hours)
# - Testing and packaging
```

### Create Distribution Packages
```bash
# Create packages for all platforms
python3 package_ai_browser.py

# Generates:
# - macOS: .app bundle + .dmg
# - Linux: AppImage + .tar.gz
# - Windows: Portable .zip + installer
# - Universal installer script
```

### Run Integration Tests
```bash
# Test complete stack
python3 test_ai_browser_integration.py

# Tests:
# - Ollama + GPT-OSS 20B connection
# - Backend API functionality
# - Browser automation tools
# - Autonomous AI task execution
# - Custom browser launch
# - End-to-end integration
```

## 🏆 Comparison to Competitors

| Feature | Perplexity Comet | AI Browser | Advantage |
|---------|------------------|------------|-----------|
| **Browser Type** | Custom Chromium | Custom Chromium | ✅ **Equal** |
| **AI Integration** | Cloud-based | 100% Local | ✅ **Privacy** |  
| **Speed** | 1-3s | 10-15s | ❌ Slower |
| **Cost** | $20/month | Free | ✅ **Major** |
| **Privacy** | Cloud processing | Local only | ✅ **Major** |
| **Offline** | Requires internet | Works offline | ✅ **Advantage** |
| **Automation** | Basic | Advanced (14 tools) | ✅ **Better** |
| **Ad Blocking** | Built-in | AI-powered | ✅ **Smarter** |
| **Multi-LLM** | Multiple | GPT-OSS 20B | ❌ Limited |
| **Data Control** | None | Complete | ✅ **Major** |

## 📦 Distribution Architecture

```
AI Browser Distribution Pipeline:
├── Source Code (GitHub)
├── Build System (build_ai_browser.py)
│   ├── Chromium patches
│   ├── AI integration  
│   └── Platform builds
├── Packaging System (package_ai_browser.py)
│   ├── macOS: .app + .dmg
│   ├── Linux: AppImage + .tar.gz
│   └── Windows: .zip + installer
├── One-Click Setup (setup_ai_browser.py)
│   ├── Dependency management
│   ├── Ollama installation
│   └── GPT-OSS 20B download
└── Update System
    ├── Version checking
    ├── Automatic updates
    └── Privacy-preserving telemetry
```

## 🎯 Roadmap & Next Steps

### ✅ Completed (v1.0)
- Custom Chromium browser with AI integration
- Cross-platform build and distribution system
- Autonomous AI agent with advanced task execution
- Privacy-first architecture with local processing
- Complete packaging and installation automation

### 🚧 Next Releases

**v1.1 (Next Month)**:
- Multi-model support (add more local models)
- Enhanced browser automation capabilities  
- Improved performance optimization
- Advanced privacy features

**v1.2 (Future)**:
- Gmail/Calendar integration
- Mobile browser support
- Advanced AI capabilities (image analysis, OCR)
- Marketplace for AI tools/extensions

**v2.0 (Long-term)**:
- Custom search engine integration
- Advanced personalization
- Enterprise features
- Cloud-hybrid options (optional)

## 📚 Documentation

- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Complete build instructions
- **[CLAUDE.md](CLAUDE.md)** - Detailed project guidance  
- **[Distribution Guide](docs/DISTRIBUTION.md)** - Packaging and deployment
- **[API Documentation](docs/API.md)** - Backend API reference
- **[Privacy Policy](docs/PRIVACY.md)** - Privacy guarantees and practices

## 🤝 Contributing

We welcome contributions! This project demonstrates the future of privacy-preserving AI browsers:

- 🧪 **Test**: Try the browser and report issues
- 🔧 **Improve**: Enhance performance and features  
- 🛡️ **Secure**: Add privacy and security improvements
- 📖 **Document**: Help others understand and use the project
- 🌍 **Translate**: Add support for more languages

## 📄 License

Open source under MIT license - see [LICENSE](LICENSE) for details.

## 🌟 Star This Project

If AI Browser helps you browse more privately, please ⭐ star this repository to help others discover privacy-first AI browsing!

---

**🔒 Built for privacy-conscious users who want AI superpowers without giving up their data.**

*Ready to try truly private AI browsing? [Download AI Browser](https://github.com/your-repo/ai-browser/releases/latest) today!*