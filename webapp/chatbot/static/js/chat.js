// File: chatbot/static/js/chat.js
// COMPLETE WORKING VERSION with PROPER CSRF TOKEN HANDLING

class MindLiftChat {
    constructor() {
        this.messages = [];
        this.currentSessionId = null;
        this.conversations = [];
        this.useRasa = true;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.csrfToken = this.getCSRFToken();
        this.init();
    }

    init() {
        const urlParams = new URLSearchParams(window.location.search);
        this.currentSessionId = urlParams.get('session_id');
        
        console.log('🔐 CSRF Token:', this.csrfToken ? 'Found' : 'Not found');
        
        this.setupEventListeners();
        this.loadConversations();
        this.checkSystemStatus();
        this.initSpeechRecognition();
        
        if (this.currentSessionId) {
            sessionStorage.setItem('currentSessionId', this.currentSessionId);
        }
    }

    // ===== CRITICAL: PROPER CSRF TOKEN RETRIEVAL =====
    getCSRFToken() {
        // Method 1: Try to get from window (set in template)
        if (window.CSRF_TOKEN) {
            console.log('✅ Using CSRF token from window');
            return window.CSRF_TOKEN;
        }
        
        // Method 2: Try to get from cookie
        const cookieValue = this.getCookie('csrftoken');
        if (cookieValue) {
            console.log('✅ Using CSRF token from cookie');
            return cookieValue;
        }
        
        // Method 3: Try to get from meta tag
        const metaTag = document.querySelector('[name=csrfmiddlewaretoken]');
        if (metaTag) {
            console.log('✅ Using CSRF token from meta tag');
            return metaTag.value || metaTag.content;
        }
        
        // Method 4: Try to get from hidden input
        const hiddenInput = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (hiddenInput) {
            console.log('✅ Using CSRF token from hidden input');
            return hiddenInput.value;
        }
        
        console.error('❌ No CSRF token found!');
        return null;
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    setupEventListeners() {
        document.getElementById('sendBtn')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        document.getElementById('voiceBtn')?.addEventListener('click', () => this.toggleVoiceRecording());
        document.getElementById('newConversationBtn')?.addEventListener('click', () => this.createNewConversation());
        document.getElementById('clearChatBtn')?.addEventListener('click', () => this.clearCurrentChat());
        document.getElementById('generateReportBtn')?.addEventListener('click', () => this.generateReport());
    }

    // ===== SPEECH TO TEXT =====
    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
                this.showNotification('Voice recognized! Click send.', 'success');
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.showNotification('Could not recognize speech.', 'danger');
            };

