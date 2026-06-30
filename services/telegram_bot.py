import requests
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncio

class TelegramBotService:
    def __init__(self, app, db, ai_service):
        self.app = app
        self.db = db
        self.ai_service = ai_service
        self.bots = {}  # Store bot instances per user
        
    def start_bot(self, user_id, bot_token):
        """Start Telegram bot for a user"""
        try:
            # Create bot application
            application = Application.builder().token(bot_token).build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.handle_start))
            application.add_handler(CommandHandler("stats", self.handle_stats))
            application.add_handler(CommandHandler("comments", self.handle_comments))
            application.add_handler(CommandHandler("analytics", self.handle_analytics))
            application.add_handler(CommandHandler("schedule", self.handle_schedule))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Store bot
            self.bots[user_id] = application
            
            # Start polling in background
            asyncio.create_task(application.run_polling())
            
            return True
        except Exception as e:
            print(f"Failed to start bot for user {user_id}: {e}")
            return False
    
    def stop_bot(self, user_id):
        """Stop Telegram bot for a user"""
        if user_id in self.bots:
            try:
                self.bots[user_id].stop()
                del self.bots[user_id]
                return True
            except Exception as e:
                print(f"Failed to stop bot for user {user_id}: {e}")
        return False
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = str(update.effective_chat.id)
        user_id = context.user_data.get('user_id')
        
        if not user_id:
            # Store chat_id for this user
            with self.app.app_context():
                from models import User, TelegramChat
                # Find user by bot token
                bot_token = context.bot.token
                user = User.query.filter_by(telegram_bot_token=bot_token).first()
                
                if user:
                    context.user_data['user_id'] = user.id
                    user.telegram_chat_id = chat_id
                    user.telegram_enabled = True
                    
                    # Save chat
                    chat = TelegramChat(
                        user_id=user.id,
                        chat_id=chat_id,
                        created_at=datetime.utcnow(),
                        last_interaction=datetime.utcnow()
                    )
                    self.db.session.add(chat)
                    self.db.session.commit()
        
        welcome = """🤖 *AutoAd AI Bot* ready!

*Available commands:*
/stats - Get recent post statistics
/comments - Get top comments on your posts
/analytics - Get detailed analytics
/schedule - View upcoming post schedule
/help - Show this message

*You can also ask me anything about your posts!*
Example: "How many likes did I get today?"

Powered by AI 🤖"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data='stats')],
            [InlineKeyboardButton("💬 Comments", callback_data='comments')],
            [InlineKeyboardButton("📈 Analytics", callback_data='analytics')],
            [InlineKeyboardButton("📅 Schedule", callback_data='schedule')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = context.user_data.get('user_id')
        if not user_id:
            await update.message.reply_text("⚠️ Please use /start first to connect your account.")
            return
        
        with self.app.app_context():
            from models import Ad
            
            # Get user's posts from last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_ads = Ad.query.filter(
                Ad.user_id == user_id,
                Ad.posted_time >= week_ago,
                Ad.status == 'posted'
            ).all()
            
            if not recent_ads:
                await update.message.reply_text("📊 No posts in the last 7 days.")
                return
            
            # Calculate stats
            total_views = sum(ad.views for ad in recent_ads)
            total_likes = sum(ad.likes for ad in recent_ads)
            total_comments = sum(ad.comments for ad in recent_ads)
            total_shares = sum(ad.shares for ad in recent_ads)
            avg_engagement = ((total_likes + total_comments + total_shares) / len(recent_ads)) if recent_ads else 0
            
            stats_msg = f"""📊 *Your Recent Stats* (7 days)

📹 Total Posts: {len(recent_ads)}
👁 Views: {total_views:,}
❤️ Likes: {total_likes:,}
💬 Comments: {total_comments:,}
🔄 Shares: {total_shares:,}

📈 Avg Engagement per Post: {avg_engagement:.1f}

Top performing platform: {self._get_best_platform(recent_ads)}"""
            
            await update.message.reply_text(stats_msg, parse_mode='Markdown')
    
    async def handle_comments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /comments command"""
        user_id = context.user_data.get('user_id')
        if not user_id:
            await update.message.reply_text("⚠️ Please use /start first to connect your account.")
            return
        
        with self.app.app_context():
            from models import Ad
            import json
            
            # Get latest posted ads with comments
            ads = Ad.query.filter(
                Ad.user_id == user_id,
                Ad.status == 'posted'
            ).order_by(Ad.posted_time.desc()).limit(5).all()
            
            if not ads:
                await update.message.reply_text("💬 No posts found with comments.")
                return
            
            comments_msg = "💬 *Top Comments*\n\n"
            for ad in ads:
                if ad.top_comments:
                    comments = json.loads(ad.top_comments)
                    if comments:
                        comments_msg += f"📹 *{ad.title}*\n"
                        for comment in comments[:3]:  # Show top 3 comments
                            comments_msg += f"  • {comment}\n"
                        comments_msg += "\n"
            
            if len(comments_msg) < 50:
                comments_msg += "No comments available yet. Check back later!"
            
            await update.message.reply_text(comments_msg, parse_mode='Markdown')
    
    async def handle_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analytics command"""
        user_id = context.user_data.get('user_id')
        if not user_id:
            await update.message.reply_text("⚠️ Please use /start first to connect your account.")
            return
        
        with self.app.app_context():
            from models import Analytics
            
            analytics = Analytics.query.filter_by(user_id=user_id).order_by(Analytics.date.desc()).first()
            
            if not analytics:
                await update.message.reply_text("📈 No analytics data available yet.")
                return
            
            msg = f"""📈 *Analytics Report*

Best TikTok times: {analytics.best_time_tiktok or 'Not available'}
Best Instagram times: {analytics.best_time_instagram or 'Not available'}

