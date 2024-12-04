import logging
import os
from datetime import datetime
import re

# Configurare logging
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Funcții pentru validarea input-ului
def sanitize_input(text):
    """Curăță input-ul de caractere potențial periculoase."""
    if not text:
        return text
    # Elimină caractere speciale și HTML
    text = re.sub(r'[<>"/\'%;()&+]', '', str(text))
    return text.strip()

def validate_length(text, max_length):
    """Validează lungimea textului."""
    if not text:
        return False
    return len(str(text)) <= max_length

def validate_time_format(time_str):
    """Validează formatul orei (HH:MM)."""
    if not time_str:
        return False
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def validate_date_format(date_str):
    """Validează formatul datei (YYYY-MM-DD)."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def normalize_username(username):
    """
    Normalizează numele de utilizator pentru a gestiona ambele formate.
    Returnează o listă cu posibile variante ale numelui de utilizator.
    De exemplu: pentru 'laurentiuhenegariu' returnează ['laurentiuhenegariu', 'laurentiu.henegariu']
    """
    if not username:
        return []
    
    # Dacă username-ul conține deja punct, returnăm și varianta fără punct
    if '.' in username:
        return [username, username.replace('.', '')]
    
    # Dacă username-ul nu conține punct, încercăm să găsim locul unde ar trebui să fie
    # Verificăm dacă există în baza de date cu punct
    import pyodbc
    import configparser
    from pathlib import Path
    
    try:
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / 'config.ini'
        config.read(config_path)
        
        conn_str = (
            "DRIVER={SQL Server};"
            f"SERVER={config['MySQL']['host']},{config['MySQL']['port']};"
            f"DATABASE={config['MySQL']['database']};"
            f"UID={config['MySQL']['user']};"
            f"PWD={config['MySQL']['password']};"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Căutăm username-ul în baza de date
        cursor.execute("SELECT NumeUtilizator FROM Utilizatori WHERE NumeUtilizator LIKE ?", (f"%{username}%",))
        result = cursor.fetchone()
        
        if result:
            db_username = result[0]
            return [username, db_username]
        
        return [username]
        
    except Exception as e:
        print(f"Eroare la verificarea username-ului: {str(e)}")
        return [username]
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
