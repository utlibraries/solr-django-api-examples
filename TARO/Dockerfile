FROM python:3.11
LABEL maintainer "POD SQUAD <LIT-Pod-Squad@austin.utexas.edu>"

ENV PYTHONPATH=/app
COPY . /app/
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache gunicorn

RUN useradd -ms /bin/bash glib
RUN chown -R glib /app
USER glib

EXPOSE 9000
