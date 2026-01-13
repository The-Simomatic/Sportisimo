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
    if "type" in st.query_params and st.query_params["type"] == "recovery":
        st.title("🔄 Nouveau mot de passe")
        new_pass = st.text_input("Entre ton nouveau mot de passe", type="password")
        if st.button("Mettre à jour", use_container_width=True):
            try:
                supabase.auth.update_user({"password": new_pass})
                st.success("✅ Mot de passe mis à jour !")
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

def ui_stat_card(label, value):
    st.markdown(f"""
        <div style="background: rgba(40,165,168,0.1); border-left: 4px solid #28A5A8; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
            <div style="font-size: 0.8rem; color: #28A5A8; font-weight: bold;">{label}</div>
            <div style="font-size: 1.5rem; color: white; font-weight: 700;">{value}</div>
        </div>
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
            
            # CORRECTION : Suppression de variant="ghost" pour éviter l'erreur TypeError
            if st.button("Mot de passe oublié ?"):
                if e_log:
                    try:
                        supabase.auth.reset_password_for_email(e_log)
                        st.info(f"📩 Lien envoyé à {e_log}")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Saisis ton email ci-dessus.")

        with tab_reg:
            st.write("### Inscription")
            new_e = st.text_input("Email", key="r_email").lower().strip()
            new_p = st.text_input("Mot de passe", type="password", key="r_pass")
            
            c1, c2 = st.columns(2)
            prenom_in = c1.text_input("Prénom")
            nom_in = c2.text_input("Nom")
            poids_in = c1.number_input("Poids (kg)", 30, 200, 75)
            sport_in = c2.selectbox("Sport", ["Running", "Cyclisme", "Trail"])
            
            if st.button("Valider l'inscription", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({
                        "email": new_e, 
                        "password": new_p,
                        "options": {"data": {
                            "prenom": prenom_in, "nom": nom_in, "poids": poids_in, "sport_pref": sport_in
                        }}
                    })
                    if res.user:
                        st.success("### 📧 Mail envoyé !")
                        st.info("Vérifie ta boîte mail pour activer ton compte.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

else:
    # --- ÉCRAN CONNECTÉ ---
    user = st.session_state.user
    
    # 1. RECUPERATION DU PROFIL
    try:
        res_p = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        prof = res_p.data
    except:
        prof = None

    # 2. CREATION DU PROFIL SI MANQUANT
    if not prof:
        st.balloons()
        meta = user.user_metadata
        new_prof = {
            "id": user.id,
            "email": user.email,
            "prenom": meta.get("prenom", "Champion"),
            "nom": meta.get("nom", ""),
            "poids": meta.get("poids", 75),
            "sport_pref": meta.get("sport_pref", "Running"),
            "vma": 16.0,
            "statut": "gratuit"
        }
        try:
            supabase.table("profiles").insert(new_prof).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Erreur base : {e}")
            st.stop()

    # 3. AFFICHAGE
    with st.sidebar:
        # Sécurité pour l'affichage du prénom
        display_name = prof.get('prenom', 'Sportif') if prof else "Sportif"
        st.markdown(f"## Salut {display_name} ! 👋")
        if st.button("Se déconnecter", use_container_width=True):
            logout_user()
        st.divider()
        menu = st.radio("Menu", ["🏃 Dashboard", "⚙️ Paramètres"])

    if menu == "🏃 Dashboard":
        st.title("🏃 Mes Allures")
        vma = prof.get('vma', 16.0)
        c1, c2, c3 = st.columns(3)
        with c1: ui_stat_card("Endurance (70%)", f"{int(3600/(vma*0.7)//60)}:{int(3600/(vma*0.7)%60):02d} /km")
        with c2: ui_stat_card("Seuil (85%)", f"{int(3600/(vma*0.85)//60)}:{int(3600/(vma*0.85)%60):02d} /km")
        with c3: ui_stat_card("VMA (100%)", f"{int(3600/vma//60)}:{int(3600/vma%60):02d} /km")

    elif menu == "⚙️ Paramètres":
        st.title("⚙️ Réglages")
        with st.form("edit_p"):
            v_input = st.slider("VMA (km/h)", 8.0, 22.0, float(prof.get('vma', 16.0)))
            p_input = st.number_input("Poids (kg)", 30, 200, int(prof.get('poids', 75)))
            if st.form_submit_button("Sauvegarder"):
                supabase.table("profiles").update({"vma": v_input, "poids": p_input}).eq("id", user.id).execute()
                st.success("Mis à jour !")
                st.rerun()