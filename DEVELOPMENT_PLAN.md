# AI Browser Development Plan

## Current Status

✅ **Foundation Complete**
- Development environment with conda, Ollama, GPT-OSS 20B
- Python FastAPI backend with AI integration
- Comprehensive architecture document
- Git repository initialized
- depot_tools cloned for Chromium development

## Next Immediate Steps (This Week)

### 1. Set up Chromium Build Environment
```bash
# Add depot_tools to PATH
export PATH=$PWD/depot_tools:$PATH

# Create chromium directory and fetch source
mkdir chromium && cd chromium
fetch chromium

# This will take several hours and ~20GB of disk space
# We'll do this in phases to avoid timeouts
```

### 2. Fork BrowserOS Repository
- Clone BrowserOS repository: `https://github.com/browseros-ai/BrowserOS`
- Study their Chromium patches in `patches/nxtscape/`
- Understand their AI sidebar implementation
- Adapt for our GPT-OSS integration

### 3. Create Minimal Viable Browser
**Goal**: Get a basic Chromium browser running with AI sidebar

**Key Files to Modify**:
- `chrome/browser/ui/views/frame/browser_view.cc` - Add sidebar
- `chrome/browser/ui/webui/` - Create AI chat interface
- `chrome/common/chrome_switches.cc` - Add AI-related flags

**Implementation Approach**:
1. Start with BrowserOS patches as reference
2. Replace their AI backend calls with our Ollama integration
3. Simplify initially - just get basic chat working
4. Add browser automation APIs incrementally

## Technical Implementation Details

### Chromium Patches Needed

#### 1. AI Sidebar Panel
```cpp
// File: chrome/browser/ui/views/side_panel/ai_chat_coordinator.h
class AIChatCoordinator : public SidePanelEntryObserver {
public:
  AIChatCoordinator(Browser* browser);
  void ShowAIChat();
  void SendMessage(const std::string& message);
private:
  Browser* browser_;
  std::unique_ptr<AIBackendClient> ai_client_;
};
```

#### 2. JavaScript APIs for Page Access
```javascript
// Expose to content scripts
chrome.ai = {
  getPageContent: function() {
    // Access accessibility tree
    return chrome.automation.getTree();
  },
  
  performAction: function(action, parameters) {
    // Execute browser actions
    return chrome.runtime.sendMessage({
      type: 'AI_ACTION',
      action: action,
      params: parameters
    });
  }
};
```

#### 3. Backend Integration
```cpp
// File: chrome/browser/ai/ai_backend_client.cc
class AIBackendClient {
public:
  void SendChatMessage(const std::string& message, 
                      const PageContext& context,
                      base::OnceCallback<void(std::string)> callback);
                      
private:
  std::string ollama_endpoint_ = "http://localhost:11434";
};
```

### Build Process

#### 1. Configure Build
```bash
cd chromium/src
gn gen out/Release --args='
  is_debug=false
  is_official_build=false
  symbol_level=1
  enable_nacl=false
  enable_widevine=false
  proprietary_codecs=false
  ffmpeg_branding="Chromium"
  target_cpu="arm64"
  use_custom_libcxx=false
'
```

#### 2. Apply Our Patches
- Create `patches/ai_browser/` directory
- Implement patches for AI sidebar
- Add Ollama integration code
- Modify build files to include our components

#### 3. Build Browser
```bash
# This will take 2-4 hours on Apple Silicon
autoninja -C out/Release chrome
```

### Integration with Our Backend

#### WebSocket Connection
The Chromium browser will connect to our FastAPI backend via WebSocket:

```javascript
// AI sidebar frontend
const aiSocket = new WebSocket('ws://localhost:8001/ws');

aiSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chat_chunk') {
    appendToChat(data.content);
  } else if (data.type === 'action_result') {
    handleActionResult(data.result);
  }
};

function sendMessage(message) {
  const pageContext = chrome.ai.getPageContent();
  aiSocket.send(JSON.stringify({
    type: 'chat',
    message: message,
    context: pageContext
  }));
}
```

#### Page Content Extraction
```cpp
// C++ side - extract accessibility tree
std::string ExtractPageContext(content::WebContents* web_contents) {
  auto* ax_tree = web_contents->GetOrCreateRootBrowserAccessibilityManager();
  auto* root_node = ax_tree->GetRoot();
  
  // Convert accessibility tree to JSON
  base::Value::Dict context;
  context.Set("url", web_contents->GetLastCommittedURL().spec());
  context.Set("title", web_contents->GetTitle());
  context.Set("accessibility_tree", SerializeAXTree(root_node));
  
  return base::WriteJson(context).value_or("{}");
}
```

## Development Timeline

### Week 1: Chromium Setup
- **Day 1-2**: Complete Chromium source checkout (~4-6 hours download)
- **Day 3-4**: Study BrowserOS patches and understand integration points
- **Day 5-7**: Create minimal AI sidebar patch and test build

### Week 2: Basic Integration
- **Day 1-3**: Implement AI sidebar UI with basic chat interface
- **Day 4-5**: Connect sidebar to our FastAPI backend
- **Day 6-7**: Test page content extraction and basic AI responses

### Week 3: Browser Automation
- **Day 1-3**: Implement JavaScript APIs for browser actions
- **Day 4-5**: Add click/type/navigate functionality
- **Day 6-7**: Test end-to-end workflows (summarize page, simple actions)

### Week 4: Polish and Testing
- **Day 1-3**: Performance optimization and bug fixes
- **Day 4-5**: Add error handling and user feedback
- **Day 6-7**: Package as macOS application

## Risk Mitigation

### Technical Challenges
1. **Chromium Build Complexity**: Use BrowserOS patches as starting point
2. **Integration Issues**: Start minimal, add features incrementally
3. **Performance**: Profile early, optimize critical paths
4. **Stability**: Extensive testing on common websites

### Development Approach
- **Iterative Development**: Get something working quickly, then improve
- **Regular Commits**: Save progress frequently
- **Testing Strategy**: Manual testing on popular sites (Google, GitHub, Amazon)
- **Fallback Plan**: If Chromium proves too complex, pivot to Electron with deeper integration

## Success Metrics

### Week 1 Success
- [ ] Chromium builds successfully on local machine
- [ ] Basic AI sidebar appears in browser
- [ ] Can send message to GPT-OSS via sidebar

### Week 2 Success  
- [ ] Page content extraction working
- [ ] AI responds with page summaries
- [ ] Basic Q&A about current page works

### Week 3 Success
- [ ] Can click buttons via AI commands
- [ ] Can fill simple forms
- [ ] Multi-step actions work (e.g., "search for X then click first result")

### Week 4 Success
- [ ] Packaged as standalone macOS app
- [ ] Performance acceptable (no noticeable slowdown)
- [ ] Ready for user testing

## Next Actions

1. **Start Chromium Source Checkout** (run in background, will take hours)
2. **Study BrowserOS Architecture** while Chromium downloads
3. **Plan Minimal Patch Set** for first iteration
4. **Set up Build Scripts** and automation for testing

The key is starting with the smallest possible changes that demonstrate AI integration, then building up functionality incrementally. This approach minimizes risk while ensuring we have a working prototype quickly.