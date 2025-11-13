FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

#System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

#Requirements instalation
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#Copy app, expose port and startup
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]