            this.recognition.onend = () => {
                const btn = document.getElementById('voiceBtn');
                btn.innerHTML = '<i class="fas fa-microphone"></i>';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-light');
            };
        }
    }

    toggleVoiceRecording() {
        if (!this.recognition) {
            this.showNotification('Speech recognition not supported', 'warning');
            return;
        }

        const btn = document.getElementById('voiceBtn');

        if (btn.classList.contains('btn-danger')) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
                btn.innerHTML = '<i class="fas fa-stop"></i>';
                btn.classList.remove('btn-light');
                btn.classList.add('btn-danger');
                this.showNotification('Listening... Speak now', 'info');
            } catch (error) {
                console.error('Recognition error:', error);
                this.showNotification('Could not start voice recognition', 'danger');
            }
        }
    }

    // ===== TEXT TO SPEECH =====
    speakText(text) {
        if (!this.synthesis) return;

        this.synthesis.cancel();

        const cleanText = text
            .replace(/[*#_~`]/g, '')
            .replace(/\[.*?\]/g, '')
            .replace(/https?:\/\/[^\s]+/g, '')
            .trim();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;

        this.synthesis.speak(utterance);
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        if (!this.csrfToken) {
            this.showNotification('Security token error. Please refresh the page.', 'danger');
            console.error('❌ No CSRF token available');
            return;
        }

        if (!this.currentSessionId) {
            await this.createNewConversation();
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        this.addMessage(message, 'user');
        input.value = '';
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSessionId,
                    use_rasa: this.useRasa
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Server error:', response.status, errorText);
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.currentSessionId = data.session_id;
                sessionStorage.setItem('currentSessionId', this.currentSessionId);
                
                const newUrl = `${window.location.pathname}?session_id=${this.currentSessionId}`;
                window.history.replaceState({}, '', newUrl);

                this.hideTypingIndicator();

                data.bot_messages.forEach(botMsg => {
                    this.addMessage(botMsg.text, 'bot', { video: botMsg.video });
                    // Uncomment to enable text-to-speech
                    // this.speakText(botMsg.text);
                });
                
                this.loadConversations();
            } else {
                throw new Error(data.error || 'Failed to send message');
            }

        } catch (error) {
            console.error('❌ Error:', error);
            this.hideTypingIndicator();
            this.addMessage('I apologize, but I encountered an error. Please try again.', 'bot');
        }
    }

    addMessage(text, sender, options = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        
        const welcomeMsg = messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        let messageContent = `
            <div class="message-avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
        `;

        if (text) {
            messageContent += `<div class="message-text">${this.formatMessage(text)}</div>`;
        }

        if (options.video) {
            const videoHTML = this.createVideoPlayer(options.video);
            messageContent += videoHTML;
        }

        messageContent += '</div>';
        messageDiv.innerHTML = messageContent;
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        this.messages.push({ text, sender, timestamp: new Date(), ...options });
    }

    createVideoPlayer(videoData) {
        if (!videoData || !videoData.embed_url) return '';

        const videoId = this.extractYouTubeId(videoData.embed_url);
        if (!videoId) return '';

        const title = videoData.title || 'Mental Health Video';
        const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}`;

        return `
            <div class="video-container" style="margin-top: 1rem; max-width: 500px;">
                <div class="video-wrapper" style="position: relative; padding-bottom: 56.25%; height: 0; background: #000; border-radius: 12px; overflow: hidden;">
                    <iframe 
                        src="${embedUrl}?rel=0&modestbranding=1"
                        title="${this.escapeHtml(title)}"
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        `;
    }

    extractYouTubeId(url) {
        if (!url) return null;
        
        const patterns = [
            /(?:youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
            /(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
            /(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})/,
            /(?:youtu\.be\/)([a-zA-Z0-9_-]{11})/,
            /^([a-zA-Z0-9_-]{11})$/
        ];
        
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match && match[1]) return match[1];
        }
        
        return null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatMessage(text) {
        const urlRegex = /(https?:\/\/(?!(?:www\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com))[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        text = text.replace(/\n/g, '<br>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return text;
    }

    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.style.display = 'block';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.style.display = 'none';
    }

    scrollToBottom() {
        const container = document.getElementById('chatMessages');
        if (container) {
            setTimeout(() => {
                container.scrollTop = container.scrollHeight;
            }, 100);
        }
    }

    async checkSystemStatus() {
        try {
            const response = await fetch('/api/check-llm-status/');
            const data = await response.json();
            console.log('System Status:', data);
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations/');
            const data = await response.json();
            if (data.success) this.conversations = data.conversations;
        } catch (error) {
            console.error('Load conversations error:', error);
        }
    }

    async createNewConversation() {
        try {
            const response = await fetch('/api/new-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = `/chat/?session_id=${data.session_id}`;
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Failed to create conversation', 'danger');
        }
    }

    async deleteConversation(sessionId) {
        if (!confirm('Delete this conversation?')) return;
        
        try {
            const response = await fetch('/api/delete-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({ session_id: sessionId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Conversation deleted', 'success');
                if (sessionId === this.currentSessionId) {
                    window.location.href = '/chat/';
                } else {
                    location.reload();
                }
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Failed to delete', 'danger');
        }
    }

    async clearCurrentChat() {
        if (!this.currentSessionId) {
            this.showNotification('No active conversation', 'warning');
            return;
        }
        
        if (!confirm('Clear all messages?')) return;
        
        try {
            const response = await fetch('/api/clear-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({ session_id: this.currentSessionId })
            });
            
            const data = await response.json();
            if (data.success) window.location.reload();
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async generateReport() {
        if (!this.currentSessionId) {
            this.showNotification('No conversation to generate report from', 'warning');
            return;
        }
        
        this.showNotification('Generating report...', 'info');
        
        try {
            const response = await fetch('/api/generate-report/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    days: 7
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Report generated!', 'success');
                setTimeout(() => {
                    window.location.href = '/reports/';
                }, 1000);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Failed to generate report', 'danger');
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }
}

function sendQuickMessage(message) {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    if (input && sendBtn) {
        input.value = message;
        sendBtn.click();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing MindLift Chat...');
    window.chatApp = new MindLiftChat();
    console.log('✅ MindLift initialized');
});