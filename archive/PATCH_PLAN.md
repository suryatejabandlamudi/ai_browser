# AI Browser Patch System Design

## Overview

Based on detailed analysis of BrowserOS patches, this document outlines our approach to integrating GPT-OSS 20B with Chromium using the proven patch system methodology.

## BrowserOS Analysis Summary

### Key Insights from BrowserOS Architecture

**Patch Application System**:
- Uses Python build system (`build/build.py`) with modular approach
- Applies patches via `modules/patches.py` using Git patch mechanism
- Patches defined in `patches/series` file with dependency ordering
- Platform-specific filtering (macOS, Windows, Linux)

**Core Integration Strategy**:
1. **browserOS API** - Custom Chrome extension API (`browserOS-API.patch`, 760 lines)
2. **Component Extension** - Built-in extension loaded by browser (`ai-chat-extension.patch`)
3. **Side Panel Integration** - Native UI integration (`embed-third-party-llm-in-side-panel.patch`)
4. **Extension Files** - AI extension resources embedded in browser (`resources/files/ai_side_panel/`)

**Critical Patches for AI Integration**:
```
nxtscape/disable-user-gesture-restriction-on-sidepanel.patch
nxtscape/ai-chat-extension.patch                             # Loads component extension
nxtscape/browserOS-API.patch                                 # Core API (760 lines)
nxtscape/embed-third-party-llm-in-side-panel.patch          # UI integration
nxtscape/pin-nxtscape-ai-chat.patch                         # Extension pinning
```

## Our GPT-OSS Adaptation Strategy

### Phase 1: Core API Adaptation
**Target Patches to Adapt**:
1. **`gpt-oss-api.patch`** (based on `browserOS-API.patch`)
   - Create custom Chrome extension API for local LLM
   - Add accessibility tree access functions
   - Implement page content extraction APIs
   - Add browser automation primitives

2. **`ai-extension.patch`** (based on `ai-chat-extension.patch`)
   - Load our component extension instead of BrowserOS's
   - Register AI sidebar extension as built-in component

### Phase 2: UI Integration
**Target Patches**:
1. **`gpt-oss-sidebar.patch`** (based on `embed-third-party-llm-in-side-panel.patch`)
   - Integrate our FastAPI backend instead of cloud LLMs
   - Add local GPT-OSS connection interface
   - Implement Comet-style conversational UX

2. **`disable-sidepanel-restrictions.patch`** (copy from BrowserOS)
   - Remove user gesture restrictions
   - Enable programmatic sidebar control

