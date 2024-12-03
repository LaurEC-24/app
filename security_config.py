from datetime import timedelta

# Configurări pentru sesiune
SESSION_TIMEOUT = timedelta(hours=8)  # Sesiunea expiră după 8 ore
MAX_LOGIN_ATTEMPTS = 5  # Numărul maxim de încercări de autentificare
LOGIN_COOLDOWN = timedelta(minutes=15)  # Timpul de așteptare după prea multe încercări

# Configurări pentru parole
MIN_PASSWORD_LENGTH = 8
REQUIRE_SPECIAL_CHAR = True
REQUIRE_NUMBER = True
REQUIRE_UPPERCASE = True

# Configurări pentru logging
LOG_AUTH_ATTEMPTS = True
LOG_SENSITIVE_OPERATIONS = True

# Lista de caractere permise pentru input
ALLOWED_SPECIAL_CHARS = set('-_.@() ')  # Caractere speciale permise în input

def validate_password_strength(password):
    """Validează puterea parolei."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, "Parola trebuie să aibă cel puțin 8 caractere"
    
    if REQUIRE_SPECIAL_CHAR and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Parola trebuie să conțină cel puțin un caracter special"
    
    if REQUIRE_NUMBER and not any(c.isdigit() for c in password):
        return False, "Parola trebuie să conțină cel puțin o cifră"
    
    if REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Parola trebuie să conțină cel puțin o literă mare"
    
    return True, "Parola îndeplinește cerințele de securitate"

def sanitize_input(text, allow_special=False):
    """Curăță input-ul de caractere potențial periculoase."""
    if not text:
        return text
    
    # Convertim la string și eliminăm whitespace la capete
    text = str(text).strip()
    
    # Eliminăm caractere periculoase
    if allow_special:
        # Păstrăm doar caracterele alfanumerice și cele special permise
        return ''.join(c for c in text if c.isalnum() or c in ALLOWED_SPECIAL_CHARS)
    else:
        # Păstrăm doar caracterele alfanumerice
        return ''.join(c for c in text if c.isalnum())
