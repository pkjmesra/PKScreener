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
import warnings
import os
import time
from PKDevTools.classes.OutputControls import OutputControls
warnings.simplefilter("ignore", UserWarning,append=True)
os.environ["PYTHONWARNINGS"]="ignore::UserWarning"

def init_pool_processes(the_lock):
    '''Initialize each process with a global variable lock.
    '''
    global lock
    lock = the_lock

import multiprocessing
from multiprocessing import Lock

# from time import sleep
from concurrent.futures import ProcessPoolExecutor
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.console import Console
from rich.control import Control
from rich.segment import ControlType
from pkscreener.classes.PKTask import PKTask

if __name__ == '__main__':
    multiprocessing.freeze_support()

# def long_running_fn(*args, **kwargs):
#     len_of_task = random.randint(3, 20000)  # take some random length of time
#     task = args[0]
#     progress = task.progressStatusDict
#     task_id = task.taskId
#     for n in range(0, len_of_task):
#         # sleep(1)  # sleep for a bit to simulate work
#         progress[task_id] = {"progress": n + 1, "total": len_of_task}
#     # if task is not None:
#     #     progress[task_id] = task.progress_fn(task_id)
#     # else:
#     #     progress[task_id] = {"progress": 100, "total": 100}

progressUpdater=None
class PKScheduler():
    def scheduleTasks(tasksList=[], label:str=None, showProgressBars=False,submitTaskAsArgs=True, timeout=6, minAcceptableCompletionPercentage=100):
        n_workers = multiprocessing.cpu_count() - 1  # set this to the number of cores you have on your machine
        global progressUpdater
        console = Console()
        with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
                TimeElapsedColumn(),
                auto_refresh = True,
                refresh_per_second=100,  # bit slower updates if we keep it to 1
                console=console
            ) as progress:
            progressUpdater = progress
            if len(tasksList) == 0:
                raise ValueError("No tasks in the tasksList!")
            for task in tasksList:
                if not isinstance(task, PKTask):
                    raise ValueError("Each task in the tasksList must be of type PKTask!")
            futures = []  # keep track of the jobs
            with multiprocessing.Manager() as manager:
                # this is the key - we share some state between our 
                # main process and our worker functions
                _progress = manager.dict()
                _results = manager.dict()
                console.control(Control(*((ControlType.CURSOR_UP,1),))) # Cursor up 1 lines f"\x1b[{param}A"
                # sys.stdout.write("\x1b[2K")  # delete the last line
                if showProgressBars:
                    overall_progress_task = progress.add_task(f"[green]{label if label is not None else 'Pending jobs progress:'}", visible=showProgressBars)

                lock = Lock()
                taskResultsUpdated = False
                with ProcessPoolExecutor(max_workers=n_workers,
                                         initializer=init_pool_processes,
                                         initargs=(lock,)) as executor:
                    for task in tasksList:  # iterate over the jobs we need to run
                        # set visible false so we don't have a lot of bars all at once:
                        task_id = progress.add_task(f"Task :{task.taskName}", visible=showProgressBars)
                        task.taskId = task_id
                        task.progressStatusDict = _progress
                        task.resultsDict = _results
                        futures.append(executor.submit(task.long_running_fn, task if submitTaskAsArgs else task.long_running_fn_args))

                    # monitor the progress:
                    start_time = time.time()
                    while (((n_finished := int(sum([future.done() for future in futures]))) < len(futures)) and ((time.time() - start_time) < timeout)):
                        if showProgressBars:
                            progress.update(
                                overall_progress_task,
                                completed=n_finished,
                                total=len(futures),
                                visible=n_finished < len(futures)
                            )
                            OutputControls().printOutput(f"{n_finished} of {len(futures)}")
                        # We've reached a state where the caller may not want to wait any further
                        if n_finished*100/len(futures) >= minAcceptableCompletionPercentage:
                            break
                        for task_id, update_data in _progress.items():
                            for task in tasksList:
                                if task.taskId == task_id:
                                    taskResultsUpdated = True
                                    task.result = task.resultsDict.get(task_id)
                            latest = update_data["progress"]
                            total = update_data["total"]
                            if showProgressBars:
                                # update the progress bar for this task:
                                progress.update(
                                    task_id,
                                    completed=latest,
                                    total=total,
                                    visible=(latest < total) and showProgressBars,
                                )
                            lock.acquire()
                            progress.refresh()
                            lock.release()
                    # sleep(0.1)
                    if showProgressBars:
                        progress.update(
                                overall_progress_task,
                                completed=1,
                                total=1,
                                visible=False
                            )
                    for task_id, update_data in _progress.items():
                        # update the progress bar for this task:
                        if showProgressBars:
                            progress.update(
                                task_id,
                                completed=1,
                                total=1,
                                visible=False,
                            )
                    if not taskResultsUpdated:
                        for task in tasksList:
                            if task.taskId == task_id:
                                task.result = task.resultsDict.get(task_id)
                    lock.acquire()
                    progress.refresh()
                    # raise any errors:
                    # for future in futures:
                    #     future.result()
                    lock.release()

# if __name__ == "__main__":
#     scheduleTasks([PKTask("Task 1",long_running_fn,),
#                 PKTask("Task 2",long_running_fn),
#                 PKTask("Task 3",long_running_fn),
#                 PKTask("Task 4",long_running_fn),
#                 PKTask("Task 5",long_running_fn),
#                 PKTask("Task 6",long_running_fn),
#                 PKTask("Task 7",long_running_fn),
#                 PKTask("Task 8",long_running_fn),
#                 PKTask("Task 9",long_running_fn),
#                 PKTask("Task 10",long_running_fn)])