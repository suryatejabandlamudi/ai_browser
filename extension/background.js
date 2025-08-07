// Background script for AI Browser Extension
// Handles communication between extension components and FastAPI backend

let backendUrl = 'http://localhost:8000';

// Extension installation/startup
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Browser Extension installed');
  
  // Enable side panel for all tabs
  chrome.sidePanel.setOptions({
    enabled: true,
    path: 'sidepanel.html'
  });
});

// Handle side panel toggle command
chrome.commands.onCommand.addListener((command) => {
  if (command === 'toggle-panel') {
    chrome.sidePanel.setOptions({
      enabled: true,
      path: 'sidepanel.html'
    });
  }
});

// Communication handler between content scripts and side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender, sendResponse);
  return true; // Keep the message channel open for async response
});

async function handleMessage(message, sender, sendResponse) {
  try {
    switch (message.type) {
      case 'GET_PAGE_CONTENT':
        const pageContent = await extractPageContent(sender.tab.id);
        sendResponse({ success: true, data: pageContent });
        break;
        
      case 'SEND_TO_AI':
        const aiResponse = await sendToAI(message.data);
        sendResponse({ success: true, data: aiResponse });
        break;
        
      case 'EXECUTE_ACTION':
        const actionResult = await executeAction(message.data, sender.tab.id);
        sendResponse({ success: true, data: actionResult });
        break;
        
      default:
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  } catch (error) {
    console.error('Error handling message:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Extract page content using accessibility tree and DOM
async function extractPageContent(tabId) {
  try {
    // Get basic page info
    const tab = await chrome.tabs.get(tabId);
    
    // Execute content script to get DOM content
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      function: extractDOMContent
    });
    
    const domContent = results[0].result;
    
    return {
      url: tab.url,
      title: tab.title,
      content: domContent,
      timestamp: Date.now()
    };
  } catch (error) {
    console.error('Error extracting page content:', error);
    throw error;
  }
}

// Function that runs in the content script context
function extractDOMContent() {
  // Get main content using Readability-style extraction
  const content = {
    title: document.title,
    text: document.body.innerText.slice(0, 10000), // Limit to 10k chars
    html: document.body.innerHTML.slice(0, 20000), // Limit to 20k chars
    
    // Extract interactive elements
    interactive: Array.from(document.querySelectorAll('button, input, a, select, textarea')).map(el => ({
      tag: el.tagName.toLowerCase(),
      text: el.innerText || el.value || el.getAttribute('aria-label') || '',
      id: el.id,
      classes: el.className,
      type: el.type || '',
      href: el.href || '',
      rect: el.getBoundingClientRect()
    })).slice(0, 50) // Limit to 50 elements
  };
  
  return content;
}

// Send message to FastAPI backend
async function sendToAI(data) {
  try {
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: data.message,
        page_url: data.pageUrl,
        page_content: data.pageContent
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error communicating with AI backend:', error);
    throw error;
  }
}

// Execute browser actions based on AI response
async function executeAction(action, tabId) {
  try {
    switch (action.type) {
      case 'CLICK':
        return await executeClick(action, tabId);
      case 'TYPE':
        return await executeType(action, tabId);
      case 'NAVIGATE':
        return await executeNavigate(action, tabId);
      case 'SCROLL':
        return await executeScroll(action, tabId);
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  } catch (error) {
    console.error('Error executing action:', error);
    throw error;
  }
}

async function executeClick(action, tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId: tabId },
    function: (selector) => {
      const element = document.querySelector(selector);
      if (element) {
        element.click();
        return { success: true, message: 'Element clicked' };
      } else {
        return { success: false, message: 'Element not found' };
      }
    },
    args: [action.selector]
  });
  
  return results[0].result;
}

async function executeType(action, tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId: tabId },
    function: (selector, text) => {
      const element = document.querySelector(selector);
      if (element) {
        element.value = text;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        return { success: true, message: 'Text typed' };
      } else {
        return { success: false, message: 'Element not found' };
      }
    },
    args: [action.selector, action.text]
  });
  
  return results[0].result;
}

async function executeNavigate(action, tabId) {
  await chrome.tabs.update(tabId, { url: action.url });
  return { success: true, message: 'Navigation started' };
}

async function executeScroll(action, tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId: tabId },
    function: (direction, amount) => {
      const scrollAmount = amount || 500;
      if (direction === 'down') {
        window.scrollBy(0, scrollAmount);
      } else if (direction === 'up') {
        window.scrollBy(0, -scrollAmount);
      }
      return { success: true, message: `Scrolled ${direction}` };
    },
    args: [action.direction, action.amount]
  });
  
  return results[0].result;
}