[![MADE-IN-INDIA](https://img.shields.io/badge/MADE%20WITH%20%E2%9D%A4%20IN-INDIA-orange?style=for-the-badge)](https://en.wikipedia.org/wiki/India) [![GitHub release (latest by date)](https://img.shields.io/github/v/release/pkjmesra/PKScreener?style=for-the-badge)](#) [![GitHub all releases](https://img.shields.io/github/downloads/pkjmesra/PKScreener/total?color=Green&label=Downloads&style=for-the-badge)](#) [![MADE_WITH](https://img.shields.io/badge/BUILT%20USING-PYTHON-yellow?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)

## What's New?
1. [v0.43.20240107.75] release
* Growth of 10k scan option added. Try it out with G >. Enabled also in bot @nse_pkscreener_bot .
* Summary of scan filters/strategies included along-side the main scan results.
* Added option to scan using Lorenzian classifier. Try out X > 12 > 6 > 7. It was already there but was not available for Python 3.9. Upgraded the project to use Python 3.11.
* Included 52 week high/low in all scan results for better comparison and understanding.
* A lot of changes to keep the backtest reports running faster. The reports are now concise and more friendly and easier to follow. The backtest report for relevant stocks in the scan result are also now part of user report when requested using bot @@nse_pkscreener_bot.
* Added the option to scan all such stocks showing higher highs, higher lows and higher close trend. Try X > 12 > 24.
* Added the option to view the currently breaking out stocks. Try option X > 12 > 23.
* Added the stocks based on fund house popularity. Try the X > 12 > 21> options.
* Added the option to scan all such stocks showing lower highs, lower lows but still in bullish RSI zone. Try X > 12 > 25.
* You can now see which stocks the mutual funds are investing into and where they are selling out. Try the X > 12 > 21> options.
* Many other minor changes for speed and agility. Most scans now finish within 10 seconds when run locally. On GitHub servers, most scans now finish within 2 minutes.

## Older Releases
* https://github.com/pkjmesra/PKScreener/releases

## Downloads
| Operating System                                                                                         | Executable File                                                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white) | **[pkscreenercli.exe](https://github.com/pkjmesra/PKScreener/releases/download/0.43.20240107.75/pkscreenercli.exe)**                                                                                                         |
| ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)       | **[pkscreenercli.bin](https://github.com/pkjmesra/PKScreener/releases/download/0.43.20240107.75/pkscreenercli.bin)**                                                                                                         |
| ![Mac OS](https://img.shields.io/badge/mac%20os-D3D3D3?style=for-the-badge&logo=apple&logoColor=000000)  | **[pkscreenercli.run](https://github.com/pkjmesra/PKScreener/releases/download/0.43.20240107.75/pkscreenercli.run)** ([Read Installation Guide](https://github.com/pkjmesra/PKScreener/blob/main/INSTALLATION.md#for-macos)) |

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
