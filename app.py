import streamlit as st
import requests
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION INITIALE ---
load_dotenv()
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

# Connexion Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 🔄 GESTION RIGOUREUSE DE LA SESSION ---
if "user" not in st.session_state:
    st.session_state.user = None

def handle_auth():
    """Gère l'échange de code Google et la récupération de session"""
    # Étape A : Si on voit un 'code' dans l'URL (retour de Google)
    if "code" in st.query_params:
        try:
            auth_code = st.query_params.get("code")
            # C'est ici que la magie opère : on échange le code contre la session
            res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            if res.user:
                st.session_state.user = res.user
                st.query_params.clear() # On nettoie l'URL
                st.rerun()
        except Exception as e:
            st.error(f"Erreur d'échange de code : {e}")

    # Étape B : Si pas de code, on vérifie si une session existe déjà
    if st.session_state.user is None:
        try:
            res = supabase.auth.get_session()
            if res and res.user:
                st.session_state.user = res.user
        except:
            pass

# Lancement de la vérification au démarrage
handle_auth()

# --- 2. FONCTIONS D'ACCÈS ---
def logout_user():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

@st.cache_resource
def get_google_auth_url():
    """Génère l'URL Google pour l'authentification PKCE"""
    is_prod = "sportisimo.streamlit.app" in st.query_params or os.getenv("STREAMLIT_SERVER_PORT") is None
    redirect_url = "https://sportisimo.streamlit.app" if is_prod else "http://localhost:8501"
    
    # Utilisation du flux PKCE (plus sûr pour Streamlit)
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": redirect_url,
            "skip_browser_redirect": True # Très important pour les boutons Streamlit
        }
    })
    return res.url if res else None

# --- 3. FONCTIONS TECHNIQUES ---
def get_new_access_token(refresh_token):
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': os.getenv("STRAVA_CLIENT_ID"),
        'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    try:
        r = requests.post(url, data=payload)
        return r.json().get('access_token') if r.status_code == 200 else None
    except: return None

