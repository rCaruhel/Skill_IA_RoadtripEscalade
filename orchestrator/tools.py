import os
import sys
from langchain_core.tools import tool

# Add project root to sys.path to import existing skills
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geocode.geocode import geocode as get_coordinates
from climbing_weather.weather import get_best_time_to_climb as get_weather
from hotels.hotels import find_hotels
from climbing_routing.routing import get_route
from climbing_spots.spots import find_climbing_spots

# On ajoute le sys.path pour healthcheck s'il n'y est pas déjà
import healthcheck.api_check as api_check

@tool
def outil_geocode(city: str) -> dict:
    """Traduit le nom d'une ville en coordonnées GPS (latitude et longitude).
    A appeler en premier pour trouver où se situe un spot.
    """
    return get_coordinates(city)

@tool
def outil_weather(lat: float, lon: float, is_indoor: bool = False) -> list:
    """Récupère les prévisions météo pour l'escalade à partir de coordonnées GPS.
    Renvoie une liste d'heures avec température et précipitations.
    Précise is_indoor=True si le spot est en intérieur.
    """
    return get_weather(lat, lon, is_indoor)

@tool
def outil_hotels(lat: float, lon: float, radius: int = 10000) -> list:
    """Cherche des hôtels ou auberges autour d'une position GPS.
    Renvoie le nom, la position et un prix estimé.
    """
    return find_hotels(lat, lon, radius)

@tool
def outil_routing(coords_str: str, auto_hotels: bool = True) -> dict:
    """Calcule le trajet routier. 
    L'argument coords_str doit être sous la forme EXACTE "lat1,lon1 lat2,lon2".
    Il ne doit contenir QUE des chiffres, des virgules et des espaces. PAS DE NOMS DE VILLES.
    Peut ajouter automatiquement des hôtels si auto_hotels est True.
    Renvoie la distance, la durée et un lien Google Maps.
    """
    try:
        return get_route(coords_str, auto_hotels=auto_hotels)
    except Exception as e:
        return {"error": f"Format de coordonnées invalide. Utilise 'lat,lon lat,lon'. Erreur: {e}"}

@tool
def outil_spots_par_ville(ville: str) -> list:
    """Cherche les meilleurs sites d'escalade autour d'une ville donnée.
    Renvoie une liste de spots avec leur nom et leurs coordonnées.
    """
    coords = get_coordinates(ville)
    if "error" in coords:
        return [{"error": f"Impossible de géocoder la ville {ville}."}]
    
    # 50km radius pour trouver des spots proches de la ville
    spots = find_climbing_spots(coords["lat"], coords["lon"], 50000)
    if isinstance(spots, list):
        return spots[:5]  # Limiter à 5 spots pour ne pas saturer la mémoire (context window) du petit LLM
    return spots

@tool
def outil_healthcheck() -> dict:
    """Vérifie l'état des serveurs et APIs externes (météo, routage, cartes).
    Si un utilisateur demande si les systèmes fonctionnent, utilise cet outil.
    Renvoie un dictionnaire avec le statut de chaque API ('OK' ou 'DOWN').
    """
    return api_check.check_apis()
