FROM python:3.10-slim
RUN echo "DOCKERFILE: SCRAPING-Start"
WORKDIR /app
COPY requirements.txt .
RUN echo "DOCKERFILE: SCRAPING-Pip install requirements"
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
