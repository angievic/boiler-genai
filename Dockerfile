FROM python:3.9

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Set Python path
ENV PYTHONPATH=/app

CMD ["sh", "-c","fastapi run main.py & streamlit run ./edtech/generate_educational_video.py --server.port=8501"]
