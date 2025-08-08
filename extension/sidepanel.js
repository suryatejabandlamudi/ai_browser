// Side panel JavaScript for AI Browser Extension

class AIBrowserSidePanel {
    constructor() {
        this.currentTab = null;
        this.pageContent = null;
        this.isProcessing = false;
        this.websocket = null;
        this.currentStreamingMessage = null;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadCurrentTab();
        this.initializeWebSocket();
        
        console.log('AI Browser Side Panel initialized');
    }
    
    initializeElements() {
        this.elements = {
            status: document.getElementById('status'),
            pageTitle: document.getElementById('pageTitle'),
            pageUrl: document.getElementById('pageUrl'),
            refreshBtn: document.getElementById('refreshBtn'),
            chatContainer: document.getElementById('chatContainer'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn')
        };
    }
    
    attachEventListeners() {
        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (Shift+Enter for new line)
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input changes
        this.elements.messageInput.addEventListener('input', () => {
            this.updateSendButton();
            this.adjustTextareaHeight();
        });
        
        // Refresh button
        this.elements.refreshBtn.addEventListener('click', () => this.refreshPageContent());
        
        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', () => this.handleQuickAction(btn.dataset.action));
        });
    }
    
    async loadCurrentTab() {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs.length > 0) {
                this.currentTab = tabs[0];
                this.updatePageInfo();
                await this.refreshPageContent();
                this.updateStatus('ready', 'Ready');
            }
        } catch (error) {
            console.error('Error loading current tab:', error);
            this.updateStatus('error', 'Error loading page');
        }
    }
    
    updatePageInfo() {
        if (this.currentTab) {
            this.elements.pageTitle.textContent = this.currentTab.title || 'Untitled Page';
            this.elements.pageUrl.textContent = this.currentTab.url || '';
        }
    }
    
    async refreshPageContent() {
        if (!this.currentTab) return;
        
        try {
            this.updateStatus('connecting', 'Loading page content...');
            
            const response = await chrome.runtime.sendMessage({
                type: 'GET_PAGE_CONTENT',
                tabId: this.currentTab.id
            });
            
            if (response.success) {
                this.pageContent = response.data;
                this.updateStatus('ready', 'Ready');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Error refreshing page content:', error);
            this.updateStatus('error', 'Failed to load page content');
        }
    }
    
    updateStatus(type, text) {
        this.elements.status.className = `status ${type}`;
        this.elements.status.querySelector('.status-text').textContent = text;
    }
    
    updateSendButton() {
        const hasText = this.elements.messageInput.value.trim().length > 0;
        this.elements.sendBtn.disabled = !hasText || this.isProcessing;
    }
    
    adjustTextareaHeight() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    initializeWebSocket() {
        // Initialize WebSocket connection for streaming AI responses
        this.connectWebSocket();
    }
    
    connectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        const clientId = this.generateClientId();
        const wsUrl = `ws://127.0.0.1:8000/ws/${clientId}`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected for streaming AI responses');
                this.updateStatus('ready', 'Connected - Ready for AI assistance');
                
                // Show connection success message
                this.addSystemMessage('🚀 Connected to AI Browser - Ready for intelligent automation!');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleStreamingMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected', 'Disconnected - Attempting to reconnect...');
                this.addSystemMessage('❌ Connection lost - Reconnecting...', 'error');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('error', 'Connection error');
                this.addSystemMessage('⚠️ Connection error - Check if backend is running', 'error');
            };
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.updateStatus('error', 'Failed to connect to AI backend');
            this.addSystemMessage('❌ Failed to connect to AI backend - Check if server is running', 'error');
        }
    }
    
    generateClientId() {
        return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    handleStreamingMessage(message) {
        console.log('Streaming message received:', message);
        
        const { type, content, data, timestamp } = message;
        
        switch (type) {
            case 'connection':
                this.addSystemMessage(content, 'success');
                break;
                
            case 'thinking':
                this.removeTypingIndicator();
                this.updateCurrentStreamingMessage(content, 'thinking');
                break;
                
            case 'tool_execution':
                this.updateCurrentStreamingMessage(content, 'tool');
                break;
                
            case 'ai_response':
                this.addAIMessage(content, data);
                this.clearCurrentStreamingMessage();
                break;
                
            case 'completion':
                this.addSystemMessage(content, 'success');
                this.clearCurrentStreamingMessage();
                this.finishProcessing();
                break;
                
            case 'error':
                this.addSystemMessage(content, 'error');
                this.clearCurrentStreamingMessage();
                this.finishProcessing();
                break;
                
            default:
                console.log('Unknown message type:', type);
        }
    }
    
    updateCurrentStreamingMessage(content, messageType) {
        // Update or create current streaming message
        if (this.currentStreamingMessage) {
            this.currentStreamingMessage.querySelector('.message-content').innerHTML = this.formatMessageContent(content);
        } else {
            this.currentStreamingMessage = this.createStreamingMessage(content, messageType);
            this.elements.chatContainer.appendChild(this.currentStreamingMessage);
        }
        
        this.scrollToBottom();
    }
    
    createStreamingMessage(content, messageType) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ai-message streaming ${messageType}`;
        
        const icon = this.getMessageIcon(messageType);
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-icon">${icon}</span>
                <span class="message-timestamp">${new Date().toLocaleTimeString()}</span>
                <div class="streaming-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
            <div class="message-content">${this.formatMessageContent(content)}</div>
        `;
        
        return messageDiv;
    }
    
    getMessageIcon(messageType) {
        const icons = {
            'thinking': '🤔',
            'tool': '🔧',
            'ai': '🤖',
            'system': '💡',
            'success': '✅',
            'error': '❌'
        };
        return icons[messageType] || '💬';
    }
    
    clearCurrentStreamingMessage() {
        if (this.currentStreamingMessage) {
            this.currentStreamingMessage.classList.remove('streaming');
            this.currentStreamingMessage.querySelector('.streaming-indicator')?.remove();
            this.currentStreamingMessage = null;
        }
    }
    
    addSystemMessage(content, type = 'info') {
        return this.addMessage(content, 'system', false, type);
    }
    
    addAIMessage(content, data = null) {
        const message = this.addMessage(content, 'ai', false);
        
        // Handle additional data (like actions, tools results, etc.)
        if (data && data.ai_actions && data.ai_actions.length > 0) {
            this.handleActions(data.ai_actions);
        }
        
        return message;
    }
    
    finishProcessing() {
        this.isProcessing = false;
        this.updateSendButton();
        this.removeTypingIndicator();
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || this.isProcessing) return;
        
        this.isProcessing = true;
        this.updateSendButton();
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.elements.messageInput.value = '';
        this.adjustTextareaHeight();
        
        // Show typing indicator
        this.addTypingIndicator();
        
        try {
            // Use WebSocket for streaming if available
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    message: message,
                    page_url: this.currentTab?.url,
                    page_content: this.pageContent,
                    tab_id: this.currentTab?.id?.toString(),
                    page_title: this.currentTab?.title,
                    session_id: this.generateSessionId()
                }));
            } else {
                // Fallback to HTTP request
                await this.sendMessageHTTP(message);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'ai');
            this.isProcessing = false;
            this.updateSendButton();
        }
    }
    
    async sendMessageHTTP(message) {
        // Original HTTP-based method as fallback
        const response = await chrome.runtime.sendMessage({
            type: 'SEND_TO_AI',
            data: {
                message: message,
                pageUrl: this.currentTab?.url,
                pageContent: this.pageContent
            }
        });
        
        this.removeTypingIndicator();
        
        if (response.success) {
            const aiResponse = response.data;
            
            // Add AI response to chat
            this.addMessage(aiResponse.response || aiResponse.message || 'I received your message.', 'ai');
            
            // Handle any actions
            if (aiResponse.actions && aiResponse.actions.length > 0) {
                await this.handleActions(aiResponse.actions);
            }
        } else {
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', 'ai');
        }
        
        this.isProcessing = false;
        this.updateSendButton();
    }
    
    addMessage(content, sender, isStreaming = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Format content for display
        if (sender === 'ai' && !isStreaming) {
            contentDiv.innerHTML = this.formatAIResponse(content);
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMsg = this.elements.chatContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        this.elements.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Return the message div for streaming updates
        return messageDiv;
    }
    
    formatAIResponse(content) {
        // Simple formatting for AI responses
        return content
            .replace(/\\n/g, '<br>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/```([\\s\\S]+?)```/g, '<pre>$1</pre>');
    }
    
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message message-ai';
        typingDiv.id = 'typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.elements.chatContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    scrollToBottom() {
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }
    
    async handleActions(actions) {
        for (const action of actions) {
            try {
                const result = await chrome.runtime.sendMessage({
                    type: 'EXECUTE_ACTION',
                    data: action
                });
                
                if (result.success) {
                    this.addActionFeedback(`✓ ${action.type}: ${result.data.message}`, 'success');
                } else {
                    this.addActionFeedback(`✗ ${action.type}: ${result.data.message}`, 'error');
                }
                
                // Small delay between actions
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (error) {
                console.error('Error executing action:', error);
                this.addActionFeedback(`✗ ${action.type}: Failed to execute`, 'error');
            }
        }
        
        // Refresh page content after actions
        await this.refreshPageContent();
    }
    
    addActionFeedback(message, type) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = `message message-ai`;
        feedbackDiv.innerHTML = `
            <div class="message-content" style="font-size: 12px; opacity: 0.8; color: ${type === 'success' ? '#34a853' : '#ea4335'}">
                ${message}
            </div>
        `;
        
        this.elements.chatContainer.appendChild(feedbackDiv);
        this.scrollToBottom();
    }
    
    async handleQuickAction(action) {
        switch (action) {
            case 'summarize':
                this.elements.messageInput.value = 'Please summarize this page for me.';
                break;
            case 'extract':
                this.elements.messageInput.value = 'Extract the key information from this page.';
                break;
            case 'help':
                this.showHelp();
                return;
        }
        
        this.updateSendButton();
        this.adjustTextareaHeight();
    }
    
    showHelp() {
        const helpMessage = `Here are some things you can ask me to do:

**Page Analysis:**
• "Summarize this page"
• "What is this page about?"
• "Extract key information"
• "Find contact information"

**Navigation:**
• "Click the login button"
• "Go to the pricing page"
• "Scroll down"
• "Open the first search result"

**Form Interaction:**
• "Fill in the email field with john@example.com"
• "Type 'hello world' in the search box"
• "Select 'Premium' from the dropdown"

**General:**
• "Help me find information about X"
• "What can I do on this page?"
• "Navigate to the checkout"`;
        
        this.addMessage(helpMessage, 'ai');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIBrowserSidePanel();
});