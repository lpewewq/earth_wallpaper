FROM python:3.8-slim

WORKDIR /daemon

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY main.py .
COPY common.py .
COPY ptree.py .
COPY BlackMarble_2016_Himawari8_preprocessed.png .

ENV PTREE_USERNAME=${PTREE_USERNAME}
ENV PTREE_PASSWORD=${PTREE_PASSWORD}

CMD ["python", "main.py"]
