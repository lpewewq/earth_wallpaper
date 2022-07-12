FROM python:3.8-slim

WORKDIR /api

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .
COPY common.py .
COPY skyfield_wallpaper.py .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
