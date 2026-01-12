import streamlit as st
import requests
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION & CONNEXIONS ---
load_dotenv()

st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

# Centralisation des clés (Local via .env ou Cloud via Secrets)
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 🔄 GESTION DE LA SESSION ---
if "user" not in st.session_state:
    st.session_state.user = None

# Fonction de vérification améliorée
def check_auth_status():
    # On vérifie si Supabase a une session active
    try:
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session.user
            return True
    except:
        pass
    
    # ASTUCE : Si on revient de Google, l'URL contient des paramètres
    # On force une petite pause ou un rafraîchissement interne si nécessaire
    if "access_token" in st.query_params or "id_token" in st.query_params:
        try:
            user = supabase.auth.get_user()
            if user:
                st.session_state.user = user
                return True
        except:
            pass
    return False

# On exécute la vérification au tout début du script
check_auth_status()

# --- 2. FONCTIONS AUTHENTIFICATION ---
def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.rerun()
    except:
        st.error("Identifiants incorrects.")

def signup_user(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "email": email}).execute()
            st.info("Vérifie tes emails pour confirmer l'inscription !")
    except Exception as e:
        st.error(f"Erreur : {e}")

def logout_user():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

def login_with_google():
    # Détection si on est sur Streamlit Cloud ou en local
    # On utilise l'URL de l'app si possible, sinon localhost
    is_prod = False
    try:
        if st.secrets.get("SUPABASE_URL"):
            is_prod = True
    except:
        pass

    redirect_url = "https://sportisimo.streamlit.app" if is_prod else "http://localhost:8501"

    try:
        return supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
    except Exception as e:
        return None

# --- 3. FONCTIONS TECHNIQUES STRAVA ---
def get_new_access_token(refresh_token):
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': os.getenv("STRAVA_CLIENT_ID"),
        'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post(url, data=payload)
        return response.json().get('access_token') if response.status_code == 200 else None
    except: return None

@st.cache_data(ttl=300)
def get_strava_data(refresh_token):
    token = get_new_access_token(refresh_token)
    if not token: return None
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params={'per_page': 5})
        return response.json() if response.status_code == 200 else None
    except: return None

def formater_allure(secondes_totales):
    if secondes_totales <= 0: return "--:--"
    minutes = int(secondes_totales // 60)
    secondes = int(secondes_totales % 60)
    return f"{minutes}:{secondes:02d}"

# --- 4. DESIGN CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@700&display=swap');
    
    html, body, [data-testid="stWidgetLabel"], .stText, p, span { 
        color: #E5E5E5 !important; 
        font-family: 'Ubuntu', sans-serif; 
    }

    .logo-container { text-align: center; margin-top: -50px; margin-bottom: 20px; }
    .logo-sport { color: #28A5A8; font-size: 4.5rem; font-weight: 700; }
    .logo-simo { color: #F37B1F; font-size: 4.5rem; font-weight: 700; }

    .main-title { text-align: center; color: #F37B1F !important; font-size: 2.2rem; font-weight: 700; margin-bottom: 30px; }
    .sub-title { color: #28A5A8 !important; font-size: 1.8rem; font-weight: 700; margin-top: 25px; }

    div[data-testid="stFormSubmitButton"] > button, 
    div[data-testid="stLinkButton"] > a {
        background-color: #F37B1F !important; 
        color: white !important; 
        border-radius: 10px !important; 
        border: none !important; 
        font-weight: bold !important; 
        width: auto !important; 
        padding: 10px 30px !important;
        height: 3rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        transition: 0.3s ease all !important;
    }

    button[data-baseweb="tab"] { background-color: transparent !important; border: none !important; color: #888 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #F37B1F !important; border-bottom: 3px solid #F37B1F !important; }
</style>
""", unsafe_allow_html=True)

def logo():
    st.markdown("<div class='logo-container'><span class='logo-sport'>Sporti</span><span class='logo-simo'>Simo</span></div>", unsafe_allow_html=True)

def titre(texte):
    st.markdown(f"<div class='main-title'>{texte}</div>", unsafe_allow_html=True)

def sous_titre(texte):
    st.markdown(f"<div class='sub-title'>{texte}</div>", unsafe_allow_html=True)

# --- 5. LOGIQUE D'AFFICHAGE ---

if st.session_state.user is None:
    logo()
    titre("Bienvenue sur SportiSimo")

    google_url = None
    auth_res = login_with_google()
    if auth_res:
        google_url = auth_res.url

    tab1, tab2 = st.tabs(["🔒 Connexion", "📝 Créer un compte"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                login_user(email, pw)
        
        if google_url:
            st.link_button("✨ Se connecter avec Google", google_url)
        
        if st.button("Mot de passe oublié ?", key="forgot_password"):
            if email:
                supabase.auth.reset_password_for_email(email)
                st.success("Lien envoyé !")
            else:
                st.warning("Indique ton email.")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_pw = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("S'inscrire par Email"):
                signup_user(new_email, new_pw)
        
        st.divider()
        if google_url:
            st.link_button("✨ S'inscrire avec Google", google_url)

else:
    # --- APPLICATION CONNECTÉE ---
    try:
        profile_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
        profile = profile_res.data
    except:
        profile = None

    refresh_token = profile.get("strava_refresh_token") if profile else None

    with st.sidebar:
        logo()
        st.write(f"🏃 {st.session_state.user.email}")
        if st.button("Se déconnecter", key="logout_sidebar"):
            logout_user()
        st.divider()
        menu = st.radio("Navigation", ["Mon Dashboard", "Mon CV Sportif"])
        st.divider()
        vma_default = profile.get("vma", 16.0) if profile else 16.0
        vma = st.slider("Ta VMA (km/h)", 8.0, 22.0, float(vma_default))

    if not refresh_token:
        titre("Bienvenue !")
        st.info("Pour commencer, connectez votre compte Strava.")
        if st.button("🔗 Lier mon compte Strava"):
            # Logique Strava à venir
            pass
    else:
        if menu == "Mon Dashboard":
            titre("🏃 Tableau de Bord")
            activities = get_strava_data(refresh_token)
            if activities:
                sous_titre("📊 Dernières Séances")
                for act in activities[:3]:
                    date_p = datetime.datetime.strptime(act['start_date_local'][:10], "%Y-%m-%d").strftime("%d/%m")
                    st.info(f"**{act['name']}** | {act['distance']/1000:.2f}km | {date_p}")
            
            st.divider()
            sous_titre("⏱️ Tes Allures")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("70% (EF)", formater_allure((60/(vma*0.7))*60))
            with c2: st.metric("85% (Seuil)", formater_allure((60/(vma*0.85))*60))
            with c3: st.metric("100% (VMA)", formater_allure((60/vma)*60))