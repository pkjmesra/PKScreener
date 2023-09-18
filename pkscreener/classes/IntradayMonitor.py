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

from multiprocessing import Process
from datetime import datetime
from time import sleep

import pytz
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger
from pkscreener.classes.TaskHandler import taskHandler
from pkscreener.classes.PKMultiProcessorClient import PKMultiProcessorClient

configManagerLocal = ConfigManager.tools()
fetcherLocal = Fetcher.tools(configManagerLocal)

class Clock:
    """Renders the time at the top of the screen."""
    def __rich__(self) -> Text:
        ist = datetime.now(pytz.timezone('Asia/Kolkata'))
        return Text(f"PKScreener Intraday Monitor ({ist.ctime()} IST)", style="bold magenta", justify="center")

class ProgressFooter:
    def __init__(self,progressText,panelName):
        self.progressText = progressText
        self.panelName = panelName

    def progressCallback(self,progressText,panelName):
        self.progressText = progressText

    """Renders the time at the top of the screen."""
    def __rich__(self) -> Align:
        return Align.left(Text(f"{self.progressText}",justify="left"),vertical="top")

class DataPanelUpdater:
    def __init__(self,screenedResults,panelName,panelTitle):
        self.screenedResults = screenedResults
        self.panelTitle = panelTitle
        self.panelName = panelName

    def dataCallback(self,screenedResults,panelName,panelTitle):
        self.screenedResults = screenedResults

    """Renders the time at the top of the screen."""
    def __rich__(self) -> Panel:
        if self.screenedResults is None or len(self.screenedResults) == 0:
            return Panel("",title=f"{colorText.GREEN}{self.panelTitle}{colorText.END}", border_style="blue",
                                                 expand=False)
        self.screenedResults.set_index("Stock", inplace=True)
        self.screenedResults.loc[:, "Volume"] = self.screenedResults.loc[:, "Volume"].apply(
            lambda x: Utility.tools.formatRatio(x, self.configManager.volumeRatio)
        )
        # self.layout[panelName].update(f'{self.console.print(tabulate(screenedResults,headers="keys", tablefmt="psql"))}')
        return Panel(f'{tabulate(self.screenedResults,headers="keys", tablefmt="psql")}',
                                                #  overflow="ellipsis",no_wrap=True,end=""),
                                                 title=f"{colorText.GREEN}{self.panelTitle}{colorText.END}", border_style="blue",
                                                 expand=False)
    
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
        self.table = None
        self.keyboardInterruptEvent = None

    def monitor(self):
        self.listStockCodes = fetcherLocal.fetchStockCodes(12, stockCode=None)
        self.stockDict = multiprocessing.Manager().dict()
        Utility.tools.loadStockData(
                        self.stockDict,
                        self.configManager,
                        downloadOnly=False,
                        defaultAnswer='Y',
                )
        self.keyboardInterruptEvent = multiprocessing.Manager().Event()
        self.addTaskHandlers()
        self.layout["header"].update(Clock())
        with Live(self.layout,auto_refresh=True,screen=True,redirect_stderr=False,refresh_per_second=2):
            try:
                while True:
                    self.counter = 60
                    for th in self.taskHandlers:
                        th["value"].task_queue.put(th["key"].handlerTickParams())
                    while self.counter > 0:
                        self.counter -= 1
                        sleep(1)
            except KeyboardInterrupt:
                for th in self.taskHandlers:
                    th["value"].task_queue.put(None)
                    th["value"].keyboardInterruptEvent.set()
                    th["value"].terminate()
                pass
    
    # def dataCallback(self,screenedResults,panelName,panelTitle):
    #     # keys = ["Stock","%Chng","Volume","LTP"]
    #     # for key in screenedResults.keys():
    #     #     if key in keys:
    #     #         self.table.add_row(screenedResults["Stock"],
    #     #                            screenedResults["%Chng"],
    #     #                            f'{screenedResults["Volume"]}x',
    #     #                            str(screenedResults["LTP"]))
    #     # self.layout[panelName].update(self.table)
    #     screenedResults.set_index("Stock", inplace=True)
    #     screenedResults.loc[:, "Volume"] = screenedResults.loc[:, "Volume"].apply(
    #         lambda x: Utility.tools.formatRatio(x, self.configManager.volumeRatio)
    #     )
    #     # self.layout[panelName].update(f'{self.console.print(tabulate(screenedResults,headers="keys", tablefmt="psql"))}')
    #     self.layout[panelName].update(Panel(f'{tabulate(screenedResults,headers="keys", tablefmt="psql")}',
    #                                             #  overflow="ellipsis",no_wrap=True,end=""),
    #                                              title=f"{colorText.GREEN}{panelTitle}{colorText.END}", border_style="blue",
    #                                              expand=False))


    def addTaskHandlers(self):
        containerLayouts = ["left_top","left_bottom",
                            "middle_top","middle_bottom",
                            "right_top","right_bottom"]
        containerWidgets = ["5 min Volume breakout","left_bottom Widget",
                    "middle_top Widget","middle_bottom Widget",
                    "right_top Widget","right_bottom Widget"]
        itemCounter = 0
        for item in containerLayouts:
            t1,p1 = self.getNewTask(containerLayouts[itemCounter],containerWidgets[itemCounter])
            itemCounter += 1
            self.taskHandlers.append({"key":t1,"value":p1})

    def getNewTask(self, layoutName, widgetName):
        stocks = self.listStockCodes
        pf1 = ProgressFooter("", f"{layoutName}_footer")
        self.layout[f"{layoutName}_footer"].update(pf1)
        pd1 = DataPanelUpdater(None,layoutName,widgetName)
        self.layout[layoutName].update(pd1)
        t1 = taskHandler(executeOption=11,siblingsCount=2,configManager=self.configManager,
                        containerName=layoutName,containerTitle=widgetName)
        tasks_queue = multiprocessing.JoinableQueue()
        p1 = PKMultiProcessorClient(
                t1.tick,
                tasks_queue,
                None,
                None,
                None,
                self.stockDict,
                None,
                self.keyboardInterruptEvent,
                default_logger(),
                stocks,
                pd1.dataCallback,
                pf1.progressCallback
            )
        p1.daemon = False
        p1.start()
        return t1, p1
    
intradayMonitorInstance = intradayMonitor()