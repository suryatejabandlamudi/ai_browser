// Content script for AI Browser Extension
// Runs on all pages to facilitate DOM interaction and page analysis

(function() {
  'use strict';
  
  // Prevent multiple injections
  if (window.aiBrowserExtensionInjected) {
    return;
  }
  window.aiBrowserExtensionInjected = true;
  
  // Load accessibility integration
  const accessibilityScript = document.createElement('script');
  accessibilityScript.src = chrome.runtime.getURL('accessibility.js');
  accessibilityScript.onload = function() {
    console.log('[AI Browser] Accessibility integration loaded');
  };
  (document.head || document.documentElement).appendChild(accessibilityScript);
  
  // Enhanced element finder that uses multiple strategies
  function findElement(description) {
    const strategies = [
      // By text content
      () => Array.from(document.querySelectorAll('*')).find(el => 
        el.textContent && el.textContent.toLowerCase().includes(description.toLowerCase())
      ),
      
      // By aria-label
      () => document.querySelector(`[aria-label*="${description}"]`),
      
      // By placeholder
      () => document.querySelector(`[placeholder*="${description}"]`),
      
      // By title
      () => document.querySelector(`[title*="${description}"]`),
      
      // By id or class containing keywords
      () => document.querySelector(`[id*="${description.toLowerCase().replace(/\s+/g, '')}"], [class*="${description.toLowerCase().replace(/\s+/g, '')}"]`)
    ];
    
    for (const strategy of strategies) {
      try {
        const element = strategy();
        if (element && isVisible(element)) {
          return element;
        }
      } catch (e) {
        continue;
      }
    }
    
    return null;
  }
  
  // Check if element is visible
  function isVisible(element) {
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && 
           getComputedStyle(element).visibility !== 'hidden' &&
           getComputedStyle(element).display !== 'none';
  }
  
  // Extract comprehensive page information
  function extractPageInfo() {
    return {
      url: window.location.href,
      title: document.title,
      content: {
        text: document.body.innerText.slice(0, 15000),
        
        // Interactive elements with better context
        interactive: Array.from(document.querySelectorAll('button, input, a, select, textarea, [role="button"], [onclick]'))
          .filter(isVisible)
          .slice(0, 100)
          .map(el => {
            const rect = el.getBoundingClientRect();
            return {
              tag: el.tagName.toLowerCase(),
              text: getElementText(el),
              id: el.id,
              classes: el.className,
              type: el.type || el.getAttribute('role') || '',
              href: el.href || '',
              ariaLabel: el.getAttribute('aria-label') || '',
              placeholder: el.placeholder || '',
              position: {
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
              },
              selector: generateSelector(el)
            };
          }),
        
        // Form information
        forms: Array.from(document.forms).slice(0, 10).map(form => ({
          action: form.action,
          method: form.method,
          fields: Array.from(form.elements).slice(0, 20).map(field => ({
            name: field.name,
            type: field.type,
            placeholder: field.placeholder || '',
            required: field.required
          }))
        })),
        
        // Headings for structure
        headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
          .slice(0, 20)
          .map(h => ({
            level: h.tagName.toLowerCase(),
            text: h.textContent.trim().slice(0, 200)
          }))
      },
      metadata: {
        description: document.querySelector('meta[name="description"]')?.content || '',
        keywords: document.querySelector('meta[name="keywords"]')?.content || '',
        ogTitle: document.querySelector('meta[property="og:title"]')?.content || '',
        ogDescription: document.querySelector('meta[property="og:description"]')?.content || ''
      }
    };
  }
  
  function getElementText(element) {
    return element.textContent || element.value || element.alt || 
           element.getAttribute('aria-label') || element.title || '';
  }
  
  // Generate a robust CSS selector for an element
  function generateSelector(element) {
    // If element has a unique ID, use it
    if (element.id && document.querySelectorAll(`#${element.id}`).length === 1) {
      return `#${element.id}`;
    }
    
    // Try aria-label
    if (element.getAttribute('aria-label')) {
      return `[aria-label="${element.getAttribute('aria-label')}"]`;
    }
    
    // Try data attributes
    const dataAttrs = Array.from(element.attributes).filter(attr => attr.name.startsWith('data-'));
    if (dataAttrs.length > 0) {
      const attr = dataAttrs[0];
      return `[${attr.name}="${attr.value}"]`;
    }
    
    // Build path-based selector as fallback
    const path = [];
    let current = element;
    
    while (current && current !== document.body) {
      let selector = current.tagName.toLowerCase();
      
      if (current.className) {
        selector += '.' + Array.from(current.classList).join('.');
      }
      
      // Add nth-child if needed for uniqueness
      const siblings = Array.from(current.parentElement?.children || [])
        .filter(sibling => sibling.tagName === current.tagName);
      
      if (siblings.length > 1) {
        const index = siblings.indexOf(current) + 1;
        selector += `:nth-child(${index})`;
      }
      
      path.unshift(selector);
      current = current.parentElement;
      
      // Limit depth
      if (path.length > 5) break;
    }
    
    return path.join(' > ');
  }
  
  // Enhanced click function with multiple fallbacks
  function smartClick(selector) {
    let element;
    
    // Try direct selector first
    element = document.querySelector(selector);
    
    // If not found, try finding by description
    if (!element) {
      element = findElement(selector);
    }
    
    if (element && isVisible(element)) {
      // Try multiple click methods
      try {
        element.click();
        return { success: true, message: 'Clicked successfully' };
      } catch (e) {
        // Fallback to dispatch event
        try {
          element.dispatchEvent(new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: window
          }));
          return { success: true, message: 'Clicked via event dispatch' };
        } catch (e2) {
          return { success: false, message: 'Click failed: ' + e2.message };
        }
      }
    } else {
      return { success: false, message: 'Element not found or not visible' };
    }
  }
  
  // Enhanced type function
  function smartType(selector, text) {
    let element = document.querySelector(selector);
    
    if (!element) {
      element = findElement(selector);
    }
    
    if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {
      try {
        // Focus the element first
        element.focus();
        
        // Clear existing content
        element.value = '';
        
        // Type the text
        element.value = text;
        
        // Trigger events
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        
        return { success: true, message: 'Text typed successfully' };
      } catch (e) {
        return { success: false, message: 'Typing failed: ' + e.message };
      }
    } else {
      return { success: false, message: 'Element not found or not typeable' };
    }
  }
  
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
      case 'EXTRACT_PAGE_INFO':
        sendResponse(extractPageInfo());
        break;
        
      case 'SMART_CLICK':
        sendResponse(smartClick(message.selector));
        break;
        
      case 'SMART_TYPE':
        sendResponse(smartType(message.selector, message.text));
        break;
        
      case 'HIGHLIGHT_ELEMENT':
        highlightElement(message.selector);
        sendResponse({ success: true });
        break;
    }
  });
  
  // Visual feedback for element highlighting
  function highlightElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
      const originalStyle = element.style.outline;
      element.style.outline = '3px solid #ff6b35';
      element.style.outlineOffset = '2px';
      
      setTimeout(() => {
        element.style.outline = originalStyle;
      }, 2000);
    }
  }
  
  console.log('AI Browser Extension content script loaded');
})();