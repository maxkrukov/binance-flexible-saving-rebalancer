import atexit
import os
import time
import logging

from binance.spot import Spot as Client
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask
from flask_restful import Api, Resource

from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort

config_logging(logging, logging.INFO)

api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
asset = os.getenv('ASSET')
min_spot_amount = float(os.getenv('MIN_SPOT_AMOUNT'))
min_hop = float(os.getenv('MIN_HOP'))
spread = float(os.getenv('SPREAD'))

futures_enabled = eval(os.getenv('FUTURES_ENABLED'))
min_futures_amount = float(os.getenv('MIN_FUTURES_AMOUNT'))

# SPOT
spot_client = Client(apikey, apisecret, base_url = "https://api.binance.com")
# FUTURES
um_futures_client = UMFutures(key=apikey, secret=apisecret, base_url = "https://fapi.binance.com")

app = Flask(__name__)
api = Api(app)

def rebalancer():
    # FUTURES-SPOT
    if futures_enabled:
            try:
                futures_balance = um_futures_client.balance(recvWindow=6000)
                for i in futures_balance:
                    if i['asset'] == asset:
                        futures_full = round(float(i['balance']), 8)
                        futures_free = round(float(i['availableBalance']), 8)
                        logger.info(f"Futures balance: free - {futures_free} {asset}, full - {futures_full} {asset}")
                        if futures_free < min_futures_amount - 1:
                            to_f_wallet = min_futures_amount - futures_free
                            logging.info(f"Transfer {to_f_wallet} {asset} to Future wallet")
                            logging.info(spot_client.futures_transfer(asset=asset, amount=to_f_wallet, type=1))
                        elif futures_free > min_futures_amount + spread:
                            from_f_wallet = futures_free - min_futures_amount
                            logging.info(f"Transfer {from_f_wallet} {asset} to Spot wallet")
                            logging.info(spot_client.futures_transfer(asset=asset, amount=from_f_wallet, type=2))

            except ClientError as error:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )

    # SPOT-SAVINGS
    try:
        for i in spot_client.savings_account()["positionAmountVos"]:
          if i['asset'] == asset:
            on_saving = float(i['amount'])
        response = spot_client.user_asset(asset=asset, recvWindow=5000)
        on_spot = float(response[0]['free'])

        if on_spot < min_spot_amount:
           add_amount_to_spot = round(min_spot_amount - on_spot, 8)
           if on_saving >= add_amount_to_spot:
              logging.info(f"Redeem {add_amount_to_spot} {asset} from flexible saving product")
              logging.info(
                 spot_client.savings_flexible_redeem(productId=f"{asset}001", amount=add_amount_to_spot, type="NORMAL")
              )
           else:
              logging.info(f"Too low savings balance to add asset {asset}. SPOT: {on_spot},  SAVING: {on_saving}")

        elif on_spot > min_spot_amount + spread:
           remove_amount_from_spot = round(on_spot - min_spot_amount, 8)
           if remove_amount_from_spot >= min_hop:
              logging.info(f"Purchase {remove_amount_from_spot} {asset} for flexible saving product")
              logging.info(spot_client.savings_purchase_flexible_product(productId=f"{asset}001", amount=remove_amount_from_spot))

    except ClientError as error:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )

    logging.info(f"SPOT: {on_spot}, SAVING: {on_saving}, FUTURES: {futures_free} [{futures_full}]")

# REST API

class Balance(Resource):
    def get(self):
        return {"message": "balance"}

class Action(Resource):
    """An addition endpoint."""

    add_args = {
            "pair": fields.String(required=True),
            "action": fields.String(required=True),
            "amount": fields.Float(required=True)
          }

    @use_kwargs(add_args)
    def post(self, pair, action, amount):
        """An addition endpoint."""
        return f"{pair} {action} {amount}"


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(error_status_code, errors=err.messages)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=rebalancer, trigger="interval", seconds=20)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    api.add_resource(Action, "/action")
    api.add_resource(Balance, "/balance")
    app.run(port=5001, debug=False)
