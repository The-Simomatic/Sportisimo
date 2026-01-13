import streamlit as st
import requests
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

# Connexion Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

# --- 2. LOGIQUE D'AUTHENTIFICATION ---
def handle_auth():
    """Vérifie la session au chargement (Google & Email)"""
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

# --- 3. COMPOSANTS UI ---
def ui_stat_card(label, value):
    st.markdown(f"""
        <div style="background: rgba(40,165,168,0.1); border-left: 4px solid #28A5A8; padding: 15px; border-radius: 10px; text-align: center; min-height: 110px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
            <div style="font-size: 0.8rem; color: #28A5A8; font-weight: bold; text-transform: uppercase;">{label}</div>
            <div style="font-size: 1.6rem; color: white; font-weight: 700;">{value}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap');
    html, body, [data-testid="stWidgetLabel"], p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo-text { text-align: center; font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
    .stLinkButton a { background-color: #F37B1F !important; color: white !important; border-radius: 10px !important; padding: 0.8rem 2rem !important; text-decoration: none !important; display: block; text-align: center; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. AFFICHAGE PRINCIPAL ---
if st.session_state.user is None:
    # --- PAGE NON CONNECTÉ ---
    st.markdown("<div class='logo-text'><span style='color:#28A5A8'>Sporti</span><span style='color:#F37B1F'>Simo</span></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        tab1, tab2, tab3 = st.tabs(["Connexion", "Créer un compte", "Google ✨"])
        
        with tab1:
            e_log = st.text_input("Email", key="l_email")
            p_log = st.text_input("Mot de passe", type="password", key="l_pass")
            if st.button("Se connecter", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e_log, "password": p_log})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                except: st.error("Identifiants incorrects.")

        with tab2:
            st.write("### Rejoins l'aventure")
            new_e = st.text_input("Email", key="r_email")
            new_p = st.text_input("Mot de passe", type="password", key="r_pass")
            col_a, col_b = st.columns(2)
            with col_a:
                prenom = st.text_input("Prénom")
                sexe = st.selectbox("Sexe", ["Homme", "Femme", "Autre"])
                poids = st.number_input("Poids (kg)", 30, 200, 70)
            with col_b:
                nom = st.text_input("Nom")
                date_n = st.date_input("Naissance", datetime.date(1990, 1, 1))
                sport = st.selectbox("Sport favori", ["Running", "Cyclisme", "Trail", "VTT"])
            
            niv = st.select_slider("Niveau", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])
            
            if st.button("S'inscrire", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": new_e, "password": new_p})
                    if res.user:
                        supabase.table("profiles").insert({
                            "id": res.user.id, "email": new_e, "nom": nom, "prenom": prenom,
                            "sexe": sexe, "poids": poids, "date_naissance": str(date_n),
                            "sport_pref": sport, "niveau": niv, "statut": "gratuit", "vma": 16.0
                        }).execute()
                        st.success("Compte créé ! Connecte-toi maintenant.")
                except Exception as e: st.error(f"Erreur: {e}")

        with tab3:
            g_url = get_google_auth_url()
            if g_url: st.link_button("🚀 Continuer avec Google", g_url)

else:
    # --- PAGE CONNECTÉ ---
    user = st.session_state.user
    
    # Récupération profil
    try:
        res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        prof = res_p.data
        if not prof: # Cas d'un premier login Google sans profil créé
            prof = {"id": user.id, "email": user.email, "vma": 16.0, "statut": "gratuit", "prenom": "Nouvel adepte"}
            supabase.table("profiles").insert(prof).execute()
    except: prof = {"vma": 16.0, "prenom": "Sportif", "statut": "gratuit"}

    # Sidebar
    with st.sidebar:
        st.markdown(f"### Bienvenue {prof.get('prenom', 'Sportif')} !")
        st.write(f"Plan : **{prof.get('statut', 'gratuit').upper()}**")
        if st.button("Déconnexion"): logout_user()
        st.divider()
        menu = st.radio("Aller vers :", ["🏃 Dashboard Running", "🚴 Stats Vélo", "⚙️ Paramètres"])

    # Contenu
    if menu == "🏃 Dashboard Running":
        st.title("🏃 Mes Performances Running")
        vma = prof.get('vma', 16.0)
        c1, c2, c3 = st.columns(3)
        with c1: ui_stat_card("EF (70%)", f"{int(3600/(vma*0.7)//60)}:{int(3600/(vma*0.7)%60):02d} /km")
        with c2: ui_stat_card("Seuil (85%)", f"{int(3600/(vma*0.85)//60)}:{int(3600/(vma*0.85)%60):02d} /km")
        with c3: ui_stat_card("VMA (100%)", f"{int(3600/vma//60)}:{int(3600/vma%60):02d} /km")
        
    elif menu == "🚴 Stats Vélo":
        st.title("🚴 Mon Profil Cyclisme")
        st.info("Données Strava bientôt disponibles...")
        
    elif menu == "⚙️ Paramètres":
        st.title("⚙️ Mes Réglages")
        vma_val = st.slider("Ajuster ma VMA", 8.0, 22.0, float(prof.get('vma', 16.0)))
        if st.button("Sauvegarder ma nouvelle VMA"):
            supabase.table("profiles").update({"vma": vma_val}).eq("id", user.id).execute()
            st.success("VMA mise à jour !")
            st.rerun()