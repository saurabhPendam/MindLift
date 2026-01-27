# 🧠 MindLift - AI-Powered Mental Health Chatbot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A comprehensive mental health support platform combining AI chatbot technology, sentiment analysis, and professional consultation features to provide 24/7 emotional wellness support.

![MindLift Banner](docs/images/banner.png)

## 🌟 Features

### 💬 Intelligent AI Chatbot
- **Hybrid AI System**: Combines RASA NLU for intent detection with Groq LLM for natural, empathetic responses
- **Crisis Detection**: Automatic identification of crisis keywords with immediate professional resource recommendations
- **Context-Aware**: Maintains conversation history for coherent, personalized interactions
- **Multi-modal Support**: Text and voice input capabilities

### 📊 Sentiment Analysis
- **Real-time Analysis**: VADER sentiment analysis on every user message
- **Emotion Detection**: NRCLex-based emotion recognition (joy, sadness, anger, fear, etc.)
- **Trend Tracking**: Monitor emotional patterns over time
- **Detailed Reports**: Generate comprehensive sentiment reports with actionable insights

### 🎥 Therapeutic Content Integration
- **YouTube Integration**: Context-aware mental health video recommendations
- **Curated Resources**: Fallback library of verified mental health content
- **Activity Suggestions**: Guided breathing exercises, meditation, mindfulness activities

### 🏥 Professional Support
- **Video Consultations**: Integrated Jitsi Meet for secure video calls with mental health professionals
- **Doctor Profiles**: Browse and connect with licensed therapists and psychiatrists
- **Appointment Scheduling**: Book and manage therapy sessions

### 📈 Wellness Tracking
- **Activity Logger**: Track completion of wellness activities with ratings
- **Progress Visualization**: Charts and graphs showing emotional journey
- **Motivational Quotes**: Daily inspirational content with favorites system
- **Goal Setting**: Personal wellness objectives and milestones

### 🔒 Privacy & Security
- **End-to-End Encryption**: Secure data transmission
- **Account Deletion**: 30-day grace period for account deletion with data export
- **Audit Logging**: Comprehensive activity tracking for security
- **GDPR Compliant**: User data rights and privacy controls

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