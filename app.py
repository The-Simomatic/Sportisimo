import streamlit as st
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
    """Gère la session et les retours de mails de récupération"""
    if "type" in st.query_params and st.query_params["type"] == "recovery":
        st.title("🔄 Nouveau mot de passe")
        new_pass = st.text_input("Entre ton nouveau mot de passe", type="password")
        if st.button("Mettre à jour", use_container_width=True):
            try:
                supabase.auth.update_user({"password": new_pass})
                st.success("✅ Mot de passe mis à jour ! Connecte-toi.")
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
        st.stop()

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
                except:
                    st.error("Identifiants incorrects ou email non validé.")
            
            if st.button("Mot de passe oublié ?"):
                if e_log:
                    try:
                        supabase.auth.reset_password_for_email(e_log)
                        st.info(f"📩 Lien de récupération envoyé à {e_log}")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Saisis ton email ci-dessus pour recevoir le lien.")

        with tab_reg:
            st.write("### Inscription")
            # Ordre demandé : Mail, Pass, Prénom, Nom, Date N., Poids, Sport, Niveau
            new_e = st.text_input("Email d'inscription", key="reg_email").lower().strip()
            new_p = st.text_input("Mot de passe", type="password", key="reg_pass")
            
            c1, c2 = st.columns(2)
            with c1:
                prenom = st.text_input("Prénom")
                # Date de naissance améliorée : vide par défaut, plage large
                date_n = st.date_input(
                    "Date de naissance", 
                    value=None, 
                    min_value=datetime.date(1920, 1, 1),
                    max_value=datetime.date.today(),
                    format="DD/MM/YYYY"
                )
            with c2:
                nom = st.text_input("Nom")
                poids = st.number_input("Poids (kg)", 30, 200, 75)
            
            c3, c4 = st.columns(2)
            with c3:
                sport = st.selectbox("Sport favori", ["Running", "Cyclisme", "Trail", "VTT"])
            with c4:
                niv = st.selectbox("Niveau", ["Débutant", "Intermédiaire", "Confirmé", "Expert"])
            
            if st.button("Valider l'inscription", use_container_width=True):
                # Validation stricte des champs obligatoires
                if not new_e or not new_p or not prenom or not nom or date_n is None:
                    st.warning("⚠️ Merci de remplir tous les champs, y compris ta date de naissance.")
                else:
                    try:
                        res = supabase.auth.sign_up({
                            "email": new_e, 
                            "password": new_p,
                            "options": {"data": {
                                "prenom": prenom, 
                                "nom": nom, 
                                "date_n": str(date_n),
                                "poids": poids, 
                                "sport": sport,
                                "niveau": niv
                            }}
                        })
                        if res.user:
                            st.success("### 📧 Mail envoyé !")
                            st.info("Consulte tes mails pour valider ton compte, puis connecte-toi ici.")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

else:
    # --- ÉCRAN CONNECTÉ & REMPLISSAGE BASE ---
    user = st.session_state.user
    
    # 1. Vérification si le profil existe déjà
    res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
    prof = res_p.data
    
    # 2. Création automatique du profil (First Login)
    if not prof:
        st.balloons()
        meta = user.user_metadata
        # On fait correspondre EXACTEMENT aux colonnes de ton image 99e082.png
        new_prof_data = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "date_naissance": meta.get("date_n"), # Colonne exacte
            "poids": float(meta.get("poids", 75)),  # Supabase attend souvent un float
            "niveau": meta.get("niveau", "Débutant"),
            "sport_pref": meta.get("sport", "Running"),
            "vma": 16.0,
            "statut": "gratuit"
        }
        try:
            supabase.table("profiles").insert(new_prof_data).execute()
            st.success("Profil synchronisé avec succès !")
            st.rerun() # Recharge pour afficher le dashboard avec les données de 'prof'
        except Exception as e:
            st.error(f"Erreur lors de la création du profil : {e}")
            st.stop()

    # 3. Affichage du Dashboard une fois le profil chargé
    with st.sidebar:
        st.markdown(f"## Salut {prof.get('prenom', 'Sportif')} ! 👋")
        if st.button("Se déconnecter", use_container_width=True):
            logout_user()
        st.divider()
        st.write(f"Niveau : **{prof.get('niveau')}**")

    st.title("🏃 Mon Dashboard Sportif")
    st.write(f"Bienvenue sur ton espace personnalisé, {prof.get('prenom')}.")
    
    # Exemple de calcul d'allure basé sur la VMA par défaut (16.0)
    vma = prof.get('vma', 16.0)
    st.metric("VMA Actuelle", f"{vma} km/h")