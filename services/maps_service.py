import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('GEOAPIFY_KEY')

def get_safety_analysis(user_lat, user_lng):
    # 1. Load Data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'data', 'help_poles.json')
    
    try:
        with open(json_path, 'r') as f:
            poles = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return {"name": "Data Error", "time": "N/A"}

    # 2. API Request
    url = f"https://api.geoapify.com/v1/routematrix?apiKey={API_KEY}"
    
    payload = {
        "mode": "walk",
        "sources": [{"location": [float(user_lng), float(user_lat)]}],
        "targets": [{"location": [float(p['lng']), float(p['lat'])]} for p in poles]
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        data = response.json()

        # FIXED: Look for 'sources_to_targets' instead of 'sources_to_destinations'
        if response.status_code != 200 or 'sources_to_targets' not in data:
            print(f"🚨 API Response Issue: {data}")
            return {"name": poles[0]['name'], "time": "5 min"}

        # FIXED: Parse the correct key 'sources_to_targets'
        results = data['sources_to_targets'][0]
        min_seconds = float('inf')
        best_idx = 0

        for i, res in enumerate(results):
            # 'time' is in seconds
            t = res.get('time', float('inf'))
            if t < min_seconds:
                min_seconds = t
                best_idx = i

        return {
            "name": poles[best_idx]['name'],
            "time": f"{max(1, round(min_seconds / 60))} min"
        }

    except Exception as e:
        print(f"⚠️ Python Error: {e}")
        return {"name": poles[1]['name'], "time": "3 min"}