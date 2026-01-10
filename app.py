import streamlit as st
import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- FONCTIONS TECHNIQUES ---
def get_new_access_token():
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': os.getenv("STRAVA_CLIENT_ID"),
        'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
        'refresh_token': os.getenv("STRAVA_REFRESH_TOKEN"),
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post(url, data=payload)
        return response.json().get('access_token') if response.status_code == 200 else None
    except: return None

@st.cache_data(ttl=300)
def get_strava_data():
    token = get_new_access_token()
    if not token: return None
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(url, headers=headers, params={'per_page': 2})
        return response.json() if response.status_code == 200 else None
    except: return None

def formater_allure(secondes_totales):
    if secondes_totales <= 0:
        return "--:--"
    minutes = int(secondes_totales // 60)
    secondes = int(secondes_totales % 60)
    return f"{minutes}:{secondes:02d}"

@st.cache_data(ttl=1800)
def get_athlete_stats():
    token = get_new_access_token()
    if not token: return None
    # L'ID 5476825 semble être le tien d'après tes messages précédents
    athlete_id = "5476825" 
    url = f"https://www.strava.com/api/v3/athletes/{athlete_id}/stats"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=3600) # Garde les données en mémoire 1 heure
def get_activites_un_an():
    token = get_new_access_token()
    if not token:
        return None
        
    # Date d'il y a 365 jours
    il_y_a_un_an = int((datetime.datetime.now() - datetime.timedelta(days=365)).timestamp())
    
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {token}'}
    # On récupère les 200 dernières activités en une seule fois
    params = {'after': il_y_a_un_an, 'per_page': 200}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# --- DESIGN (CSS) ---
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@700&display=swap');
    html, body, [data-testid="stWidgetLabel"], .stText, p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo-container { line-height: 0.9; margin-bottom: 25px; }
    .logo-sport { color: #28A5A8 !important; font-size: 3.2rem; font-weight: 700; display: block; }
    .logo-simo { color: #F37B1F !important; font-size: 3.2rem; font-weight: 700; display: block; }
    .stButton>button { background-color: #F37B1F !important; color: white !important; border-radius: 10px !important; border: none !important; font-weight: bold !important; width: 100%; transition: 0.3s ease; }
    .stButton>button:hover { background-color: #28A5A8 !important; }
    .main-title { color: #F37B1F !important; font-size: 2.8rem; font-weight: 700; margin-bottom: 10px; }
    .sub-title { color: #28A5A8 !important; font-size: 1.8rem; font-weight: 700; margin-top: 25px; margin-bottom: 10px; }
    [data-testid="stNotification"] { background-color: rgba(255, 255, 255, 0.05) !important; border: 1px solid #28A5A8 !important; }
    @media (max-width: 640px) { .logo-sport, .logo-simo { font-size: 2.2rem; } .main-title { font-size: 1.8rem !important; text-align: center; } }
</style>
""", unsafe_allow_html=True)

def logo():
    st.markdown("<div class='logo-container'><span class='logo-sport'>Sporti</span><span class='logo-simo'>Simo</span></div>", unsafe_allow_html=True)

def titre(texte):
    st.markdown(f"<div class='main-title'>{texte}</div>", unsafe_allow_html=True)

def sous_titre(texte):
    st.markdown(f"<div class='sub-title'>{texte}</div>", unsafe_allow_html=True)

# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    logo()
    # Ajout du menu de navigation
    # Section Objectif
    st.divider()
    st.markdown("""
        <div style='text-align: center; border: 1px solid #F37B1F; padding: 10px; border-radius: 10px;'>
            <span style='color: #E5E5E5; font-size: 0.9rem; display: block;'>OBJECTIF :</span>
            <span style='color: #F37B1F; font-size: 1.4rem; font-weight: bold;'>MARATHON</span>
            <span style='color: #28A5A8; font-size: 1.6rem; font-weight: bold; display: block;'>2h59'59"</span>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Navigation", ["Mon Dashboard", "Mon CV Sportif"])
    st.divider()
    vma = st.slider("Ta VMA (km/h)", 8.0, 22.0, 16.0, 0.5)
    st.divider()
    if st.button("🔄 Actualiser Strava"):
        st.rerun()
    

# --- LOGIQUE D'AFFICHAGE ---
if menu == "Mon Dashboard":
    titre("🏃 Tableau de Bord")

# 1. DERNIÈRES SÉANCES
    sous_titre("📊 Dernières Séances (Strava)")
    activities = get_strava_data()
    
    if activities:
        for act in activities:
            # Icône selon le sport
            icon = "🏃" if act['type'] == 'Run' else "🚲"
            
            # Formatage de la date (ex: 2026-01-10 -> 10/01)
            date_brute = act['start_date_local'][:10] # On prend les 10 premiers caractères
            date_objet = datetime.datetime.strptime(date_brute, "%Y-%m-%d")
            date_propre = date_objet.strftime("%d/%m")
            
            # Affichage
            st.info(f"{icon} **{act['name']}**")
            # Ajout de la date à la fin de la ligne
            st.write(f"📏 {act['distance']/1000:.2f} km | ⏱️ {act['moving_time']//60} min | 📅 {date_propre}")
    else:
        st.warning("Connexion Strava en cours...")

    st.divider()

    # 2. PROCHAINE SÉANCE
    sous_titre("🎯 Prochaine Séance")
    st.info("📅 **Demain** : Séance de seuil - 3 x 2000m")
    if st.button("📅 Accéder à mon plan d'entrainement"):
        st.toast("Redirection vers le plan...")

    st.divider()

# 3. RAPPEL DES ALLURES
    sous_titre("⏱️ Rappel de tes Allures")
    st.write(f"Basé sur une VMA de **{vma} km/h**")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        ae = (60 / (vma * 0.7)) * 60
        st.info(f"**70% (EF)** \n### {formater_allure(ae)}")
        
    with c2:
        as_ = (60 / (vma * 0.85)) * 60
        st.info(f"**85% (Seuil)** \n### {formater_allure(as_)}")
        
    with c3:
        av = (60 / vma) * 60
        st.info(f"**100% (VMA)** \n### {formater_allure(av)}")
    st.divider()

    # 4. RENFORCEMENT
    sous_titre("🏋️ Renforcement")
    st.write("Optimisé pour ta récupération.")
    if st.button("💪 Générer ma séance de renfort"):
        st.balloons()

elif menu == "Mon CV Sportif":
    titre("🏆 Mon CV Sportif")
    
    stats_globales = get_athlete_stats()
    activites = get_activites_un_an()
    
    if stats_globales and activites:
        # --- LOGIQUE PR ---
        def chercher_pr(dist_min, dist_max):
            potents = [a for a in activites if a['type'] in ['Run', 'TrailRun'] and dist_min <= a['distance'] <= dist_max]
            if potents:
                meilleur = min(potents, key=lambda x: x['moving_time'] / x['distance'])
                temps_estime = (meilleur['moving_time'] / meilleur['distance']) * dist_min
                return formater_allure(temps_estime)
            return "--:--"

        tab1, tab2 = st.tabs(["🏃 Course à pied", "🚲 Cyclisme"])
        
        with tab1:
            sous_titre("📊 Stats 2026")
            run = stats_globales.get('ytd_run_totals', {})
            d_km = run.get('distance', 0) / 1000
            t_sec = run.get('moving_time', 0)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.info(f"**Distance** \n### {d_km:.1f} km")
            with c2: st.info(f"**Sorties** \n### {run.get('count', 0)}")
            with c3: st.info(f"**Durée** \n### {t_sec // 3600}h")
            with c4:
                allure_moy = t_sec / d_km if d_km > 0 else 0
                st.info(f"**Allure** \n### {formater_allure(allure_moy) if d_km > 0 else '--:--'}")
            
            st.divider()
            
            # --- CORRECTION : Ces lignes doivent être INDENTÉES sous "with tab1" ---
            sous_titre("⏱️ Mes Meilleurs Chronos")
            r1, r2, r3, r4 = st.columns(4)
            with r1: st.info(f"**PR 5 km** \n### {chercher_pr(5000, 5500)}")
            with r2: st.info(f"**PR 10 km** \n### {chercher_pr(10000, 10500)}")
            with r3: st.info(f"**PR Semi** \n### {chercher_pr(21000, 21700)}")
            with r4: st.info(f"**PR Marathon** \n### {chercher_pr(42100, 42800)}")
            
            st.markdown('<p style="text-align: left; font-size: 0.8rem; opacity: 0.8;">ℹ️ Records basés sur vos activités les plus rapides des 12 derniers mois.</p>', unsafe_allow_html=True)
            st.divider()
            # --- BLOC OBJECTIF 2H59 ---
        with st.container(border=True):
            col_obj1, col_obj2 = st.columns([2, 1])
            
            pr_marathon_brut = [a for a in activites if a['type'] == 'Run' and 42000 <= a['distance'] <= 43000]
            
            if pr_marathon_brut:
                meilleur_temps = min(pr_marathon_brut, key=lambda x: x['moving_time'])['moving_time'] / 60
                ecart = meilleur_temps - 179
                progression = min(1.0, 179 / meilleur_temps)
                message = f"Encore **{int(ecart)} min** à gagner !" if ecart > 0 else "Objectif atteint ! 🔥"
            else:
                # Si pas de marathon trouvé, on peut baser l'estimation sur ton PR Semi x 2 + 10min
                progression = 0.5 # Jauge à moitié par défaut
                message = "Pas encore de chrono cette année..."

            with col_obj1:
                st.markdown("🎯 **Objectif Sub-3h**")
                st.progress(progression)
                st.write(message)
            
            with col_obj2:
                st.metric("Cible", "4:15/km")

        with tab2:
            sous_titre("📊 Stats Cyclisme 2026")
            bike = stats_globales.get('ytd_ride_totals', {})
            db_km = bike.get('distance', 0) / 1000
            tb_sec = bike.get('moving_time', 0)
            
            # 1. Stats Annuelles en Blocs Bleus
            b1, b2, b3, b4 = st.columns(4)
            with b1: st.info(f"**Distance** \n### {db_km:.1f} km")
            with b2: st.info(f"**Sorties** \n### {bike.get('count', 0)}")
            with b3: st.info(f"**Durée** \n### {tb_sec // 3600}h")
            with b4:
                vit_an = db_km / (tb_sec / 3600) if tb_sec > 0 else 0
                st.info(f"**Vit. Moy** \n### {vit_an:.1f} km/h")

            st.divider()
            sous_titre("🏆 Records Cyclisme (12 mois)")

           # 2. Logique pour extraire les records vélo
            rides = [a for a in activites if a['type'] in ['Ride', 'MountainBikeRide']]
            
            if rides:
                max_dist = max(rides, key=lambda x: x['distance'])['distance'] / 1000
                
                # --- CALCUL DURÉE PRÉCISE ---
                total_secondes = max(rides, key=lambda x: x['moving_time'])['moving_time']
                heures = total_secondes // 3600
                minutes = (total_secondes % 3600) // 60
                duree_formatee = f"{heures}h {minutes:02d}" # Format ex: 3h 05
                
                max_deniv = max(rides, key=lambda x: x.get('total_elevation_gain', 0))['total_elevation_gain']
                
                potents_vitesse = [r for r in rides if r['distance'] > 10000]
                max_vit = max(potents_vitesse, key=lambda x: x['distance'] / x['moving_time']) if potents_vitesse else None
                vit_top = (max_vit['distance'] / max_vit['moving_time']) * 3.6 if max_vit else 0

                r_v1, r_v2, r_v3, r_v4 = st.columns(4)
                with r_v1: st.info(f"**Plus Longue** \n### {max_dist:.1f} km")
                with r_v2: st.info(f"**Plus Durable** \n### {duree_formatee}") # Affichage h + min
                with r_v3: st.info(f"**Max D+** \n### {max_deniv:.0f} m")
                with r_v4: st.info(f"**Vitesse Max** \n### {vit_top:.1f} km/h")
            else:
                st.info("Aucune activité cycliste enregistrée sur les 12 derniers mois.")

            st.markdown('<p style="text-align: left; font-size: 0.8rem; opacity: 0.8;">ℹ️ Basé sur vos meilleures performances cyclisme sur les 12 derniers mois.</p>', unsafe_allow_html=True)

    else:
        st.error("Impossible de charger les statistiques Strava.")