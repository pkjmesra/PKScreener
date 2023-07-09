
---

## What is PKScreener?

### A Python-based stock screener for NSE, India.

**pkscreener** is an advanced stock screener to find potential breakout stocks from NSE and tell it's possible breakout values. It also helps to find the stocks which are consolidating and may breakout, or the particular chart patterns that you're looking specifically to make your decisions.
pkscreener is totally customizable and it can screen stocks with the settings that you have provided.

You can get daily scan results/alerts at scheduled times by subscribing to the following Telegram channel:
https://t.me/PKScreener
![Telegram Channel](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/Telegram_Channel_Prod.jpg)

For any discussion related to PKScreener, you may like to join the following related Telegram group:
https://t.me/PKScreeners
![Telegram Group](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/Telegram_Channel_Prod.jpg)

## Receiving Scheduled Scan results
If you would like to receive the scan results, please join the telegram channel and group above. 
You may receive the following scan results:
1. Next day Nifty/Market AI prediction by 4pm IST, Monday - Friday
2. For all Nifty stocks at/by 9:45am and 4pm IST, Monday - Friday
    2.1 Scan result containing all relevant technical indicators 
    2.2 Scan result with probable breakouts
    2.3 Scan result with recent breakouts and volumes
    2.4 Scan result with volume gainers/shockers
    2.5 Scan result with stocks gaining at least 2% since last 3 sessions
    2.6 Scan result with short term bullish stocks
    2.7 Scan result with CCI outside the -100,+150 range
    2.8 Scan result with buy signals(Bullish reversals)
    2.9 Scan result with sell signals(bearish reversals)
    2.10 Scan result with momentum gainers (Rising bullish momentum)
    2.11 Scan result for NR4 daily

## How to use on your own local Windows/Linux/Macbook laptop?
* Download the suitable file according to your OS.
* Linux & Mac users should make sure that the `pkscreener.bin or pkscreener.run` is having `execute` permission.
* **Run** the file. Following window will appear after a brief delay.

![home](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/pkscreener_demo.gif)

* **Configure** the parameters as per your requirement using `Option > E`.

![config](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/config.png)

* Following are the screenshots of screening and output results.

![screening](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/screening.png)
![results](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/results.png)
![done](https://raw.githubusercontent.com/pkjmesra/PKScreener/new-features/screenshots/done.png)

* Once done, you can also save the results in an excel file.

## Understanding the Result Table:

The Result table contains a lot of different parameters which can be pretty overwhelming to the new users, so here's the description and significance of each parameter.

| Sr | Parameter | Description | Example |
|:---:|:---:|:---|:---|
|1|**Stock**|This is a NSE scrip symbol. If your OS/Terminal supports unicode, You can directly open **[TradingView](https://in.tradingview.com/)** charts by pressing `Ctrl+Click` on the stock name.|[TATAMOTORS](https://in.tradingview.com/chart?symbol=NSE%3ATATAMOTORS)|
|2|**Consolidating**|It gives the price range in which stock is trading since last `N` days. `N` is configurable and can be modified by executing `Edit User Configuration` option.|If stock is trading between price 100-120 in last 30 days, Output will be `Range = 20.0 %`|
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
Try to tweak this parameters as per your trading styles. For example, If you're comfortable with weekly charts, make `duration=5d` and so on. For intraday, you can set `period=1d and duration=5m` if you would like to calculate with 5minute candles. Set the duration to `15m` or whatever value you desire, but keep the period to `1d`. This tool, however, works best for short/mid term instead of intraday, but some scans like momentum/volume/NR4 etc can be used for screening stocks for intraday as well.

## Contributing:
* Please feel free to Suggest improvements bugs by creating an issue.
* Please follow the [Guidelines for Contributing](https://github.com/pkjmesra/PKScreener/blob/new-features/CONTRIBUTING.md) while making a Pull Request.

## Disclaimer:
* DO NOT use the result provided by the software 'solely' to make your trading decisions.
* Always backtest and analyze the stocks manually before you trade.
* The Author and the software will not be held liable for your losses.
* A lot of this work is based on the original work of https://github.com/pranjal-joshi/Screeni-py. A big thank you!
