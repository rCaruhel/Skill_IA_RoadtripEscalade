#!/usr/bin/env python3
import sys
import json
import argparse
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from _lib.llm import get_llm
from models import TripPlan, UserIntent
from tools import outil_geocode, outil_weather, outil_hotels, outil_routing, outil_spots_par_ville, outil_healthcheck

def interactive_agent():
    llm = get_llm(temperature=0)
    
    print("Bonjour ! D'où partez-vous et où souhaitez-vous aller pour votre road-trip d'escalade ? ( 'quit' pour quitter).")
    
    # --- PHASE 1 & 2 : Extraction et Arbre de Décision Python ---
    extractor = llm.with_structured_output(UserIntent)
    current_intent = UserIntent(depart=None, arrivee=None, etapes=[], wants_stops_asked=False, is_single_location=False, infos_complementaires="")
    
    last_agent_message = "D'où partez-vous et où souhaitez-vous aller pour votre road-trip d'escalade ?"
    
    while True:
        user_input = input("\nVous : ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Au revoir !")
            return
            
        print("(Analyse de votre demande...)")
        
        # On demande au LLM d'extraire la structure de la phrase en lui passant la dernière question
        extraction_prompt = (
            f"Dernière question posée par l'agent : '{last_agent_message}'\n"
            f"Réponse de l'utilisateur : '{user_input}'\n\n"
            "INSTRUCTIONS STRICTES :\n"
            "- Extrais les informations de voyage en fonction du contexte.\n"
            "- Si l'agent demandait d'où l'utilisateur part, place la réponse UNIQUEMENT dans 'depart'.\n"
            "- Si l'agent demandait la destination, place la réponse UNIQUEMENT dans 'arrivee'.\n"
            "- Si l'agent demandait quelles villes ajouter comme étapes, place la réponse UNIQUEMENT dans 'etapes'. Ne modifie PAS le 'depart' ou 'arrivee'.\n"
            "- Si l'agent demandait s'il y a des arrêts, place les arrêts dans 'etapes'. Si l'utilisateur dit non, laisse 'etapes' vide.\n"
            "- N'invente pas de lieux. Ne place JAMAIS de termes génériques ou abréviations (ex: 'spots', 'la montagne', 'oui', 'stp', 'svp', 'st', 'une entre les deux', 'arrêts', 'arrêts stp') dans le départ, l'arrivée ou les étapes.\n"
            "- Si l'utilisateur veut explicitement un roadtrip LOCAL autour d'une SEULE ville (ex: 'grimpe autour de Chamonix'), mets la ville dans 'arrivee' et 'is_single_location' à True."
        )
        extracted = extractor.invoke(extraction_prompt)
        
        # Mise à jour de l'état
        if extracted.depart: current_intent.depart = extracted.depart
        if extracted.arrivee: current_intent.arrivee = extracted.arrivee
        if extracted.etapes: 
            for e in extracted.etapes:
                if e not in current_intent.etapes:
                    current_intent.etapes.append(e)
        if extracted.is_single_location: current_intent.is_single_location = True
        if extracted.infos_complementaires: 
            current_intent.infos_complementaires += " " + extracted.infos_complementaires
            
        # Arbre de décision strict (Python)
        if current_intent.is_single_location and current_intent.arrivee:
            current_intent.depart = current_intent.arrivee  # Départ et arrivée identiques pour un roadtrip local
            print(f"Agent : D'accord, je vais organiser un roadtrip local autour de {current_intent.arrivee}.")
            break
        elif current_intent.depart and current_intent.arrivee:
            if not current_intent.wants_stops_asked and not current_intent.etapes:
                current_intent.wants_stops_asked = True
                last_agent_message = f"D'accord pour un voyage de {current_intent.depart} vers {current_intent.arrivee}. Souhaitez-vous faire des arrêts sur le chemin ou aller directement à destination ?"
                print(f"Agent : {last_agent_message}")
                continue
            else:
                if current_intent.etapes:
                    etapes_str = ", ".join(current_intent.etapes)
                    print(f"Agent : D'accord, je vais organiser votre voyage de {current_intent.depart} vers {current_intent.arrivee} en passant par {etapes_str}.")
                    break
                else:
                    # L'utilisateur a répondu affirmativement mais sans préciser de ville
                    mots_affirmatifs = ["oui", "veux", "bien sûr", "ouep", "yes", "volontiers", "arrêts", "stp", "svp", "s'il te plait"]
                    if any(mot in user_input.lower() for mot in mots_affirmatifs):
                        print(f"Agent : Recherche d'une ville sur la route entre {current_intent.depart} et {current_intent.arrivee}...")
                        from climbing_routing.routing import get_intermediate_cities
                        villes = get_intermediate_cities(current_intent.depart, current_intent.arrivee, max_drive_hours=10.0)
                        if villes:
                            current_intent.etapes.extend(villes)
                            villes_str = ", ".join(villes)
                            if len(villes) == 1:
                                print(f"Agent : D'accord, j'ai trouvé {villes_str} sur la route ! Je l'ajoute comme étape.")
                            else:
                                print(f"Agent : Le trajet est long ! J'ai ajouté {len(villes)} étapes pour limiter la conduite : {villes_str}.")
                            break
                        else:
                            print(f"Agent : Je n'ai pas pu trouver de ville intermédiaire par API. Je vais calculer le trajet directement.")
                            break
                    else:
                        print(f"Agent : D'accord, je vais organiser votre voyage de {current_intent.depart} vers {current_intent.arrivee} directement.")
                        break
        elif not current_intent.depart and not current_intent.arrivee:
            last_agent_message = "Il me manque vos points de départ et d'arrivée. D'où partez-vous et où allez-vous ?"
            print(f"Agent : {last_agent_message}")
        elif not current_intent.depart:
            last_agent_message = "Il me manque votre point de départ. D'où partez-vous ?"
            print(f"Agent : {last_agent_message}")
        elif not current_intent.arrivee:
            last_agent_message = "Il me manque votre destination. Où allez-vous ?"
            print(f"Agent : {last_agent_message}")

    # --- PHASE 3 : Exécution ---
    print("\nVérification des villes et génération du plan de route...")
    
    # Vérification préventive des lieux pour bloquer les faux appels API météo
    villes_a_verifier = [current_intent.depart] + current_intent.etapes + [current_intent.arrivee]
    villes_en_erreur = []
    
    from geocode.geocode import geocode as get_coordinates
    for v in villes_a_verifier:
        if v and v not in villes_en_erreur:
            res = get_coordinates(v)
            if "error" in res:
                villes_en_erreur.append(v)
                
    if villes_en_erreur:
        erreurs_str = ", ".join(villes_en_erreur)
        system_prompt = (
            f"Tu es un agent expert en organisation de road-trips. "
            f"ATTENTION: L'outil de géolocalisation indique que les lieux suivants n'existent pas ou sont introuvables : {erreurs_str}. "
            f"Il t'est STRICTEMENT INTERDIT d'appeler l'outil météo, l'outil routing, ou de chercher des hôtels pour ces lieux. "
            f"Contente-toi de résumer la situation à l'utilisateur en expliquant que ces lieux sont introuvables et demande s'il a fait une faute de frappe."
        )
    else:
        system_prompt = (
            "Tu es un agent planificateur de road-trips. "
            "POUR ACCOMPLIR TA MISSION, TU DOIS APPELER LES OUTILS SUIVANTS : "
            "1. 'outil_healthcheck' en premier. "
            "2. 'outil_routing' pour obtenir la distance et le trajet exact. "
            "3. 'outil_spots_par_ville' sur les villes pour trouver des spots d'escalade réels. "
            "Ne génère ton résumé final qu'APRÈS avoir appelé ces outils. "
            "N'invente aucune donnée (pas de faux kilométrages, pas de fausses météos, pas de faux spots). "
            "Si un outil échoue ou renvoie une erreur, mentionne l'erreur et arrête-toi sans inventer de trajet de remplacement."
        )
    
    outils = [outil_geocode, outil_weather, outil_hotels, outil_routing, outil_spots_par_ville, outil_healthcheck]
    
    agent = create_agent(
        model=llm,
        tools=outils,
        system_prompt=system_prompt
    )
    
    prompt_final = f"MISSION OBLIGATOIRE : Organise un voyage partant EXACTEMENT de {current_intent.depart} et se terminant EXACTEMENT à {current_intent.arrivee}."
    if current_intent.etapes:
        prompt_final += f" Passe OBLIGATOIREMENT par les étapes suivantes : {', '.join(current_intent.etapes)}."
    if current_intent.infos_complementaires:
        prompt_final += f" Instructions spéciales : {current_intent.infos_complementaires}"
    
    resultat = agent.invoke({"messages": [HumanMessage(content=prompt_final)]})
    reponse_texte = resultat["messages"][-1].content
    
    print(f"\nAgent (Résumé) : {reponse_texte}")
    
    print("\nL'agent a toutes les infos ! Génération du JSON Pydantic structuré...")
    try:
        from json import loads
        # On demande au modèle de nous retourner l'objet Pydantic final
        prompt_extraction = f"À partir de ce résumé de voyage, remplis le JSON structuré complet. EXTRAIS SOIGNEUSEMENT la liste des spots d'escalade dans 'spots_escalade' (inclus toutes les infos supplémentaires type indoor/outdoor, coordonnées). N'oublie pas d'extraire le 'lien_google_maps'. Résumé:\n{reponse_texte}"
        # On utilise une instance d'extracteur dédiée
        extracteur_final = llm.with_structured_output(TripPlan)
        plan = extracteur_final.invoke(prompt_extraction)
        
        # --- PHASE 4 : Présentation conviviale (Natural Language Generation) ---
        print("\n(Rédaction du guide de voyage...)")
        presentation_prompt = (
            "Voici les données JSON validées d'un road-trip d'escalade :\n"
            f"{plan.model_dump_json()}\n\n"
            "Rédige une réponse professionnelle, factuelle et sérieuse pour présenter ce programme à l'utilisateur. "
            "Structure bien ta réponse : \n"
            "1. L'itinéraire (départ, étapes, arrivée, temps de trajet), EN INCLUANT obligatoirement le lien de trajet Google Maps.\n"
            "2. La météo détaillée.\n"
            "3. Les spots d'escalade trouvés : liste-les AVEC TOUTES LES INFORMATIONS SUPPLÉMENTAIRES disponibles (coordonnées, type indoor/outdoor, etc.). Si aucun spot, dis-le.\n"
            "4. Les recommandations d'hôtels.\n"
            "CONSIGNES STRICTES : \n"
            "- NE PARLE SOUS AUCUN PRETEXTE DES APIs NI DE LEUR SANTE. Le bilan technique est réservé à un usage interne.\n"
            "- S'il n'y a pas de spots d'escalade dans le JSON, dis EXACTEMENT que tu n'en as pas trouvé. N'invente AUCUNE information.\n"
            "- NE METS AUCUN EMOJI DANS TON TEXTE. C'EST STRICTEMENT INTERDIT.\n"
            "- N'invente aucune donnée pour satisfaire le client. Reste 100% factuel par rapport au JSON.\n"
            "Ne montre pas de JSON, adresse-toi directement à l'utilisateur comme un guide professionnel."
        )
        # On appelle le LLM pour faire la traduction du JSON en un beau texte
        presentation_response = llm.invoke([HumanMessage(content=presentation_prompt)])
        
        print("\n\n" + "="*50)
        print("VOTRE ROAD-TRIP ESCALADE EST PRÊT")
        print("="*50 + "\n")
        print(presentation_response.content)
        
    except Exception as e:
        print("\nErreur lors de la génération du plan structuré :", e)

if __name__ == "__main__":
    interactive_agent()
