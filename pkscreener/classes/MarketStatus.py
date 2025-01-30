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
import os
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes import log as log

class MarketStatus(SingletonMixin, metaclass=SingletonType):
    nseFetcher = nseStockDataFetcher()
    def __init__(self):
        super(MarketStatus, self).__init__()

    @property
    def exchange(self):
        if "exchange" in self.attributes.keys():
            return self.attributes["exchange"]
        else:
            return "^NSEI"
    
    @exchange.setter
    def exchange(self, exchangeKey):
        if self.exchange != exchangeKey:
            self.marketStatus = self.getMarketStatus(exchangeSymbol=exchangeKey)
        self.attributes["exchange"] = exchangeKey

    @property
    def marketStatus(self):
        if "marketStatus" in self.attributes.keys():
            return self.attributes["marketStatus"]
        else:
            # self.attributes["lock"] = "" # We don't need threading lock here
            self.marketStatus = ""
            return self.marketStatus
    
    @marketStatus.setter
    def marketStatus(self, status):
        self.attributes["marketStatus"] = status

    def getMarketStatus(self, progress=None, task_id=0, exchangeSymbol="^NSEI",namedOnly=False):
        lngStatus = ""
        try:
            suppressLogs = True
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                suppressLogs = os.environ["PKDevTools_Default_Log_Level"] == str(log.logging.NOTSET)
            with SuppressOutput(suppress_stdout=suppressLogs, suppress_stderr=suppressLogs):
                if progress:
                    progress[task_id] = {"progress": 0, "total": 1}
                _,lngStatus,_ = MarketStatus.nseFetcher.capitalMarketStatus(exchange=exchangeSymbol)
                if exchangeSymbol in ["^NSEI","^BSESN"] and not namedOnly:
                    _,bseStatus,_ = MarketStatus.nseFetcher.capitalMarketStatus(exchange="^BSESN")
                    lngStatus = f"{lngStatus} | {bseStatus}"
            if progress:
                progress[task_id] = {"progress": 1, "total": 1}
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        self.marketStatus = lngStatus
        return lngStatus
