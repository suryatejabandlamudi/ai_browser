# AI Browser Knowledge Base

This document captures key insights, technical decisions, and learnings from the development process that will be valuable for future sessions and team members.

## Executive Summary

We're building a privacy-first AI browser for macOS inspired by Perplexity Comet but using local LLMs. Our approach combines BrowserOS's proven Chromium patching methodology with Comet's superior UX patterns, powered by GPT-OSS 20B running locally via Ollama.

## Key Technical Decisions & Rationale

### 1. Real Browser vs Extension
**Decision**: Build custom Chromium browser, not browser extension
**Rationale**: 
- Full control over browser internals and APIs
- Native performance and integration
- Can access Accessibility Tree directly
- No extension permission limitations
- Comet and BrowserOS prove this approach works

### 2. Local LLM vs Cloud APIs
**Decision**: GPT-OSS 20B via Ollama (local processing)
**Rationale**:
- Complete privacy (data never leaves machine)
- No subscription costs (Comet costs $200/month)
- Apple Silicon optimization via Metal
- No internet dependency for AI features
- Aligns with Apple's privacy-first philosophy

### 3. macOS-Only Focus
**Decision**: Build exclusively for macOS
**Rationale**:
- Simplifies development and testing
- Apple Silicon provides best local LLM performance
- Smaller, focused user base initially
- Can optimize for Metal acceleration
- Easier app distribution and signing

### 4. BrowserOS + Comet Hybrid Approach
**Decision**: Use BrowserOS patches as foundation, adapt Comet UX
**Rationale**:
- BrowserOS solved the technical Chromium integration
- Comet's UX patterns are superior (side panel, context)
- Don't reinvent the wheel, adapt proven solutions
- Focus on local AI integration, not browser plumbing

## Architecture Insights

### BrowserOS Technical Architecture
- **Patch System**: ~30 .patch files modify Chromium source
- **Key Patches**:
  - `browserOS-API.patch` (760 lines) - Main browser APIs
  - `ai-chat-extension.patch` - Extension integration
  - `embed-third-party-llm-in-side-panel.patch` - UI integration
- **Build Process**: Python build system (`build/build.py`)
- **Extension Integration**: Built-in component extension
- **API Layer**: Custom browserOS namespace for page interaction

### Perplexity Comet Architecture (July 2025)
- **Platform**: Chromium-based browser
- **AI Integration**: Side panel assistant with persistent context
- **UX Pattern**: Conversational browsing with memory across tabs
- **Pricing**: $200/month subscription (Max plan)
- **LLMs**: GPT-4o, Claude 4.0 Sonnet, Perplexity Sonar
- **Key Features**:
  - Context threading across sessions
  - Natural language commands
  - Task automation (email, booking, etc.)
  - Page content integration

### Our Hybrid Approach
```
BrowserOS Technical Foundation + Comet UX Patterns = Our AI Browser
├── Chromium Patches (from BrowserOS)
├── Side Panel UI (inspired by Comet)
├── Local LLM Integration (our innovation)
└── macOS Native Packaging (our focus)
```

## Technical Implementation Details

### Chromium Build Process
1. **Source Download**: 55GB, 4-6 hours via gclient
2. **Patch Application**: Apply .patch files to modify Chromium
3. **Build Configuration**: macOS-specific GN args for Apple Silicon
4. **Compilation**: 2-4 hours on Apple Silicon
5. **Packaging**: macOS app bundle with DMG installer

### Local AI Integration Stack
```
User ←→ Chromium Browser ←→ Built-in Extension ←→ FastAPI Backend ←→ Ollama ←→ GPT-OSS 20B
```

- **Browser**: Custom Chromium with AI sidebar
- **Extension**: Component extension (built into browser)
- **Backend**: Python FastAPI server (port 8001)
- **AI**: Ollama serving GPT-OSS 20B (port 11434)
- **Communication**: HTTP/WebSocket between layers

### Page Content Extraction Strategy
1. **Accessibility Tree**: Use Chrome's a11y APIs for semantic content
2. **Readability.js**: Clean main content extraction
3. **Interactive Elements**: Identify clickable/typeable elements
4. **Context Building**: Combine page content with user intent
5. **Action Planning**: LLM generates browser automation steps