def ui_stat_card(label, value):
    st.markdown(f"""
        <div style="background: rgba(40,165,168,0.1); border-left: 4px solid #28A5A8; padding: 15px; border-radius: 10px; text-align: center; min-height: 100px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.8rem; color: #28A5A8; font-weight: bold; text-transform: uppercase;">{label}</div>
            <div style="font-size: 1.5rem; color: white; font-weight: 700;">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. DESIGN ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap');
    html, body, [data-testid="stWidgetLabel"], p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo { text-align: center; font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
    .stLinkButton a { background-color: #F37B1F !important; color: white !important; border-radius: 10px !important; padding: 0.5rem 2rem !important; text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE D'AFFICHAGE ---
if st.session_state.user is None:
    # --- PAGE DE CONNEXION ---
    st.markdown("<div class='logo'><span style='color:#28A5A8'>Sporti</span><span style='color:#F37B1F'>Simo</span></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align:center;'>Connexion</h3>", unsafe_allow_html=True)
        
        # On récupère l'URL Google
        google_url = get_google_auth_url()
        if google_url:
            st.link_button("✨ Se connecter avec Google", google_url, use_container_width=True)
        
        st.divider()
        with st.expander("Ou utiliser un compte par e-mail"):
            email = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                except:
                    st.error("Identifiants incorrects")

else:
    # --- APPLICATION CONNECTÉE ---
    user_id = st.session_state.user.id
    
    # Récupération du profil
    try:
        res = supabase.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
        profile = res.data
        if profile is None:
            # Création auto si manquant
            new_prof = {"id": user_id, "email": st.session_state.user.email, "vma": 16.0}
            supabase.table("profiles").insert(new_prof).execute()
            profile = new_prof
    except:
        profile = {"vma": 16.0}

    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='text-align:center; color:#28A5A8;'>SportiSimo</h2>", unsafe_allow_html=True)
        st.write(f"🏃 {st.session_state.user.email}")
        if st.button("Se déconnecter"): logout_user()
        st.divider()
        menu = st.radio("Navigation", ["Mon Dashboard", "Mes Stats Vélo"])
        st.divider()
        vma = st.sidebar.slider("Ta VMA (km/h)", 8.0, 22.0, float(profile.get('vma', 16.0)))
        # Mise à jour VMA en base si elle change
        if vma != profile.get('vma'):
            supabase.table("profiles").update({"vma": vma}).eq("id", user_id).execute()

    # --- CONTENU ---
    refresh_token = profile.get("strava_refresh_token")

    if not refresh_token:
        st.title("Bienvenue !")
        st.info("Liez votre compte Strava dans les paramètres pour voir vos données.")
    else:
        token = get_new_access_token(refresh_token)
        
        if menu == "Mon Dashboard":
            st.markdown(f"<div class='main-title'>🏃 Mon Dashboard</div>", unsafe_allow_html=True)
            
            # Allures de course
            st.markdown("<div class='sub-title'>⏱️ Tes Allures de Travail</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: ui_stat_card("70% (EF)", formater_allure((60/(vma*0.7))*60) + " /km")
            with c2: ui_stat_card("85% (Seuil)", formater_allure((60/(vma*0.85))*60) + " /km")
            with c3: ui_stat_card("100% (VMA)", formater_allure((60/vma)*60) + " /km")

            # Dernières activités
            activites = get_strava_activities(token)
            if activites:
                st.markdown("<div class='sub-title'>📊 Dernières Activités</div>", unsafe_allow_html=True)
                for act in activites[:3]:
                    date_p = datetime.datetime.strptime(act['start_date_local'][:10], "%Y-%m-%d").strftime("%d/%m")
                    st.info(f"**{act['name']}** | {act['distance']/1000:.2f}km | {date_p}")

        elif menu == "Mes Stats Vélo":
            st.markdown(f"<div class='main-title'>🚴 Mon Profil Cycliste</div>", unsafe_allow_html=True)
            
            stats = get_strava_stats(profile.get("strava_id"), token)
            activites = get_strava_activities(token)

            if stats and activites:
                bike = stats.get('ytd_ride_totals', {})
                db_km = bike.get('distance', 0) / 1000
                tb_sec = bike.get('moving_time', 0)

                # 1. Stats Annuelles
                st.markdown("<div class='sub-title'>📅 Bilan Annuel</div>", unsafe_allow_html=True)
                b1, b2, b3, b4 = st.columns(4)
                with b1: ui_stat_card("Distance", f"{db_km:.1f} km")
                with b2: ui_stat_card("Sorties", f"{bike.get('count', 0)}")
                with b3: ui_stat_card("Durée", f"{tb_sec // 3600}h")
                with b4:
                    vit_an = db_km / (tb_sec / 3600) if tb_sec > 0 else 0
                    ui_stat_card("Vit. Moy", f"{vit_an:.1f} km/h")

                st.divider()
                st.markdown("<div class='sub-title'>🏆 Records (12 mois)</div>", unsafe_allow_html=True)

                # 2. Logique Records
                rides = [a for a in activites if a['type'] in ['Ride', 'MountainBikeRide']]
                if rides:
                    max_dist = max(rides, key=lambda x: x['distance'])['distance'] / 1000
                    
                    total_sec_rec = max(rides, key=lambda x: x['moving_time'])['moving_time']
                    duree_rec = f"{total_sec_rec // 3600}h {(total_sec_rec % 3600) // 60:02d}"
                    
                    max_deniv = max(rides, key=lambda x: x.get('total_elevation_gain', 0))['total_elevation_gain']
                    
                    # Vitesse max sur sortie > 10km
                    potents = [r for r in rides if r['distance'] > 10000]
                    vit_top = 0
                    if potents:
                        max_v_obj = max(potents, key=lambda x: x['distance'] / x['moving_time'])
                        vit_top = (max_v_obj['distance'] / max_v_obj['moving_time']) * 3.6

                    r1, r2, r3, r4 = st.columns(4)
                    with r1: ui_stat_card("Plus Longue", f"{max_dist:.1f} km")
                    with r2: ui_stat_card("Plus Durable", duree_rec)
                    with r3: ui_stat_card("Max D+", f"{max_deniv:.0f} m")
                    with r4: ui_stat_card("Vitesse Top", f"{vit_top:.1f} km/h")
                else:
                    st.info("Aucune donnée vélo trouvée.")