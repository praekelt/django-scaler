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

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
)
