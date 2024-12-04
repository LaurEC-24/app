import hashlib

def test_password_variations():
    """Testează diferite variante de hash pentru parola '12345'."""
    # Hash țintă din baza de date
    target_hash = "6baad6f126fa53233f5120dd32225d4a9eeaea26dce58789f0b3b6efcdb0dadb"
    password = "12345"
    
    print(f"Testare metode de hash pentru parola: {password}")
    print(f"Hash țintă: {target_hash}")
    print("\nRezultate:")
    
    # Test 1: MD5 apoi SHA256
    md5_first = hashlib.md5(password.encode()).hexdigest()
    md5_sha256 = hashlib.sha256(md5_first.encode()).hexdigest()
    print(f"\n1. MD5 apoi SHA256:\n{md5_sha256}")
    
    # Test 2: SHA256 apoi MD5
    sha256_first = hashlib.sha256(password.encode()).hexdigest()
    sha256_md5 = hashlib.md5(sha256_first.encode()).hexdigest()
    print(f"\n2. SHA256 apoi MD5:\n{sha256_md5}")
    
    # Test 3: SHA256 cu padding zero la început
    padded_start = hashlib.sha256(("0" + password).encode()).hexdigest()
    print(f"\n3. SHA256 cu '0' la început:\n{padded_start}")
    
    # Test 4: SHA256 cu encoding Windows-1252
    win1252_hash = hashlib.sha256(password.encode('cp1252')).hexdigest()
    print(f"\n4. SHA256 cu Windows-1252:\n{win1252_hash}")
    
    # Test 5: SHA256 cu salt numeric
    salt_num = "123"
    salted_num = hashlib.sha256((password + salt_num).encode()).hexdigest()
    print(f"\n5. SHA256 cu salt numeric '123':\n{salted_num}")
    
    # Test 6: SHA256 cu password repetat
    double_pass = hashlib.sha256((password + password).encode()).hexdigest()
    print(f"\n6. SHA256 cu password repetat:\n{double_pass}")
    
    # Test 7: SHA256 cu bytes în hex
    hex_pass = password.encode().hex()
    hex_hash = hashlib.sha256(hex_pass.encode()).hexdigest()
    print(f"\n7. SHA256 cu bytes în hex:\n{hex_hash}")
    
    # Test 8: SHA256 cu reverse password
    rev_pass = password[::-1]
    rev_hash = hashlib.sha256(rev_pass.encode()).hexdigest()
    print(f"\n8. SHA256 cu password inversat:\n{rev_hash}")
    
    # Test 9: SHA256 cu salt specific aplicației
    app_salt = "InterventiiElcen2023"
    app_hash = hashlib.sha256((password + app_salt).encode()).hexdigest()
    print(f"\n9. SHA256 cu salt specific aplicației:\n{app_hash}")

if __name__ == "__main__":
    test_password_variations()
