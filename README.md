# AppElcen - Sistem de Gestiune Intervenții

Aplicație web pentru gestionarea și urmărirea intervențiilor tehnice, dezvoltată cu Streamlit.

## Caracteristici

- Autentificare securizată cu persistența sesiunii
- Gestionare intervenții (adăugare, vizualizare, aprobare)
- Interfață intuitivă pentru utilizatori
- Sistem de logging pentru monitorizare
- Suport pentru roluri diferite (IT, management)

## Tehnologii Utilizate

- Python 3.9+
- Streamlit
- SQL Server
- Docker

## Instalare

1. Clonați repository-ul:
```bash
git clone [URL_REPOSITORY]
```

2. Creați un mediu virtual și instalați dependențele:
```bash
python -m venv venv
source venv/bin/activate  # Pentru Linux/Mac
venv\Scripts\activate     # Pentru Windows
pip install -r requirements.txt
```

3. Configurați baza de date:
- Creați un fișier `config.ini` după modelul `config.ini.example`
- Configurați conexiunea la baza de date SQL Server

4. Rulați aplicația:
```bash
streamlit run main.py
```

## Docker

Pentru a rula aplicația în Docker:

```bash
docker-compose up -d
```

## Securitate

- Configurați `security_config.py` pentru politicile de securitate
- Nu includeți fișierele de configurare cu credențiale în Git
- Folosiți variabile de mediu pentru informații sensibile

## Contribuții

Contribuțiile sunt binevenite! Vă rugăm să:
1. Faceți fork la repository
2. Creați un branch pentru feature-ul nou
3. Faceți commit la modificări
4. Creați un Pull Request

## Licență

[Specificați licența]