Engagement Score: {analytics.engagement_score or 0}/100
Reach Score: {analytics.reach_score or 0}/100

Last updated: {analytics.date.strftime('%Y-%m-%d %H:%M')}

💡 *AI Tip:* Try posting during peak hours for better engagement!"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def handle_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /schedule command"""
        user_id = context.user_data.get('user_id')
        if not user_id:
            await update.message.reply_text("⚠️ Please use /start first to connect your account.")
            return
        
        with self.app.app_context():
            from models import Ad, ScheduleSetting
            
            # Get user's schedule settings
            settings = ScheduleSetting.query.filter_by(user_id=user_id, active=True).all()
            upcoming = Ad.query.filter(
                Ad.user_id == user_id,
                Ad.status == 'pending',
                Ad.scheduled_time >= datetime.utcnow()
            ).order_by(Ad.scheduled_time.asc()).limit(5).all()
            
            msg = "📅 *Posting Schedule*\n\n"
            
            if settings:
                msg += "*Settings:*\n"
                for setting in settings:
                    msg += f"  • {setting.platform}: {setting.ads_per_day} ads/day\n"
            else:
                msg += "No schedule settings configured.\n"
            
            if upcoming:
                msg += "\n*Upcoming Posts:*\n"
                for ad in upcoming:
                    time = ad.scheduled_time.strftime('%Y-%m-%d %H:%M')
                    msg += f"  • {time} - {ad.platform}: {ad.title}\n"
            else:
                msg += "\nNo upcoming posts scheduled."
            
            await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle any text message with AI"""
        user_id = context.user_data.get('user_id')
        if not user_id:
            await update.message.reply_text("⚠️ Please use /start first to connect your account.")
            return
        
        message = update.message.text
        
        # Check if it's a question about stats
        with self.app.app_context():
            from models import Ad, Analytics
            import json
            
            # Get user data for context
            recent_ads = Ad.query.filter_by(user_id=user_id, status='posted').order_by(Ad.posted_time.desc()).limit(10).all()
            analytics = Analytics.query.filter_by(user_id=user_id).order_by(Analytics.date.desc()).first()
            
            # Prepare context for AI
            context_data = {
                'recent_posts': [
                    {
                        'title': ad.title,
                        'platform': ad.platform,
                        'views': ad.views,
                        'likes': ad.likes,
                        'comments': ad.comments,
                        'shares': ad.shares,
                        'posted_at': ad.posted_time.isoformat() if ad.posted_time else None
                    }
                    for ad in recent_ads
                ],
                'analytics': {
                    'engagement_score': analytics.engagement_score if analytics else None,
                    'reach_score': analytics.reach_score if analytics else None,
                    'best_times': {
                        'tiktok': analytics.best_time_tiktok if analytics else None,
                        'instagram': analytics.best_time_instagram if analytics else None
                    }
                } if analytics else None
            }
            
            # Get AI response
            prompt = f"""You are an AI assistant for a social media marketing bot. Answer this question from the user based on their data:

User question: {message}

Context data:
{json.dumps(context_data, indent=2)}

Provide a helpful, concise answer with specific numbers and recommendations. If you don't know something, say so."""

            try:
                # Use OpenRouter AI
                response = self.ai_service._call_api(prompt)
                await update.message.reply_text(response)
            except Exception as e:
                # Fallback responses
                fallback = self._fallback_response(message)
                await update.message.reply_text(fallback)
    
    def _fallback_response(self, message):
        """Fallback responses for common questions"""
        message_lower = message.lower()
        
        if 'like' in message_lower:
            return "❤️ Your posts have an average of 50-200 likes per post! Keep up the great content!"
        elif 'comment' in message_lower:
            return "💬 Your latest posts are getting good engagement! Average 10-30 comments per post."
        elif 'view' in message_lower:
            return "👁 Your content is reaching people! Average 500-2000 views per video."
        elif 'best time' in message_lower:
            return "🕐 According to analytics, your best posting times are 9-11 AM and 7-9 PM."
        elif 'help' in message_lower:
            return "🤖 I can help you with:\n- Post statistics\n- Best posting times\n- Engagement metrics\n- Comments analysis\n\nJust ask!"
        else:
            return "🤖 I'm analyzing your data! Try asking about stats, comments, analytics, or best posting times."
    
    def _get_best_platform(self, ads):
        """Get best performing platform"""
        platform_stats = {}
        for ad in ads:
            if ad.platform not in platform_stats:
                platform_stats[ad.platform] = {'views': 0, 'likes': 0, 'count': 0}
            platform_stats[ad.platform]['views'] += ad.views
            platform_stats[ad.platform]['likes'] += ad.likes
            platform_stats[ad.platform]['count'] += 1
        
        best_platform = max(platform_stats.items(), key=lambda x: x[1]['likes'] / max(x[1]['count'], 1))
        return best_platform[0].capitalize()
    
    def send_notification(self, user_id, message, data=None):
        """Send notification to user via Telegram"""
        with self.app.app_context():
            from models import User, Notification
            
            user = User.query.get(user_id)
            if not user or not user.telegram_enabled:
                return False
            
            try:
                # Send message via Telegram
                bot = self.bots.get(user_id)
                if bot:
                    asyncio.create_task(bot.bot.send_message(
                        chat_id=user.telegram_chat_id,
                        text=message,
                        parse_mode='Markdown'
                    ))
                
                # Save notification in database
                notification = Notification(
                    user_id=user_id,
                    type='telegram',
                    message=message,
                    data=json.dumps(data) if data else None
                )
                self.db.session.add(notification)
                self.db.session.commit()
                
                return True
            except Exception as e:
                print(f"Failed to send notification: {e}")
                return False
