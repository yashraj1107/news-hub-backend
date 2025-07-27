from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json 
from config import Config
from services import (
    get_db_connection,
    fetch_articles_by_category, 
    generate_article_with_gemini,
    save_article_to_db,
    get_articles_from_db,
    get_single_article_from_db,
    get_articles_by_category_from_db,
    get_related_articles_from_db,
    search_articles_in_db,
    save_subscriber_to_db, # NEW
    JSONEncoder
)

app = Flask(__name__)
CORS(app)

db = get_db_connection(Config.MONGO_CONNECTION_STRING)
if db is None:
    raise Exception("Failed to connect to the database. Application cannot start.")

def make_json_response(data, status_code=200):
    return Response(response=json.dumps(data, cls=JSONEncoder), status=status_code, mimetype='application/json')

# --- API Endpoints (Unchanged) ---
@app.route('/api/v1/articles', methods=['GET'])
def get_articles():
    page = int(request.args.get('page', 1)); limit = int(request.args.get('limit', 10))
    articles = get_articles_from_db(db, page, limit)
    return make_json_response(articles)

@app.route('/api/v1/articles/category/<category_name>/<slug>', methods=['GET'])
def get_article_by_slug(category_name, slug):
    article = get_single_article_from_db(db, category_name, slug)
    if article:
        related_articles = get_related_articles_from_db(db, article['category'], str(article['_id']))
        return make_json_response({"article": article, "related": related_articles})
    return jsonify({"status": "error", "message": "Article not found."}), 404

@app.route('/api/v1/articles/category/<category_name>', methods=['GET'])
def get_articles_by_category(category_name):
    page = int(request.args.get('page', 1)); limit = int(request.args.get('limit', 10))
    articles = get_articles_by_category_from_db(db, category_name, page, limit)
    return make_json_response(articles)

@app.route('/api/v1/search', methods=['GET'])
def search_articles():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": "error", "message": "Search query 'q' is required."}), 400
    results = search_articles_in_db(db, query)
    return make_json_response(results)


# --- NEW: Subscription Endpoint ---
@app.route('/api/v1/subscribe', methods=['POST'])
def subscribe_to_newsletter():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"status": "error", "message": "Email is required."}), 400
    
    result = save_subscriber_to_db(db, email)

    if result['status'] == 'success':
        return jsonify({"status": "success", "message": "Successfully subscribed!"}), 201
    elif result['status'] == 'exists':
        return jsonify({"status": "exists", "message": "This email is already subscribed."}), 200
    else:
        return jsonify({"status": "error", "message": "An error occurred."}), 500


# --- Scheduler Endpoint (Unchanged) ---
@app.route('/api/v1/generate-and-save', methods=['POST'])
def generate_and_save_articles():
    # This function is unchanged
    guardian_articles = fetch_articles_by_category(Config.GUARDIAN_API_KEY)
    if not guardian_articles:
        return jsonify({"status": "success", "message": "No new articles to process."}), 200
    generated_count = 0
    for article in guardian_articles:
        generated_article = generate_article_with_gemini(api_key=Config.GEMINI_API_KEY, original_content=article['body'], original_headline=article['headline'])
        if generated_article and 'title' in generated_article:
            result = save_article_to_db(db_conn=db, article_data=generated_article, category=article['category'], image_url=article['thumbnail'])
            if result:
                generated_count += 1
    return jsonify({"status": "success", "message": f"Generated and saved {generated_count} articles."}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
