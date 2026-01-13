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

# --- 2. GESTION DE L'AUTH ---
def handle_auth():
    try:
        res = supabase.auth.get_session()
        if res and res.session:
            st.session_state.user = res.user
    except:
        pass

handle_auth()

# --- 3. INTERFACE DE CONNEXION ---
if st.session_state.user is None:
    st.markdown("<h1 style='text-align:center;'>SportiSimo</h1>", unsafe_allow_html=True)
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
            except Exception:
                st.error("Accès refusé. Vérifie tes identifiants ou valide ton e-mail.")

    with tab_reg:
        st.write("### Inscription")
        new_e = st.text_input("Email d'inscription", key="reg_email").lower().strip()
        new_p = st.text_input("Mot de passe", type="password", key="reg_pass")
        
        c1, c2 = st.columns(2)
        with c1:
            prenom_in = st.text_input("Prénom")
            date_n_in = st.date_input("Date de naissance", value=None, min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today(), format="DD/MM/YYYY")
        with c2:
            nom_in = st.text_input("Nom")
            poids_in = st.number_input("Poids (kg)", 30.0, 200.0, 75.0)
        
        sport_in = st.selectbox("Sport favori", ["Running", "Cyclisme", "Trail"])
        niv_in = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])
        
        if st.button("Valider l'inscription", use_container_width=True):
            if not prenom_in or not nom_in or date_n_in is None:
                st.warning("⚠️ Complète tous les champs.")
            else:
                try:
                    # On stocke tout dans les métadonnées pour plus tard
                    supabase.auth.sign_up({
                        "email": new_e, 
                        "password": new_p,
                        "options": {"data": {
                            "prenom": prenom_in, "nom": nom_in, "date_n": str(date_n_in),
                            "poids": poids_in, "sport": sport_in, "niveau": niv_in
                        }}
                    })
                    st.success("📩 E-mail envoyé ! Valide ton compte pour activer ton profil.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

# --- 4. ÉCRAN CONNECTÉ ---
else:
    user = st.session_state.user
    
    # Sécurité pour éviter l'AttributeError (Image 9ac8e9)
    prof = None
    try:
        res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        if res_p:
            prof = res_p.data
    except Exception as e:
        st.warning("Initialisation de ton profil...")

    # Si le profil est vide (Base vide), on le crée
    if not prof:
        meta = user.user_metadata
        new_data = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "date_naissance": meta.get("date_n"), # Image 99e082
            "poids": float(meta.get("poids", 75.0)),
            "niveau": meta.get("niveau", "Débutant"),
            "sport_pref": meta.get("sport", "Running"),
            "vma": 16.0,
            "statut": "gratuit"
        }
        try:
            supabase.table("profiles").insert(new_data).execute()
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Erreur d'écriture : {e}")
            st.info("Vérifie tes RLS Policies (Insert doit être sur TRUE).")
            st.stop()

    # Dashboard final
    st.sidebar.title(f"Salut {prof['prenom']} !")
    if st.sidebar.button("Déconnexion"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    
    st.title("🏃 SportiSimo")
    st.write(f"Ton profil est prêt et ta base de données est remplie !")