---
name: climbing_routing
description: Calcule la distance, le temps de trajet en voiture et renvoie un lien GPS. Trigger when user asks "comment y aller", "trajet pour", "distance jusqu'à".
allowed-tools: Bash(python3 *)
---

# Skill `climbing_routing`

Pour calculer l'itinéraire entre plusieurs étapes (road-trip) :

```bash
python3 ${CLAUDE_SKILL_DIR}/routing.py --coords "lat1,lon1 lat2,lon2 lat3,lon3" [--auto-hotels] [--max-drive-hours 10.0]
```

Renvoie du JSON contenant la distance, le temps de trajet et un lien Google Maps. 
Si `--auto-hotels` est utilisé, le script insérera automatiquement des hôtels trouvés sur la route pour les étapes dépassant `max-drive-hours`, et les inclura dans le trajet.
