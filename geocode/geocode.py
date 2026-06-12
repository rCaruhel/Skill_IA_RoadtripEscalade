#!/usr/bin/env python3
import argparse
import json
import requests
import sys

def geocode(city_name: str):
    """Simple geocoder using Nominatim (OpenStreetMap)"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "Skile_IA_Climbing_Agent/1.0"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            return {"city": city_name, "lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
        else:
            return {"error": "City not found"}
    except Exception as e:
        return {"error": str(e)}

def reverse_geocode(lat: float, lon: float):
    """Trouve la ville correspondant à des coordonnées GPS via Nominatim."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "Skile_IA_Climbing_Agent/1.0"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "address" in data:
            addr = data["address"]
            # Cherche la ville, le village ou le bourg
            city = addr.get("city", addr.get("town", addr.get("village", addr.get("municipality"))))
            if city:
                return {"city": city, "lat": lat, "lon": lon}
            else:
                return {"error": "No city found at these coordinates"}
        else:
            return {"error": "No address found"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geocode a city name to coordinates.")
    parser.add_argument("--city", required=True, help="Name of the city to geocode")
    args = parser.parse_args()
    
    result = geocode(args.city)
    print(json.dumps(result, ensure_ascii=False))
