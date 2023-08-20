#!/usr/bin/env python3

import os
import time
import signal
import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging

api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
asset = os.getenv('ASSET')
min_spot_amount = float(os.getenv('MIN_SPOT_AMOUNT'))
min_hop = float(os.getenv('MIN_HOP'))
spread = float(os.getenv('SPREAD'))

config_logging(logging, logging.INFO)

client = Client(api_key, api_secret)

def run():
  for i in client.savings_account()["positionAmountVos"]:
    if i['asset'] == asset:
      on_saving = float(i['amount'])
  response = client.user_asset(asset=asset, recvWindow=5000)
  on_spot = float(response[0]['free'])

  if on_spot < min_spot_amount:
     add_amount_to_spot = min_spot_amount - on_spot
     if on_saving >= add_amount_to_spot:
        logging.info(f"Redeem {add_amount_to_spot} {asset} from flexible saving product")
        logging.info(
           client.savings_flexible_redeem(productId=f"{asset}001", amount=add_amount_to_spot, type="NORMAL")
        )
     else:
        logging.info(f"Too low savings balance to add asset {asset}. SPOT: {on_spot},  SAVING: {on_saving}")

  elif on_spot > min_spot_amount + spread:
     remove_amount_from_spot = on_spot - min_spot_amount
     if remove_amount_from_spot >= min_hop:
        logging.info(f"Purchase {remove_amount_from_spot} {asset} for flexible saving product")
        logging.info(client.savings_purchase_flexible_product(productId=f"{asset}001", amount=remove_amount_from_spot))

  logging.info(f"SPOT: {on_spot},  SAVING: {on_saving}")

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, *args):
    self.kill_now = True

if __name__ == '__main__':
  killer = GracefulKiller()
  while not killer.kill_now:
    run()
    time.sleep(20)
  logging.info("Process was killed gracefully")
