"""
Django settings for webapp project.
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
    # REMOVED: 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'chatbot.middleware.YouTubeEmbedMiddleware',  # Must be last
]


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
# RASA CONFIGURATION
# ------------------------------------------------------------------
RASA_SERVER_URL = os.getenv('RASA_SERVER_URL', 'http://localhost:5005')


# ------------------------------------------------------------------
# SECURITY SETTINGS FOR DEVELOPMENT - YOUTUBE EMBED FIX
# ------------------------------------------------------------------
# Disable X-Frame-Options to allow YouTube embeds
X_FRAME_OPTIONS = None

# Disable these security features for development
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# SSL and Cookie settings for development
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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
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
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}