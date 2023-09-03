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

from pkscreener.classes.MenuOptions import MenuRenderStyle, menus

m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()
HTMLHEAD_TEXT="""
<html>
    <body>
        <span>1. Backtest and Summary Reports for All Nifty Stocks over the last 30-trading-sessions-periods</span><br />
        <span>2. Backtest report for a given scan strategy shows what profit/loss one would have incurred following that strategy over that given x-trading-period.</span><br />
        <span>3. Summary report shows the overall correctness of the strategy outcome for a given period and then overall for all periods combined altogether in the last row.</span><br />
        <span><b>Disclaimer: Only for learning purposes! Use at your own risk!</b>></span><br />
        <table border="1px">
            <tr>
                <th>Srl #</th>
                <th>Report Name</th>
                <th>Stock-wise Report</th>
                <th>Summary Report</th>
            </tr>"""
HTMLFOOTER_TEXT = """
        </table>
    </body>
</html>
"""
TR_OPENER = "\n            <tr>"
TR_CLOSER = "            </tr>\n"
TD_GENERAL="\n                <td>{}</td>"
TD_LINK="\n                <td><a href='https://pkjmesra.github.io/PKScreener/Backtest-Reports/PKScreener_{}_{}_StockSorted.html' target='_blank'>{}</a></td>"

f = open(os.path.join(os.getcwd(),"BacktestReports.html"), "w")
f.write(HTMLHEAD_TEXT)

cmds0 = m0.renderForMenu(
        selectedMenu=None,
        skip=["S", "T", "E", "U", "Z", "X", "H", "Y"],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
counter = 1
for mnu0 in cmds0:
    p0 = mnu0.menuKey.upper()
    selectedMenu = m0.find(p0)
    cmds1 = m1.renderForMenu(
        selectedMenu=selectedMenu,
        skip=["W","N","E","M","Z","0","1","2","3","4","5","6","7","8","9","10","11","13","14"],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    for mnu1 in cmds1:
        p1 = mnu1.menuKey.upper()
        selectedMenu = m1.find(p1)
        cmds2 = m2.renderForMenu(
            selectedMenu=selectedMenu,
            skip=[
                "0"
                "21",
                "22",
                "23",
                "24",
                "25",
                "26",
                "27",
                "28",
                "42",
                "M",
                "Z",
            ],
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for mnu2 in cmds2:
            p2 = mnu2.menuKey.upper()
            if p2 == "0":
                continue
            if p2 in ["6", "7"]:
                selectedMenu = m2.find(p2)
                cmds3 = m3.renderForMenu(
                    selectedMenu=selectedMenu,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
                for mnu3 in cmds3:
                    p3 = mnu3.menuKey.upper()
                    f.writelines([TR_OPENER,
                              f"{TD_GENERAL}".format(str(counter)),
                              f"{TD_GENERAL}".format(str(mnu2.menuText.strip()+" > <br />"+mnu3.menuText.strip())),
                              f"{TD_LINK}".format(f"{p0}_{p1}_{p2}_{p3}","backtest_result",f"{p0}_{p1}_{p2}_{p3}"),
                              f"{TD_LINK}".format(f"{p0}_{p1}_{p2}_{p3}","Summary",f"{p0}_{p1}_{p2}_{p3}"),
                              TR_CLOSER
                              ])
                    counter += 1
            else:
                f.writelines([TR_OPENER,
                              f"{TD_GENERAL}".format(str(counter)),
                              f"{TD_GENERAL}".format(str(mnu2.menuText.strip())),
                              f"{TD_LINK}".format(f"{p0}_{p1}_{p2}","backtest_result",f"{p0}_{p1}_{p2}"),
                              f"{TD_LINK}".format(f"{p0}_{p1}_{p2}","Summary",f"{p0}_{p1}_{p2}"),
                              TR_CLOSER
                              ])
                counter += 1

f.write(HTMLFOOTER_TEXT)                
f.close()