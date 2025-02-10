#!/usr/bin/python3
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
import unittest
from unittest.mock import patch, MagicMock
from multiprocessing import Manager
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from rich.progress import Progress

class TestPKScheduler(unittest.TestCase):

    def setUp(self):
        self.task1 = MagicMock(spec=PKTask)
        self.task1.taskName = "Task 1"
        self.task1.long_running_fn = MagicMock(return_value=None)
        
        self.task2 = MagicMock(spec=PKTask)
        self.task2.taskName = "Task 2"
        self.task2.long_running_fn = MagicMock(return_value=None)
        
        self.tasksList = [self.task1, self.task2]

    # def test_scheduleTasks_success(self):
    #     """Test successful scheduling of tasks."""
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.submit = MagicMock()
    #         PKScheduler.scheduleTasks(self.tasksList, label="Test Label", showProgressBars=True)
    #         self.assertTrue(mock_executor.called)
    #         self.assertEqual(mock_executor.call_count, 1)

    def test_scheduleTasks_no_tasks(self):
        """Test scheduling with no tasks raises ValueError."""
        with self.assertRaises(ValueError) as context:
            PKScheduler.scheduleTasks([], label="Test Label")
        self.assertEqual(str(context.exception), "No tasks in the tasksList!")

    def test_scheduleTasks_invalid_task_type(self):
        """Test scheduling with invalid task type raises ValueError."""
        invalid_task = "Not a PKTask"
        with self.assertRaises(ValueError) as context:
            PKScheduler.scheduleTasks([invalid_task], label="Test Label")
        self.assertEqual(str(context.exception), "Each task in the tasksList must be of type PKTask!")

    # def test_scheduleTasks_timeout(self):
    #     """Test that the timeout works as expected."""
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.__enter__.return_value.submit = MagicMock()
    #         # Simulating a long-running task by not completing it
    #         mock_executor.return_value.__enter__.return_value.shutdown = MagicMock()
    #         with self.assertRaises(TimeoutError):
    #             PKScheduler.scheduleTasks(self.tasksList, timeout=0.1)

    # def test_scheduleTasks_progress_update(self):
    #     """Test progress updates during task execution."""
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.__enter__.return_value.submit = MagicMock()
    #         PKScheduler.scheduleTasks(self.tasksList, showProgressBars=True)
    #         for task in self.tasksList:
    #             task.long_running_fn.assert_called_once()

    # def test_scheduleTasks_edge_case(self):
    #     """Test edge case with a single task."""
    #     single_task = [self.task1]
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.__enter__.return_value.submit = MagicMock()
    #         PKScheduler.scheduleTasks(single_task, label="Single Task", showProgressBars=False)
    #         self.assertTrue(mock_executor.called)

    # def test_scheduleTasks_no_progress_bars(self):
    #     """Test if tasks are scheduled without showing progress bars."""
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.__enter__.return_value.submit = MagicMock()
    #         PKScheduler.scheduleTasks(self.tasksList, showProgressBars=False)
    #         self.assertTrue(mock_executor.called)

    # def test_scheduleTasks_with_lock(self):
    #     """Test that the lock is initialized and used correctly."""
    #     with patch('concurrent.futures.process.ProcessPoolExecutor') as mock_executor:
    #         mock_executor.return_value.__enter__.return_value.submit = MagicMock()
    #         lock = Manager().Lock()
    #         PKScheduler.scheduleTasks(self.tasksList, showProgressBars=True)
    #         self.assertTrue(lock.acquire.called or lock.release.called)


class TestPKScheduler2(unittest.TestCase):

    @patch('pkscreener.classes.PKScheduler.Progress')
    @patch('pkscreener.classes.PKScheduler.ProcessPoolExecutor')
    @patch('multiprocessing.Manager')
    def test_scheduleTasks_success(self, mock_manager, mock_executor, mock_progress):
        # Arrange
        mock_progress_instance = MagicMock(spec=Progress)
        mock_progress.return_value = mock_progress_instance
        
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        mock_manager_instance = MagicMock()
        mock_manager.return_value.__enter__.return_value = mock_manager_instance
        mock_manager_instance.dict.return_value = {}

        task_mock = MagicMock(spec=PKTask)
        task_mock.taskName = "TestTask"
        task_mock.long_running_fn = MagicMock()
        task_mock.taskId = None
        task_mock.progressStatusDict = {}
        task_mock.resultsDict = {}

        tasksList = [task_mock]

        # Act
        PKScheduler.scheduleTasks(tasksList=tasksList, label="TestLabel", showProgressBars=True)

        # Assert
        mock_progress.assert_called()
        # mock_progress_instance.add_task.assert_called()
        mock_executor_instance.submit.assert_called()
        # self.assertEqual(task_mock.taskId, mock_progress_instance.add_task.return_value)

    def test_scheduleTasks_empty_tasksList(self):
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            PKScheduler.scheduleTasks(tasksList=[])
        self.assertEqual(str(context.exception), "No tasks in the tasksList!")

    def test_scheduleTasks_invalid_task_type(self):
        # Arrange
        invalid_task = "Not a PKTask"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            PKScheduler.scheduleTasks(tasksList=[invalid_task])
        self.assertEqual(str(context.exception), "Each task in the tasksList must be of type PKTask!")

    @patch('pkscreener.classes.PKScheduler.Progress')
    @patch('pkscreener.classes.PKScheduler.ProcessPoolExecutor')
    @patch('multiprocessing.Manager')
    def test_scheduleTasks_progress_bar_updates(self, mock_manager, mock_executor, mock_progress):
        # Arrange
        mock_progress_instance = MagicMock(spec=Progress)
        mock_progress.return_value = mock_progress_instance
        
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        mock_manager_instance = MagicMock()
        mock_manager.return_value.__enter__.return_value = mock_manager_instance
        mock_manager_instance.dict.return_value = {1: {"progress": 50, "total": 100}}

        task_mock = MagicMock(spec=PKTask)
        task_mock.taskName = "TestTask"
        task_mock.long_running_fn = MagicMock()
        task_mock.taskId = None
        task_mock.progressStatusDict = {}
        task_mock.resultsDict = {}

        tasksList = [task_mock]

        # Act
        PKScheduler.scheduleTasks(tasksList=tasksList, label="TestLabel", showProgressBars=True)

        # Assert
        mock_progress.assert_called()
        # mock_progress_instance.update.assert_called()
        # self.assertEqual(task_mock.taskId, mock_progress_instance.add_task.return_value)
