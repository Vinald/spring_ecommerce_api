FROM python:3.7.9

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /root/ivr

RUN apt-get update
RUN apt-get install asterisk asterisk-mp3 -y

COPY requirements.txt .
COPY config.ini.test config.ini

RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash", "ivr-docker.sh"]
