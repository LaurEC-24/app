## Cripteaza parolele din baza de date cu hash-uri
import pyodbc
from database import get_db_connection, hash_password

def is_password_hashed(password):
    """Verifică dacă parola este deja hash-uită (are 64 caractere și conține doar hex)."""
    if len(password) != 64:
        return False
    try:
        # Verifică dacă string-ul conține doar caractere hexadecimale
        int(password, 16)
        return True
    except ValueError:
        return False

def update_all_passwords():
    """Actualizează toate parolele din baza de date cu hash-uri."""
    try:
        conn = get_db_connection()
        if not conn:
            print("Nu s-a putut conecta la baza de date")
            return False
            
        cursor = conn.cursor()
        
        # Mai întâi luăm toate parolele existente
        query = "SELECT ID, NumeUtilizator, Parola FROM Utilizatori"
        cursor.execute(query)
        users = cursor.fetchall()
        
        updated_count = 0
        skipped_count = 0
        
        # Actualizăm fiecare parolă cu hash-ul său
        for user in users:
            user_id = user[0]
            username = user[1]
            current_password = user[2]
            
            # Verificăm dacă parola este deja hash-uită
            if is_password_hashed(current_password):
                print(f"Parola pentru utilizatorul {username} este deja hash-uită. Se sare peste.")
                skipped_count += 1
                continue
            
            # Generăm hash-ul parolei
            hashed_password = hash_password(current_password)
            
            # Actualizăm parola în baza de date
            update_query = "UPDATE Utilizatori SET Parola = ? WHERE ID = ?"
            cursor.execute(update_query, (hashed_password, user_id))
            print(f"Actualizat parola pentru utilizatorul: {username}")
            updated_count += 1
        
        conn.commit()
        print(f"\nRezultat:")
        print(f"- {updated_count} parole actualizate")
        print(f"- {skipped_count} parole sărite (deja hash-uite)")
        print(f"- {updated_count + skipped_count} total utilizatori verificați")
        return True
        
    except Exception as e:
        print(f"Eroare la actualizarea parolelor: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Începe actualizarea parolelor...")
    update_all_passwords()
