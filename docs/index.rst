What is PKScreener
------------------
 .. image:: https://static.pepy.tech/personalized-badge/pkscreener?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=PyPi%20Downloads
         :width: 15%
         :alt: PyPi Downloads

A Python-based stock screener for NSE, India.

`pkscreener` is an advanced stock screener to find potential breakout stocks from NSE and tell it's possible breakout values. It also helps to find the stocks which are consolidating and may breakout, or the particular chart patterns that you're looking specifically to make your decisions.
pkscreener is totally customizable and it can screen stocks with the settings that you have provided.

Alerts on Telegram Channel
--------------------------
You can get daily scan results/alerts at scheduled times by subscribing to the following Telegram channel:

.. list-table:: Telegram Channel and Discussion groups
   :widths: 25 50 25
   :header-rows: 1

   * - QR Code
     - Purpose
     - Description/link
   * - .. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/Telegram_Channel_Prod.jpg
         :width: 100%
         :alt: Telegram Channel
     - Alerts Channel
     - https://t.me/PKScreener > You wil receive all the major alerts on this 
       telegram channel. These alerts are sent for all major strategy scans daily 
       around 9:30am-10:15am and then around 4pm. You will also receive the next 
       day's market predictions.
     
   * - .. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/PKScreeners_Group.jpg
         :width: 100%
         :alt: Telegram Group
     - Discussions
     - https://t.me/PKScreeners > For any discussion related to PKScreener, you may 
       like to join this related Telegram group

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/telegram.png
         :width: 100%
         :alt: Telegram Channel

Receiving On-Demand Scan results
--------------------------------

You can now run the ``pkscreenerbot`` on your local machine or if it's running on the GitHub server under a GitHub Actions workflow, you can use the ``pkscreener Bot``(@nse_pkscreener_bot on Telegram) to get on-demand scan results.

 .. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/bot.gif
         :width: 50%
         :alt: Telegram bot

Installation
------------
Requirements: Python 3.9+.

How to use on your own local Windows/Linux/Macbook laptop?
----------------------------------------------------------
Installing the latest version from PyPi.
----------------------------------------
* Go ahead and install using ``pip install pkscreener``
* This should install all of the major dependencies, except maybe, TA-Lib. 
* This app can still run without TA-Lib, but if you need to install TA-Lib for technical indicators (which otherwise is used from ``pandas_ta`` in the absence of TA-Lib), you can do this: Head to ``.github/dependencies/`` under this repo. Download the respective TA-Lib file/whl file and install either from the .whl file or from source. Check out any of the workflow files for steps to install TA-Lib.
* Now launch your favorite command line CLI and issue ``pkscreener``. This will launch the pkscreener executable.

Using docker, running within docker container
----------------------------------------------
* Download and install docker desktop: https://docs.docker.com/get-docker/
* After installation, launch/run docker desktop and if it asks, login using your docker credentials.
* Launch any command line and type ``docker pull pkjmesra/pkscreener-debian:latest``. Then type ``docker run pkjmesra/pkscreener-debian:latest python3 pkscreener -a Y -o X:12:10 -e`` ow whatever -o options you'd like executed.
* Pass whatever option you'd like to pass in ``-o``. Look at the menu options above. For, example, ``12`` is ``Scanners.``. ``10`` ``Closing at least 2% up since last 3 days`` etc. Wait while it runs and produces the output for you.

Building from source repo
-------------------------
* Install python 3.9 for your OS/CPU. Download the installer from https://www.python.org/downloads/release/python-3913/#Files
* Just clone the repo with ``git clone https://github.com/pkjmesra/PKScreener.git``
* ``cd PKScreener``
* ``pip install -r requirements.txt`` .
* (Optional) If you would like to have technical indicators evaluated using TA-Lib, go ahead and install TA-Lib as well. ``pip3 install ta-lib``
* ``cd pkscreener``
* Finally, from within the ``pkscreener`` directory, run ``python pkscreenercli.py``. You are all set.