## Development Workflow & Best Practices

### Repository Structure
```
ai_browser/
├── ARCHITECTURE.md       # System design (updated with latest)
├── DEVELOPMENT_PLAN.md   # Implementation timeline  
├── STATUS.md            # Current progress tracking
├── CLAUDE.md           # Claude Code guidance
├── KNOWLEDGE_BASE.md   # This file
├── backend/            # FastAPI + AI integration (ready)
│   ├── chromium/       # Chromium source (60% downloaded)
│   └── BrowserOS/      # Reference implementation
├── extension/          # Testing prototype (complete)
└── README.md          # Project overview
```

### Git Workflow
- Regular commits with detailed messages
- Status updates after major progress
- Knowledge capture in documents
- All insights preserved for future sessions
- Remote backup of all progress

### Testing Strategy
1. **Extension Prototype**: Rapid iteration and testing
2. **FastAPI Backend**: Direct API testing
3. **Browser Integration**: Manual testing on popular sites
4. **Performance**: Profiling LLM response times
5. **User Testing**: Dogfooding on real browsing tasks

## Critical Dependencies & Requirements

### Software Dependencies
- **Xcode Command Line Tools**: For Chromium compilation
- **depot_tools**: Google's Chromium build tools
- **Python 3.13**: FastAPI backend runtime
- **Conda**: Environment management
- **Ollama**: Local LLM serving
- **Node.js**: For extension development (testing)

### Hardware Requirements
- **Platform**: macOS (Apple Silicon preferred)
- **RAM**: 16GB+ (for Chromium compilation)
- **Storage**: 100GB+ free space
- **Internet**: Fast connection for initial Chromium download

### Model Requirements
- **GPT-OSS 20B**: 13GB model file
- **VRAM**: Apple Silicon unified memory
- **Performance**: Metal acceleration required

## Key Challenges & Solutions

### Challenge 1: Chromium Download Size
- **Problem**: 55GB download, 4-6 hours
- **Solution**: Background download, shallow clone options
- **Mitigation**: Good documentation, progress tracking

### Challenge 2: Complex Patch System  
- **Problem**: BrowserOS has 30+ patches to understand
- **Solution**: Start with core patches, adapt incrementally
- **Strategy**: Focus on AI sidebar and browserOS API first

### Challenge 3: Local LLM Performance
- **Problem**: Need fast response times for good UX
- **Solution**: Apple Silicon + Metal optimization
- **Backup**: Streaming responses, async processing

### Challenge 4: Browser Extension vs Real Browser
- **Problem**: Extension has limitations, real browser is complex
- **Solution**: Use extension for rapid prototyping, browser for production
- **Workflow**: Test in extension, implement in browser

## Competitive Analysis

### Perplexity Comet (Cloud)
**Strengths**: Polished UX, powerful cloud LLMs, well-funded
**Weaknesses**: $200/month cost, privacy concerns, internet dependency
**Our Advantage**: Free, private, local processing

### BrowserOS (Open Source)
**Strengths**: Technical foundation, Chromium patches, open source
**Weaknesses**: Complex setup, limited AI integration, no local LLM
**Our Advantage**: Better AI integration, local privacy, macOS focus

### Arc Browser (Design-focused)
**Strengths**: Beautiful UX, productivity features, active community
**Weaknesses**: No AI integration, closed source, limited automation
**Our Advantage**: AI-first design, automation capabilities, open source

### Chrome + Extensions
**Strengths**: Mature platform, extension ecosystem, wide adoption
**Weaknesses**: Extension limitations, no deep AI integration, privacy issues
**Our Advantage**: Native AI integration, local processing, better UX

## Future Enhancement Roadmap

### Phase 1: Core Browser (Weeks 1-4)
- Complete Chromium download and build
- Apply BrowserOS patches
- Basic AI sidebar integration
- Local GPT-OSS connection

### Phase 2: AI Features (Weeks 5-8)
- Conversational context across tabs
- Page content understanding
- Basic browser automation
- Task execution capabilities

