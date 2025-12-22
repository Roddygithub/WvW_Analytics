#!/bin/bash
# Script de correction Nginx pour WvW Analytics

echo "=== Diagnostic et correction Nginx ==="

# Vérifier que l'app tourne sur le port 8000
echo "1. Vérification du port 8000..."
netstat -tlnp 2>/dev/null | grep 8000 || ss -tlnp | grep 8000

# Vérifier les logs Nginx
echo ""
echo "2. Logs d'erreur Nginx (20 dernières lignes):"
sudo tail -20 /var/log/nginx/wvw_analytics_error.log 2>/dev/null || echo "Pas de logs d'erreur"

# Vérifier la configuration Nginx
echo ""
echo "3. Test de la configuration Nginx:"
sudo nginx -t

# Vérifier que le site est activé
echo ""
echo "4. Sites Nginx activés:"
ls -la /etc/nginx/sites-enabled/

# Tester la connexion directe
echo ""
echo "5. Test connexion directe au backend:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://127.0.0.1:8000

# Recharger Nginx
echo ""
echo "6. Rechargement de Nginx..."
sudo systemctl reload nginx

# Test final
echo ""
echo "7. Test final via Nginx:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost

echo ""
echo "=== Diagnostic terminé ==="
