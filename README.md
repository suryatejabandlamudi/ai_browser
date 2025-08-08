# AI Browser - Privacy-First Local AI Assistant

A Chrome extension with local AI capabilities that aims to provide private, offline AI assistance for web browsing without sending data to the cloud.

## Current Status: Working Prototype

✅ **What Works**:
- Chrome extension with AI chat sidebar
- Local AI processing via GPT-OSS 20B (Ollama)
- Basic page content reading and analysis  
- FastAPI backend with 30+ endpoints
- Real-time WebSocket streaming
- Browser automation framework (14 registered tools)

⚠️ **Limitations**:
- Slow AI responses (10-15 seconds vs 1-3s for cloud services)
- Chrome extension only (not custom browser)
- Limited automation testing
- No Gmail/calendar integration
- Single AI model (GPT-OSS 20B only)

## Quick Start

### Prerequisites
- Chrome browser
- Python 3.8+
- [Ollama](https://ollama.ai/) installed
- 16GB+ RAM recommended for local AI model

### Setup
1. **Install AI Model**:
   ```bash
   ollama serve
   ollama pull gpt-oss:20b  # 14GB download
   ```

2. **Start Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py  # Starts on http://127.0.0.1:8000
   ```

3. **Load Extension**:
   - Open Chrome → `chrome://extensions/`
   - Enable "Developer mode" 
   - Click "Load unpacked" → Select `extension/` folder
   - Extension icon appears in Chrome toolbar

4. **Test**:
   - Open any webpage
   - Click Chrome side panel (right sidebar)
   - Look for AI Browser and start chatting

## Architecture

```
Chrome Extension → FastAPI Backend → Ollama + GPT-OSS 20B
     (UI)              (API)            (Local AI)
```

## Privacy Advantages

- 🔒 **100% Local Processing**: No data sent to cloud services
- 💰 **No Subscription**: Free after initial setup (vs $20/month for Perplexity Comet)  
- 🌐 **Works Offline**: Full functionality without internet
- 🎯 **Data Ownership**: All conversations and data stay on your machine

## Performance Trade-offs

- ⚡ Cloud AI: 1-3 seconds response time
- 🐢 Local AI: 10-15 seconds response time
- 💾 High RAM usage: ~8-16GB for AI model
- 🔋 GPU acceleration helps but not required

## Comparison to Perplexity Comet

| Feature | Perplexity Comet | AI Browser | Status |
|---------|------------------|------------|--------|
| Browser Type | Custom Chromium | Chrome Extension | ❌ Major gap |
| AI Search | Built-in | Regular search + AI chat | ❌ Not implemented |
| Speed | 1-3s | 10-15s | ❌ Much slower |  
| Privacy | Cloud | 100% Local | ✅ **Major advantage** |
| Cost | $20/month | Free | ✅ **Major advantage** |
| Gmail Integration | Yes | No | ❌ Missing |
| Multi-LLM | Yes | Local only | ❌ Limited |

## Roadmap

See [REALISTIC_ROADMAP.md](REALISTIC_ROADMAP.md) for development phases:
- **Phase 1** (1 month): Stabilize prototype, improve performance
- **Phase 2** (3 months): Add Gmail/calendar, multi-LLM, advanced automation  
- **Phase 3** (2 months): UI polish, ad blocking, performance optimization
- **Phase 4** (12 months): Custom browser, native integration
- **Phase 5** (12+ months): Market competitive features

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete project guidance and technical status
- **[REALISTIC_ROADMAP.md](REALISTIC_ROADMAP.md)** - Development phases and timelines
- **[SETUP.md](SETUP.md)** - Detailed installation instructions  
- **[BROWSEROS_ANALYSIS_INSIGHTS.md](BROWSEROS_ANALYSIS_INSIGHTS.md)** - Competitive analysis
- **[AI_BROWSER_COMPETITIVE_STRATEGY.md](AI_BROWSER_COMPETITIVE_STRATEGY.md)** - Strategic positioning

## Contributing

This is an experimental project exploring local AI for browsers. Contributions welcome:
- Test the extension on different websites
- Improve performance and reliability
- Add new automation capabilities
- Enhance privacy and security features

## License

Open source - see LICENSE file for details.

---

**Note**: This is a prototype exploring privacy-first AI browsing. It's not yet ready for production use but demonstrates the potential of local AI processing for maintaining user privacy while providing intelligent web assistance.