import streamlit as st
from database import verify_credentials, get_user_service
from pages._it_page import show_interventii_page
from security_config import SESSION_TIMEOUT, MAX_LOGIN_ATTEMPTS, LOGIN_COOLDOWN, sanitize_input
from datetime import datetime, timedelta
import logging
import os

# Creăm directorul pentru loguri dacă nu există
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurare logging
log_file = os.path.join(log_dir, 'auth.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Adăugăm și logging în consolă
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)

# Ascundem meniul de navigare
st.set_page_config(
    page_title="Aplicație Intervenții",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# CSS pentru a ascunde complet meniul și a stiliza pagina de login
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    /* Stiluri pentru pagina de login */
    div[data-testid="stForm"] {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        background-color: transparent !important;
        border: none !important;
    }
    
    /* Stiluri pentru câmpurile de input */
    div[data-testid="stTextInput"] input {
        max-width: 300px;
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(49, 51, 63, 0.2);
    }
    
    /* Stiluri pentru butonul de login */
    .stButton button {
        width: 150px;
        margin: 0 auto;
        display: block;
    }
    
    /* Centrare titlu */
    .css-10trblm {
        text-align: center;
    }
    
    /* Spațiere pentru subheader */
    .css-17lntkn {
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inițializează variabilele de sesiune"""
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'service' not in st.session_state:
        st.session_state['service'] = None
    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = 0
    if 'last_attempt_time' not in st.session_state:
        st.session_state['last_attempt_time'] = None
    if 'login_time' not in st.session_state:
        st.session_state['login_time'] = None

def check_session_timeout():
    """Verifică dacă sesiunea a expirat"""
    if st.session_state['login_time']:
        time_elapsed = datetime.now() - st.session_state['login_time']
        if time_elapsed > SESSION_TIMEOUT:
            st.session_state['authentication_status'] = False
            st.session_state['username'] = None
            st.session_state['service'] = None
            st.session_state['login_time'] = None
            return True
    return False

def show_login_page():
    # Verifică dacă utilizatorul este deja autentificat
    if st.session_state['authentication_status']:
        if check_session_timeout():
            st.warning("Sesiunea a expirat. Vă rugăm să vă autentificați din nou.")
            return False
            
        col1, col2 = st.sidebar.columns([3, 1])
        col1.write(f"👤 {st.session_state['username']}")
        if col2.button("Deconectare", key='logout'):
            st.session_state['authentication_status'] = False
            st.session_state['username'] = None
            st.session_state['service'] = None
            st.session_state['login_time'] = None
            st.query_params.clear()
            logging.info(f"Utilizatorul {st.session_state['username']} s-a deconectat")
            st.rerun()
        return True

    # Verifică dacă utilizatorul este blocat
    if (st.session_state['login_attempts'] >= MAX_LOGIN_ATTEMPTS and 
        st.session_state['last_attempt_time'] and 
        datetime.now() - st.session_state['last_attempt_time'] < LOGIN_COOLDOWN):
        remaining_time = LOGIN_COOLDOWN - (datetime.now() - st.session_state['last_attempt_time'])
        st.error(f"Prea multe încercări eșuate. Încercați din nou în {remaining_time.seconds//60} minute.")
        return False

    with st.form("login_form", clear_on_submit=False):
        username = sanitize_input(st.text_input("👤 Utilizator", key='username_input'))
        password = st.text_input("🔑 Parolă", type="password", key='password_input')
        submitted = st.form_submit_button("Conectare", use_container_width=True)

        if submitted and username and password:
            st.session_state['last_attempt_time'] = datetime.now()
            
            if verify_credentials(username, password):
                st.session_state['authentication_status'] = True
                st.session_state['username'] = username
                st.session_state['service'] = get_user_service(username)
                st.session_state['login_time'] = datetime.now()
                st.session_state['login_attempts'] = 0
                logging.info(f"Autentificare reușită pentru utilizatorul {username}")
                st.rerun()
            else:
                st.session_state['login_attempts'] += 1
                logging.warning(f"Încercare eșuată de autentificare pentru utilizatorul {username}")
                st.error("❌ Utilizator sau parolă incorectă!")
                if st.session_state['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                    st.error(f"Cont blocat pentru {LOGIN_COOLDOWN.seconds//60} minute din cauza prea multor încercări eșuate.")
                return False

    return False

def main():
    init_session_state()  # Mutăm inițializarea la începutul main
    st.title("Aplicație Intervenții")

    # Verifică autentificarea
    if not show_login_page():
        st.stop()

    # Adăugăm logging pentru a vedea serviciul
    logging.info(f"Serviciul utilizatorului {st.session_state['username']} este: {st.session_state['service']}")

    if st.session_state['service'] == 'IT':
        show_interventii_page()
    else:
        st.warning("Doar utilizatorii din serviciul IT au acces la registrul de intervenții.")
        st.error(f"Serviciul tău actual este: {st.session_state['service']}")

if __name__ == "__main__":
    main()