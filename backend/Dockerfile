FROM python:3.11-slim

WORKDIR /app

ENV HOST=0.0.0.0
ENV PORT=8001
ENV ENVIRONMENT=production
ENV ALLOWED_ORIGINS=*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
