#!/usr/bin/env python3
"""
PKScreener Documentation Migration Script
Converts existing Sphinx/RST documentation to mdBook format
"""

import os
import shutil
import re
from pathlib import Path

class MDBookMigrator:
    def __init__(self, docs_dir: str = "docs", book_dir: str = "docs/book"):
        self.docs_dir = Path(docs_dir)
        self.book_dir = Path(book_dir)
        self.src_dir = self.book_dir / "src"
        self.assets_dir = self.book_dir / "src/assets"
        
    def setup_mdbook_structure(self):
        """Create mdBook directory structure"""
        print("Creating mdBook structure...")
        
        self.src_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        self._create_book_config()
        self._create_summary()
        
        print("mdBook structure created")
    
    def _create_book_config(self):
        """Create book.toml configuration"""
        config = '''[book]
authors = ["pkjmesra"]
language = "en"
multilingual = false
src = "src"
title = "PKScreener Documentation"
description = "Complete documentation for PKScreener - Professional Stock Screening Tool"

[output.html]
git-repository-url = "https://github.com/pkjmesra/PKScreener"
edit-url-template = "https://github.com/pkjmesra/PKScreener/edit/main/docs/book/src/{path}"
site-url = "/PKScreener/"
default-theme = "light"
preferred-dark-theme = "navy"
additional-css = ["custom.css"]

[output.html.fold]
enable = true
level = 1

[output.html.search]
enable = true
limit-results = 30

[build]
build-dir = "book"
create-missing = false
'''
        
        with open(self.book_dir / "book.toml", "w") as f:
            f.write(config)
    
    def _create_summary(self):
        """Create SUMMARY.md with book structure"""
        summary = '''# Summary

[Introduction](README.md)

## User Guide

- [Getting Started](README.md)
- [Scanners Overview](SCAN_WORKFLOWS.md)
- [Results Interpretation](README.md)
- [Telegram Bot Setup](README.md)

## Developer Guide

- [Developer Guide](DEVELOPER_GUIDE.md)
- [System Architecture](ARCHITECTURE.md)
- [High-Performance Data System](HIGH_PERFORMANCE_DATA.md)
- [Scalable Architecture](SCALABLE_ARCHITECTURE.md)

## Technical Reference

- [Scan Workflows](SCAN_WORKFLOWS.md)
- [API Reference](API_REFERENCE.md)
- [Testing Guide](TESTING.md)

## Advanced Topics

- [Release Process](RELEASE_PROCESS.md)
- [Disclaimer](Disclaimer.txt)

## Appendices

- [Glossary](GLOSSARY.md)
- [Changelog](CHANGELOG.md)
- [FAQ](FAQ.md)
'''
        
        with open(self.src_dir / "SUMMARY.md", "w") as f:
            f.write(summary)
    
    def process_documentation_files(self):
        """Process all documentation files"""
        print("Processing documentation files...")
        
        files_to_process = [
            "README.md",
            "DEVELOPER_GUIDE.md",
            "ARCHITECTURE.md",
            "HIGH_PERFORMANCE_DATA.md",
            "SCALABLE_ARCHITECTURE.md",
            "SCAN_WORKFLOWS.md",
            "API_REFERENCE.md",
            "TESTING.md",
            "RELEASE_PROCESS.md",
            "Disclaimer.txt",
        ]
        
        for filename in files_to_process:
            source_path = self.docs_dir / filename
            if source_path.exists():
                dest_path = self.src_dir / filename
                
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content = self.convert_markdown_links(content)
                
                if filename == "README.md":
                    content = self._add_frontmatter(content, "Introduction", 1)
                elif filename == "DEVELOPER_GUIDE.md":
                    content = self._add_frontmatter(content, "Developer Guide", 2)
                elif filename == "ARCHITECTURE.md":
                    content = self._add_frontmatter(content, "System Architecture", 2)
                
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  Processed: {filename}")
        
        self._create_glossary()
        self._create_changelog()
        self._create_faq()
        
        print("All documentation files processed")
    
    def _add_frontmatter(self, content: str, title: str, level: int) -> str:
        """Add frontmatter to markdown files"""
        frontmatter = f'''---
title: {title}
weight: {level}
---

'''
        content = re.sub(r'^# .*\n', '', content)
        return frontmatter + content
    
    def convert_markdown_links(self, content: str) -> str:
        """Convert internal links to mdBook format"""
        content = re.sub(r'\(([^)]+)\.rst\)', r'(\1.md)', content)
        content = re.sub(
            r'\[([^\]]+)\]\(https://github\.com/pkjmesra/PKScreener/blob/main/docs/([^)]+)\)',
            r'[\1](\2)',
            content
        )
        return content
    
    def _create_glossary(self):
        """Create glossary file"""
        glossary_content = '''---
title: Glossary
weight: 90
---

# Glossary

## A

### ATR (Average True Range)
A technical indicator that measures market volatility.

### ADX (Average Directional Index)
A technical indicator used to quantify trend strength.

## B

### Breakout
When a stock price moves above resistance with increased volume.

### Backtesting
Testing a strategy on historical data.

## C

### CCI (Commodity Channel Index)
A momentum-based oscillator for identifying cycles.

### Consolidation
Price trading within a defined range without clear trend.

## D

### Data Persistence
Storage of stock data in local cache.

## E

### EMA (Exponential Moving Average)
Moving average that gives more weight to recent prices.

## F

### Fetcher
Component for retrieving stock data.

## G

### GitHub Actions
Automated workflows for scans and data updates.

## H

### High-Performance Data
Real-time data system using in-memory stores.

## I

### Intraday
Positions opened and closed same trading day.

## L

### LTP (Last Traded Price)
Most recent price a stock was traded.

## M

### MACD
Trend-following momentum indicator.

### Multiprocessing
Parallel processing of multiple stocks.

## N

### NSE (National Stock Exchange)
India's leading stock exchange.

## O

### OHLCV
Open, High, Low, Close, Volume data structure.

## P

### Piped Scanners
Chaining multiple screening criteria.

## R

### RSI (Relative Strength Index)
Momentum oscillator measuring price speed and change.

## S

### SMA (Simple Moving Average)
Average price over a specified period.

### Screening
Filtering stocks based on technical criteria.

## T

### Telegram Bot
Chat interface for scan results and triggers.

### Technical Analysis
Evaluation based on statistical trends.

## V

### VCP (Volatility Contraction Pattern)
Volatility decreasing over time.

### VSA (Volume Spread Analysis)
Analysis of price, volume, and spread relationship.
'''
        
        with open(self.src_dir / "GLOSSARY.md", "w") as f:
            f.write(glossary_content)
        print("  Created: GLOSSARY.md")
    
    def _create_changelog(self):
        """Create changelog file"""
        changelog_content = '''---
title: Changelog
weight: 91
---

# Changelog

## [Unreleased]

### Added
- mdBook documentation format
- Glossary section
- FAQ section

### Changed
- Reorganized documentation structure

## [0.13.0] - 2025-12-25

### Added
- High-performance real-time data documentation
- Scalable architecture documentation
- API reference

## [0.12.0] - 2025-11-15

### Added
- Telegram bot documentation
- Piped scanner workflows
- Backtesting documentation
'''
        
        with open(self.src_dir / "CHANGELOG.md", "w") as f:
            f.write(changelog_content)
        print("  Created: CHANGELOG.md")
    
    def _create_faq(self):
        """Create FAQ file"""
        faq_content = '''---
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
'''
        
        with open(self.src_dir / "FAQ.md", "w") as f:
            f.write(faq_content)
        print("  Created: FAQ.md")
    
    def copy_assets(self):
        """Copy static assets"""
        print("Copying assets...")
        
        screenshots_dir = self.docs_dir.parent / "screenshots"
        if screenshots_dir.exists():
            dest_screenshots = self.assets_dir / "screenshots"
            dest_screenshots.mkdir(exist_ok=True)
            for img in screenshots_dir.glob("*.*"):
                shutil.copy2(img, dest_screenshots / img.name)
            print(f"  Copied screenshots")
        
        custom_css = '''/* Custom CSS for PKScreener Documentation */

pre, .hljs {
    border-radius: 8px;
    margin: 1em 0;
    padding: 1em;
}

table {
    width: 100%;
    margin: 1em 0;
    border-collapse: collapse;
}

th, td {
    padding: 8px 12px;
    border: 1px solid #ddd;
}

th {
    background-color: #f5f5f5;
    font-weight: 600;
}

@media (max-width: 768px) {
    body {
        font-size: 16px;
    }
}
'''
        
        with open(self.src_dir / "custom.css", "w") as f:
            f.write(custom_css)
        print("  Created: custom.css")
    
    def create_github_workflow(self):
        """Create GitHub Actions workflow"""
        workflow_content = '''name: Deploy mdBook Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/book/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup mdBook
        uses: peaceiris/actions-mdbook@v1
        with:
          mdbook-version: '0.4.36'
      
      - name: Build mdBook
        run: |
          cd docs/book
          mdbook build
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'docs/book/book'
      
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
'''
        
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        with open(workflow_dir / "deploy-docs.yml", "w") as f:
            f.write(workflow_content)
        print("GitHub Actions workflow created")
    
    def migrate(self):
        """Run full migration"""
        print("="*60)
        print("Starting PKScreener Documentation Migration to mdBook")
        print("="*60)
        print("")
        
        self.setup_mdbook_structure()
        self.process_documentation_files()
        self.copy_assets()
        self.create_github_workflow()
        
        print("")
        print("="*60)
        print("Migration Complete!")
        print("="*60)
        print("")
        print("Next steps:")
        print("1. Install mdBook: cargo install mdbook")
        print("2. Build the book: cd docs/book && mdbook build")
        print("3. Serve locally: mdbook serve --open")
        print("4. Push to GitHub to trigger automatic deployment")

if __name__ == "__main__":
    migrator = MDBookMigrator()
    migrator.migrate()