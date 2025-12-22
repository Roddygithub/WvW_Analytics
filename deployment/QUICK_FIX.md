# Fix Rapide - Conflit Nginx

Le problème est simple : l'ancienne configuration `gw2-counterpicker` interfère avec `wvw-analytics`.

## Solution en 3 commandes

Connectez-vous au serveur et exécutez :

```bash
# 1. Supprimer l'ancienne configuration
sudo rm -f /etc/nginx/sites-enabled/gw2-counterpicker
sudo rm -f /etc/nginx/sites-available/gw2-counterpicker

# 2. Recharger Nginx
sudo systemctl reload nginx

# 3. Tester
curl http://localhost
```

Vous devriez voir le HTML de la page d'accueil WvW Analytics !

## Accès à l'application

Une fois corrigé, l'application sera accessible sur :
**http://82.64.171.203**
