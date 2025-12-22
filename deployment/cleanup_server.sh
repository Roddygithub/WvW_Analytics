#!/bin/bash
# Script de nettoyage du serveur pour WvW Analytics
# À exécuter sur le serveur distant

set -e

echo "=== Nettoyage de l'ancien projet GW2 CounterPicker ==="

# Arrêter et désactiver le service
echo "Arrêt du service gw2-counterpicker..."
sudo systemctl stop gw2-counterpicker.service || true
sudo systemctl disable gw2-counterpicker.service || true

# Supprimer le fichier de service
echo "Suppression du fichier de service..."
sudo rm -f /etc/systemd/system/gw2-counterpicker.service
sudo systemctl daemon-reload

# Supprimer les dossiers du projet
echo "Suppression des dossiers du projet..."
rm -rf ~/gw2-counterpicker
sudo rm -rf /root/gw2optimizer
rm -f ~/gw2opt-deploy.tar.gz
rm -f ~/deploy_*.sh
rm -f ~/fix_apache_and_start.sh

# Vérifier les services Apache/Nginx en cours
echo "Vérification des services web..."
sudo systemctl status apache2 || echo "Apache2 non installé/actif"
sudo systemctl status nginx || echo "Nginx non installé/actif"

# Arrêter Apache s'il tourne (on utilisera Nginx pour WvW Analytics)
sudo systemctl stop apache2 || true
sudo systemctl disable apache2 || true

echo "=== Nettoyage terminé ==="
echo ""
echo "Vérification de l'espace disque:"
df -h /
echo ""
echo "Services actifs:"
systemctl list-units --type=service --state=running | grep -E 'apache|nginx|gw2' || echo "Aucun service web actif"
