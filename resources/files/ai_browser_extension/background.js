/**
 * AI Browser Extension Background Script
 * 
 * Service worker that handles communication between the browser extension
 * and the local FastAPI backend with GPT-OSS integration.
 * 
 * Based on BrowserOS-agent architecture but adapted for local AI.
 */

// Configuration
const FASTAPI_BASE = 'http://localhost:8001';
const OLLAMA_BASE = 'http://localhost:11434';
const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds

// Service state
let isBackendHealthy = false;
let isOllamaHealthy = false;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Browser Extension installed');
  checkBackendHealth();
  
  // Set up periodic health checks
  setInterval(checkBackendHealth, HEALTH_CHECK_INTERVAL);
});

// Health check functions
async function checkBackendHealth() {
  try {
    // Check FastAPI backend
    const backendResponse = await fetch(`${FASTAPI_BASE}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    isBackendHealthy = backendResponse.ok;
    
    // Check Ollama service
    const ollamaResponse = await fetch(`${OLLAMA_BASE}/api/tags`, {
      method: 'GET'
    });
    isOllamaHealthy = ollamaResponse.ok;
    
    console.log(`Backend healthy: ${isBackendHealthy}, Ollama healthy: ${isOllamaHealthy}`);
  } catch (error) {
    isBackendHealthy = false;
    isOllamaHealthy = false;
    console.warn('Health check failed:', error);
  }
}

// Message handling - based on BrowserOS-agent message patterns
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.type) {
    case 'HEALTH_CHECK':
      handleHealthCheck(sendResponse);
      return true; // Async response
      
    case 'EXECUTE_AGENT_TASK':
      handleAgentTask(request.data, sendResponse);
      return true; // Async response
      
    case 'SEND_TO_AI':
      handleAIRequest(request.data, sendResponse);  
      return true; // Async response
      
    case 'GET_PAGE_CONTENT':
      getPageContent(request.tabId, sendResponse);
      return true; // Async response
      
    case 'EXECUTE_ACTION':
      executeAction(request.data, sendResponse);
      return true; // Async response
      
    default:
      console.warn('Unknown message type:', request.type);
      sendResponse({ success: false, error: 'Unknown message type' });
  }
});

// Health check handler
function handleHealthCheck(sendResponse) {
  sendResponse({
    success: true,
    data: {
      backend: isBackendHealthy,
      ollama: isOllamaHealthy,
      timestamp: Date.now()
    }
  });
}

// Agent task execution - core BrowserOS-agent pattern
async function handleAgentTask(data, sendResponse) {
  if (!isBackendHealthy) {
    sendResponse({
      success: false,
      error: 'Backend service is not available. Please ensure FastAPI server is running on port 8001.'
    });
    return;
  }
  
  try {
    const response = await fetch(`${FASTAPI_BASE}/api/agent/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: data.query,
        context: data.context || {},
        streaming: data.streaming || true
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    sendResponse({ success: true, data: result });
    
  } catch (error) {
    console.error('Agent task execution failed:', error);
    sendResponse({
      success: false, 
      error: error.message || 'Failed to execute agent task'
    });
  }
}

// AI request handler - similar to BrowserOS but local
async function handleAIRequest(data, sendResponse) {
  if (!isBackendHealthy) {
    sendResponse({
      success: false,
      error: 'AI backend is not available. Please check that Ollama and FastAPI are running.'
    });
    return;
  }

  try {
    const response = await fetch(`${FASTAPI_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: data.message,
        pageUrl: data.pageUrl,
        pageContent: data.pageContent,
        streaming: true
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    sendResponse({ success: true, data: result });

  } catch (error) {
    console.error('AI request failed:', error);
    sendResponse({
      success: false,
      error: error.message || 'Failed to process AI request'
    });
  }
}

// Page content extraction
async function getPageContent(tabId, sendResponse) {
  try {
    // If no tabId provided, get current active tab
    if (!tabId) {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs.length === 0) {
        throw new Error('No active tab found');
      }
      tabId = tabs[0].id;
    }

    // Execute content script to extract page data
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      function: extractPageContent
    });

    if (results && results[0] && results[0].result) {
      sendResponse({ success: true, data: results[0].result });
    } else {
      throw new Error('Failed to extract page content');
    }

  } catch (error) {
    console.error('Page content extraction failed:', error);
    sendResponse({
      success: false,
      error: error.message || 'Failed to extract page content'
    });
  }
}

// Content extraction function (injected into page)
function extractPageContent() {
  return {
    title: document.title || '',
    url: window.location.href || '',
    html: document.documentElement.outerHTML || '',
    text: document.body ? document.body.innerText || '' : '',
    timestamp: Date.now()
  };
}

// Browser action execution - adapted from BrowserOS tools
async function executeAction(actionData, sendResponse) {
  try {
    const { type, ...params } = actionData;
    
    switch (type) {
      case 'navigate':
        await executeNavigation(params);
        break;
      case 'click':
        await executeClick(params);
        break;
      case 'type':
        await executeType(params);
        break;
      case 'scroll':
        await executeScroll(params);
        break;
      default:
        throw new Error(`Unknown action type: ${type}`);
    }
    
    sendResponse({
      success: true,
      data: { message: `Successfully executed ${type} action` }
    });
    
  } catch (error) {
    console.error('Action execution failed:', error);
    sendResponse({
      success: false,
      data: { message: error.message || 'Action execution failed' }
    });
  }
}

// Navigation action
async function executeNavigation(params) {
  const { url, tabId } = params;
  
  if (tabId) {
    await chrome.tabs.update(tabId, { url: url });
  } else {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs.length > 0) {
      await chrome.tabs.update(tabs[0].id, { url: url });
    } else {
      await chrome.tabs.create({ url: url });
    }
  }
}

// Click action (simplified - would use chrome.aiBrowser API in real browser)
async function executeClick(params) {
  const { selector, x, y, tabId } = params;
  
  const targetTabId = tabId || (await chrome.tabs.query({ active: true, currentWindow: true }))[0].id;
  
  await chrome.scripting.executeScript({
    target: { tabId: targetTabId },
    function: (selector, x, y) => {
      if (selector) {
        const element = document.querySelector(selector);
        if (element) {
          element.click();
          return;
        }
      }
      
      if (x !== undefined && y !== undefined) {
        const element = document.elementFromPoint(x, y);
        if (element) {
          element.click();
        }
      }
    },
    args: [selector, x, y]
  });
}

// Type action
async function executeType(params) {
  const { text, selector, tabId } = params;
  
  const targetTabId = tabId || (await chrome.tabs.query({ active: true, currentWindow: true }))[0].id;
  
  await chrome.scripting.executeScript({
    target: { tabId: targetTabId },
    function: (text, selector) => {
      let element;
      
      if (selector) {
        element = document.querySelector(selector);
      } else {
        element = document.activeElement;
      }
      
      if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }
    },
    args: [text, selector]
  });
}

// Scroll action
async function executeScroll(params) {
  const { direction, amount, tabId } = params;
  
  const targetTabId = tabId || (await chrome.tabs.query({ active: true, currentWindow: true }))[0].id;
  
  await chrome.scripting.executeScript({
    target: { tabId: targetTabId },
    function: (direction, amount) => {
      const scrollAmount = amount || 500;
      
      switch (direction) {
        case 'up':
          window.scrollBy(0, -scrollAmount);
          break;
        case 'down':
          window.scrollBy(0, scrollAmount);
          break;
        case 'left':
          window.scrollBy(-scrollAmount, 0);
          break;
        case 'right':
          window.scrollBy(scrollAmount, 0);
          break;
        case 'top':
          window.scrollTo(0, 0);
          break;
        case 'bottom':
          window.scrollTo(0, document.body.scrollHeight);
          break;
      }
    },
    args: [direction, amount]
  });
}

// Error handling for unhandled promise rejections
self.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection in AI Browser extension:', event.reason);
});