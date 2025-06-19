FROM ubuntu:22.04

# Create user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Install basic tools
RUN sudo apt update && sudo apt install -y curl gnupg git python3 python3-pip

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Optional: Pull the model ahead of time
RUN ollama pull nomic-embed-text

# Create working directory
WORKDIR /app

# Copy files
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY --chown=user . /app

# Expose ports
EXPOSE 8000
EXPOSE 11434

# Start Ollama and FastAPI
CMD ollama serve & uvicorn app:app --host 0.0.0.0 --port 8000
