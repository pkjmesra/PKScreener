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
# import gspread
# import pandas as pd
# '''
# Start using gspread:

# import gspread

# gc = gspread.service_account()

# # Open a sheet from a spreadsheet in one go
# wks = gc.open("Where is the money Lebowski?").sheet1

# # Update a range of cells using the top left corner address
# wks.update('A1', [[1, 2], [3, 4]])

# # Or update a single cell
# wks.update('B42', "it's down there somewhere, let me take another look.")

# # Format the header
# wks.format('A1:B1', {'textFormat': {'bold': True}})
# More Examples
# Opening a Spreadsheet
# # You can open a spreadsheet by its title as it appears in Google Docs
# sh = gc.open('My poor gym results') # <-- Look ma, no keys!

# # If you want to be specific, use a key (which can be extracted from
# # the spreadsheet's url)
# sht1 = gc.open_by_key('0BmgG6nO_6dprdS1MN3d3MkdPa142WFRrdnRRUWl1UFE')

# # Or, if you feel really lazy to extract that key, paste the entire url
# sht2 = gc.open_by_url('https://docs.google.com/spreadsheet/ccc?key=0Bm...FE&hl')
# Creating a Spreadsheet
# sh = gc.create('A new spreadsheet')

# # But that new spreadsheet will be visible only to your script's account.
# # To be able to access newly created spreadsheet you *must* share it
# # with your email. Which brings us to…
# Sharing a Spreadsheet
# sh.share('otto@example.com', perm_type='user', role='writer')
# Selecting a Worksheet
# # Select worksheet by index. Worksheet indexes start from zero
# worksheet = sh.get_worksheet(0)

# # By title
# worksheet = sh.worksheet("January")

# # Most common case: Sheet1
# worksheet = sh.sheet1

# # Get a list of all worksheets
# worksheet_list = sh.worksheets()
# Creating a Worksheet
# worksheet = sh.add_worksheet(title="A worksheet", rows="100", cols="20")
# Deleting a Worksheet
# sh.del_worksheet(worksheet)
# Getting a Cell Value
# # With label
# val = worksheet.get('B1').first()

# # With coords
# val = worksheet.cell(1, 2).value
# Getting All Values From a Row or a Column
# # Get all values from the first row
# values_list = worksheet.row_values(1)

# # Get all values from the first column
# values_list = worksheet.col_values(1)
# Getting All Values From a Worksheet as a List of Lists
# list_of_lists = worksheet.get_values()
# Finding a Cell
# # Find a cell with exact string value
# cell = worksheet.find("Dough")

# print("Found something at R%sC%s" % (cell.row, cell.col))

# # Find a cell matching a regular expression
# amount_re = re.compile(r'(Big|Enormous) dough')
# cell = worksheet.find(amount_re)
# Finding All Matched Cells
# # Find all cells with string value
# cell_list = worksheet.findall("Rug store")

# # Find all cells with regexp
# criteria_re = re.compile(r'(Small|Room-tiering) rug')
# cell_list = worksheet.findall(criteria_re)
# Updating Cells
# # Update a single cell
# worksheet.update('B1', 'Bingo!')

# # Update a range
# worksheet.update('A1:B2', [[1, 2], [3, 4]])

# # Update multiple ranges at once
# worksheet.batch_update([{
#     'range': 'A1:B2',
#     'values': [['A1', 'B1'], ['A2', 'B2']],
# }, {
#     'range': 'J42:K43',
#     'values': [[1, 2], [3, 4]],
# }])

# Color the background of A2:B2 cell range in black, change horizontal alignment, text color and font size:

# worksheet.format("A2:B2", {
#     "backgroundColor": {
#       "red": 0.0,
#       "green": 0.0,
#       "blue": 0.0
#     },
#     "horizontalAlignment": "CENTER",
#     "textFormat": {
#       "foregroundColor": {
#         "red": 1.0,
#         "green": 1.0,
#         "blue": 1.0
#       },
#       "fontSize": 12,
#       "bold": True
#     }
# })
# The second argument to format() is a dictionary containing the fields to update. A full specification of format options is available at CellFormat in Sheet API Reference.
# Documentation: https://gspread.readthedocs.io/
# '''
# def track(portfolio:None):
#     # gc = gspread.service_account_from_dict(credentials) # credentials can be a dictionary as well.
#     # credentials = {
#     # "type": "service_account",
#     # "project_id": "api-project-XXX",
#     # "private_key_id": "2cd … ba4",
#     # "private_key": "-----BEGIN PRIVATE KEY-----\nNrDyLw … jINQh/9\n-----END PRIVATE KEY-----\n",
#     # "client_email": "473000000000-yoursisdifferent@developer.gserviceaccount.com",
#     # "client_id": "473 … hd.apps.googleusercontent.com",
#     # ...
#     # }
#     # 'Stock', 'Consol.(30Prds)', 'Breakout (30Prds)', 'LTP','%Chng','Volume', 'MA-Signal', 'RSI', 'Trend(30Prds)', 'Pattern', 'CCI'])

#     gc = gspread.service_account(filename='pkscreener-ae8d8706001a.json')
#     worksheet = gc.open("PKScreener_Portfolio_Tracker")
#     folioSheet = worksheet.worksheet("All_NSE_Stocks")
#     print (portfolio)
#     portfolio.reset_index(inplace=True)
#     portfolio = pd.DataFrame(portfolio['Stock'],columns=['Stock'])
#     print(portfolio)
#     folioSheet.update([portfolio.columns.values.tolist()] + portfolio.values.tolist())

# import pandas as pd

# data = {'Name': ['John', 'Mary', 'Peter'],
#         'Age': [25, 35, 30],
#         'City': ['New York', 'San Francisco', 'Los Angeles'],
#         'State': ['NY', 'CA', 'CA']}

# df = pd.DataFrame(data)
# print(df)

# # Step 1: Convert the columns into a MultiIndex
# df.columns = [['PII','PII','Location','Location'],['Name','Age','City','State']]
# print(df)
# track(df)