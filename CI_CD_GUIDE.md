# 🚀 Guide CI/CD - Service Produits PayeTonKawa

## 📋 Vue d'ensemble

Ce projet utilise GitHub Actions pour l'intégration et le déploiement continus dans **un seul workflow unifié**.

### Workflow Unique

**CI/CD - API Produits** (`.github/workflows/ci-api-produits.yml`)

Ce workflow consolidé gère :
- ✅ Validation des Pull Requests (format titre, taille, conflits)
- 🔍 Analyse de code (lint, formatage, qualité)
- 🧪 Tests unitaires et couverture (>40%)
- 🔒 Analyse de sécurité (Safety, Bandit, OWASP, SonarCloud)
- 🏗️ Build et validation de l'application
- 🔗 Tests d'intégration avec PostgreSQL
- 🐳 Build et push d'images Docker
- 🚀 Déploiement automatique (staging/production)
- ⏮️ Rollback automatique en cas d'échec

---

## 🔄 CI/CD Pipeline

### Déclencheurs

Le pipeline se déclenche automatiquement sur :
- **Push** vers les branches : `main`, `develop`, `feature/**`, `release/**`
- **Pull requests** vers ces mêmes branches
- **Déclenchement manuel** (workflow_dispatch) pour choisir l'environnement de déploiement

### Étapes du Pipeline Consolidé

#### Phase 1 : Validation PR (uniquement pour les Pull Requests)
- **📝 Check PR Title** : Vérification format Conventional Commits
- **📊 PR Size Check** : Avertissement si PR > 1000 lignes
- **🔀 Conflict Check** : Détection automatique des conflits de merge

#### Phase 2 : CI - Analyse et Tests (toujours exécutée)

##### 1. 🔍 Lint - Analyse de code
- **Flake8** : Vérification de la syntaxe Python et des erreurs de style
- **Black** : Vérification du formatage du code
- **isort** : Vérification de l'ordre des imports
- **Pylint** : Analyse statique approfondie
- **ReviewDog** : Code review automatique sur PR

**Commandes locales :**
```bash
# Linter tout le code
flake8 app tests

# Formater le code
black app tests

# Trier les imports
isort app tests

# Analyse pylint
pylint app
```

##### 2. 🧪 Tests - Tests unitaires et couverture
- Exécution de tous les tests avec pytest
- Génération du rapport de couverture
- **Seuil minimum : 40% de couverture**
- Upload vers Codecov pour suivi

**Commandes locales :**
```bash
# Exécuter les tests avec couverture
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Voir le rapport HTML
open htmlcov/index.html
```

##### 3. 🔒 Sécurité - Scan de vulnérabilités
- **Safety** : Vérification des dépendances vulnérables
- **Bandit** : Analyse de sécurité du code Python
- **OWASP Dependency Check** : Scan des dépendances connues
- **SonarCloud** : Analyse de qualité et sécurité complète

**Commandes locales :**
```bash
# Vérifier les vulnérabilités
safety check

# Scan de sécurité Bandit
bandit -r app

# Voir les rapports
cat bandit-report.json
```

##### 4. 🏗️ Build - Construction de l'application
- Vérification que l'application peut démarrer
- Build de l'image Docker
- Tests de l'image construite

**Commandes locales :**
```bash
# Build Docker local
docker build -t mspr4-produits:test .

# Tester l'image
docker run --rm mspr4-produits:test python -c "from app.main import app; print('OK')"
```

##### 5. 🔗 Intégration - Tests d'intégration
- Lancement de PostgreSQL en service
- Exécution des migrations Alembic
- Tests d'intégration avec base de données réelle

#### Phase 3 : CD - Déploiement (uniquement sur push vers main/develop)

##### 1. 🐳 Build and Push
- Construction de l'image Docker multi-architecture (amd64/arm64)
- Push vers GitHub Container Registry
- Tagging avec version et SHA

##### 2. 🚀 Deploy to Staging (develop)
- Déploiement automatique sur l'environnement de staging
- Exécution des migrations
- Tests de fumée (smoke tests)

##### 3. 🌟 Deploy to Production (main)
- Déploiement sur l'environnement de production
- Exécution des migrations
- Health checks
- Notifications

##### 4. ⏮️ Rollback (en cas d'échec)
- Rollback automatique si le déploiement échoue
- Notifications de l'équipe

---

## 🔐 Configuration des Secrets

### Secrets Requis

Ajoutez ces secrets dans GitHub Settings → Secrets and variables → Actions :

```bash
# SonarCloud
SONAR_TOKEN=<your_sonar_token>

# Déploiement (selon votre plateforme)
RENDER_SERVICE_ID_STAGING=<staging_service_id>
RENDER_SERVICE_ID_PROD=<production_service_id>

# Ou pour Railway
RAILWAY_TOKEN=<your_railway_token>

# Notifications (optionnel)
SLACK_WEBHOOK_URL=<your_slack_webhook>
```

