#!/usr/bin/env python3

import atexit
import os
import time
import logging
import re

from binance.spot import Spot as Client
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError

from apscheduler.schedulers.background import BackgroundScheduler

from expiringdict import ExpiringDict

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
client = Client(api_key, api_secret, base_url = "https://api.binance.com")
# FUTURES
um_futures_client = UMFutures(key=api_key, secret=api_secret, base_url = "https://fapi.binance.com")

app = Flask(__name__)
api = Api(app)

bal = 0.0
sa = client.savings_account()["positionAmountVos"]
ua = client.user_asset(recvWindow=5000)

def rebalancer():
    global sa
    global ua
    sa = client.savings_account()["positionAmountVos"]
    ua = client.user_asset(recvWindow=5000)

    global vars_with_expiry
    vars_with_expiry = ExpiringDict(max_age_seconds=300, max_len=100)


    def spot_ua(asset):
                for i in ua:
                    if i['asset'] == asset:
                        return i['free']
                return 0.0

    def staking_sa(asset):
                for i in sa:
                    if i['asset'] == asset:
                        return i['amount']
                return 0.0


    on_saving = round(float(staking_sa(asset=asset)), 8)
    on_spot = round(float(spot_ua(asset=asset)), 8)


    # FUTURES-SPOT
    if futures_enabled:
            try:
                futures_balance = um_futures_client.balance(recvWindow=6000)
                for i in futures_balance:
                    if i['asset'] == asset:
                        futures_full = round(float(i['balance']), 8)
                        futures_free = round(float(i['availableBalance']), 8)
                        # logging.info(f"Futures balance: free - {futures_free} {asset}, full - {futures_full} {asset}")
                        if futures_free < min_futures_amount and on_saving > min_futures_amount:
                            to_f_wallet = min_futures_amount - futures_free
                            if to_f_wallet > 0.1:
                                logging.info(f"Transfer {to_f_wallet} {asset} to Future wallet")
                                logging.info(client.futures_transfer(asset=asset, amount=to_f_wallet, type=1))
                        elif futures_free > min_futures_amount + spread:
                            from_f_wallet = futures_free - min_futures_amount
                            if from_f_wallet > 0.1:
                                logging.info(f"Transfer {from_f_wallet} {asset} to Spot wallet")
                                logging.info(client.futures_transfer(asset=asset, amount=from_f_wallet, type=2))

            except ClientError as error:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )

    # SPOT-SAVINGS
    try:
        if on_spot < min_spot_amount:
           add_amount_to_spot = round(min_spot_amount - on_spot, 8)
           if on_saving >= add_amount_to_spot:
              logging.info(f"Redeem {add_amount_to_spot} {asset} from flexible saving product")
              logging.info(
                 client.savings_flexible_redeem(productId=f"{asset}001", amount=add_amount_to_spot, type="NORMAL")
              )
           else:
              logging.info(f"Too low savings balance to add asset {asset}. SPOT: {on_spot},  SAVING: {on_saving}")

        elif on_spot > min_spot_amount + spread:
           remove_amount_from_spot = round(on_spot - min_spot_amount, 8)
           if remove_amount_from_spot >= min_hop:
              logging.info(f"Purchase {remove_amount_from_spot} {asset} for flexible saving product")
              logging.info(client.savings_purchase_flexible_product(productId=f"{asset}001", amount=remove_amount_from_spot))

    except ClientError as error:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )
    logging.info(f"SPOT: {on_spot}, SAVING: {on_saving}, FUTURES: {futures_free} [{futures_full}]")
    global bal
    bal = on_spot + on_saving

# REST API

class Balance(Resource):
    def get(self):
        return bal

class Action(Resource):
    add_args = {
            "pair": fields.Str(required=True),
            "action": fields.Str(required=True),
            "amount": fields.Float(required=True)
          }

    @use_kwargs(add_args)
    def post(self, pair, action, amount):

        # global vars
        #sa = client.savings_account()["positionAmountVos"]
        #ua = client.user_asset(recvWindow=5000)

        def spot_ua(token):
                for i in ua:
                    if i['asset'] == token:
                        return i['free']
                return 0.0

        def staking_sa(token):
                for i in sa:
                    if i['asset'] == token:
                        return i['amount']
                return 0.0


        # STAKE
        if action == "stake":

                    token = re.sub("/.+", "", pair)

                    # lock token
                    if vars_with_expiry[token] == "locked":
                        return f"Token: {token} locked"

                    on_saving = round(float(staking_sa(token)), 8)
                    on_spot = round(float(spot_ua(token)), 8)

                    try:
                        if on_saving + on_spot > 0:
                            if on_spot/(on_saving + on_spot) > 0.005:
                                logging.info(f"Purchase {on_spot} {token} for flexible saving product")
                                logging.info(client.savings_purchase_flexible_product(productId=f"{token}001", amount=on_spot))

                    except ClientError as error:
                                logging.error(
                                    "Found error {}. status: {}, error code: {}, error message: {}".format(
                                        asset, error.status_code, error.error_code, error.error_message
                                    )
                                )

        # REDEEM
        if action == "redeem":

                token = re.sub("/.+", "", pair)

                on_saving = round(float(staking_sa(token)), 8)
                on_spot = round(float(spot_ua(token)), 8)

                # Lock token to avoid staking
                vars_with_expiry[token] = "locked"

                if on_spot >= amount:
                    return True
                else:
                    if on_saving + on_spot < amount:
                        logging.info(f"Not enough {token} to sell via bot. Need {amount - (on_saving + on_spot)} more")
                        return False
                    else:
                        toadd = amount - on_spot
                        logging.info(f"Redeem {toadd} {token} to sell via bot")
                        logging.info(
                            client.savings_flexible_redeem(productId=f"{token}001", amount=toadd, type="NORMAL")
                        )
                        return True
                return False

# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(error_status_code, errors=err.messages)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=rebalancer, trigger="interval", seconds=30)
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    api.add_resource(Action, "/action")
    api.add_resource(Balance, "/balance")
    app.run(host="0.0.0.0", port=5001, debug=False)
