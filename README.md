## Binance rebalancer
Tool for switching asset between spot and flexible saving balance.
Can be used in pair with trading bot when free spot asset is present
to get more profit. For example USDT APR is above 3-5% on flexible saving.

### Howto
1. Generate api key and api secret
2. Environment variables
|Variable|Spec|Value|
|API_KEY and API_SECRET|Binance api credentials|requred|
|ASSET|asset to rebalance|dafault: USDT|
|MIN_SPOT_AMOUNT|Min amount on spot wallet|default: 250|
|MIN_HOP|Min value to add for savings|default: 10|
|SPREAD|Max spread between MIN_SPOT_AMOUNT and MAX_SPOT_AMOUNT=(MIN_SPOT_AMOUNT+SPREAD)|default: 50|

3. Installation 
##### Docker
```
cp .env-smaple .env
vim .env # Change it
docker build . -t binance-rebalancer:v1
docker run -it --rm --env-file .env binance-rebalancer:v1
``` 
