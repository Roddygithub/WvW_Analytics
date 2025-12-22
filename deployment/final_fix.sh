#!/bin/bash
# Script final de correction - À exécuter DIRECTEMENT sur le serveur

echo "=== Correction Finale WvW Analytics ==="

# 1. Nettoyage complet gw2-counterpicker (sans sudo)
echo ""
echo "1. Nettoyage des fichiers utilisateur gw2..."
rm -rf ~/gw2-counterpicker
rm -f ~/gw2opt-deploy.tar.gz
rm -f ~/deploy_*.sh
rm -f ~/fix_apache_and_start.sh
find ~ -maxdepth 1 -name "*gw2*" -type f -delete 2>/dev/null || true
echo "   ✓ Fichiers utilisateur nettoyés"

# 2. Nettoyage avec sudo (vous devrez entrer le mot de passe)
echo ""
echo "2. Nettoyage des configurations système (mot de passe requis)..."
sudo systemctl stop gw2-counterpicker.service 2>/dev/null || true
sudo systemctl disable gw2-counterpicker.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/gw2-counterpicker.service
sudo systemctl daemon-reload
sudo rm -f /etc/nginx/sites-enabled/gw2-counterpicker
sudo rm -f /etc/nginx/sites-available/gw2-counterpicker
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -rf /root/gw2optimizer
echo "   ✓ Configurations système nettoyées"

# 3. Vérifier la configuration Nginx
echo ""
echo "3. Configuration Nginx..."
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
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ OK ($HTTP_CODE)"
else
    echo "✗ ERREUR ($HTTP_CODE)"
fi

echo -n "   - Nginx (port 80): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ OK ($HTTP_CODE)"
else
    echo "✗ ERREUR ($HTTP_CODE)"
    echo ""
    echo "Diagnostic Nginx:"
    sudo tail -5 /var/log/nginx/error.log
fi

# 6. Configuration du déploiement automatique
echo ""
echo "6. Configuration du déploiement automatique..."

cat > ~/wvw-analytics/deployment/auto_deploy.sh << 'DEPLOYEOF'
#!/bin/bash
# Script de déploiement automatique

cd ~/wvw-analytics
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
deactivate
sudo systemctl restart wvw-analytics
echo "✓ Déploiement automatique terminé à $(date)"
DEPLOYEOF

chmod +x ~/wvw-analytics/deployment/auto_deploy.sh

# Hook post-merge
mkdir -p ~/wvw-analytics/.git/hooks
cat > ~/wvw-analytics/.git/hooks/post-merge << 'HOOKEOF'
#!/bin/bash
echo "Déploiement automatique déclenché..."
~/wvw-analytics/deployment/auto_deploy.sh
HOOKEOF
chmod +x ~/wvw-analytics/.git/hooks/post-merge

echo "   ✓ Déploiement automatique configuré"

# Résumé final
echo ""
echo "=== Configuration Terminée ==="
echo ""
echo "Application accessible sur: http://82.64.171.203"
echo ""
echo "Pour mettre à jour depuis votre machine locale:"
echo "  git push origin main"
echo "  ssh syff@82.64.171.203 -p 2222 'cd ~/wvw-analytics && git pull && ~/wvw-analytics/deployment/auto_deploy.sh'"
echo ""
