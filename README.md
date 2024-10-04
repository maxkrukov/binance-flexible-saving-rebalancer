# Binance Flask API

This Flask-based API provides a simple interface to interact with Binance's Spot, Flexible Savings, and Futures accounts. You can use it to check balances, stake assets into flexible savings, and redeem assets from savings.

## Requirements

- Python 3.8 or higher
- Binance API credentials
- Flask and dependencies listed in `requirements.txt`

### Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Set your Binance API credentials as environment variables:

```bash
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
```

## Running the Application

Run the Flask API locally:

```bash
python3 rebalancer.py
```

By default, the API will run on `http://0.0.0.0:5001`.

## API Endpoints

### 1. `/balance` (POST)

Retrieve the balance of a specific asset from the Spot, Flexible Savings, and Futures accounts.

- **Parameters**:
  - `asset` (string): The asset symbol (e.g., `BTC`, `ETH`).
  
- **Example Request (cURL)**:

```bash
curl -X POST http://127.0.0.1:5001/balance \
-H "Content-Type: application/json" \
-d '{"asset": "BTC"}'
```

- **Example Request (Python)**:

```python
import requests

url = "http://127.0.0.1:5001/balance"
data = {"asset": "BTC"}
response = requests.post(url, json=data)
print(response.json())
```

- **Example Response**:

```json
{
  "spot_balance": 0.05,
  "savings_balance": 0.01,
  "total_balance": 0.06,
  "futures_balance": {
    "futures_full": 0.02,
    "futures_free": 0.01
  }
}
```

### 2. `/action` (POST)

Perform an action (`stake` or `redeem`) for a given asset.

- **Parameters**:
  - `asset` (string): The asset symbol (e.g., `BTC`, `ETH`).
  - `action` (string): The action to perform (`stake` or `redeem`).
  - `amount` (float): The amount of the asset to stake or redeem.

#### Stake Action
- Stakes the given amount of an asset into Binance's flexible savings product. If the amount is greater than available, it stakes the maximum possible.

- **Example Request (cURL)**:

```bash
curl -X POST http://127.0.0.1:5001/action \
-H "Content-Type: application/json" \
-d '{"asset": "BTC", "action": "stake", "amount": 0.01}'
```

- **Example Request (Python)**:

```python
import requests

url = "http://127.0.0.1:5001/action"
data = {
    "asset": "BTC",
    "action": "stake",
    "amount": 0.01
}
response = requests.post(url, json=data)
print(response.json())
```

- **Example Response**:

```json
{
  "message": "Staked 0.01 BTC to savings"
}
```

#### Redeem Action
- Redeems the given amount of an asset from flexible savings. If part of the required amount is available in the spot account, it only redeems the rest from savings.

- **Example Request (cURL)**:

```bash
curl -X POST http://127.0.0.1:5001/action \
-H "Content-Type: application/json" \
-d '{"asset": "BTC", "action": "redeem", "amount": 0.01}'
```

- **Example Request (Python)**:

```python
import requests

url = "http://127.0.0.1:5001/action"
data = {
    "asset": "BTC",
    "action": "redeem",
    "amount": 0.01
}
response = requests.post(url, json=data)
print(response.json())
```

- **Example Response**:

```json
{
  "message": "Redeemed 0.01 BTC from savings"
}
```

## Error Handling

The API returns meaningful error messages if something goes wrong. For example, if the provided amount is invalid or no assets are available to stake or redeem, an appropriate error message is returned.

- **Example Error Response**:

```json
{
  "message": "No BTC available in spot account"
}
```

## Logging

All actions and errors are logged using the Python logging module. Logs are output to the console by default.

