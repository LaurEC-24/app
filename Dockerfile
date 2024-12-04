# Folosim o imagine Python oficială
FROM python:3.11-slim

# Instalăm dependențele necesare
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Adăugăm repository-ul Microsoft și instalăm ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Configurăm driver-ul ODBC
RUN echo "[ODBC Driver 18 for SQL Server]\nDriver = /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.*.so.*.*.* \nUsageCount = 1\n" >> /etc/odbcinst.ini

# Setăm directorul de lucru
WORKDIR /app

# Copiem doar requirements.txt primul pentru a folosi cache-ul Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem restul fișierelor
COPY . .

# Expunem portul Streamlit
EXPOSE 8501

# Comanda de pornire
CMD ["streamlit", "run", "main.py"]