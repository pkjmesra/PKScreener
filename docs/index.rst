Features
--------

A Python-based stock screener for NSE, India.

**pkscreener** is an advanced stock screener to find potential breakout stocks from NSE and tell it's possible breakout values. It also helps to find the stocks which are consolidating and may breakout, or the particular chart patterns that you're looking specifically to make your decisions.
pkscreener is totally customizable and it can screen stocks with the settings that you have provided.

Usage
-----

Installation
------------
Requirements: Python 3.9+.

# Using docker, running within docker container
* Download and install docker desktop: https://docs.docker.com/get-docker/
* After installation, launch/run docker desktop and if it asks, login using your docker credentials.
* Launch any command line and type `docker pull pkjmesra/pkscreener-debian:latest`. Then type `docker run pkjmesra/pkscreener-debian:latest python3 pkscreener -a Y -o X:12:10 -e` ow whatever -o options you'd like executed.
* Pass whatever option you'd like to pass in `-o`. Look at the menu options above. For, example, `12` is `Scanners.`. `10` `Closing at least 2% up since last 3 days` etc. Wait while it runs and produces the output for you.

# Building from source repo
* Download the suitable file according to your OS.
* Linux & Mac users should make sure that the `pkscreener.bin or pkscreener.run` is having `execute` permission.
* **Run** the file. Following window will appear after a brief delay.

.. code:: sh
   cd PKScreener-main
   python3 pkscreener.py
