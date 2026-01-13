import streamlit as st
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
st.set_page_config(page_title="SportiSimo", page_icon="🏃", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if "user" not in st.session_state:
    st.session_state.user = None

# --- 2. LOGIQUE D'AUTHENTIFICATION ---
def handle_auth():
    try:
        res = supabase.auth.get_session()
        if res and res.session:
            st.session_state.user = res.user
    except:
        pass

handle_auth()

def logout_user():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# --- 3. DESIGN ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap');
    html, body, [data-testid="stWidgetLabel"], p, span { color: #E5E5E5 !important; font-family: 'Ubuntu', sans-serif; }
    .logo-text { text-align: center; font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 4. INTERFACE ---
if st.session_state.user is None:
    st.markdown("<div class='logo-text'><span style='color:#28A5A8'>Sporti</span><span style='color:#F37B1F'>Simo</span></div>", unsafe_allow_html=True)
    
    col_main = st.columns([1, 2, 1])[1]
    with col_main:
        tab_log, tab_reg = st.tabs(["Connexion", "Créer un compte"])
        
        with tab_log:
            e_log = st.text_input("Email", key="l_email").lower().strip()
            p_log = st.text_input("Mot de passe", type="password", key="l_pass")
            
            if st.button("Se connecter", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e_log, "password": p_log})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                except Exception as e:
                    st.error("Identifiants incorrects ou email non validé.")

        with tab_reg:
            st.write("### Inscription")
            new_e = st.text_input("Email d'inscription", key="reg_email").lower().strip()
            new_p = st.text_input("Mot de passe", type="password", key="reg_pass")
            
            c1, c2 = st.columns(2)
            with c1:
                prenom = st.text_input("Prénom")
                date_n = st.date_input("Date de naissance", value=None, min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today(), format="DD/MM/YYYY")
            with c2:
                nom = st.text_input("Nom")
                poids = st.number_input("Poids (kg)", 30, 200, 75)
            
            c3, c4 = st.columns(2)
            with c3:
                sport = st.selectbox("Sport favori", ["Running", "Cyclisme", "Trail", "VTT"])
            with c4:
                niv = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])
            
            if st.button("Valider l'inscription", use_container_width=True):
                if not new_e or not new_p or not prenom or not nom or date_n is None:
                    st.warning("⚠️ Remplis tous les champs !")
                else:
                    try:
                        # ON ENREGISTRE LES INFOS DANS LES METADATA (C'est stocké en attente du mail)
                        res = supabase.auth.sign_up({
                            "email": new_e, 
                            "password": new_p,
                            "options": {"data": {
                                "prenom": prenom, "nom": nom, "date_n": str(date_n),
                                "poids": poids, "sport": sport, "niveau": niv
                            }}
                        })
                        if res.user:
                            st.success("📩 Mail envoyé ! Clique sur le lien dans l'e-mail pour activer ton compte.")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

else:
    # --- ÉCRAN CONNECTÉ ---
    user = st.session_state.user
    
    # 1. On cherche le profil
    res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
    prof = res_p.data
    
    # 2. Si le profil n'existe pas ENCORE (Première connexion après clic e-mail)
    if not prof:
        st.balloons()
        meta = user.user_metadata
        new_prof_data = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "date_naissance": meta.get("date_n"),
            "poids": float(meta.get("poids", 75)),
            "niveau": meta.get("niveau", "Débutant"),
            "sport_pref": meta.get("sport", "Running"),
            "vma": 16.0,
            "statut": "gratuit"
        }
        try:
            # ICI l'utilisateur est CONNECTÉ donc Supabase accepte l'insertion
            supabase.table("profiles").insert(new_prof_data).execute()
            st.rerun() 
        except Exception as e:
            st.error(f"Erreur création profil : {e}")
            st.stop()

    # 3. Dashboard
    with st.sidebar:
        st.markdown(f"## Salut {prof.get('prenom')} ! 👋")
        if st.button("Se déconnecter", use_container_width=True):
            logout_user()

    st.title("🏃 SportiSimo Dashboard")
    st.write(f"Content de te revoir, {prof.get('prenom')} {prof.get('nom')}.")