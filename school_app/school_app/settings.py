from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# En production : définir la variable d'environnement DJANGO_SECRET_KEY
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-rdcschool-2024-secret-key-change-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# CSRF : domaines autorisés
# En production sur PythonAnywhere, définir la variable DJANGO_SITE_URL
# Exemple : export DJANGO_SITE_URL=https://educ.pythonanywhere.com
_site_url = os.environ.get('DJANGO_SITE_URL', '').strip()

CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.spock.replit.dev',
    'https://*.replit.app',
    'http://localhost:8000',
    'http://localhost:8008',
]

if _site_url:
    # Ajouter automatiquement l'URL de production (ex: https://educ.pythonanywhere.com)
    if not _site_url.startswith(('http://', 'https://')):
        _site_url = 'https://' + _site_url
    CSRF_TRUSTED_ORIGINS.append(_site_url)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'dashboard',
    'students',
    'teachers',
    'subjects',
    'classes',
    'bulletin',
    'grades',
    'reports',
    'school_settings',
    'portail',
    'carte_eleve',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.ForcePasswordChangeMiddleware',   # doit être APRÈS AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'school_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'school_settings.context_processors.school_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'school_app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',           # connexion par e-mail (prioritaire)
    'django.contrib.auth.backends.ModelBackend', # fallback identifiant (comptes existants)
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# ── Connexions DB persistantes (réduit la latence de reconnexion) ─────────────
CONN_MAX_AGE = 60  # secondes

# ── Logging ───────────────────────────────────────────────────────────────────
import os as _os
_os.makedirs(BASE_DIR / 'logs', exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'WARNING',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR / 'logs' / 'sgn.log'),
            'maxBytes': 5 * 1024 * 1024,   # 5 MB par fichier
            'backupCount': 3,
            'formatter': 'verbose',
            'level': 'INFO',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # Erreurs Django (vues, templates, requêtes) → fichier
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Logger applicatif SGN → utilisé dans les vues avec logger = logging.getLogger('sgn')
        'sgn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
