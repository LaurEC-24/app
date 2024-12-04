import pyodbc
from database import get_db_connection

def check_service_mapping():
    """Verifică maparea serviciilor pentru utilizatori."""
    try:
        conn = get_db_connection()
        if not conn:
            print("Nu s-a putut conecta la baza de date")
            return
            
        cursor = conn.cursor()
        
        # Afișăm toate serviciile disponibile
        print("\nServicii disponibile:")
        print("-" * 40)
        cursor.execute("SELECT Id, Nume FROM Servicii")
        services = cursor.fetchall()
        for service in services:
            print(f"ID: {service[0]}, Nume: {service[1]}")
            
        # Afișăm maparea utilizator-serviciu
        print("\nMapare Utilizator-Serviciu:")
        print("-" * 40)
        query = """
        SELECT u.NumeUtilizator, u.ServiciuId, s.Nume as NumeServiciu
        FROM Utilizatori u
        LEFT JOIN Servicii s ON u.ServiciuId = s.Id
        """
        cursor.execute(query)
        mappings = cursor.fetchall()
        for mapping in mappings:
            print(f"Utilizator: {mapping[0]}")
            print(f"ServiciuID: {mapping[1]}")
            print(f"Nume Serviciu: {mapping[2]}")
            print("-" * 20)
            
        # Verifică specific pentru laurentiu.henegariu
        print("\nVerificare specifică pentru laurentiu.henegariu:")
        print("-" * 40)
        cursor.execute("""
            SELECT u.NumeUtilizator, u.ServiciuId, s.Nume
            FROM Utilizatori u
            LEFT JOIN Servicii s ON u.ServiciuId = s.Id
            WHERE u.NumeUtilizator = ?
        """, ('laurentiu.henegariu',))
        user_service = cursor.fetchone()
        if user_service:
            print(f"Username: {user_service[0]}")
            print(f"ServiciuID: {user_service[1]}")
            print(f"Nume Serviciu: {user_service[2]}")
        else:
            print("Utilizatorul nu a fost găsit sau nu are serviciu asociat")
            
    except Exception as e:
        print(f"Eroare: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_service_mapping()
