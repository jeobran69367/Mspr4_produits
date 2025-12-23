# 🚀 Démarrage Rapide - Service Produits

## Pour les utilisateurs pressés

### Si Docker ne fonctionne pas chez vous

**1. Lancez simplement le script:**

```bash
# Linux/macOS
./start_local.sh

# Windows
start_local.bat
```

**2. C'est tout!** 🎉

Le script va:
- ✅ Créer l'environnement Python
- ✅ Installer les dépendances
- ✅ Configurer le fichier .env
- ✅ Appliquer les migrations
- ✅ Démarrer l'application

## Accès à l'application

- **API:** http://localhost:8000
- **Documentation interactive:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Avant de commencer

Assurez-vous que **PostgreSQL est installé et démarré**.

### Installation rapide de PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Téléchargez depuis: https://www.postgresql.org/download/windows/

### Configuration automatique de la base de données

**Utilisez le script de configuration (recommandé):**
```bash
chmod +x setup_database.sh
./setup_database.sh
```

Ce script va automatiquement:
- ✅ Détecter votre configuration PostgreSQL
- ✅ Créer la base de données 'produits_db'
- ✅ Configurer le fichier .env avec les bons identifiants

### Ou créer manuellement

```bash
createdb produits_db
```

**En cas d'erreur "role does not exist":**
```bash
# Créer l'utilisateur PostgreSQL
createuser -s $(whoami)
# Puis créer la base
createdb produits_db
```

## RabbitMQ (Optionnel)

⚠️ **L'application fonctionne sans RabbitMQ!**

RabbitMQ n'est nécessaire que pour la communication entre microservices. Si vous testez uniquement ce service, vous pouvez l'ignorer.

## En cas de problème

1. **Vérifiez que PostgreSQL est démarré:**
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list                # macOS
   ```

2. **Vérifiez la base de données:**
   ```bash
   psql -l  # Liste les bases de données
   ```

3. **Consultez le guide détaillé:**
   Voir [DEMARRAGE_SANS_DOCKER.md](DEMARRAGE_SANS_DOCKER.md)

## Tester rapidement

```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Créer une catégorie de test
curl -X POST http://localhost:8000/api/v1/categories/ \
  -H "Content-Type: application/json" \
  -d '{"nom":"Arabica","code":"ARAB","description":"Test"}'
```

## Commandes utiles

```bash
# Lancer les tests
pytest

# Arrêter l'application
Ctrl+C dans le terminal

# Relancer l'application
uvicorn app.main:app --reload
```

## Besoin d'aide?

1. Consultez http://localhost:8000/docs pour la documentation API
2. Lisez le guide détaillé: [DEMARRAGE_SANS_DOCKER.md](DEMARRAGE_SANS_DOCKER.md)
3. Vérifiez le [README.md](README.md) complet
