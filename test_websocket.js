// Simple WebSocket test to verify backend communication
const WebSocket = require('ws');

async function testWebSocket() {
    console.log('Testing WebSocket connection to AI backend...');
    
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.on('open', () => {
        console.log('✅ WebSocket connected');
        
        // Test message
        const testMessage = {
            client_id: 'test_client',
            session_id: 'test_session',
            message: 'Hello from test',
            page_url: 'https://example.com'
        };
        
        ws.send(JSON.stringify(testMessage));
        console.log('📤 Sent test message');
    });
    
    ws.on('message', (data) => {
        console.log('📥 Received:', data.toString());
    });
    
    ws.on('error', (error) => {
        console.error('❌ WebSocket error:', error);
    });
    
    ws.on('close', () => {
        console.log('🔌 WebSocket connection closed');
        process.exit(0);
    });
    
    // Close after 10 seconds
    setTimeout(() => {
        ws.close();
    }, 10000);
}

testWebSocket().catch(console.error);