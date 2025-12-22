#!/bin/bash
# Script de mise à jour rapide de l'application WvW Analytics
# À exécuter sur le serveur distant

set -e

APP_DIR="$HOME/wvw-analytics"

echo "=== Mise à jour de WvW Analytics ==="

cd "$APP_DIR"

# Sauvegarder la base de données
echo "Sauvegarde de la base de données..."
sudo -u postgres pg_dump wvw_analytics > backup_$(date +%Y%m%d_%H%M%S).sql

# Récupérer les dernières modifications
echo "Récupération des modifications depuis GitHub..."
git pull origin main

# Activer l'environnement virtuel et mettre à jour les dépendances
echo "Mise à jour des dépendances Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Redémarrer le service
echo "Redémarrage du service..."
sudo systemctl restart wvw-analytics

# Attendre que le service démarre
sleep 3

# Vérifier le statut
echo ""
echo "Statut du service:"
sudo systemctl status wvw-analytics --no-pager

echo ""
echo "=== Mise à jour terminée ==="
echo "L'application a été mise à jour et redémarrée avec succès"
