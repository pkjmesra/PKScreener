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
from PKDevTools.classes.ColorText import colorText


def performXRay(saveResults=None, args=0):
    if saveResults is not None:
        print(saveResults)
        saveResults['LTP'] = saveResults['LTP'].astype(float).fillna(0.0)
        saveResults['LTPTdy'] = saveResults['LTPTdy'].astype(float).fillna(0.0)
        saveResults['Growth'] = saveResults['Growth'].astype(float).fillna(0.0)
        ltpSum1ShareEach = round(saveResults['LTP'].sum(),2)
        tdySum1ShareEach= saveResults['LTPTdy'].sum()
        growthSum1ShareEach= round(saveResults['Growth'].sum(),2)
        percentGrowth = round(100*growthSum1ShareEach/ltpSum1ShareEach,2)
        growth10k = 10000*(1+0.01*percentGrowth)
        clr = colorText.GREEN if growthSum1ShareEach >=0 else colorText.FAIL
        print(f"[+] Total (1 share each bought on the date above)           : ₹ {ltpSum1ShareEach:7.2f}")
        print(f"[+] Total (portfolio value today for 1 share each)          : ₹ {clr}{tdySum1ShareEach:7.2f}{colorText.END}")
        print(f"[+] Total (portfolio value growth in {args.backtestdaysago} days                : ₹ {clr}{growthSum1ShareEach:7.2f}{colorText.END}")
        print(f"[+] Growth (@ {clr}{percentGrowth:5.2f} %{colorText.END}) of ₹ 10k, if you'd have invested)    : ₹ {clr}{growth10k:7.2f}{colorText.END}")
