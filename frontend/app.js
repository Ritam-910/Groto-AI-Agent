/**
 * AI Agent Frontend Application
 * Handles UI interactions and API communication
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
let conversationId = null;
let isProcessing = false;

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const statusIndicator = document.getElementById('statusIndicator');
const welcomeMessage = document.getElementById('welcomeMessage');
const charCount = document.getElementById('charCount');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    await checkHealth();
    loadConversationFromStorage();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Send button
    sendBtn.addEventListener('click', handleSendMessage);

    // Enter key to send
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Input changes
    messageInput.addEventListener('input', () => {
        updateCharCount();
        updateSendButton();
        autoResizeTextarea();
    });

    // Clear conversation
    clearBtn.addEventListener('click', handleClearConversation);
}



/**
 * Check API health
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.ollama_connected) {
            updateStatus('connected', 'Connected');
        } else {
            updateStatus('error', 'Ollama not running');
        }
    } catch (error) {
        updateStatus('error', 'API offline');
        console.error('Health check failed:', error);
    }
}

/**
 * Update status indicator
 */
function updateStatus(status, text) {
    statusIndicator.className = `status-indicator ${status}`;
    statusIndicator.querySelector('.status-text').textContent = text;
}

/**
 * Handle send message
 */
async function handleSendMessage() {
    const message = messageInput.value.trim();

    if (!message || isProcessing) return;

    // Add user message to UI
    addMessage('user', message);

    // Clear input
    messageInput.value = '';
    updateCharCount();
    updateSendButton();

    // Hide welcome message
    if (welcomeMessage) {
        welcomeMessage.classList.add('fade-out');
        setTimeout(() => welcomeMessage.remove(), 300);
    }

    // Show typing indicator
    const typingId = addTypingIndicator();

    // Send to API
    isProcessing = true;

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();

        // Update conversation ID
        conversationId = data.conversation_id;
        saveConversationToStorage();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant response
        addMessage('assistant', data.response);

    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(typingId);
        addMessage('assistant', '❌ Sorry, I encountered an error. Please make sure the backend is running.');
    } finally {
        isProcessing = false;
    }
}

/**
 * Add message to chat
 */
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    if (role === 'user') {
        avatar.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
    } else {
        avatar.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>`;
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = content;

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    contentDiv.appendChild(textDiv);
    contentDiv.appendChild(timeDiv);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    chatContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

/**
 * Add typing indicator
 */
function addTypingIndicator() {
    const id = `typing-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = id;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    contentDiv.appendChild(typingDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    chatContainer.appendChild(messageDiv);
    scrollToBottom();

    return id;
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

/**
 * Handle clear conversation
 */
async function handleClearConversation() {
    if (!conversationId) {
        // Just clear UI
        clearChatUI();
        return;
    }

    if (!confirm('Are you sure you want to clear this conversation?')) {
        return;
    }

    try {
        await fetch(`${API_BASE_URL}/chat/clear/${conversationId}`, {
            method: 'DELETE'
        });

        conversationId = null;
        clearConversationFromStorage();
        clearChatUI();

    } catch (error) {
        console.error('Error clearing conversation:', error);
        // Clear UI anyway
        clearChatUI();
    }
}

/**
 * Clear chat UI
 */
function clearChatUI() {
    // Remove all messages
    const messages = chatContainer.querySelectorAll('.message');
    messages.forEach(msg => msg.remove());

    // Show welcome message again
    const welcome = document.createElement('div');
    welcome.className = 'welcome-message';
    welcome.id = 'welcomeMessage';
    welcome.innerHTML = `
        <div class="welcome-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="url(#paint0_linear_new)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <defs>
                    <linearGradient id="paint0_linear_new" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#7F5AF0"/>
                        <stop offset="1" stop-color="#2CB67D"/>
                    </linearGradient>
                </defs>
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 16v-4"></path>
                <path d="M12 8h.01"></path>
            </svg>
        </div>
        <h2>System Online</h2>
        <p>Advanced neural agent ready for processing.</p>
        
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3>Real-time Analysis</h3>
                <p>Instant processing of complex queries</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3>Neural Graph</h3>
                <p>State-aware conversation flow</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🛡️</div>
                <h3>Secure Core</h3>
                <p>Local data processing environment</p>
            </div>
        </div>
    `;

    chatContainer.insertBefore(welcome, chatContainer.firstChild);
}

/**
 * Update character count
 */
function updateCharCount() {
    const count = messageInput.value.length;
    charCount.textContent = `${count} / 2000`;

    if (count > 1800) {
        charCount.style.color = 'var(--accent-pink)';
    } else {
        charCount.style.color = 'var(--text-tertiary)';
    }
}

/**
 * Update send button state
 */
function updateSendButton() {
    const hasText = messageInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || isProcessing;
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
}

/**
 * Scroll to bottom of chat
 */
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Save conversation to localStorage
 */
function saveConversationToStorage() {
    if (conversationId) {
        localStorage.setItem('ai_agent_conversation_id', conversationId);
    }
}

/**
 * Load conversation from localStorage
 */
function loadConversationFromStorage() {
    const stored = localStorage.getItem('ai_agent_conversation_id');
    if (stored) {
        conversationId = stored;
    }
}

/**
 * Clear conversation from localStorage
 */
function clearConversationFromStorage() {
    localStorage.removeItem('ai_agent_conversation_id');
}

// Periodic health check
setInterval(checkHealth, 30000); // Every 30 seconds
