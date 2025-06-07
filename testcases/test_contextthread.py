import pytest

import time

from contexttools import \
    ContextThread, \
    ContextThreadDidNotExitException

STATE_INIT = 1
STATE_RUNNING = 2
STATE_STOPPED = 3


class TestCtxThread(ContextThread):
    state: int

    def __init__(self) -> None:
        self.state = STATE_INIT

    def run(self) -> None:
        self.state = STATE_RUNNING
        while self.is_running:
            time.sleep(0.05)
        self.state = STATE_STOPPED


class TestCtxFixedRuntime(ContextThread):
    THREAD_EXIT_TIMEOUT = 0.2

    def __init__(self) -> None:
        pass

    def run(self) -> None:
        time.sleep(1.0)


def test_thred_running() -> None:
    thread = TestCtxThread()
    time.sleep(0.1)  # Make sure enough time to task switch
    assert thread.state == STATE_INIT

    with thread:
        time.sleep(0.1)  # Make sure enough time to task switch
        assert thread.state == STATE_RUNNING

    assert thread.state == STATE_STOPPED


def test_default_impl_callable() -> None:
    # Mostly for coverage
    with ContextThread():
        pass


def test_thred_no_exit_exception() -> None:
    thread = TestCtxFixedRuntime()
    with pytest.raises(ContextThreadDidNotExitException):
        with thread:
            time.sleep(0.1)  # Make sure enough time to task switch
