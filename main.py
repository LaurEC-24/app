import streamlit as st
import extra_streamlit_components as stx
import logging
from database import verify_credentials, get_user_service
from pages._it_page import show_interventii_page
from security_config import SESSION_TIMEOUT, MAX_LOGIN_ATTEMPTS, LOGIN_COOLDOWN, sanitize_input
from datetime import datetime, timedelta
import os
import uuid
import base64
import json

# Configurare pagină
st.set_page_config(
    page_title="AppElcen - Registru Intervenții IT",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Adăugăm CSS personalizat pentru câmpurile de login
st.markdown("""
    <style>
    /* Stilizare pentru câmpurile de login */
    div[data-testid="stTextInput"] {
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Stilizare pentru butonul de login */
    div[data-testid="stForm"] {
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Centrare text pentru titlu */
    h1 {
        text-align: center;
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

def encode_session_data(data):
    """Encodează datele sesiunii pentru URL."""
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def decode_session_data(encoded_data):
    """Decodează datele sesiunii din URL."""
    try:
        json_str = base64.urlsafe_b64decode(encoded_data.encode()).decode()
        return json.loads(json_str)
    except:
        return None

def save_session_to_params(username, persistent=False):
    """Salvează sesiunea în URL parameters."""
    print(f"\nDEBUG: === Salvare sesiune pentru {username} ===")
    session_id = str(uuid.uuid4())
    login_time = datetime.now()
    
    # Creăm datele sesiunii
    session_data = {
        'username': username,
        'session_id': session_id,
        'login_time': login_time.isoformat(),
        'persistent': persistent
    }
    
    # Encodăm datele pentru URL
    encoded_data = encode_session_data(session_data)
    
    # Salvăm în query params
    st.query_params["session"] = encoded_data
    
    # Actualizăm session state
    st.session_state['session_id'] = session_id
    st.session_state['login_time'] = login_time
    st.session_state['persistent_auth'] = persistent
    print(f"DEBUG: Sesiune salvată în params: {session_data}")

def init_session_state():
    """Inițializează variabilele de sesiune."""
    print("\nDEBUG: === Inițializare sesiune ===")
    
    # Încercăm să restaurăm sesiunea din query params
    encoded_session = st.query_params.get("session", None)
    
    if encoded_session:
        session_data = decode_session_data(encoded_session)
        print(f"DEBUG: Sesiune găsită în params: {session_data}")
        
        if session_data:
            username = session_data.get('username')
            session_id = session_data.get('session_id')
            login_time_str = session_data.get('login_time')
            is_persistent = session_data.get('persistent', False)
            
            try:
                login_time = datetime.fromisoformat(login_time_str) if login_time_str else datetime.now()
                
                # Verificăm dacă sesiunea este validă
                if username and session_id:
                    # Pentru sesiuni persistente, folosim un timeout mai lung
                    timeout = SESSION_TIMEOUT * 3 if is_persistent else SESSION_TIMEOUT
                    time_passed = datetime.now() - login_time
                    
                    print(f"DEBUG: Timp trecut: {time_passed}, Timeout: {timeout}")
                    
                    if time_passed <= timeout:
                        # Restaurăm sesiunea
                        st.session_state['authentication_status'] = True
                        st.session_state['username'] = username
                        st.session_state['service'] = get_user_service(username)
                        st.session_state['login_time'] = login_time
                        st.session_state['session_id'] = session_id
                        st.session_state['persistent_auth'] = is_persistent
                        print(f"DEBUG: Sesiune restaurată cu succes pentru {username}")
                        return
                    else:
                        print("DEBUG: Sesiune expirată")
                        st.query_params.clear()
            except Exception as e:
                print(f"DEBUG: Eroare la restaurarea sesiunii: {str(e)}")
                st.query_params.clear()

    print("DEBUG: Inițializare sesiune nouă")
    # Inițializăm o sesiune nouă
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'service' not in st.session_state:
        st.session_state['service'] = None
    if 'login_time' not in st.session_state:
        st.session_state['login_time'] = None
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = 0
    if 'last_attempt_time' not in st.session_state:
        st.session_state['last_attempt_time'] = None
    if 'show_add_form' not in st.session_state:
        st.session_state['show_add_form'] = False
    if 'persistent_auth' not in st.session_state:
        st.session_state['persistent_auth'] = False

def show_login_page():
    """Afișează pagina de login"""
    if st.session_state['authentication_status']:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.write(f"👤 {st.session_state['username']}")
        if col2.button("Deconectare", key='logout'):
            # Ștergem query params
            st.query_params.clear()
            # Ștergem toate variabilele din sesiune
            for key in list(st.session_state.keys()):
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
        remember_me = st.checkbox("Ține-mă minte", value=False, help="Păstrează-mă conectat pentru 24 de ore")
        submitted = st.form_submit_button("Conectare", use_container_width=True)

        if submitted and username and password:
            st.session_state['last_attempt_time'] = datetime.now()
            
            result = verify_credentials(username, password)
            if result['success']:
                st.session_state['authentication_status'] = True
                st.session_state['username'] = username
                st.session_state['service'] = get_user_service(username)
                
                # Salvăm sesiunea în params
                save_session_to_params(username, persistent=remember_me)
                
                logging.info(f"Autentificare reușită pentru utilizatorul {username}")
                st.rerun()
            else:
                st.session_state['login_attempts'] += 1
                logging.warning(f"Încercare eșuată de autentificare pentru utilizatorul {username}: {result['message']}")
                st.error(f"Autentificare eșuată: {result['message']}")
                if st.session_state['login_attempts'] >= MAX_LOGIN_ATTEMPTS:
                    st.error(f"Ați depășit numărul maxim de încercări. Contul va fi blocat pentru {LOGIN_COOLDOWN.seconds//60} minute.")
    return False

def check_session_timeout():
    """Verifică dacă sesiunea a expirat"""
    if not st.session_state['authentication_status']:
        return

    if not st.session_state['login_time']:
        return
    
    # Calculăm timpul trecut de la ultima autentificare
    time_passed = datetime.now() - st.session_state['login_time']
    
    # Folosim un timeout mai lung pentru sesiuni persistente
    timeout = SESSION_TIMEOUT * 3 if st.session_state.get('persistent_auth') else SESSION_TIMEOUT
    
    # Dacă timpul depășește timeout-ul, deconectăm utilizatorul
    if time_passed > timeout:
        # Ștergem query params
        st.query_params.clear()
        
        # Resetăm starea sesiunii
        st.session_state['authentication_status'] = False
        st.session_state['username'] = None
        st.session_state['service'] = None
        st.session_state['login_time'] = None
        st.session_state['session_id'] = None
        st.session_state['persistent_auth'] = False
        
        st.warning('Sesiunea a expirat. Te rog să te reconectezi.')
        st.rerun()

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