### Variables d'Environnement

Pour chaque environnement (staging/production), configurez :

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
RABBITMQ_URL=amqp://guest:guest@host:5672/  # Optionnel
```

---

## 📊 SonarCloud Setup

### 1. Créer un projet SonarCloud

1. Allez sur https://sonarcloud.io/
2. Connectez votre repository GitHub
3. Créez un projet avec la clé : `jeobran69367_Mspr4_produits`
4. Créez une organization : `jeobran69367`

### 2. Obtenir le token

1. SonarCloud → Account → Security
2. Generate Token → Copier le token
3. Ajouter comme secret `SONAR_TOKEN` dans GitHub

### 3. Configuration locale

Le fichier `sonar-project.properties` est déjà configuré. Pour scanner localement :

```bash
# Installer SonarScanner
# Puis exécuter
sonar-scanner
```

---

## 🛠️ Outils de Développement

### Configuration des Pre-commit Hooks

```bash
# Installer pre-commit
pip install pre-commit

# Installer les hooks
pre-commit install

# Exécuter manuellement
pre-commit run --all-files
```

### Configuration de l'IDE

#### VS Code (`settings.json`)

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 🔧 Résolution des Problèmes

### CI échoue sur Lint

```bash
# Formater automatiquement tout le code
black app tests
isort app tests

# Vérifier les erreurs
flake8 app tests
```

### Tests échouent

```bash
# Exécuter en mode verbose
pytest tests/ -vv

# Exécuter un test spécifique
pytest tests/test_categories.py::test_create_category -v

# Voir le troubleshooting
cat TESTS_TROUBLESHOOTING.md
```

### Couverture insuffisante (<40%)

1. Identifiez les fichiers non couverts :
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

2. Ajoutez des tests pour les fichiers manquants

3. Vérifiez la couverture :
   ```bash
   pytest --cov=app --cov-report=html
   open htmlcov/index.html
   ```

### Scan de sécurité trouve des vulnérabilités

```bash
# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt

# Vérifier les vulnérabilités
safety check

# Voir les détails
bandit -r app -f screen
```

### Build Docker échoue

```bash
# Build local avec logs détaillés
docker build -t mspr4-produits:debug . --progress=plain

# Vérifier le Dockerfile
docker build -t mspr4-produits:test . --no-cache
```

---

## 📈 Monitoring et Métriques

### Badges à ajouter dans README.md

```markdown
[![CI Status](https://github.com/jeobran69367/Mspr4_produits/workflows/CI%20-%20Int%C3%A9gration%20Continue/badge.svg)](https://github.com/jeobran69367/Mspr4_produits/actions)
[![codecov](https://codecov.io/gh/jeobran69367/Mspr4_produits/branch/main/graph/badge.svg)](https://codecov.io/gh/jeobran69367/Mspr4_produits)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jeobran69367_Mspr4_produits&metric=alert_status)](https://sonarcloud.io/dashboard?id=jeobran69367_Mspr4_produits)
```

### Dashboards Recommandés

1. **GitHub Actions** : Suivi des workflows
2. **Codecov** : Évolution de la couverture
3. **SonarCloud** : Qualité du code et dette technique
4. **OWASP** : Vulnérabilités des dépendances

---

## 🚦 Workflow de Développement

### 1. Créer une branche feature

```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

### 2. Développer et tester localement

```bash
# Formater le code
black app tests
isort app tests

# Lancer les tests
pytest tests/ -v

# Vérifier la couverture
pytest --cov=app --cov-report=term
```

### 3. Commit et push

```bash
git add .
git commit -m "feat: ajout de ma nouvelle fonctionnalité"
git push origin feature/ma-nouvelle-fonctionnalite
```

### 4. Créer une Pull Request

- Le CI se lance automatiquement
- Vérifiez que tous les checks passent ✅
- Demandez une revue de code

### 5. Merge et déploiement

- Merge vers `develop` → Déploiement automatique sur staging
- Merge vers `main` → Déploiement automatique sur production

---

## 📚 Ressources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SonarCloud Documentation](https://sonarcloud.io/documentation)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Codecov Documentation](https://docs.codecov.io/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🤝 Support

Pour toute question sur le CI/CD :

1. Consultez ce guide
2. Vérifiez les logs des workflows GitHub Actions
3. Consultez `TESTS_TROUBLESHOOTING.md` pour les problèmes de tests
4. Ouvrez une issue si le problème persiste

---

**✨ Pipeline CI/CD configuré et prêt à l'emploi !**
