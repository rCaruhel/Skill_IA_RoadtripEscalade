#!/usr/bin/env python3
import argparse
import json
import requests
import sys
import os

# Add parent directory to sys.path to import hotels
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from hotels.hotels import find_hotels
except ImportError:
    find_hotels = None

sys.stdout.reconfigure(encoding='utf-8')

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

def get_osrm_route(osrm_coords, overview="simplified"):
    coords_str = ";".join(osrm_coords)
    url = f"{OSRM_URL}{coords_str}?overview={overview}&geometries=geojson"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
            return data["routes"][0]
    except Exception:
        pass
    return None

def get_route(coords_list, auto_hotels=False, max_drive_hours=10):
    points = coords_list.strip().split()
    if len(points) < 2:
        return {"error": "At least 2 points are required."}
        
    osrm_coords = []
    
    for p in points:
        lat, lon = p.split(',')
        osrm_coords.append(f"{lon},{lat}") # OSRM needs lon,lat
        
    final_osrm_coords = []
    added_hotels = []
    
    # Process leg by leg to check for auto-hotels
    for i in range(len(osrm_coords) - 1):
        final_osrm_coords.append(osrm_coords[i])
        
        if auto_hotels and find_hotels is not None:
            leg_coords = [osrm_coords[i], osrm_coords[i+1]]
            leg_route = get_osrm_route(leg_coords, overview="full")
            
            if leg_route:
                leg_duration_hours = leg_route["duration"] / 3600.0
                if leg_duration_hours > max_drive_hours:
                    # Find midpoint along the route
                    geom = leg_route.get("geometry", {}).get("coordinates", [])
                    if geom:
                        mid_idx = len(geom) // 2
                        mid_lon, mid_lat = geom[mid_idx]
                        
                        # Find hotel near midpoint
                        hotels = find_hotels(mid_lat, mid_lon, radius=10000)
                        if isinstance(hotels, list) and len(hotels) > 0:
                            best_hotel = hotels[0]
                            added_hotels.append(best_hotel)
                            final_osrm_coords.append(f"{best_hotel['lon']},{best_hotel['lat']}")

    final_osrm_coords.append(osrm_coords[-1])
            
    # Final global route calculation
    route = get_osrm_route(final_osrm_coords, overview="false")
    if not route:
        return {"error": "Route not found"}
        
    distance_km = route["distance"] / 1000.0
    duration_min = route["duration"] / 60.0
    
    # Generate Google Maps Link
    gmaps_origin = final_osrm_coords[0].split(',')[1] + "," + final_osrm_coords[0].split(',')[0]
    gmaps_dest = final_osrm_coords[-1].split(',')[1] + "," + final_osrm_coords[-1].split(',')[0]
    
    gmaps_link = f"https://www.google.com/maps/dir/?api=1&origin={gmaps_origin}&destination={gmaps_dest}&travelmode=driving"
    
    gmaps_waypoints = []
    for coord in final_osrm_coords[1:-1]:
        lon, lat = coord.split(',')
        gmaps_waypoints.append(f"{lat},{lon}")
        
    if gmaps_waypoints:
        gmaps_link += f"&waypoints={'|'.join(gmaps_waypoints)}"
    
    result = {
        "distance_km": round(distance_km, 2),
        "duration_min": round(duration_min, 0),
        "maps_link": gmaps_link
    }
    
    if added_hotels:
        result["auto_added_hotels"] = added_hotels
        
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate multi-stop route with optional auto-hotels.")
    parser.add_argument("--coords", type=str, required=True, help='Space separated lat,lon e.g. "48.8,2.3 45.7,4.8"')
    parser.add_argument("--auto-hotels", action="store_true", help="Automatically add hotels for legs longer than max-drive-hours")
    parser.add_argument("--max-drive-hours", type=float, default=10.0, help="Max driving hours before requiring a hotel break")
    args = parser.parse_args()
    
    result = get_route(args.coords, args.auto_hotels, args.max_drive_hours)
    print(json.dumps(result, ensure_ascii=False))
