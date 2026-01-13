import streamlit as st
import requests
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION INITIALE ---
load_dotenv()
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

# Connexion Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

# --- 2. GESTION DE L'AUTHENTIFICATION ---
def handle_auth():
    """Gère la session et le retour de Google"""
    try:
        res = supabase.auth.get_session()
        if res and res.user:
            st.session_state.user = res.user
            if "code" in st.query_params:
                st.query_params.clear()
                st.rerun()
    except:
        pass

handle_auth()

def logout_user():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

@st.cache_resource
def get_google_auth_url():
    is_prod = "sportisimo.streamlit.app" in st.query_params or os.getenv("STREAMLIT_SERVER_PORT") is None
    redirect_url = "https://sportisimo.streamlit.app" if is_prod else "http://localhost:8501"
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": redirect_url}
    })
    return res.url if res else None

# --- 3. FONCTIONS UTILES ---
def formater_allure(secondes):
    if secondes <= 0: return "--:--"
    return f"{int(secondes//60)}:{int(secondes%60):02d}"

def ui_stat_card(label, value):
    st.markdown(f"""
        <div style="background: rgba(40,165,168,0.1); border-left: 4px solid #28A5A8; padding: 15px; border-radius: 10px; text-align: center; min-height: 110px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
            <div style="font-size: 0.8rem; color: #28A5A8; font-weight: bold; text-transform: uppercase;">{label}</div>
            <div style="font-size: 1.6rem; color: white; font-weight: 700;">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# CSS Global
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap');
    html, body, [data-testid="stWidgetLabel"], p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo-text { text-align: center; font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
    .stLinkButton a { background-color: #F37B1F !important; color: white !important; border-radius: 10px !important; padding: 0.8rem 2rem !important; text-decoration: none !important; display: block; text-align: center; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIQUE D'AFFICHAGE ---
if st.session_state.user is None:
    # PAGE DE CONNEXION
    st.markdown("<div class='logo-text'><span style='color:#28A5A8'>Sporti</span><span style='color:#F37B1F'>Simo</span></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        url = get_google_auth_url()
        if url:
            st.link_button("✨ Se connecter avec Google", url)
        st.divider()
        with st.expander("Connexion e-mail"):
            em = st.text_input("Email")
            pw = st.text_input("Mdp", type="password")
            if st.button("OK"):
                res = supabase.auth.sign_in_with_password({"email": em, "password": pw})
                if res.user:
                    st.session_state.user = res.user
                    st.rerun()
else:
    # APPLICATION CONNECTÉE
    user = st.session_state.user

    # Création auto du profil si la table est vide
    try:
        res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        profile = res_p.data
        if not profile:
            profile = {"id": user.id, "email": user.email, "vma": 16.0}
            supabase.table("profiles").insert(profile).execute()
    except:
        profile = {"vma": 16.0}

    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='color:#28A5A8'>SportiSimo</h2>", unsafe_allow_html=True)
        st.write(f"👤 {user.email}")
        if st.button("Déconnexion"): logout_user()
        st.divider()
        menu = st.radio("Navigation", ["🏃 Running", "🚴 Vélo"])
        st.divider()
        vma_actuelle = float(profile.get('vma', 16.0))
        vma = st.slider("Ta VMA", 8.0, 22.0, vma_actuelle)
        if vma != vma_actuelle:
            supabase.table("profiles").update({"vma": vma}).eq("id", user.id).execute()
            st.rerun()

    # Contenu
    if menu == "🏃 Running":
        st.title("🏃 Mes Allures")
        c1, c2, c3 = st.columns(3)
        with c1: ui_stat_card("EF (70%)", f"{formater_allure(3600/(vma*0.7))} /km")
        with c2: ui_stat_card("Seuil (85%)", f"{formater_allure(3600/(vma*0.85))} /km")
        with c3: ui_stat_card("VMA (100%)", f"{formater_allure(3600/vma)} /km")
    else:
        st.title("🚴 Mes Stats Vélo")
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1: ui_stat_card("Distance Totale", "1,245 km")
        with col_v2: ui_stat_card("Dénivelé", "8,450 m")
        with col_v3: ui_stat_card("Sortie Max", "102 km")
        with col_v4: ui_stat_card("Vitesse Moy", "28.5 km/h")