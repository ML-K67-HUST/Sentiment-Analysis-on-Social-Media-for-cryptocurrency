FROM python:3.10-slim

WORKDIR /src

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data to avoid runtime downloads
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt vader_lexicon averaged_perceptron_tagger maxent_ne_chunker words stopwords

COPY . .