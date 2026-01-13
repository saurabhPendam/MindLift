// MindLift Chat Application with RASA Integration
// File: chatbot/static/js/chat.js

class MindLiftChat {
    constructor() {
        this.messages = [];
        this.isRecording = false;
        this.recordingTimer = null;
        this.recordingSeconds = 0;
        this.conversationId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadChatHistory();
        this.checkRasaStatus();
    }

    setupEventListeners() {
        // Send message
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Voice recording
        document.getElementById('voiceBtn')?.addEventListener('click', () => this.toggleVoiceRecording());
        document.getElementById('stopRecordingBtn')?.addEventListener('click', () => this.stopRecording());

        // Clear chat
        document.getElementById('clearChatBtn').addEventListener('click', () => this.clearChat());

        // Generate report
        document.getElementById('generateReportBtn').addEventListener('click', () => this.generateReport());

        // Sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', () => this.toggleSidebar());

        // Panel controls
        document.getElementById('showReportBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPanel('Reports');
        });

        document.getElementById('showHistoryBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showPanel('Chat History');
        });

        document.getElementById('closePanelBtn')?.addEventListener('click', () => {
            document.getElementById('rightPanel').style.display = 'none';
        });

        // Download report button
        document.getElementById('downloadReportBtn')?.addEventListener('click', () => {
            this.downloadReportPDF();
        });
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to UI
        this.addMessage(message, 'user');
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to Django backend which will communicate with RASA
            const response = await fetch('/api/send-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update conversation ID
                this.conversationId = data.conversation_id;

                // Hide typing indicator
                this.hideTypingIndicator();

                // Add bot responses
                data.bot_messages.forEach(botMsg => {
                    this.addMessage(botMsg.text, 'bot', {
                        youtubeUrl: botMsg.youtube_url,
                        buttons: botMsg.buttons,
                        image: botMsg.image,
                        messageId: botMsg.id
                    });
                });
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
            // Extract YouTube URL from text if present
            const youtubeUrl = this.extractYouTubeUrl(text);
            if (youtubeUrl && !options.youtubeUrl) {
                options.youtubeUrl = youtubeUrl;
                // Remove URL from text
                text = text.replace(/https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube-nocookie\.com\/embed\/)[^\s]+/g, '').trim();
            }
            
            if (text) {
                messageContent += `<div class="message-text">${this.formatMessage(text)}</div>`;
            }
        }

        // Add YouTube video with improved embedding
        if (options.youtubeUrl) {
            const videoId = this.extractYouTubeId(options.youtubeUrl);
            if (videoId) {
                messageContent += `
                    <div class="youtube-embed" style="margin-top: 15px; border-radius: 12px; overflow: hidden; background: #000;">
                        <iframe 
                            width="400" 
                            height="400" 
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

        // Add image if present
        if (options.image) {
            messageContent += `<img src="${options.image}" class="message-image" alt="Image" style="max-width: 100%; border-radius: 10px; margin-top: 10px;">`;
        }

        // Add buttons if present
        if (options.buttons && options.buttons.length > 0) {
            messageContent += '<div class="message-buttons" style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px;">';
            options.buttons.forEach(button => {
                messageContent += `
                    <button class="btn btn-sm btn-outline-primary message-button" 
                            onclick="window.chatApp.handleButtonClick('${button.payload}')">
                        ${button.title}
                    </button>
                `;
            });
            messageContent += '</div>';
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

    formatMessage(text) {
        // Convert URLs to links (but not YouTube URLs as they're embedded)
        const urlRegex = /(https?:\/\/(?!(?:www\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com))[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Format bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        return text;
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

    handleButtonClick(payload) {
        // Handle button clicks by sending the payload as a message
        document.getElementById('messageInput').value = payload;
        this.sendMessage();
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

    async checkRasaStatus() {
        try {
            const response = await fetch('/api/check-rasa-status/');
            const data = await response.json();
            
            if (!data.rasa_running) {
                console.warn('RASA server is not running');
            }
        } catch (error) {
            console.error('Failed to check RASA status:', error);
        }
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

        console.log('Recording started...');
    }

    stopRecording() {
        this.isRecording = false;
        clearInterval(this.recordingTimer);
        
        document.getElementById('voiceRecording').style.display = 'none';
        document.getElementById('voiceBtn').classList.remove('btn-danger');
        document.getElementById('voiceBtn').classList.add('btn-light');

        console.log('Recording stopped');
    }

    clearChat() {
        if (confirm('Are you sure you want to clear all messages?')) {
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <h4 class="fw-bold mb-2">Chat Cleared</h4>
                    <p class="text-muted mb-4">Start a new conversation</p>
                </div>
            `;
            this.messages = [];
            this.conversationId = null;
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
                    days: 7,
                    conversation_id: this.conversationId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayReport(data.report);
                this.currentReport = data.report;
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
                    An error occurred while generating the report. Please try again.
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
                <h5 class="fw-bold mb-3"><i class="fas fa-heart me-2" style="color: #7c9cbf;"></i>Top Emotions Detected</h5>
                <div class="emotions-list">
                    ${Object.entries(report.top_emotions).map(([emotion, score]) => `
                        <div class="emotion-item mb-2">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="emotion-name text-capitalize fw-bold">${emotion}</span>
                                <span class="text-muted">${score}</span>
                            </div>
                            <div class="emotion-bar" style="background: #e8ecef; height: 8px; border-radius: 10px; overflow: hidden;">
                                <div class="emotion-fill" style="width: ${(score / Math.max(...Object.values(report.top_emotions))) * 100}%; background: linear-gradient(135deg, #7c9cbf, #9d9cb3); height: 100%;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="report-section mb-4" style="background: #f5f7fa; padding: 1.5rem; border-radius: 15px;">
                <h5 class="fw-bold mb-3"><i class="fas fa-calendar me-2" style="color: #7c9cbf;"></i>Analysis Period</h5>
                <p class="mb-2"><strong>From:</strong> ${report.date_range.start}</p>
                <p class="mb-2"><strong>To:</strong> ${report.date_range.end}</p>
                <p class="mb-0"><strong>Total Messages Analyzed:</strong> ${report.total_messages}</p>
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

    downloadReportPDF() {
        if (!this.currentReport) {
            alert('No report available to download');
            return;
        }

        const printWindow = window.open('', '_blank');
        const reportData = this.currentReport;
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>MindLift Sentiment Report</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 3px solid #7c9cbf;
                        padding-bottom: 20px;
                    }
                    .header h1 {
                        color: #7c9cbf;
                        margin-bottom: 10px;
                    }
                    .score-section {
                        text-align: center;
                        margin: 30px 0;
                        padding: 20px;
                        background: #f5f7fa;
                        border-radius: 10px;
                    }
                    .score {
                        font-size: 48px;
                        font-weight: bold;
                        color: ${reportData.overall_sentiment === 'positive' ? '#10b981' : reportData.overall_sentiment === 'negative' ? '#ef4444' : '#f59e0b'};
                    }
                    .stats {
                        display: flex;
                        justify-content: space-around;
                        margin: 20px 0;
                    }
                    .stat-box {
                        text-align: center;
                        padding: 15px;
                        background: #fff;
                        border-radius: 8px;
                        border: 2px solid #e8ecef;
                    }
                    .section {
                        margin: 25px 0;
                        page-break-inside: avoid;
                    }
                    .section h3 {
                        color: #7c9cbf;
                        border-bottom: 2px solid #e8ecef;
                        padding-bottom: 10px;
                        margin-bottom: 15px;
                    }
                    .emotion-item {
                        margin: 10px 0;
                        padding: 10px;
                        background: #f5f7fa;
                        border-radius: 5px;
                    }
                    ul {
                        list-style: none;
                        padding-left: 0;
                    }
                    ul li {
                        margin: 8px 0;
                        padding-left: 25px;
                        position: relative;
                    }
                    ul li:before {
                        content: "✓";
                        position: absolute;
                        left: 0;
                        color: #10b981;
                        font-weight: bold;
                    }
                    .footer {
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 2px solid #e8ecef;
                        text-align: center;
                        color: #7f8c8d;
                        font-size: 14px;
                    }
                    @media print {
                        body { padding: 20px; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🧠 MindLift Sentiment Analysis Report</h1>
                    <p>Generated on ${new Date().toLocaleDateString()}</p>
                </div>

                <div class="score-section">
                    <div class="score">${Math.round(reportData.average_score * 100)}%</div>
                    <div style="font-size: 24px; font-weight: bold; text-transform: uppercase; color: #7f8c8d;">
                        ${reportData.overall_sentiment} Sentiment
                    </div>
                </div>

                <div class="stats">
                    <div class="stat-box">
                        <div style="font-size: 28px; font-weight: bold; color: #10b981;">${reportData.positive.percentage}%</div>
                        <div>Positive</div>
                        <small>${reportData.positive.count} messages</small>
                    </div>
                    <div class="stat-box">
                        <div style="font-size: 28px; font-weight: bold; color: #f59e0b;">${reportData.neutral.percentage}%</div>
                        <div>Neutral</div>
                        <small>${reportData.neutral.count} messages</small>
                    </div>
                    <div class="stat-box">
                        <div style="font-size: 28px; font-weight: bold; color: #ef4444;">${reportData.negative.percentage}%</div>
                        <div>Negative</div>
                        <small>${reportData.negative.count} messages</small>
                    </div>
                </div>

                <div class="section">
                    <h3>📊 Analysis Period</h3>
                    <p><strong>From:</strong> ${reportData.date_range.start}</p>
                    <p><strong>To:</strong> ${reportData.date_range.end}</p>
                    <p><strong>Total Messages:</strong> ${reportData.total_messages}</p>
                </div>

                <div class="section">
                    <h3>❤️ Top Emotions Detected</h3>
                    ${Object.entries(reportData.top_emotions).map(([emotion, score]) => `
                        <div class="emotion-item">
                            <strong style="text-transform: capitalize;">${emotion}:</strong> ${score}
                        </div>
                    `).join('')}
                </div>

                <div class="section">
                    <h3>💡 Recommendations</h3>
                    <ul>
                        ${reportData.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>

                <div class="footer">
                    <p>This report was generated by MindLift - Your AI Mental Health Companion</p>
                    <p>For support, visit our website or contact a mental health professional</p>
                </div>

                <div class="no-print" style="text-align: center; margin-top: 30px;">
                    <button onclick="window.print()" style="padding: 10px 30px; background: #7c9cbf; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                        Print / Save as PDF
                    </button>
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
    }

    toggleSidebar() {
        document.querySelector('.chat-sidebar').classList.toggle('show');
    }

    showPanel(title) {
        const panel = document.getElementById('rightPanel');
        const panelTitle = document.getElementById('panelTitle');
        const panelContent = document.getElementById('panelContent');
        
        panelTitle.textContent = title;
        
        if (title === 'Reports') {
            panelContent.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-chart-line fa-3x text-primary mb-3"></i>
                    <p>Click "Generate Report" to create your sentiment analysis report</p>
                </div>
            `;
        } else if (title === 'Chat History') {
            this.loadChatHistoryPanel(panelContent);
        }
        
        panel.style.display = 'flex';
    }

    async loadChatHistoryPanel(container) {
        try {
            const response = await fetch(`/api/chat-history/?conversation_id=${this.conversationId || ''}`);
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                const historyHTML = data.messages.map((msg, index) => `
                    <div class="history-item mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="text-${msg.sender === 'user' ? 'primary' : 'secondary'}">
                                ${msg.sender === 'user' ? 'You' : 'MindLift'}
                            </strong>
                            <small class="text-muted">${new Date(msg.timestamp).toLocaleTimeString()}</small>
                        </div>
                        <p class="small mb-0">${msg.content.substring(0, 100)}${msg.content.length > 100 ? '...' : ''}</p>
                        ${msg.sentiment ? `<span class="badge bg-${msg.sentiment === 'positive' ? 'success' : msg.sentiment === 'negative' ? 'danger' : 'secondary'}">${msg.sentiment}</span>` : ''}
                    </div>
                    ${index < data.messages.length - 1 ? '<hr>' : ''}
                `).join('');
                
                container.innerHTML = historyHTML;
            } else {
                container.innerHTML = '<p class="text-center text-muted">No chat history yet</p>';
            }
        } catch (error) {
            console.error('Error loading history:', error);
            container.innerHTML = '<p class="text-center text-danger">Failed to load history</p>';
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch(`/api/chat-history/?limit=50`);
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    this.addMessage(msg.content, msg.sender, {
                        youtubeUrl: msg.video_url,
                        messageId: msg.id
                    });
                });
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
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