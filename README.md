# Crypto Market Monitoring Tool

## Core Purpose
A real-time cryptocurrency market monitoring tool that tracks:
- Live trades
- Liquidations (forced closures of leveraged positions)

## Key Features

### Market Size Categories
The system categorizes trades/liquidations into distinct tiers with visual and audio indicators:

| Category | Min Size | Symbol | Repeat | Sound |
|----------|----------|--------|--------|-------|
| Aquaman | $10M+ | ★★ | x5 | High pitch, long duration |
| Whale | $1M+ | ◈◈ | x4 | Higher pitch, longer duration |
| Orca | $500K+ | ◆◆ | x3 | High pitch, medium duration |
| Shark | $250K+ | ▲▲ | x2 | Medium pitch, medium duration |
| Dolphin | $100K+ | ■■ | x2 | Lower pitch, short duration |
| Fish | $50K+ | ►► | x1 | Base pitch, short duration |
| Shrimp | $10K+ | ▪▪ | x1 | No sound |
| Plankton | < $10K | ·· | x1 | No sound |

### Real-time Monitoring
- Monitors multiple trading pairs simultaneously (default: BTC, ETH, BNB, SOL, DOGE, XRP)
- Color-coded display with size-based categorization
- Automatic terminal size adjustment
- Real-time price tracking for monitored pairs

### Smart Notifications
- Size-based audio alerts with configurable:
  * Frequency (pitch)
  * Duration
  * Volume
- Visual blinking for large trades
- Color-coded trade types (green for buys, red for sells)
- Higher priority sounds for liquidations

### Flexible Configuration
- Command line filters:
  * By minimum trade size (--min-size)
  * By category (--min-category)
  * By trading pairs (--pairs)
- Debug logging options (--debug --log-file)
- Configurable display settings
- European number formatting

## Usage
The tool can be run in two modes:
1. Interactive mode
2. Command-line mode with specific parameters (e.g., minimum size: $100,000)

## Technical Implementation
- Asynchronous WebSocket handling with websockets library
- Thread-safe display management
- Robust error handling and reconnection logic
- Efficient trade categorization system
- Terminal manipulation with ANSI escape codes
- Sound generation with custom frequency/duration
- European number formatting for global usage

This project creates a professional-grade market monitoring tool that helps traders and analysts track significant market movements and liquidations in real-time with visual and audio feedback.# retro_terminal
