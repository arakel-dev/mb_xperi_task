FROM python:3.12.2-slim
LABEL authors="arakel-dev"

WORKDIR /application

COPY app.py .
COPY search.py .
COPY sql.py .
COPY test_main.py .
COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python", "app.py"]