import streamlit as st
import extra_streamlit_components as stx
import logging
from database import verify_credentials, get_user_service
from pages._it_page import show_interventii_page
from security_config import SESSION_TIMEOUT, MAX_LOGIN_ATTEMPTS, LOGIN_COOLDOWN, sanitize_input
from datetime import datetime, timedelta
import os

# Configurare pagină - TREBUIE să fie primul apel Streamlit
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

# Inițializare cookie manager ca variabilă globală
if 'cookie_manager' not in st.session_state:
    st.session_state.cookie_manager = stx.CookieManager()

def get_manager():
    """Returnează instanța existentă de CookieManager."""
    return st.session_state.cookie_manager

def init_session_state():
    """Inițializează variabilele de sesiune."""
    # Încercăm să recuperăm datele din cookie
    saved_auth_data = get_manager().get('auth_data')
    
    logging.info(f"Recuperare cookie-uri: auth_data={saved_auth_data}")
    
    if saved_auth_data and isinstance(saved_auth_data, dict) and 'username' in saved_auth_data and 'auth_status' in saved_auth_data and saved_auth_data['auth_status'] == 'true':
        logging.info("Cookie-uri valide găsite, restaurăm sesiunea")
        st.session_state['authentication_status'] = True
        st.session_state['username'] = saved_auth_data['username']
        st.session_state['service'] = get_user_service(saved_auth_data['username'])
        st.session_state['login_time'] = datetime.now()
    else:
        logging.info("Nu s-au găsit cookie-uri valide, inițializăm sesiune nouă")
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = False
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'service' not in st.session_state:
            st.session_state['service'] = None
        if 'login_time' not in st.session_state:
            st.session_state['login_time'] = None
    
    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = 0
    if 'last_attempt_time' not in st.session_state:
        st.session_state['last_attempt_time'] = None
    if 'show_add_form' not in st.session_state:
        st.session_state['show_add_form'] = False

def check_session_timeout():
    """Verifică dacă sesiunea a expirat"""
    # Dacă nu suntem autentificați, nu facem nimic
    if not st.session_state['authentication_status']:
        return

    # Verificăm dacă avem un timp de login setat
    if not st.session_state['login_time']:
        return
    
    # Calculăm timpul trecut de la ultima autentificare
    time_passed = datetime.now() - st.session_state['login_time']
    
    # Dacă timpul depășește SESSION_TIMEOUT, deconectăm utilizatorul
    if time_passed > SESSION_TIMEOUT:
        st.session_state['authentication_status'] = False
        st.session_state['username'] = None
        st.session_state['service'] = None
        st.session_state['login_time'] = None
        st.warning('Sesiunea a expirat. Te rog să te reconectezi.')
        st.rerun()

def show_login_page():
    """Afișează pagina de login"""
    if st.session_state['authentication_status']:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.write(f"👤 {st.session_state['username']}")
        if col2.button("Deconectare", key='logout'):
            # Ștergem cookie-urile la delogare
            cookie_manager = get_manager()
            cookie_manager.delete('auth_data')
            logging.info("Cookie-uri șterse la delogare")
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
        return True

    st.markdown("<h1 style='text-align: center;'>🔐 Autentificare</h1>", unsafe_allow_html=True)
    
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
                # Setăm cookie-urile pentru sesiune persistentă
                cookie_manager = get_manager()
                expiry = datetime.now() + timedelta(days=1)
                
                # Setăm ambele cookie-uri într-un singur apel
                cookie_data = {
                    'username': username,
                    'auth_status': 'true'
                }
                cookie_manager.set('auth_data', cookie_data, expires_at=expiry)
                
                logging.info(f"Cookie-uri setate pentru {username} cu expirare la {expiry}")
                
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
                st.error("Autentificare eșuată. Verificați numele de utilizator și parola.")
                if st.session_state['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                    st.error(f"Ați depășit numărul maxim de încercări. Contul va fi blocat pentru {LOGIN_COOLDOWN.seconds//60} minute.")
    return False

def main():
    """Funcția principală a aplicației."""
    # Inițializăm starea sesiunii
    init_session_state()
    
    # Verificăm timeout-ul sesiunii
    check_session_timeout()
    
    # Afișăm pagina de login sau pagina principală
    if show_login_page():
        st.title("Aplicație Intervenții")
        show_interventii_page()

if __name__ == "__main__":
    main()