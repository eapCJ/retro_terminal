# Crypto Market Monitoring Tool 🐋

> Track the Whales. Follow the Money. Master the Market.

## ⚠️ Disclaimer
This tool is provided as-is for personal use and educational purposes only. No financial advice is given. Use at your own risk. The creator accepts no responsibility for any trading decisions or losses incurred while using this tool.

## Overview
A professional-grade market monitoring tool that brings institutional-level trade flow analysis to your terminal. Track significant market movements and liquidations in real-time with visual and audio feedback.

> "Where whales make waves, we make signals."

### Core Purpose
- Real-time monitoring of live cryptocurrency trades
- Tracking of liquidations (forced closures of leveraged positions)

## Market Size Categories

The system categorizes trades/liquidations into distinct tiers:

| Category | Min Size | Symbol | Alert Repeats | Sound Profile |
|----------|----------|--------|---------------|---------------|
| Aquaman | $10M+ | ★★ | x5 | High pitch, long duration |
| Whale | $1M+ | ◈◈ | x4 | Higher pitch, longer duration |
| Orca | $500K+ | ◆◆ | x3 | High pitch, medium duration |
| Shark | $250K+ | ▲▲ | x2 | Medium pitch, medium duration |
| Dolphin | $100K+ | ■■ | x2 | Lower pitch, short duration |
| Fish | $50K+ | ►► | x1 | Base pitch, short duration |
| Shrimp | $10K+ | ▪▪ | x1 | No sound |
| Plankton | < $10K | ·· | x1 | No sound |

## Features

### Real-time Monitoring
- Multi-pair monitoring (default: BTC, ETH, BNB, SOL, DOGE, XRP)
- Color-coded display with size-based categorization
- Automatic terminal size adjustment
- Real-time price tracking

### Smart Notifications
- Configurable audio alerts:
  - Adjustable frequency (pitch)
  - Customizable duration
  - Volume control
- Visual blinking for large trades
- Color-coded trade types (green=buy, red=sell)
- Priority sound alerts for liquidations

### Configuration Options
- Command line filters:
  - `--min-size`: Filter by minimum trade size
  - `--min-category`: Filter by market category
  - `--pairs`: Specify trading pairs to monitor
- Debug options (`--debug --log-file`)
- Display customization
- European number formatting support

## Usage

The tool supports two operation modes:
1. Interactive mode
2. Command-line mode with parameters (e.g., `--min-size 100000`)

### ⚠️ Important Notes
- Not guaranteed to capture all trades/liquidations
- Data may be delayed or incomplete
- No warranty for accuracy/reliability
- Not suitable for automated trading

## Technical Details

### Implementation
- Asynchronous WebSocket handling
- Thread-safe display management
- Robust error handling & reconnection
- Efficient trade categorization
- ANSI terminal manipulation
- Custom sound generation
- International number formatting

### Known Limitations
- Potential trade misses during high volatility
- Audio compatibility varies by system
- Terminal display issues possible
- WebSocket connection stability
- Edge case handling limitations

---

**Note**: This is an experimental project created for personal use and learning purposes. Use at your own risk. Not financial advice.
