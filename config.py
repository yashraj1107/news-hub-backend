# config.py
import os
from dotenv import load_dotenv

# This code robustly finds and loads your .env file.
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    raise FileNotFoundError("ERROR: The '.env' file was not found.")

class Config:
    """
    Configuration class to hold all the settings and API keys.
    This securely loads keys from your .env file.
    """
    GUARDIAN_API_KEY = os.getenv('GUARDIAN_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

    # This check ensures that the keys were found in your .env file.
    if not GUARDIAN_API_KEY:
        raise ValueError("GUARDIAN_API_KEY not found in .env file.")
        
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    if not MONGO_CONNECTION_STRING:
        raise ValueError("MONGO_CONNECTION_STRING not found in .env file.")

