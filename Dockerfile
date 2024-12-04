# Folosim o imagine Python oficială
FROM python:3.11-slim

# Instalăm ODBC Driver pentru SQL Server într-un singur layer
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setăm directorul de lucru
WORKDIR /app

# Copiem doar requirements.txt primul pentru a folosi cache-ul Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem restul fișierelor
COPY . .

# Expunem portul Streamlit
EXPOSE 8501

# Comandă pentru rulare
CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0"]