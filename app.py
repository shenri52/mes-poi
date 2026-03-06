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
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/data"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return [f['name'] for f in r.json() if f['name'].endswith('.geojson')]
    return []

def api_github(file_path, data=None, sha=None, methode="GET"):
    full_path = f"data/{file_path}"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{full_path}"
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
        payload = {"message": "📍 Ajout POI", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        r = requests.put(url, json=payload, headers=headers)
        return r.status_code in [200, 201]
    elif methode == "DELETE":
        payload = {"message": f"🗑️ Suppression de {file_path}", "sha": sha, "branch": BRANCH}
        r = requests.delete(url, json=payload, headers=headers)
        return r.status_code == 200

# --- 3. INTERFACE ---
st.title("📍 GéoCollect de mes POI")

if 'clic' not in st.session_state: st.session_state.clic = None
if 'mode_selection' not in st.session_state: st.session_state.mode_selection = "Existant"
if 'last_created' not in st.session_state: st.session_state.last_created = None
if 'form_count' not in st.session_state: st.session_state.form_count = 0

st.subheader("🗺️ Couche")
modes = ["Existant", "Nouveau"]
idx_defaut = modes.index(st.session_state.mode_selection)

choice = st.radio("", modes, index=idx_defaut, horizontal=True)
st.session_state.mode_selection = choice

existing_data = None 
current_sha = None

if st.session_state.mode_selection == "Nouveau":
    nom_saisi = st.text_input("Nom du nouveau fichier (ex: velos)", "").strip()
    file_name = f"{nom_saisi}.geojson" if nom_saisi else None
else:
    liste_fichiers = lister_geojson_github()
    dict_affichage = {f: f.replace('.geojson', '') for f in liste_fichiers}
    
    idx_fichier = 0
    if st.session_state.last_created in liste_fichiers:
        idx_fichier = liste_fichiers.index(st.session_state.last_created)
    
    # --- MISE EN PAGE : LISTE + BOUTON SUPPRIMER ---
    col_list, col_del = st.columns([3, 1])
    
    with col_list:
        file_name = st.selectbox(
            "Choisir un jeu de donnée existant", 
            options=liste_fichiers, 
            format_func=lambda x: dict_affichage.get(x, x),
            index=idx_fichier,
            label_visibility="collapsed" # Optionnel: pour gagner de la place si besoin
        )
    
    with col_del:
        if file_name:
            existing_data, current_sha = api_github(file_name)
            if st.button("🗑️", use_container_width=True, help="Supprimer ce fichier"):
                if api_github(file_name, sha=current_sha, methode="DELETE"):
                    st.warning(f"Supprimé")
                    st.session_state.last_created = None
                    st.rerun()

st.write("---")
st.subheader("✍️ Saisie")
st.info("💡 Cliquer sur la carte pour indiquer la localisation.")

# --- CARTE ---
m = folium.Map(location=[46.6, 2.2], zoom_start=5)
LocateControl(auto_start=False).add_to(m)

if existing_data and "features" in existing_data:
    for feature in existing_data["features"]:
        coords = feature["geometry"]["coordinates"]
        prop = feature["properties"]
        folium.Marker(
            [coords[1], coords[0]], 
            popup=f"<b>{prop.get('libelle', 'Sans nom')}</b><br>Date: {prop.get('date', 'N/A')}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

if st.session_state.clic:
    folium.Marker([st.session_state.clic['lat'], st.session_state.clic['lng']], 
                  icon=folium.Icon(color="red", icon="star")).add_to(m)

donnees_carte = st_folium(m, width="100%", height=350)
if donnees_carte.get("last_clicked"):
    if st.session_state.clic != donnees_carte["last_clicked"]:
        st.session_state.clic = donnees_carte["last_clicked"]
        st.rerun()

# --- FORMULAIRE ---
libelle = st.text_input("Libellé du point", key=f"libelle_{st.session_state.form_count}")
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
            st.success("Enregistré !")
            if st.session_state.mode_selection == "Nouveau":
                st.session_state.last_created = file_name
                st.session_state.mode_selection = "Existant"
            st.session_state.clic = None
            st.session_state.form_count += 1
            st.rerun()
    else:
        st.error("Données manquantes.")
