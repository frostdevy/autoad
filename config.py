import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///autoad.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenRouter
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'jpg', 'jpeg', 'png', 'gif'}
    
    # App settings
    APP_NAME = "AutoAd AI"
    TELEGRAM_WEBHOOK_URL = os.environ.get('TELEGRAM_WEBHOOK_URL')