### Phase 3: Extension Resources
**Extension Structure** (based on BrowserOS's `ai_side_panel/`):
```
resources/files/ai_browser_extension/
├── manifest.json          # Component extension manifest
├── sidepanel.html         # AI chat interface
├── sidepanel.js          # Frontend logic
├── background.js         # Extension service worker
├── content.js            # Page interaction scripts
└── assets/               # Icons and resources
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Detailed Patch Plan

### Patch 1: `gpt-oss-api.patch`
**Purpose**: Create Chrome extension API for local GPT-OSS integration
**Based on**: `browserOS-API.patch` (760 lines)

**Key API Functions to Implement**:
```cpp
// chrome/browser/extensions/api/gpt_oss/gpt_oss_api.h
namespace extensions {
namespace api {

class GptOssGetPageContentFunction : public ExtensionFunction {
 public:
  DECLARE_EXTENSION_FUNCTION("gptOss.getPageContent", GPTOSS_GETPAGECONTENT)
 protected:
  ~GptOssGetPageContentFunction() override;
  ResponseAction Run() override;
};

class GptOssGetAccessibilityTreeFunction : public ExtensionFunction {
 public:
  DECLARE_EXTENSION_FUNCTION("gptOss.getAccessibilityTree", GPTOSS_GETACCESSIBILITYTREE)
 protected:
  ~GptOssGetAccessibilityTreeFunction() override;
  ResponseAction Run() override;
};

class GptOssExecuteActionFunction : public ExtensionFunction {
 public:
  DECLARE_EXTENSION_FUNCTION("gptOss.executeAction", GPTOSS_EXECUTEACTION)
 protected:
  ~GptOssExecuteActionFunction() override;
  ResponseAction Run() override;
};

}}  // namespace extensions::api
```

**IDL Definition** (`chrome/common/extensions/api/gpt_oss.idl`):
```idl
namespace gptOss {
  dictionary PageContent {
    DOMString html;
    DOMString text;
    DOMString title;
    DOMString url;
  };
  
  dictionary AccessibilityNode {
    DOMString role;
    DOMString name;
    DOMString? value;
    long? x;
    long? y;
    long? width;
    long? height;
  };
  
  dictionary BrowserAction {
    DOMString type;  // "click", "type", "navigate", "scroll"
    DOMString? selector;
    DOMString? text;
    long? x;
    long? y;
  };
  
  callback GetPageContentCallback = void(PageContent content);
  callback GetAccessibilityTreeCallback = void(AccessibilityNode[] nodes);
  callback ExecuteActionCallback = void(boolean success, DOMString? error);
  
  interface Functions {
    static void getPageContent(GetPageContentCallback callback);
    static void getAccessibilityTree(GetAccessibilityTreeCallback callback);
    static void executeAction(BrowserAction action, ExecuteActionCallback callback);
  };
};
```

### Patch 2: `ai-extension.patch`
**Purpose**: Register our component extension
**Based on**: `ai-chat-extension.patch`

**Changes**:
1. **`chrome/browser/browser_resources.grd`**:
   ```diff
   +      <include name="IDR_AI_BROWSER_MANIFEST" file="resources\ai_browser_extension\manifest.json" type="BINDATA" />
   ```

2. **`chrome/browser/extensions/component_loader.cc`**:
   ```cpp
   #if BUILDFLAG(ENABLE_AI_BROWSER_EXTENSION)
     Add(IDR_AI_BROWSER_MANIFEST,
         base::FilePath(FILE_PATH_LITERAL("ai_browser_extension")));
   #endif
   ```

### Patch 3: `gpt-oss-sidebar.patch`
**Purpose**: Integrate sidebar UI with local FastAPI backend
**Based on**: `embed-third-party-llm-in-side-panel.patch`

**Key Changes**:
1. **Add sidebar entry**: `chrome/browser/ui/views/side_panel/side_panel_entry_id.h`
2. **Create coordinator**: `chrome/browser/ui/views/side_panel/gpt_oss/gpt_oss_panel_coordinator.cc`
3. **Add keyboard shortcut**: Command+E to toggle sidebar
4. **Connect to FastAPI**: Replace cloud API calls with local HTTP requests

### Extension Implementation

**manifest.json**:
```json
{
  "manifest_version": 3,
  "name": "AI Browser Assistant",
  "version": "1.0",
  "description": "Local GPT-OSS AI Assistant",
  "permissions": [
    "activeTab",
    "storage", 
    "scripting",
    "tabs",
    "sidePanel",
    "gptOss"
  ],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js"
  },
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "run_at": "document_start",
    "all_frames": true
  }],
  "component": true
}
```

**background.js** (Service Worker):
```javascript
// Handle extension messages and coordinate with FastAPI backend
const FASTAPI_BASE = 'http://localhost:8001';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.type) {
    case 'SEND_TO_AI':
      handleAIRequest(request.data, sendResponse);
      return true; // Async response
    case 'GET_PAGE_CONTENT':
      getPageContent(request.tabId, sendResponse);
      return true;
    case 'EXECUTE_ACTION':
      executeAction(request.data, sendResponse);
      return true;
  }
});

