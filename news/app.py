import requests
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from googletrans import Translator
import os

app = Flask(__name__)
CORS(app)
translator = Translator()

# --- CONFIGURATION ---
API_KEY = '54d06bca5ccc423487e13d532edfde8c'
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filename(lang, location):
    safe_location = "".join(c for c in location if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return os.path.join(CACHE_DIR, f'news_{lang}_{safe_location}.json')

def is_cache_valid(filepath):
    if not os.path.exists(filepath): return False
    return datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath)) < timedelta(hours=6)

@app.route('/news')
def get_news():
    lang = request.args.get('lang', 'en')
    location = request.args.get('location', 'Andhra Pradesh')
    cache_file = get_cache_filename(lang, location)

    if is_cache_valid(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))

    # Search query: Mix of location and trending topics
    query = f"{location} OR Hyderabad OR India OR cinema OR sports"
    url = f'https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={API_KEY}'

    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])
        formatted_news = []

        for art in articles[:15]: # Limit to 15 for speed
            en_title = art['title']
            en_desc = art['description'][:150] if art['description'] else "Tap to read more."
            
            entry = {
                "img": art['urlToImage'] if art['urlToImage'] else "https://images.unsplash.com/photo-1504711432869-efd5971ee142",
                "en": {"title": en_title, "desc": en_desc}
            }

            # Auto-Translate for Telugu and Hindi
            for target_lang in ['te', 'hi']:
                try:
                    t_title = translator.translate(en_title, dest=target_lang).text
                    t_desc = translator.translate(en_desc, dest=target_lang).text
                    entry[target_lang] = {"title": t_title, "desc": t_desc}
                except:
                    entry[target_lang] = {"title": en_title, "desc": en_desc}

            formatted_news.append(entry)

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_news, f, indent=4, ensure_ascii=False)

        return jsonify(formatted_news)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)