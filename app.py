import streamlit as st
import json
import requests
import base64
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Fullscreen

# --- 1. CONFIGURATION ET SECRETS ---
st.set_page_config(page_title="GéoCollect", page_icon="📍", layout="wide")

def verifier_mot_de_passe():
    if "authentifie" not in st.session_state:
        st.session_state["authentifie"] = False
    if not st.session_state["authentifie"]:
        st.markdown("<h1 style='text-align: center;'>🔒 Accès réservé</h1>", unsafe_allow_html=True)
        mdp_saisi = st.text_input("Veuillez saisir le mot de passe :", type="password")
        if st.button("Se connecter", use_container_width=True):
            if mdp_saisi == st.secrets["APP_PASSWORD"]:
                st.session_state["authentifie"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        return False
    return True

if not verifier_mot_de_passe():
    st.stop()

try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_OWNER = st.secrets["REPO_OWNER"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = st.secrets.get("BRANCH", "main")
except KeyError:
    st.error("⚠️ Secrets GitHub manquants.")
    st.stop()

# --- 2. LOGIQUE D'INDEXATION ---
def api_github_brut(file_path, data=None, sha=None, methode="GET"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    if methode == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            return json.loads(base64.b64decode(res['content']).decode('utf-8')), res['sha']
        return None, None
    elif methode == "PUT":
        content_encoded = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
        payload = {"message": f"🔄 Maj {file_path}", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        return requests.put(url, json=payload, headers=headers).status_code in [200, 201]

def gerer_index(ajouter=None, supprimer=None):
    index_file = "data/index.json"
    index_data, sha = api_github_brut(index_file)
    if index_data is None:
        url_scan = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/data"
        r = requests.get(url_scan, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        fichiers = [f['name'] for f in r.json() if f['name'].endswith('.geojson')] if r.status_code == 200 else []
        index_data = {"fichiers": fichiers}
        api_github_brut(index_file, data=index_data, methode="PUT")
        return fichiers
    liste = index_data.get("fichiers", [])
    maj = False
    if ajouter and ajouter not in liste:
        liste.append(ajouter); maj = True
    if supprimer and supprimer in liste:
        liste.remove(supprimer); maj = True
    if maj:
        index_data["fichiers"] = liste
        api_github_brut(index_file, data=index_data, sha=sha, methode="PUT")
    return liste

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
        payload = {"message": "📍 Modif POI", "content": content_encoded, "branch": BRANCH}
        if sha: payload["sha"] = sha
        return requests.put(url, json=payload, headers=headers).status_code in [200, 201]
    elif methode == "DELETE":
        payload = {"message": f"🗑️ Suppression de {file_path}", "sha": sha, "branch": BRANCH}
        return requests.delete(url, json=payload, headers=headers).status_code == 200

# --- 3. INITIALISATION ---
if 'clic' not in st.session_state: st.session_state.clic = None
if 'mode_selection' not in st.session_state: st.session_state.mode_selection = "Existant"
if 'last_created' not in st.session_state: st.session_state.last_created = None
if 'form_count' not in st.session_state: st.session_state.form_count = 0
if 'map_center' not in st.session_state: st.session_state.map_center = [46.6, 2.2]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 5
if 'edit_idx' not in st.session_state: st.session_state.edit_idx = None
if 'edit_label' not in st.session_state: st.session_state.edit_label = ""
if 'extra_fields' not in st.session_state: st.session_state.extra_fields = []

st.title("📍 GéoCollect")

# --- 4. SELECTION DE LA COUCHE ---
st.markdown("#### 🗺️ Couche")
modes = ["Existant", "Nouveau"]
choice = st.radio("", modes, index=modes.index(st.session_state.mode_selection), horizontal=True, label_visibility="collapsed")
st.session_state.mode_selection = choice

existing_data, current_sha, file_name = None, None, None

if st.session_state.mode_selection == "Nouveau":
    nom_saisi = st.text_input("Nom du nouveau fichier", "").strip()
    file_name = f"{nom_saisi}.geojson" if nom_saisi else None
else:
    liste_fichiers = gerer_index()
    dict_affichage = {f: f.replace('.geojson', '') for f in liste_fichiers}
    idx_fichier = 0
    if st.session_state.last_created in liste_fichiers:
        idx_fichier = liste_fichiers.index(st.session_state.last_created)
    
    col_list, col_del = st.columns([3, 1])
    with col_list:
        file_name = st.selectbox("Choisir", options=liste_fichiers, format_func=lambda x: dict_affichage.get(x, x), index=idx_fichier, label_visibility="collapsed")
    with col_del:
        if file_name:
            existing_data, current_sha = api_github(file_name)
            if st.button("🗑️", key="btn_del_file", use_container_width=True):
                if api_github(file_name, sha=current_sha, methode="DELETE"):
                    gerer_index(supprimer=file_name)
                    st.session_state.last_created = None
                    st.rerun()

st.write("---")

# --- 5. STYLE CSS ---
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    div[data-testid="stHtmlBlock"] + div { margin-top: -20px !important; }
    .element-container:has(iframe) { margin-top: -20px !important; margin-bottom: -20px !important; }
    div.stButton > button:first-child { margin-bottom: 1px !important; height: 38px; border-radius: 8px !important; }
    .valign { display: flex; align-items: center; height: 100%; padding-top: 8px; font-weight: bold; }
    .coord-box { background-color: rgba(212, 237, 218, 0.8); color: #155724; margin-top: 5px !important; margin-bottom: 5px !important; padding: 5px 8px; border-radius: 5px; font-size: 0.75em; border: 1px solid #c3e6cb; }
    </style>
""", unsafe_allow_html=True)

st.markdown("### ✍️ Saisir ou modifier")

col_h, _ = st.columns([1, 4])
with col_h:
    if st.button("🏠 Vue France", use_container_width=True):
        st.session_state.map_center = [46.6, 2.2]; st.session_state.map_zoom = 5
        st.session_state.clic = None; st.session_state.form_count += 1; st.rerun()

m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)
LocateControl(auto_start=False).add_to(m)
Fullscreen(position="topright", force_separate_button=True).add_to(m)

if existing_data and "features" in existing_data:
    for i, feature in enumerate(existing_data["features"]):
        coords = feature["geometry"]["coordinates"]
        nom_txt = str(feature["properties"].get('libelle', 'Sans nom')).replace('<b>', '').replace('</b>', '').split('<')[0]
        folium.Marker([coords[1], coords[0]], tooltip=nom_txt, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

if st.session_state.clic:
    folium.Marker([st.session_state.clic['lat'], st.session_state.clic['lng']], icon=folium.Icon(color="red", icon="star")).add_to(m)

donnees_carte = st_folium(m, width="100%", height=325, center=st.session_state.map_center, zoom=st.session_state.map_zoom, key=f"map_{st.session_state.form_count}")

# --- 6. LOGIQUE DE CLIC ---
if donnees_carte.get("last_object_clicked"):
    obj = donnees_carte["last_object_clicked"]
    st.session_state.map_center = [donnees_carte["center"]["lat"], donnees_carte["center"]["lng"]]
    st.session_state.map_zoom = donnees_carte["zoom"]
    if existing_data:
        for i, feat in enumerate(existing_data["features"]):
            coords = feat["geometry"]["coordinates"]
            if abs(coords[1] - obj["lat"]) < 0.0001 and abs(coords[0] - obj["lng"]) < 0.0001:
                if st.session_state.edit_idx != i:
                    st.session_state.edit_label = str(feat["properties"].get("libelle", "")).replace('<b>', '').replace('</b>', '').split('<')[0]
                    st.session_state.edit_idx = i
                    st.session_state.clic = {"lat": obj["lat"], "lng": obj["lng"]}
                    st.session_state[f"libelle_{st.session_state.form_count}"] = st.session_state.edit_label
                    st.rerun()

if donnees_carte.get("last_clicked") and not donnees_carte.get("last_object_clicked"):
    st.session_state.map_center = [donnees_carte["center"]["lat"], donnees_carte["center"]["lng"]]
    st.session_state.map_zoom = donnees_carte["zoom"]
    if st.session_state.clic != donnees_carte["last_clicked"]:
        st.session_state.clic = donnees_carte["last_clicked"]
        st.session_state.edit_idx = None
        st.session_state.edit_label = ""
        st.session_state[f"libelle_{st.session_state.form_count}"] = ""
        st.rerun()

# --- 7. FORMULAIRE & CHAMPS DYNAMIQUES ---
c_lab, c_inp, c_pts = st.columns([0.4, 5, 1.5])
with c_lab: st.markdown('<div class="valign">Libellé</div>', unsafe_allow_html=True)
with c_inp: 
    libelle = st.text_input("Libellé", key=f"libelle_{st.session_state.form_count}", label_visibility="collapsed")
    
    # AJOUT DYNAMIQUE (Uniquement en mode Nouveau)
    if st.session_state.mode_selection == "Nouveau":
        st.info(f"💡 {10 - len(st.session_state.extra_fields)} champs personnalisés disponibles.")
        for i, field in enumerate(st.session_state.extra_fields):
            col_k, col_v, col_d = st.columns([2, 3, 0.5])
            with col_k: field['key'] = st.text_input(f"Nom {i}", key=f"k_{i}_{st.session_state.form_count}", placeholder="Nom (ex: CP)", label_visibility="collapsed")
            with col_v: field['val'] = st.text_input(f"Val {i}", key=f"v_{i}_{st.session_state.form_count}", placeholder="Valeur", label_visibility="collapsed")
            with col_d: 
                if st.button("❌", key=f"del_{i}"):
                    st.session_state.extra_fields.pop(i); st.rerun()
        if len(st.session_state.extra_fields) < 10:
            if st.button(f"➕ Ajouter un champ ({10 - len(st.session_state.extra_fields)} restants)"):
                st.session_state.extra_fields.append({'key': '', 'val': ''}); st.rerun()

with c_pts:
    if st.session_state.clic:
        st.markdown(f'<div class="coord-box">📍 {st.session_state.clic["lat"]:.5f}, {st.session_state.clic["lng"]:.5f}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="coord-box" style="background-color: transparent; border: 1px dashed #ccc; color: #ccc;">Attente...</div>', unsafe_allow_html=True)

# --- 8. ACTIONS ---
if st.session_state.edit_idx is not None:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Modifier", use_container_width=True):
            data, sha = api_github(file_name)
            data["features"][st.session_state.edit_idx]["properties"]["libelle"] = libelle
            if api_github(file_name, data=data, sha=sha, methode="PUT"):
                st.session_state.clic = None; st.session_state.edit_idx = None; st.session_state.form_count += 1; st.rerun()
    with c2:
        if st.button("🗑️ Supprimer", use_container_width=True):
            data, sha = api_github(file_name)
            del data["features"][st.session_state.edit_idx]
            if api_github(file_name, data=data, sha=sha, methode="PUT"):
                st.session_state.clic = None; st.session_state.edit_idx = None; st.session_state.form_count += 1; st.rerun()
else:
    if st.button("🚀 Sauvegarder", use_container_width=True):
        if file_name and libelle and st.session_state.clic:
            # Récupération des champs bonus
            extra_props = {f['key'].strip(): f['val'].strip() for f in st.session_state.extra_fields if f['key'].strip()}
            data_save, sha_save = api_github(file_name)
            if data_save is None: data_save = {"type": "FeatureCollection", "features": []}
            nouveau_poi = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [st.session_state.clic['lng'], st.session_state.clic['lat']]},
                "properties": {"libelle": libelle, "date": datetime.now().strftime("%Y-%m-%d"), **extra_props}
            }
            data_save['features'].append(nouveau_poi)
            if api_github(file_name, data=data_save, sha=sha_save, methode="PUT"):
                gerer_index(ajouter=file_name)
                st.session_state.extra_fields = [] # Reset des champs bonus
                st.session_state.mode_selection = "Existant"; st.session_state.last_created = file_name
                st.session_state.clic = None; st.session_state.form_count += 1; st.rerun()
