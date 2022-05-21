FROM python:3.8

WORKDIR /daemon

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .
COPY common.py .
COPY ptree.py .
COPY BlackMarble_2016_Himawari8_preprocessed.png .


CMD ["python", "main.py"]
