# Guide de Démarrage sans Docker

Ce guide explique comment lancer le Service Produits **sans utiliser Docker**.

## 🎯 Vue d'ensemble

Le Service Produits peut fonctionner de deux manières:
1. **Mode complet** : Avec PostgreSQL + RabbitMQ (recommandé)
2. **Mode simplifié** : Avec PostgreSQL uniquement (RabbitMQ optionnel)

## 📋 Prérequis

### Installation des composants

#### PostgreSQL (Requis)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Télécharger depuis https://www.postgresql.org/download/windows/

#### RabbitMQ (Optionnel)

**Ubuntu/Debian:**
```bash
sudo apt install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

**macOS:**
```bash
brew install rabbitmq
brew services start rabbitmq
```

**Windows:**
Télécharger depuis https://www.rabbitmq.com/download.html

#### Python 3.11+

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
Télécharger depuis https://www.python.org/downloads/

## 🚀 Démarrage Rapide

### Méthode 1: Script automatique (Recommandé)

**Linux/macOS:**
```bash
chmod +x start_local.sh
./start_local.sh
```

**Windows:**
```cmd
start_local.bat
```

### Méthode 2: Étapes manuelles

#### 1. Créer l'environnement virtuel

```bash
python3 -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 2. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configuration

```bash
# Copier le template de configuration
cp .env.template .env

# Éditer .env avec vos paramètres
nano .env  # ou vim, code, notepad, etc.
```

**Configuration minimale dans .env:**
```env
# Database (Requis)
DATABASE_URL=postgresql://user:password@localhost:5432/produits_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=produits_db

# RabbitMQ (Optionnel - l'application démarre sans)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=payetonkawa
RABBITMQ_QUEUE_PRODUCTS=products_events

# Application
APP_NAME=Service Produits - PayeTonKawa
APP_VERSION=1.0.0
DEBUG=True
API_V1_PREFIX=/api/v1
```

#### 4. Créer la base de données

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Dans psql:
CREATE DATABASE produits_db;
CREATE USER user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE produits_db TO user;
\q
```

Ou avec createdb:
```bash
createdb produits_db
```

#### 5. Exécuter les migrations

```bash
alembic upgrade head
```

#### 6. Lancer l'application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🧪 Vérification

L'application est accessible sur:
- **API:** http://localhost:8000
- **Documentation Swagger:** http://localhost:8000/docs
- **Documentation ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Tester l'API

```bash
# Test du health check
curl http://localhost:8000/health

# Créer une catégorie
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Arabica",
    "description": "Café Arabica de qualité",
    "code": "ARAB"
  }'

# Lister les catégories
curl http://localhost:8000/api/v1/categories/
```

## 🔧 Dépannage

### Erreur: "role does not exist" (PostgreSQL)

**Symptôme:**
```
psycopg2.OperationalError: FATAL: role "user" does not exist
```

**Cause:** Les identifiants par défaut dans `.env` ne correspondent pas à votre configuration PostgreSQL.

**Solution:**

**Option 1: Utiliser le script de configuration automatique**
```bash
./setup_database.sh
```
Ce script va:
- Détecter votre nom d'utilisateur système
- Créer la base de données si nécessaire
- Configurer automatiquement le fichier .env

**Option 2: Configuration manuelle**

1. **Identifier votre utilisateur PostgreSQL:**
   ```bash
   whoami  # Affiche votre nom d'utilisateur système
   ```

2. **Modifier le fichier .env:**
   ```bash
   # Sans mot de passe (recommandé pour développement local)
   DATABASE_URL=postgresql://votre_username@localhost:5432/produits_db
   
   # Exemples:
   # DATABASE_URL=postgresql://jeobrankombou@localhost:5432/produits_db
   # DATABASE_URL=postgresql://postgres@localhost:5432/produits_db
   ```

3. **Créer l'utilisateur PostgreSQL si nécessaire:**
   ```bash
   # Sur macOS avec Homebrew
   createuser -s $(whoami)
   
   # Sur Linux
   sudo -u postgres createuser -s $(whoami)
   ```

4. **Créer la base de données:**
   ```bash
   createdb produits_db
   ```

**Option 3: Utiliser l'utilisateur postgres par défaut**

Modifiez `.env`:
```bash
DATABASE_URL=postgresql://postgres@localhost:5432/produits_db
```

Puis créez la base:
```bash
sudo -u postgres createdb produits_db
```

### Erreur: "Connection refused" pour PostgreSQL

```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Démarrer PostgreSQL si nécessaire
sudo systemctl start postgresql   # Linux
brew services start postgresql    # macOS
```

### Erreur: "database does not exist"

```bash
# Créer la base de données
createdb produits_db

