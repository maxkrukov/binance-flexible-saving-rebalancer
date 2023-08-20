FROM alpine:latest

ENV API_KEY=""
ENV API_SECRET=""
ENV ASSET=USDT
ENV MIN_SPOT_AMOUNT=250
ENV MIN_HOP=10
ENV SPREAD=50

RUN apk add bash python3 py3-pip && pip3 install binance-connector

COPY rebalancer.py /rebalancer.py

ENTRYPOINT ["/usr/bin/python3", "/rebalancer.py"]
