#!/bin/bash

helm -n binance-rebalancer upgrade -i --create-namespace binance-rebalancer ./rebalancer-helm
