#!/bin/bash

# BTC Market Trades (>$1000)
echo "Launching BTC Market Trades Monitor..."
lxterminal -e crypto-monitor trades --pairs btcusdt --min-size 25000 &

# BTC Liquidations
echo "Launching BTC Liquidations Monitor..."
lxterminal -e crypto-monitor liquidations -p btcusdt -p avaxusdt -p solusdt -p ethusdt --min-size 1000 &
