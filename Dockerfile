FROM alpine:latest

ENV API_KEY=""
ENV API_SECRET=""

COPY requirements.txt requirements.txt

RUN apk add bash python3 py3-pip && pip3 install -r requirements.txt

COPY rebalancer.py /rebalancer.py

ENTRYPOINT ["/usr/bin/python3", "/rebalancer.py"]
