import streamlit as st
import requests
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION & CONNEXIONS ---
load_dotenv()
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

# Centralisation des clés
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

# --- 🎯 INTERCEPTION DU CODE GOOGLE ---
query_params = st.query_params
if "code" in query_params and st.session_state.user is None:
    try:
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session.user
            st.query_params.clear()
            st.rerun()
    except:
        pass

# --- 2. FONCTIONS AUTHENTIFICATION ---
def login_with_google():
    # Détection Local vs Prod sans crash
    is_prod = "sportisimo.streamlit.app" in st.query_params or os.getenv("STREAMLIT_SERVER_PORT") is None
    redirect_url = "https://sportisimo.streamlit.app" if is_prod else "http://localhost:8501"

    try:
        return supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_url}
        })
    except:
        return None

def logout_user():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- 3. FONCTIONS TECHNIQUES ---
def formater_allure(secondes_totales):
    if secondes_totales <= 0: return "--:--"
    minutes = int(secondes_totales // 60)
    secondes = int(secondes_totales % 60)
    return f"{minutes}:{secondes:02d}"

# --- 4. DESIGN CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@700&display=swap');
    html, body, [data-testid="stWidgetLabel"], .stText, p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo-container { text-align: center; margin-top: -50px; margin-bottom: 20px; }
    .logo-sport { color: #28A5A8; font-size: 4.5rem; font-weight: 700; }
    .logo-simo { color: #F37B1F; font-size: 4.5rem; font-weight: 700; }
    .main-title { text-align: center; color: #F37B1F !important; font-size: 2.2rem; font-weight: 700; }
    div[data-testid="stLinkButton"] > a {
        background-color: #F37B1F !important; color: white !important; border-radius: 10px !important;
        padding: 10px 30px !important; text-decoration: none !important; display: inline-flex;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE D'AFFICHAGE ---
if st.session_state.user is None:
    st.markdown("<div class='logo-container'><span class='logo-sport'>Sporti</span><span class='logo-simo'>Simo</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='main-title'>Bienvenue sur SportiSimo</div>", unsafe_allow_html=True)
    
    auth_res = login_with_google()
    if auth_res:
        st.link_button("✨ Se connecter avec Google", auth_res.url)
else:
    # --- VÉRIFICATION / CRÉATION DU PROFIL ---
    user_id = st.session_state.user.id
    try:
        # On vérifie si la ligne existe dans ta table vide
        res = supabase.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
        profile = res.data

        if profile is None:
            # SI VIDE : On crée la ligne automatiquement
            new_profile = {"id": user_id, "email": st.session_state.user.email, "vma": 16.0}
            supabase.table("profiles").insert(new_profile).execute()
            profile = new_profile
            st.toast("Profil créé !")
    except Exception as e:
        st.error(f"Erreur Profil : {e}")
        profile = {"vma": 16.0}

    # --- DASHBOARD ---
    with st.sidebar:
        st.write(f"🏃 {st.session_state.user.email}")
        if st.button("Déconnexion"): logout_user()
        vma = st.slider("Ta VMA", 8.0, 22.0, float(profile.get('vma', 16.0)))

    st.title("🏃 Mon Dashboard")
    st.write("Bienvenue dans ton espace sportif !")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("70% (EF)", formater_allure((60/(vma*0.7))*60))
    c2.metric("85% (Seuil)", formater_allure((60/(vma*0.85))*60))
    c3.metric("100% (VMA)", formater_allure((60/vma)*60))