import pyodbc
import os

def test_connection():
    try:
        # Afișăm driverele ODBC disponibile
        print("\nDrivere ODBC disponibile:")
        print("-" * 50)
        for driver in pyodbc.drivers():
            print(driver)

        # Construim și afișăm string-ul de conexiune
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=10.10.8.12,1433;"
            "DATABASE=Interventii;"
            "UID=Laur;"
            "PWD=Hh1236996321;"
            "TrustServerCertificate=yes;"
        )
        print("\nÎncercare conectare cu string:")
        print("-" * 50)
        print(conn_str.replace("Hh1236996321", "****"))

        # Încercăm conexiunea
        print("\nÎncercare conectare...")
        print("-" * 50)
        conn = pyodbc.connect(conn_str)
        
        print("Conexiune reușită!")
        
        # Testăm o interogare simplă
        cursor = conn.cursor()
        cursor.execute("SELECT @@version")
        row = cursor.fetchone()
        print("\nVersiune SQL Server:")
        print("-" * 50)
        print(row[0])
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nEroare la conectare:")
        print("-" * 50)
        print(str(e))

if __name__ == "__main__":
    test_connection()
