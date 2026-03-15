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


class PKImageTools:
    """
    Utility class for image generation and manipulation.
    
    This class provides methods for:
    - Converting tabular data to images
    - Adding watermarks to images
    - Color/style management for console and image output
    - Text sizing and positioning utilities
    
    Attributes:
        fetcher: Instance of screenerStockDataFetcher for data retrieval
        configManager: Application configuration manager
    """
    
    fetcher = Fetcher.screenerStockDataFetcher()
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)
    
    # ========================================================================
    # Text Sizing Utilities
    # ========================================================================
    
    @staticmethod
    def getsize_multiline(font, srcText, x=0, y=0):
        """
        Calculate the size of multiline text when rendered with a specific font.
        
        Args:
            font: PIL ImageFont object
            srcText: The text to measure
            x: X offset for bounding box calculation (default: 0)
            y: Y offset for bounding box calculation (default: 0)
            
        Returns:
            tuple: (width, height) of the rendered text
        """
        zeroSizeImage = Image.new('RGB', (0, 0), (0, 0, 0))
        zeroDraw = ImageDraw.Draw(zeroSizeImage)
        bbox = zeroDraw.multiline_textbbox((x, y), srcText, font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    
    @staticmethod
    def getsize(font, srcText, x=0, y=0):
        """
        Calculate the size of single-line text when rendered with a specific font.
        
        Args:
            font: PIL ImageFont object
            srcText: The text to measure
            x: X offset (unused, kept for API consistency)
            y: Y offset (unused, kept for API consistency)
            
        Returns:
            tuple: (width, height) of the rendered text
        """
        left, top, bottom, right = font.getbbox(srcText)
        return right - left, bottom - top
    
    # ========================================================================
    # Watermark Methods
    # ========================================================================
    
    @staticmethod
    def addQuickWatermark(sourceImage: Image, xVertical=None, dataSrc="", dataSrcFontSize=10):
        """
        Add a watermark to an image with copyright text and optional data source.
        
        This method adds:
        - A diagonal watermark across the center of the image
        - A vertical watermark on the left side
        - A logo watermark (if available)
        - A data source attribution at the bottom right
        
        Args:
            sourceImage: PIL Image object to watermark
            xVertical: X position for vertical watermark (auto-calculated if None)
            dataSrc: Data source attribution text
            dataSrcFontSize: Font size for data source text
            
        Returns:
            PIL.Image: The watermarked image
        """
        width, height = sourceImage.size
        watermarkText = f"© {datetime.date.today().year} pkjmesra | PKScreener"
        message_length = len(watermarkText)
        
        # Font sizing constants
        FONT_RATIO = 1.5
        DIAGONAL_PERCENTAGE = .85
        DATASRC_FONTSIZE = dataSrcFontSize
        dataSrc = f"Src: {dataSrc}"
        
        # Calculate font sizes based on image dimensions
        diagonal_length = int(math.sqrt((width**2) + (height**2)))
        diagonal_to_use = diagonal_length * DIAGONAL_PERCENTAGE
        height_to_use = height * DIAGONAL_PERCENTAGE
        font_size = int(diagonal_to_use / (message_length / FONT_RATIO))
        font_size_vertical = int(height_to_use / (message_length / FONT_RATIO))
        
        # Load fonts
        fontPath = PKImageTools.setupReportFont()
        font = ImageFont.truetype(fontPath, font_size)
        font_vertical = ImageFont.truetype(fontPath, font_size_vertical)
        
        # Create diagonal watermark
        opacity = int(256 * .6)
        _, _, mark_width, mark_height = font.getbbox(watermarkText)
        watermark = Image.new('RGBA', (mark_width, mark_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        draw.text((0, 0), text=watermarkText, font=font, fill=(128, 128, 128, opacity))
        angle = math.degrees(math.atan(height / width))
        watermark_diag = watermark.rotate(angle, expand=1)
        
        # Create vertical watermark
        _, _, mark_width_ver, mark_height_ver = font_vertical.getbbox(watermarkText)
        watermark_ver = Image.new('RGBA', (mark_width_ver, mark_height_ver), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_ver)
        draw.text((0, 0), text=watermarkText, font=font_vertical, fill=(128, 128, 128, opacity))
        watermark_vertical = watermark_ver.rotate(90, expand=1)
        
        # Add logo watermark
        PKImageTools._addLogoWatermark(sourceImage, width, height)
        
        # Position and paste watermarks
        wx, wy = watermark_diag.size
        px = int((width - wx) / 2)
        py = int((height - wy) / 2)
        wxv, wyv = watermark_vertical.size
        pxv = int((width - wxv) / 12) if xVertical is None else xVertical
        pyv = int((height - wyv) / 2)
        sourceImage.paste(watermark_diag, (px, py, px + wx, py + wy), watermark_diag)
        sourceImage.paste(watermark_vertical, (pxv, pyv, pxv + wxv, pyv + wyv), watermark_vertical)
        
        # Add data source attribution
        dataSrcFont = ImageFont.truetype(fontPath, DATASRC_FONTSIZE)
        dataSrc_width, dataSrc_height = PKImageTools.getsize_multiline(font=dataSrcFont, srcText=dataSrc)
        draw = ImageDraw.Draw(sourceImage)
        draw.text(
            (width - dataSrc_width, height - dataSrc_height - 2),
            text=dataSrc, font=dataSrcFont, fill=(128, 128, 128, opacity)
        )
        
        return sourceImage
    
    @staticmethod
    def _addLogoWatermark(sourceImage, width, height):
        """
        Add logo watermark to the image.
        
        Args:
            sourceImage: PIL Image to add logo to
            width: Image width
            height: Image height
        """
        try:
            logo_wm_path = os.path.join(
                Archiver.get_user_outputs_dir().replace("results", "pkscreener"),
                "LogoWM.txt"
            )
            if not os.path.isfile(logo_wm_path):
                resp = Utility.tools.tryFetchFromServer(
                    cache_file="LogoWM.png",
                    directory="screenshots/logos",
                    hideOutput=True
                )
                with open(logo_wm_path, "wb") as f:
                    f.write(resp.content)
            logo_img = Image.open(logo_wm_path, formats=["PNG"]).convert('LA')
            lx, ly = logo_img.size
            plx = int((width - lx) / 4)
            ply = int((height - ly) / 3)
            sourceImage.paste(logo_img, (plx, ply), logo_img)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    # ========================================================================
    # Color Style Management
    # ========================================================================
    
    @staticmethod
    def removeAllColorStyles(styledText):
        """
        Remove all ANSI color codes from text or DataFrame.
        
        Args:
            styledText: Text string or pandas DataFrame with color codes
            
        Returns:
            The input with all color codes removed
        """
        styles = [
            colorText.HEAD, colorText.END, colorText.BOLD, colorText.UNDR,
            colorText.BLUE, colorText.GREEN, colorText.BRIGHTGREEN,
            colorText.WARN, colorText.BRIGHTYELLOW, colorText.FAIL,
            colorText.BRIGHTRED, colorText.WHITE,
        ]
        
        if isinstance(styledText, pd.DataFrame):
            styledTextCopy = styledText.copy()
            with pd.option_context('mode.chained_assignment', None):
                for col in styledTextCopy.columns:
                    for style in styles:
                        try:
                            styledTextCopy[col] = styledTextCopy[col].astype(str).str.replace(style, "")
                        except:
                            pass
            return styledTextCopy
        elif isinstance(styledText, str):
            cleanedUpStyledValue = str(styledText)
            for style in styles:
                cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
            return cleanedUpStyledValue
        else:
            return styledText
    
    @staticmethod
    def getCellColors(cellStyledValue="", defaultCellFillColor="black"):
        """
        Extract colors and clean values from styled cell text.
        
        Parses ANSI color codes in cell values and returns the corresponding
        color names and cleaned (un-styled) text values.
        
        Args:
            cellStyledValue: Cell value potentially containing color codes
            defaultCellFillColor: Default color if no style codes found
            
        Returns:
            tuple: (list of color names, list of cleaned text values)
        """
        otherStyles = [colorText.HEAD, colorText.BOLD, colorText.UNDR]
        mainStyles = [
            colorText.BLUE, colorText.GREEN, colorText.BRIGHTGREEN,
            colorText.WARN, colorText.BRIGHTYELLOW, colorText.FAIL,
            colorText.BRIGHTRED, colorText.WHITE,
        ]
        
        # Color mapping based on background color
        colorsDict = {
            colorText.BLUE: "blue",
            colorText.BRIGHTGREEN: "darkgreen",
            colorText.GREEN: "green" if defaultCellFillColor == "black" else "lightgreen",
            colorText.WARN: "darkorange" if defaultCellFillColor == "black" else "yellow",
            colorText.BRIGHTYELLOW: "darkyellow",
            colorText.FAIL: "red",
            colorText.BRIGHTRED: "darkred",
            colorText.WHITE: "white" if defaultCellFillColor == "white" else "black",
        }
        
        cleanedUpStyledValues = []
        cellFillColors = []
        cleanedUpStyledValue = str(cellStyledValue)
        prefix = ""
        
        # Remove non-color styles first
        for style in otherStyles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
        
        # Split by color end markers and process each segment
        coloredStyledValues = cleanedUpStyledValue.split(colorText.END)
        for cleanedUpStyledValue in coloredStyledValues:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(colorText.END, "")
            if cleanedUpStyledValue.strip() in ["", ",", "/"]:
                if len(cleanedUpStyledValues) > 0:
                    cleanedUpStyledValues[-1] = f"{cleanedUpStyledValues[-1]}{cleanedUpStyledValue}"
                else:
                    prefix = cleanedUpStyledValue
            else:
                for style in mainStyles:
                    if style in cleanedUpStyledValue:
                        cellFillColors.append(colorsDict[style])
                        for s in mainStyles:
                            cleanedUpStyledValue = cleanedUpStyledValue.replace(s, "")
                        cleanedUpStyledValues.append(prefix + cleanedUpStyledValue)
                        prefix = ""
        
        # Use defaults if no colors found
        if len(cellFillColors) == 0:
            cellFillColors = [defaultCellFillColor]
        if len(cleanedUpStyledValues) == 0:
            cleanedUpStyledValues = [str(cellStyledValue)]
            
        return cellFillColors, cleanedUpStyledValues
    
    # ========================================================================
    # Table to Image Conversion
    # ========================================================================
    
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
        summaryLabel=None,
        detailLabel=None,
        legendPrefixText=""
    ):
        """
        Convert tabular data to an image with styling and legends.
        
        Creates a comprehensive report image containing:
        - Application art/header
        - Main results table
        - Backtest summary (if provided)
        - Backtest detail (if provided)
        - Addendum information (if provided)
        - Help text and legend
        - Watermarks
        
        Args:
            table: Plain text table content
            styledTable: Color-styled table content
            filename: Output filename for the image
            label: Report label/title
            backtestSummary: Optional backtest summary table
            backtestDetail: Optional backtest detail table
            addendum: Optional additional information
            addendumLabel: Label for addendum section
            summaryLabel: Custom label for summary section
            detailLabel: Custom label for detail section
            legendPrefixText: Text to prepend to legend
        """
        # Skip in certain running modes
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if "RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER":
                return
                
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        ART_FONT_SIZE = 30
        STD_FONT_SIZE = 60
        
        try:
            fontPath = PKImageTools.setupReportFont()
            artfont = ImageFont.truetype(fontPath, ART_FONT_SIZE)
            stdfont = ImageFont.truetype(fontPath, STD_FONT_SIZE)
            
            bgColor, gridColor, artColor, menuColor = PKImageTools.getDefaultColors()
            
            # Calculate image dimensions
            dimensions = PKImageTools._calculateImageDimensions(
                table, styledTable, label, backtestSummary, backtestDetail,
                addendum, artfont, stdfont
            )
            
            # Create the image
            im = Image.new("RGB", (dimensions['width'], dimensions['height']), bgColor)
            draw = ImageDraw.Draw(im)
            
            # Render content
            PKImageTools._renderImageContent(
                im, draw, table, styledTable, label, backtestSummary, backtestDetail,
                addendum, addendumLabel, summaryLabel, detailLabel, legendPrefixText,
                artfont, stdfont, dimensions, bgColor, gridColor, artColor, menuColor
            )
            
            # Apply compression, watermark, and save
            im = im.resize(
                (
                    int(im.size[0] * PKImageTools.configManager.telegramImageCompressionRatio),
                    int(im.size[1] * PKImageTools.configManager.telegramImageCompressionRatio)
                ),
                Image.LANCZOS, reducing_gap=2
            )
            im = PKImageTools.addQuickWatermark(
                im, dimensions.get('xVertical', None),
                dataSrc="Yahoo!finance; Morningstar, Inc; National Stock Exchange of India Ltd;TradingHours.com;",
                dataSrcFontSize=ART_FONT_SIZE
            )
            im.save(
                filename,
                format=PKImageTools.configManager.telegramImageFormat,
                bitmap_format=PKImageTools.configManager.telegramImageFormat,
                optimize=True,
                quality=int(PKImageTools.configManager.telegramImageQualityPercentage)
            )
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    @staticmethod
    def _calculateImageDimensions(table, styledTable, label, backtestSummary, 
                                   backtestDetail, addendum, artfont, stdfont):
        """Calculate required image dimensions based on content."""
        startColValue = 100
        
        # Get text dimensions
        arttext_width, arttext_height = PKImageTools.getsize_multiline(
            font=artfont, srcText=artText + f"{marketStatus()}"
        )
        label_width, label_height = PKImageTools.getsize_multiline(font=stdfont, srcText=label)
        table_width, table_height = PKImageTools.getsize_multiline(
            font=stdfont, srcText=table
        ) if len(table) > 0 else (0, 0)
        
        unstyled_summary = PKImageTools.removeAllColorStyles(backtestSummary)
        unstyled_detail = PKImageTools.removeAllColorStyles(backtestDetail)
        
        summary_width, summary_height = PKImageTools.getsize_multiline(
            font=stdfont, srcText=unstyled_summary
        ) if (unstyled_summary is not None and len(unstyled_summary) > 0) else (0, 0)
        
        detail_width, detail_height = PKImageTools.getsize_multiline(
            font=stdfont, srcText=unstyled_detail
        ) if (unstyled_detail is not None and len(unstyled_detail) > 0) else (0, 0)
        
        addendum_width, addendum_height = 0, 0
        if addendum is not None and len(addendum) > 0:
            unstyled_addendum = PKImageTools.removeAllColorStyles(addendum)
            addendum_width, addendum_height = PKImageTools.getsize_multiline(
                font=stdfont, srcText=unstyled_addendum
            )
        
        repoText = PKImageTools.getRepoHelpText(table, backtestSummary)
        repo_width, repo_height = PKImageTools.getsize_multiline(font=artfont, srcText=repoText)
        
        legendText = PKImageTools.getLegendHelpText(table, backtestSummary)
        _, legend_height = PKImageTools.getsize_multiline(font=artfont, srcText=legendText)
        
        # Calculate final dimensions
        im_width = max(
            arttext_width, label_width, table_width, summary_width,
            detail_width, repo_width, addendum_width
        ) + int(startColValue * 2)
        
        im_height = int(
            arttext_height +
            3 * label_height +
            table_height + (label_height if table_height > 0 else 0) +
            summary_height + (label_height if summary_height > 0 else 0) +
            detail_height + (label_height if detail_height > 0 else 0) +
            repo_height + legend_height +
            addendum_height + (label_height if addendum_height > 0 else 0)
        )
        
        return {
            'width': im_width,
            'height': im_height,
            'startColValue': startColValue,
            'xVertical': startColValue,
            'arttext_height': arttext_height,
            'label_height': label_height,
        }
    
    @staticmethod
    def _renderImageContent(im, draw, table, styledTable, label, backtestSummary,
                            backtestDetail, addendum, addendumLabel, summaryLabel,
                            detailLabel, legendPrefixText, artfont, stdfont,
                            dimensions, bgColor, gridColor, artColor, menuColor):
        """Render all content onto the image."""
        startColValue = dimensions['startColValue']
        rowPixelRunValue = 9
        
        # Draw artwork header
        draw.text(
            (startColValue, rowPixelRunValue),
            artText + f"{PKImageTools.removeAllColorStyles(marketStatus())}",
            font=artfont, fill=artColor
        )
        rowPixelRunValue += dimensions['arttext_height'] + 1
        
        # Draw report title
        reportTitle = f"  [+] As of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H.%M.%S')} IST > You chose {label}"
        draw.text((startColValue, rowPixelRunValue), reportTitle, font=stdfont, fill=menuColor)
        rowPixelRunValue += dimensions['label_height'] + 1
        
        # Prepare data frames and labels for rendering
        dfs_to_print = [styledTable, backtestSummary, backtestDetail]
        unstyled_dfs = [table, backtestSummary, backtestDetail]
        titleLabels = [
            f"  [+] Scan results for {label} :",
            summaryLabel or "  [+] For chosen scan, summary of correctness from past:",
            detailLabel or "  [+] 1 to 30 period gain/loss % for matching stocks:",
        ]
        
        if addendum is not None and len(addendum) > 0:
            titleLabels.append(addendumLabel)
            dfs_to_print.append(addendum)
            unstyled_dfs.append(PKImageTools.removeAllColorStyles(addendum))
        
        # Render each data section
        column_separator = "|"
        stdfont_sep_width, _ = PKImageTools.getsize_multiline(font=stdfont, srcText=column_separator)
        
        for counter, df in enumerate(dfs_to_print):
            if df is None or len(df) == 0:
                continue
                
            colPixelRunValue = startColValue
            draw.text(
                (colPixelRunValue, rowPixelRunValue),
                titleLabels[counter], font=stdfont, fill=menuColor
            )
            rowPixelRunValue += dimensions['label_height']
            
            # Render table rows
            rowPixelRunValue = PKImageTools._renderTableRows(
                draw, df, unstyled_dfs[counter], stdfont, startColValue,
                rowPixelRunValue, column_separator, stdfont_sep_width,
                bgColor, gridColor, dimensions
            )
            rowPixelRunValue += dimensions['label_height']
        
        # Draw repo and legend text
        repoText = PKImageTools.getRepoHelpText(table, backtestSummary)
        draw.text((startColValue, rowPixelRunValue + 1), repoText, font=artfont, fill=menuColor)
        rowPixelRunValue += 2 * dimensions['label_height'] + 20
        
        legendText = legendPrefixText + PKImageTools.getLegendHelpText(table, backtestSummary)
        PKImageTools._renderLegend(draw, legendText, artfont, startColValue, rowPixelRunValue, gridColor)
    
    @staticmethod
    def _renderTableRows(draw, df, unstyled_df, stdfont, startColValue, 
                          rowPixelRunValue, column_separator, sep_width,
                          bgColor, gridColor, dimensions):
        """Render table rows with proper styling."""
        unstyledLines = unstyled_df.splitlines() if isinstance(unstyled_df, str) else []
        screenLines = df.splitlines() if isinstance(df, str) else []
        
        for lineNumber, line in enumerate(screenLines):
            _, line_height = PKImageTools.getsize_multiline(font=stdfont, srcText=line)
            colPixelRunValue = startColValue
            
            if not line.startswith(column_separator):
                draw.text(
                    (colPixelRunValue, rowPixelRunValue),
                    line, font=stdfont, fill=gridColor
                )
            else:
                # Process colored cell values
                valueScreenCols = line.split(column_separator)
                try:
                    del valueScreenCols[0]
                    del valueScreenCols[-1]
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        line, font=stdfont, fill=gridColor
                    )
                
                for columnNumber, val in enumerate(valueScreenCols):
                    if lineNumber >= len(unstyledLines):
                        continue
                        
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        column_separator, font=stdfont, fill=gridColor
                    )
                    colPixelRunValue += sep_width
                    
                    cellStyles, cellCleanValues = PKImageTools.getCellColors(
                        val, defaultCellFillColor=gridColor
                    )
                    
                    for valCounter, style in enumerate(cellStyles):
                        cleanValue = cellCleanValues[valCounter]
                        if bgColor == "white" and style == "yellow":
                            style = "blue"
                        elif bgColor == "black" and style == "blue":
                            style = "yellow"
                            
                        col_width, _ = PKImageTools.getsize_multiline(font=stdfont, srcText=cleanValue)
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            cleanValue, font=stdfont, fill=style
                        )
                        colPixelRunValue += col_width
                
                if len(valueScreenCols) > 0:
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        column_separator, font=stdfont, fill=gridColor
                    )
            
            rowPixelRunValue += line_height + 1
        
        return rowPixelRunValue
    
    @staticmethod
    def _renderLegend(draw, legendText, artfont, startColValue, rowPixelRunValue, gridColor):
        """Render the legend section with styled text."""
        legendLines = legendText.splitlines()
        legendSeperator = "***"
        col_width_sep, _ = PKImageTools.getsize_multiline(font=artfont, srcText=legendSeperator)
        
        for line in legendLines:
            colPixelRunValue = startColValue
            _, line_height = PKImageTools.getsize_multiline(font=artfont, srcText=line)
            lineitems = line.split(legendSeperator)
            red = True
            
            for lineitem in lineitems:
                if lineitem == "" or not red:
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        legendSeperator, font=artfont, fill=gridColor
                    )
                    colPixelRunValue += col_width_sep + 1
                    
                style = "red" if not red else gridColor
                red = not red
                lineitem = lineitem.replace(": ", "***: ")
                draw.text(
                    (colPixelRunValue, rowPixelRunValue),
                    lineitem, font=artfont, fill=style
                )
                col_width, _ = PKImageTools.getsize_multiline(font=artfont, srcText=lineitem)
                colPixelRunValue += col_width + 1
            
            rowPixelRunValue += line_height + 1
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    @staticmethod
    def wrapFitLegendText(table=None, backtestSummary=None, legendText=None):
        """
        Wrap legend text to fit within table width.
        
        Args:
            table: Table text for width reference
            backtestSummary: Alternative width reference
            legendText: Text to wrap
            
        Returns:
            str: Wrapped text
        """
        if legendText is None or len(legendText) < 1:
            return legendText
            
        width = 2 * int(
            len(table.split("\n")[0]) if (table is not None and len(table) > 0)
            else (len(backtestSummary.split("\n")[0]) if backtestSummary is not None else 80)
        )
        
        if width <= 0:
            return legendText
            
        wrapper = textwrap.TextWrapper(width=width)
        word_list = wrapper.wrap(text=legendText)
        return "\n".join(word_list)
    
    @staticmethod
    def getDefaultColors():
        """
        Get default color scheme for image generation.
        
        The color scheme alternates between light and dark based on the current day.
        
        Returns:
            tuple: (bgColor, gridColor, artColor, menuColor)
        """
        artColors = ["blue", "indigo", "green", "red", "yellow", "orange", "violet"]
        bgColor = "white" if PKDateUtilities.currentDateTime().day % 2 == 0 else "black"
        gridColor = "black" if bgColor == "white" else "white"
        artColor = random.choice(artColors[3:]) if bgColor == "black" else random.choice(artColors[:3])
        menuColor = "red"
        return bgColor, gridColor, artColor, menuColor
    
    @staticmethod
    def setupReportFont():
        """
        Set up the font file for report generation.
        
        Downloads the font if not available locally, falls back to system fonts.
        
        Returns:
            str: Path to the font file
        """
        fontURL = "https://raw.githubusercontent.com/pkjmesra/pkscreener/main/pkscreener/courbd.ttf"
        fontFile = fontURL.split("/")[-1]
        bData, fontPath, _ = Archiver.findFile(fontFile)
        
        if bData is None:
            resp = PKImageTools.fetcher.fetchURL(fontURL, stream=True)
            if resp is not None:
                with open(fontPath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
            else:
                fontPath = PKImageTools._getFallbackFontPath()
        return fontPath
    
    @staticmethod
    def _getFallbackFontPath():
        """Get platform-specific fallback font path."""
        path1 = os.path.join(
            Archiver.get_user_outputs_dir().replace("results", "pkscreener"),
            "courbd.ttf"
        )
        path2 = os.path.join(os.getcwd(), "courbd.ttf")
        
        if os.path.isfile(path1):
            return path1
        elif os.path.isfile(path2):
            return path2
        elif "Windows" in platform.system():
            return "arial.ttf"
        elif "Darwin" in platform.system():
            return "/System/Library/Fonts/Keyboard.ttf"
        else:
            return "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
    
    @staticmethod
    def getLegendHelpText(table=None, backtestSummary=None):
        """
        Get the comprehensive legend/help text for reports.
        
        Returns:
            str: Formatted legend text explaining all report fields
        """
        legendText = (
            "\n***1.Stock***: This is the NSE symbol/ticker for a company. "
            "Stocks that are NOT stage two, are coloured red."
            "***2.Consol.***: It shows the price range in which stock is trading "
            "for the last 22 trading sessions(22 trading sessions per month)"
            "***3.Breakout(22Prds)***: The BO is Breakout level based on last 22 sessions. "
            "R is the resistance level (if available)."
        )
        legendText += (
            " An investor should consider both BO & R level to analyse entry / exits "
            "in their trading lessons. If the BO value is green, it means the stock "
            "has already broken out (is above BO level). If BO is in red, it means "
            "the stock is yet to break out."
            "***4.LTP***: This is the last/latest trading/closing price of the given "
            "stock on a given date at NSE. The LTP in green/red means the stock price "
            "has increased / decreased since last trading session. (1.5%, 1.3%,1.8%) "
            "with LTP shows the stock price rose by 1.5%, 1.3% and 1.8% in the last "
            "1, 2 and 3 trading sessions respectively."
            "***5.%Chng***: This is the change(rise/fall in percentage) in closing/trading "
            "price from the previous trading session's closing price. Green means that "
            "price rose from the previous trading session. Red means it fell."
        )
        legendText += (
            "***6.volume***: This shows the relative volume in the most recent trading "
            "day /today with respect to last 20 trading periods moving average of Volume. "
            "For example, 8.5x would mean today's volume so far is 8.5 times the average "
            "volume traded in the last 20 trading sessions. Volume in green means that "
            "volume for the date so far has been at least 2.5 times more than the average "
            "volume of last 20 sessions. If the volume is in red, it means the given date's "
            "volume is less than 2.5 times the avg volume of the last 20 sessions."
            "***7.MA-Signal***: It shows the price trend of the given stock by analyzing "
            "various 50-200 moving/exponential averages crossover strategies. Perform a "
            "Google search for the shown MA-Signals to learn about them more. If it is "
            "in green, the signal is bullish. Red means bearish."
        )
        legendText += (
            "***8.RSI-or-RSI/i***: Relative Strength Index is a momentum index which "
            "describes 14-period relative strength at the given price. Generally, below "
            "30 is considered oversold and above 80 is considered overbought. When RSI/i "
            "has value, say, 80/41, it means that the daily RSI value is 80 while the "
            "1-minute intraday RSI is 41."
            "***9.Trend(22Prds)***: This describes the average trendline computed based "
            "on the last 22 trading sessions. Their strength is displayed depending on "
            "the steepness of the trendlines. (Strong / Weak) Up / Down shows how high/low "
            "the demand is respectively. A Sideways trend is the horizontal price movement "
            "that occurs when the forces of supply and demand are nearly equal. "
            "T:▲ or T:▼ shows the general moving average uptrend/downtrend from a 200 day "
            "MA perspective if the current 200DMA is more/less than the last 20/80/100 days' "
            "200DMA. Similarly, t:▲ or t:▼ shows for 50DMA based on 9/14/20 days' 50DMA trend. "
            "MFI:▲ or MFI:▼ shows if the overall top 5 mutual funds and top 5 institutional "
            "investors ownership went up or down on the closing of the last month."
        )
        legendText += (
            "***10.Pattern***: This shows if the chart or the candle (from the candlestick "
            "chart) is forming any known pattern in the recent timeframe or as per the "
            "selected screening options. Do a google search for the shown pattern names to learn."
            "***11.CCI***: The Commodity Channel Index (CCI) is a technical indicator that "
            "measures the difference between the current price and the historical average "
            "price of the given stock. Generally below '- 100' is considered oversold and "
            "above 100 is considered overbought. If the CCI is < '-100' or CCI is > 100 and "
            "the Trend(22Prds) is Strong/Weak Up, it is shown in green. Otherwise it's in red."
        )
        legendText += (
            "***12.1-Pd/2-Pd-etc.***: 60.29% of (413) under 1-Pd in green shows that the "
            "given scan option was correct 60.23% of the times for 413 stocks that scanner "
            "found in the last 22 trading sessions under the same scan options. Similarly, "
            "61.69 % of (154) in green under 22-Pd, means we found that 61.56% of 154 stocks "
            "(~95 stocks) prices found under the same scan options increased in 22 trading periods."
            "***13.1-to-30-period-gain/loss%***: 4.17% under 1-Pd in green in the gain/loss "
            "table/grid means the stock price increased by 4.17% in the next 1 trading session. "
            "If this is in red, example, -5.67%, it means the price actually decreased by 5.67%. "
            "Gains are in green and losses are in red in this grid."
        )
        legendText += (
            "***14.52Wk-H/L***: These have 52 weeks high/low prices and will be shown in red, "
            "green or yellow based on how close the price is to the 52 wk high/low value."
            "***15.1-Pd-%***: Shows the 1 period gain in percent from the given date. "
            "Similarly 2-Pd-%, 3-Pd-% etc shows 2 day, 3 days gain etc."
            "***16.1-Pd-10k***: Shows 1 period/day portfolio value if you would have invested "
            "10,000 on the given date."
            "***17.[T][_trend_]***: [T] is for Trends followed by the trend name in the filter."
            "***18.[BO]***: This Shows the Breakout filter value from the backtest reports."
            "***19.[P]***: [P] shows pattern name."
            "***20.MFI***: Top 5 Mutual fund ownership and top 5 Institutional investor ownership "
            "status as on the last day of the last month, based on analysis from Morningstar."
            "***21.FairValue***: Morningstar Fair value of a given stock as of last trading day."
            "***22.MCapWt%***: This shows the market-cap weighted portfolio weight to consider investing."
            "***23.Block/Bulk/Short Deals***: Ⓑ : Bulk Deals, Ⓛ: Block Deals, Ⓢ: Short deals. "
            "(B) indicates Buy, (S) indicates Sell. (1M) or (1K) indicates the quantity.\n"
        )
        return PKImageTools.wrapFitLegendText(table=table, backtestSummary=backtestSummary, legendText=legendText)
    
    @staticmethod
    def getRepoHelpText(table, backtestSummary):
        """
        Get repository help text with copyright and disclaimer.
        
        Returns:
            str: Formatted help text
        """
        repoText = (
            f"Source: https://GitHub.com/pkjmesra/pkscreener/  | "
            f"© {datetime.date.today().year} pkjmesra | "
            f"Telegram: https://t.me/PKScreener |"
        )
        disclaimer = (
            "The author is NOT a financial advisor and is NOT SEBI registered. "
            "This report is for learning/analysis purposes ONLY. Author assumes "
            "no responsibility or liability for any errors or omissions in this "
            "report or repository, or gain/loss bearing out of this analysis. "
            "The user MUST take advise ONLY from registered SEBI financial advisors only."
        )
        repoText = f"{repoText}\n{PKImageTools.wrapFitLegendText(table, backtestSummary, disclaimer)}"
        repoText = f"{repoText}\n  [+] Understanding this report:\n\n"
        return repoText
    
    # ========================================================================
    # Value Formatting Methods
    # ========================================================================
    
    @staticmethod
    def roundOff(value, places):
        """
        Round a numeric value while preserving color codes.
        
        Args:
            value: Value to round (may contain color codes)
            places: Number of decimal places
            
        Returns:
            Rounded value with preserved color codes
        """
        roundValue = value
        try:
            newValue = PKImageTools.removeAllColorStyles(str(roundValue))
            newValue = newValue.replace("%", "").replace("x", "")
            roundValue = round(float(newValue), places)
            if places == 0:
                roundValue = int(roundValue)
            roundValue = str(value).replace(str(newValue), str(roundValue))
        except:
            pass
        return roundValue
    
    @staticmethod
    def stockNameFromDecoratedName(stockName):
        """
        Extract plain stock name from a hyperlink-decorated name.
        
        Args:
            stockName: Decorated stock name (may contain hyperlink escape sequences)
            
        Returns:
            str: Plain stock name
            
        Raises:
            TypeError: If stockName is None
        """
        if stockName is None:
            raise TypeError
        cleanName = PKImageTools.removeAllColorStyles(stockName.replace("\x1B]8;;", ""))
        decoratedParts = cleanName.split("\x1B\\")
        if len(decoratedParts) > 1:
            cleanName = decoratedParts[1]
        return cleanName
