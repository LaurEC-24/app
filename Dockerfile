# Folosim o imagine Ubuntu 20.04 ca imagine de bază
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Bucharest

# Instalăm Python și alte dependențe necesare
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalăm Microsoft ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Setăm directorul de lucru
WORKDIR /app

# Upgrade pip
RUN python3.9 -m pip install --upgrade pip

# Copiem requirements.txt și instalăm dependențele Python
COPY requirements.txt .
RUN python3.9 -m pip install --no-cache-dir -r requirements.txt

# Copiem restul fișierelor
COPY . .

# Expunem portul Streamlit
EXPOSE 8501

# Comanda de pornire
CMD ["python3.9", "-m", "streamlit", "run", "main.py"]