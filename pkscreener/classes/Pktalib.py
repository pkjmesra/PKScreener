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
from time import sleep

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls

from pkscreener import Imports

if Imports["talib"]:
    try:
        import talib
    except Exception as e: # pragma: no cover
        issueLink = "https://github.com/pkjmesra/PKScreener"
        issueLink = f"\x1b[97m\x1b]8;;{issueLink}\x1b\\{issueLink}\x1b]8;;\x1b\\\x1b[0m"
        taLink = "https://github.com/ta-lib/ta-lib-python"
        taLink = f"\x1b[97m\x1b]8;;{taLink}\x1b\\{taLink}\x1b]8;;\x1b\\\x1b[0m"
        OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] 'TA-Lib' library is not installed. For best results, please install 'TA-Lib'! You may wish to follow instructions from\n  [+] {issueLink}"
                + colorText.END
            )
        try:
            import pandas_ta as talib
            OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] TA-Lib is not installed. Falling back on pandas_ta.\n  [+] For full coverage(candle patterns), you may wish to follow instructions from\n  [+] {taLink}"
                + colorText.END
            )
        except: # pragma: no cover
            OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] pandas_ta is not installed. Falling back on pandas_ta also failed.\n  [+] For full coverage(candle patterns), you may wish to follow instructions from\n  [+] {taLink}"
                + colorText.END
            )
            pass
        pass
else:
    try:
        import pandas_ta as talib
        OutputControls().printOutput(
            colorText.FAIL
            + "  [+] TA-Lib is not installed. Falling back on pandas_ta.\n  [+] For full coverage(candle patterns), you may wish to follow instructions from\n  [+] https://github.com/ta-lib/ta-lib-python"
            + colorText.END
        )
        sleep(3)
    except Exception:  # pragma: no cover
        # default_logger().debug(e, exc_info=True)
        import talib


