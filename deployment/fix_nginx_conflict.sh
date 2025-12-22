#!/bin/bash
# Script de correction du conflit Nginx

echo "=== Correction du conflit Nginx ==="

# Supprimer l'ancienne configuration gw2-counterpicker
echo "1. Suppression de l'ancienne configuration gw2-counterpicker..."
echo "syff" | sudo -S rm -f /etc/nginx/sites-enabled/gw2-counterpicker
echo "syff" | sudo -S rm -f /etc/nginx/sites-available/gw2-counterpicker

# Vérifier la configuration
echo ""
echo "2. Test de la configuration Nginx..."
echo "syff" | sudo -S nginx -t

# Recharger Nginx
echo ""
echo "3. Rechargement de Nginx..."
echo "syff" | sudo -S systemctl reload nginx

# Attendre un peu
sleep 2

# Test final
echo ""
echo "4. Test final:"
echo "   - Port 8000 direct:"
curl -s -o /dev/null -w "     Status: %{http_code}\n" http://127.0.0.1:8000

echo "   - Via Nginx (port 80):"
curl -s -o /dev/null -w "     Status: %{http_code}\n" http://localhost

echo ""
echo "=== Correction terminée ==="
echo ""
echo "Si le statut est 200, l'application est accessible sur:"
echo "http://82.64.171.203"
