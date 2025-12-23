# Service Produits - PayeTonKawa ☕

Microservice de gestion du catalogue de produits café pour PayeTonKawa, développé avec FastAPI, PostgreSQL et RabbitMQ.

> 🚀 **Démarrage sans Docker:** Si Docker ne fonctionne pas, utilisez `./start_local.sh` (Linux/macOS) ou `start_local.bat` (Windows)  
> 📖 **Guide complet:** [DEMARRAGE_SANS_DOCKER.md](DEMARRAGE_SANS_DOCKER.md) | **Démarrage rapide:** [QUICKSTART.md](QUICKSTART.md)

## 🎯 Fonctionnalités

- **Gestion des catégories** : Création et organisation des catégories de café (Arabica, Robusta, Bio, etc.)
- **Gestion des produits** : CRUD complet pour les produits avec prix, descriptions et caractéristiques
- **Gestion des stocks** : Suivi des quantités, alertes de réapprovisionnement
- **Communication asynchrone** : Événements RabbitMQ pour synchronisation avec autres services
- **API REST** : Documentation automatique avec OpenAPI/Swagger

## 🏗️ Architecture Technique

- **Framework** : FastAPI 0.104+
- **Base de données** : PostgreSQL 15
- **ORM** : SQLAlchemy 2.0
- **Migrations** : Alembic
- **Message Broker** : RabbitMQ
- **Validation** : Pydantic v2
- **Tests** : Pytest + httpx
- **Conteneurisation** : Docker + Docker Compose

## 📋 Prérequis

- Python 3.11+
- PostgreSQL 15+
- RabbitMQ 3.12+
- Docker & Docker Compose (optionnel mais recommandé)

## 🚀 Installation et Démarrage

### ⚡ Démarrage Rapide (SANS Docker)

**Pour démarrer rapidement sans Docker, utilisez les scripts fournis:**

**Linux/macOS:**
```bash
# 1. Configuration de la base de données (recommandé)
chmod +x setup_database.sh
./setup_database.sh

# 2. Démarrage de l'application
chmod +x start_local.sh
./start_local.sh
```

**Windows:**
```cmd
start_local.bat
```

📖 **Guide complet:** Voir [DEMARRAGE_SANS_DOCKER.md](DEMARRAGE_SANS_DOCKER.md) pour les instructions détaillées.