### Phase 3: UX Polish (Weeks 9-12)
- Comet-inspired interface refinements
- Performance optimization
- Error handling and recovery
- User onboarding flow

### Phase 4: Distribution (Weeks 13-16)
- macOS app packaging
- DMG installer creation
- Basic update mechanism
- Documentation and website

## BrowserOS-Agent Deep Analysis

### Key Architecture Insights

**Agent System**:
- **Unified BrowserAgent** - Single agent handles all tasks through classification and planning
- **LangChain Integration** - Uses `@langchain` packages for tool binding and LLM interaction
- **Streaming Support** - Real-time response streaming with `llm.stream()` instead of `llm.invoke()`
- **Tool System** - Modular tools using `DynamicStructuredTool` with Zod schemas

**Critical Agent Components**:
```typescript
// Core execution flow
User Query → NxtScape.run() → BrowserAgent.execute()
                                        ↓
                              ClassificationTool
                                   ↙        ↘
                            Simple Task   Complex Task
                                ↓              ↓
                          Direct Tool     PlannerTool
                           Execution      (3 steps)
                                ↓              ↓
                              Tool         Execute Each
                             Result      Step with Tools
```

**Tool Architecture**:
- **ToolManager** - Centralized tool registration and management
- **Tools as LangChain DynamicStructuredTool** - Each tool is a structured function with Zod schema
- **Tool Types**: Navigation, Interaction, Planning, Classification, Extraction, Tab Management
- **Tool Results**: Standardized `{ ok: boolean, output?: any, error?: string }` format

**LLM Provider Strategy**:
- **Multiple Providers** - OpenAI, Anthropic, Ollama, Google, custom Nxtscape proxy
- **LangChainProvider Singleton** - Centralized LLM instance management
- **Streaming Architecture** - Progressive tool call building in streams
- **Model Capabilities** - Context window and capability tracking

### Our GPT-OSS Adaptation Strategy

**Key Adaptations for Local AI**:
1. **Replace Cloud LLM** - Use Ollama + GPT-OSS instead of OpenAI/Claude
2. **Simplify Provider** - Single local provider instead of multiple cloud providers  
3. **Enhanced FastAPI** - Bridge between browser extension and Ollama
4. **Local Streaming** - Maintain streaming UX with local model

**Implementation Approach**:
```typescript
// Our LangChain + Ollama integration
export class LocalLangChainProvider {
  private static instance: BaseChatModel;
  
  static async getInstance(): Promise<BaseChatModel> {
    if (!this.instance) {
      this.instance = new ChatOllama({
        baseUrl: 'http://localhost:11434',
        model: 'gpt-oss:20b',
        temperature: 0.7,
        streaming: true
      });
    }
    return this.instance;
  }
}
```

**BrowserOS Tool System Adaptation**:
- **Copy Tool Architecture** - Use their DynamicStructuredTool approach
- **Adapt for Chrome APIs** - Replace puppeteer with Chrome extension APIs
- **Local FastAPI Bridge** - Tools communicate via our FastAPI backend
- **Maintain Streaming** - Keep real-time user feedback

### Technical Implementation Details

**BrowserOS Chrome Extension Structure**:
```
BrowserOS-agent/
├── src/
│   ├── background/           # Service worker
│   ├── content/             # DOM interaction
│   ├── sidepanel/           # React UI
│   └── lib/
│       ├── agent/           # BrowserAgent core
│       ├── browser/         # puppeteer-core integration  
│       ├── tools/           # Tool implementations
│       ├── llm/            # LangChain providers
│       └── runtime/        # ExecutionContext, MessageManager
```

**Key Files for Our Adaptation**:
- `BrowserAgent.ts` - Agent execution loop with planning
- `ToolManager.ts` - Tool registration system
- `NavigationTool.ts` - Browser navigation example
- `LangChainProvider.ts` - LLM integration pattern
- `ExecutionContext.ts` - Runtime state management

**Chrome Extension vs Browser Integration**:
- **BrowserOS-agent** - Chrome extension using puppeteer-core + debugger API
- **Our Approach** - Native Chromium browser with built-in extension
- **Advantage** - Full browser control vs extension limitations
- **Implementation** - Apply BrowserOS agent patterns to native browser