Usage
-----
Running the executables
-----------------------
* Download the suitable file according to your OS.
* Linux & Mac users should make sure that the ``pkscreener.bin or pkscreener.run`` is having ``execute`` permission.
* :guilabel:`Run` the file.

Configuration
-------------
* :guilabel:`Configure` the parameters as per your requirement using ``Option > E``.

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/config.png
         :width: 100%
         :alt: Configuration

Scanners
--------
* :guilabel:`Scanner Menus` the scanner menus for each level/sub-level

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu.png
         :width: 100%
         :alt: MenuLevel1

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu_level2.png
         :width: 100%
         :alt: MenuLevel2

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/menu_level3.png
         :width: 100%
         :alt: MenuLevel3


* Following are the screenshots of screening and output results.

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/screening.png
         :width: 100%
         :alt: Screening

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/results.png
         :width: 100%
         :alt: Screening results

* Once done, you can also save the results in an excel file.

Backtests
---------
You can now use the *Backtests* menu to backtest any of the selected strategies.

.. image:: https://raw.githubusercontent.com/pkjmesra/PKScreener/main/screenshots/backtest.png
         :width: 100%
         :alt: Backtests

* Once done, you can also view the output html file saved at the same location from where you launched the app.

Scanning as a scheduled job once or at regular intervals
--------------------------------------------------------
Running it once with pre-defined inputs
---------------------------------------

