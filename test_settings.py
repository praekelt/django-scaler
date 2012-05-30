import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ROOT_URLCONF = 'scaler.urls'

INSTALLED_APPS = (
    'scaler',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
)

MIDDLEWARE_CLASSES = (
    'scaler.middleware.ScalerMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)
