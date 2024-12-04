##import din csv in databese la coloana de PersonalITC
import pandas as pd
import pyodbc
from datetime import datetime
import csv

def get_db_connection():
    """Creează conexiunea la baza de date."""
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=10.10.8.12,1433;'
        'DATABASE=Interventii;'
        'UID=Laur;'
        'PWD=Hh1236996321;'
    )
    return conn

def clean_duration(duration_str):
    """Curăță și convertește durata în număr întreg."""
    if pd.isna(duration_str) or duration_str == '':
        return 0
    try:
        # Încearcă să convertească string-ul în float și apoi în int
        return int(float(str(duration_str).replace(',', '.')))
    except:
        return 0

def clean_date(date_str):
    """Curăță și validează data."""
    if pd.isna(date_str) or date_str == '':
        return datetime.now().strftime('%Y-%m-%d')
    try:
        return pd.to_datetime(date_str, format='%d.%m.%Y').strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')

def read_csv_file():
    """Citește fișierul CSV și returnează un DataFrame."""
    # Mai întâi citim primele linii pentru a determina structura
    with open('Registru de Interventii.csv', 'r', encoding='windows-1252') as f:
        first_lines = [next(f) for _ in range(5)]
        print("Primele linii din fișier:")
        for i, line in enumerate(first_lines):
            print(f"Linia {i+1}: {line.strip()}")
    
    # Încercăm să citim cu diferite separatoare
    separators = [';', ',', '\t']
    for sep in separators:
        try:
            df = pd.read_csv('Registru de Interventii.csv',
                           encoding='windows-1252',
                           sep=sep,
                           engine='python',  # Mai flexibil pentru parsing
                           on_bad_lines='skip')  # Ignoră liniile problematice
            
            # Curățăm numele coloanelor de spații în plus
            df.columns = df.columns.str.strip()
            
            # Verificăm dacă avem coloanele necesare
            required_columns = ['DataInterventie', 'Zi', 'Solicitant', 'Solicitare', 
                              'Ora', 'DurataInterventiei', 'PersonalITC']
            
            if all(col in df.columns for col in required_columns):
                print(f"\nCSV citit cu succes folosind separatorul: '{sep}'")
                print("Coloane găsite:", df.columns.tolist())
                return df
            
        except Exception as e:
            print(f"Încercare eșuată cu separatorul '{sep}': {str(e)}")
            continue
    
    raise Exception("Nu s-a putut citi fișierul CSV cu niciun separator!")

def import_csv():
    try:
        # Citim CSV-ul folosind funcția specializată
        df = read_csv_file()
        
        # Curățăm datele și eliminăm rândurile complet goale
        df = df.fillna('')  # Înlocuim NaN cu string gol
        df = df.dropna(how='all')  # Eliminăm rândurile complet goale
        
        # Conectare la baza de date
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query pentru inserare
        query = """
            INSERT INTO RegistruInterventii 
            (DataInterventie, Zi, Solicitant, Solicitare, Ora, 
            DurataInterventie, PersonalITC, Observatii, ServiciuID, Status,
            DataAprobare, AprobatDe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Valori implicite
        serviciu_id = 1
        status = 'Aprobat'
        data_aprobare = '2024-11-29 12:00:00'
        aprobat_de = 'virgil.ionita'
        
        # Contor pentru progres
        successful_imports = 0
        total_rows = len(df)
        errors = []
        
        print(f"\nÎncepem importul pentru {total_rows} înregistrări...")
        
        # Iterăm prin fiecare rând
        for index, row in df.iterrows():
            try:
                # Verificăm dacă rândul are date valide
                if not any(str(row[col]).strip() for col in df.columns):
                    continue  # Sărim peste rândurile goale
                
                # Pregătim parametrii cu validare pentru fiecare câmp
                data = clean_date(row['DataInterventie'])
                ora = str(row['Ora']).strip() if pd.notna(row['Ora']) else '00:00'
                durata = clean_duration(row['DurataInterventiei'])
                
                # Curățăm și validăm observațiile
                observatii = str(row.get('Observatii', '')).strip()
                if pd.isna(observatii) or observatii == '':
                    observatii = None
                
                params = (
                    data,                   # DataInterventie
                    str(row['Zi']).strip() or 'N/A',  # Zi
                    str(row['Solicitant']).strip() or 'N/A',  # Solicitant
                    str(row['Solicitare']).strip() or 'N/A',  # Solicitare
                    ora,                    # Ora
                    durata,                 # DurataInterventie
                    str(row['PersonalITC']).strip() or 'N/A',  # PersonalITC
                    observatii,            # Observatii
                    serviciu_id,           # ServiciuID
                    status,                # Status
                    data_aprobare,         # DataAprobare
                    aprobat_de             # AprobatDe
                )
                
                cursor.execute(query, params)
                successful_imports += 1
                
                # Afișăm progresul la fiecare 50 de înregistrări
                if (index + 1) % 50 == 0:
                    print(f"Progres: {index + 1}/{total_rows} înregistrări procesate")
                    conn.commit()  # Commit intermediar
                
            except Exception as e:
                error_msg = f"Eroare la rândul {index + 1}: {str(e)}\nDate rând: {dict(row)}"
                errors.append(error_msg)
                print(error_msg)
                continue
        
        # Final commit
        conn.commit()
        
        print(f"\nImport finalizat!")
        print(f"Total înregistrări procesate cu succes: {successful_imports}/{total_rows}")
        
        if errors:
            print("\nErori întâlnite:")
            for error in errors[:10]:  # Afișăm primele 10 erori
                print(error)
            if len(errors) > 10:
                print(f"...și încă {len(errors) - 10} alte erori")
        
        return True
        
    except Exception as e:
        print(f"Eroare generală: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Începe importul din CSV...")
    import_csv()