# Ou via psql
sudo -u postgres psql -c "CREATE DATABASE produits_db;"
```

### Erreur: "Connection refused" pour RabbitMQ

L'application peut fonctionner **sans RabbitMQ**. Elle affichera un warning au démarrage mais continuera à fonctionner.

Pour utiliser RabbitMQ:
```bash
# Démarrer RabbitMQ
sudo systemctl start rabbitmq-server  # Linux
brew services start rabbitmq          # macOS
```

### Erreur de migration Alembic

```bash
# Réinitialiser les migrations
alembic downgrade base
alembic upgrade head

# Ou recréer la base de données
dropdb produits_db
createdb produits_db
alembic upgrade head
```

### Port 8000 déjà utilisé

```bash
# Utiliser un autre port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🧪 Exécuter les tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_products.py -v
```

## 🔄 Mode Développement

Pour développer avec rechargement automatique:

```bash
# Avec uvicorn (rechargement auto)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Logs détaillés
uvicorn app.main:app --reload --log-level debug
```

## 📊 Monitoring

### Logs de l'application
Les logs s'affichent dans la console. Pour les sauvegarder:

```bash
uvicorn app.main:app --reload 2>&1 | tee app.log
```

### Accès RabbitMQ Management (si installé)
http://localhost:15672
- Username: guest
- Password: guest

## ⚙️ Configuration Avancée

### Variables d'environnement importantes

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL | `postgresql://user:password@localhost:5432/produits_db` |
| `RABBITMQ_URL` | URL de connexion RabbitMQ | `amqp://guest:guest@localhost:5672/` |
| `DEBUG` | Mode debug | `True` |
| `API_V1_PREFIX` | Préfixe des routes API | `/api/v1` |

### Utiliser une base de données SQLite (pour tests locaux)

Modifier `.env`:
```env
DATABASE_URL=sqlite:///./produits.db
```

⚠️ **Note:** SQLite n'est pas recommandé pour la production, uniquement pour les tests locaux.

## 🛑 Arrêter l'application

Appuyez sur `Ctrl+C` dans le terminal où l'application s'exécute.

Pour arrêter les services:
```bash
# PostgreSQL
sudo systemctl stop postgresql    # Linux
brew services stop postgresql     # macOS

# RabbitMQ
sudo systemctl stop rabbitmq-server  # Linux
brew services stop rabbitmq          # macOS
```

## 📝 Notes Importantes

1. **RabbitMQ est optionnel** - L'application démarre et fonctionne sans RabbitMQ (avec un warning)
2. **PostgreSQL est requis** - Impossible de démarrer sans base de données
3. **Port par défaut** - 8000 (modifiable avec `--port`)
4. **Mode reload** - Utiliser `--reload` uniquement en développement

## 🆘 Besoin d'aide?

Si vous rencontrez des problèmes:
1. Vérifiez les logs dans la console
2. Testez le health check: `curl http://localhost:8000/health`
3. Vérifiez que PostgreSQL est accessible: `psql -h localhost -U user -d produits_db`
4. Consultez la documentation: http://localhost:8000/docs
