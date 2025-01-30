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

import asyncio
import os
import datetime
from PIL import Image,ImageDraw,ImageFont
try:
    from pyppeteer import launch
except: # pragma: no cover
    pass
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger
from pkscreener.classes import Utility
from pkscreener.classes.MarketStatus import MarketStatus
from pkscreener.classes import ConfigManager
configManager = ConfigManager.tools()

QUERY_SELECTOR_TIMEOUT = 1000

async def takeScreenshot(page,saveFileName=None,text=""):
    configManager.getConfig(ConfigManager.parser)
    clip_x = configManager.barometerx
    clip_y = configManager.barometery
    clip_width = configManager.barometerwidth
    clip_height = configManager.barometerheight
    window_width = configManager.barometerwindowwidth
    window_height = configManager.barometerwindowheight

    countriesSVG = await page.querySelector(selector='.countries.zoomable')
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    elementWidth = await page.evaluate(f'(countriesSVG) => countriesSVG.parentElement.parentElement.width.baseVal.valueInSpecifiedUnits', countriesSVG)
    clip_x = int((window_width - elementWidth)/2)
    clip_width = elementWidth
    folderPath = Archiver.get_user_data_dir()
    indiaElement = await page.querySelector(selector='#India')
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    indiaPolygon = await page.evaluate('(indiaElement) => indiaElement.children[0]', indiaElement)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    gSelector = 'g[id="India"]'
    dismissSelector = '.date-label'
    await page.click(gSelector)
    # await page.evaluate('(gSelector) => gSelector.click()', gSelector)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    hoverElement = await page.querySelector(selector='.popover-title')
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    await page.evaluate(f'(hoverElement) => hoverElement.innerHTML=hoverElement.innerHTML.replaceAll("Morningstar","").replaceAll("PR INR","{text}")', hoverElement)
    
    # Fix the popover pointer to top right and adjust it to show european market status
    popoverSelector = '.map-popover'
    hoverElement = await page.querySelector(selector=popoverSelector)
    await page.evaluate('(hoverElement) => hoverElement.classList.value="map-popover details top-right"', hoverElement)
    await page.evaluate('(hoverElement) => hoverElement.style.top="270.5px"', hoverElement)
    await page.evaluate('(hoverElement) => hoverElement.style.left="425px"', hoverElement)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)

    # Take the screenshot
    srcFilePath = os.path.join(folderPath,saveFileName)
    await page.screenshot({'path': srcFilePath, 'clip': {"x":clip_x,"y":clip_y,"width":clip_width,"height":clip_height}})
    await page.click(dismissSelector)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    srcFileSize = os.stat(srcFilePath).st_size if os.path.exists(srcFilePath) else 0
    default_logger().debug(f"{saveFileName} saved at {srcFilePath} with size {srcFileSize} bytes")

# Get the Global Market Barometer for global and Indian stock markets.
# This captures the screenshot of the India market and its growth 
# status by loading it in the browser and simulating the click 
# behaviour  of the pop-ups.
async def getScreenshotsForGlobalMarketBarometer():
    # https://scrapeops.io/python-web-scraping-playbook/python-pyppeteer/#how-to-click-on-buttons-with-pyppeteer
    launchDict = {
            "headless": True,
            "args": [
                '--start-maximized',
                '--window-size=1920,1080',
                '--no-sandbox'
            ],
            "defaultViewport": None,
        }
    if "PUPPETEER_EXECUTABLE_PATH" in os.environ.keys():
        launchDict["executablePath"] = os.environ["PUPPETEER_EXECUTABLE_PATH"]
    browser = await launch(launchDict); 
    page = await browser.newPage()
    # # Must use this when headless = True above. Not needed when headless = False
    # await page._client.send('Emulation.clearDeviceMetricsOverride')

    await page.goto('https://www.morningstar.ca/ca/Markets/global-market-barometer.aspx',timeout=30*QUERY_SELECTOR_TIMEOUT, waitUntil=['load','domcontentloaded','networkidle0'])
    # Get the latest date for which this GMB is being loaded
    # dateElement = await page.querySelector(selector='.date-label')
    # date = await page.evaluate('(dateElement) => dateElement.textContent', dateElement)
    # await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    # Show the india hover tooltip. If you don't do this, the screenshot is only 50% of the map
    await takeScreenshot(page=page, saveFileName='gmbstat.png',text="Performance")

    # Let's find the valuation of the market
    # xpath = '//*[@id="tabs"]/div/mds-button-group/div/slot/div/mds-button[2]/label/input'
    selector = 'input[value="Valuation"]'
    btnValuation = await page.querySelector(selector=selector)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)
    await page.evaluate('(btnValuation) => btnValuation.click()', btnValuation)
    await page.waitFor(selectorOrFunctionOrTimeout=QUERY_SELECTOR_TIMEOUT)

    await takeScreenshot(page=page, saveFileName='gmbvaluation.png',text="Valuation")
    await browser.close()

