# Folosim o imagine Python oficială
FROM python:3.11-slim

# Instalăm ODBC Driver pentru SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

# Setăm directorul de lucru
WORKDIR /app

# Copiem fișierele necesare
COPY requirements.txt .
COPY *.py .
COPY config.ini .

# Instalăm dependențele Python
RUN pip install --no-cache-dir -r requirements.txt

# Expunem portul pentru Streamlit
EXPOSE 8501

# Comanda de pornire
CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0"]
