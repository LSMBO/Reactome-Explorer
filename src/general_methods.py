import requests
import time

def send_request(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

