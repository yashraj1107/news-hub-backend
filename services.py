import requests
import google.generativeai as genai
import json
from datetime import datetime
from pymongo import MongoClient, TEXT
from pymongo.errors import ConnectionFailure
from bson import ObjectId
import os
import certifi

# --- Category Mapping (Unchanged) ---
CATEGORIES = {
    "World News": "world", "Politics": "politics", "Tech": "technology",
    "Business": "business", "Sports": "sport", "Entertainment": "culture"
}

# --- Database Connection (Unchanged) ---
db_client = None
def get_db_connection(mongo_uri):
    global db_client
    if db_client: return db_client
    try:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        client.admin.command('ismaster')
        db_client = client['news_database']
        return db_client
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        return None

# --- Helpers (Unchanged) ---
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId): return str(o)
        if isinstance(o, datetime): return o.isoformat()
        return json.JSONEncoder.default(self, o)

def get_collection_name(category_name: str) -> str:
    return category_name.lower().replace(' ', '_')

# --- Article Fetching & Generation (Unchanged) ---
# ... (All the functions for fetching and generating articles remain the same) ...
def fetch_articles_by_category(api_key: str):
    api_url = "https://content.guardianapis.com/search"
    all_articles = []
    for category_name, section_id in CATEGORIES.items():
        params = {'api-key': api_key, 'section': section_id, 'order-by': 'newest', 'show-fields': 'bodyText,headline,thumbnail', 'lang': 'en', 'page-size': 1}
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get('response', {}).get('results', [])
            if articles:
                article_info = articles[0]
                all_articles.append({
                    'headline': article_info['fields']['headline'],
                    'body': article_info['fields']['bodyText'],
                    'category': category_name,
                    'thumbnail': article_info['fields'].get('thumbnail') 
                })
        except requests.exceptions.RequestException:
            continue
    return all_articles

def generate_article_with_gemini(api_key: str, original_content: str, original_headline: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f'Rewrite the following article with a new headline. Output as a JSON object with "title" and "content" keys.\n\nSource:\n{original_content}'
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    except Exception:
        return None
        
def save_article_to_db(db_conn, article_data: dict, category: str, image_url: str):
    try:
        collection_name = get_collection_name(category)
        articles_collection = db_conn[collection_name]
        article_data['publishedAt'] = datetime.utcnow()
        article_data['category'] = category
        article_data['imageUrl'] = image_url
        slug = article_data['title'].lower().replace(' ', '-').replace('"', '').replace("'", "").replace("?", "")
        article_data['slug'] = ''.join(c for c in slug if c.isalnum() or c == '-')[:80]
        if articles_collection.find_one({'slug': article_data['slug']}):
            return None
        return articles_collection.insert_one(article_data)
    except Exception:
        return None

def get_articles_from_db(db_conn, page: int = 1, per_page: int = 10):
    all_articles = []
    try:
        for category_name in CATEGORIES.keys():
            collection_name = get_collection_name(category_name)
            articles_cursor = db_conn[collection_name].find().sort('publishedAt', -1).limit(3)
            all_articles.extend(list(articles_cursor))
        all_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
        start = (page - 1) * per_page
        end = start + per_page
        return all_articles[start:end]
    except Exception:
        return []

def get_single_article_from_db(db_conn, category_name: str, slug: str):
    try:
        collection_name = get_collection_name(category_name)
        return db_conn[collection_name].find_one({'slug': slug})
    except Exception:
        return None

def get_articles_by_category_from_db(db_conn, category: str, page: int = 1, per_page: int = 10):
    try:
        collection_name = get_collection_name(category)
        articles_cursor = db_conn[collection_name].find().sort('publishedAt', -1).skip((page - 1) * per_page).limit(per_page)
        return list(articles_cursor)
    except Exception:
        return []

def get_related_articles_from_db(db_conn, category_name: str, original_article_id: str, count: int = 3):
    try:
        collection_name = get_collection_name(category_name)
        return list(db_conn[collection_name].find(
            {'_id': {'$ne': ObjectId(original_article_id)}}
        ).sort('publishedAt', -1).limit(count))
    except Exception:
        return []

def search_articles_in_db(db_conn, query: str):
    search_results = []
    try:
        for category_name in CATEGORIES.keys():
            collection_name = get_collection_name(category_name)
            results = db_conn[collection_name].find({'$text': {'$search': query}}).sort([('score', {'$meta': 'textScore'})])
            search_results.extend(list(results))
        search_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return search_results
    except Exception:
        return []


# --- NEW: Function for Saving Subscribers ---
def save_subscriber_to_db(db_conn, email: str):
    """
    Saves a new email subscriber to the database.
    Ensures that emails are unique.
    """
    try:
        subscribers_collection = db_conn['subscribers']
        # Create a unique index on the 'email' field if it doesn't exist.
        # This is an efficient way to prevent duplicate emails.
        subscribers_collection.create_index("email", unique=True)
        
        # Check if the email already exists
        if subscribers_collection.find_one({'email': email}):
            print(f"Email already subscribed: {email}")
            return {"status": "exists"}

        # Insert the new subscriber
        result = subscribers_collection.insert_one({
            'email': email,
            'subscribedAt': datetime.utcnow()
        })
        print(f"New subscriber saved: {email}")
        return {"status": "success", "id": result.inserted_id}
    except Exception as e:
        print(f"Error saving subscriber: {e}")
        return {"status": "error"}