### Integration with Our Patch System

**Patch 1: Native Agent Integration**
```cpp
// chrome/browser/extensions/api/ai_browser/ai_browser_agent.h
class AIBrowserAgent {
 public:
  // Copy BrowserOS-agent execution patterns
  async ExecuteTask(const std::string& user_query);
  
 private:
  // Integration with local FastAPI + GPT-OSS
  std::unique_ptr<LocalLLMProvider> llm_provider_;
  std::unique_ptr<ToolManager> tool_manager_;
};
```

**Patch 2: Tool System Integration**
```cpp
// Native Chrome APIs instead of puppeteer
namespace ai_browser {
  // Navigation tool using native Chrome navigation
  void NavigateToUrl(const std::string& url, base::OnceCallback callback);
  
  // Interaction tool using Chrome accessibility APIs  
  void ClickElement(const gfx::Point& position, base::OnceCallback callback);
}
```

**Patch 3: FastAPI Bridge**
```javascript
// Extension communicates with our FastAPI backend
const AI_BACKEND = 'http://localhost:8001';

async function executeAgentTask(query) {
  const response = await fetch(`${AI_BACKEND}/api/agent/execute`, {
    method: 'POST',
    body: JSON.stringify({ query, context: await getPageContext() })
  });
  return response.json();
}
```

## Lessons Learned

### What Worked Well
1. **Research First**: Understanding Comet and BrowserOS saved weeks of work
2. **Extension Prototype**: Rapid testing and validation approach
3. **Documentation**: Comprehensive docs enable future continuation
4. **Local Focus**: macOS-only simplifies everything
5. **Git Discipline**: Regular commits preserve all progress

### What to Avoid
1. **Don't Reinvent**: Use BrowserOS patches as foundation
2. **Don't Over-engineer**: Start simple, add features incrementally  
3. **Don't Ignore UX**: Comet's patterns are proven to work
4. **Don't Skip Testing**: Extension prototype enables rapid iteration
5. **Don't Forget Privacy**: Local processing is our key differentiator

### Technical Gotchas
1. **Chromium Size**: Much larger than expected (55GB)
2. **Nested Git Repos**: Need proper .gitignore for submodules
3. **Build Time**: Compilation takes hours, not minutes
4. **Patch Complexity**: BrowserOS patches are intricate
5. **Extension Limits**: Real browser needed for full functionality

## Success Metrics & KPIs

### Technical Metrics
- **Build Success**: Browser compiles and launches
- **AI Response Time**: <3 seconds for typical queries
- **Memory Usage**: <2GB additional RAM over base browser
- **Crash Rate**: <1% of user sessions

### User Experience Metrics
- **Setup Time**: <10 minutes from download to working
- **Task Success Rate**: >90% for common automation tasks
- **User Satisfaction**: Positive feedback on local privacy
- **Performance**: Feels as fast as regular Chrome

### Business Metrics
- **Downloads**: Track DMG downloads from GitHub
- **GitHub Stars**: Open source community adoption
- **Issue Reports**: Quality feedback from users
- **Retention**: Users who continue using after first week

## Development Environment Setup

### Complete Setup Commands
```bash
# 1. Install dependencies
brew install ollama python@3.13 node

# 2. Set up conda environment  
conda create -n ai_browser_env python=3.13
conda activate ai_browser_env

# 3. Install Ollama model
ollama pull gpt-oss:20b

# 4. Clone and setup project
git clone https://github.com/suryatejabandlamudi/ai_browser.git
cd ai_browser
pip install -r backend/requirements.txt

# 5. Start backend
python -m backend.main

# 6. Load extension in Chrome (for testing)
# Chrome > Extensions > Developer Mode > Load Unpacked > extension/
```

### Directory Setup for Chromium Build
```bash
# Navigate to chromium directory
cd backend/chromium

# Set up depot_tools path
export PATH="../depot_tools:$PATH"

# Start/continue download
gclient sync

# Verify completion (~55GB expected)
du -sh . && ls -la src/
```

This knowledge base should provide comprehensive context for future development sessions and enable smooth continuation of the project by any team member.