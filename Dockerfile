FROM alpine:latest

ENV API_KEY=""
ENV API_SECRET=""
ENV ASSET=USDT
ENV MIN_SPOT_AMOUNT=250
ENV MIN_HOP=10
ENV SPREAD=50

ENV FUTURES_ENABLED="True"
ENV MIN_FUTURES_AMOUNT=100 

RUN apk add bash python3 py3-pip && pip3 install apscheduler flask flask_restful webargs joblib binance-connector==3.3.1 binance-futures-connector==3.3.1

COPY rebalancer.py /rebalancer.py

ENTRYPOINT ["/usr/bin/python3", "/rebalancer.py"]
