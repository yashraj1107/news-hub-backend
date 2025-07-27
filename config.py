# config.py
import os
from dotenv import load_dotenv

# --- UPDATED for Production ---
# This code looks for a .env file for local development, but does not
# raise an error if it's not found (which is the case on a server like Render).
print("Loading configuration...")
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print("Found .env file, loading for local development.")
    load_dotenv(dotenv_path=dotenv_path)

class Config:
    """
    This class now reads variables either from the local .env file
    or from the environment variables set in the Render dashboard.
    """
    GUARDIAN_API_KEY = os.getenv('GUARDIAN_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
    GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # These checks are still important. They will now cause a deploy to fail
    # if you forget to set a variable in the Render dashboard.
    if not GUARDIAN_API_KEY: raise ValueError("FATAL ERROR: GUARDIAN_API_KEY is not set in the environment.")
    if not GEMINI_API_KEY: raise ValueError("FATAL ERROR: GEMINI_API_KEY is not set in the environment.")
    if not MONGO_CONNECTION_STRING: raise ValueError("FATAL ERROR: MONGO_CONNECTION_STRING is not set in the environment.")
    if not GOOGLE_PROJECT_ID: raise ValueError("FATAL ERROR: GOOGLE_PROJECT_ID is not set in the environment.")
    if not GOOGLE_APPLICATION_CREDENTIALS: raise ValueError("FATAL ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in the environment.")

print("Configuration loaded successfully.")
