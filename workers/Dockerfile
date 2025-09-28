FROM python:3.11-slim

WORKDIR /worker

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY ../backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt apscheduler

COPY ../backend/app ./app
COPY schedules.py ./schedules.py

CMD ["python", "schedules.py"]
