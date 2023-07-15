
# PKScreener

![main workflow](https://img.shields.io/github/actions/workflow/status/pkjmesra/pkscreener/workflow-prod-scans_2.1.yml?logo=github)
![github license](https://img.shields.io/pypi/l/gspread?logo=github)
![latest download](https://img.shields.io/github/downloads-pre/pkjmesra/pkscreener/latest/total?logo=github)
![documentation](https://img.shields.io/readthedocs/pkscreener?logo=readthedocs)
| [![GitHub release (latest by date)](https://img.shields.io/github/v/release/pkjmesra/PKScreener?style=for-the-badge)](https://github.com/pkjmesra/PKScreener/releases/latest) [![GitHub all releases](https://img.shields.io/github/downloads/pkjmesra/PKScreener/total?color=Green&label=Downloads&style=for-the-badge)](#) [![GitHub](https://img.shields.io/github/license/pkjmesra/PKScreener?style=for-the-badge)](https://github.com/pkjmesra/PKScreener/blob/main/LICENSE) [![CodeFactor](https://www.codefactor.io/repository/github/pkjmesra/PKScreener/badge?style=for-the-badge)](https://www.codefactor.io/repository/github/pkjmesra/PKScreener) [![MADE-IN-INDIA](https://img.shields.io/badge/MADE%20WITH%20%E2%9D%A4%20IN-INDIA-orange?style=for-the-badge)](https://en.wikipedia.org/wiki/India) [![BADGE](https://img.shields.io/badge/PULL%20REQUEST-GUIDELINES-red?style=for-the-badge)](https://github.com/pkjmesra/PKScreener/blob/new-features/CONTRIBUTING.md) |
| [![Screenipy Test - New Features](https://github.com/pkjmesra/PKScreener/actions/workflows/workflow-test.yml/badge.svg?branch=new-features)](https://github.com/pkjmesra/PKScreener/actions/workflows/workflow-test.yml) [![Screenipy Build - New Release](https://github.com/pkjmesra/PKScreener/actions/workflows/workflow-build-matrix.yml/badge.svg)](https://github.com/pkjmesra/PKScreener/actions/workflows/workflow-build-matrix.yml) |
| [![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/pkjmesra/PKScreener/releases/download/0.01/pkscreener.exe) [![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://github.com/pkjmesra/PKScreener/releases/download/0.01/pkscreener.bin) [![Mac OS](https://img.shields.io/badge/mac%20os-D3D3D3?style=for-the-badge&logo=apple&logoColor=000000)](https://github.com/pkjmesra/PKScreener/releases/download/0.01/pkscreener.run) |


## What is PKScreener?

### A Python-based stock screener for NSE, India.

**pkscreener** is an advanced stock screener to find potential breakout stocks from NSE and tell it's possible breakout values. It also helps to find the stocks which are consolidating and may breakout, or the particular chart patterns that you're looking specifically to make your decisions.
pkscreener is totally customizable and it can screen stocks with the settings that you have provided.

You can get daily scan results/alerts at scheduled times by subscribing to the following Telegram channel:

https://t.me/PKScreener (or scan the QR code to join)

<img src="https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/Telegram_Channel_Prod.jpg" alt="Telegram Channel" width="100"/>

For any discussion related to PKScreener, you may like to join the following related Telegram group:

https://t.me/PKScreeners (or scan the QR code to join)

<img src="https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/PKScreeners_Group.jpg" alt="Telegram Group" width="100"/>

![telegram](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/telegram.png)

## Receiving Scheduled Scan results
If you would like to receive the scan results, please join the telegram channel and group above. 
You may receive the following scan results:
1. Next day Nifty/Market AI prediction by 4pm IST, Monday - Friday
2. For all Nifty stocks at/by 9:45-10:15am and 4pm IST, Monday - Friday

    * 2.1 Scan result containing all relevant technical indicators 
    * 2.2 Scan result with probable breakouts
    * 2.3 Scan result with recent breakouts and volumes
    * 2.4 Scan result with volume gainers/shockers
    * 2.5 Scan result with stocks gaining at least 2% since last 3 sessions
    * 2.6 Scan result with short term bullish stocks
    * 2.7 Scan result with CCI outside the -100,+150 range
    * 2.8 Scan result with buy signals(Bullish reversals)
    * 2.9 Scan result with sell signals(bearish reversals)
    * 2.10 Scan result with momentum gainers (Rising bullish momentum)
    * 2.11 Scan result for NR4 daily

## Scanners

Screening options to choose from:
* Artificial Intelligence v2 for Nifty 50 Prediction
* Live Index Scan : 5 EMA for Intraday
* Screen stocks by the stock names (NSE Stock Code)
* Nifty 50
* Nifty Next 50
* Nifty 100
* Nifty 200
* Nifty 500
* Nifty Smallcap 50
* Nifty Smallcap 100
* Nifty Smallcap 250
* Nifty Midcap 50
* Nifty Midcap 100
* Nifty Midcap 150
* Nifty (All Stocks)
* Newly Listed (IPOs in last 2 Year)
* F&O Stocks Only

Followin scanners are already implemented. Others are `In Progress`
```
     0 > Full Screening (Shows Technical Parameters without any criterion)
     1 > Probable Breakouts                     2 > Recent Breakouts & Volumes
     3 > Consolidating stocks                   4 > Lowest Volume in last 'N'-days (Early Breakout Detection)
     5 > RSI screening                          6 > Reversal Signals
     7 > Stocks making Chart Patterns           8 > CCI outside of the given range
     9 > Volume gainers                         10 > Closing at least 2% up since last 3 days
    11 > Short term bullish stocks              12 > 15 Minute Price & Volume breakout
    13 > Bullish RSI & MACD Intraday            14 > NR4 Daily Today
```
## How to use on your own local Windows/Linux/Macbook laptop?

# Using docker, running within docker container
* Download and install docker desktop: https://docs.docker.com/get-docker/
* After installation, launch/run docker desktop and if it asks, login using your docker credentials.
* Launch any command line and type `docker pull pkjmesra/pkscreener-debian:latest`. Then type `docker run pkjmesra/pkscreener-debian:latest python3 pkscreener -a Y -o X:12:10 -e` ow whatever -o options you'd like executed.
* Pass whatever option you'd like to pass in `-o`. Look at the menu options above. For, example, `12` is `Scanners.`. `10` `Closing at least 2% up since last 3 days` etc. Wait while it runs and produces the output for you.

# Building from source repo
* Download the suitable file according to your OS.
* Linux & Mac users should make sure that the `pkscreener.bin or pkscreener.run` is having `execute` permission.
* **Run** the file. Following window will appear after a brief delay.


* **Configure** the parameters as per your requirement using `Option > E`.

![config](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/config.png)

* **Scanner Menus** the scanner menus for each level/sub-level
![menulevel1](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu.png)
![menulevel2](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu_level2.png)
![menulevel3](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu_level3.png)


* Following are the screenshots of screening and output results.

![screening](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/screening.png)
![results](https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/results.png)

* Once done, you can also save the results in an excel file.

## Scanning as a scheduled job once or at regular intervals
* Running it once with pre-defined inputs
You can also run it as a one time job in any scheduler with pre-defined options. For example `./pkscreener.py -a Y -o X:12:10 -e` (or `pkscreener.exe -a Y -o X:12:10 -e` if you're executing with the exe) will run the scanner for all Nifty stocks and find all stocks matching CCI filter, save the results in xlsx file and exit. `./pkscreener.py -a Y -o X:12:9:2.5 -e` will run the scanner (menu option `X`) for all Nifty stocks (menu option `12`) to find volume gainers (menu option `9`) with at least the volume multiplier of 2.5 (input variable `2.5`), save the results in xlsx file and exit (menu option `-e`). Passing in the `-p` option for example `pkscreener.py -a Y -p -o X:12:6:1 -e` will also silence all command line prints/outputs and just run silently for the given options, save results and exit. Try and see all options with `./pkscreener.py -h`.

* Running it at regular intervals
If you want to runn it at regular intervals, you can just pass the interval in `-c` command line option. For example, `./pkscreener.py -a Y -o X:12:6:1 -c 180` will run it every `180` seconds with console outputs also being printed. If you'd just like it to run as a cron job without console outputs, you may also pass the `-p` parameter. For example, `./pkscreener.py -a Y -p -o X:12:6:1 -c 180`

## Understanding the Result Table:

The Result table contains a lot of different parameters which can be pretty overwhelming to the new users, so here's the description and significance of each parameter.

| Sr | Parameter | Description | Example |
|:---:|:---:|:---|:---|
|1|**Stock**|This is a NSE scrip symbol. If your OS/Terminal supports unicode, You can directly open **[TradingView](https://in.tradingview.com/)** charts by pressing `Ctrl+Click` on the stock name.|[TATAMOTORS](https://in.tradingview.com/chart?symbol=NSE%3ATATAMOTORS)|
|2|**Consolidating**|It gives the price range in which stock is trading since last `N` days. `N` is configurable and can be modified by executing `Edit User Configuration` option.|If stock is trading between price 100-120 in last 30 days, Output will be `Range:20.0 %`|
|3|**Breakout (N Days)**|This is pure magic! The `BO` is Breakout level in last N days while `R` is the next resistance level if available. Investor should consider both BO & R level to decide entry/exits in their trades.|`B:302, R:313`(Breakout level is 100 & Next resistance is 102)|
|4|**LTP**|LTP is the Last Traded Price of an asset traded on NSE.|`298.7` (Stock is trading at this price)|
|5|**Volume**|Volume shows the relative volume of the recent candle with respect to 20 period MA of Volume. It could be `Unknown` for newly listed stocks.|if 20MA(Volume) is 1M and todays Volume is 2.8M, then `Volume = 2.8x`|
|6|**MA-Signal**|It describes the price trend of an asset by analysing various 50-200 MA/EMA crossover strategies.|`200MA-Support`,`BullCross-50MA` etc|
|7|**RSI**|For the momentum traders, it describes 14-period RSI for quick decision making about their trading plans|`0 to 100`|
|8|**Trend**|By using advance algorithms, the average trendlines are computed for `N` days and their strenght is displayed depending on steepness of trendlines. (This does NOT show any trendline on chart, it is calculated internally)|`Strong Up`, `Weak Down` etc.|
|9|**Pattern**|If the chart or the candle itself forming any important pattern in the recent timeframe or as per the selected screening option, various important patterns will be indicated here.|`Momentum Gainer`, `Inside Bar (N)`,`Bullish Engulfing` etc.|

## Hack it your way:
Feel free to Edit the parameters in the `pkscreener.ini` file which will be generated by the application.
```
[config]
period = 300d
daystolookback = 30
duration = 1d
minprice = 30
maxprice = 10000
volumeratio = 2
consolidationpercentage = 10
shuffle = y
cachestockdata = y
onlystagetwostocks = y
useema = n
```
Try to tweak this parameters as per your trading styles. For example, If you're comfortable with weekly charts, make `duration=5d` and so on. For intraday, you can set `period=1d and duration=5m` if you would like to calculate with 5minute candles. Set the duration to `15m` or whatever value you desire, but keep the period to `1d`. This tool, however, works best for short/mid term instead of intraday, but some scans like momentum/volume/NR4 etc can be used for screening stocks for intraday as well. You can use the toggle menu option `T` to toggle between long term and intraday config before you begin the scanners.

## Creating your own Telegram channel to receive your own alerts:
You can create your own telegram channel to receive alerts wherenevr you run it locally on your laptop either from a command line interface console or run it as a scheduler. Simply, go ahead and 
1. Create a bot for yourself, then a channel and get their IDs. Follow the steps in https://medium.com/codex/using-python-to-send-telegram-messages-in-3-simple-steps-419a8b5e5e2 and https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token
2. After you have created the bot using `botFather` and have received/verified your bot id/token and channel ID using `get id bot`, simply go to `src` folder in the source code directory and create a `.env.dev` file with the following (If you are instead using the .exe or .bin or .run file from release, just create this file in the same folder where the executable (.exe or .bin or .run) is placed.)
```
CHAT_ID=Your_Channel_Id_Here_Without_A_Hyphen_or_Minus_Sign
TOKEN=Your_Bot_Token_Here
chat_idADMIN=Your_Own_ID_Here
```
3. From now on, you will begin to receive your own alerts on your telegram channel.

## Contributing:
* Please feel free to Suggest improvements bugs by creating an issue.
* Please follow the [Guidelines for Contributing](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) while making a Pull Request.

## Disclaimer:
* DO NOT use the result provided by the software 'solely' to make your trading decisions.
* Always backtest and analyze the stocks manually before you trade.
* The Author and the software will not be held liable for your losses.
* A lot of this work is based on the original work of https://github.com/pranjal-joshi/Screeni-py. A big thank you!
