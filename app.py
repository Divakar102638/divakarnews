import requests
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- CONFIGURATION ---
API_KEY = '54d06bca5ccc423487e13d532edfde8c'
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filename(lang, location):
    # Sanitize location for filename
    safe_location = "".join(c for c in location if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return os.path.join(CACHE_DIR, f'news_{lang}_{safe_location}.json')

def is_cache_valid(filepath):
    if not os.path.exists(filepath):
        return False
    # Check if file is less than 24 hours old
    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - file_time < timedelta(hours=24)

@app.route('/news')
def get_news():
    lang = request.args.get('lang', 'en')
    location = request.args.get('location', 'India')
    
    cache_file = get_cache_filename(lang, location)
    
    if is_cache_valid(cache_file):
        print(f"📋 Using cached news for {location} in {lang}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    
    print(f"🚀 Fetching fresh news for {datetime.now().strftime('%Y-%m-%d')} in {location}, language: {lang}...")
    
    # Query based on location + all major categories (cinema/sports/politics/business/tech)
    location_fragment = location if location else 'Andhra Pradesh'
    category_boost = 'cinema OR sports OR entertainment OR politics OR business OR technology'
    location_query = f'{location_fragment} OR Andhra Pradesh OR Hyderabad OR India OR {category_boost}'

    # Fetching 50 items (Max per request on free plan)
    url = f'https://newsapi.org/v2/everything?q={location_query}&language={lang}&sortBy=publishedAt&pageSize=50&apiKey={API_KEY}'
    
    try:
        response = requests.get(url)
        data = response.json()

        if data.get('status') == 'ok':
            articles = data['articles']
            formatted_news = []

            for art in articles:
                # This structure matches your HTML/JS 'newsData' perfectly
                entry = {
                    "img": art['urlToImage'] if art['urlToImage'] else "https://images.unsplash.com/photo-1504711432869-efd5971ee142",
                    "en": {
                        "title": art['title'],
                        "desc": art['description'][:150] if art['description'] else "Real-time update from Omni News."
                    },
                    "te": {
                        "title": f"వార్త: {art['title'][:40]}...", # Placeholder for Telugu
                        "desc": "తెలుగు అప్‌డేట్ త్వరలో రాబోతోంది."
                    },
                    "hi": {
                        "title": f"समाचार: {art['title'][:40]}...", # Placeholder for Hindi
                        "desc": "हिंदी अपडेट जल्द ही आ रहा है।"
                    }
                }
                formatted_news.append(entry)

            # Cache the result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_news, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Success! {len(formatted_news)} items fetched and cached.")
            return jsonify(formatted_news)
        else:
            print(f"❌ API Error: {data.get('message')}")
            return jsonify({"error": data.get('message')}), 500
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)