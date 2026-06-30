import requests
import json
import re

class OpenRouterService:
    def __init__(self, api_key=None, api_url=None, model=None):
        self.api_key = api_key
        self.api_url = api_url or "https://openrouter.ai/api/v1/chat/completions"
        self.model = model or "google/gemini-2.0-flash-thinking-exp:free"
    
    def set_api_key(self, api_key):
        """Set API key for user"""
        self.api_key = api_key
    
    def generate_description(self, product_name, product_desc, platform, api_key=None):
        """Generate AI description for ad"""
        if api_key:
            self.api_key = api_key
            
        prompt = f"""Generate a compelling social media ad description for {platform} platform.
        
Product: {product_name}
Description: {product_desc}

Requirements:
- Engaging hook (first line)
- 2-3 benefits of the product
- Call to action
- Use relevant emojis
- Max 150 characters for TikTok, 2200 for Instagram
- Include trending hashtags (3-5)

Return only the description text."""

        try:
            if self.api_key:
                response = self._call_api(prompt)
                return response.strip()
            else:
                return self._fallback_description(product_name, platform)
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._fallback_description(product_name, platform)
    
    def analyze_best_times(self, historical_data, api_key=None):
        """Analyze best posting times using AI"""
        if api_key:
            self.api_key = api_key
            
        prompt = f"""Analyze this social media engagement data and recommend best posting times:
        
{json.dumps(historical_data, indent=2)}

Return a JSON with:
1. Best time slots for TikTok (3 time ranges)
2. Best time slots for Instagram (3 time ranges)
3. Engagement score (0-100)
4. Recommendation explanation

Format: {{"tiktok_times": [...], "instagram_times": [...], "score": 0, "explanation": ""}}"""

        try:
            if self.api_key:
                response = self._call_api(prompt)
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            return self._fallback_times()
        except Exception as e:
            print(f"Time analysis error: {e}")
            return self._fallback_times()
    
    def chat(self, user_message, context, api_key=None):
        """Handle chat messages"""
        if api_key:
            self.api_key = api_key
            
        prompt = f"""You are an AI assistant for a social media marketing automation tool. 
Context from user's account:
{json.dumps(context, indent=2)}

User message: {user_message}

Provide a helpful, friendly response with specific insights from their data."""

        try:
            if self.api_key:
                response = self._call_api(prompt)
                return response
            else:
                return "Please add your OpenRouter API key in settings to use AI features."
        except Exception as e:
            return f"AI error: {e}"
    
    def _call_api(self, prompt):
        """Call OpenRouter API"""
        if not self.api_key:
            raise Exception("API key not set")
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert social media marketing AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _fallback_description(self, product_name, platform):
        """Fallback if AI fails"""
        emojis = ['🔥', '✨', '💯', '🎯', '⭐']
        hashtags = ['#viral', '#trending', '#new', '#amazing']
        
        import random
        desc = f"Check out {product_name}! {random.choice(emojis)} Get yours now!"
        desc += " " + ' '.join(random.sample(hashtags, 3))
        return desc
    
    def _fallback_times(self):
        """Fallback time analysis"""
        return {
            "tiktok_times": ["09:00-11:00", "14:00-16:00", "19:00-21:00"],
            "instagram_times": ["10:00-12:00", "15:00-17:00", "20:00-22:00"],
            "score": 75,
            "explanation": "Optimal times based on general engagement patterns"
        }
