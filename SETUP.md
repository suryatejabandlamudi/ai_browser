# AI Browser Setup Guide

## System Requirements

- **macOS** (Apple Silicon recommended for optimal performance)
- **16GB+ RAM** (required for GPT-OSS 20B model)
- **50GB+ free disk space** (for Chromium source + models)
- **Fast internet connection** (for initial downloads)

## Development Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/suryatejabandlamudi/ai_browser.git
cd ai_browser
```

### 2. Python Environment Setup
**Using Conda (Recommended)**:
```bash
# Create conda environment
conda create -n ai_browser_env python=3.13
conda activate ai_browser_env

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

**Manual Python Setup**:
```bash
# Ensure Python 3.11+ is installed
python3 --version  # Should be 3.11 or higher

# Create virtual environment
python3 -m venv ai_browser_env
source ai_browser_env/bin/activate  # On macOS/Linux
# or: ai_browser_env\Scripts\activate  # On Windows

# Install dependencies
pip install fastapi uvicorn aiohttp structlog
pip install aiosqlite beautifulsoup4 readability-lxml requests
pip install pydantic python-multipart websockets
```

### 3. Required Dependencies
```bash
# Core backend dependencies
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install aiohttp==3.9.1
pip install structlog==23.2.0
pip install aiosqlite==0.20.0
pip install beautifulsoup4==4.13.0
pip install readability-lxml==0.8.4.1
pip install pydantic==2.5.0

# Optional OCR dependencies (for visual processing)
pip install pytesseract pillow  # For Tesseract OCR
pip install easyocr            # For EasyOCR (GPU recommended)
pip install paddlepaddle paddleocr  # For PaddleOCR
```

## AI Model Setup (GPT-OSS 20B via Ollama)

### 1. Install Ollama
```bash
# On macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### 2. Download GPT-OSS 20B Model
```bash
# This will download ~14GB model
ollama pull gpt-oss:20b

# Verify model is available
ollama list
```

### 3. Test Ollama Connection
```bash
# Start Ollama server (runs on localhost:11434 by default)
ollama serve

# In another terminal, test the model
ollama run gpt-oss:20b "Hello, can you help me browse the web?"
```

## Browser Development Setup

### 1. Chrome Extension Development
The extension is located in `/extension/` directory:
```bash
# No build step required - it's vanilla JavaScript
# Load extension in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the /extension/ folder
```

### 2. Chromium Fork Setup (Advanced - Optional for Phase 1)
```bash
# Install depot_tools (required for Chromium development)
cd backend
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PWD/depot_tools:$PATH"

# Download Chromium source (~55GB, takes 4-6 hours)
mkdir chromium
cd chromium
fetch chromium
cd src

# This is for Phase 2 - custom browser development
# Extension approach is recommended for initial development
```

## Directory Structure

```
ai_browser/
├── backend/                 # FastAPI backend server
│   ├── main.py             # Main server application
│   ├── ai_client.py        # Ollama integration
│   ├── browser_agent.py    # Core automation
│   ├── task_classifier.py  # Intent analysis
│   ├── visual_highlighter.py # DOM highlighting
│   ├── form_intelligence.py # Form processing
│   ├── context_memory.py   # Cross-tab memory
│   ├── visual_processor.py # Screenshots/OCR
│   ├── accessibility_tree.py # DOM analysis
│   ├── tools/              # Browser automation tools
│   └── chromium/           # Chromium source (Phase 2)
├── extension/              # Chrome extension (Phase 1)
│   ├── manifest.json       # Extension configuration
│   ├── sidepanel.html      # AI chat interface
│   ├── sidepanel.js        # Frontend logic
│   ├── content.js          # Page interaction
│   └── background.js       # Extension background
├── SETUP.md               # This file
├── ARCHITECTURE.md        # System design
└── FEATURE_IMPLEMENTATION_PLAN.md
```

## Running the System

### 1. Start the Backend Server
```bash
cd backend
conda activate ai_browser_env  # or source ai_browser_env/bin/activate

# Ensure Ollama is running
ollama serve  # In another terminal

# Start the backend server
python main.py
```

Expected output:
```
2025-08-07 16:51:14 [info] Starting AI Browser Backend...
2025-08-07 16:51:14 [info] ✅ GPT-OSS 20B connection verified  
2025-08-07 16:51:14 [info] 🚀 AI Browser Backend ready!
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Load Chrome Extension
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Navigate to the `extension/` folder and select it
5. The extension should appear with a side panel icon

### 3. Test the Integration
1. Navigate to any webpage
2. Open the side panel (click extension icon)
3. Try asking: "What is this page about?"
4. The AI should analyze the page content and respond

## Verification Tests

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ai_model": "gpt-oss:20b",
  "backend": "ollama",
  "agents": {
    "browser_agent": true,
    "task_classifier": true,
    "visual_highlighter": true,
    "form_processor": true,
    "memory_manager": true
  }
}
```

### AI Chat Test
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?", "page_url": "https://example.com"}'
```

### Extension Test
1. Load extension in Chrome
2. Go to any webpage
3. Open side panel
4. Ask: "Summarize this page"
5. Should get AI response about page content

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Missing dependencies
pip install -r requirements.txt

# Python path issues
export PYTHONPATH="${PYTHONPATH}:/path/to/ai_browser/backend"
```

**2. Ollama Connection Failed**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama server
ollama serve

# Test connection
curl http://localhost:11434/v1/models
```

**3. Model Not Found**
```bash
# List available models
ollama list

# Pull GPT-OSS model
ollama pull gpt-oss:20b
```

**4. Chrome Extension Issues**
- Ensure extension is loaded in developer mode
- Check browser console for errors (F12 → Console)
- Verify backend server is running on port 8000

### Performance Issues
- **Slow AI responses**: Normal for 20B model, ~2-4 tokens/sec
- **High memory usage**: Expected, 16GB+ RAM required
- **Cold start delay**: First request takes ~10 seconds

### Development Tips
1. **Use conda environment** for consistent Python setup
2. **Keep Ollama running** in background during development  
3. **Check logs** in terminal for detailed error messages
4. **Test APIs individually** before testing full integration
5. **Use browser dev tools** to debug extension issues

## Next Steps After Setup

1. **Verify basic functionality** with health check endpoints
2. **Test Ollama integration** with simple chat requests
3. **Load and test Chrome extension** with page analysis
4. **Experiment with form analysis** on various websites
5. **Try task classification** with different user requests

## Phase 2: Chromium Fork Development

Once basic functionality is working:
1. **Study BrowserOS patches** for integration patterns
2. **Set up Chromium build environment** (requires significant disk space)
3. **Implement native accessibility tree** access
4. **Create custom browser UI** with integrated AI sidebar
5. **Package and distribute** standalone browser application

## Support

For issues or questions:
1. Check this setup guide first
2. Review error logs in terminal
3. Test individual components in isolation
4. Ensure all dependencies are properly installed
5. Verify system meets minimum requirements