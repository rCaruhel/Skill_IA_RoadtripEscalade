#!/usr/bin/env python3
import requests
import json
import argparse

def check_apis():
    """Vérifie l'état des APIs externes utilisées par l'agent."""
    status = {}
    headers = {"User-Agent": "Skile_IA_Climbing_Agent/1.0"}

    # 1. Nominatim (Geocoding)
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search?q=Paris&format=json&limit=1", headers=headers, timeout=5)
        status["Nominatim"] = "OK" if r.status_code == 200 else f"ERROR ({r.status_code})"
    except Exception as e:
        status["Nominatim"] = f"DOWN ({str(e)})"

    # 2. Open-Meteo (Weather)
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=48&longitude=2&hourly=temperature_2m", timeout=5)
        status["Open-Meteo"] = "OK" if r.status_code == 200 else f"ERROR ({r.status_code})"
    except Exception as e:
        status["Open-Meteo"] = f"DOWN ({str(e)})"

    # 3. Overpass (Spots & Hotels)
    try:
        # Requête minimale rapide
        query = "[out:json][timeout:15];node(50.7,7.1,50.8,7.25)[amenity=cafe];out 1;"
        r = requests.post("http://overpass-api.de/api/interpreter", data={'data': query}, headers=headers, timeout=15)
        status["Overpass"] = "OK" if r.status_code == 200 else f"ERROR ({r.status_code})"
    except Exception as e:
        status["Overpass"] = f"DOWN ({str(e)})"

    # 4. OSRM (Routing)
    try:
        r = requests.get("http://router.project-osrm.org/route/v1/driving/2.3522,48.8566;2.3522,48.8566", timeout=5)
        status["OSRM"] = "OK" if r.status_code == 200 else f"ERROR ({r.status_code})"
    except Exception as e:
        status["OSRM"] = f"DOWN ({str(e)})"

    return status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Healthcheck des APIs de l'agent d'escalade.")
    args = parser.parse_args()
    
    result = check_apis()
    print(json.dumps(result, ensure_ascii=False, indent=2))
