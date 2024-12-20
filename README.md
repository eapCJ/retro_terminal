# Crypto Market Monitoring Tool

## Core Purpose
A real-time cryptocurrency market monitoring tool that tracks:
- Live trades
- Liquidations (forced closures of leveraged positions)

## Key Features

### Market Size Categories
The system categorizes trades/liquidations into distinct tiers with visual and audio indicators:

| Category | Size | Symbol |
|----------|------|--------|
| Whale | ≥$1M | ◆ |
| Shark | ≥$500K | ▲ |
| Dolphin | ≥$250K | ♦ |
| Swordfish | ≥$100K | ⚔ |
| Plankton | < $100K | - |

### Real-time Monitoring
- Connects to Binance WebSocket API
- Monitors multiple trading pairs simultaneously
- Supports preset configurations for different coin groups (major, DeFi, gaming, layer1)
- Provides visual feedback with color-coded output

### Smart Notifications
- Configurable sound alerts for significant trades
- Different sound patterns for different market size categories
- Statistical analysis to identify unusual trade sizes
- Visual highlighting for exceptional events

### Flexible Configuration
- Customizable minimum trade size filters
- Preset market size filters (all, small, medium, large, whale)
- Configurable coin pairs and groupings
- Sound threshold customization

## Usage
The tool can be run in two modes:
1. Interactive mode
2. Command-line mode with specific parameters (e.g., minimum size: $100,000)

## Technical Implementation
- Uses WebSocket for real-time data streaming
- Implements object-oriented design with base classes and inheritance
- Includes error handling and logging
- Provides statistical analysis of trade volumes
- Uses colorama for terminal color output
- Implements sound generation for alerts

This project creates a professional-grade market monitoring tool that helps traders and analysts track significant market movements and liquidations in real-time with visual and audio feedback.