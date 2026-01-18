// MindLift Chat Application - FIXED VERSION
// File: chatbot/static/js/chat.js

class MindLiftChat {
    constructor() {
        this.messages = [];
        this.currentSessionId = null;
        this.conversations = [];
        this.isRecording = false;
        this.recordingTimer = null;
        this.recordingSeconds = 0;
        this.init();
    }

    init() {
        // Get session ID from URL ONLY (no auto-creation)
        const urlParams = new URLSearchParams(window.location.search);
        this.currentSessionId = urlParams.get('session_id');
        
        this.setupEventListeners();
        this.loadConversations();
        this.checkLLMStatus();
        
        // Save session ID if exists
        if (this.currentSessionId) {
            sessionStorage.setItem('currentSessionId', this.currentSessionId);
        }
    }

    setupEventListeners() {
        // Send message
        document.getElementById('sendBtn')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Voice recording
        document.getElementById('voiceBtn')?.addEventListener('click', () => this.toggleVoiceRecording());
        document.getElementById('stopRecordingBtn')?.addEventListener('click', () => this.stopRecording());

        // Clear chat
        document.getElementById('clearChatBtn')?.addEventListener('click', () => this.clearCurrentChat());

        // Generate report
        document.getElementById('generateReportBtn')?.addEventListener('click', () => this.generateReport());

        // New conversation - FIXED
        document.getElementById('newConversationBtn')?.addEventListener('click', () => this.createNewConversation());

        // Sidebar toggle
        document.getElementById('sidebarToggle')?.addEventListener('click', () => this.toggleSidebar());

        // Panel controls
        document.getElementById('showHistoryBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showConversationsPanel();
        });

