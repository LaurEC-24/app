import pyodbc
import os
import hashlib

# Setăm variabilele de mediu
os.environ['DB_HOST'] = '10.10.8.12'
os.environ['DB_PORT'] = '1433'
os.environ['DB_NAME'] = 'Interventii'
os.environ['DB_USER'] = 'Laur'
os.environ['DB_PASSWORD'] = 'Hh1236996321'

def get_db_connection():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={os.getenv('DB_HOST')},{os.getenv('DB_PORT')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Eroare conexiune: {str(e)}")
        return None

def test_different_hashes(password):
    """Testează diferite metode de hash pentru a găsi potrivirea corectă."""
    print(f"\nTestare diferite metode de hash pentru parola: {password}")
    
    # SHA256 cu diferite encoding-uri
    encodings = ['utf-8', 'ascii', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            hash_val = hashlib.sha256(password.encode(enc)).hexdigest()
            print(f"SHA256 cu {enc}: {hash_val}")
        except Exception as e:
            print(f"Eroare la {enc}: {str(e)}")
    
    # SHA256 cu diferite salt-uri
    salts = ['AppElcen', 'app', 'elcen', password.upper()]
    for salt in salts:
        # Salt la început
        hash_start = hashlib.sha256((salt + password).encode()).hexdigest()
        print(f"SHA256 cu salt '{salt}' la început: {hash_start}")
        
        # Salt la sfârșit
        hash_end = hashlib.sha256((password + salt).encode()).hexdigest()
        print(f"SHA256 cu salt '{salt}' la sfârșit: {hash_end}")
    
    # Hash-uri multiple
    double_hash = hashlib.sha256(hashlib.sha256(password.encode()).digest()).hexdigest()
    print(f"Double SHA256: {double_hash}")
    
    triple_hash = hashlib.sha256(hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()).hexdigest()
    print(f"Triple SHA256: {triple_hash}")
    
    # Hash cu username ca salt (common practice)
    username = "laurentiu.henegariu"
    hash_with_username = hashlib.sha256((password + username).encode()).hexdigest()
    print(f"SHA256 cu username ca salt: {hash_with_username}")
    
    print(f"\nHash din baza de date: 6baad6f126fa53233f5120dd32225d4a9eeaea26dce58789f0b3b6efcdb0dadb")

def main():
    # Testăm diferite variante de hash
    test_different_hashes("12345")
    
    conn = get_db_connection()
    if not conn:
        print("Nu s-a putut realiza conexiunea!")
        return

    cursor = conn.cursor()
    
    try:
        print("\nStructura tabelului Utilizatori:")
        cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Utilizatori'")
        for col in cursor.fetchall():
            print(f"{col[0]}: {col[1]}")

        print("\nPrimele înregistrări din Utilizatori:")
        cursor.execute("SELECT TOP 5 * FROM Utilizatori")
        columns = [column[0] for column in cursor.description]
        print("Coloane:", columns)
        for row in cursor.fetchall():
            print(row)

    except Exception as e:
        print(f"Eroare la interogare: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
