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
import datetime
import math
import pandas as pd
import textwrap
import random
import platform
import warnings

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

from PIL import Image, ImageDraw, ImageFont
import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = None
from halo import Halo

from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities

from pkscreener.classes import Utility, ConfigManager
from pkscreener.classes.Utility import artText, marketStatus
import pkscreener.classes.Fetcher as Fetcher

# Class for managing misc image utility methods
class PKImageTools:
    fetcher = Fetcher.screenerStockDataFetcher()
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)

    def getsize_multiline(font,srcText,x=0,y=0):
        zeroSizeImage = Image.new('RGB',(0, 0), (0,0,0))
        zeroDraw = ImageDraw.Draw(zeroSizeImage)
        # zeroDraw = ImageDraw.Draw(zeroSizeImage)
        bbox = zeroDraw.multiline_textbbox((x,y),srcText,font)
        # Calculate width and height from the bounding box
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        # default_logger().debug(f"Text size for text: {srcText}: {width}x{height}")
        return width, height

    def getsize(font,srcText,x=0,y=0):
        left, top, bottom, right = font.getbbox(srcText)
        return right - left, bottom - top
    
    def addQuickWatermark(sourceImage:Image, xVertical=None, dataSrc="", dataSrcFontSize=10):
        width, height = sourceImage.size
        watermarkText = f"© {datetime.date.today().year} pkjmesra | PKScreener"
        message_length = len(watermarkText)
        # load font (tweak ratio based on a particular font)
        FONT_RATIO = 1.5
        DIAGONAL_PERCENTAGE = .85
        DATASRC_FONTSIZE = dataSrcFontSize
        dataSrc = f"Src: {dataSrc}"
        diagonal_length = int(math.sqrt((width**2) + (height**2)))
        diagonal_to_use = diagonal_length * DIAGONAL_PERCENTAGE
        height_to_use = height * DIAGONAL_PERCENTAGE
        font_size = int(diagonal_to_use / (message_length / FONT_RATIO))
        font_size_vertical = int(height_to_use / (message_length / FONT_RATIO))
        fontPath = PKImageTools.setupReportFont()
        font = ImageFont.truetype(fontPath, font_size)
        font_vertical = ImageFont.truetype(fontPath, font_size_vertical)
        #font = ImageFont.load_default() # fallback

        # watermark 1
        opacity = int(256 * .6)
        _,_,mark_width, mark_height = font.getbbox(watermarkText)
        watermark = Image.new('RGBA', (mark_width, mark_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        draw.text((0, 0), text=watermarkText, font=font, fill=(128, 128, 128, opacity))
        angle = math.degrees(math.atan(height/width))
        watermark_diag = watermark.rotate(angle, expand=1)
        
        _,_,mark_width_ver, mark_height_ver = font_vertical.getbbox(watermarkText)
        watermark_ver = Image.new('RGBA', (mark_width_ver, mark_height_ver), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_ver)
        draw.text((0, 0), text=watermarkText, font=font_vertical, fill=(128, 128, 128, opacity))
        watermark_vertical = watermark_ver.rotate(90, expand=1)

        # merge
        try:
            logo_wm_path = os.path.join(Archiver.get_user_outputs_dir().replace("results","pkscreener"),"LogoWM.txt")
            if not os.path.isfile(logo_wm_path):
                resp = Utility.tools.tryFetchFromServer(cache_file="LogoWM.png",directory="screenshots/logos",hideOutput=True)
                with open(logo_wm_path,"wb",) as f:
                    f.write(resp.content)
            logo_img = Image.open(logo_wm_path,formats=["PNG"]).convert('LA')
            # logo_img = logo_img.resize((min(width,height),min(width,height)), Image.LANCZOS, reducing_gap=2)
            lx, ly = logo_img.size
            plx = int((width - lx)/4)
            ply = int((height - ly)/3)
            sourceImage.paste(logo_img, (plx, ply), logo_img)
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            default_logger().debug(e,exc_info=True)
            pass

        wx, wy = watermark_diag.size
        px = int((width - wx)/2)
        py = int((height - wy)/2)
        wxv, wyv = watermark_vertical.size
        pxv =  int((width - wxv)/12) if xVertical is None else xVertical
        pyv= int((height - wyv)/2)
        sourceImage.paste(watermark_diag, (px, py, px + wx, py + wy), watermark_diag)
        sourceImage.paste(watermark_vertical, (pxv, pyv, pxv + wxv, pyv + wyv), watermark_vertical)
        
        # Draw the data sources
        dataSrcFont = ImageFont.truetype(fontPath, DATASRC_FONTSIZE)
        dataSrc_width, dataSrc_height = PKImageTools.getsize_multiline(font=dataSrcFont,srcText=dataSrc)
        draw = ImageDraw.Draw(sourceImage)
        draw.text((width-dataSrc_width, height-dataSrc_height-2), text=dataSrc, font=dataSrcFont, fill=(128, 128, 128, opacity))
        # sourceImage.show()
        return sourceImage
    
    def removeAllColorStyles(styledText):
        styles = [
            colorText.HEAD,
            colorText.END,
            colorText.BOLD,
            colorText.UNDR,
            colorText.BLUE,
            colorText.GREEN,
            colorText.BRIGHTGREEN,
            colorText.WARN,
            colorText.BRIGHTYELLOW,
            colorText.FAIL,
            colorText.BRIGHTRED,
            colorText.WHITE,
        ]
        if isinstance(styledText,pd.DataFrame):
            styledTextCopy = styledText.copy()
            with pd.option_context('mode.chained_assignment', None):
                for col in styledTextCopy.columns:
                    for style in styles:
                        try:
                            styledTextCopy[col] = styledTextCopy[col].astype(str).str.replace(style,"")
                        except: # pragma: no cover
                            pass
            return styledTextCopy
        elif isinstance(styledText,str):
            cleanedUpStyledValue = str(styledText)
            for style in styles:
                cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
            return cleanedUpStyledValue
        else:
            return styledText

    def getCellColors(cellStyledValue="", defaultCellFillColor="black"):
        otherStyles = [colorText.HEAD, colorText.BOLD, colorText.UNDR]
        mainStyles = [
            colorText.BLUE,
            colorText.GREEN,
            colorText.BRIGHTGREEN,
            colorText.WARN,
            colorText.BRIGHTYELLOW,
            colorText.FAIL,
            colorText.BRIGHTRED,
            colorText.WHITE,
        ]
        colorsDict = {
            colorText.BLUE: "blue",
            colorText.BRIGHTGREEN: "darkgreen",
            colorText.GREEN: "green"
            if defaultCellFillColor == "black"
            else "lightgreen",
            colorText.WARN: "darkorange"
            if defaultCellFillColor == "black"
            else "yellow",
            colorText.BRIGHTYELLOW: "darkyellow",
            colorText.FAIL: "red",
            colorText.BRIGHTRED : "darkred",
            colorText.WHITE: "white" 
            if defaultCellFillColor == "white"
            else "black",
        }
        cleanedUpStyledValues = []
        cellFillColors = []
        cleanedUpStyledValue = str(cellStyledValue)
        prefix = ""
        for style in otherStyles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
        # Find how many different colors are used for the cell value
        coloredStyledValues = cleanedUpStyledValue.split(colorText.END)
        for cleanedUpStyledValue in coloredStyledValues:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(colorText.END,"")
            if cleanedUpStyledValue.strip() in ["", ",","/"]:
                if len(cleanedUpStyledValues) > 0:
                    cleanedUpStyledValues[len(cleanedUpStyledValues)-1] = f"{cleanedUpStyledValues[len(cleanedUpStyledValues)-1]}{cleanedUpStyledValue}"
                else:
                    prefix = cleanedUpStyledValue
            else:
                for style in mainStyles:
                    if style in cleanedUpStyledValue:
                        cellFillColors.append(colorsDict[style])
                        for style in mainStyles:
                            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
                        cleanedUpStyledValues.append(prefix + cleanedUpStyledValue)
                        prefix = ""
                
        if len(cellFillColors) == 0:
            cellFillColors = [defaultCellFillColor]
        if len(cleanedUpStyledValues) == 0:
            cleanedUpStyledValues = [str(cellStyledValue)]
        return cellFillColors, cleanedUpStyledValues

    @Halo(text='', spinner='dots')
    def tableToImage(
        table,
        styledTable,
        filename,
        label,
        backtestSummary=None,
        backtestDetail=None,
        addendum=None,
        addendumLabel=None,
        summaryLabel = None,
        detailLabel = None,
        legendPrefixText = ""
    ):
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if (("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
                return
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        ART_FONT_SIZE = 30
        STD_FONT_SIZE = 60
        try:
            # First 4 lines are headers. Last 1 line is bottom grid line
            fontPath = PKImageTools.setupReportFont()
            artfont = ImageFont.truetype(fontPath, ART_FONT_SIZE)
            stdfont = ImageFont.truetype(fontPath, STD_FONT_SIZE)
            
            bgColor, gridColor, artColor, menuColor = PKImageTools.getDefaultColors()

            dfs_to_print = [styledTable, backtestSummary, backtestDetail]
            unstyled_dfs = [table, backtestSummary, backtestDetail]
            reportTitle = f"  [+] As of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H.%M.%S')} IST > You chose {label}"
            titleLabels = [
                f"  [+] Scan results for {label} :",
                summaryLabel if summaryLabel is not None else "  [+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)",
                detailLabel if detailLabel is not None else "  [+] 1 to 30 period gain/loss % for matching stocks on respective date from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]",
            ]

            artfont_arttext_width, artfont_arttext_height = PKImageTools.getsize_multiline(font=artfont,srcText=artText+ f"{marketStatus()}")
            stdFont_oneLinelabel_width, stdFont_oneLinelabel_height = PKImageTools.getsize_multiline(font=stdfont,srcText=label)
            stdFont_scanResulttext_width, stdFont_scanResulttext_height = PKImageTools.getsize_multiline(font=stdfont,srcText=table) if len(table) > 0 else (0,0)
            unstyled_backtestsummary = PKImageTools.removeAllColorStyles(backtestSummary)
            unstyled_backtestDetail = PKImageTools.removeAllColorStyles(backtestDetail)
            stdFont_backtestSummary_text_width,stdFont_backtestSummary_text_height= PKImageTools.getsize_multiline(font=stdfont,srcText=unstyled_backtestsummary) if (unstyled_backtestsummary is not None and len(unstyled_backtestsummary) > 0) else (0,0)
            stdFont_backtestDetail_text_width, stdFont_backtestDetail_text_height = PKImageTools.getsize_multiline(font=stdfont, srcText=unstyled_backtestDetail) if (unstyled_backtestDetail is not None and len(unstyled_backtestDetail) > 0) else (0,0)
            artfont_scanResultText_width, _ = PKImageTools.getsize_multiline(font=artfont,srcText=table) if len(table) > 0 else (0,0)
            artfont_backtestSummary_text_width, _ = PKImageTools.getsize_multiline(font= artfont,srcText=backtestSummary) if (backtestSummary is not None and len(backtestSummary)) > 0 else (0,0)
            stdfont_addendumtext_height = 0
            stdfont_addendumtext_width = 0
            if addendum is not None and len(addendum) > 0:
                unstyled_addendum = PKImageTools.removeAllColorStyles(addendum)
                stdfont_addendumtext_width , stdfont_addendumtext_height = PKImageTools.getsize_multiline(font=stdfont,srcText=unstyled_addendum)
                titleLabels.append(addendumLabel)
                dfs_to_print.append(addendum)
                unstyled_dfs.append(unstyled_addendum)

            repoText = PKImageTools.getRepoHelpText(table,backtestSummary)
            artfont_repotext_width, artfont_repotext_height = PKImageTools.getsize_multiline(font=artfont,srcText=repoText)
            legendText = legendPrefixText + PKImageTools.getLegendHelpText(table,backtestSummary)
            _, artfont_legendtext_height = PKImageTools.getsize_multiline(font=artfont,srcText=legendText)
            column_separator = "|"
            line_separator = "+"
            stdfont_sep_width, _ = PKImageTools.getsize_multiline(font=stdfont, srcText=column_separator)

            startColValue = 100
            xVertical = startColValue
            rowPixelRunValue = 9
            im_width = max(
                artfont_arttext_width,
                stdFont_oneLinelabel_width,
                stdFont_scanResulttext_width,
                stdFont_backtestSummary_text_width,
                stdFont_backtestDetail_text_width,
                artfont_repotext_width,
                artfont_scanResultText_width,
                artfont_backtestSummary_text_width,
                stdfont_addendumtext_width
            ) + int(startColValue * 2)
            im_height = int(
                        artfont_arttext_height # Always
                        + 3*stdFont_oneLinelabel_height # Title label # Always
                        + stdFont_scanResulttext_height + (stdFont_oneLinelabel_height if int(stdFont_scanResulttext_height) > 0 else 0)
                        + stdFont_backtestSummary_text_height + (stdFont_oneLinelabel_height if int(stdFont_backtestSummary_text_height) > 0 else 0)
                        + stdFont_backtestDetail_text_height + (stdFont_oneLinelabel_height if int(stdFont_backtestDetail_text_height) > 0 else 0)
                        + artfont_repotext_height # Always
                        + artfont_legendtext_height # Always
                        + stdfont_addendumtext_height + (stdFont_oneLinelabel_height if int(stdfont_addendumtext_height) > 0 else 0)
                    )
            im = Image.new("RGB",(im_width,im_height),bgColor)
            draw = ImageDraw.Draw(im)
            # artwork
            draw.text((startColValue, rowPixelRunValue), artText+ f"{PKImageTools.removeAllColorStyles(marketStatus())}", font=artfont, fill=artColor)
            rowPixelRunValue += artfont_arttext_height + 1
            # Report title
            # reportTitle = tools.wrapFitLegendText(table,backtestSummary, reportTitle)
            draw.text((startColValue, rowPixelRunValue), reportTitle, font=stdfont, fill=menuColor)
            rowPixelRunValue += stdFont_oneLinelabel_height + 1
            counter = -1
            for df in dfs_to_print:
                counter += 1
                colPixelRunValue = startColValue
                try:
                    if df is None or len(df) == 0:
                        continue
                except: # pragma: no cover
                    continue
                # selected menu options and As of DateTime
                draw.text(
                    (colPixelRunValue, rowPixelRunValue),
                    titleLabels[counter],
                    font=stdfont,
                    fill=menuColor,
                )
                rowPixelRunValue += stdFont_oneLinelabel_height
                unstyledLines = unstyled_dfs[counter].splitlines()
                lineNumber = 0
                screenLines = df.splitlines()
                for line in screenLines:
                    _, stdfont_line_height = PKImageTools.getsize_multiline(font=stdfont, srcText=line)
                    # Print the row separators
                    if not (line.startswith(column_separator)):
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            line,
                            font=stdfont,
                            fill=gridColor,
                        )
                        rowPixelRunValue += stdfont_line_height + 1
                    else: # if (line.startswith(column_separator)):
                        # Print the row contents
                        columnNumber = 0
                        valueScreenCols = line.split(column_separator)
                        try:
                            del valueScreenCols[0] # Remove the empty column header at the first position
                            del valueScreenCols[-1] # Remove the empty column header at the last position
                        except KeyboardInterrupt: # pragma: no cover
                            raise KeyboardInterrupt
                        except Exception as e:# pragma: no cover
                            default_logger().debug(e, exc_info=True)
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                line,
                                font=stdfont,
                                fill=gridColor,
                            )
                            lineNumber = lineNumber - 1
                            pass
                        # Print each colored value of each cell as we go over each row
                        for val in valueScreenCols:
                            if lineNumber >= len(unstyledLines):
                                continue
                            # Draw the column separator first
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                column_separator,
                                font=stdfont,
                                fill=gridColor,
                            )
                            colPixelRunValue = colPixelRunValue + stdfont_sep_width
                            unstyledLine = unstyledLines[lineNumber]
                            cellStyles, cellCleanValues = PKImageTools.getCellColors(
                                val, defaultCellFillColor=gridColor
                            )
                            valCounter = 0
                            for style in cellStyles:
                                cleanValue = cellCleanValues[valCounter]
                                valCounter += 1
                                if columnNumber == 0 and len(cleanValue.strip()) > 0:
                                    if column_separator in unstyledLine:
                                        cleanValue = unstyledLine.split(column_separator)[1]
                                    if "\\" in cleanValue:
                                        cleanValue = cleanValue.split("\\")[-1]
                                    # style = style if "%" in cleanValue else gridColor
                                if bgColor == "white" and style == "yellow":
                                    # Yellow on a white background is difficult to read
                                    style = "blue"
                                elif bgColor == "black" and style == "blue":
                                    # blue on a black background is difficult to read
                                    style = "yellow"
                                col_width, _ = PKImageTools.getsize_multiline(font=stdfont, srcText=cleanValue)
                                draw.text(
                                    (colPixelRunValue, rowPixelRunValue),
                                    cleanValue,
                                    font=stdfont,
                                    fill=style,
                                )
                                colPixelRunValue = colPixelRunValue + col_width
                                if columnNumber == 0:
                                    xVertical = int(columnNumber/2)

                            columnNumber = columnNumber + 1
                        if len(valueScreenCols) > 0:
                            # Close the row with the separator
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                column_separator,
                                font=stdfont,
                                fill=gridColor,
                            )
                            colPixelRunValue = startColValue
                        rowPixelRunValue +=  stdfont_line_height + 1
                    lineNumber = lineNumber + 1
                rowPixelRunValue += stdFont_oneLinelabel_height
            
            # Repo text
            draw.text(
                (colPixelRunValue, rowPixelRunValue + 1),
                repoText,
                font=artfont,
                fill=menuColor,
            )
            # Legend text
            rowPixelRunValue += 2 * stdFont_oneLinelabel_height + 20
            legendLines = legendText.splitlines()
            legendSeperator = "***"
            col_width_sep, _ = PKImageTools.getsize_multiline(font=artfont, srcText=legendSeperator)
            for line in legendLines:
                colPixelRunValue = startColValue
                _, artfont_line_height = PKImageTools.getsize_multiline(font=artfont, srcText=line)
                lineitems = line.split(legendSeperator)
                red = True
                for lineitem in lineitems:
                    if lineitem == "" or not red:
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            legendSeperator,
                            font=artfont,
                            fill=gridColor,
                        )
                        colPixelRunValue += col_width_sep + 1
                    style = "red" if not red else gridColor
                    red = not red
                    lineitem = lineitem.replace(": ","***: ")
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        lineitem,
                        font=artfont,
                        fill=style,
                    )
                    col_width, _ = PKImageTools.getsize_multiline(font=artfont, srcText=lineitem)
                    # Move to the next text in the same line
                    colPixelRunValue += col_width + 1
                    
                # Let's go to the next line
                rowPixelRunValue += artfont_line_height + 1

            im = im.resize((int(im.size[0]*PKImageTools.configManager.telegramImageCompressionRatio),int(im.size[1]*PKImageTools.configManager.telegramImageCompressionRatio)), Image.LANCZOS, reducing_gap=2)
            im = PKImageTools.addQuickWatermark(im,xVertical,dataSrc="Yahoo!finance; Morningstar, Inc; National Stock Exchange of India Ltd;TradingHours.com;",dataSrcFontSize=ART_FONT_SIZE)
            im.save(filename, format=PKImageTools.configManager.telegramImageFormat, bitmap_format=PKImageTools.configManager.telegramImageFormat, optimize=True, quality=int(PKImageTools.configManager.telegramImageQualityPercentage))
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
        # if 'RUNNER' not in os.environ.keys() and 'PKDevTools_Default_Log_Level' in os.environ.keys():
        # im.show()

    def wrapFitLegendText(table=None, backtestSummary=None, legendText=None):
        if legendText is None or len(legendText) < 1:
            return legendText
        wrapper = textwrap.TextWrapper(
            width=2
            * int(
                len(table.split("\n")[0])
                if (table is not None and len(table) > 0)
                else (len(backtestSummary.split("\n")[0]) if backtestSummary is not None else 80)
            )
        )
        if wrapper.width <= 0:
            return legendText
        word_list = wrapper.wrap(text=legendText)
        legendText_new = ""
        for ii in word_list[:-1]:
            legendText_new = legendText_new + ii + "\n"
        legendText_new += word_list[-1]
        legendText = legendText_new
        return legendText

    def getDefaultColors():
        artColors = ["blue", "indigo", "green", "red", "yellow","orange","violet"]
        bgColor = "white" if PKDateUtilities.currentDateTime().day % 2 == 0 else "black"
        gridColor = "black" if bgColor == "white" else "white"
        artColor = random.choice(artColors[3:]) if bgColor == "black" else random.choice(artColors[:3])
        menuColor = "red"
        return bgColor,gridColor,artColor,menuColor

    def setupReportFont():
        fontURL = "https://raw.githubusercontent.com/pkjmesra/pkscreener/main/pkscreener/courbd.ttf"
        fontFile = fontURL.split("/")[-1]
        bData, fontPath, _ = Archiver.findFile(fontFile)
        if bData is None:
            resp = PKImageTools.fetcher.fetchURL(fontURL, stream=True)
            if resp is not None:
                with open(fontPath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            else:
                path1 = os.path.join(Archiver.get_user_outputs_dir().replace("results","pkscreener"),"courbd.ttf")
                path2 = os.path.join(os.getcwd(),"courbd.ttf")
                if os.path.isfile(path1):
                    fontPath = path1
                elif os.path.isfile(path2):
                    fontPath = path2
                else:
                    if "Windows" in platform.system():
                        fontPath = "arial.ttf"
                    elif "Darwin" in platform.system():
                        fontPath = "/System/Library/Fonts/Keyboard.ttf"
                    else:
                        fontPath = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
        return fontPath

    def getLegendHelpText(table=None,backtestSummary=None):
        legendText = "\n***1.Stock***: This is the NSE symbol/ticker for a company. Stocks that are NOT stage two, are coloured red.***2.Consol.***: It shows the price range in which stock is trading for the last 22 trading sessions(22 trading sessions per month)***3.Breakout(22Prds)***: The BO is Breakout level based on last 22 sessions. R is the resistance level (if available)."
        legendText = f"{legendText} An investor should consider both BO & R level to analyse entry / exits in their trading lessons. If the BO value is green, it means the stock has already broken out (is above BO level). If BO is in red, it means the stock is yet to break out.***4.LTP***: This is the last/latest trading/closing price of the given stock on a given date at NSE. The LTP in green/red means the"
        legendText = f"{legendText} stock price has increased / decreased since last trading session. (1.5%, 1.3%,1.8%) with LTP shows the stock price rose by 1.5%, 1.3% and 1.8% in the last 1, 2 and 3 trading sessions respectively.***5.%Chng***: This is the change(rise/fall in percentage) in closing/trading price from the previous trading session's closing price. Green means that price rose from the previous"
        legendText = f"{legendText} trading session. Red means it fell.***6.volume***: This shows the relative volume in the most recent trading day /today with respect to last 20 trading periods moving average of Volume. For example, 8.5x would mean today's volume so far is 8.5 times the average volume traded in the last 20 trading sessions. Volume in green means that volume for the date so far has been at"
        legendText = f"{legendText} least 2.5 times more than the average volume of last 20 sessions. If the volume is in red, it means the given date's volume is less than 2.5 times the avg volume of the last 20 sessions.***7.MA-Signal***: It shows the price trend of the given stock by analyzing various 50-200 moving/exponential averages crossover strategies. Perform a Google search for the shown MA-Signals"
        legendText = f"{legendText} to learn about them more. If it is in green, the signal is bullish. Red means bearish.***8.RSI-or-RSI/i***: Relative Strength Index is a momentum index which describes 14-period relative strength at the given price. Generally, below 30 is considered oversold and above 80 is considered overbought. When RSI/i has value, say, 80/41, it means that the daily RSI value is 80 while"
        legendText = f"{legendText} the 1-minute intraday RSI is 41.***9.Trend(22Prds)***:  This describes the average trendline computed based on the last 22 trading sessions. Their strength is displayed depending on the steepness of the trendlines. (Strong / Weak) Up / Down shows how high/low the demand is respectively. A Sideways trend is the horizontal price movement that occurs when the forces of supply"
        legendText = f"{legendText} and demand are nearly equal. T:▲ or T:▼ shows the general moving average uptrend/downtrend from a 200 day MA perspective"
        legendText = f"{legendText} if the current 200DMA is more/less than the last 20/80/100 days' 200DMA. Similarly, t:▲ or t:▼ shows for 50DMA based on 9/14/20 days' 50DMA trend. MFI:▲ or MFI:▼ shows"
        legendText = f"{legendText} if the overall top 5 mutual funds and top 5 institutional investors ownership went up or down on the closing of the last month.***10.Pattern***:This shows if the chart or the candle (from the candlestick chart) is"
        legendText = f"{legendText} forming any known pattern in the recent timeframe or as per the selected screening options. Do a google search for the shown pattern names to learn.***11.CCI***: The Commodity Channel Index (CCI) is a technical indicator that measures the difference between the current price and the historical average price of the given stock. Generally below '- 100' is considered oversold"
        legendText = f"{legendText} and above 100 is considered overbought. If the CCI is < '-100' or CCI is > 100 and the Trend(22Prds) is Strong/Weak Up, it is shown in green. Otherwise it's in red.***12.1-Pd/2-Pd-etc.***: 60.29% of (413) under 1-Pd in green shows that the given scan option was correct 60.23% of the times for 413 stocks that scanner found in the last 22 trading sessions under the same scan"
        legendText = f"{legendText} options. Similarly, 61.69 % of (154) in green under 22-Pd, means we found that 61.56% of 154 stocks (~95 stocks) prices found under the same scan options increased in 22 trading periods. 57.87% of (2661) under 'Overall' means that over the last 22 trading sessions we found 2661 stock instances under the same scanning options (for example, Momentum Gainers), out of which 57.87%"
        legendText = f"{legendText} of the stock prices increased in one or more of the last 1 or 2 or 3 or 4 or 5 or 10 or 22 or 22 trading sessions. If you want to see by what percent the prices increased, you should see the details.***13.1-to-30-period-gain/loss%***: 4.17% under 1-Pd in green in the gain/loss table/grid means the stock price increased by 4.17% in the next 1 trading session. If this is in"
        legendText = f"{legendText} red, example, -5.67%, it means the price actually decreased by 5.67%. Gains are in green and losses are in red in this grid. The Date column has the date(s) on which that specific stock was found under the chosen scan options in the past 22 trading sessions.***14.52Wk-H/L***: These have 52 weeks high/low prices and will be shown in red, green or yellow based on how close the"
        legendText = f"{legendText} price is to the 52 wk high/low value.If the 52 week high/low value is within 10% of LTP:Yellow, LTP is above 52 week high:Green. If the LTP is below 90% of 52 week high:Red.***15.1-Pd-%***: Shows the 1 period gain in percent from the given date. Similarly 2-Pd-%, 3-Pd-% etc shows 2 day, 3 days gain etc.***16.1-Pd-10k***: Shows 1 period/day portfolio value if you would"
        legendText = f"{legendText} have invested 10,000 on the given date.***17.[T][_trend_]***: [T] is for Trends followed by the trend name in the filter.***18.[BO]***: This Shows the Breakout filter value from the backtest reports and will be available only if 'showpaststrategydata' configuration is turned on.***19.[P]***: [P] shows pattern name.***20.MFI***: Top 5 Mutual fund ownership and "
        legendText = f"{legendText} top 5 Institutional investor ownership status as on the last day of the last month, based on analysis from Morningstar.***21.FairValue***: Morningstar Fair value of a given stock as of last trading day as determined by 3rd party analysis based on fundamentals.***22.MCapWt%***: This shows the market-cap weighted portfolio weight to consider investing. "
        legendText = f"{legendText} ***23.Block/Bulk/Short Deals***: Ⓑ : Bulk Deals,Ⓛ: Block Deals,Ⓢ: Short deals. (B) indicates Buy, (S) indicates Sell. (1M) or (1K) indicates the quantity in million/kilo(thousand).\n"
        legendText = PKImageTools.wrapFitLegendText(table=table,backtestSummary=backtestSummary, legendText=legendText)
        # legendText = legendText.replace("***:", colorText.END + colorText.WHITE)
        # legendText = legendText.replace("***", colorText.END + colorText.FAIL)
        # return colorText.WHITE + legendText + colorText.END
        return legendText

    def getRepoHelpText(table,backtestSummary):
        repoText = f"Source: https://GitHub.com/pkjmesra/pkscreener/  | © {datetime.date.today().year} pkjmesra | Telegram: https://t.me/PKScreener |"
        disclaimer = f"The author is NOT a financial advisor and is NOT SEBI registered. This report is for learning/analysis purposes ONLY. Author assumes no responsibility or liability for any errors or omissions in this report or repository, or gain/loss bearing out of this analysis. The user MUST take advise ONLY from registered SEBI financial advisors only."
        repoText = f"{repoText}\n{PKImageTools.wrapFitLegendText(table,backtestSummary,disclaimer)}"
        repoText = f"{repoText}\n  [+] Understanding this report:\n\n"
        return repoText

    def roundOff(value,places):
        roundValue = value
        try:
            newValue = PKImageTools.removeAllColorStyles(str(roundValue))
            newValue = newValue.replace("%","").replace("x","")
            roundValue = round(float(newValue),places)
            if places == 0:
                roundValue = int(roundValue)
            roundValue = str(value).replace(str(newValue),str(roundValue))
        except: # pragma: no cover
            pass
        return roundValue
    
    def stockNameFromDecoratedName(stockName):
        if stockName is None:
            raise TypeError
        cleanName = PKImageTools.removeAllColorStyles(stockName.replace("\x1B]8;;",""))
        decoratedParts = cleanName.split("\x1B\\")
        if len(decoratedParts) > 1:
            cleanName = decoratedParts[1]
        return cleanName
