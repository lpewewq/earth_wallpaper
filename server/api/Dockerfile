FROM python:3.10-slim

WORKDIR /app

COPY common common
COPY api api

RUN pip install -r api/requirements.txt

ENV DATA_DIRECTORY=${DATA_DIRECTORY}

EXPOSE 80

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]
