FROM python:3.11-slim-buster

RUN mkdir -p /app/
COPY chat/requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src
COPY chat/ /app/chat

WORKDIR /app/
ENV PYTHONPATH "/app"

CMD ["python", "/app/chat/bot.py"]