#!/usr/bin/env python3

import atexit
import os
import logging
import re

from binance.spot import Spot as Client
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

from flask import Flask
from flask_restful import Api, Resource

from webargs import fields
from webargs.flaskparser import use_kwargs, parser, abort

# Configure logging for the app
config_logging(logging, logging.INFO)

# Load environment variables for Binance API
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# Ensure API keys are present
if not api_key or not api_secret:
    logging.error("API Key or Secret not set!")
    exit(1)

# Constants
RECV_WINDOW = 5000

# Initialize Binance Spot and Futures clients
spot_client = Client(api_key, api_secret, base_url="https://api.binance.com")
um_futures_client = UMFutures(key=api_key, secret=api_secret, base_url="https://fapi.binance.com")

# Initialize Flask app and API
app = Flask(__name__)
api = Api(app)

# Helper functions to retrieve balance information
def spot_ua(asset):
    """Retrieve user's asset balance in the spot account."""
    try:
        ua = spot_client.user_asset(recvWindow=RECV_WINDOW)
        for i in ua:
            if i['asset'] == asset:
                return float(i['free'])
    except ClientError as error:
        logging.error(f"Spot UA error: {error}")
    return 0.0

def staking_sa(asset):
    """Retrieve user's asset balance in flexible savings."""
    try:
        sa = spot_client.get_flexible_product_position(current=1, size=100, recvWindow=RECV_WINDOW)
        if sa and 'rows' in sa:
            for i in sa['rows']:
                if i['asset'] == asset:
                    return float(i['totalAmount'])
    except ClientError as error:
        logging.error(f"Staking SA error: {error}")
    return 0.0

def futures_balance(asset):
    """Retrieve user's asset balance in futures."""
    try:
        futures_balance = um_futures_client.balance(recvWindow=6000)
        for i in futures_balance:
            if i['asset'] == asset:
                return {
                    "futures_full": float(i['balance']),
                    "futures_free": float(i['availableBalance'])
                }
    except ClientError as error:
        logging.error(f"Futures Balance error: {error}")
    return {"futures_full": 0.0, "futures_free": 0.0}

# REST API endpoints
class Balance(Resource):
    add_args = {
        "asset": fields.Str(required=True)
    }

    @use_kwargs(add_args)
    def post(self, asset):
        """Calculate and return the total balance from spot and savings accounts, along with futures balance."""
        try:
            spot_balance = spot_ua(asset)
            savings_balance = staking_sa(asset)
            futures_bal = futures_balance(asset)

            total_balance = spot_balance + savings_balance

            return {
                "spot_balance": spot_balance,
                "savings_balance": savings_balance,
                "total_balance": total_balance,  # Sum of spot and savings
                "futures_balance": {
                    "futures_full": futures_bal["futures_full"],  # Full balance in futures
                    "futures_free": futures_bal["futures_free"]   # Free balance in futures
                }
            }
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {"message": "An unexpected error occurred"}, 500

