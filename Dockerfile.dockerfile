FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Download spaCy model
RUN python -m spacy download en_core_web_md

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]