async function handleAIRequest(data, sendResponse) {
  try {
    const response = await fetch(`${FASTAPI_BASE}/api/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    const result = await response.json();
    sendResponse({success: true, data: result});
  } catch (error) {
    sendResponse({success: false, error: error.message});
  }
}
```

## Build Integration

### Patch Application Order
```
# Create series file: patches/series
ai-browser/disable-user-gesture-restriction-on-sidepanel.patch
ai-browser/gpt-oss-api.patch
ai-browser/ai-extension.patch  
ai-browser/gpt-oss-sidebar.patch
```

### Build Script Adaptation
**Adapt BrowserOS build system**:
1. **Copy** `build/build.py` and modules
2. **Modify** `modules/patches.py` for our patches
3. **Update** `config/` files for macOS focus
4. **Create** `patches/ai-browser/` directory
5. **Add** extension resources to `resources/files/`

### Resource Integration
**Copy and adapt from BrowserOS**:
- Extension icons and assets
- Build configuration files
- macOS-specific signing and packaging

## FastAPI Backend Integration

### Connection Strategy
**Replace BrowserOS cloud APIs with local FastAPI**:
```javascript
// Instead of: await fetch('https://api.openai.com/v1/chat/completions')
// Use: await fetch('http://localhost:8001/api/chat')

const AI_CONFIG = {
  baseUrl: 'http://localhost:8001',
  endpoints: {
    chat: '/api/chat',
    summarize: '/api/summarize', 
    actions: '/api/actions'
  }
};
```

### Health Check Integration
**Browser startup checks**:
1. Verify Ollama is running (`http://localhost:11434`)
2. Verify FastAPI backend (`http://localhost:8001/health`)
3. Show setup instructions if services not available

## Advantages of This Approach

### Technical Benefits
1. **Proven Foundation**: BrowserOS has solved Chromium integration challenges
2. **Incremental Development**: Can adapt patches one-by-one
3. **Native Performance**: Full browser integration, not extension limitations
4. **Local Privacy**: Replace cloud APIs with local FastAPI calls

### Development Benefits
1. **Clear Roadmap**: BrowserOS patches provide implementation guide
2. **Modular System**: Can test individual patches independently  
3. **Build Automation**: Existing build system handles complexity
4. **Cross-Platform**: BrowserOS supports macOS, Windows, Linux

### Differentiation from BrowserOS
1. **Local AI**: GPT-OSS via Ollama instead of cloud APIs
2. **Privacy-First**: No data ever leaves user's machine
3. **macOS Focus**: Optimized for Apple Silicon and macOS UX
4. **Comet UX**: Superior conversational interface patterns

## Implementation Timeline

### Week 1: Foundation
- [ ] Complete Chromium source download
- [ ] Adapt BrowserOS build system for our project
- [ ] Create first patch: `gpt-oss-api.patch`
- [ ] Test basic patch application

### Week 2: Core Integration  
- [ ] Implement `ai-extension.patch`
- [ ] Create basic component extension
- [ ] Test extension loading in custom browser
- [ ] Connect to FastAPI backend

### Week 3: UI Development
- [ ] Implement `gpt-oss-sidebar.patch`
- [ ] Create Comet-inspired sidebar interface
- [ ] Integrate with GPT-OSS responses
- [ ] Add keyboard shortcuts and UX polish

### Week 4: Testing & Polish
- [ ] End-to-end workflow testing
- [ ] Performance optimization
- [ ] Error handling and edge cases
- [ ] macOS packaging and distribution

## Risk Mitigation

### Technical Risks
1. **Chromium Complexity**: Use BrowserOS patches as tested foundation
2. **API Changes**: Focus on stable Chromium APIs used by BrowserOS  
3. **Build Issues**: Start with proven BrowserOS build system
4. **Performance**: Profile and optimize for Apple Silicon

### Development Risks
1. **Patch Conflicts**: Apply patches incrementally with testing
2. **Chromium Updates**: Pin to specific Chromium version initially
3. **Local AI Issues**: Extensive testing with Ollama integration
4. **UX Complexity**: Start minimal, add features incrementally

This patch plan provides a clear, proven path to implementing our privacy-first AI browser by building on BrowserOS's solid technical foundation while differentiating with local GPT-OSS integration and superior UX.