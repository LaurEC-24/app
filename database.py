import pyodbc
import configparser
from datetime import datetime
import hashlib
import os
from pathlib import Path

def get_db_connection():
    """Creează și returnează o conexiune la baza de date."""
    try:
        # Încercăm să citim credențialele în siguranță
        config = configparser.ConfigParser()
        
        # Căutăm config.ini în directorul curent pentru dezvoltare locală
        local_config = Path(__file__).parent / 'config.ini'
        
        if local_config.exists():
            config.read(local_config)
            host = config['MySQL']['host']
            port = config['MySQL']['port']
            database = config['MySQL']['database']
            user = config['MySQL']['user']
            password = config['MySQL']['password']
        else:
            # Folosim variabilele de mediu pentru Docker
            host = os.getenv('DB_HOST')
            port = os.getenv('DB_PORT')
            database = os.getenv('DB_NAME')
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')

        if not all([host, port, database, user, password]):
            raise Exception("Lipsesc configurări necesare pentru baza de date")

        conn_str = (
            "DRIVER={SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
        )
        
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Eroare la conectarea la baza de date: {str(e)}")
        return None

def hash_password(password):
    """Creează un hash pentru parolă folosind SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def normalize_username(username):
    """
    Normalizează username-ul pentru a se potrivi cu formatul din baza de date.
    Caută username-ul ignorând punctele și apoi returnează formatul corect din baza de date.
    """
    try:
        conn = get_db_connection()
        if not conn:
            return username
            
        cursor = conn.cursor()
        
        # Căutăm username-ul ignorând punctele
        clean_username = username.replace('.', '')
        query = """
            SELECT NumeUtilizator 
            FROM Utilizatori 
            WHERE REPLACE(NumeUtilizator, '.', '') = ?
        """
        
        cursor.execute(query, (clean_username,))
        result = cursor.fetchone()
        
        if result:
            print(f"DEBUG: Found matching username in database: {result[0]}")
            return result[0]
            
        # Dacă nu găsim nimic, returnăm username-ul original
        print(f"DEBUG: No matching username found for {username}")
        return username
        
    except Exception as e:
        print(f"DEBUG: Error in normalize_username: {str(e)}")
        return username
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_credentials(username, password):
    """Verifică credențialele utilizatorului în baza de date."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            print("DEBUG: Nu s-a putut realiza conexiunea la baza de date")
            return {'success': False, 'message': 'Nu s-a putut realiza conexiunea la baza de date'}
            
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        
        # Normalizăm username-ul
        normalized_username = normalize_username(username)
        if not normalized_username:
            return {'success': False, 'message': 'Utilizator negăsit'}

        query = """
        SELECT TOP 1 Id, Username, ServiciuId 
        FROM Users 
        WHERE Username = ? AND Password = ?
        """
        cursor.execute(query, (normalized_username, hashed_password))
        result = cursor.fetchone()

        if result:
            return {
                'success': True,
                'username': result[1],
                'serviciu': result[2]
            }
        return {'success': False, 'message': 'Credențiale invalide'}
        
    except Exception as e:
        print(f"DEBUG: Error during credential verification: {str(e)}")
        return {'success': False, 'message': f'Eroare de conectare: {str(e)}'}
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"DEBUG: Error closing cursor: {str(e)}")
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"DEBUG: Error closing connection: {str(e)}")

def get_user_service(username):
    """Obține serviciul asociat unui utilizator."""
    try:
        conn = get_db_connection()
        if not conn:
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
        print(f"DEBUG: Getting service for normalized username: {normalized_username}")
        
        cursor.execute(query, (normalized_username,))
        result = cursor.fetchone()
        
        if result:
            print(f"DEBUG: Found service {result[0]} for user {normalized_username}")
            return result[0]
        return None
        
    except Exception as e:
        print(f"Eroare la obținerea serviciului: {str(e)}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
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
        print(f"Eroare la obținerea intervențiilor: {str(e)}")
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
            print("Eroare: Textul solicitării este prea lung (maxim 1000 caractere)")
            return False
            
        # Formatăm datele pentru SQL Server
        data_sql = data_interventie.strftime('%Y-%m-%d')
        ora_sql = ora  # ora este deja în format HH:MM
        durata_sql = int(durata) if durata else 0
        serviciu_id_sql = int(serviciu_id) if serviciu_id else None
        observatii_sql = observatii if observatii else None
        
        query = """
            INSERT INTO RegistruInterventii 
            (DataInterventie, Zi, Solicitant, Solicitare, Ora, DurataInterventie, PersonalITC, Observatii, ServiciuID, Status)
            VALUES 
            (CONVERT(DATE, ?), ?, ?, ?, CONVERT(TIME, ?), ?, ?, ?, ?, 'In Asteptare')
        """
        
        params = (
            data_sql,           # DataInterventie (date)
            zi,                 # Zi (varchar)
            solicitant,         # Solicitant (varchar)
            solicitare,         # Solicitare (varchar)
            ora_sql,           # Ora (time)
            durata_sql,        # DurataInterventie (int)
            personal_itc,       # PersonalITC (varchar)
            observatii_sql,     # Observatii (varchar, nullable)
            serviciu_id_sql     # ServiciuID (int)
        )
        
        cursor.execute(query, params)
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Eroare la adăugarea intervenției: {str(e)}")
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
        print(f"Eroare la obținerea serviciilor: {str(e)}")
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
            return False
        
        cursor = conn.cursor()
        
        query = """
            SELECT 1
            FROM Utilizatori
            WHERE NumeUtilizator = ? AND NumeUtilizator = 'virgil.ionita'
        """
        cursor.execute(query, (username,))
        return cursor.fetchone() is not None
        
    except Exception as e:
        print(f"Eroare la verificarea rolului: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def aproba_interventie(nr_crt, approved_by, action='Aprobat'):
    """Aprobă sau respinge o intervenție folosind procedura stocată."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Executăm procedura stocată
        cursor.execute("{CALL ApproveIntervention (?, ?, ?)}", (nr_crt, approved_by, action))
        
        # Obținem rezultatul
        result = cursor.fetchone()
        if result and result[0] == 'Success':
            conn.commit()
            return True
        return False
        
    except Exception as e:
        print(f"Eroare la procesarea intervenției: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

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
        print(f"Eroare la ștergerea intervențiilor: {str(e)}")
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
                print(f"Eroare la importul rândului: {str(e)}")
                continue
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Eroare la importul din CSV: {str(e)}")
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
        print("NrCrt a fost reordonat cu succes!")
        
        # Verificăm rezultatul
        cursor.execute("SELECT MIN(NrCrt) as Min, MAX(NrCrt) as Max, COUNT(*) as Total FROM RegistruInterventii")
        result = cursor.fetchone()
        print(f"Verificare: Min={result[0]}, Max={result[1]}, Total={result[2]}")
        
    except Exception as e:
        print(f"Eroare la reordonarea NrCrt: {str(e)}")
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
        print(f"DEBUG: Formatting username from {username} to {formatted_username}")
        
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
        print(f"DEBUG: Added new user {formatted_username} with service ID {serviciu_id}")
        
        return True, "Utilizator adăugat cu succes"
        
    except Exception as e:
        print(f"Eroare la adăugarea utilizatorului: {str(e)}")
        return False, f"Eroare la adăugarea utilizatorului: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reorder_nrcrt()
