# scheduler.py
import requests

def trigger_article_generation():
    """
    Sends a POST request to the local Flask server to start the generation process.
    In a real-world scenario, a cloud service (like Google Cloud Scheduler or a cron job)
    would run this script periodically.
    """
    api_url = "https://api.news.lurnetreau.com/api/v1/generate-and-save"
    print(f"Sending request to trigger article generation at {api_url}...")
    
    try:
        response = requests.post(api_url, timeout=300) # 5 minute timeout for the whole process
        response.raise_for_status()
        print("Successfully triggered generation process.")
        print("Response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Failed to trigger generation process: {e}")

if __name__ == "__main__":
    trigger_article_generation()

