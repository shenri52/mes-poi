# 📍 GéoCollect

GéoCollect est une application web interactive développée avec **Streamlit** permettant de collecter, modifier et visualiser des points d'intérêt (POI) sur une carte. Les données sont stockées de manière persistante au format **GeoJSON** directement sur un dépôt GitHub.

## 🤖 Conception & IA
Ce projet a la particularité d'avoir été **entièrement développé à l'aide de l'IA Gemini** grâce à des **instructions précises et détaillées**. L'application a été structurée, codée et optimisée sans écriture manuelle de code.

## 🎯 But du projet
Simplifier la création et la collecte de données géographiques **à la volée**.

## ✨ Fonctionnalités

* **Sécurisation** : Accès protégé par mot de passe via les secrets Streamlit.
* **Cartographie Interactive** : Visualisation des points via Folium avec support du plein écran et de la géolocalisation.
* **Gestion de Couches** : Possibilité de créer de nouveaux fichiers GeoJSON en définissant une structure sur mesure (jusqu'à 10 champs personnalisables) pour s'adapter à tout type de collecte de données.
* **Édition en Temps Réel** : Ajouter, modifier le libellé ou supprimer des points par simple clic sur la carte.
* **Synchronisation GitHub** : Sauvegarde automatique des modifications sur votre dépôt via l'API GitHub.

## 🚀 Installation et Configuration

### 1. Prérequis
Vous devez disposer d'un compte GitHub et d'un jeton d'accès personnel (*** Fine-grained personal access tokens **) avec les permissions Read/Wrtie sur `Content `.

### 2. Configurer Streamlit Cloud
Pour fonctionner, l'application nécessite les secrets suivants (à configurer dans vos paramètres Streamlit Cloud) :

```toml
- APP_PASSWORD = "votre_mot_de_passe"
- GITHUB_TOKEN = "votre_token_github"
- REPO_OWNER = "votre_nom_utilisateur"
- REPO_NAME = "nom_du_depot"
- BRANCH = "main"
```
### 3. Arborescence du projet
```
├── app.py                # Fichier principal (Gestion du menu)
├── requirements.txt      # Liste des bibliothèques nécessaires
└── data                  # Dossier de stockage de geojson
  └── index.json          # Index pour recherche rapide
```
