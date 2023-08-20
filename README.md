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

4. Installation 
##### Docker
```
cp .env-smaple .env
vim .env # Change it
docker build . -t binance-rebalancer:v1
docker run -it --rm --env-file .env binance-rebalancer:v1
``` 


##### Log example
```
$ docker run -it --rm --env-file .env binance-rebalancer:v1
2023-08-20 11:47:46.763 UTC INFO root: SPOT: 271.52854,  SAVING: 501.94267855
2023-08-20 11:48:07.448 UTC INFO root: SPOT: 271.52854,  SAVING: 501.94267855
2023-08-20 11:48:28.133 UTC INFO root: SPOT: 271.52854,  SAVING: 501.94269656
2023-08-20 11:48:48.820 UTC INFO root: SPOT: 271.52854,  SAVING: 501.94269656
...
2023-08-20 11:56:19.202 UTC INFO root: Purchase 171.52854 USDT for flexible saving product
2023-08-20 11:56:19.690 UTC INFO root: {'purchaseId': 5162402326}
2023-08-20 11:56:19.690 UTC INFO root: SPOT: 271.52854,  SAVING: 501.94284055
2023-08-20 11:56:40.375 UTC INFO root: SPOT: 100.0,  SAVING: 673.47138056
2023-08-20 11:57:01.162 UTC INFO root: SPOT: 100.0,  SAVING: 673.47138056
...
2023-08-20 11:58:13.559 UTC INFO root: Redeem 150.0 USDT from flexible saving product
2023-08-20 11:58:14.062 UTC INFO root: {}
2023-08-20 11:58:14.062 UTC INFO root: SPOT: 100.0,  SAVING: 673.47142883
2023-08-20 11:58:34.757 UTC INFO root: SPOT: 250.0,  SAVING: 523.47142883
2023-08-20 11:58:55.442 UTC INFO root: SPOT: 250.0,  SAVING: 523.47142883

```
