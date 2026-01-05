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

# Copier .env si nécessaire et le configurer
SYSTEM_USER=$(whoami)

if [ ! -f ".env" ]; then
    echo "📝 Copie du fichier .env.template vers .env..."
    cp .env.template .env
    echo "🔧 Configuration automatique de PostgreSQL..."
    echo "   Utilisateur système détecté: $SYSTEM_USER"
else
    # Vérifier si .env contient les anciennes credentials par défaut
    if grep -q "DATABASE_URL=.*user:password@" .env 2>/dev/null; then
        echo "🔧 Détection d'anciennes credentials - mise à jour..."
        echo "   Utilisateur système détecté: $SYSTEM_USER"
    elif grep -q "DATABASE_URL=postgresql://localhost:5432" .env 2>/dev/null; then
        echo "🔧 Configuration de DATABASE_URL..."
        echo "   Utilisateur système détecté: $SYSTEM_USER"
    fi
fi

# Toujours mettre à jour DATABASE_URL avec le bon utilisateur système
# Gère plusieurs formats possibles de DATABASE_URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    # Remplacer n'importe quel format postgresql://...@localhost:5432/produits_db
    sed -i '' "s|^DATABASE_URL=postgresql://[^@]*@localhost:5432/produits_db.*|DATABASE_URL=postgresql://$SYSTEM_USER@localhost:5432/produits_db|g" .env
    # Remplacer le format sans utilisateur
    sed -i '' "s|^DATABASE_URL=postgresql://localhost:5432/produits_db.*|DATABASE_URL=postgresql://$SYSTEM_USER@localhost:5432/produits_db|g" .env
else
    # Linux
    # Remplacer n'importe quel format postgresql://...@localhost:5432/produits_db
    sed -i "s|^DATABASE_URL=postgresql://[^@]*@localhost:5432/produits_db.*|DATABASE_URL=postgresql://$SYSTEM_USER@localhost:5432/produits_db|g" .env
    # Remplacer le format sans utilisateur
    sed -i "s|^DATABASE_URL=postgresql://localhost:5432/produits_db.*|DATABASE_URL=postgresql://$SYSTEM_USER@localhost:5432/produits_db|g" .env
fi

echo "✅ DATABASE_URL configuré: postgresql://$SYSTEM_USER@localhost:5432/produits_db"

# Vérifier PostgreSQL
echo ""
echo "🔍 Vérification de PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL est installé"
    
    # Tester la connexion
    SYSTEM_USER=$(whoami)
    DB_NAME="produits_db"
    
    if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        echo "✅ La base de données '$DB_NAME' existe déjà"
    else
        echo "⚠️  La base de données '$DB_NAME' n'existe pas"
        echo ""
        read -p "Voulez-vous créer la base de données maintenant? (o/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            if createdb "$DB_NAME" 2>/dev/null; then
                echo "✅ Base de données '$DB_NAME' créée avec succès"
            else
                echo "❌ Erreur lors de la création de la base de données"
                echo "   Essayez manuellement: createdb $DB_NAME"
                echo "   Ou avec un utilisateur spécifique: createdb -U postgres $DB_NAME"
                exit 1
            fi
        else
            echo "⚠️  Vous devez créer la base de données manuellement:"
            echo "   createdb $DB_NAME"
            echo "   Ou: createdb -U postgres $DB_NAME"
            exit 1
        fi
    fi
else
    echo "❌ PostgreSQL n'est pas installé ou pas dans le PATH"
    echo ""
    echo "Installation de PostgreSQL:"
    echo "  macOS:   brew install postgresql@15 && brew services start postgresql@15"
    echo "  Ubuntu:  sudo apt install postgresql postgresql-contrib"
    echo "  Fedora:  sudo dnf install postgresql postgresql-server"
    exit 1
fi

# Vérifier la configuration
echo ""
echo "📋 Configuration actuelle:"
echo "   - Fichier .env: ✅ Présent"
if grep -q "DATABASE_URL=.*localhost" .env 2>/dev/null; then
    DB_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    echo "   - DATABASE_URL actuel: $DB_URL"
    
    # Double vérification: si les anciennes credentials persistent
    if echo "$DB_URL" | grep -q "user:password"; then
        echo ""
        echo "❌ ERREUR: Les anciennes credentials sont toujours présentes!"
        echo "   Cela ne devrait pas arriver. Veuillez supprimer .env et relancer:"
        echo "   rm .env && ./start_local.sh"
        exit 1
    fi
else
    echo "   - DATABASE_URL: ⚠️  Non configuré"
fi

echo ""
echo "⚠️  NOTE: RabbitMQ est optionnel (l'application fonctionne sans)"
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
if alembic upgrade head 2>&1; then
    echo "✅ Migrations appliquées avec succès"
else
    echo ""
    echo "❌ Erreur lors des migrations"
    echo ""
    echo "🔧 SOLUTIONS POSSIBLES:"
    echo ""
    echo "1. Vérifier que PostgreSQL est démarré:"
    echo "   macOS:  brew services list | grep postgresql"
    echo "   Linux:  sudo systemctl status postgresql"
    echo ""
    echo "2. Tester la connexion PostgreSQL:"
    echo "   psql -d produits_db"
    echo "   Ou: psql -U postgres -d produits_db"
    echo ""
    echo "3. Si l'utilisateur n'existe pas, créez-le:"
    echo "   Sur macOS avec Homebrew: createuser -s $(whoami)"
    echo "   Ou connectez-vous en tant que postgres: sudo -u postgres createuser -s $(whoami)"
    echo ""
    echo "4. Modifier DATABASE_URL dans .env avec les bons identifiants:"
    echo "   Sans mot de passe: postgresql://$(whoami)@localhost:5432/produits_db"
    echo "   Avec mot de passe: postgresql://username:password@localhost:5432/produits_db"
    echo ""
    exit 1
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
