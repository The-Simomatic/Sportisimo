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

# --- 3. INTERFACE ---
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
            except:
                st.error("Identifiants incorrects ou email non validé.")

    with tab_reg:
        st.write("### Inscription")
        new_e = st.text_input("Email d'inscription", key="reg_email").lower().strip()
        new_p = st.text_input("Mot de passe", type="password", key="reg_pass")
        
        c1, c2 = st.columns(2)
        with c1:
            prenom = st.text_input("Prénom")
            # Correction alignement et date vide par défaut
            date_n = st.date_input("Date de naissance", value=None, min_value=datetime.date(1920, 1, 1))
        with c2:
            nom = st.text_input("Nom")
            poids = st.number_input("Poids (kg)", 30.0, 200.0, 75.0)
        
        sport = st.selectbox("Sport", ["Running", "Cyclisme", "Trail"])
        niv = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])

        # ALIGNEMENT CORRECT (Correction Image 9a582d)
        if st.button("Valider l'inscription", use_container_width=True):
            if not prenom or not nom or date_n is None:
                st.warning("⚠️ Remplis tous les champs !")
            else:
                try:
                    # Inscription simple (On ne touche pas à la base ici)
                    supabase.auth.sign_up({
                        "email": new_e, "password": new_p,
                        "options": {"data": {
                            "prenom": prenom, "nom": nom, "date_n": str(date_n),
                            "poids": poids, "sport": sport, "niveau": niv
                        }}
                    })
                    st.success("📩 Mail envoyé ! Valide-le avant de te connecter.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

else:
    # --- 4. ÉCRAN CONNECTÉ (AUTHENTIFIED) ---
    user = st.session_state.user
    
    # Sécurité pour éviter AttributeError (Image 9ac8e9)
    prof = None
    try:
        res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        if res_p:
            prof = res_p.data
    except:
        pass

    # Si profil inexistant dans la base (Image 99e082)
    if not prof:
        meta = user.user_metadata
        new_prof = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "date_naissance": meta.get("date_n"), # Colonne Image 99e082
            "poids": float(meta.get("poids", 75.0)),
            "niveau": meta.get("niveau", "Débutant"),
            "sport_pref": meta.get("sport", "Running"),
            "vma": 16.0
        }
        try:
            # ICI l'utilisateur est connecté, la RLS "authenticated" l'autorise
            supabase.table("profiles").insert(new_prof).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Erreur d'écriture : {e}")
            st.stop()

    st.title(f"Salut {prof.get('prenom')} ! 👋")
    if st.button("Déconnexion"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()