@echo off
REM Script de démarrage sans Docker pour Service Produits (Windows)
REM Ce script configure et lance l'application localement

echo ========================================
echo Demarrage du Service Produits (sans Docker)
echo ========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo Python installe: OK
echo.

REM Créer l'environnement virtuel s'il n'existe pas
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo Installation des dependances...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

REM Copier .env si nécessaire
if not exist ".env" (
    echo Copie du fichier .env.template vers .env...
    copy .env.template .env
    echo.
    echo IMPORTANT: Modifiez le fichier .env avec vos configurations
    echo.
)

echo.
echo ========================================
echo PREREQUIS:
echo   1. PostgreSQL doit etre installe et demarre
echo   2. RabbitMQ doit etre installe et demarre (optionnel)
echo   3. La base de donnees 'produits_db' doit etre creee
echo.
echo Pour creer la base de donnees PostgreSQL:
echo   createdb produits_db
echo.
echo Pour lancer les services:
echo   PostgreSQL: net start postgresql-x64-15
echo   RabbitMQ: net start RabbitMQ
echo ========================================
echo.

pause

REM Exécuter les migrations
echo.
echo Execution des migrations de base de donnees...
alembic upgrade head
if %errorlevel% neq 0 (
    echo ERREUR lors des migrations - verifiez votre configuration
    pause
)

REM Lancer l'application
echo.
echo ========================================
echo Demarrage de l'application...
echo ========================================
echo.
echo L'API sera accessible sur: http://localhost:8000
echo Documentation Swagger: http://localhost:8000/docs
echo Documentation ReDoc: http://localhost:8000/redoc
echo.
echo Pour arreter l'application, appuyez sur Ctrl+C
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
