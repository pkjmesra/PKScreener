"""

Intraday Monitor dynamic Layout

"""
import multiprocessing
import sys

try:
    # Python 3.4+
    if sys.platform.startswith("win"):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    print("Contact developer! Your platform does not support multiprocessing!")
    input("Exiting now...")
    sys.exit(0)

from datetime import datetime
from time import sleep

import pytz
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.TaskHandler import taskHandler

configManagerLocal = ConfigManager.tools()
fetcherLocal = Fetcher.tools(configManagerLocal)

class Clock:
        """Renders the time at the top of the screen."""
        def __rich__(self) -> Text:
            ist = datetime.now(pytz.timezone('Asia/Kolkata'))
            return Text(f"PKScreener Intraday Monitor ({ist.ctime()} IST)", style="bold magenta", justify="center")
        
class intradayMonitor:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.counter = 0
        self.layout.split(
            Layout(name="header", size=1),
            Layout(ratio=1, name="main"),
            Layout(name="footer", size=1),
            )
        containerLayouts = ["header",
                            "left_top","left_bottom",
                            "middle_top","middle_bottom",
                            "right_top","right_bottom",
                            "footer"]

        self.layout["main"].split_row(Layout(name="left", ratio=1),
                                Layout(name="middle", ratio=1), 
                                Layout(name="right", ratio=1))

        self.layout["left"].split(Layout(name="left_top_main"), Layout(name="left_bottom_main"))
        self.layout["middle"].split(Layout(name="middle_top_main"), Layout(name="middle_bottom_main"))
        self.layout["right"].split(Layout(name="right_top_main"), Layout(name="right_bottom_main"))

        for layoutName in containerLayouts:
            if "_" in layoutName:
                self.layout[f"{layoutName}_main"].split(Layout(ratio=1, name=layoutName),Layout(name=f"{layoutName}_footer", size=1))
                self.layout[f"{layoutName}_footer"].update(
                    Panel(Align.center(Text("",justify="center",),vertical="middle",),
                            title="...",
                            border_style="blue",
                        ))
            self.layout[layoutName].update(
                Panel(
                        Align.center(
                            Text(
                                "PKScreener Monitor\nPlease wait...\nThe results will appear here as soon as we have them.",
                                justify="center",
                            ),
                            vertical="middle",
                        ),
                        title="Waiting for the next scan...",
                        border_style="blue",
                    )
            )
        self.layout["footer"].update(
                    Panel(Align.center(Text("",justify="center",),vertical="middle",),
                            title="...",
                            border_style="blue",
                        ))
        self.layout["footer"].update(Align.center(Text(f"{colorText.FAIL}Hit Ctrl+C to exit{colorText.END}",justify="center"),
                                            vertical="middle"))
        self.listStockCodes = []
        self.taskHandlers = []
        self.configManager = ConfigManager.tools()
        self.configManager.period = "280d"
        self.configManager.duration = "1d"
        self.configManager.cacheEnabled = True

    def monitor(self):
        self.listStockCodes = fetcherLocal.fetchStockCodes(12, stockCode=None)
        self.stockDict = multiprocessing.Manager().dict()
        Utility.tools.loadStockData(
                        self.stockDict,
                        self.configManager,
                        downloadOnly=False,
                        defaultAnswer='Y',
                )
        self.addTaskHandlers()
        self.layout["header"].update(Clock())
        with Live(self.layout,auto_refresh=True,screen=True,redirect_stderr=False,refresh_per_second=2):
            try:
                while True:
                    self.counter = 60
                    for th in self.taskHandlers:
                        th.tick()
                    while self.counter > 0:
                        self.counter -= 1
                        sleep(1)
            except KeyboardInterrupt:
                for th in self.taskHandlers:
                    th.keyboardInterruptEvent.set()
                    th.stop()
                pass
    
    def dataCallback(self,screenedResults,panelName,panelTitle):
        screenedResults.set_index("Stock", inplace=True)
        screenedResults.loc[:, "Volume"] = screenedResults.loc[:, "Volume"].apply(
            lambda x: Utility.tools.formatRatio(x, self.configManager.volumeRatio)
        )
        self.layout[panelName].update(Text(f'{tabulate(screenedResults,headers="keys", tablefmt="psql")}'))
        # self.layout[panelName].update(Panel(Text(f'{tabulate(screenedResults,headers="keys", tablefmt="psql")}',
        #                                          overflow="ellipsis",no_wrap=True,end=""),
        #                                          title=f"{colorText.GREEN}{panelTitle}{colorText.END}", border_style="blue",
        #                                          expand=False))

    def progressCallback(self,progressText,panelName):
        self.layout[f"{panelName}_footer"].update(Align.left(Text(f"{progressText}",justify="left"),
                                            vertical="top"))

    def addTaskHandlers(self):
        t1 = taskHandler(executeOption=11,siblingsCount=1,configManager=self.configManager,
                         stocks=self.listStockCodes,stockDict=self.stockDict,
                         containerName="left_top",containerTitle="5 min Volume breakout",
                         dataCallbackHandler=self.dataCallback,
                         progressCallbackHandler=self.progressCallback)
        self.taskHandlers.append(t1)
