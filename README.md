# 🧠 MindLift - AI-Powered Mental Health Chatbot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A comprehensive mental health support platform combining AI chatbot technology, sentiment analysis, and professional consultation features to provide 24/7 emotional wellness support.

🌐 **Live Demo**: [https://mindlift-app.duckdns.org/](https://mindlift-app.duckdns.org/)

<p align="center">
  <img src="banner.png" alt="MindLift – AI Mental Health Chatbot" width="900"/>
</p>


## 🌟 Features

### 💬 Intelligent AI Chatbot
- **Advanced Hybrid AI System**: Seamlessly integrates RASA NLU for precise intent detection with Groq's Llama 3.1 LLM for natural, empathetic, and contextually-aware responses
- **Real-time Crisis Detection**: Intelligent monitoring system that identifies crisis keywords and emotional distress signals, providing immediate professional resource recommendations and emergency helpline information
- **Contextual Memory**: Advanced conversation history management that maintains context across multiple sessions for coherent, personalized, and meaningful interactions
- **Multi-modal Input**: Supports both text and voice input with speech recognition capabilities for enhanced accessibility
- **Adaptive Response Generation**: Dynamic response tuning based on user's emotional state and conversation history
- **Therapeutic Dialogue**: Trained on mental health best practices to provide supportive, non-judgmental conversations

### 📊 Advanced Sentiment & Emotion Analysis
- **Real-time Sentiment Tracking**: VADER sentiment analysis engine processes every message instantly to gauge emotional tone (positive, negative, neutral)
- **Multi-dimensional Emotion Detection**: NRCLex-based emotion recognition identifies 10+ emotions including joy, sadness, anger, fear, trust, anticipation, and surprise
- **Cognitive Distortion Identification**: Detects common cognitive distortions using CBT principles (catastrophizing, black-and-white thinking, overgeneralization)
- **Emotional Pattern Analysis**: Machine learning algorithms track mood trends over time with visualization dashboards
- **Comprehensive Sentiment Reports**: Generate detailed PDF/HTML reports with actionable insights, emotion timelines, and wellness recommendations
- **Crisis Alert System**: Automatic flagging of concerning emotional patterns for early intervention

### 🎥 Personalized Therapeutic Content
- **Smart YouTube Integration**: AI-powered YouTube Data API v3 integration delivers context-aware mental health video recommendations based on current mood and conversation topics
- **Curated Resource Library**: Professionally vetted collection of mental health videos, articles, podcasts, and guided exercises
- **Interactive Wellness Activities**: 
  - Guided breathing exercises with visual timers
  - Progressive muscle relaxation techniques
  - Mindfulness meditation sessions
  - Cognitive Behavioral Therapy (CBT) worksheets
  - Journaling prompts and mood trackers
- **Evidence-Based Content**: All recommendations aligned with clinical psychology best practices
- **Personalized Recommendations**: Content suggestions adapt based on user history, preferences, and therapeutic goals

### 🏥 Professional Mental Health Support
- **Secure Video Consultations**: Integrated Jitsi Meet platform for HIPAA-compliant, end-to-end encrypted video sessions with licensed mental health professionals
- **Comprehensive Doctor Profiles**: Browse detailed profiles of therapists, psychiatrists, and counselors with specializations, credentials, and availability
- **Flexible Appointment System**: Book, reschedule, and manage therapy sessions with automated email/SMS reminders
- **Session Notes**: Secure storage of therapy session summaries and treatment plans (with professional access controls)
- **Professional Dashboard**: Dedicated interface for healthcare providers to manage patients, appointments, and clinical notes
- **Insurance Integration Ready**: Framework prepared for insurance verification and billing integration

### 📈 Comprehensive Wellness Tracking
- **Activity Completion Logger**: Track and rate effectiveness of completed wellness activities including mood improvements
- **Interactive Progress Dashboards**: Beautiful charts and graphs visualizing emotional journey, sentiment trends, and wellness metrics over time
- **Daily Motivational Content**: Curated inspirational quotes with favorites system and sharing capabilities
- **Goal Setting Framework**: Set, track, and achieve personal wellness objectives with milestone celebrations
- **Habit Tracking**: Monitor consistency of wellness practices with streak counters and achievement badges
- **Weekly/Monthly Reports**: Automated progress summaries delivered via email
- **Data Export**: Download complete wellness data in CSV/PDF format for personal records or sharing with healthcare providers

### 🔒 Enterprise-Grade Privacy & Security
- **Two-Factor Authentication (2FA)**: Mandatory email verification during registration + OTP-based 2FA on every login for enhanced security
- **Email Verification System**: All users must verify email ownership before account activation, preventing fake accounts
- **Time-Limited OTPs**: Secure one-time passwords with 10-minute expiration and maximum 5 attempts to prevent brute force attacks
- **End-to-End Encryption**: All data transmission secured with TLS 1.3, sensitive data encrypted at rest using AES-256
- **Graceful Account Deletion**: 30-day grace period for account deletion requests with complete data export and secure purging after retention period
- **Comprehensive Audit Logging**: All security events, data access, and administrative actions logged for compliance and forensics
- **GDPR & HIPAA Ready**: Full compliance with data protection regulations including right to access, rectification, and erasure
- **Gmail-Only Authentication**: Enhanced security through verified Gmail accounts with OAuth 2.0 integration
- **Session Management**: Automatic session timeout, secure cookie handling with HttpOnly and SameSite flags
- **SQL Injection Prevention**: Parameterized queries and ORM-based database access
- **XSS Protection**: Content Security Policy headers and automatic template escaping
- **Rate Limiting**: API request throttling and DDoS protection

### 🧠 Advanced AI Capabilities
- **Semantic Analysis**: Deep understanding of user intent beyond keyword matching
- **Emotion-Aware Responses**: AI adjusts tone and content based on detected emotional state
- **Crisis Escalation Protocol**: Automatic escalation paths for high-risk situations
- **Continual Learning**: System improves over time through user feedback and interaction patterns
- **Multi-language Support Ready**: Architecture prepared for internationalization

### 📱 User Experience Excellence
- **Responsive Design**: Fully optimized for desktop, tablet, and mobile devices
- **Progressive Web App (PWA)**: Install as native-like app on any device
- **Accessibility First**: WCAG 2.1 AA compliant with screen reader support and keyboard navigation
- **Dark Mode**: Eye-friendly dark theme option
- **Offline Mode**: Basic functionality available without internet connection
- **Fast Loading**: Optimized performance with lazy loading and caching strategies

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- MySQL 8.0+
- Node.js 14+ (for RASA)
- pip and virtualenv

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/mindlift.git
   cd mindlift/webapp
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py load_sample_data
   python manage.py createsuperuser
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

7. **Access the Application**
   - Main Application: http://127.0.0.1:8000
   - Admin Panel: http://127.0.0.1:8000/admin

### RASA Setup (Optional)

```bash
cd ../rasa
pip install rasa
rasa train
rasa run --enable-api --cors "*"
```

## 📁 Project Structure

```
mindlift/
├── webapp/                    # Django application
│   ├── chatbot/              # Main chatbot app
│   │   ├── models.py         # Database models
│   │   ├── views.py          # API and view controllers
│   │   ├── groq_service.py   # Groq LLM integration
│   │   ├── hybrid_service.py # RASA + Groq hybrid system
│   │   ├── sentiment_service.py # Sentiment analysis
│   │   ├── templates/        # HTML templates
│   │   ├── static/          # CSS, JS, images
│   │   └── migrations/      # Database migrations
│   ├── webapp/              # Django project settings
│   ├── manage.py           # Django management script
│   └── requirements.txt    # Python dependencies
└── rasa/                   # RASA NLU (optional)
    ├── data/              # Training data
    ├── models/            # Trained models
    └── config.yml         # RASA configuration
```

## 🛠️ Technology Stack

### Backend
- **Django 5.2**: Web framework
- **Python 3.9+**: Core programming language
- **MySQL**: Primary database
- **RASA**: Natural language understanding
- **Groq API**: LLM for conversational AI

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **JavaScript (Vanilla)**: Client-side interactivity
- **AOS**: Scroll animations
- **Font Awesome**: Icon library

### AI & ML
- **VADER Sentiment**: Sentiment analysis
- **NRCLex**: Emotion detection
- **Groq (Llama 3.1)**: Large language model
- **RASA NLU**: Intent classification

### Integrations
- **YouTube Data API v3**: Video recommendations
- **Jitsi Meet**: Video consultations
- **Web Speech API**: Voice input/output

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `webapp/` directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=mindlift_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# API Keys
GROQ_API_KEY=your-groq-api-key
YOUTUBE_API_KEY=your-youtube-api-key

# AI Configuration
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=500
MAX_CONTEXT_MESSAGES=4

# RASA Configuration (Optional)
USE_RASA=True
RASA_SERVER_URL=http://localhost:5005
```

### Database Setup

1. Create MySQL database:
   ```sql
   CREATE DATABASE mindlift_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'mindlift_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON mindlift_db.* TO 'mindlift_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

## 📊 Database Schema

### Core Models
- **UserProfile**: Extended user information and deletion tracking
- **Conversation**: Chat session management
- **Message**: Individual messages with sentiment data
- **SentimentReport**: Generated analysis reports
- **Activity**: Wellness activities library
- **UserActivity**: Activity completion tracking
- **MotivationalQuote**: Inspirational quotes
- **DoctorAppointment**: Therapy session scheduling
- **AuditLog**: Security and compliance logging

## 🎯 Usage

### User Workflow

1. **Registration/Login**
   - Create account with email verification
   - Secure authentication with password validation

2. **Chat Interface**
   - Start conversation with AI chatbot
   - Receive empathetic responses and support
   - Get video recommendations based on mood

3. **Sentiment Analysis**
   - Automatic analysis of every message
   - Generate reports on emotional patterns
   - View trends and insights

4. **Wellness Activities**
   - Browse curated mental health activities
   - Complete exercises and rate helpfulness
   - Track progress over time

5. **Professional Support**
   - Browse licensed mental health professionals
   - Schedule video consultations
   - Manage appointments

### Admin Panel

Access at `/admin` with superuser credentials:
- Manage users and conversations
- Review sentiment reports
- Moderate content and activities
- View audit logs
- Generate analytics

## 🔐 Security Features

- **CSRF Protection**: Django CSRF middleware
- **SQL Injection Prevention**: ORM-based queries
- **XSS Protection**: Template auto-escaping
- **Secure Password Storage**: PBKDF2 hashing
- **Session Management**: Secure cookie configuration
- **Audit Logging**: All sensitive actions logged
- **Rate Limiting**: API request throttling
- **Data Encryption**: Sensitive data encrypted at rest

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test chatbot

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📈 Performance Optimization

- **Database Indexing**: Optimized queries on frequently accessed fields
- **Caching**: Django cache framework for API responses
- **Lazy Loading**: Pagination for large datasets
- **Query Optimization**: Select_related and prefetch_related
- **Static File Compression**: Minified CSS/JS in production

## 🌐 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL
- [ ] Configure static file serving (WhiteNoise/CDN)
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure email backend
- [ ] Set up logging and monitoring
- [ ] Enable security middleware
- [ ] Configure backup strategy

### Deployment Options

- **Heroku**: One-click deployment
- **AWS EC2**: Full control VPS
- **DigitalOcean**: Managed App Platform
- **Docker**: Containerized deployment
- **Railway**: Modern PaaS

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation
- Add comments for complex logic
- Test across different browsers

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Saurabh** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- VADER Sentiment Analysis by C.J. Hutto
- RASA Framework by Rasa Technologies
- Groq for LLM API access
- YouTube Data API by Google
- Jitsi Meet for video conferencing
- Bootstrap for UI framework
- Django community for excellent documentation

## 📞 Support

- **Email**: support@mindlift.com
- **Documentation**: [docs.mindlift.com](https://docs.mindlift.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mindlift/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mindlift/discussions)

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Multilingual support
- [ ] Group therapy sessions
- [ ] Advanced analytics dashboard
- [ ] Insurance integration
- [ ] Prescription management
- [ ] AI voice assistant
- [ ] Wearable device integration
- [ ] Crisis intervention protocol automation
- [ ] Machine learning model improvements

## ⚠️ Disclaimer

MindLift is designed to provide emotional support and mental health information. It is NOT a replacement for professional mental health treatment. If you're experiencing a mental health crisis, please contact emergency services or a crisis hotline immediately.

**Crisis Resources:**
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency: 911

---

Made with ❤️ for mental health awareness

⭐ Star this repo if you find it helpful!