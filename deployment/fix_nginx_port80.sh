#!/bin/bash
# Script pour configurer Nginx sur le port 80 pour WvW Analytics
# À exécuter sur le serveur distant: ssh syff@82.64.171.203 -p 2222

set -e

echo "=== Configuration Nginx pour WvW Analytics sur port 80 ==="

# Créer la nouvelle configuration
sudo tee /etc/nginx/sites-available/wvw-analytics > /dev/null << 'EOF'
server {
    listen 80;
    server_name 82.64.171.203;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /home/syff/wvw-analytics/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        internal;
        alias /home/syff/wvw-analytics/uploads;
    }

    # Logs
    access_log /var/log/nginx/wvw_analytics_access.log;
    error_log /var/log/nginx/wvw_analytics_error.log;
}
EOF

echo "✓ Configuration créée"

# Vérifier la configuration
echo "Vérification de la configuration Nginx..."
sudo nginx -t

# Recharger Nginx
echo "Rechargement de Nginx..."
sudo systemctl reload nginx

echo ""
echo "=== Configuration terminée ==="
echo "WvW Analytics est maintenant accessible sur:"
echo "  http://82.64.171.203"
echo ""
echo "Pour vérifier:"
echo "  curl http://82.64.171.203"
