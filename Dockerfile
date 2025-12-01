FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for optional libraries (weasyprint needs some libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpango-1.0-0 \
       libgdk-pixbuf2.0-0 \
       libffi-dev \
       libxml2 \
       libxml2-dev \
       libxslt1-dev \
       zlib1g-dev \
       libssl-dev \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first for caching
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# copy project
COPY . /app

# collect static
ENV STATIC_ROOT=/app/static_collected
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "irib_programs.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1"]
