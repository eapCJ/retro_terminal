#!/bin/bash

# BTC Market Trades (>$1000)
echo "Launching BTC Market Trades Monitor..."
lxterminal --title="BTC Market Trades" -e crypto-monitor trades --pairs btcusdt --min-size 25000 &

# BTC Liquidations
echo "Launching BTC Liquidations Monitor..."
lxterminal --title="BTC Liquidations" -e crypto-monitor liquidations -p btcusdt -p avaxusdt -p solusdt -p ethusdt --min-size 1000 &