        document.getElementById('closePanelBtn')?.addEventListener('click', () => {
            document.getElementById('rightPanel').style.display = 'none';
        });
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        // Check if we have a conversation session
        if (!this.currentSessionId) {
            // Create new conversation first
            await this.createNewConversation();
            // Wait a bit for the page to load with new session
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Add user message to UI
        this.addMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to Django backend
            const response = await fetch('/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update session ID
                this.currentSessionId = data.session_id;
                sessionStorage.setItem('currentSessionId', this.currentSessionId);
                
                // Update URL without reload
                const newUrl = `${window.location.pathname}?session_id=${this.currentSessionId}`;
                window.history.replaceState({}, '', newUrl);

                // Hide typing indicator
                this.hideTypingIndicator();

                // Add bot responses
                data.bot_messages.forEach(botMsg => {
                    this.addMessage(botMsg.text, 'bot', {
                        youtubeUrl: botMsg.youtube_url,
                        messageId: botMsg.id
                    });
                });
                
                // Reload conversations list
                this.loadConversations();
            } else {
                throw new Error(data.error || 'Failed to send message');
            }

        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.addMessage('I apologize, but I encountered an error. Please try again.', 'bot');
        }
    }

    addMessage(text, sender, options = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Remove welcome message if exists
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

        // Add text content
        if (text) {
            const youtubeUrl = this.extractYouTubeUrl(text);
            if (youtubeUrl && !options.youtubeUrl) {
                options.youtubeUrl = youtubeUrl;
                text = text.replace(/https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube-nocookie\.com\/embed\/)[^\s]+/g, '').trim();
            }
            
            if (text) {
                messageContent += `<div class="message-text">${this.formatMessage(text)}</div>`;
            }
        }

        // Add YouTube video
        if (options.youtubeUrl) {
            const videoId = this.extractYouTubeId(options.youtubeUrl);
            if (videoId) {
                messageContent += `
                    <div class="youtube-embed" style="margin-top: 15px; border-radius: 12px; overflow: hidden; background: #000;">
                        <iframe 
                            width="400" 
                            height="300" 
                            src="https://www.youtube-nocookie.com/embed/${videoId}?rel=0&modestbranding=1"
                            title="YouTube video player"
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            referrerpolicy="strict-origin-when-cross-origin"
                            allowfullscreen
                            style="display: block; border: none;">
                        </iframe>
                    </div>
                `;
            }
        }

        messageContent += '</div>'; // Close message-content

        messageDiv.innerHTML = messageContent;
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        // Save message
        this.messages.push({ 
            text, 
            sender, 
            timestamp: new Date(),
            ...options
        });
    }

    extractYouTubeUrl(text) {
        if (!text) return null;
        
        const patterns = [
            /https?:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,
            /https?:\/\/(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})/,
            /https?:\/\/(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
            /https?:\/\/(?:www\.)?youtube-nocookie\.com\/embed\/([a-zA-Z0-9_-]{11})/
        ];
        
        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                return `https://www.youtube-nocookie.com/embed/${match[1]}`;
            }
        }
        
        return null;
    }

    extractYouTubeId(url) {
        const patterns = [
            /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})/
        ];
        
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) return match[1];
        }
        
        return null;
    }

    formatMessage(text) {
        const urlRegex = /(https?:\/\/(?!(?:www\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com))[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        text = text.replace(/\n/g, '<br>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return text;
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'block';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }

    scrollToBottom() {
        const container = document.getElementById('chatMessages');
        container.scrollTop = container.scrollHeight;
    }

    async checkLLMStatus() {
        try {
            const response = await fetch('/api/check-llm-status/');
            const data = await response.json();
            
            console.log('📊 LLM Status:', data);
            
            if (!data.primary_model_ready && !data.fallback_model_ready && !data.rasa_ready) {
                this.showNotification('⚠️ AI services unavailable. Using basic responses.', 'warning');
            } else if (data.primary_model_ready) {
                console.log('✅ Primary model (MindLift) is ready');
            } else if (data.fallback_model_ready) {
                console.log('⚠️ Using fallback model (Phi)');
            }
        } catch (error) {
            console.error('Failed to check LLM status:', error);
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations/');
            const data = await response.json();
            
            if (data.success) {
                this.conversations = data.conversations;
                this.renderConversationsList();
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    renderConversationsList() {
        const sidebar = document.querySelector('.sidebar-conversations');
        if (!sidebar) return;
        
        sidebar.innerHTML = '<h6 class="px-3 py-2 text-muted small">CONVERSATIONS</h6>';
        
        this.conversations.forEach(conv => {
            const isActive = conv.session_id === this.currentSessionId;
            const convElement = document.createElement('a');
            convElement.href = `/chat/?session_id=${conv.session_id}`;
            convElement.className = `sidebar-item conversation-item ${isActive ? 'active' : ''}`;
            convElement.innerHTML = `
                <div class="flex-grow-1">
                    <div class="conversation-title">${conv.title}</div>
                    <small class="text-muted">${conv.message_count} messages</small>
                </div>
                <button class="btn btn-sm btn-link text-danger delete-conversation" 
                        data-session-id="${conv.session_id}"
                        onclick="event.preventDefault(); window.chatApp.deleteConversation('${conv.session_id}');">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            sidebar.appendChild(convElement);
        });
    }

    async createNewConversation() {
        try {
            const response = await fetch('/api/new-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Redirect to new conversation
                window.location.href = `/chat/?session_id=${data.session_id}`;
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            this.showNotification('Failed to create new conversation', 'danger');
        }
    }

    async deleteConversation(sessionId) {
        if (!confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/delete-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Conversation deleted', 'success');
                
                // If deleted current conversation, redirect to chat without session
                if (sessionId === this.currentSessionId) {
                    window.location.href = '/chat/';
                } else {
                    this.loadConversations();
                }
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            this.showNotification('Failed to delete conversation', 'danger');
        }
    }

    async clearCurrentChat() {
        if (!this.currentSessionId) {
            this.showNotification('No active conversation to clear', 'warning');
            return;
        }
        
        if (!confirm('Are you sure you want to clear all messages in this conversation?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/clear-conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ session_id: this.currentSessionId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload page to show cleared conversation
                window.location.reload();
            }
        } catch (error) {
            console.error('Error clearing conversation:', error);
            this.showNotification('Failed to clear conversation', 'danger');
        }
    }

    async generateReport() {
        const modal = new bootstrap.Modal(document.getElementById('reportModal'));
        const reportContent = document.getElementById('reportContent');
        
        reportContent.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-3">Generating report...</p></div>';
        modal.show();
        
        try {
            const response = await fetch('/api/generate-report/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayReport(data.report);
            } else {
                reportContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${data.error || 'Failed to generate report. Please try again.'}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error generating report:', error);
            reportContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    An error occurred while generating the report.
                </div>
            `;
        }
    }

    displayReport(report) {
        const reportContent = document.getElementById('reportContent');
        
        const reportHTML = `
            <div class="text-center mb-4">
                <div class="sentiment-score-circle ${report.overall_sentiment}" style="width: 150px; height: 150px; margin: 0 auto; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 5px solid; ${this.getSentimentColor(report.overall_sentiment)}">
                    <div>
                        <h1 class="display-4 fw-bold mb-0">${Math.round(report.average_score * 100)}%</h1>
                        <p class="text-uppercase fw-bold mb-0">${report.overall_sentiment}</p>
                    </div>
                </div>
            </div>
            
            <div class="row text-center mb-4">
                <div class="col-4">
                    <div class="stat-card" style="background: rgba(16, 185, 129, 0.1); padding: 1.5rem; border-radius: 15px;">
                        <h3 style="color: #10b981;">${report.positive.percentage}%</h3>
                        <p class="mb-1 fw-bold">Positive</p>
                        <small class="text-muted">${report.positive.count} messages</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-card" style="background: rgba(245, 158, 11, 0.1); padding: 1.5rem; border-radius: 15px;">
                        <h3 style="color: #f59e0b;">${report.neutral.percentage}%</h3>
                        <p class="mb-1 fw-bold">Neutral</p>
                        <small class="text-muted">${report.neutral.count} messages</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-card" style="background: rgba(239, 68, 68, 0.1); padding: 1.5rem; border-radius: 15px;">
                        <h3 style="color: #ef4444;">${report.negative.percentage}%</h3>
                        <p class="mb-1 fw-bold">Negative</p>
                        <small class="text-muted">${report.negative.count} messages</small>
                    </div>
                </div>
            </div>
            
            <div class="report-section mb-4" style="background: #f5f7fa; padding: 1.5rem; border-radius: 15px;">
                <h5 class="fw-bold mb-3"><i class="fas fa-heart me-2" style="color: #7c9cbf;"></i>Top Emotions</h5>
                <div class="emotions-list">
                    ${Object.entries(report.top_emotions).map(([emotion, score]) => `
                        <div class="emotion-item mb-2">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-capitalize fw-bold">${emotion}</span>
                                <span class="text-muted">${score}</span>
                            </div>
                            <div class="emotion-bar" style="background: #e8ecef; height: 8px; border-radius: 10px; overflow: hidden;">
                                <div style="width: ${(score / Math.max(...Object.values(report.top_emotions))) * 100}%; background: linear-gradient(135deg, #7c9cbf, #9d9cb3); height: 100%;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="report-section" style="background: #f5f7fa; padding: 1.5rem; border-radius: 15px;">
                <h5 class="fw-bold mb-3"><i class="fas fa-lightbulb me-2" style="color: #7c9cbf;"></i>Recommendations</h5>
                <ul class="list-unstyled mb-0">
                    ${report.recommendations.map(rec => `
                        <li class="mb-2">
                            <i class="fas fa-check-circle me-2" style="color: #10b981;"></i>
                            ${rec}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
        
        reportContent.innerHTML = reportHTML;
    }

    getSentimentColor(sentiment) {
        const colors = {
            'positive': 'border-color: #10b981; color: #10b981;',
            'neutral': 'border-color: #f59e0b; color: #f59e0b;',
            'negative': 'border-color: #ef4444; color: #ef4444;'
        };
        return colors[sentiment] || colors['neutral'];
    }

    showConversationsPanel() {
        const panel = document.getElementById('rightPanel');
        const panelTitle = document.getElementById('panelTitle');
        const panelContent = document.getElementById('panelContent');
        
        panelTitle.textContent = 'Chat History';
        
        let historyHTML = '<div class="list-group">';
        
        this.conversations.forEach(conv => {
            const isActive = conv.session_id === this.currentSessionId;
            historyHTML += `
                <a href="/chat/?session_id=${conv.session_id}" 
                   class="list-group-item list-group-item-action ${isActive ? 'active' : ''}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${conv.title}</h6>
                            <small>${conv.message_count} messages • ${new Date(conv.last_message_at).toLocaleDateString()}</small>
                        </div>
                        <button class="btn btn-sm btn-danger" 
                                onclick="event.preventDefault(); window.chatApp.deleteConversation('${conv.session_id}');">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </a>
            `;
        });
        
        historyHTML += '</div>';
        panelContent.innerHTML = historyHTML;
        panel.style.display = 'flex';
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    toggleSidebar() {
        document.querySelector('.chat-sidebar')?.classList.toggle('show');
    }

    toggleVoiceRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    startRecording() {
        this.isRecording = true;
        this.recordingSeconds = 0;
        
        document.getElementById('voiceRecording').style.display = 'block';
        document.getElementById('voiceBtn').classList.add('btn-danger');
        document.getElementById('voiceBtn').classList.remove('btn-light');

        this.recordingTimer = setInterval(() => {
            this.recordingSeconds++;
            const minutes = Math.floor(this.recordingSeconds / 60);
            const seconds = this.recordingSeconds % 60;
            document.getElementById('recordingTime').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopRecording() {
        this.isRecording = false;
        clearInterval(this.recordingTimer);
        
        document.getElementById('voiceRecording').style.display = 'none';
        document.getElementById('voiceBtn').classList.remove('btn-danger');
        document.getElementById('voiceBtn').classList.add('btn-light');
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
}

// Quick message function
function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    document.getElementById('sendBtn').click();
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new MindLiftChat();
});