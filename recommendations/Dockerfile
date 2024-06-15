FROM python:3.11-slim-buster

RUN mkdir -p /app/
COPY recommendations/requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src
COPY recommendations/ /app/recommendations

WORKDIR /app/
ENV PYTHONPATH "/app"

CMD ["python", "/app/recommendations/main.py"]