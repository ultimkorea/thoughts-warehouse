FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone --depth=1 https://github.com/ultimkorea/thoughts-warehouse.git /app
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["python", "/app/bot.py"]
