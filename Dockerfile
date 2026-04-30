# Squad Sheet Generator — production image
# Bundles Python + TeX Live so pdflatex works out of the box on Render/Fly/Railway.

FROM python:3.11-slim

# Install TeX Live (only the packages we need — keeps the image lean)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so Docker can cache them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Render injects $PORT at runtime; default to 8501 for local docker runs
ENV PORT=8501
EXPOSE 8501

# Streamlit needs to bind to 0.0.0.0 and disable CORS for hosted environments
CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
