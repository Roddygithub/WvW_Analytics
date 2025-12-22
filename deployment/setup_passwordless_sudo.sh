#!/bin/bash
# Configuration du sudo sans mot de passe (à exécuter UNE FOIS)

echo "=== Configuration Sudo Sans Mot de Passe ==="
echo "Vous allez devoir entrer votre mot de passe UNE SEULE FOIS."
echo ""

# Créer le fichier sudoers pour wvw-analytics
sudo tee /etc/sudoers.d/wvw-analytics > /dev/null << 'SUDOEOF'
# WvW Analytics - Commandes sans mot de passe
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl start wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl status wvw-analytics
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl daemon-reload
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload nginx
syff ALL=(ALL) NOPASSWD: /usr/bin/systemctl disable *
syff ALL=(ALL) NOPASSWD: /usr/bin/nginx -t
syff ALL=(ALL) NOPASSWD: /usr/bin/journalctl *
syff ALL=(ALL) NOPASSWD: /usr/bin/cp /home/syff/wvw-analytics/deployment/* /etc/systemd/system/
syff ALL=(ALL) NOPASSWD: /usr/bin/cp /home/syff/wvw-analytics/deployment/* /etc/nginx/sites-available/
syff ALL=(ALL) NOPASSWD: /usr/bin/ln -sf /etc/nginx/sites-available/* /etc/nginx/sites-enabled/
syff ALL=(ALL) NOPASSWD: /usr/bin/rm -f /etc/nginx/sites-enabled/*
syff ALL=(ALL) NOPASSWD: /usr/bin/rm -f /etc/nginx/sites-available/*
syff ALL=(ALL) NOPASSWD: /usr/bin/rm -f /etc/systemd/system/gw2*
syff ALL=(ALL) NOPASSWD: /usr/bin/rm -rf /root/gw2*
syff ALL=(ALL) NOPASSWD: /usr/bin/tee /var/log/nginx/*
syff ALL=(ALL) NOPASSWD: /usr/bin/tail *
SUDOEOF

sudo chmod 440 /etc/sudoers.d/wvw-analytics

echo ""
echo "✓ Configuration terminée !"
echo ""
echo "Vous pouvez maintenant exécuter les commandes sudo sans mot de passe."
echo "Testez avec: sudo systemctl status wvw-analytics"
