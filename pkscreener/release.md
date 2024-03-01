[![MADE-IN-INDIA](https://img.shields.io/badge/MADE%20WITH%20%E2%9D%A4%20IN-INDIA-orange?style=for-the-badge)](https://en.wikipedia.org/wiki/India) [![GitHub release (latest by date)](https://img.shields.io/github/v/release/pkjmesra/PKScreener?style=for-the-badge)](#) [![GitHub all releases](https://img.shields.io/github/downloads/pkjmesra/PKScreener/total?color=Green&label=Downloads&style=for-the-badge)](#) [![MADE_WITH](https://img.shields.io/badge/BUILT%20USING-PYTHON-yellow?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)

## What's New?
1. [v0.44.20240229.209] release
* Support for TTM Squeeze for bollinger bands and Keltner's channel. Try X>12>7>6>
* Support for Golden/Dead crossovers under MA confluence (Try X>12>7>3)
* Support for portfolio calculations as part of backtests (by default disabled, but can be enabled in configuration)
* Strategies menu is now enabled with various strategies that you can try out on your own alongside the scan types.
* Summary of scan filters/strategies included along-side the main scan results.
* Added the Mutual funds and institutional investor ownership trend based on the previous month's closing in the Trends column (See the MFI:<Trend>). This is updated once every week, over the weekend or daily after market-hours. You must already have been seeing stocks based on fund house popularity (X > 12 > 21> options).
* Added the fair value for all stocks. This is updated once every week, over the weekend or daily after market-hours.
* Added the Buy/Sell opportunities screening option based on fair value. Try X > 12 > 21 > 8 or 9
* Added a default 22-pd (1 month) return for all stocks as part of default reports
* Alongside 30 candle trends, and MFI trends, now the moving averages based uptrend/downtrend is also shown with T:<Trend> in the same column.
* Added option to scan using Lorenzian classifier. Try out X > 12 > 6 > 7.
* Backtest reports can now run super fast. The reports are now concise and more friendly and easier to follow. The backtest report for relevant stocks in the scan result are also now part of user report when requested using bot @nse_pkscreener_bot.
* Many other minor changes for speed and agility. Most scans now finish within 10 seconds when run locally. On GitHub servers, most scans now finish within 1-2 minutes.

## Older Releases
* https://github.com/pkjmesra/PKScreener/releases

## Downloads
| Operating System                                                                                         | Executable File                                                                                                                                                                                                               |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white) | **[pkscreenercli.exe](https://github.com/pkjmesra/PKScreener/releases/download/0.44.20240229.209/pkscreenercli.exe)**                                                                                                         |
| ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)       | **[pkscreenercli.bin](https://github.com/pkjmesra/PKScreener/releases/download/0.44.20240229.209/pkscreenercli.bin)**                                                                                                         |
| ![Mac OS](https://img.shields.io/badge/mac%20os-D3D3D3?style=for-the-badge&logo=apple&logoColor=000000)  | **[pkscreenercli.run](https://github.com/pkjmesra/PKScreener/releases/download/0.44.20240229.209/pkscreenercli.run)** ([Read Installation Guide](https://github.com/pkjmesra/PKScreener/blob/main/INSTALLATION.md#for-macos)) |

## How to use?

[**Click Here**](https://github.com/pkjmesra/PKScreener) to read the documentation. You can also read it at https://pkscreener.readthedocs.io/en/latest/?badge=latest

## Join our Community Discussion

[**Click Here**](https://github.com/pkjmesra/PKScreener/discussions) to join the community discussion and see what other users are doing!

## Facing an Issue? Found a Bug?

[**Click Here**](https://github.com/pkjmesra/PKScreener/issues/new/choose) to open an Issue so we can fix it for you!

## Want to Contribute?

[**Click Here**](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) before you start working with us on new features!

## Disclaimer:
* DO NOT use the result provided by the software solely to make your trading decisions.
* Always backtest and analyze the stocks manually before you trade.
* The Author(s) and the software will not be held liable for any losses.

## License
* MIT: https://github.com/pkjmesra/PKScreener/blob/main/LICENSE
