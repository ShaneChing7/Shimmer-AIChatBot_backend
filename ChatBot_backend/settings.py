"""
Django settings for ChatBot_backend project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv  # 引入 dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------------
# 加载环境变量
# -------------------------------------------------------------------------
# load_dotenv 会寻找根目录下的 .env 文件
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# 优先从环境变量读取，读不到则使用默认值（防止开发环境报错）
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
# 环境变量读取出来是字符串，需要转换
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*'] # 开发环境允许所有，生产环境请修改


# Application definition

INSTALLED_APPS = [
    'corsheaders',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 第三方库 (Third-party apps)
    'rest_framework',                 # Django REST Framework，用于构建API
    'rest_framework_simplejwt',       # 用于JWT Token认证
    'drf_spectacular',

    # 自定义应用 (Your custom apps)
    'apps.users',                      # 用户应用，用于自定义User模型
    'apps.chat',                      # 聊天应用

    
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware", # 视情况开启
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",     # 您的前端开发服务器
    "http://127.0.0.1:5174",     # 以防万一
]
# 告诉 Django 哪些外部来源是受信任的，它们发起的 POST 请求可以被接受。
# 必须包含您的前端地址。注意，这里只需要协议和域名/端口。
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5174',      # 您的前端 Vue/Vite 开发服务器
    'http://127.0.0.1:5174',      # 以防万一
]

ROOT_URLCONF = "ChatBot_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ChatBot_backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'aichat_db'),
        'USER': os.getenv('DB_USER', 'root'),         # 默认 fallback，防止忘记配置
        'PASSWORD': os.getenv('DB_PASSWORD', ''),     # 默认 fallback
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'users.CustomUser'

# DeepSeek API Key (如果 .env 中没有，默认为空字符串)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', "")

# Tesseract OCR 执行路径
TESSERACT_CMD = os.getenv('TESSERACT_CMD', "")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 文件上传限制
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # 使用 spectacular 来生成 schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# 配置文档的基本信息
SPECTACULAR_SETTINGS = {
    'TITLE': 'ChatBot Backend API',
    'DESCRIPTION': '后端接口文档，提供对话与模型交互能力',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}