**Prérequis:**
- Python 3.11+
- PostgreSQL 15+ (requis)
- RabbitMQ 3.12+ (optionnel - l'app fonctionne sans)

**⚠️ En cas d'erreur "role does not exist":**
Le script `setup_database.sh` configure automatiquement PostgreSQL avec vos identifiants système.

---

### 🐳 Option 2 : Avec Docker (Recommandé)

**⚠️ Note importante:** Si vous rencontrez l'erreur "relation already exists", c'est que la base de données contient déjà des tables. Solution:

```bash
# Supprimer les volumes Docker et redémarrer proprement
docker-compose down -v
docker-compose up -d
```

**Démarrage normal:**
```bash
# Démarrer tous les services (API + PostgreSQL + RabbitMQ)
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose logs api | tail -20
```

**Accès à l'API:**
- Documentation Swagger : http://localhost:8000/docs
- Documentation ReDoc : http://localhost:8000/redoc
- API : http://localhost:8000

**Commandes utiles:**
```bash
# Voir les logs
docker-compose logs -f api

# Exécuter les migrations manuellement (si nécessaire)
docker-compose exec api alembic upgrade head

# Accéder au shell PostgreSQL
docker-compose exec db psql -U produits_user -d produits_db

# Redémarrer l'API
docker-compose restart api

# Arrêter tout
docker-compose down

# Arrêter et supprimer les volumes (reset complet)
docker-compose down -v
```

---

### Option 3 : Installation locale (Manuelle)

Si vous préférez configurer manuellement:

1. **Créer un environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer les variables d'environnement**
```bash
cp .env.template .env
# Modifier DATABASE_URL et RABBITMQ_URL dans .env
```

4. **Créer la base de données**
```bash
# Assurez-vous que PostgreSQL est en cours d'exécution
createdb produits_db
```

5. **Exécuter les migrations**
```bash
alembic upgrade head
```

7. **Lancer l'application**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

L'API sera accessible sur http://localhost:8000

Documentation interactive : http://localhost:8000/docs

---

### Option 2 : Avec Docker

**Note importante:** Si vous avez déjà un fichier `.env` pour le développement local, il peut causer des conflits avec Docker.

1. **Option A: Sans fichier .env (Recommandé)**

Docker Compose utilisera les valeurs par défaut intégrées :
```bash
docker-compose up -d
```

Les identifiants par défaut :
- User: `produits_user`
- Password: `produits_password`
- Database: `produits_db`

2. **Option B: Avec fichier .env personnalisé**

```bash
# Copier l'exemple Docker
cp .env.docker.example .env

# Modifier si nécessaire
nano .env

# Lancer
docker-compose up -d
```

3. **En cas d'erreur "database does not exist"**

Si vous aviez un ancien `.env` avec des credentials invalides :
```bash
# Arrêter et nettoyer les conteneurs
docker-compose down -v

# Supprimer le .env ou utiliser .env.docker.example
rm .env
# OU
cp .env.docker.example .env

# Relancer
docker-compose up -d
```

4. **En cas d'erreur "relation does not exist"**

Si les tables de la base de données n'ont pas été créées :
```bash
# Les migrations s'exécutent automatiquement au démarrage
# Mais si nécessaire, vous pouvez les relancer manuellement:
docker-compose exec api alembic upgrade head
```

L'API sera accessible sur http://localhost:8000

Documentation interactive : http://localhost:8000/docs

RabbitMQ Management : http://localhost:15672 (guest/guest)

## 🧪 Tests

### Exécuter tous les tests
```bash
pytest
```

### Avec couverture de code
```bash
pytest --cov=app --cov-report=html
```

### Tests spécifiques
```bash
pytest tests/test_products.py
pytest tests/test_categories.py
pytest tests/test_stock.py
```

## 📚 Documentation API

### Endpoints principaux

#### Catégories
- `GET /api/v1/categories/` - Liste des catégories
- `POST /api/v1/categories/` - Créer une catégorie
- `GET /api/v1/categories/{id}` - Détails d'une catégorie
- `PUT /api/v1/categories/{id}` - Modifier une catégorie
- `DELETE /api/v1/categories/{id}` - Supprimer une catégorie

#### Produits
- `GET /api/v1/products/` - Liste des produits (avec filtres)
- `POST /api/v1/products/` - Créer un produit
- `GET /api/v1/products/{id}` - Détails d'un produit
- `PUT /api/v1/products/{id}` - Modifier un produit
- `DELETE /api/v1/products/{id}` - Supprimer un produit

#### Stock
- `GET /api/v1/stock/` - Liste des stocks
- `GET /api/v1/stock/alerts` - Produits en alerte de stock
- `GET /api/v1/stock/product/{product_id}` - Stock d'un produit
- `POST /api/v1/stock/product/{product_id}/adjust` - Ajuster le stock
- `PUT /api/v1/stock/{id}` - Modifier un stock

### Documentation interactive

Accédez à http://localhost:8000/docs pour la documentation Swagger interactive.

## 🔧 Développement

### Structure du projet
```
api-products/
├── app/
│   ├── main.py              # Application FastAPI
│   ├── config.py            # Configuration
│   ├── database.py          # Configuration DB
│   ├── models/              # Modèles SQLAlchemy
│   ├── schemas/             # Schémas Pydantic
│   ├── api/v1/              # Endpoints REST
│   ├── services/            # Logique métier
│   ├── repositories/        # Accès données
│   └── events/              # RabbitMQ
├── tests/                   # Tests
├── migrations/              # Migrations Alembic
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Générer une nouvelle migration
```bash
alembic revision --autogenerate -m "Description du changement"
alembic upgrade head
```

### Formater le code
```bash
black app tests
```

### Linter
```bash
flake8 app tests
```

## 📊 Modèles de données

### Category
- Nom, description, code
- Relations avec produits

### Product
- SKU, nom, description
- Prix HT/TTC, TVA
- Catégorie, fournisseur, origine
- Caractéristiques (poids, unité)
- Statut (actif, rupture, archivé)

### Stock
- Quantités (disponible, réservée, min, max)
- Alertes de stock bas
- Historique des mouvements

## 🔌 Événements RabbitMQ

Le service publie les événements suivants :

- `product.created` - Produit créé
- `product.updated` - Produit modifié
- `product.deleted` - Produit supprimé
- `stock.updated` - Stock modifié
- `stock.low_alert` - Alerte stock bas

## 🔒 Sécurité

- Validation des données avec Pydantic
- Protection contre injection SQL avec SQLAlchemy
- Gestion des erreurs structurée
- CORS configuré pour production

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet fait partie du système PayeTonKawa - MSPR 4

## 👥 Équipe

Projet développé dans le cadre de la migration vers une architecture microservices.

## 📞 Support

Pour toute question ou problème, ouvrir une issue sur le repository.
