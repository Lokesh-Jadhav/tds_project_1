# --------------------------
# Hugging Face Flask Deployment Dockerfile
# --------------------------

# Use a small Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 7860

# Set environment variables
ENV PORT=7860
ENV HOST=0.0.0.0

# Run Flask app
CMD ["python", "app.py"]
