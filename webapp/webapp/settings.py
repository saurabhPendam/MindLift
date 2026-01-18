"""
Django settings for webapp project - Optimized for Performance
File: webapp/settings.py
"""

from pathlib import Path
import os

# ------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------
SECRET_KEY = 'django-insecure-q2z$9m3=o61l90eo&*4jne!nihuj-srh2piaxd+2xf3n*(l!y!'

DEBUG = True

ALLOWED_HOSTS = ['*']


# ------------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------------
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'chatbot',
]


# ------------------------------------------------------------------
# MIDDLEWARE - IMPORTANT: Order matters!
# ------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'chatbot.middleware.YouTubeEmbedMiddleware',  # Must be last
]


# ------------------------------------------------------------------
# CACHING CONFIGURATION (NEW - For Performance)
# ------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mindlift-cache',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}


# ------------------------------------------------------------------
# URL CONFIGURATION
# ------------------------------------------------------------------
ROOT_URLCONF = 'webapp.urls'


# ------------------------------------------------------------------
# TEMPLATES CONFIGURATION
# ------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'chatbot' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ------------------------------------------------------------------
# WSGI
# ------------------------------------------------------------------
WSGI_APPLICATION = 'webapp.wsgi.application'


# ------------------------------------------------------------------
# DATABASE (DEV MODE)
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mindlift_db',
        'USER': 'mindlift_user',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,  # Connection pooling for better performance
    }
}


# ------------------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------
# STATIC FILES (CSS, JS, IMAGES)
# ------------------------------------------------------------------
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'chatbot' / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ------------------------------------------------------------------
# MEDIA FILES
# ------------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ------------------------------------------------------------------
# AUTHENTICATION REDIRECTS
# ------------------------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/chat/'
LOGOUT_REDIRECT_URL = '/'


# ------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------------
# SESSION SETTINGS
# ------------------------------------------------------------------
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True


# ------------------------------------------------------------------
# SECURITY SETTINGS FOR DEVELOPMENT
# ------------------------------------------------------------------
X_FRAME_OPTIONS = None
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'


# ------------------------------------------------------------------
# LOGGING CONFIGURATION
# ------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'chatbot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # Changed from DEBUG
            'propagate': False,
        },
        'llm_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
# ------------------------------------------------------------------
# LLM CONFIGURATION (Ollama + RASA)
# ------------------------------------------------------------------

import os

# LLM CONFIGURATION (Ollama + RASA) - OPTIMIZED
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_PRIMARY_MODEL = os.getenv('OLLAMA_PRIMARY_MODEL', 'gemma:2b')
OLLAMA_FALLBACK_MODEL = os.getenv('OLLAMA_FALLBACK_MODEL', 'phi3:mini')
USE_OLLAMA = os.getenv('USE_OLLAMA', 'True').lower() == 'true'

# RASA Configuration
RASA_SERVER_URL = os.getenv('RASA_SERVER_URL', 'http://localhost:5005')

# ------------------------------------------------------------------
# PERFORMANCE SETTINGS - OPTIMIZED
# ------------------------------------------------------------------

# Reduced timeouts for faster user experience
OLLAMA_PRIMARY_TIMEOUT = int(os.getenv('OLLAMA_PRIMARY_TIMEOUT', '20'))   # 8 seconds 
OLLAMA_FALLBACK_TIMEOUT = int(os.getenv('OLLAMA_FALLBACK_TIMEOUT', '15')) # 4 seconds 
RASA_REQUEST_TIMEOUT = int(os.getenv('RASA_REQUEST_TIMEOUT', '10'))      # 10 seconds

# Context window - reduced for speed
MAX_CONTEXT_MESSAGES = int(os.getenv('MAX_CONTEXT_MESSAGES', '2'))  # Last 2 messages 

# Response length - reduced for speed
MAX_RESPONSE_TOKENS = int(os.getenv('MAX_RESPONSE_TOKENS', '100'))  # 100 tokens 