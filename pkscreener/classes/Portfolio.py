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
import pandas as pd
import numpy as np
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from pkscreener.classes.PKScheduledTaskProgress import PKScheduledTaskProgress
from pkscreener.classes.PKTask import PKTask

class PortfolioSecurity:
    def __init__(self, ticker):
        self.name = ticker
        self.ltp = 0
        self.quantity = 0
        self.date = None
        self.growth = 0
    
    @property
    def action(self):
        return (colorText.GREEN + "[Buy]"+ colorText.END) if self.quantity > 0 else ((colorText.FAIL + "[Sell]"+ colorText.END) if self.quantity < 0 else (colorText.WARN + "[Hold]"+ colorText.END))
    
    @property
    def investment(self):
        return self.ltp * self.quantity
    
    @property
    def description(self):
        return {"Date": self.date or PKDateUtilities.currentDateTime().strftime("%Y-%m-%d"),
                "Name": self.name, "LTP": self.ltp, "Quantity": self.quantity, 
                "Action": self.action, "Investment": self.investment, "RunningTotal": 0, 
                "Growth": self.growth, "Profits" : 0}

class Portfolio(PKScheduledTaskProgress):
    def __init__(self, name):
        super(Portfolio, self).__init__()
        self.name = name
        self._initialValue = 0
        self._currentValue = 0
        self.ledger = {}
        self.securities = {}
    
    @property
    def descriptionAsDataframe(self):
        portfolio_df = None
        for date, ledgerEntries in self.ledger.items():
            firstLedgerEntry = ledgerEntries[0]
            if portfolio_df is None:
                portfolio_df = pd.DataFrame(ledgerEntries,columns=firstLedgerEntry.keys())
            else:
                newEntries_df = pd.DataFrame(ledgerEntries,columns=firstLedgerEntry.keys())
                portfolio_df = pd.concat([portfolio_df,newEntries_df], axis=0)
        if portfolio_df is not None:
            portfolio_df["RunningTotal"] = portfolio_df[['Investment']].cumsum()
            portfolio_df["Profits"] = portfolio_df[['Growth']].cumsum()
        return portfolio_df
    
    def updatePortfolioFromXRayDataFrame(self,df:pd.DataFrame, periods:list,task:PKTask=None):
        if task is not None:
            taskId = task.taskId
            if taskId > 0:
                self.tasksDict[taskId] = task
        xray_df = df.copy()
        df_grouped = xray_df.groupby("Stock")
        periodCounter = -1
        task.progress = 0
        for period in periods:
            periodCounter += 1
            if f"LTP{period}" not in xray_df.columns:
                continue
            for stock, df_group in df_grouped:
                df_group["LTP"] = df_group["LTP"].astype(float).fillna(0)
                df_group[f"LTP{period}"] = df_group[f"LTP{period}"].astype(float).fillna(0)
                df_group[f"Growth{period}"] = df_group[f"Growth{period}"].astype(float).fillna(0)
                if df_group.iloc[0][f"LTP{period}"] == 0 or df_group.iloc[0][f"LTP"] == 0:
                    continue
                task.total = len(periods) * len(df_grouped)
                task.progress += 1
                self.updateProgress(task.taskId)
                security = PortfolioSecurity(stock)
                security.ltp = df_group.iloc[0]["LTP"] if not self.hasSecurity(stock) else df_group.iloc[0][f"LTP{period}"]
                previousPeriod = periods[periodCounter-1]
                try:
                    priceRise = round(df_group.iloc[0][f"LTP{period}"] - df_group.iloc[0]["LTP" if periodCounter == 0 else f"LTP{previousPeriod}"],2)
                    growth = df_group.iloc[0][f"Growth{period}"]
                    security.date = df_group.iloc[0]["Date"] if periodCounter == 0 else PKDateUtilities.nextTradingDate(df_group.iloc[0]["Date"], days=period).strftime("%Y-%m-%d")
                    if self.hasSecurity(stock):
                        # This security was already added earlier and exists in the portfolio
                        security.quantity = 1 if priceRise >= 0 else -1
                        if priceRise < 0:
                            security.growth = priceRise * abs(security.quantity)
                            self.removeSecurity(security=security)
                        else:
                            security.quantity = 0 # This is not an actual buy
                            security.growth = priceRise
                            security.ltp = df_group.iloc[0][f"LTP{period}"]
                            self.addSecurity(security=security)
                    else:
                        # This security was never added earlier. The very fact it exists under this
                        # outcome dataframe, we need to take losses and then remove it from portfolio
                        security.quantity = 1
                        security.growth = 0 # First day of trade
                        security.date = df_group.iloc[0]["Date"]
                        security.ltp = df_group.iloc[0]["LTP"]
                        self.addSecurity(security=security)
                        if priceRise < 0:
                            security.date = PKDateUtilities.nextTradingDate(df_group.iloc[0]["Date"], days=period).strftime("%Y-%m-%d")
                            security.ltp = df_group.iloc[0][f"LTP{period}"]
                            security.quantity = -1
                            security.growth = priceRise * abs(security.quantity)
                            self.removeSecurity(security=security)
                except: # pragma: no cover
                    pass
                    continue
        task.progress = task.total
        self.updateProgress(task.taskId)

    @property
    def profit(self):
        sorted_ledger_dates = sorted(self.ledger.items(), key=lambda kv: kv[0])
        bought = 0
        sold = 0
        for date, ledgerEntries in sorted_ledger_dates:
            for securityDict in ledgerEntries:
                if securityDict["Quantity"] > 0 and date == securityDict["Date"]:
                    bought += securityDict["LTP"] * securityDict["Quantity"]
                elif securityDict["Quantity"] < 0 and date == securityDict["Date"]:
                    sold += securityDict["LTP"] * securityDict["Quantity"]
        return round(abs(sold) - bought,2) if (sold != 0 and bought != 0) else 0
        
    @property
    def initialValue(self):
        if self._initialValue != 0:
            return self._initialValue
        sorted_ledger_dates = sorted(self.ledger.items(), key=lambda kv: kv[0])
        initialLedgerEntries = sorted_ledger_dates[1][0]
        initialValue = 0
        for securityDict in initialLedgerEntries:
            initialValue += securityDict["LTP"] * securityDict["Quantity"]
        self._initialValue = initialValue
        return initialValue

    @property
    def currentValue(self):
        if self._currentValue != 0:
            return round(self._currentValue,2)
        sorted_ledger_dates = sorted(self.ledger.items(), key=lambda kv: kv[0])
        currentValue = 0
        for date,ledgerEntries in sorted_ledger_dates:
            for securityDict in ledgerEntries:
                currentValue += securityDict["LTP"] * securityDict["Quantity"]
        self._currentValue = currentValue
        return currentValue
    
    @currentValue.setter
    def currentValue(self, newValue):
        self._currentValue = newValue
        
    def hasSecurity(self, securityName:str):
        return securityName in self.securities.keys()
    
    def addSecurity(self, security:PortfolioSecurity=None):
        self.securities[security.name] = security
        self.currentValue += security.ltp*security.quantity
        self.updateLedger(security=security)

    def removeSecurity(self, security:PortfolioSecurity=None):
        del self.securities[security.name]
        self.currentValue -= security.ltp*security.quantity
        self.updateLedger(security=security)

    def updateLedger(self,security:PortfolioSecurity=None):
        ledgerEntries = self.ledger.get(security.date) or []
        runningLedger = {"ScanType": self.name, "Date": security.date} | security.description
        ledgerEntries.append(runningLedger)
        self.ledger[security.date] = ledgerEntries

    def getDifference(self,x):
        return x.iloc[-1] - x.iloc[0]

    def differenceFromLastNTradingSession(self,df,n=1):
        df['LTP'].rolling(window=n).apply(self.getDifference)


class PortfolioCollection(SingletonMixin,PKScheduledTaskProgress, metaclass=SingletonType):
    def __init__(self):
        super(PortfolioCollection, self).__init__()
        self._portfolios = {}
        self._portfolios_df = None
        self._portfoliosSummary_df = None
        self.ledgerSummaryAsDataframeTaskId = 0
        self.portfoliosAsDataframeTaskId = 0

    def getLedgerSummaryAsDataframe(self,*args):
        task = args[0]
        taskId = task.taskId
        if taskId > 0:
            self.tasksDict[taskId] = task
            self.ledgerSummaryAsDataframeTaskId = taskId
        return self.ledgerSummaryAsDataframe
    
    def getPortfoliosAsDataframe(self,*args):
        task = args[0]
        taskId = task.taskId
        if taskId > 0:
            self.tasksDict[taskId] = task
            self.portfoliosAsDataframeTaskId = taskId
        return self.portfoliosAsDataframe
    
    @property
    def ledgerSummaryAsDataframe(self):
        task = None
        if self._portfoliosSummary_df is not None:
            if self.ledgerSummaryAsDataframeTaskId > 0:
                task = self.tasksDict.get(self.ledgerSummaryAsDataframeTaskId)
                task.total = len(self._portfolios.keys())
                task.progress = task.total
                self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
                task.result = self._portfoliosSummary_df
                task.resultsDict[task.taskId] = self._portfoliosSummary_df
            return self._portfoliosSummary_df
        portfolios_df = None
        if len(self._portfolios) > 0:
            for _, portfolio in self._portfolios.items():
                portfolio_df = portfolio.descriptionAsDataframe
                if portfolio_df is None:
                    continue
                if portfolios_df is None:
                    portfolios_df = portfolio_df.tail(5).copy()
                else:
                    portfolios_df = pd.concat([portfolios_df,portfolio_df.tail(5)], axis=0)
                if task is not None:
                    task.progress = len(portfolios_df)
                self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
        self._portfoliosSummary_df = portfolios_df
        if task is not None:
            # Mark the progress finished
            task.progress = task.total
            self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
            task.result = portfolios_df
            task.resultsDict[task.taskId] = self.portfolios_df
        return portfolios_df
        
    @property
    def portfoliosAsDataframe(self):
        task = None
        if self._portfolios_df is not None:
            if self.portfoliosAsDataframeTaskId > 0:
                task = self.tasksDict.get(self.portfoliosAsDataframeTaskId)
                task.total = len(self._portfolios.keys())
                task.progress = task.total
                self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
                task.result = self._portfolios_df
                task.resultsDict[task.taskId] = self._portfolios_df
            return self._portfolios_df
        portfolios_df = None
        if len(self._portfolios) > 0:
            for _, portfolio in self._portfolios.items():
                portfolio_df = portfolio.descriptionAsDataframe
                if portfolio_df is None:
                    continue
                if portfolios_df is None:
                    portfolios_df = portfolio_df.copy()
                else:
                    portfolios_df = pd.concat([portfolios_df,portfolio_df], axis=0)
                if task is not None:
                    task.progress = len(portfolios_df)
                self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
        self._portfolios_df = portfolios_df
        if task is not None:
            # Mark the progress finished
            task.progress = task.total
            self.updateProgress(self.ledgerSummaryAsDataframeTaskId)
            task.result = portfolios_df
            task.resultsDict[task.taskId] = self.portfolios_df
        return portfolios_df

    def addPortfolio(self,portfolio:Portfolio):
        self._portfolios[portfolio.name] = portfolio