class pktalib:
    @classmethod
    def AVWAP(self,df,anchored_date:pd.Timestamp):
        # anchored_date = pd.to_datetime('2022-01-30')
        # Choosing a meaningful anchor point is an essential part of using 
        # Anchored VWAP effectively. Traders may choose to anchor VWAP to 
        # a significant event that is likely to impact the stock’s price 
        # movement, such as an earnings announcement, product launch, or 
        # other news events. By anchoring VWAP to such events, traders 
        # can get a more meaningful reference point that reflects the 
        # sentiment of the market around that time. This can help traders 
        # identify potential areas of support and resistance more accurately 
        # and make better trading decisions.
        with pd.option_context('mode.chained_assignment', None):
            df["VWAP_D"] = pktalib.VWAP(high=df["High"],low=df["Low"],close=df["Close"],volume=df["Volume"],anchor="D")
            # If we create a column 'typical_price', it should be identical with 'VWAP_D'
            df['typical_price'] = (df['High'] + df['Low'] + df['Close'])/3
            tpp_d = ((df['High'] + df['Low'] + df['Close'])*df['Volume'])/3
            df['anchored_VWAP'] = tpp_d.where(df.index >= anchored_date).groupby(
                df.index >= anchored_date).cumsum()/df['Volume'].where(
                    df.index >= anchored_date).groupby(
                        df.index >= anchored_date).cumsum()
        return df['anchored_VWAP']

    @classmethod
    def BBANDS(self, close, timeperiod,std=2, mamode=0):
        try:
            return talib.bbands(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.BBANDS(close, timeperiod, std, std, mamode)
        
    @classmethod
    def EMA(self, close, timeperiod):
        try:
            return talib.ema(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.EMA(close, timeperiod)

    @classmethod
    def VWAP(self, high, low, close, volume,anchor=None):
        try:
            import pandas_ta as talib
            return talib.vwap(high, low, close, volume,anchor=anchor)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return None
        
    @classmethod
    def KeltnersChannel(self, high, low, close, timeperiod=20):
        try:
            low_kel = None
            upp_kel = None
            tr = pktalib.TRUERANGE(high, low, close)
            atr = pktalib.ATR(high, low, close, timeperiod=timeperiod)
            sma = pktalib.SMA(close=close, timeperiod=timeperiod)
            low_kel = sma - atr * 1.5
            upp_kel = sma + atr * 1.5
            return low_kel, upp_kel
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return low_kel, upp_kel
        
    @classmethod
    def SMA(self, close, timeperiod):
        try:
            return talib.sma(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.SMA(close, timeperiod)

    @classmethod
    def WMA(self, close, timeperiod):
        try:
            return talib.wma(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.WMA(close, timeperiod)
        
    @classmethod
    def ATR(self, high, low, close, timeperiod=14):
        try:
            return talib.atr(high, low, close, length= timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.ATR(high, low, close, timeperiod=timeperiod)
        
    @classmethod
    def TRUERANGE(self, high, low, close):
        try:
            return talib.true_range(high, low, close)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.TRANGE(high, low, close)

    @classmethod
    def MA(self, close, timeperiod):
        try:
            return talib.ma(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.MA(close, timeperiod)

    @classmethod
    def TriMA(self, close,length=10):
        try:
            import pandas_ta as talib
            return talib.trima(close=close, length=length)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return None

    @classmethod
    def MACD(self, close, fast, slow, signal):
        try:
            # import pandas_ta as talib
            return talib.macd(close, fast, slow, signal, talib=Imports["talib"])
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.MACD(close, fast, slow, signal)

    @classmethod
    def MFI(self, high, low, close,volume, timeperiod=14):
        try:
            return talib.mfi(high, low, close,volume, length= timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.MFI(high, low, close,volume, timeperiod=timeperiod)

    @classmethod
    def RSI(self, close, timeperiod):
        try:
            return talib.rsi(close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.RSI(close, timeperiod)

    @classmethod
    def CCI(self, high, low, close, timeperiod):
        try:
            return talib.cci(high, low, close, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CCI(high, low, close, timeperiod)

    @classmethod
    def Aroon(self, high, low, timeperiod):
        try:
            return talib.aroon(high, low, timeperiod)
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            aroon_down, aroon_up = talib.AROON(high, low, timeperiod)
            aroon_up.name = f"AROONU_{timeperiod}"
            aroon_down.name = f"AROOND_{timeperiod}"
            data = {
                aroon_down.name: aroon_down,
                aroon_up.name: aroon_up,
            }
            return pd.DataFrame(data)

    @classmethod
    def STOCHF(self, high, low, close, fastk_period, fastd_period, fastd_matype):
        fastk, fastd = talib.STOCHF(high,
                            low,
                            close,
                            fastk_period, 
                            fastd_period,
                            fastd_matype)
        return fastk, fastd
    
    @classmethod
    def STOCHRSI(self, close, timeperiod, fastk_period, fastd_period, fastd_matype):
        try:
            _name = "STOCHRSI"
            _props = f"_{timeperiod}_{timeperiod}_{fastk_period}_{fastd_period}"
            stochrsi_kname = f"{_name}k{_props}"
            stochrsi_dname = f"{_name}d{_props}"
            df = talib.stochrsi(
                close,
                length=timeperiod,
                rsi_length=timeperiod,
                k=fastk_period,
                d=fastd_period,
                mamode=fastd_matype,
            )
            return df[stochrsi_kname], df[stochrsi_dname]
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.STOCHRSI(
                close.values, timeperiod, fastk_period, fastd_period, fastd_matype
            )

    @classmethod
    def highest(self, df,columnName, timeperiod):
        return df.rolling(timeperiod, min_periods=1)[columnName].max()

    @classmethod
    def lowest(self, df,columnName, timeperiod):
        return df.rolling(timeperiod, min_periods=1)[columnName].min()
    
    @classmethod
    def RVM(self, high, low, close, timeperiod):
        # Relative Volatality Measure
        #Short-term ATRs
        short1    = pktalib.ATR(high, low, close,3)
        short2    = pktalib.ATR(high, low, close,5)
        short3    = pktalib.ATR(high, low, close,8)
        shortAvg  = (short1 + short2 + short3) / 3

        #Long-term ATRs
        long1   = pktalib.ATR(high, low, close,55)
        long2   = pktalib.ATR(high, low, close,89)
        long3   = pktalib.ATR(high, low, close,144)
        longAvg = (long1 + long2 + long3) / 3

        #Combined ATR value
        combinedATR = (shortAvg + longAvg) / 2

        #Highest and lowest combined ATR over lookback period
        df_catr = pd.DataFrame(data=combinedATR,columns=["combinedATR"])
        highestCombinedATR = pktalib.highest(df_catr,"combinedATR", timeperiod)
        lowestCombinedATR = pktalib.lowest(df_catr,"combinedATR", timeperiod)

        #RVM Calculation
        diffLowest = (combinedATR - lowestCombinedATR)
        diffLowest = [x for x in diffLowest if ~np.isnan(x)]
        diffHighLow = (highestCombinedATR - lowestCombinedATR)
        diffHighLow = [x for x in diffHighLow if ~np.isnan(x)]
        df_diff_lowest = pd.DataFrame(data=diffLowest,columns=["diffLowest"])
        df_diff_highLow = pd.DataFrame(data=diffHighLow,columns=["diffHighLow"])
        maxHighLow = max(df_diff_highLow["diffHighLow"])
        rvm =  df_diff_lowest["diffLowest"]/ maxHighLow * 100
        return round(rvm.tail(1),1)

    @classmethod
    def ichimoku(
        self, df, tenkan=None, kijun=None, senkou=None, include_chikou=True, offset=None
    ):
        import pandas_ta as ta

        ichimokudf, spandf = ta.ichimoku(
            df["high"], df["low"], df["close"], tenkan, kijun, senkou, False, 26
        )
        return ichimokudf

    @classmethod
    def supertrend(self, df, length=7, multiplier=3):
        import pandas_ta as ta

        sti = ta.supertrend(
            df["High"], df["Low"], df["Close"], length=length, multiplier=multiplier
        )
        # trend, direction, long, short
        # SUPERT_7_3.0  SUPERTd_7_3.0  SUPERTl_7_3.0  SUPERTs_7_3.0
        return sti if sti is not None else {'SUPERT_7_3.0':np.nan}

    @classmethod
    def psar(self, high, low, acceleration=0.02, maximum=0.2):
        psar = talib.SAR(high, low, acceleration=acceleration, maximum=maximum)
        return psar

    # @classmethod
    # def momentum(self, df):
    #     df.loc[:,'MOM'] = talib.MOM(df.loc[:,'Close'],2).apply(lambda x: round(x, 2))
    #     return df.loc[:,'MOM']

    # @classmethod
    # def get_dmi_df(self, df):
    #     df.loc[:,'DMI'] = talib.DX(df.loc[:,'High'],df.loc[:,'Low'],df.loc[:,'Close'],timeperiod=14)
    #     return df.loc[:,'DMI']

    # @classmethod
    # def get_macd_df(self, df):
    #     df.loc[:,'macd(12)'], df.loc[:,'macdsignal(9)'], df.loc[:,'macdhist(26)'] = talib.MACD(df.loc[:,'Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    #     df.loc[:,'macd(12)'] = df.loc[:,'macd(12)'].apply(lambda x: round(x, 3))
    #     df.loc[:,'macdsignal(9)']= df.loc[:,'macdsignal(9)'].apply(lambda x: round(x, 3))
    #     df.loc[:,'macdhist(26)'] = df.loc[:,'macdhist(26)'].apply(lambda x: round(x, 3))
    #     return df.loc[:,['macd(12)','macdsignal(9)', 'macdhist(26)']]

    # @classmethod
    # def get_sma_df(self, df):
    #     df.loc[:,'SMA(10)'] = talib.SMA(df.loc[:,'Close'],10).apply(lambda x: round(x, 2))
    #     df.loc[:,'SMA(50)'] = talib.SMA(df.loc[:,'Close'],50).apply(lambda x: round(x, 2))
    #     return df.loc[:,['Close','SMA(10)', 'SMA(50)']]

    # @classmethod
    # def get_ema_df(self, df):
    #     df.loc[:,'EMA(9)'] = talib.EMA(df.loc[:,'Close'], timeperiod = 9).apply(lambda x: round(x, 2))
    #     return df.loc[:,['Close','EMA(9)']]

    # @classmethod
    # def get_adx_df(self, df):
    #     df.loc[:,'ADX'] = talib.ADX(df.loc[:,'High'],df.loc[:,'Low'], df.loc[:,'Close'], timeperiod=14).apply(lambda x: round(x, 2))
    #     return df.loc[:,'ADX']

    # @classmethod
    # def get_bbands_df(self, df):
    #     df.loc[:,'BBands-U'], df.loc[:,'BBands-M'], df.loc[:,'BBands-L'] = talib.BBANDS(df.loc[:,'Close'], timeperiod =20)
    #     df.loc[:,'BBands-U'] = df.loc[:,'BBands-U'].apply(lambda x: round(x, 2))
    #     df.loc[:,'BBands-M'] = df.loc[:,'BBands-M'].apply(lambda x: round(x, 2))
    #     df.loc[:,'BBands-L'] = df.loc[:,'BBands-L'].apply(lambda x: round(x, 2))
    #     return df[['Close','BBands-U','BBands-M','BBands-L']]

    # @classmethod
    # def get_obv_df(self, df):
    #     if ('Close' not in df.keys()) or ('Volume' not in df.keys()):
    #         return np.nan
    #     df.loc[:,'OBV'] = talib.OBV(df.loc[:,'Close'], df.loc[:,'Volume'])
    #     return df.loc[:,'OBV']

    # @classmethod
    # def get_atr_df(self, df):
    #     df.loc[:,'ATR'] = talib.ATR(df.loc[:,'High'], df.loc[:,'Low'], df.loc[:,'Close'], timeperiod=14).apply(lambda x: round(x, 2))
    #     return df.loc[:,'ATR']

    # @classmethod
    # def get_natr_df(self, df):
    #     df.loc[:,'NATR'] = talib.NATR(df.loc[:,'High'], df.loc[:,'Low'], df.loc[:,'Close'], timeperiod=14).apply(lambda x: round(x, 2))
    #     return df.loc[:,'NATR']

    # @classmethod
    # def get_trange_df(self, df):
    #     df.loc[:,'TRANGE'] = talib.TRANGE(df.loc[:,'High'], df.loc[:,'Low'], df.loc[:,'Close']).apply(lambda x: round(x, 2))
    #     return df.loc[:,'TRANGE']

    # @classmethod
    # def get_atr_extreme(self, df):
    #     """
    #     ATR Exterme: which is based on 《Volatility-Based Technical Analysis》
    #     TTI is 'Trading The Invisible'

    #     @return: fasts, slows
    #     """
    #     highs = df.loc[:,'High']
    #     lows = df.loc[:,'Low']
    #     closes = df.loc[:,'Close']
    #     slowPeriod=30
    #     fastPeriod=3
    #     atr = self.get_atr_df(df)

    #     highsMean = talib.EMA(highs, 5)
    #     lowsMean = talib.EMA(lows, 5)
    #     closesMean = talib.EMA(closes, 5)

    #     atrExtremes = np.where(closes > closesMean,
    #                 ((highs - highsMean)/closes * 100) * (atr/closes * 100),
    #                 ((lows - lowsMean)/closes * 100) * (atr/closes * 100)
    #                 )
    #     fasts = talib.MA(atrExtremes, fastPeriod)
    #     slows = talib.EMA(atrExtremes, slowPeriod)
    #     return fasts, slows, np.std(atrExtremes[-slowPeriod:])

    # @classmethod
    # def get_atr_ratio(self, df):
    #     """
    #     ATR(14)/MA(14)
    #     """
    #     closes = df.loc[:,'Close']

    #     atr = self.get_atr_df(df)
    #     ma = talib.MA(closes, timeperiod=14)

    #     volatility = atr/ma

    #     s = pd.Series(volatility, index=df.index, name='volatility').dropna()
    #     pd.set_option('mode.chained_assignment', None)
    #     return pd.DataFrame({'volatility':round(s,2)})

    @classmethod
    def get_ppsr_df(self, high, low, close,pivotPoint=None):
        try:
            PSR = None
            if pivotPoint is None:
                return PSR
            PP = pd.Series((high + low + close) / 3)
            result = None
            if pivotPoint != "PP":
                if pivotPoint == "R1":
                    result = pd.Series(2 * PP - low)
                elif pivotPoint == "S1":
                    result = pd.Series(2 * PP - high)
                elif pivotPoint == "R2":
                    result = pd.Series(PP + high - low)
                elif pivotPoint == "S2":
                    result = pd.Series(PP - high + low)
                elif pivotPoint == "R3":
                    result = pd.Series(high + 2 * (PP - low))
                elif pivotPoint == "S3":
                    result = pd.Series(low - 2 * (high - PP))
            psr = {'Close':close, 'PP':round(PP,2)}
            if pivotPoint != "PP" and result is not None:
                psr[pivotPoint] = round(result,2)
            with pd.option_context('mode.chained_assignment', None):
                PSR = pd.DataFrame(psr)
        except: # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            pass
        return PSR

    @classmethod
    def CDLMORNINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "morningstar")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLMORNINGSTAR(open, high, low, close)

    @classmethod
    def CDLCUPANDHANDLE(self, open, high, low, close):
        if len(high) < 8:
            return False
        return (high.iloc[7] < high.iloc[6] and 
                high.iloc[7] < high.iloc[5] and 
                high.iloc[5] < high.iloc[4] and 
                high.iloc[5] < high.iloc[3] and 
                high.iloc[3] > high.iloc[2] and 
                high.iloc[0] > high.iloc[6])

    @classmethod
    def CDLMORNINGDOJISTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "morningdojistar")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLMORNINGDOJISTAR(open, high, low, close)

    @classmethod
    def CDLEVENINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "eveningstar")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLEVENINGSTAR(open, high, low, close)

    @classmethod
    def CDLEVENINGDOJISTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "eveningdojistar")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLEVENINGDOJISTAR(open, high, low, close)

    @classmethod
    def CDLLADDERBOTTOM(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "ladderbottom")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLLADDERBOTTOM(open, high, low, close)

    @classmethod
    def CDL3LINESTRIKE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3linestrike")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDL3LINESTRIKE(open, high, low, close)

    @classmethod
    def CDL3BLACKCROWS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3blackcrows")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDL3BLACKCROWS(open, high, low, close)

    @classmethod
    def CDL3INSIDE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3inside")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDL3INSIDE(open, high, low, close)

    @classmethod
    def CDL3OUTSIDE(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3outside")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDL3OUTSIDE(open, high, low, close)

    @classmethod
    def CDL3WHITESOLDIERS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "3whitesoldiers")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDL3WHITESOLDIERS(open, high, low, close)

    @classmethod
    def CDLHARAMI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "harami")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLHARAMI(open, high, low, close)

    @classmethod
    def CDLHARAMICROSS(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "haramicross")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLHARAMICROSS(open, high, low, close)

    @classmethod
    def CDLMARUBOZU(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "marubozu")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLMARUBOZU(open, high, low, close)

    @classmethod
    def CDLHANGINGMAN(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "hangingman")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLHANGINGMAN(open, high, low, close)

    @classmethod
    def CDLHAMMER(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "hammer")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLHAMMER(open, high, low, close)

    @classmethod
    def CDLINVERTEDHAMMER(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "invertedhammer")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLINVERTEDHAMMER(open, high, low, close)

    @classmethod
    def CDLSHOOTINGSTAR(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "shootingstar")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLSHOOTINGSTAR(open, high, low, close)

    @classmethod
    def CDLDRAGONFLYDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "dragonflydoji")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLDRAGONFLYDOJI(open, high, low, close)

    @classmethod
    def CDLGRAVESTONEDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "gravestonedoji")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLGRAVESTONEDOJI(open, high, low, close)

    @classmethod
    def CDLDOJI(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "doji")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLDOJI(open, high, low, close)

    @classmethod
    def CDLENGULFING(self, open, high, low, close):
        try:
            return talib.cdl_pattern(open, high, low, close, "engulfing")
        except Exception:  # pragma: no cover
            # default_logger().debug(e, exc_info=True)
            return talib.CDLENGULFING(open, high, low, close)

    @classmethod
    def argrelextrema(self, data, comparator, axis=0, order=1, mode="clip"):
        """
        Calculate the relative extrema of `data`.

        Relative extrema are calculated by finding locations where
        ``comparator(data[n], data[n+1:n+order+1])`` is True.

        Parameters
        ----------
        data : ndarray
            Array in which to find the relative extrema.
        comparator : callable
            Function to use to compare two data points.
            Should take two arrays as arguments.
        axis : int, optional
            Axis over which to select from `data`. Default is 0.
        order : int, optional
            How many points on each side to use for the comparison
            to consider ``comparator(n,n+x)`` to be True.
        mode : str, optional
            How the edges of the vector are treated. 'wrap' (wrap around) or
            'clip' (treat overflow as the same as the last (or first) element).
            Default 'clip'. See numpy.take.

        Returns
        -------
        extrema : ndarray
            Boolean array of the same shape as `data` that is True at an extrema,
            False otherwise.

        See also
        --------
        argrelmax, argrelmin

        Examples
        --------
        >>> import numpy as np
        >>> testdata = np.array([1,2,3,2,1])
        >>> _boolrelextrema(testdata, np.greater, axis=0)
        array([False, False,  True, False, False], dtype=bool)

        """
        if (int(order) != order) or (order < 1):
            raise ValueError("Order must be an int >= 1")

        datalen = data.shape[axis]
        locs = np.arange(0, datalen)

        results = np.ones(data.shape, dtype=bool)
        main = data.take(locs, axis=axis, mode=mode)
        for shift in range(1, order + 1):
            plus = data.take(locs + shift, axis=axis, mode=mode)
            minus = data.take(locs - shift, axis=axis, mode=mode)
            results &= comparator(main, plus)
            results &= comparator(main, minus)
            if ~results.any():
                return results
        return np.nonzero(results)
