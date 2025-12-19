"""
Django settings for zennovel_web project.
Updated for Production & Local Development Compatibility.
"""

from pathlib import Path
import os
from decouple import config  # Pastikan sudah install python-decouple
import dj_database_url       # Pastikan sudah install dj-database-url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- KONFIGURASI KEAMANAN & DEPLOY ---

# 1. SECRET KEY
# Di laptop, pakai default 'django-insecure...'. Di server, wajib pakai env variable.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-84i+&^h#rbio_@0$$x_6_ea$cir-44utw#!b9b#)(6(2fh^x%n')

# 2. DEBUG
# True hanya jika di laptop. False jika di server (Render/Railway/dll).
# Kita deteksi apakah ada environment variable bernama 'RENDER' (atau lainnya).
DEBUG = config('DEBUG', default=True, cast=bool)

# 3. ALLOWED HOSTS
# '*' membolehkan semua domain mengakses (aman untuk tahap awal deploy).
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',      # <--- Tambah ini
    'library',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    
    # WhiteNoise: Wajib ada di sini (urutan ke-2) untuk melayani CSS/JS di server
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zennovel_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'library/templates')],
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

WSGI_APPLICATION = 'zennovel_web.wsgi.application'


# --- DATABASE ---
# Otomatis pilih: SQLite di Laptop, PostgreSQL di Server (jika ada DATABASE_URL)
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- STATIC & MEDIA FILES (PENTING UNTUK TAMPILAN) ---

STATIC_URL = 'static/'

# Folder tempat mengumpulkan file static saat deploy
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Folder static tambahan di project (jika ada)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Kompresi file static agar website cepat (WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files (Upload Cover/EPUB)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "https://zennovel-frontend.netlify.app", # Contoh domain frontend Anda nanti
#     "http://localhost:3000", # Untuk testing di laptop (Vite/React)
# ]