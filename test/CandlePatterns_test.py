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
import warnings
from unittest.mock import patch

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import pytest

from pkscreener.classes import Pktalib
from pkscreener.classes.CandlePatterns import CandlePatterns


@pytest.fixture
def candle_patterns():
    return CandlePatterns()

def prepData():
    ohlc = {
        "Open": [1, 2, 3, 4],
        "High": [5, 6, 7, 8],
        "Low": [9, 10, 11, 12],
        "Close": [13, 14, 15, 16]}
    df = pd.DataFrame(ohlc, columns=ohlc.keys())
    return df

def prepPatch(keyCandle):
    cdls = ["CDLDOJI","CDLMORNINGSTAR","CDLMORNINGDOJISTAR","CDLEVENINGSTAR","CDLEVENINGDOJISTAR","CDLLADDERBOTTOM","CDL3LINESTRIKE","CDL3BLACKCROWS","CDL3INSIDE","CDL3OUTSIDE","CDL3WHITESOLDIERS","CDLHARAMI","CDLHARAMICROSS","CDLMARUBOZU","CDLHANGINGMAN","CDLHAMMER","CDLINVERTEDHAMMER","CDLSHOOTINGSTAR","CDLDRAGONFLYDOJI","CDLGRAVESTONEDOJI","CDLENGULFING"]
    cdl_obj = None
    for cdl in cdls:
        if cdl != keyCandle:
            patch.object(Pktalib.pktalib, cdl, autospec=getattr(Pktalib.pktalib, cdl))
        else:
            cdl_obj = patch.object(Pktalib.pktalib, keyCandle, autospec=getattr(Pktalib.pktalib, keyCandle))
    return cdl_obj

def test_findPattern_positive(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    assert candle_patterns.findPattern(df, dict, saveDict) is False
    assert dict["Pattern"] == ""
    assert saveDict["Pattern"] == ""

def test_findPattern_doji(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLDOJI") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
        assert dict["Pattern"] == "\033[1mDoji\033[0m"
        assert saveDict["Pattern"] == "Doji"

def test_findPattern_morning_star(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLMORNINGSTAR") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mMorning Star\033[0m"
    assert saveDict["Pattern"] == "Morning Star"

def test_findPattern_morning_dojistar(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLMORNINGDOJISTAR") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mMorning Doji Star\033[0m"
    assert saveDict["Pattern"] == "Morning Doji Star"

def test_findPattern_evening_star(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLEVENINGSTAR") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mEvening Star\033[0m"
    assert saveDict["Pattern"] == "Evening Star"

def test_findPattern_ladder_bottom_bullish(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLLADDERBOTTOM") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mLadder Bottom\033[0m"
    assert saveDict["Pattern"] == "Bullish Ladder Bottom"

def test_findPattern_ladder_bottom_bearish(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLLADDERBOTTOM") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mLadder Bottom\033[0m"
    assert saveDict["Pattern"] == "Bearish Ladder Bottom"

def test_findPattern_3_line_strike_bullish(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3LINESTRIKE") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92m3 Line Strike\033[0m"
    assert saveDict["Pattern"] == "3 Line Strike"

def test_findPattern_3_line_strike_bearish(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3LINESTRIKE") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91m3 Line Strike\033[0m"
    assert saveDict["Pattern"] == "3 Line Strike"

def test_findPattern_3_black_crows(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3BLACKCROWS") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91m3 Black Crows\033[0m"
    assert saveDict["Pattern"] == "3 Black Crows"

def test_findPattern_3_inside_up(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3INSIDE") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92m3 Outside Up\033[0m"
    assert saveDict["Pattern"] == "3 Inside Up"

def test_findPattern_3_inside_down(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3INSIDE") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91m3 Outside Down\033[0m"
    assert saveDict["Pattern"] == "3 Inside Down"

def test_findPattern_3_outside_up(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3OUTSIDE") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92m3 Outside Up\033[0m"
    assert saveDict["Pattern"] == "3 Outside Up"

def test_findPattern_3_outside_down(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3OUTSIDE") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91m3 Outside Down\033[0m"
    assert saveDict["Pattern"] == "3 Outside Down"

def test_findPattern_3_white_soldiers(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDL3WHITESOLDIERS") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92m3 White Soldiers\033[0m"
    assert saveDict["Pattern"] == "3 White Soldiers"

def test_findPattern_bullish_harami(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHARAMI") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mBullish Harami\033[0m"
    assert saveDict["Pattern"] == "Bullish Harami"

def test_findPattern_bearish_harami(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHARAMI") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mBearish Harami\033[0m"
    assert saveDict["Pattern"] == "Bearish Harami"

def test_findPattern_bullish_harami_cross(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHARAMICROSS") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mBullish Harami Cross\033[0m"
    assert saveDict["Pattern"] == "Bullish Harami Cross"

def test_findPattern_bearish_harami_cross(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHARAMICROSS") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mBearish Harami Cross\033[0m"
    assert saveDict["Pattern"] == "Bearish Harami Cross"

def test_findPattern_bullish_marubozu(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLMARUBOZU") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mBullish Marubozu\033[0m"
    assert saveDict["Pattern"] == "Bullish Marubozu"

def test_findPattern_bearish_marubozu(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLMARUBOZU") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mBearish Marubozu\033[0m"
    assert saveDict["Pattern"] == "Bearish Marubozu"

def test_findPattern_hanging_man(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHANGINGMAN") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mHanging Man\033[0m"
    assert saveDict["Pattern"] == "Hanging Man"

def test_findPattern_hammer(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLHAMMER") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mHammer\033[0m"
    assert saveDict["Pattern"] == "Hammer"

def test_findPattern_inverted_hammer(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLINVERTEDHAMMER") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mInverted Hammer\033[0m"
    assert saveDict["Pattern"] == "Inverted Hammer"

def test_findPattern_shooting_star(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLSHOOTINGSTAR") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mShooting Star\033[0m"
    assert saveDict["Pattern"] == "Shooting Star"

def test_findPattern_dragonfly_doji(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLDRAGONFLYDOJI") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[92mDragonfly Doji\033[0m"
    assert saveDict["Pattern"] == "Dragonfly Doji"

def test_findPattern_gravestone_doji(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLGRAVESTONEDOJI") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mGravestone Doji\033[0m"
    assert saveDict["Pattern"] == "Gravestone Doji"

def test_findPattern_bullish_engulfing(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLENGULFING") as cdl_obj:
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] =="\033[1m\033[92mBullish Engulfing\033[0m"
    assert saveDict["Pattern"] == "Bullish Engulfing"

def test_findPattern_bearish_engulfing(candle_patterns):
    dict = {}
    saveDict = {}
    df = prepData()
    with prepPatch("CDLENGULFING") as cdl_obj:
        df["Close"][3] = -1
        cdl_obj.return_value = df.tail(1).squeeze()
        assert candle_patterns.findPattern(df, dict, saveDict) is True
    assert dict["Pattern"] == "\033[1m\033[91mBearish Engulfing\033[0m"
    assert saveDict["Pattern"] == "Bearish Engulfing"