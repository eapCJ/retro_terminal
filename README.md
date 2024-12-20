╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                        CRYPTO MARKET MONITORING TOOL                         ║
║                                                                             ║
║     ★★  Track the Whales. Follow the Money. Master the Market.  ★★         ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

+                              ⚠️ DISCLAIMER ⚠️
+ This tool is provided as-is for personal use and educational purposes only.
+ No financial advice is given. Use at your own risk. The creator accepts no
+ responsibility for any trading decisions or losses incurred while using this tool.
+
                        ╔═══════════════════════════╗                          
                        ║    REAL-TIME TRACKING     ║                          
                        ╚═══════════════════════════╝                          

           ★★ AQUAMAN ($10M+)  |  ◈◈ WHALE ($1M+)  |  ◆◆ ORCA ($500K+)
           ▲▲ SHARK ($250K+)   |  ■■ DOLPHIN ($100K+)  |  ►► FISH ($50K+)

A professional-grade market monitoring tool that brings institutional-level trade 
flow analysis to your terminal. Track significant market movements and liquidations 
in real-time with visual and audio feedback. This is an experimental project and
may contain bugs or inaccuracies. Not intended for production use.

"Where whales make waves, we make signals."

Core Purpose
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

+⚠️ Important Notes:
+- This tool is not guaranteed to capture all trades or liquidations
+- Data may be delayed or incomplete
+- No warranty is provided for accuracy or reliability
+- Not suitable for automated trading systems

## Technical Implementation
- Asynchronous WebSocket handling with websockets library
- Thread-safe display management
- Robust error handling and reconnection logic
- Efficient trade categorization system
- Terminal manipulation with ANSI escape codes
- Sound generation with custom frequency/duration
- European number formatting for global usage

## Known Limitations
- May miss some trades during high volatility
- Audio alerts may not work on all systems
- Terminal display may break in some environments
- WebSocket connection can be unstable
- Not all edge cases are handled

This is an experimental project created for personal use and learning purposes.
Use at your own risk. Not financial advice.
