import pyodbc
import configparser
from datetime import datetime
import hashlib
import os
from pathlib import Path
import logging
from utils import normalize_username

def get_db_connection():
    """Creează și returnează o conexiune la baza de date."""
    try:
        # Încercăm să folosim variabilele de mediu mai întâi
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT')
        database = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')

        # Dacă nu avem variabile de mediu, folosim config.ini
        if not all([host, port, database, user, password]):
            config = configparser.ConfigParser()
            config_path = Path(__file__).parent / 'config.ini'
            config.read(config_path)
            
            host = config['MySQL']['host']
            port = config['MySQL']['port']
            database = config['MySQL']['database']
            user = config['MySQL']['user']
            password = config['MySQL']['password']

        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )
        
        logging.info("Încercare de conectare la baza de date")
        return pyodbc.connect(conn_str)
    except Exception as e:
        logging.error(f"Eroare la conectarea la baza de date: {str(e)}")
        return None

def hash_password(password):
    """Creează un hash pentru parolă folosind SHA-256 cu salt."""
    if not password:
        logging.warning("Încercare de a hash-a unei parole vide")
        return None
        
    # Adăugăm un salt constant pentru toate parolele
    salt = "AppElcen2023"  # Acest salt ar trebui să fie într-un fișier de configurare securizat
    
    try:
        # Convertim parola la string și eliminăm spațiile de la început și sfârșit
        password_str = str(password).strip()
        
        # Verificăm dacă parola este goală după curățare
        if not password_str:
            logging.warning("Parola este goală după curățare")
            return None
            
        # Combinăm parola cu salt-ul
        salted_password = password_str + salt
        
        # Creăm hash-ul
        hashed = hashlib.sha256(salted_password.encode()).hexdigest()
        logging.info(f"Hash creat pentru parolă: {hashed}")
        return hashed
        
    except Exception as e:
        logging.error(f"Eroare la crearea hash-ului parolei: {str(e)}")
        return None

