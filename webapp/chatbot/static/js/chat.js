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
        
        // Load voices when they become available
        if (this.synthesis) {
            this.synthesis.addEventListener('voiceschanged', () => {
                console.log('🔊 Available voices loaded:', this.synthesis.getVoices().length);
            });
        }
        
        this.init();
    }

    init() {
        const urlParams = new URLSearchParams(window.location.search);
        this.currentSessionId = urlParams.get('session_id');
        
        console.log('🔐 CSRF Token:', this.csrfToken ? 'Found' : 'Not found');
        
        this.setupEventListeners();
        this.setupSidebarToggle();
        this.loadConversations();
        this.checkSystemStatus();
        this.initSpeechRecognition();
        this.monitorNetworkStatus();
        
        if (this.currentSessionId) {
            sessionStorage.setItem('currentSessionId', this.currentSessionId);
        }
    }

    monitorNetworkStatus() {
        // Update voice button state based on network status
        const updateVoiceButtonState = () => {
            const voiceBtn = document.getElementById('voiceBtn');
            if (voiceBtn && !voiceBtn.classList.contains('btn-danger')) {
                if (!navigator.onLine) {
                    voiceBtn.classList.add('opacity-50');
                    voiceBtn.title = 'Voice Chat (No Internet Connection)';
                } else {
                    voiceBtn.classList.remove('opacity-50');
                    voiceBtn.title = 'Voice Chat (Requires Internet Connection)';
                }
            }
        };

        // Check on load
        updateVoiceButtonState();

        // Monitor network changes
        window.addEventListener('online', () => {
            console.log('🌐 Internet connection restored');
            updateVoiceButtonState();
            this.showNotification('✅ Internet connected - Voice chat available', 'success');
        });

        window.addEventListener('offline', () => {
            console.log('🌐 Internet connection lost');
            updateVoiceButtonState();
            this.showNotification('⚠️ No internet - Voice chat unavailable', 'warning');
        });
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

    setupSidebarToggle() {
        const sidebar = document.getElementById('chatSidebar');
        const toggleBtn = document.getElementById('sidebarToggleBtn');
        const openBtn = document.getElementById('sidebarOpenBtn');
        const mobileToggleBtn = document.getElementById('mobileSidebarBtn');
        const sidebarOverlay = document.getElementById('chatSidebarOverlay');
        const isMobile = () => window.matchMedia('(max-width: 768px)').matches;

        const openMobileSidebar = () => {
            if (!sidebar) return;
            sidebar.classList.add('show');
            sidebarOverlay?.classList.add('active');
            document.body.classList.add('sidebar-open');
        };

        const closeMobileSidebar = () => {
            if (!sidebar) return;
            sidebar.classList.remove('show');
            sidebarOverlay?.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        };

        const toggleMobileSidebar = () => {
            if (!sidebar) return;
            if (sidebar.classList.contains('show')) {
                closeMobileSidebar();
            } else {
                openMobileSidebar();
            }
        };
        
        if (toggleBtn && sidebar) {
            // Check if sidebar state was saved
            const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
            }
            
            toggleBtn.addEventListener('click', () => {
                if (isMobile()) {
                    toggleMobileSidebar();
                } else {
                    sidebar.classList.toggle('collapsed');
                    // Save state
                    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                }
            });
        }

        // Open button handler (for collapsed sidebar)
        if (openBtn && sidebar) {
            openBtn.addEventListener('click', () => {
                sidebar.classList.remove('collapsed');
                localStorage.setItem('sidebarCollapsed', 'false');
            });
        }

        if (mobileToggleBtn && sidebar) {
            mobileToggleBtn.addEventListener('click', () => {
                if (isMobile()) {
                    toggleMobileSidebar();
                } else {
                    sidebar.classList.toggle('collapsed');
                    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                }
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', closeMobileSidebar);
        }

        if (sidebar) {
            sidebar.querySelectorAll('a').forEach((link) => {
                link.addEventListener('click', () => {
                    if (isMobile()) {
                        closeMobileSidebar();
                    }
                });
            });
        }

        window.addEventListener('resize', () => {
            if (!isMobile()) {
                closeMobileSidebar();
            }
        });
    }

    // ===== SPEECH TO TEXT =====
    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;

            this.recognition.onstart = () => {
                console.log('🎤 Speech recognition started');
            };

            this.recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }

                const input = document.getElementById('messageInput');
                if (input) {
                    input.value = transcript.trim();
                }

                const lastResult = event.results[event.results.length - 1];
                if (lastResult && lastResult.isFinal) {
                    const confidence = lastResult[0]?.confidence;
                    console.log('🎤 Recognized:', transcript, 'Confidence:', confidence);
                    this.showNotification(`✅ Voice recognized`, 'success');
                }
            };

            this.recognition.onerror = (event) => {
                console.error('🎤 Speech recognition error:', event.error);
                let errorMessage = 'Could not recognize speech.';
                
                switch(event.error) {
                    case 'no-speech':
                        errorMessage = '🔇 No speech detected. Please speak louder and try again.';
                        break;
                    case 'audio-capture':
                        errorMessage = '🎤 Microphone not found. Please check your microphone connection.';
                        break;
                    case 'not-allowed':
                        errorMessage = '⚠️ Microphone access denied. Click the 🔒 icon in address bar to allow microphone.';
                        break;
                    case 'network':
                        errorMessage = '🌐 Network error. Speech recognition requires internet connection. Please check your connection and try again.';
                        break;
                    case 'aborted':
                        errorMessage = '⏹️ Recording stopped.';
                        break;
                    case 'service-not-allowed':
                        errorMessage = '🚫 Speech recognition service is blocked. Please check browser settings.';
                        break;
                    default:
                        errorMessage = `❌ Error: ${event.error}. Please try again.`;
                }
                
                this.showNotification(errorMessage, 'danger');
                this.resetVoiceButton();
            };

            this.recognition.onend = () => {
                console.log('🎤 Speech recognition ended');
                this.resetVoiceButton();
            };
        } else {
            console.warn('🎤 Speech recognition not supported in this browser');
            const btn = document.getElementById('voiceBtn');
            if (btn) {
                btn.disabled = true;
                btn.classList.add('opacity-50');
                btn.title = 'Voice input is not supported in this browser';
            }
        }
    }

    resetVoiceButton() {
        const btn = document.getElementById('voiceBtn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-microphone"></i>';
            btn.classList.remove('btn-danger', 'recording');
            btn.classList.add('btn-light');
        }
    }

    toggleVoiceRecording() {
        if (!this.recognition) {
            this.showNotification('Speech recognition not supported in this browser. Please use Chrome or Edge.', 'warning');
            return;
        }

        // Check internet connection first
        if (!navigator.onLine) {
            this.showNotification('No internet connection. Speech recognition requires internet access.', 'danger');
            return;
        }

        const btn = document.getElementById('voiceBtn');

        if (btn.classList.contains('btn-danger')) {
            // Stop recording
            this.recognition.stop();
            btn.classList.remove('recording');
            this.showNotification('Recording stopped', 'info');
        } else {
            // Show loading state
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            try {
                // Check if microphone permission is granted
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(() => {
                        // Reset button state
                        btn.disabled = false;
                        
                        // Start recording
                        this.recognition.start();
                        btn.innerHTML = '<i class="fas fa-stop"></i>';
                        btn.classList.remove('btn-light');
                        btn.classList.add('btn-danger', 'recording');
                        this.showNotification('🎤 Listening... Speak clearly', 'info');
                    })
                    .catch((error) => {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fas fa-microphone"></i>';
                        console.error('Microphone access denied:', error);
                        this.showNotification('⚠️ Microphone access denied. Please allow microphone in browser settings.', 'danger');
                    });
            } catch (error) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-microphone"></i>';
                console.error('Recognition start error:', error);
                this.showNotification('Could not start voice recognition. Please try again.', 'danger');
            }
        }
    }

    // ===== TEXT TO SPEECH =====
    speakText(text) {
        if (!this.synthesis) {
            this.showNotification('Text-to-speech not supported in this browser', 'warning');
            return;
        }

        // Cancel any ongoing speech
        this.synthesis.cancel();

        // Clean text for better speech output
        const cleanText = text
            .replace(/[*#_~`]/g, '') // Remove markdown
            .replace(/\[.*?\]/g, '') // Remove links text
            .replace(/https?:\/\/[^\s]+/g, '') // Remove URLs
            .replace(/\n/g, ' ') // Replace newlines with spaces
            .trim();

        if (!cleanText) {
            this.showNotification('No text to speak', 'warning');
            return;
        }

        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Get available voices and select a soothing one
        const voices = this.synthesis.getVoices();
        
        // Prefer female voices (typically more soothing) or voices with "natural" in name
        const soothingVoice = voices.find(voice => 
            (voice.name.includes('Female') || 
             voice.name.includes('female') || 
             voice.name.includes('Samantha') ||
             voice.name.includes('Victoria') ||
             voice.name.includes('Karen') ||
             voice.name.includes('Natural') ||
             voice.name.includes('Zira') ||
             voice.name.includes('Google UK English Female') ||
             voice.lang === 'en-GB') && 
            voice.lang.startsWith('en')
        ) || voices.find(voice => voice.lang.startsWith('en'));

        if (soothingVoice) {
            utterance.voice = soothingVoice;
            console.log('🔊 Using voice:', soothingVoice.name);
        }

        // Soothing settings
        utterance.rate = 0.85;  // Slower, calmer pace (0.1 to 10, default 1)
        utterance.pitch = 1.1;  // Slightly higher pitch for warmth (0 to 2, default 1)
        utterance.volume = 0.9; // Slightly softer volume (0 to 1, default 1)
        utterance.lang = 'en-US';

        utterance.onstart = () => {
            console.log('🔊 Speaking with soothing voice...');
        };

        utterance.onend = () => {
            console.log('🔊 Speech finished');
        };

        utterance.onerror = (event) => {
            console.error('🔊 Speech synthesis error:', event);
            this.showNotification('Could not play audio', 'danger');
        };

        try {
            this.synthesis.speak(utterance);
        } catch (error) {
            console.error('🔊 Error speaking text:', error);
            this.showNotification('Text-to-speech failed', 'danger');
        }
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

                // Show thinking animation for 1-2 seconds
                await this.showThinkingAnimation();
                this.hideTypingIndicator();

                // Type each bot message with character-by-character effect
                for (const botMsg of data.bot_messages) {
                    await this.typeMessage(botMsg.text, 'bot', { video: botMsg.video });
                    // Uncomment to enable text-to-speech
                    // this.speakText(botMsg.text);
                }
                
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
            
            // Add speaker button for bot messages
            if (sender === 'bot') {
                messageContent += `
                    <button class="btn btn-sm btn-light mt-2 speaker-btn" onclick="chatApp.speakText(\`${text.replace(/`/g, '\\`').replace(/\n/g, ' ')}\`)" title="Listen">
                        <i class="fas fa-volume-up"></i> Listen
                    </button>
                `;
            }
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
            // Update text to show thinking
            const textElement = indicator.querySelector('.typing-text');
            if (textElement) {
                textElement.textContent = 'Thinking';
            }
            this.scrollToBottom();
        }
    }

    async showThinkingAnimation() {
        // Simulate thinking time (1-2 seconds)
        const thinkingTime = 1000 + Math.random() * 1000;
        return new Promise(resolve => setTimeout(resolve, thinkingTime));
    }

    async typeMessage(text, sender, options = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        
        const welcomeMsg = messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();

        // Create message structure
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Add typing class for animation
        if (sender === 'bot') {
            messageDiv.classList.add('typing');
        }
        
        let messageContent = `
            <div class="message-avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-text"></div>
            </div>
        `;

        messageDiv.innerHTML = messageContent;
        messagesContainer.appendChild(messageDiv);
        
        const textElement = messageDiv.querySelector('.message-text');
        const contentDiv = messageDiv.querySelector('.message-content');
        
        // Type text character by character
        if (sender === 'bot') {
            await this.typeText(textElement, text);
            // Remove typing class after done
            messageDiv.classList.remove('typing');
            
            // Add speaker button for bot messages
            const speakerBtn = document.createElement('button');
            speakerBtn.className = 'btn btn-sm btn-light mt-2 speaker-btn';
            speakerBtn.title = 'Listen';
            speakerBtn.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
            speakerBtn.onclick = () => this.speakText(text);
            contentDiv.appendChild(speakerBtn);
        } else {
            textElement.innerHTML = this.formatMessage(text);
        }
        
        // Add video if present
        if (options.video) {
            const videoHTML = this.createVideoPlayer(options.video);
            contentDiv.insertAdjacentHTML('beforeend', videoHTML);
        }
        
        this.scrollToBottom();
        this.messages.push({ text, sender, timestamp: new Date(), ...options });
    }

    async typeText(element, text, speed = 30) {
        // Speed in milliseconds per character (30ms = fast but readable)
        let displayText = '';
        const formattedText = this.formatMessage(text);
        
        // Check if text has complex HTML formatting
        const hasComplexFormatting = formattedText.includes('<a ') || formattedText.includes('<iframe');
        
        if (hasComplexFormatting) {
            // For complex HTML, use a fade-in effect instead
            element.style.opacity = '0';
            element.innerHTML = formattedText;
            await this.fadeIn(element, 300);
            return;
        }
        
        // Remove formatting temporarily for typing effect
        const plainText = text
            .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markers
            .replace(/\n/g, ' '); // Replace newlines with spaces for smoother typing
        
        // Type plain text character by character
        const words = plainText.split(' ');
        
        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            
            // Type word character by character
            for (let j = 0; j < word.length; j++) {
                displayText += word[j];
                element.textContent = displayText;
                
                // Random variation in typing speed for more natural feel
                const variance = Math.random() * 15 - 5; // -5 to +10ms
                await new Promise(resolve => setTimeout(resolve, speed + variance));
            }
            
            // Add space after word (except last word)
            if (i < words.length - 1) {
                displayText += ' ';
                element.textContent = displayText;
                
                // Slightly longer pause after punctuation
                const lastChar = word[word.length - 1];
                const pauseTime = ['.', '!', '?', ','].includes(lastChar) ? 200 : 50;
                await new Promise(resolve => setTimeout(resolve, pauseTime));
            }
            
            // Scroll periodically
            if (i % 3 === 0) {
                this.scrollToBottom();
            }
        }
        
        // Apply formatting after typing complete
        await new Promise(resolve => setTimeout(resolve, 100));
        element.innerHTML = this.formatMessage(text);
        this.scrollToBottom();
    }
    
    async fadeIn(element, duration = 300) {
        let opacity = 0;
        const increment = 0.05;
        const stepTime = duration / (1 / increment);
        
        const fade = () => {
            opacity += increment;
            if (opacity <= 1) {
                element.style.opacity = opacity;
                setTimeout(fade, stepTime);
            } else {
                element.style.opacity = '1';
            }
        };
        
        fade();
        return new Promise(resolve => setTimeout(resolve, duration));
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