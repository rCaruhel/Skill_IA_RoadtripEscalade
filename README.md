# Organisateur de Road-Trips d'Escalade (Agent IA)

Ce projet est un assistant intelligent basé sur un LLM, conçu pour planifier de bout en bout des road-trips d'escalade. Il interprète vos demandes en langage naturel, gère l'ajout d'arrêts intermédiaires, calcule les itinéraires de route, trouve des hôtels, vérifie la météo et cherche les spots d'escalade autour de vos destinations.

L'objectif principal est de transformer une phrase en langage naturel (ex: "Je veux aller de Paris à Berlin en passant par Strasbourg") en un plan de route Pydantic structuré et validé via diverses APIs géospatiales.

---

## Architecture et Structure des Agents

Le système repose sur une architecture en 3 phases, combinant un contrôle strict en Python et la flexibilité d'un agent Langchain.

### Phase 1 : L'Extracteur d'Intention
- Fichier clé : orchestrator/models.py
- L'utilisateur interagit via la console. Son entrée texte est analysée par un LLM contraint pour correspondre au modèle Pydantic UserIntent. 
- Le système extrait les points de départ, d'arrivée, les étapes, et le besoin d'hôtels.
- Si le voyage est incomplet, le script Python pose des questions interactives ("Voulez-vous faire des arrêts ?").

### Phase 2 : Validation et Arbre de Décision Python
- Fichier clé : orchestrator/agent.py
- Le script Python effectue des vérifications :
  1. Il vérifie si les villes demandées existent réellement à l'aide de l'outil de géocodage.
  2. Si l'utilisateur mentionne une ville introuvable, le système détecte l'erreur avant d'aller plus loin.
  3. L'agent Langchain final reçoit alors l'instruction de ne pas requêter les APIs de météo ou de routes pour les villes inexistantes, afin d'économiser du temps et des ressources.

### Phase 3 : L'Agent Langchain ReAct
- Fichiers clés : orchestrator/agent.py, orchestrator/tools.py
- Une fois les villes validées, un agent Langchain prend le relais avec plusieurs outils :
  - outil_routing : Calcule la distance, la durée et génère le lien Google Maps via OSRM.
  - outil_weather : Vérifie la météo locale.
  - outil_hotels : Récupère des recommandations d'hébergement.
  - outil_spots_par_ville : Recherche des spots d'escalade.
- Le LLM utilise de façon autonome ces outils pour combler son manque de données en temps réel, fournit un résumé textuel, et remplit un objet JSON structuré (TripPlan).

---

## Installation et Configuration

### Prérequis
- Python 3.10 ou supérieur.
- Ollama installé localement.

### Dépendances Python
Installez les librairies requises :
```bash
pip install -r requirements.txt
```

### Configuration LLM (.env)

Le projet est nativement configuré pour fonctionner avec un modèle local (Ollama). **Il a été testé et validé avec la version Ollama 0.30.7.**

Toutefois, le système a été conçu pour être facilement modifiable afin de supporter d'autres modèles LLM commerciaux via des clés API.

1. Si vous utilisez Ollama en local, téléchargez le modèle Llama 3.1 :
```bash
ollama run llama3.1
```

2. Créez un fichier `.env` à la racine de votre projet avec la structure suivante pour configurer votre LLM :

```env
# Choisissez le backend LLM : ollama, mistral, gemini, openai, ou anthropic
LLM_BACKEND=ollama

# Si vous avez choisi "ollama", indiquez le modèle cible (par défaut llama3.1)
OLLAMA_MODEL=llama3.1

# ---------------------------------------------------------
# Si vous avez choisi un autre backend, renseignez la clé API correspondante :
# (Décommentez la ligne de votre choix)
# MISTRAL_API_KEY=votre_cle_mistral
# GOOGLE_API_KEY=votre_cle_gemini
# OPENAI_API_KEY=votre_cle_openai
# ANTHROPIC_API_KEY=votre_cle_anthropic
```

En modifiant `LLM_BACKEND` (par exemple vers `gemini` ou `openai`) et en fournissant la clé API associée, l'assistant utilisera automatiquement ce modèle en ligne à la place du modèle local.

---

## Comment utiliser le projet

Pour lancer l'assistant interactif, exécutez le script suivant :

```bash
python orchestrator/agent.py
```

Le programme démarrera et vous posera des questions. Vous pouvez indiquer un trajet direct ou un point de chute unique. Le système vous proposera d'ajouter des étapes sur la route.
Une fois les informations confirmées, l'agent se mettra au travail, appellera les outils nécessaires et vous résumera l'itinéraire calculé.

Tapez "quit" ou "exit" à n'importe quel moment pour quitter le programme.
