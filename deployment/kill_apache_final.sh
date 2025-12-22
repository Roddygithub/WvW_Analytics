#!/bin/bash
# Arrêt définitif d'Apache et vérification Nginx

echo "=== Arrêt Définitif d'Apache ==="
echo ""

# Tuer tous les processus Apache
echo "1. Arrêt de tous les processus Apache..."
sudo pkill -9 apache2 2>/dev/null || true
sudo systemctl stop apache2 2>/dev/null || true
sudo systemctl disable apache2 2>/dev/null || true
sudo systemctl mask apache2 2>/dev/null || true

# Supprimer les paquets Apache
echo ""
echo "2. Désinstallation d'Apache..."
sudo apt-get remove -y apache2 apache2-bin apache2-data 2>/dev/null || true

echo ""
echo "3. Vérification des ports..."
echo "Processus écoutant sur le port 80:"
sudo netstat -tlnp | grep ':80' || echo "Aucun processus sur le port 80"

echo ""
echo "4. Redémarrage de Nginx..."
sudo systemctl restart nginx

sleep 2

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
fi

echo ""
echo "6. Test depuis l'extérieur..."
echo -n "   - IP publique: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://82.64.171.203)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ OK ($HTTP_CODE)"
else
    echo "✗ ERREUR ($HTTP_CODE)"
fi

echo ""
echo "=== Vérification Finale ==="
echo ""
echo "Processus sur le port 80:"
sudo netstat -tlnp | grep ':80'

echo ""
echo "Si Nginx écoute sur le port 80, votre site est accessible sur:"
echo "http://82.64.171.203"
