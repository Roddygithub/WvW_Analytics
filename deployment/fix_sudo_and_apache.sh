#!/bin/bash
# Configuration complète sudo + arrêt Apache

echo "=== Configuration Sudo Sans Mot de Passe + Arrêt Apache ==="
echo ""
echo "Vous devrez entrer votre mot de passe UNE DERNIÈRE FOIS."
echo ""

# Configuration sudo complète
sudo tee /etc/sudoers.d/wvw-analytics > /dev/null << 'SUDOEOF'
# WvW Analytics - Commandes sans mot de passe
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl *
syff ALL=(ALL) NOPASSWD: /usr/bin/nginx *
syff ALL=(ALL) NOPASSWD: /usr/bin/journalctl *
syff ALL=(ALL) NOPASSWD: /usr/bin/cp *
syff ALL=(ALL) NOPASSWD: /usr/bin/ln *
syff ALL=(ALL) NOPASSWD: /usr/bin/rm *
syff ALL=(ALL) NOPASSWD: /usr/bin/tee *
syff ALL=(ALL) NOPASSWD: /usr/bin/tail *
syff ALL=(ALL) NOPASSWD: /usr/bin/sed *
syff ALL=(ALL) NOPASSWD: /usr/bin/netstat *
syff ALL=(ALL) NOPASSWD: /usr/bin/ss *
syff ALL=(ALL) NOPASSWD: /usr/sbin/apache2ctl *
SUDOEOF

sudo chmod 440 /etc/sudoers.d/wvw-analytics

echo "✓ Sudo sans mot de passe configuré"
echo ""

# Arrêter Apache complètement
echo "Arrêt d'Apache..."
sudo systemctl stop apache2 2>/dev/null || true
sudo systemctl disable apache2 2>/dev/null || true
sudo systemctl mask apache2 2>/dev/null || true
sudo pkill -9 apache2 2>/dev/null || true

echo "✓ Apache arrêté"
echo ""

# Redémarrer Nginx
echo "Redémarrage de Nginx..."
sudo systemctl restart nginx

echo "✓ Nginx redémarré"
echo ""

# Tests
echo "Tests de fonctionnement..."
sleep 2

echo -n "  - Port 8000: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ OK ($HTTP_CODE)"
else
    echo "✗ ERREUR ($HTTP_CODE)"
fi

echo -n "  - Nginx (port 80): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ OK ($HTTP_CODE)"
else
    echo "✗ ERREUR ($HTTP_CODE)"
fi

echo ""
echo "=== Configuration Terminée ==="
echo ""
echo "Application accessible sur: http://82.64.171.203"
echo ""
echo "Testez maintenant: http://82.64.171.203/analyze"