def normalize_username(username):
    """
    Normalizează username-ul pentru a se potrivi cu formatul din baza de date.
    Caută username-ul ignorând punctele și apoi returnează formatul corect din baza de date.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logging.warning(f"Nu s-a putut obține conexiunea la baza de date în normalize_username pentru {username}")
            return username
            
        cursor = conn.cursor()
        
        # Căutăm username-ul ignorând punctele
        clean_username = username.replace('.', '')
        query = """
            SELECT NumeUtilizator 
            FROM Utilizatori 
            WHERE REPLACE(NumeUtilizator, '.', '') = ?
        """
        
        logging.info(f"Căutăm username: {username}, curățat: {clean_username}")
        cursor.execute(query, (clean_username,))
        result = cursor.fetchone()
        
        if result:
            logging.info(f"Am găsit un username potrivit în baza de date: {result[0]}")
            return result[0]
            
        # Dacă nu găsim nimic, returnăm username-ul original
        logging.info(f"Nu am găsit un username potrivit pentru {username}")
        return username
        
    except Exception as e:
        logging.error(f"Eroare în normalize_username: {str(e)}")
        return username
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_credentials(username, password=None):
    """Verifică credențialele utilizatorului în baza de date."""
    conn = None
    cursor = None
    try:
        logging.info("\n=== Începe verificarea credențialelor ===")
        logging.info(f"Username primit: {username}")
        logging.info(f"Parolă primită: {'[NONE]' if password is None else '[SET]'}")
        
        conn = get_db_connection()
        if not conn:
            logging.error("Nu s-a putut realiza conexiunea la baza de date")
            return {'success': False, 'message': 'Eroare la conectarea la baza de date'}
        
        cursor = conn.cursor()
        
        # Mai întâi găsim utilizatorul pentru a verifica dacă există
        find_user_query = """
            SELECT u.ID, u.NumeUtilizator, u.Parola, s.Nume as Serviciu, u.EsteManager
            FROM Utilizatori u
            JOIN Servicii s ON u.ServiciuID = s.ID
            WHERE u.NumeUtilizator = ?
        """
        
        normalized_username = normalize_username(username)
        logging.info(f"Username normalizat: {normalized_username}")
        
        cursor.execute(find_user_query, (normalized_username,))
        user = cursor.fetchone()
        
        if not user:
            logging.info("Utilizatorul nu a fost găsit în baza de date")
            return {'success': False, 'message': 'Credențiale invalide'}
            
        logging.info(f"Utilizator găsit: ID={user[0]}, Username={user[1]}")
            
        # Dacă verificăm doar username-ul (pentru sesiune), returnăm success
        if password is None:
            logging.info("Verificare doar username pentru sesiune")
            return {
                'success': True,
                'user_id': user[0],
                'username': user[1],
                'serviciu': user[3],
                'este_manager': user[4] == 1
            }
        
        # Verificăm dacă parola introdusă este goală
        if not password:
            logging.warning("Parola introdusă este goală")
            return {'success': False, 'message': 'Parola invalidă'}
            
        # Comparăm parola introdusă cu cea din baza de date
        stored_password = user[2].strip() if user[2] else ''
        hashed_input_password = hash_password(password)
        
        logging.info("\n=== Verificare parolă ===")
        logging.info(f"Hash pentru parola corectă '12345': {hash_password('12345')}")
        logging.info(f"Hash pentru parola introdusă: {hashed_input_password}")
        logging.info(f"Hash stocat în baza de date: {stored_password}")
        
        if not hashed_input_password:
            logging.error("Nu s-a putut genera hash-ul pentru parola introdusă")
            return {'success': False, 'message': 'Eroare la procesarea parolei'}
            
        if hashed_input_password != stored_password:
            logging.info("\nPAROLĂ INVALIDĂ!")
            logging.info(f"Hash-urile nu se potrivesc:")
            logging.info(f"Hash parola introdusă : {hashed_input_password}")
            logging.info(f"Hash stocat în DB    : {stored_password}")
            return {'success': False, 'message': 'Credențiale invalide'}
        
        logging.info("\n=== Autentificare reușită ===")
        logging.info(f"User ID: {user[0]}")
        logging.info(f"Username: {user[1]}")
        logging.info(f"Serviciu: {user[3]}")
        logging.info(f"Este manager: {user[4] == 1}")
        
        return {
            'success': True,
            'user_id': user[0],
            'username': user[1],
            'serviciu': user[3],
            'este_manager': user[4] == 1
        }
        
    except Exception as e:
        logging.error(f"Eroare în timpul verificării credențialelor: {str(e)}")
        return {'success': False, 'message': f'Eroare de conectare: {str(e)}'}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_service(username):
    """Obține serviciul asociat unui utilizator."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("Nu s-a putut obține conexiunea la baza de date")
            return None
        
        cursor = conn.cursor()
        
        query = """
            SELECT s.Nume
            FROM Utilizatori u
            JOIN Servicii s ON u.ServiciuID = s.ID
            WHERE u.NumeUtilizator = ?
        """
        
        # Normalizăm username-ul
        normalized_username = normalize_username(username)
        logging.info(f"Obținem serviciul pentru username normalizat: {normalized_username}")
        
        cursor.execute(query, (normalized_username,))
        result = cursor.fetchone()
        
        if result:
            logging.info(f"Am găsit serviciul {result[0]} pentru utilizator {normalized_username}")
            return result[0]
        logging.info(f"Nu am găsit serviciul pentru utilizator {normalized_username}")
        return None
        
    except Exception as e:
        logging.error(f"Eroare la obținerea serviciului: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_interventii():
    """Obține toate intervențiile din registru."""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        query = """
            SELECT 
                NrCrt,
                DataInterventie,
                Zi,
                Solicitant,
                Solicitare,
                Ora,
                DurataInterventie,
                PersonalITC,
                Observatii,
                Status,
                DataAprobare,
                AprobatDe
            FROM RegistruInterventii
            ORDER BY DataInterventie DESC, Ora DESC
        """
        
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        return results
        
    except Exception as e:
        logging.error(f"Eroare la obținerea intervențiilor: {str(e)}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def adauga_interventie(data_interventie, zi, solicitant, solicitare, ora, durata, personal_itc, observatii, serviciu_id):
    """Adaugă o nouă intervenție în registru."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Validăm lungimea textului pentru solicitare
        if len(solicitare) > 1000:
            logging.warning("Textul solicitării este prea lung (maxim 1000 caractere)")
            return False
            
        # Formatăm datele pentru SQL Server
        data_sql = data_interventie.strftime('%Y-%m-%d')
        ora_sql = ora  # ora este deja în format HH:MM
        durata_sql = int(durata) if durata else 0
        serviciu_id_sql = int(serviciu_id) if serviciu_id else None
        observatii_sql = observatii if observatii else None
        
        query = """
            INSERT INTO RegistruInterventii 
            (DataInterventie, Zi, Solicitant, Solicitare, Ora, 
            DurataInterventie, PersonalITC, Observatii, ServiciuID, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            data_sql,           # DataInterventie
            zi,                 # Zi
            solicitant,         # Solicitant
            solicitare,         # Solicitare
            ora_sql,           # Ora
            durata_sql,        # DurataInterventie
            personal_itc,       # PersonalITC
            observatii_sql,     # Observatii
            serviciu_id_sql,    # ServiciuID
            'In Asteptare'      # Status initial
        )
        
        cursor.execute(query, params)
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Eroare la adăugarea intervenției: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_servicii():
    """Obține lista tuturor serviciilor."""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        
        query = "SELECT ID, Nume FROM Servicii ORDER BY Nume"
        cursor.execute(query)
        
        return {row.Nume: row.ID for row in cursor.fetchall()}
        
    except Exception as e:
        logging.error(f"Eroare la obținerea serviciilor: {str(e)}")
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def is_sef_birou(username):
    """Verifică dacă utilizatorul este șef de birou."""
    try:
        conn = get_db_connection()
        if not conn:
            logging.warning("Nu s-a putut obține conexiunea în is_sef_birou")
            return False
        
        cursor = conn.cursor()
        normalized_username = normalize_username(username)
        
        query = """
            SELECT EsteManager
            FROM Utilizatori
            WHERE NumeUtilizator = ?
        """
        
        logging.info(f"Verificare rol șef pentru utilizatorul {normalized_username}")
        cursor.execute(query, (normalized_username,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            logging.info(f"Utilizatorul {normalized_username} ESTE șef de birou")
            return True
        else:
            logging.info(f"Utilizatorul {normalized_username} NU este șef de birou")
            return False
        
    except Exception as e:
        logging.error(f"Eroare la verificarea rolului: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def aproba_interventie(nr_crt, approved_by, action='Aprobat'):
    """Aprobă sau respinge o intervenție direct în baza de date."""
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("Nu s-a putut realiza conexiunea la baza de date")
            return False
        
        cursor = conn.cursor()
        logging.info("\n=== Aprobare intervenție ===")
        logging.info(f"Nr. crt: {nr_crt}")
        logging.info(f"Aprobat de: {approved_by}")
        logging.info(f"Acțiune: {action}")
        
        # Facem update direct în baza de date
        query = """
            UPDATE RegistruInterventii 
            SET Status = ?, 
                DataAprobare = GETDATE(), 
                AprobatDe = ? 
            WHERE NrCrt = ?
        """
        
        cursor.execute(query, (action, approved_by, nr_crt))
        
        # Verificăm câte rânduri au fost afectate
        rows_affected = cursor.rowcount
        logging.info(f"Rânduri afectate: {rows_affected}")
        
        if rows_affected > 0:
            conn.commit()
            logging.info("Tranzacție finalizată cu succes")
            return True
            
        logging.info("Nu s-a găsit intervenția pentru actualizare")
        return False
        
    except Exception as e:
        logging.error(f"Eroare la procesarea intervenției: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Conexiune închisă")

def sterge_toate_interventiile():
    """Șterge toate intervențiile din baza de date."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        query = "DELETE FROM RegistruInterventii"
        cursor.execute(query)
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Eroare la ștergerea intervențiilor: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_interventii_csv(file_path):
    """Importă intervenții din fișier CSV."""
    try:
        import pandas as pd
        from datetime import datetime
        
        # Citim CSV-ul
        df = pd.read_csv(file_path)
        
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Pregătim query-ul de inserare
        query = """
            INSERT INTO RegistruInterventii 
            (DataInterventie, Zi, Solicitant, Solicitare, Ora, 
            DurataInterventie, PersonalITC, Observatii, ServiciuID, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Iterăm prin fiecare rând și inserăm în baza de date
        for _, row in df.iterrows():
            try:
                # Convertim data în format corect
                data = pd.to_datetime(row['DataInterventie']).strftime('%Y-%m-%d')
                ora = pd.to_datetime(row['Ora']).strftime('%H:%M')
                
                params = (
                    data,                   # DataInterventie
                    row['Zi'],             # Zi
                    row['Solicitant'],     # Solicitant
                    row['Solicitare'],     # Solicitare
                    ora,                   # Ora
                    int(row['DurataInterventie']), # DurataInterventie
                    row['PersonalITC'],    # PersonalITC
                    row['Observatii'] if 'Observatii' in row else None,  # Observatii
                    int(row['ServiciuID']), # ServiciuID
                    'In Asteptare'         # Status initial
                )
                
                cursor.execute(query, params)
                
            except Exception as e:
                logging.error(f"Eroare la importul rândului: {str(e)}")
                continue
        
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Eroare la importul din CSV: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def reorder_nrcrt():
    """Reordonează NrCrt să înceapă de la 1 și să crească cu 1."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Dezactivăm IDENTITY dacă există
        cursor.execute("""
        IF EXISTS (SELECT 1 FROM sys.identity_columns 
                  WHERE object_id = OBJECT_ID('RegistruInterventii') 
                  AND name = 'NrCrt')
        BEGIN
            SET IDENTITY_INSERT RegistruInterventii OFF
        END
        """)
        
        # Facem update-ul folosind ROW_NUMBER()
        cursor.execute("""
        WITH CTE AS (
            SELECT NrCrt,
                   ROW_NUMBER() OVER (ORDER BY DataInterventie, ID) as NewNrCrt
            FROM RegistruInterventii
        )
        UPDATE CTE
        SET NrCrt = NewNrCrt
        """)
        
        conn.commit()
        logging.info("NrCrt a fost reordonat cu succes!")
        
        # Verificăm rezultatul
        cursor.execute("SELECT MIN(NrCrt) as Min, MAX(NrCrt) as Max, COUNT(*) as Total FROM RegistruInterventii")
        result = cursor.fetchone()
        logging.info(f"Verificare: Min={result[0]}, Max={result[1]}, Total={result[2]}")
        
    except Exception as e:
        logging.error(f"Eroare la reordonarea NrCrt: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def format_username(username):
    """Formatează username-ul în formatul corect (nume.prenume)"""
    # Dacă username-ul conține deja punct, îl returnăm așa cum este
    if '.' in username:
        return username
    
    # Dacă nu conține punct, încercăm să-l separăm în nume și prenume
    # Presupunem că primul cuvânt este numele și restul este prenumele
    parts = username.strip().split()
    if len(parts) >= 2:
        return f"{parts[0].lower()}.{'.'.join(parts[1:]).lower()}"
    return username.lower()

def add_user(username, password, serviciu_id):
    """Adaugă un utilizator nou în baza de date."""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Eroare la conectarea la baza de date"
        
        cursor = conn.cursor()
        
        # Formatăm username-ul în formatul corect
        formatted_username = format_username(username)
        logging.info(f"Formatăm username-ul din {username} în {formatted_username}")
        
        # Verificăm dacă username-ul există deja
        cursor.execute("SELECT COUNT(*) FROM Utilizatori WHERE NumeUtilizator = ?", (formatted_username,))
        if cursor.fetchone()[0] > 0:
            return False, "Utilizatorul există deja"
        
        # Hash-uim parola
        hashed_password = hash_password(password)
        
        # Adăugăm utilizatorul
        cursor.execute("""
            INSERT INTO Utilizatori (NumeUtilizator, Parola, ServiciuID)
            VALUES (?, ?, ?)
        """, (formatted_username, hashed_password, serviciu_id))
        
        conn.commit()
        logging.info(f"Am adăugat un utilizator nou {formatted_username} cu ID-ul serviciului {serviciu_id}")
        
        return True, "Utilizator adăugat cu succes"
        
    except Exception as e:
        logging.error(f"Eroare la adăugarea utilizatorului: {str(e)}")
        return False, f"Eroare la adăugarea utilizatorului: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_personal_it():
    """Obține lista personalului IT din baza de date."""
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("Nu s-a putut obține conexiunea la baza de date")
            return []
        
        cursor = conn.cursor()
        query = """
            SELECT NumeUtilizator
            FROM Utilizatori
            WHERE ServiciuID = (SELECT ID FROM Servicii WHERE Nume = 'IT')
            ORDER BY NumeUtilizator
        """
        
        cursor.execute(query)
        personal_it = [row[0] for row in cursor.fetchall()]
        
        logging.info(f"Lista personal IT obținută din baza de date: {personal_it}")
        return personal_it
        
    except Exception as e:
        logging.error(f"Eroare la obținerea listei personalului IT: {str(e)}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def is_it_personal(username):
    """Verifică dacă utilizatorul face parte din serviciul IT."""
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("Nu s-a putut obține conexiunea la baza de date")
            return False
        
        cursor = conn.cursor()
        query = """
            SELECT COUNT(*)
            FROM Utilizatori u
            JOIN Servicii s ON u.ServiciuID = s.ID
            WHERE u.NumeUtilizator = ? AND s.Nume = 'IT'
        """
        
        cursor.execute(query, normalize_username(username))
        count = cursor.fetchone()[0]
        
        return count > 0
        
    except Exception as e:
        logging.error(f"Eroare la verificarea serviciului IT pentru {username}: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reorder_nrcrt()
