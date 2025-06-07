#
# Copyright (c) Max Sikstrom <max@pengi.se>
# Licensed under the MIT license. See LICENSE file in the project root for
# details.
#
# SPDX-License-Identifier: MIT
#

import threading as th

from typing import Optional, Type, Self
from types import TracebackType


class ContextThreadDidNotExitException(Exception):
    pass


class ContextThread:
    _thread: th.Thread
    _halt: th.Event

    THREAD_EXIT_TIMEOUT: Optional[float] = None

    @property
    def is_running(self) -> bool:
        return not self._halt.is_set()

    def run(self) -> None:
        pass

    def __enter__(self) -> Self:
        # Initialize is_running internals
        self._halt = th.Event()
        self._halt.clear()

        self._thread = th.Thread(target=self.run)
        self._thread.start()

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        self._halt.set()
        self._thread.join(timeout=self.THREAD_EXIT_TIMEOUT)
        if self._thread.is_alive():
            raise ContextThreadDidNotExitException()
        return bool(False)
