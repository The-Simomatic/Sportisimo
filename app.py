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
    """Capture la session et gère le retour Google/Email"""
    try:
        res = supabase.auth.get_session()
        if res and res.session:
            st.session_state.user = res.user
        
        # Nettoyage de l'URL si retour de login
        if st.session_state.user and "code" in st.query_params:
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
        "options": {"redirect_to": redirect_url, "skip_browser_redirect": False}
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
    st.markdown("<div class='logo-text'><span style='color:#28A5A8'>Sporti</span><span style='color:#F37B1F'>Simo</span></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        tab_log, tab_reg, tab_goo = st.tabs(["Connexion", "Créer un compte", "Google ✨"])
        
        with tab_log:
            e_log = st.text_input("Email", key="l_email").lower().strip()
            p_log = st.text_input("Mot de passe", type="password", key="l_pass")
            if st.button("Se connecter", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e_log, "password": p_log})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                except: st.error("Identifiants incorrects ou email non vérifié.")

        with tab_reg:
            st.write("### Rejoins la communauté")
            new_e = st.text_input("Ton Email", key="r_email").lower().strip()
            new_p = st.text_input("Ton Mot de passe", type="password", key="r_pass")
            
            col_a, col_b = st.columns(2)
            with col_a:
                prenom = st.text_input("Prénom")
                sexe = st.selectbox("Sexe", ["Homme", "Femme", "Autre"])
                poids = st.number_input("Poids (kg)", 30, 200, 75)
            with col_b:
                nom = st.text_input("Nom")
                date_n = st.date_input("Naissance", datetime.date(1990, 1, 1))
                sport = st.selectbox("Sport favori", ["Running", "Cyclisme", "VTT", "Trail"])
            
            niv = st.select_slider("Ton niveau actuel", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])
            
            if st.button("S'inscrire sur SportiSimo", use_container_width=True):
                try:
                    # Inscription avec stockage des infos en métadonnées
                    res = supabase.auth.sign_up({
                        "email": new_e, 
                        "password": new_p,
                        "options": {"data": {
                            "prenom": prenom, "nom": nom, "sexe": sexe, 
                            "poids": poids, "sport_pref": sport, "niveau": niv, "date_n": str(date_n)
                        }}
                    })
                    if res.user:
                        st.success("### 📧 Mail envoyé !")
                        st.info(f"Vérifie la boîte `{new_e}` pour valider ton inscription.")
                        if st.button("C'est fait ! Me connecter", use_container_width=True):
                            st.rerun()
                except Exception as e: st.error(f"Oups : {e}")

        with tab_goo:
            g_url = get_google_auth_url()
            if g_url: st.link_button("🚀 Continuer avec Google", g_url, use_container_width=True)

else:
    # --- PAGE CONNECTÉ ---
    user = st.session_state.user
    
    # Récupération / Création du profil (Sync après confirmation email)
    res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
    prof = res_p.data
    
    if not prof:
        # Première connexion détectée !
        st.balloons()
        meta = user.user_metadata
        prof_data = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "sexe": meta.get("sexe", "Autre"),
            "poids": meta.get("poids", 70),
            "sport_pref": meta.get("sport_pref", "Running"),
            "niveau": meta.get("niveau", "Intermédiaire"),
            "statut": "gratuit",
            "vma": 16.0,
            "date_naissance": meta.get("date_n")
        }
        supabase.table("profiles").insert(prof_data).execute()
        st.toast(f"Profil créé ! Bienvenue {prof_data['prenom']} !")
        st.rerun()

    # Sidebar
    with st.sidebar:
        st.markdown(f"## Salut {prof.get('prenom')} ! 👋")
        st.write(f"Plan actuel : **{prof.get('statut', 'gratuit').upper()}**")
        if st.button("Se déconnecter", use_container_width=True): logout_user()
        st.divider()
        menu = st.radio("Navigation", ["🏃 Running", "🚴 Cyclisme", "⚙️ Paramètres"])

    # Contenu des pages
    if menu == "🏃 Running":
        st.title("🏃 Mes Allures Running")
        vma = prof.get('vma', 16.0)
        c1, c2, c3 = st.columns(3)
        with c1: ui_stat_card("Endurance (70%)", f"{int(3600/(vma*0.7)//60)}:{int(3600/(vma*0.7)%60):02d} /km")
        with c2: ui_stat_card("Seuil (85%)", f"{int(3600/(vma*0.85)//60)}:{int(3600/(vma*0.85)%60):02d} /km")
        with c3: ui_stat_card("VMA (100%)", f"{int(3600/vma//60)}:{int(3600/vma%60):02d} /km")
        
    elif menu == "🚴 Cyclisme":
        st.title("🚴 Mon Dashboard Vélo")
        st.info("Bientôt : Connecte ton Strava pour voir tes records personnels.")
        
    elif menu == "⚙️ Paramètres":
        st.title("⚙️ Réglages Profil")
        with st.form("update_profile"):
            new_vma = st.slider("Ta VMA (km/h)", 8.0, 22.0, float(prof.get('vma', 16.0)))
            new_poids = st.number_input("Poids (kg)", 30, 200, int(prof.get('poids', 70)))
            if st.form_submit_button("Sauvegarder les modifications"):
                supabase.table("profiles").update({"vma": new_vma, "poids": new_poids}).eq("id", user.id).execute()
                st.success("Profil mis à jour !")
                st.rerun()