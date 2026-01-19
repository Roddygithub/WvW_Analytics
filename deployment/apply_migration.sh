#!/bin/bash
# Script pour appliquer la migration de schéma sur le serveur distant
# À exécuter sur le serveur: ssh syff@82.64.171.203 -p 2222

set -e

echo "=== Migration du Schéma de Base de Données ==="
echo ""

# Vérifier que le fichier SQL existe
if [ ! -f ~/wvw-analytics/deployment/migrate_db_schema.sql ]; then
    echo "❌ Erreur: Fichier migrate_db_schema.sql introuvable"
    exit 1
fi

echo "📋 Application de la migration SQL..."
sudo -u postgres psql -d wvw_analytics -f ~/wvw-analytics/deployment/migrate_db_schema.sql

echo ""
echo "✅ Migration terminée avec succès!"
echo ""
echo "🔄 Redémarrage du service WvW Analytics..."
sudo systemctl restart wvw-analytics

echo ""
echo "✓ Service redémarré"
echo ""
echo "📊 Vérification du statut:"
sudo systemctl status wvw-analytics --no-pager -l

echo ""
echo "=== Migration Complète ==="
echo "Vous pouvez maintenant uploader des logs sur http://82.64.171.203"
