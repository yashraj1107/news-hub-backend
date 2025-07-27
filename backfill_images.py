# backfill_images.py
# A one-time script to find articles without images and generate them.

import time
from config import Config
from services import (
    get_db_connection,
    generate_image_with_imagen,
    CATEGORIES,
    get_collection_name
)

def backfill_missing_images():
    """
    Connects to the database, finds all articles in each category
    that are missing an 'imageUrl', generates an image, and updates
    the document.
    """
    print("--- Starting Image Backfill Script ---")
    
    # Establish database connection
    db = get_db_connection(Config.MONGO_CONNECTION_STRING)
    if db is None:
        print("!!! Could not connect to the database. Aborting script. !!!")
        return

    total_updated = 0

    # Loop through each defined category
    for category_name, details in CATEGORIES.items():
        collection_name = get_collection_name(category_name)
        articles_collection = db[collection_name]
        
        print(f"\n>>> Checking collection: '{collection_name}'...")

        # Find all documents where 'imageUrl' field does not exist or is null
        articles_to_update = list(articles_collection.find({
            "$or": [
                { "imageUrl": { "$exists": False } },
                { "imageUrl": None }
            ]
        }))

        if not articles_to_update:
            print("    - No articles found without images in this collection.")
            continue

        print(f"    - Found {len(articles_to_update)} articles to update.")
        
        # Process each article found
        for article in articles_to_update:
            article_id = article['_id']
            title = article.get('title', 'Untitled')
            style = details.get('style', 'photorealistic') # Use the style from our config

            print(f"        -> Processing article: '{title}' (ID: {article_id})")

            # 1. Generate the image
            image_url = generate_image_with_imagen(
                api_key=Config.GEMINI_API_KEY,
                title=title,
                style=style
            )

            if image_url:
                # 2. Update the document in the database
                articles_collection.update_one(
                    {'_id': article_id},
                    {'$set': {'imageUrl': image_url}}
                )
                print(f"        SUCCESS: Image added to article {article_id}.")
                total_updated += 1
            else:
                print(f"        FAILURE: Could not generate image for article {article_id}.")

            # Add a small delay to avoid hitting API rate limits too quickly
            time.sleep(2) 

    print(f"\n--- Script Finished ---")
    print(f"Total articles updated with a new image: {total_updated}")


if __name__ == '__main__':
    backfill_missing_images()