# Gets the valuation of the India Stock Market from the pop-over
# on the Global Market Barometer. It also takes the screenshot
# adds the watermarks, repository details and then saves it as a
# PNG file that can then be shared with others.
def getGlobalMarketBarometerValuation():
    gmbPath = None
    try:
        asyncio.get_event_loop().run_until_complete(getScreenshotsForGlobalMarketBarometer())
    except (asyncio.exceptions.IncompleteReadError,asyncio.exceptions.InvalidStateError): # pragma: no cover
        return gmbPath
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e: # pragma: no cover
        default_logger().debug(e, exc_info=True)
        pass
    folderPath = Archiver.get_user_data_dir()

    try:
        gapHeight = 65
        bgColor = (0,0,0)
        fontPath = Utility.tools.setupReportFont()
        artfont = ImageFont.truetype(fontPath, 12)
        gmbPerformance = Image.open(os.path.join(folderPath,'gmbstat.png')) # 710 x 460
        gmbValuation = Image.open(os.path.join(folderPath,'gmbvaluation.png')) # 710 x 450
        gmbPerf_size = gmbPerformance.size
        gmbValue_size = gmbValuation.size
        gmbPerformance = Utility.tools.addQuickWatermark(gmbPerformance, dataSrc="Morningstar, Inc")
        gmbValuation = Utility.tools.addQuickWatermark(gmbValuation, dataSrc="Morningstar, Inc")
        gmbCombined = Image.new('RGB',(gmbPerf_size[0], gmbPerf_size[1]+gmbValue_size[1]+gapHeight), bgColor)
        gmbCombined.paste(gmbPerformance,(0,0))
        draw = ImageDraw.Draw(gmbCombined)
        # artwork
        nseMarketStatus = MarketStatus().getMarketStatus(exchangeSymbol="^NSEI",namedOnly=True)
        bseMarketStatus = MarketStatus().getMarketStatus(exchangeSymbol="^BSESN",namedOnly=True)
        nasdaqMarketStatus = MarketStatus().getMarketStatus(exchangeSymbol="^IXIC")
        repoText = f'https://GitHub.com/pkjmesra/pkscreener/ | © {datetime.date.today().year} pkjmesra | https://t.me/PKScreener\n{nseMarketStatus}\n{bseMarketStatus}\n{nasdaqMarketStatus}'
        draw.text((5, gmbPerf_size[1]+5), Utility.tools.removeAllColorStyles(repoText), font=artfont, fill="lightgreen")
        gmbCombined.paste(gmbValuation,(0,gmbPerf_size[1]+gapHeight))
        gmbCombined.save(os.path.join(folderPath,"gmb.png"),"PNG")
        gmbPath = os.path.join(folderPath,"gmb.png")
        srcFileSize = os.stat(gmbPath).st_size if os.path.exists(gmbPath) else 0
        default_logger().debug(f"gmb.png saved at {gmbPath} with size {srcFileSize} bytes")
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e: # pragma: no cover
        default_logger().debug(e, exc_info=True)
        pass
    return gmbPath