You can also run it as a one time job in any scheduler with pre-defined options. For example ``./pkscreenercli.py -a Y -o X:12:10 -e`` (or ``pkscreener.exe -a Y -o X:12:10 -e`` if you're executing with the exe) will run the scanner for all Nifty stocks and find all stocks matching CCI filter, save the results in xlsx file and exit. ``./pkscreenercli.py -a Y -o X:12:9:2.5 -e`` will run the scanner (menu option ``X``) for all Nifty stocks (menu option ``12``) to find volume gainers (menu option ``9``) with at least the volume multiplier of 2.5 (input variable ``2.5``), save the results in xlsx file and exit (menu option ``-e``). Passing in the ``-p`` option for example ``pkscreenercli.py -a Y -p -o X:12:6:1 -e`` will also silence all command line prints/outputs and just run silently for the given options, save results and exit. Try and see all options with ``./pkscreenercli.py -h``.

Running it at regular intervals
-------------------------------

If you want to runn it at regular intervals, you can just pass the interval in ``-c`` command line option. For example, ``./pkscreenercli.py -a Y -o X:12:6:1 -c 180`` will run it every ``180`` seconds with console outputs also being printed. If you'd just like it to run as a cron job without console outputs, you may also pass the ``-p`` parameter. For example, ``./pkscreenercli.py -a Y -p -o X:12:6:1 -c 180``

Understanding the Result Table
------------------------------
The Result table contains a lot of different parameters which can be pretty overwhelming to the new users, so here's the description and significance of each parameter.

.. list-table:: Telegram Channel and Discussion groups
   :widths: 5 15 65 15
   :header-rows: 1

   * - Sr
     - Parameter
     - Description
     - Example
   * - 1
     - :guilabel:`Stock`
     - This is a NSE scrip symbol. If your OS/Terminal supports unicode, 
       You can directly open :guilabel:`[TradingView](https://in.tradingview.com/)` 
       charts by pressing ``Ctrl+Click`` on the stock name.
     - [TATAMOTORS](https://in.tradingview.com/chart?symbol=NSE%3ATATAMOTORS)
   * - 2
     - :guilabel:`Consolidating`
     - It gives the price range in which stock is trading since last ``N`` days.
       ``N`` is configurable and can be modified by executing ``Edit User Configuration`` 
       option.
     - If stock is trading between price 100-120 in last 30 days, Output will be ``Range:20.0 %``
   * - 3
     - :guilabel:`Breakout (N Days)`
     - This is pure magic! The ``BO`` is Breakout level in last N days while ``R`` 
       is the next resistance level if available. Investor should consider both BO & R 
       level to decide entry/exits in their trades.
     - ``BO:302, R:313`` (Breakout level is 302 & Next resistance is 313)
   * - 4
     - :guilabel:`LTP`
     - LTP is the Last Traded Price of an asset traded on NSE.
     - ``298.7`` (Stock is trading at this price)
   * - 5
     - :guilabel:`Volume`
     - Volume shows the relative volume of the recent candle with respect to 20 period 
       MA of Volume. It could be ``Unknown`` for newly listed stocks.
     - if 20MA(Volume) is 1M and todays Volume is 2.8M, then ``Volume = 2.8x``
   * - 6
     - :guilabel:`MA-Signal`
     - It describes the price trend of an asset by analysing various 50-200 MA/EMA 
       crossover strategies.
     - ``200MA-Support``,``BullCross-50MA`` etc
   * - 7
     - :guilabel:`RSI`
     - For the momentum traders, it describes 14-period RSI for quick decision 
       making about their trading plans
     - ``0 to 100``
   * - 8
     - :guilabel:`Trend`
     - By using advance algorithms, the average trendlines are computed for ``N`` days 
       and their strenght is displayed depending on steepness of trendlines. (This does 
       NOT show any trendline on chart, it is calculated internally)
     - ``Strong Up``, ``Weak Down`` etc.
   * - 9
     - :guilabel:`Pattern`
     - If the chart or the candle itself forming any important pattern in the recent 
       timeframe or as per the selected screening option, various important patterns 
       will be indicated here.
     - ``Momentum Gainer``, ``Inside Bar (N)``,``Bullish Engulfing`` etc.

Hack it your way
----------------
Feel free to Edit the parameters in the ``pkscreener.ini`` file which will be generated by the application.

.. code-block::
   :caption: pkscreener.ini

    [config]
    period = 400d
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
    logsEnabled = n


Try to tweak this parameters as per your trading styles. For example, If you're comfortable with weekly charts, make ``duration=5d`` and so on. For intraday, you can set ``period=1d and duration=5m`` if you would like to calculate with 5minute candles. Set the duration to ``15m`` or whatever value you desire, but keep the period to ``1d``. This tool, however, works best for short/mid term instead of intraday, but some scans like momentum/volume/NR4 etc can be used for screening stocks for intraday as well. You can use the toggle menu option ``T`` to toggle between long term and intraday config before you begin the scanners.

Creating your own Telegram channel to receive your own alerts
-------------------------------------------------------------

You can create your own telegram channel to receive alerts wherenevr you run it locally on your laptop either from a command line interface console or run it as a scheduler. Simply, go ahead and 

1. Create a bot for yourself, then a channel and get their IDs. Follow the steps in https://medium.com/codex/using-python-to-send-telegram-messages-in-3-simple-steps-419a8b5e5e2 and https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token
2. After you have created the bot using ``botFather`` and have received/verified your bot id/token and channel ID using ``get id bot``, simply go to ``pkscreener`` folder in the source code directory and create a ``.env.dev`` file with the following (If you are instead using the .exe or .bin or .run file from release, just create this file in the same folder where the executable (.exe or .bin or .run) is placed.)

.. code-block::
   :caption: .env.dev

    CHAT_ID=Your_Channel_Id_Here_Without_A_Hyphen_or_Minus_Sign
    TOKEN=Your_Bot_Token_Here
    chat_idADMIN=Your_Own_ID_Here

3. From now on, you will begin to receive your own alerts on your telegram channel.

Troubleshooting and Logs
------------------------

If you are having issues running the program, you can just launch a command line interface (On windows> Start > Run > cmd) and then launch PKScreener with a command line option of ``-l``. For example, ``python pkscreenercli.py -l``. This will show you the path where the program will save all the log outputs from this run. Copy that path and go ahead and run the application. Altenatively, you can just go ahead and modify the ``logsEnabled`` value to ``y``, save & close it and then run ``python pkscreenercli.py``.

After you have finished the run, go to that copied path, zip the contents of the file ``pkscreener-logs.txt`` and create an issue at https://github.com/pkjmesra/PKScreener/issues. Please do not forget to attach the log files in the issue.
