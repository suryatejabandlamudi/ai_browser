# Chrome Extension Load Test Instructions

## Real Working AI Browser Extension Test

### Prerequisites ✅
1. **Backend Running**: ✅ Confirmed at http://localhost:8000/health
2. **Icons Created**: ✅ 16px, 48px, 128px icons generated 
3. **WebSocket Endpoint**: ✅ Fixed to use `/ws/chat`
4. **All Files Present**: ✅ manifest.json, sidepanel.html/js/css, background.js, content.js

### Load Extension Steps

1. **Open Chrome/Edge**: Navigate to chrome://extensions/
2. **Enable Developer Mode**: Toggle in top-right corner
3. **Load Extension**: Click "Load unpacked" button
4. **Select Folder**: Choose `/Users/suryatejabandlamudi/personal_projects/apple/ai_browser/extension/`

### Expected Results After Loading

#### ✅ Extension Should Load Without Errors
- Extension appears in extensions list
- AI Browser icon visible in extensions toolbar
- No error messages in chrome://extensions/

#### ✅ Side Panel Should Be Available
- Click the extension icon OR use Cmd+E (Mac) / Ctrl+E (Windows)
- Side panel opens on right side of browser
- Shows "AI Browser" header with status indicator

#### ✅ UI Elements Should Work
- **Status Indicator**: Shows "Connected - Ready for AI assistance" (green dot)
- **Current Page Info**: Displays current tab title and URL
- **Chat Interface**: Welcome message with capabilities list
- **Input Field**: Text area with placeholder text
- **Quick Actions**: "Summarize Page", "Extract Key Info", "Help" buttons

#### ✅ Backend Connection Should Work
- WebSocket connects to ws://127.0.0.1:8000/ws/chat
- Status shows "Connected" (not "Disconnected" or "Connection error")
- No error messages in browser console (F12 → Console)

### Functional Tests

#### Test 1: Basic Chat
1. Type "Hello" in the input field
2. Click send button or press Enter
3. **Expected**: 
   - Message appears in chat as user message
   - AI responds within 4-5 seconds (our current response time)
   - Response appears as AI message bubble

#### Test 2: Page Analysis  
1. Navigate to any website (e.g., https://example.com)
2. Type "What is this page about?" 
3. Click send
4. **Expected**:
   - Extension reads current page content
   - AI analyzes page and provides summary
   - Response includes relevant page information

#### Test 3: WebSocket Streaming
1. Type any message and send
2. **Expected**:
   - "Thinking..." indicator appears immediately
   - Real-time streaming messages show AI processing
   - Final response appears without page reload

#### Test 4: Quick Actions
1. Click "Summarize Page" button
2. **Expected**:
   - Input field fills with "Please summarize this page for me."
   - Can send message normally
   - AI provides page summary

### Debugging Common Issues

#### Extension Won't Load
- Check manifest.json syntax
- Verify all referenced files exist (icons, scripts)
- Check for JavaScript errors in background.js

#### Side Panel Won't Open
- Try clicking extension icon directly
- Use keyboard shortcut (Cmd/Ctrl + E)
- Check if sidePanel permission is granted

#### Can't Connect to Backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console for WebSocket errors
- Ensure no CORS issues (backend allows localhost)

#### No AI Responses
- Check if Ollama is running: `ollama list`
- Verify gpt-oss:20b model is available
- Check backend logs for errors

### Success Criteria

**Extension is WORKING if:**
1. ✅ Loads without errors
2. ✅ Side panel opens and shows UI
3. ✅ Connects to backend (green status dot)
4. ✅ Can send messages and receive AI responses
5. ✅ WebSocket streaming shows real-time updates
6. ✅ Page content is read and analyzed correctly

**Extension is BROKEN if:**
- Won't load (manifest errors)
- Side panel blank/won't open
- Status shows "Connection error" (red dot)
- Messages sent but no AI response
- JavaScript errors in console
- WebSocket connection fails

---

## Installation Guide for User

### Step 1: Start the Backend
```bash
cd ai_browser/backend
python main.py
```
Wait for "Application startup complete" message.

### Step 2: Install Extension
1. Open Chrome/Edge
2. Go to chrome://extensions/
3. Enable "Developer mode" 
4. Click "Load unpacked"
5. Select the `ai_browser/extension/` folder

### Step 3: Test It Works
1. Click the AI Browser extension icon
2. Side panel should open with welcome message
3. Status should show "Connected" with green dot
4. Type "Hello" and press Enter
5. Should get AI response in 4-5 seconds

**If it works = Real functioning AI browser extension! 🎉**
**If it fails = Need to debug and fix the broken parts ⚠️**

This is the honest test to see if we have a real working extension vs just placeholder code.