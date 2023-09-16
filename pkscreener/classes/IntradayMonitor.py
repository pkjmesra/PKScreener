"""

Intraday Monitor dynamic Layout

"""

from datetime import datetime
import pytz

from time import sleep

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

console = Console()
layout = Layout()

layout.split(
    Layout(name="header", size=1),
    Layout(ratio=1, name="main"),
    Layout(name="footer", size=1),
    )
containerLayouts = ["header",
                    "left_top","left_bottom",
                    "middle_top","middle_bottom",
                    "right_top","right_bottom",
                    "footer"]

layout["main"].split_row(Layout(name="left", ratio=1), 
                         Layout(name="middle", ratio=1), 
                         Layout(name="right", ratio=1))

layout["left"].split(Layout(name="left_top"), Layout(name="left_bottom"))
layout["middle"].split(Layout(name="middle_top"), Layout(name="middle_bottom"))
layout["right"].split(Layout(name="right_top"), Layout(name="right_bottom"))

for layoutName in containerLayouts:
    layout[layoutName].update(
        Panel(
                Align.center(
                    Text(
                        "PKScreener Monitor",
                        justify="center",
                    ),
                    vertical="middle",
                ),
                title=layoutName,
                border_style="blue",
            )
    )
layout["footer"].update(Align.center(Text("Hit Ctrl+C to exit",justify="center"),
                                     vertical="middle"))


class Clock:
    """Renders the time at the top of the screen."""
    def __rich__(self) -> Text:
        ist = datetime.now(pytz.timezone('Asia/Kolkata'))
        return Text(f"PKScreener Intraday Monitor ({ist.ctime()} IST)", style="bold magenta", justify="center")

layout["header"].update(Clock())

with Live(layout, screen=True, redirect_stderr=False) as live:
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass
