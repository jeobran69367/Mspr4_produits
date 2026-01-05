#!/bin/bash

# Script de configuration PostgreSQL pour Service Produits
# Ce script aide à configurer PostgreSQL correctement

echo "🔧 Configuration PostgreSQL - Service Produits"
echo "=============================================="
echo ""

# Vérifier PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL n'est pas installé"
    echo ""
    echo "Installation:"
    echo "  macOS:   brew install postgresql@15"
    echo "  Ubuntu:  sudo apt install postgresql postgresql-contrib"
    echo "  Fedora:  sudo dnf install postgresql postgresql-server"
    exit 1
fi

echo "✅ PostgreSQL est installé"
echo ""

# Détecter l'utilisateur système
SYSTEM_USER=$(whoami)
DB_NAME="produits_db"

echo "📋 Configuration détectée:"
echo "   Utilisateur système: $SYSTEM_USER"
echo "   Base de données: $DB_NAME"
echo ""

# Vérifier si la base de données existe
echo "🔍 Vérification de la base de données..."
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "✅ La base de données '$DB_NAME' existe déjà"
    echo ""
    read -p "Voulez-vous la supprimer et la recréer? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo "🗑️  Suppression de la base de données..."
        dropdb "$DB_NAME" 2>/dev/null || {
            echo "❌ Impossible de supprimer la base de données"
            echo "   Essayez: dropdb -U postgres $DB_NAME"
            exit 1
        }
        echo "✅ Base de données supprimée"
    else
        echo "✅ Conservation de la base de données existante"
        exit 0
    fi
fi

# Créer la base de données
echo ""
echo "📦 Création de la base de données '$DB_NAME'..."

if createdb "$DB_NAME" 2>/dev/null; then
    echo "✅ Base de données créée avec succès"
else
    echo "⚠️  Échec avec l'utilisateur actuel, essai avec postgres..."
    
    # Essayer avec l'utilisateur postgres
    if sudo -u postgres createdb "$DB_NAME" 2>/dev/null; then
        echo "✅ Base de données créée avec l'utilisateur postgres"
        
        # Donner les droits à l'utilisateur système
        echo "🔐 Attribution des droits à $SYSTEM_USER..."
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $SYSTEM_USER;" 2>/dev/null || {
            echo "⚠️  L'utilisateur $SYSTEM_USER n'existe pas dans PostgreSQL"
            echo "   Création de l'utilisateur..."
            sudo -u postgres createuser -s "$SYSTEM_USER" 2>/dev/null
            echo "✅ Utilisateur créé avec succès"
        }
    else
        echo "❌ Impossible de créer la base de données"
        echo ""
        echo "🔧 Solutions:"
        echo "1. Vérifier que PostgreSQL est démarré:"
        echo "   macOS:  brew services start postgresql@15"
        echo "   Linux:  sudo systemctl start postgresql"
        echo ""
        echo "2. Créer manuellement:"
        echo "   createdb $DB_NAME"
        echo "   Ou: sudo -u postgres createdb $DB_NAME"
        echo ""
        echo "3. Se connecter à psql et créer:"
        echo "   psql postgres"
        echo "   CREATE DATABASE $DB_NAME;"
        exit 1
    fi
fi

# Vérifier la connexion
echo ""
echo "🔍 Test de connexion à la base de données..."
if psql -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Connexion réussie!"
    
    # Afficher la version
    PG_VERSION=$(psql -d "$DB_NAME" -tAc "SELECT version();" | head -1)
    echo "   $PG_VERSION"
else
    echo "⚠️  Impossible de se connecter à la base de données"
    echo ""
    echo "Configuration du fichier .env:"
    echo "   Sans mot de passe: DATABASE_URL=postgresql://$SYSTEM_USER@localhost:5432/$DB_NAME"
    echo "   Avec postgres:     DATABASE_URL=postgresql://postgres@localhost:5432/$DB_NAME"
fi

# Configurer le fichier .env
echo ""
echo "🔧 Configuration du fichier .env..."

if [ -f ".env" ]; then
    echo "⚠️  Le fichier .env existe déjà"
    read -p "Voulez-vous mettre à jour DATABASE_URL? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        UPDATE_ENV=true
    else
        UPDATE_ENV=false
    fi
else
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✅ Fichier .env créé depuis .env.template"
        UPDATE_ENV=true
    else
        echo "❌ Fichier .env.template introuvable"
        exit 1
    fi
fi

if [ "$UPDATE_ENV" = true ]; then
    # Mettre à jour DATABASE_URL
    DATABASE_URL="postgresql://$SYSTEM_USER@localhost:5432/$DB_NAME"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|g" .env
    else
        # Linux
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|g" .env
    fi
    
    echo "✅ DATABASE_URL mis à jour dans .env:"
    echo "   $DATABASE_URL"
fi

echo ""
echo "🎉 Configuration PostgreSQL terminée!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Vérifier le fichier .env"
echo "2. Lancer les migrations: alembic upgrade head"
echo "3. Démarrer l'application: ./start_local.sh"
echo ""
echo "Ou simplement lancer: ./start_local.sh"
