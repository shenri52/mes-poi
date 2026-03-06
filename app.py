import streamlit as st
import json
import requests
import base64
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl

# --- 1. CONFIGURATION ET SECRETS ---
st.set_page_config(page_title="GéoCollect de mes POI", page_icon="📍", layout="wide")

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_OWNER = st.secrets["REPO_OWNER"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = st.secrets.get("BRANCH", "main")
except KeyError:
    st.error("⚠️ Secrets GitHub manquants.")
    st.stop()

# --- 2. FONCTIONS GITHUB ---
def lister_geojson_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return [f['name'] for f in r.json() if f['name'].endswith('.geojson')]
    return []

def api_github(file_path, data=None, sha=None, methode="GET"):
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
        payload = {"message": f"📍 Ajout POI", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        return r.status_code in [200, 201]

# --- 3. INTERFACE ---
st.title("📍 GéoCollect de mes POI")

# Initialisation des états
if 'clic' not in st.session_state: st.session_state.clic = None
if 'mode_action' not in st.session_state: st.session_state.mode_action = "Existant"
if 'last_created' not in st.session_state: st.session_state.last_created = None

col_saisie, col_carte = st.columns([1, 2])

with col_saisie:
    st.subheader("📂 Sélection du jeu de données")
    st.session_state.mode_action = st.radio("Action", ["Existant", "Nouveau"], horizontal=True, key="radio_mode")
    
    if st.session_state.mode_action == "Nouveau":
        nom_saisi = st.text_input("Nom du nouveau fichier (ex: velos)", "").strip()
        file_name = f"{nom_saisi}.geojson" if nom_saisi else None
    else:
        liste_fichiers = lister_geojson_github()
        index_defaut = 0
        if st.session_state.last_created in liste_fichiers:
            index_defaut = liste_fichiers.index(st.session_state.last_created)
        
        file_name = st.selectbox("Choisir un fichier existant", liste_fichiers, index=index_defaut)

    st.write("---")
    st.subheader("✍️ Saisie")
    libelle = st.text_input("Libellé du point", key="input_libelle")
    date_du_jour = datetime.now().strftime("%Y-%m-%d")

    if st.session_state.clic:
        st.success(f"📍 {st.session_state.clic['lat']:.4f}, {st.session_state.clic['lng']:.4f}")
    
    if st.button("🚀 Sauvegarder", use_container_width=True):
        if file_name and libelle and st.session_state.clic:
            data, sha = api_github(file_name)
            if data is None:
                data = {"type": "FeatureCollection", "features": []}
            
            nouveau_poi = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [st.session_state.clic['lng'], st.session_state.clic['lat']]
                },
                "properties": {"libelle": libelle, "date": date_du_jour}
            }
            data['features'].append(nouveau_poi)
            
            if api_github(file_name, data=data, sha=sha, methode="PUT"):
                st.success("Enregistré sur GitHub !")
                # Logique de bascule après création
                if st.session_state.mode_action == "Nouveau":
                    st.session_state.last_created = file_name
                    st.session_state.mode_action = "Existant"
                
                st.session_state.clic = None
                st.rerun()
        else:
            st.error("Données manquantes (Fichier, Libellé ou Clic).")

with col_carte:
    m = folium.Map(location=[46.6, 2.2], zoom_start=5)
    # Bouton pour zoomer sur sa position
    LocateControl(auto_start=False).add_to(m)
    
    if st.session_state.clic:
        folium.Marker([st.session_state.clic['lat'], st.session_state.clic['lng']]).add_to(m)
    
    donnees_carte = st_folium(m, width="100%", height=500)
    if donnees_carte.get("last_clicked"):
        if st.session_state.clic != donnees_carte["last_clicked"]:
            st.session_state.clic = donnees_carte["last_clicked"]
            st.rerun()
