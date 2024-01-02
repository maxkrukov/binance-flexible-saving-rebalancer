## Binance rebalancer
Tool for switching asset between spot and flexible saving balance.
Can be used in pair with trading bot when free spot asset is present
to get more profit. For example USDT APR is above 3-5% on flexible saving.

### Howto
1. Generate api key and api secret
2. Environment variables
   
|Variable|Spec|Value|
|---|---|---|
|API_KEY and API_SECRET|Binance api credentials|requred|
|ASSET|asset to rebalance|dafault: USDT|
|MIN_SPOT_AMOUNT|Min amount on spot wallet|default: 250|
|MIN_HOP|Min value to add for savings|default: 10|
|SPREAD|Max spread between MIN_SPOT_AMOUNT and MAX_SPOT_AMOUNT=(MIN_SPOT_AMOUNT+SPREAD)|default: 50|
|FUTURES_ENABLED|Ctrl futures balance|"True" or "False"|
|MIN_FUTURES_AMOUNT|Minimum free balance for futures account|100|

4. Installation 
##### Docker
```
cp .env-smaple .env
vim .env # Change it
docker build . -t binance-rebalancer:v1
docker run -it --rm --env-file .env binance-rebalancer:v1
``` 
##### Kubernetes
```
# edit values.yaml
helm upgrade --install binance-rebalancer ./rebalancer-helm  
```

##### Rest API
- Get balance (SPOT+Savings)
```
$ http GET http://binance-rebalancer:5001/balance

HTTP/1.1 200 OK
Connection: close
Content-Length: 15
Content-Type: application/json
Date: Tue, 02 Jan 2024 20:03:47 GMT
Server: Werkzeug/3.0.1 Python/3.11.6

30579.85480103

```
- Stake all amount of token ETH (for example ETH/USDT)
```
# return nothing. code 200 OK
http  POST binance-rebalancer:5001/action action=stake pair=ETH/USDT amount=0
```
- Redeem amount of token ETH (for example ETH/USDT)
```
# return "true\n" or "false\n". code 200 OK
http  POST binance-rebalancer:5001/action action=redeem pair=ETH/USDT amount=10 # where 10 - amount you want to sell 
```
##### Log example
```
INFO:apscheduler.executors.default:Running job "rebalancer (trigger: interval[0:00:30], next run at: 2024-01-02 19:58:45 UTC)" (scheduled at 2024-01-02 19:58:15.428337+00:00)
INFO:root:SPOT: 300.0, SAVING: 30279.82286946, FUTURES: 99.99999999 [777.24714207]
INFO:apscheduler.executors.default:Job "rebalancer (trigger: interval[0:00:30], next run at: 2024-01-02 19:58:45 UTC)" executed successfully
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:20] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:20] "POST /action HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:25] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:25] "POST /action HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:30] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:30] "POST /action HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:35] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:35] "POST /action HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:40] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:40] "POST /action HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:45] "GET /balance HTTP/1.1" 200 -
INFO:werkzeug:10.1.231.91 - - [02/Jan/2024 19:58:45] "POST /action HTTP/1.1" 200 -
```
