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
import sys
from multiprocessing import Event
from queue import Queue
from unittest.mock import Mock, patch

import pytest

from pkscreener.classes.PKMultiProcessorClient import PKMultiProcessorClient


@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch('queue.Queue.task_done', new=patched_caller):
            yield


def patched_caller(*args, **kwargs):
    args[0].put(None)
    args[0].unfinished_tasks = 0

def patched_task_queue_get(*args, **kwargs):
    return None

@pytest.fixture
def task_queue():
    return Queue()

@pytest.fixture
def result_queue():
    return Queue()

@pytest.fixture
def processing_counter():
    return Mock()

@pytest.fixture
def processing_results_counter():
    return Mock()

@pytest.fixture
def object_dictionary():
    return {}

@pytest.fixture
def proxy_server():
    return Mock()

@pytest.fixture
def keyboard_interrupt_event():
    return Event()

@pytest.fixture
def default_logger():
    return Mock()

@pytest.fixture
def client(
    task_queue,
    result_queue,
    processing_counter,
    processing_results_counter,
    object_dictionary,
    proxy_server,
    keyboard_interrupt_event,
    default_logger
):
    return PKMultiProcessorClient(
        Mock(),
        task_queue,
        result_queue,
        processing_counter,
        processing_results_counter,
        object_dictionary,
        proxy_server,
        keyboard_interrupt_event,
        default_logger
    )

def test_run_positive(client, task_queue, result_queue, default_logger):
    client.task_queue.put("task")
    client.run()
    assert client.task_queue.unfinished_tasks == 0
    assert not client.result_queue.empty()
    assert default_logger.info.called

def test_run_no_task(client, task_queue, result_queue, default_logger):
    client.task_queue.put(None)
    client.run()
    assert client.task_queue.unfinished_tasks == 0
    assert client.result_queue.empty()
    assert default_logger.info.called

def test_run_exception(client, task_queue, result_queue, default_logger):
    task_queue.put("task")
    client.processorMethod.side_effect = Exception("error")
    with pytest.raises(SystemExit):
        client.run()
    assert client.task_queue.empty()
    assert client.result_queue.empty()
    assert default_logger.debug.called
    assert default_logger.info.called

def test_run_keyboard_interrupt(client, task_queue, result_queue, default_logger, keyboard_interrupt_event):
    task_queue.put("task")
    keyboard_interrupt_event.set()
    client.run()
    assert not client.task_queue.empty()
    assert client.result_queue.empty()
    assert not default_logger.debug.called
