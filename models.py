from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Social media credentials
    tiktok_email = db.Column(db.String(200))
    tiktok_password = db.Column(db.String(500))
    tiktok_session = db.Column(db.Text)
    
    instagram_email = db.Column(db.String(200))
    instagram_password = db.Column(db.String(500))
    instagram_session = db.Column(db.Text)
    
    # OpenRouter API key
    openrouter_api_key = db.Column(db.String(200))
    
    # Telegram bot
    telegram_bot_token = db.Column(db.String(200))
    telegram_chat_id = db.Column(db.String(100))
    telegram_enabled = db.Column(db.Boolean, default=False)
    
    # Profile settings
    shop_url = db.Column(db.String(500))
    shop_name = db.Column(db.String(200))
    profile_picture = db.Column(db.String(200))
    bio = db.Column(db.Text)
    business_category = db.Column(db.String(100))
    
    ads = db.relationship('Ad', backref='user', lazy=True)
    analytics = db.relationship('Analytics', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    telegram_chats = db.relationship('TelegramChat', backref='user', lazy=True)

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    video_path = db.Column(db.String(500))
    thumbnail_path = db.Column(db.String(500))
    platform = db.Column(db.String(20))
    scheduled_time = db.Column(db.DateTime)
    posted_time = db.Column(db.DateTime)
    daily_goal = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    platform_post_id = db.Column(db.String(200))
    
    # Comments tracking
    last_comments_check = db.Column(db.DateTime)
    top_comments = db.Column(db.Text)  # JSON

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    platform = db.Column(db.String(20))
    metric_type = db.Column(db.String(50))
    value = db.Column(db.Float)
    
    best_time_tiktok = db.Column(db.String(100))
    best_time_instagram = db.Column(db.String(100))
    engagement_score = db.Column(db.Float)
    reach_score = db.Column(db.Float)
    posting_times = db.Column(db.Text)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50))  # 'post_success', 'post_failed', 'milestone', 'comment'
    message = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.Text)  # JSON data

class TelegramChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.String(100))
    message_id = db.Column(db.String(100))
    command = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime)

class ScheduleSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(20))
    ads_per_day = db.Column(db.Integer, default=1)
    time_slot = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
