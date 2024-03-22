FROM python:3.10-slim

WORKDIR /app

COPY common common
COPY daemon daemon

RUN pip install -r daemon/requirements.txt

ENV PTREE_USERNAME=${PTREE_USERNAME}
ENV PTREE_PASSWORD=${PTREE_PASSWORD}
ENV DATA_DIRECTORY=${DATA_DIRECTORY}

CMD ["python", "-m", "daemon.main"]
