# 📍 GéoCollect

GéoCollect est une application web interactive développée avec **Streamlit** permettant de collecter, modifier et visualiser des points d'intérêt (POI) sur une carte. Les données sont stockées de manière persistante au format **GeoJSON** directement sur un dépôt GitHub.

## ✨ Fonctionnalités

* **Sécurisation** : Accès protégé par mot de passe via les secrets Streamlit.
* **Cartographie Interactive** : Visualisation des points via Folium avec support du plein écran et de la géolocalisation.
* **Gestion de Couches** : Possibilité de créer de nouveaux fichiers GeoJSON ou de travailler sur des fichiers existants.
* **Édition en Temps Réel** : Ajouter, modifier le libellé ou supprimer des points par simple clic sur la carte.
* **Synchronisation GitHub** : Sauvegarde automatique des modifications sur votre dépôt via l'API GitHub.

## 🚀 Installation et Configuration

### 1. Prérequis
Vous devez disposer d'un compte GitHub et d'un jeton d'accès personnel (*** Fine-grained personal access tokens **) avec les permissions Read/Wrtie sur `Content `.

### 2. Structure du dépôt
L'application s'attend à trouver un dossier nommé `data` à la racine de votre dépôt pour y lire/écrire les fichiers `.geojson`.

### 3. Secrets Streamlit
Pour fonctionner, l'application nécessite les secrets suivants (à configurer dans vos paramètres Streamlit Cloud) :

- APP_PASSWORD = "votre_mot_de_passe"
- GITHUB_TOKEN = "votre_token_github"
- REPO_OWNER = "votre_nom_utilisateur"
- REPO_NAME = "nom_du_depot"
- BRANCH = "main"

## 📖 Utilisation

1.  **Connexion** : Saisissez le mot de passe pour accéder à l'interface.
2.  **Sélection** : Choisissez une couche existante (selectbox) ou créez-en une nouvelle.
3.  **Navigation** : Utilisez la carte pour zoomer sur votre zone d'intérêt. Le bouton **🏠 Vue France** permet de revenir à la vue globale.
4.  **Ajout d'un point** : 
    * Cliquez sur la carte (un marqueur rouge apparaît).
    * Saisissez le nom dans le champ **Libellé**.
    * Cliquez sur **🚀 Sauvegarder**.
5.  **Modification/Suppression** :
    * Cliquez sur un marqueur bleu existant.
    * Le libellé actuel s'affiche. Modifiez-le et cliquez sur **📝 Modifier**, ou utilisez **🗑️ Supprimer**.

---
*Développé pour la collecte simplifiée de données géographiques.*
