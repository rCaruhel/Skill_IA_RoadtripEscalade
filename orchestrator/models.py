from pydantic import BaseModel, Field
from typing import Literal, Optional

class TripPlan(BaseModel):
    """Planification structurée d'un voyage d'escalade."""
    destination: str = Field(description="Nom complet de la destination d'escalade.")
    distance_totale_km: float = Field(description="Distance totale calculée pour le trajet en kilomètres.")
    duree_trajet_minutes: int = Field(description="Durée estimée du trajet de bout en bout en minutes.")
    hotels_recommandes: list[str] = Field(description="Liste des noms des hôtels recommandés (si disponibles).")
    budget_hotels_eur: int = Field(description="Budget total estimé pour les hôtels en euros.")
    meteo_prevue: Literal["parfaite", "moyenne", "mauvaise"] = Field(description="Évaluation globale de la météo pour l'escalade.")
    meteo_details: str = Field(default="Aucun détail.", description="Description détaillée de la météo (température, vent, précipitations) récupérée via l'outil.")
    api_health: str = Field(default="Inconnu", description="Statut de santé des APIs récupéré via l'outil healthcheck (ex: 'OK' ou 'Erreur sur API Météo').")
    spots_escalade: list[str] = Field(default_factory=list, description="Liste détaillée des spots d'escalade trouvés (noms, indoor/outdoor, lieux).")
    resume_gps: str = Field(description="Un court résumé décrivant le trajet généré par OSRM et Google Maps.")
    lien_google_maps: str = Field(default="Aucun lien trouvé.", description="Lien Google Maps de l'itinéraire calculé.")

class UserIntent(BaseModel):
    """Extraction structurée de la requête utilisateur."""
    depart: Optional[str] = Field(description="Le lieu de départ du voyage, s'il est mentionné. Si non mentionné, null.")
    arrivee: Optional[str] = Field(description="Le lieu d'arrivée ou pays cible du voyage, s'il est mentionné. Si non mentionné, null.")
    etapes: list[str] = Field(default_factory=list, description="Liste des arrêts intermédiaires mentionnés par l'utilisateur.")
    wants_stops_asked: bool = Field(default=False, description="Vrai si on a déjà demandé à l'utilisateur s'il voulait faire des arrêts.")
    is_single_location: bool = Field(description="Vrai si l'utilisateur ne donne qu'un seul lieu et souhaite chercher des spots autour de ce lieu sans faire un long trajet A vers B.")
    infos_complementaires: str = Field(description="Toute information supplémentaire (ex: besoin d'hôtels, etc).")
