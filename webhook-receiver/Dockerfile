FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set environment variables
ENV PORT=8082
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8082

# Run the application
CMD ["python", "app.py"]
