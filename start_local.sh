#!/bin/bash

# Script de démarrage sans Docker pour Service Produits
# Ce script configure et lance l'application localement

set -e

echo "🚀 Démarrage du Service Produits (sans Docker)"
echo "================================================"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Copier .env si nécessaire
if [ ! -f ".env" ]; then
    echo "📝 Copie du fichier .env.template vers .env..."
    cp .env.template .env
    echo "⚠️  IMPORTANT: Modifiez le fichier .env avec vos configurations"
fi

# Vérifier la configuration
echo ""
echo "📋 Configuration actuelle:"
echo "   - Fichier .env: ✅ Présent"
if grep -q "DATABASE_URL=.*localhost" .env 2>/dev/null; then
    echo "   - DATABASE_URL: ✅ Configuré pour localhost"
else
    echo "   - DATABASE_URL: ⚠️  Vérifiez la configuration"
fi

echo ""
echo "⚠️  PRÉREQUIS:"
echo "   1. PostgreSQL doit être installé et en cours d'exécution"
echo "   2. RabbitMQ doit être installé et en cours d'exécution (optionnel)"
echo "   3. La base de données 'produits_db' doit être créée"
echo ""
echo "Pour créer la base de données PostgreSQL:"
echo "   createdb produits_db"
echo ""
echo "Pour lancer PostgreSQL (si non démarré):"
echo "   sudo service postgresql start    # Linux"
echo "   brew services start postgresql   # macOS"
echo ""
echo "Pour lancer RabbitMQ (optionnel):"
echo "   sudo service rabbitmq-server start  # Linux"
echo "   brew services start rabbitmq        # macOS"
echo ""

read -p "Voulez-vous continuer le démarrage? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "❌ Démarrage annulé"
    exit 1
fi

# Exécuter les migrations
echo ""
echo "🔄 Exécution des migrations de base de données..."
if alembic upgrade head; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "⚠️  Erreur lors des migrations - vérifiez votre configuration de base de données"
    echo "   Vous pouvez continuer mais l'application pourrait ne pas fonctionner"
    read -p "Continuer quand même? (o/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        exit 1
    fi
fi

# Lancer l'application
echo ""
echo "🎉 Démarrage de l'application..."
echo "================================================"
echo ""
echo "📍 L'API sera accessible sur: http://localhost:8000"
echo "📖 Documentation Swagger: http://localhost:8000/docs"
echo "📖 Documentation ReDoc: http://localhost:8000/redoc"
echo ""
echo "Pour arrêter l'application, appuyez sur Ctrl+C"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
