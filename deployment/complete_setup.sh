#!/bin/bash
# Configuration complète du serveur WvW Analytics

set -e

echo "=== Configuration Complète du Serveur ==="

# 1. Nettoyage complet de gw2-counterpicker
echo ""
echo "1. Nettoyage complet de gw2-counterpicker..."

# Arrêter tous les services gw2
sudo systemctl stop gw2-counterpicker.service 2>/dev/null || true
sudo systemctl disable gw2-counterpicker.service 2>/dev/null || true

# Supprimer les fichiers de service
sudo rm -f /etc/systemd/system/gw2-counterpicker.service
sudo systemctl daemon-reload

# Supprimer les configurations Nginx
sudo rm -f /etc/nginx/sites-enabled/gw2-counterpicker
sudo rm -f /etc/nginx/sites-available/gw2-counterpicker

# Supprimer les dossiers
rm -rf ~/gw2-counterpicker
sudo rm -rf /root/gw2optimizer

# Supprimer les fichiers temporaires
rm -f ~/gw2opt-deploy.tar.gz
rm -f ~/deploy_*.sh
rm -f ~/fix_apache_and_start.sh

# Rechercher et supprimer tout ce qui contient gw2
find ~ -maxdepth 1 -name "*gw2*" -type f -delete 2>/dev/null || true

echo "   ✓ Nettoyage gw2-counterpicker terminé"

# 2. Configuration sudo sans mot de passe pour les commandes de déploiement
echo ""
echo "2. Configuration sudo sans mot de passe..."

sudo tee /etc/sudoers.d/wvw-analytics > /dev/null << 'SUDOEOF'
# WvW Analytics deployment commands
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl start wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl status wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl daemon-reload
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload nginx
syff ALL=(ALL) NOPASSWD: /usr/bin/nginx -t
syff ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u wvw-analytics *
syff ALL=(ALL) NOPASSWD: /usr/bin/cp /home/syff/wvw-analytics/deployment/wvw-analytics.service /etc/systemd/system/
syff ALL=(ALL) NOPASSWD: /usr/bin/cp /home/syff/wvw-analytics/deployment/nginx_wvw_analytics.conf /etc/nginx/sites-available/wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/ln -sf /etc/nginx/sites-available/wvw-analytics /etc/nginx/sites-enabled/
syff ALL=(ALL) NOPASSWD: /usr/bin/rm -f /etc/nginx/sites-enabled/default
SUDOEOF

sudo chmod 440 /etc/sudoers.d/wvw-analytics

echo "   ✓ Sudo sans mot de passe configuré"

# 3. Vérifier la configuration Nginx
echo ""
echo "3. Vérification de la configuration Nginx..."

# S'assurer que seul wvw-analytics est activé
sudo rm -f /etc/nginx/sites-enabled/default

# Tester la configuration
sudo nginx -t

echo "   ✓ Configuration Nginx valide"

# 4. Redémarrer les services
echo ""
echo "4. Redémarrage des services..."

sudo systemctl restart wvw-analytics
sleep 3
sudo systemctl reload nginx

echo "   ✓ Services redémarrés"

# 5. Tests
echo ""
echo "5. Tests de fonctionnement..."

echo -n "   - Port 8000: "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000 | grep -q "200"; then
    echo "✓ OK"
else
    echo "✗ ERREUR"
fi

echo -n "   - Nginx (port 80): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    echo "✓ OK"
else
    echo "✗ ERREUR"
fi

# 6. Configuration du déploiement automatique
echo ""
echo "6. Configuration du déploiement automatique..."

# Créer le script de déploiement automatique
cat > ~/wvw-analytics/deployment/auto_deploy.sh << 'DEPLOYEOF'
#!/bin/bash
# Script de déploiement automatique

cd ~/wvw-analytics

# Pull les dernières modifications
git pull origin main

# Activer l'environnement virtuel et mettre à jour les dépendances
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate

# Redémarrer le service
sudo systemctl restart wvw-analytics

echo "Déploiement automatique terminé à $(date)"
DEPLOYEOF

chmod +x ~/wvw-analytics/deployment/auto_deploy.sh

# Créer un hook post-receive (pour déploiement via git push)
mkdir -p ~/wvw-analytics/.git/hooks

cat > ~/wvw-analytics/.git/hooks/post-merge << 'HOOKEOF'
#!/bin/bash
# Hook exécuté après un git pull

echo "Déploiement automatique déclenché..."
~/wvw-analytics/deployment/auto_deploy.sh
HOOKEOF

chmod +x ~/wvw-analytics/.git/hooks/post-merge

echo "   ✓ Déploiement automatique configuré"

# 7. Résumé
echo ""
echo "=== Configuration Terminée ==="
echo ""
echo "✓ gw2-counterpicker complètement supprimé"
echo "✓ Sudo sans mot de passe configuré pour les commandes de déploiement"
echo "✓ Déploiement automatique configuré"
echo "✓ Services redémarrés"
echo ""
echo "Application accessible sur: http://82.64.171.203"
echo ""
echo "Pour mettre à jour l'application depuis votre machine locale:"
echo "  cd ~/WvW_Analytics"
echo "  git push origin main"
echo "  ssh syff@82.64.171.203 -p 2222 'cd ~/wvw-analytics && git pull && ~/wvw-analytics/deployment/auto_deploy.sh'"
echo ""
