# empty_collections.py
# A one-time script to delete all articles from all category collections.

from config import Config
from services import (
    get_db_connection,
    CATEGORIES,
    get_collection_name
)

def delete_all_articles():
    """
    Connects to the database and deletes all documents from each
    category collection.
    """
    print("--- DANGER: This script will delete all articles from the database. ---")
    
    # Confirmation step to prevent accidental deletion
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborting script. No data has been deleted.")
        return

    # Establish database connection
    db = get_db_connection(Config.MONGO_CONNECTION_STRING)
    if db is None:
        print("!!! Could not connect to the database. Aborting script. !!!")
        return

    total_deleted_count = 0

    # Loop through each defined category
    for category_name in CATEGORIES.keys():
        collection_name = get_collection_name(category_name)
        articles_collection = db[collection_name]
        
        print(f"\n>>> Checking collection: '{collection_name}'...")

        # The delete_many({}) command with an empty filter deletes all documents
        # in the collection.
        result = articles_collection.delete_many({})
        
        deleted_count = result.deleted_count
        total_deleted_count += deleted_count
        
        print(f"    - Deleted {deleted_count} articles from this collection.")

    print(f"\n--- Script Finished ---")
    print(f"Total articles deleted from all collections: {total_deleted_count}")
    print("Your database is now empty. You can run scheduler.py to start fresh.")


if __name__ == '__main__':
    delete_all_articles()
