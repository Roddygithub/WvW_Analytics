#!/bin/bash
# Script d'installation du service systemd et de la configuration Nginx
# À exécuter sur le serveur distant après deploy_app.sh

set -e

echo "=== Installation du service systemd ==="

# Copier le fichier de service
sudo cp ~/wvw-analytics/deployment/wvw-analytics.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer le service
sudo systemctl enable wvw-analytics.service
sudo systemctl start wvw-analytics.service

# Vérifier le statut
echo ""
echo "Statut du service:"
sudo systemctl status wvw-analytics.service --no-pager

echo ""
echo "=== Configuration de Nginx ==="

# Copier la configuration Nginx
sudo cp ~/wvw-analytics/deployment/nginx_wvw_analytics.conf /etc/nginx/sites-available/wvw-analytics

# Créer le lien symbolique
sudo ln -sf /etc/nginx/sites-available/wvw-analytics /etc/nginx/sites-enabled/

# Supprimer la configuration par défaut si elle existe
sudo rm -f /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx

echo ""
echo "=== Installation terminée ==="
echo ""
echo "Service WvW Analytics: ✓"
echo "Nginx configuré: ✓"
echo ""
echo "L'application est accessible sur: http://82.64.171.203"
echo ""
echo "Commandes utiles:"
echo "  sudo systemctl status wvw-analytics    # Voir le statut"
echo "  sudo systemctl restart wvw-analytics   # Redémarrer"
echo "  sudo journalctl -u wvw-analytics -f    # Voir les logs"
echo "  sudo tail -f /var/log/nginx/wvw_analytics_error.log  # Logs Nginx"
