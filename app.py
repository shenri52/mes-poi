import streamlit as st
import json
import requests
import base64
from datetime import datetime
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURATION ET SECRETS ---
st.set_page_config(page_title="GéoCollect Pro", page_icon="📍", layout="wide")

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_OWNER = st.secrets["REPO_OWNER"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = st.secrets.get("BRANCH", "main")
except KeyError:
    st.error("⚠️ Erreur : Paramètres GitHub manquants dans les Secrets Streamlit.")
    st.info("Vérifiez GITHUB_TOKEN, REPO_OWNER et REPO_NAME.")
    st.stop()

# --- 2. FONCTIONS DE COMMUNICATION GITHUB ---
def api_github(file_path, data=None, sha=None, methode="GET"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    if methode == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = json.loads(base64.b64decode(res['content']).decode('utf-8'))
            return content, res['sha']
        return None, None

    elif methode == "PUT":
        content_encoded = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
        payload = {
            "message": f"📍 GéoCollect : Ajout de point ({datetime.now().strftime('%d/%m %H:%M')})",
            "content": content_encoded,
            "branch": BRANCH
        }
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code not in [200, 201]:
            st.error(f"Erreur GitHub {r.status_code}: {r.json().get('message')}")
        return r.status_code in [200, 201]

# --- 3. INTERFACE UTILISATEUR ---
st.title("📍 GéoCollect GeoJSON")

# État du clic sur la carte
if 'clic' not in st.session_state:
    st.session_state.clic = None

col_saisie, col_carte = st.columns([1, 2])

with col_saisie:
    st.subheader("📁 Couche de données")
    
    mode = st.radio("Action", ["Choisir existante", "Créer nouvelle"], horizontal=True)
    
    if mode == "Créer nouvelle":
        nom_saisi = st.text_input("Nom du fichier (ex: stations_velo)", "").strip()
        desc_couche = st.text_area("Description de cette couche")
        file_name = f"{nom_saisi}.geojson" if nom_saisi else None
    else:
        file_name = st.text_input("Nom du fichier .geojson existant")
        desc_couche = "Mise à jour d'une couche existante"

    st.write("---")
    st.subheader("✍️ Nouveau Point")
    
    # Saisie des informations du point
    libelle = st.text_input("Libellé du point", key="input_libelle")
    date_du_jour = datetime.now().strftime("%Y-%m-%d")
    st.caption(f"📅 Date d'enregistrement : {date_du_jour}")

    # Coordonnées
    if st.session_state.clic:
        lat, lng = st.session_state.clic['lat'], st.session_state.clic['lng']
        st.success(f"Position : {lat:.5f} , {lng:.5f}")
    else:
        st.warning("👈 Cliquez sur la carte pour localiser le point")

    # BOUTON D'ENREGISTREMENT
    if st.button("🚀 Sauvegarder sur GitHub", use_container_width=True):
        if not file_name or not libelle or not st.session_state.clic:
            st.error("Formulaire incomplet (Fichier, Libellé ou Clic manquant).")
        else:
            with st.spinner("Synchronisation avec GitHub..."):
                # 1. Récupération des données existantes
                data, sha = api_github(file_name)
                
                # 2. Création de la structure si nouveau fichier
                if data is None:
                    data = {
                        "type": "FeatureCollection", 
                        "metadata": {"nom": file_name, "description": desc_couche},
                        "features": []
                    }
                
                # 3. Ajout du nouveau POI
                nouveau_poi = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [st.session_state.clic['lng'], st.session_state.clic['lat']]
                    },
                    "properties": {
                        "libelle": libelle,
                        "date": date_du_jour,
                        "auteur": "App GéoCollect"
                    }
                }
                data['features'].append(nouveau_poi)
                
                # 4. Envoi vers GitHub
                if api_github(file_name, data=data, sha=sha, methode="PUT"):
                    st.balloons()
                    st.success(f"Point ajouté avec succès dans {file_name} !")
                    # Reset
                    st.session_state.clic = None
                    st.rerun()

with col_carte:
    st.subheader("🗺️ Localisation interactive")
    
    # Centre la carte (France par défaut)
    m = folium.Map(location=[46.6, 2.2], zoom_start=5)
    
    # Affiche un marqueur là où l'utilisateur vient de cliquer
    if st.session_state.clic:
        folium.Marker(
            [st.session_state.clic['lat'], st.session_state.clic['lng']],
            icon=folium.Icon(color="red", icon="plus")
        ).add_to(m)

    # Rendu de la carte
    donnees_carte = st_folium(m, width="100%", height=600)

    # Mise à jour de l'état si clic détecté
    if donnees_carte.get("last_clicked"):
        if st.session_state.clic != donnees_carte["last_clicked"]:
            st.session_state.clic = donnees_carte["last_clicked"]
            st.rerun()def gestion_github(file_path, data=None, sha=None, methode="GET"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    if methode == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = json.loads(base64.b64decode(res['content']).decode('utf-8'))
            return content, res['sha']
        return None, None

    elif methode == "PUT":
        content_encoded = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
        payload = {"message": "Ajout POI", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        
        r = requests.put(url, json=payload, headers=headers)
        
        # --- LE DEBUG QUI SAUVE ---
        if r.status_code not in [200, 201]:
            st.error(f"Code Erreur GitHub : {r.status_code}")
            st.json(r.json()) # Affiche la raison exacte (ex: "Resource protected by organziation")
            
        return r.status_code in [200, 201]
