#!/bin/bash

# BTC Market Trades (>$1000)
echo "Launching BTC Market Trades Monitor..."
crypto-monitor trades --pairs btcusdt --min-size 1000

# BTC Liquidations
echo "Launching BTC Liquidations Monitor..."
crypto-monitor liquidations --pairs btcusdt