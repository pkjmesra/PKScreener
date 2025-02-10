"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""

# import math
# import sys
# import warnings
# import datetime
# import numpy as np
# import os
# warnings.simplefilter("ignore", DeprecationWarning)
# warnings.simplefilter("ignore", FutureWarning)
# import pandas as pd

# from sys import float_info as sflt
# import pkscreener.classes.Utility as Utility
# from pkscreener import Imports
# from pkscreener.classes.Pktalib import pktalib
# from PKDevTools.classes.OutputControls import OutputControls
# from PKDevTools.classes import Archiver
# from PKNSETools.morningstartools import Stock

# if sys.version_info >= (3, 11):
#     import advanced_ta as ata

# # from sklearn.preprocessing import StandardScaler
# if Imports["scipy"]:
#     from scipy.stats import linregress

# from PKDevTools.classes.ColorText import colorText
# from PKDevTools.classes.PKDateUtilities import PKDateUtilities
# from PKDevTools.classes.SuppressOutput import SuppressOutput
# from PKDevTools.classes.MarketHours import MarketHours
# # from PKDevTools.classes.log import measure_time

# # Exception for only downloading stock data and not screening
# class DownloadDataOnly(Exception):
#     pass

# class EligibilityConditionNotMet(Exception):
#     pass

# # Exception for stocks which are not newly listed when screening only for Newly Listed
# class NotNewlyListed(Exception):
#     pass


# # Exception for stocks which are not stage two
# class NotAStageTwoStock(Exception):
#     pass

# # Exception for LTP not being in the range as per config
# class LTPNotInConfiguredRange(Exception):
#     pass

# # Exception for stocks which are low in volume as per configuration of 'minimumVolume'
# class NotEnoughVolumeAsPerConfig(Exception):
#     pass


# # Exception for newly listed stocks with candle nos < daysToLookback
# class StockDataNotAdequate(Exception):
#     pass

# class BaseScreeningStatistics:
