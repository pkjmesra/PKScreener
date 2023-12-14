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
"""Module for downloading financial data from morningstar.in.
"""

import csv
import http.client
import json
import numpy as np
import pandas as pd
import re
import urllib.request
from bs4 import BeautifulSoup, Tag
from datetime import date

class FinancialsDownloader(object):
    """Downloads financials from http://morningstar.in/
    """

    def __init__(self, table_prefix: str = 'morningstar_'):
        """Constructs the FinancialsDownloader instance.

        :param table_prefix: Prefix of the MySQL tables.
        """
        self._table_prefix = table_prefix

    # def download(self, ticker: str, conn: pymysql.Connection = None) -> dict:
    #     """Downloads and returns a dictionary containing pandas.DataFrames
    #     representing the financials (i.e. income statement, balance sheet,
    #     cash flow) for the given Morningstar ticker. If the MySQL connection
    #     is specified then the downloaded financials are uploaded to the MySQL
    #     database.

    #     :param ticker: Morningstar ticker.
    #     :param conn: MySQL connection.
    #     :return Dictionary containing pandas.DataFrames representing the
    #     financials for the given Morningstar ticker.
    #     """
    #     result = {}
    #     for report_type, table_name in [
    #             ('is', 'income_statement'),
    #             ('bs', 'balance_sheet'),
    #             ('cf', 'cash_flow')]:
    #         frame = self._download(ticker, report_type)
    #         result[table_name] = frame
    #         if conn:
    #             self._upload_frame(
    #                 frame, ticker, self._table_prefix + table_name, conn)
    #     if conn:
    #         self._upload_unit(ticker, self._table_prefix + 'unit', conn)
    #     result['period_range'] = self._period_range
    #     result['fiscal_year_end'] = self._fiscal_year_end
    #     result['currency'] = self._currency
    #     return result

    # def _download(self, ticker: str, report_type: str) -> pd.DataFrame:
    #     """Downloads and returns a pandas.DataFrame corresponding to the
    #     given Morningstar ticker and the given type of the report.

    #     :param ticker: Morningstar ticker.
    #     :param report_type: Type of the report ('is', 'bs', 'cf').
    #     :return  pandas.DataFrame corresponding to the given Morningstar ticker
    #     and the given type of the report.
    #     """
    #     url = (r'http://financials.morningstar.com/ajax/' +
    #            r'ReportProcess4HtmlAjax.html?&t=' + ticker +
    #            r'&region=usa&culture=en-US&cur=USD' +
    #            r'&reportType=' + report_type + r'&period=12' +
    #            r'&dataType=A&order=asc&columnYear=5&rounding=3&view=raw')
    #     with urllib.request.urlopen(url) as response:
    #         json_text = response.read().decode('utf-8')
    #         json_data = json.loads(json_text)
    #         result_soup = BeautifulSoup(json_data['result'],'html.parser')
    #         return self._parse(result_soup)

    def _parse(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Extracts and returns a pandas.DataFrame corresponding to the
        given parsed HTML response from financials.morningstar.com.

        :param soup: Parsed HTML response by BeautifulSoup.
        :return pandas.DataFrame corresponding to the given parsed HTML response
        from financials.morningstar.com.
        """
        # Left node contains the labels.
        left = soup.find('div', 'left').div
        # Main node contains the (raw) data.
        main = soup.find('div', 'main').find('div', 'rf_table')
        year = main.find('div', {'id': 'Year'})
        self._year_ids = [node.attrs['id'] for node in year]
        period_month = pd.datetime.strptime(year.div.text, '%Y-%m').month
        self._period_range = pd.period_range(
            year.div.text, periods=len(self._year_ids),
            # freq=pd.datetools.YearEnd(month=period_month))
            freq = pd.tseries.offsets.YearEnd(month=period_month))
        unit = left.find('div', {'id': 'unitsAndFiscalYear'})
        self._fiscal_year_end = int(unit.attrs['fyenumber'])
        self._currency = unit.attrs['currency']
        self._data = []
        self._label_index = 0
        self._read_labels(left)
        self._data_index = 0
        self._read_data(main)
        return pd.DataFrame(self._data,
                            columns=['parent_index', 'title'] + list(
                                self._period_range))

    def _read_labels(self, root_node: Tag, parent_label_index: int = None):
        """Recursively reads labels from the parsed HTML response.
        """
        for node in root_node:
            if node.has_attr('class') and 'r_content' in node.attrs['class']:
                self._read_labels(node, self._label_index - 1)
            if (node.has_attr('id') and
                    node.attrs['id'].startswith('label') and
                    not node.attrs['id'].endswith('padding') and
                    (not node.has_attr('style') or
                        'display:none' not in node.attrs['style'])):
                label_id = node.attrs['id'][6:]
                label_title = (node.div.attrs['title']
                               if node.div.has_attr('title')
                               else node.div.text)
                self._data.append({
                    'id': label_id,
                    'index': self._label_index,
                    'parent_index': (parent_label_index
                                     if parent_label_index is not None
                                     else self._label_index),
                    'title': label_title})
                self._label_index += 1

    def _read_data(self, root_node: Tag):
        """Recursively reads data from the parsed HTML response.
        """
        for node in root_node:
            if node.has_attr('class') and 'r_content' in node.attrs['class']:
                self._read_data(node)
            if (node.has_attr('id') and
                    node.attrs['id'].startswith('data') and
                    not node.attrs['id'].endswith('padding') and
                    (not node.has_attr('style') or
                        'display:none' not in node.attrs['style'])):
                data_id = node.attrs['id'][5:]
                while (self._data_index < len(self._data) and
                       self._data[self._data_index]['id'] != data_id):
                    # In some cases we do not have data for all labels.
                    self._data_index += 1
                assert(self._data_index < len(self._data) and
                       self._data[self._data_index]['id'] == data_id)
                for (i, child) in enumerate(node.children):
                    try:
                        value = float(child.attrs['rawvalue'])
                    except ValueError:
                        value = None
                    self._data[self._data_index][
                        self._period_range[i]] = value
                self._data_index += 1