class Action(Resource):
    add_args = {
        "asset": fields.Str(required=True),
        "action": fields.Str(required=True),
        "amount": fields.Float(required=True)
    }

    @use_kwargs(add_args)
    def post(self, asset, action, amount):
        """Performs stake or redeem actions for Spot/Savings or futures transfers."""
        try:
            # --- STAKE to Flexible Savings (Spot) ---
            if action == "stake":
                if amount <= 0:
                    return {"message": "Invalid amount. Staking amount must be greater than zero."}, 400

                on_spot = spot_ua(asset)
                if on_spot == 0:
                    return {"message": f"No {asset} available in Spot account."}, 400

                # Stake the min of (requested, available)
                amount_to_stake = min(amount, on_spot)
                logging.info(f"Purchasing {amount_to_stake} {asset} for flexible savings.")

                try:
                    spot_client.subscribe_flexible_product(
                        productId=f"{asset}001",
                        amount=amount_to_stake,
                        recvWindow=RECV_WINDOW
                    )
                    return {"message": f"Staked {amount_to_stake} {asset} to savings."}
                except ClientError as error:
                    logging.error(f"Error staking {asset}: {error}")
                    return {"message": f"Failed to stake {asset}"}, 500

            # --- REDEEM from Flexible Savings (Spot) ---
            elif action == "redeem":
                on_saving = staking_sa(asset)
                on_spot = spot_ua(asset)

                # If spot balance alone is enough, do nothing for savings
                if on_spot >= amount:
                    return {"message": f"Enough {asset} available in Spot to proceed with redemption."}, 200

                to_redeem = max(0, amount - on_spot)
                if to_redeem <= 0:
                    return {"message": "Nothing to redeem from savings."}, 400

                if to_redeem > on_saving:
                    to_redeem = on_saving

                try:
                    logging.info(f"Redeeming {to_redeem} {asset} from savings.")
                    spot_client.redeem_flexible_product(
                        productId=f"{asset}001",
                        amount=to_redeem,
                        recvWindow=RECV_WINDOW
                    )
                    return {"message": f"Redeemed {to_redeem} {asset} from savings."}
                except ClientError as error:
                    logging.error(f"Error redeeming {asset}: {error}")
                    return {"message": f"Failed to redeem {asset}"}, 500

            # --- SPOT (transfer) TO Futures ---
            elif action == "futures":
                if amount <= 0:
                    return {"message": "Invalid amount. Transfer amount must be greater than zero."}, 400

                on_spot = spot_ua(asset)
                if on_spot == 0:
                    return {"message": f"No {asset} available in Spot account."}, 400

                # Transfer only as much as we have in Spot
                to_f_wallet = min(amount, on_spot)
                logging.info(f"Transferring {to_f_wallet} {asset} from Spot to Futures wallet.")

                try:
                    # type=1 => Spot to Futures
                    response = spot_client.futures_transfer(
                        asset=asset,
                        amount=to_f_wallet,
                        type=1  # 1 = Spot -> Futures
                    )
                    logging.info(f"futures_transfer response: {response}")
                    return {"message": f"Transferred {to_f_wallet} {asset} from Spot to Futures."}
                except ClientError as error:
                    logging.error(f"Error transferring to Futures: {error}")
                    return {"message": f"Failed to transfer {asset} to Futures."}, 500

            # --- REDEEM (transfer) FROM Futures ---
            elif action == "redeem_futures":
                if amount <= 0:
                    return {"message": "Invalid amount. Transfer amount must be greater than zero."}, 400

                fut_bal = futures_balance(asset)  # returns {"futures_full": ..., "futures_free": ...}
                fut_free = fut_bal["futures_free"]

                if fut_free == 0:
                    return {"message": f"No free {asset} balance in Futures."}, 400

                # Transfer only as much as we have free in Futures
                from_f_wallet = min(amount, fut_free)
                logging.info(f"Transferring {from_f_wallet} {asset} from Futures to Spot wallet.")

                try:
                    # type=2 => Futures to Spot
                    response = spot_client.futures_transfer(
                        asset=asset,
                        amount=from_f_wallet,
                        type=2  # 2 = Futures -> Spot
                    )
                    logging.info(f"futures_transfer response: {response}")
                    return {"message": f"Transferred {from_f_wallet} {asset} from Futures to Spot."}
                except ClientError as error:
                    logging.error(f"Error transferring from Futures: {error}")
                    return {"message": f"Failed to transfer {asset} from Futures."}, 500

            # If action doesn't match any known pattern
            return {"message": "Invalid action"}, 400

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {"message": "An unexpected error occurred"}, 500


# Error handler for Flask-RESTful to handle webargs parsing errors
@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """Returns JSON error response for webargs parsing errors."""
    abort(error_status_code, errors=err.messages)

if __name__ == "__main__":
    # Ensure the scheduler shuts down when the app exits
    atexit.register(lambda: print("Application shutting down..."))

    # Add API resources
    api.add_resource(Action, "/action")
    api.add_resource(Balance, "/balance")

    # Start Flask app
    app.run(host="0.0.0.0", port=5001, debug=False)

