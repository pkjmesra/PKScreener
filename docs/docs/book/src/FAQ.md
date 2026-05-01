---
title: FAQ
weight: 92
---

# Frequently Asked Questions

## Getting Started

### How do I install PKScreener?

pip install pkscreener

### Do I need a Zerodha account for real-time data?

Yes, real-time data requires a Zerodha account and PKBrokers setup. However, the tool works with cached data without one.

### Can I use PKScreener for US markets?

Yes! PKScreener supports NASDAQ stocks.

## Technical

### Why is my scan taking so long?

The first scan downloads data. Subsequent scans use cached data and are faster.

### How can I improve scan performance?

- Enable cacheEnabled in configuration
- Use specific indices
- Apply volume and price filters early

### What data intervals are supported?

Intraday: 1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m
Daily: 1d
Weekly: 5d

## Data & Caching

### Where is data stored?

Data is cached in ~/.pkscreener/ directory.

### How fresh is the real-time data?

During market hours, data updates every 5 minutes.

### Can I run scans after market hours?

Yes! The system uses cached EOD data, ensuring 24x7 availability.

## Scans & Results

### What's the difference between Breakout and Consolidation?

Breakout: Price moving above resistance with volume
Consolidation: Price trading within a range

### Can I chain multiple scanners together?

Yes! Use piped scanners with the >| operator.

Example: X:12:9:2.5:>|X:0:31:

## Troubleshooting

### "No module named 'pkscreener'" error

Ensure PKScreener is installed: pip install pkscreener

### TA-Lib installation fails

PKScreener works without TA-Lib using pandas-ta as fallback.

### How can I contribute?

See Contributing Guide for guidelines.
