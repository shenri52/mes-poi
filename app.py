import streamlit as st
import creation, ajout  # Vos futurs modules pour la logique métier

# --- CONFIGURATION ---
st.set_page_config(page_title="GéoCollect", page_icon="📍", layout="centered")

# --- INITIALISATION DE LA NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

def changer_page(nom):
    st.session_state.page = nom
    st.rerun()

# --- 1. MENU D'ACCUEIL ---
if st.session_state.page == 'accueil':
    st.markdown("<h1 style='text-align: center;'>📍 GéoCollect</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Gestionnaire de données géographiques (GeoJSON)</p>", unsafe_allow_html=True)
    st.write("---")

    # Bouton pour créer un nouveau fichier (nouveau jeu de données)
    if st.button("🏗️ Créer une nouvelle couche de POI", use_container_width=True):
        changer_page("creation")
    
    # Bouton pour alimenter un fichier existant
    if st.button("➕ Ajouter des données dans une couche existante", use_container_width=True):
        changer_page("ajouter")

# --- 2. ROUTAGE (CONTENU DES PAGES) ---
else:
    if st.session_state.page == "creation":
        st.subheader("🏗️ Création d'une nouvelle couche")
        creation.afficher() # Appelle la fonction dans creation.py
        
    elif st.session_state.page == "ajouter":
        st.subheader("➕ Ajout de points de données")
        ajout.afficher() # Appelle la fonction dans ajout.py

    # --- 3. BOUTON RETOUR ---
    st.write("---")
    if st.button("⬅️ Retour à l'accueil", use_container_width=True):
        changer_page('accueil')
