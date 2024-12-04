import pyodbc
from database import get_db_connection

def check_username_format():
    """Verifică formatul exact al username-urilor în baza de date."""
    try:
        conn = get_db_connection()
        if not conn:
            print("Nu s-a putut conecta la baza de date")
            return
            
        cursor = conn.cursor()
        
        # Afișăm toate username-urile din baza de date
        query = "SELECT NumeUtilizator FROM Utilizatori"
        cursor.execute(query)
        users = cursor.fetchall()
        
        print("\nUsername-uri în baza de date:")
        print("-" * 40)
        for user in users:
            print(f"'{user[0]}'")
            
        # Căutăm specific username-ul nostru
        test_username = "laurentiuhenegariu"
        print(f"\nCăutare pentru: '{test_username}'")
        print("-" * 40)
        
        # Căutare exactă
        cursor.execute("SELECT NumeUtilizator FROM Utilizatori WHERE NumeUtilizator = ?", (test_username,))
        exact_match = cursor.fetchone()
        print(f"Potrivire exactă: {exact_match[0] if exact_match else 'Nu există'}")
        
        # Căutare cu LIKE
        cursor.execute("SELECT NumeUtilizator FROM Utilizatori WHERE NumeUtilizator LIKE ?", (f"%{test_username}%",))
        like_match = cursor.fetchone()
        print(f"Potrivire parțială: {like_match[0] if like_match else 'Nu există'}")
        
        # Căutare ignorând punctele
        cursor.execute("SELECT NumeUtilizator FROM Utilizatori WHERE REPLACE(NumeUtilizator, '.', '') = ?", (test_username.replace('.', ''),))
        no_dots_match = cursor.fetchone()
        print(f"Potrivire fără puncte: {no_dots_match[0] if no_dots_match else 'Nu există'}")
        
    except Exception as e:
        print(f"Eroare: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_username_format()
