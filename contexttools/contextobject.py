#
# Copyright (c) Max Sikstrom <max@pengi.se>
# Licensed under the MIT license. See LICENSE file in the project root for
# details.
#
# SPDX-License-Identifier: MIT
#

from typing import ContextManager, List, TypeVar, Any, Optional, Type, Self
from types import TracebackType

T = TypeVar('T')


class ContextObject:
    _contexts: List[ContextManager[Any]]
    _context_active: bool

    def __init__(self) -> None:
        self._contexts = []
        self._context_active = False

    def attach(self, obj: ContextManager[T]) -> T:
        assert self._context_active, "attaching to non-active ContextObject"
        self._contexts.append(obj)
        return obj.__enter__()

    def __lshift__(self, obj: ContextManager[T]) -> T:
        return self.attach(obj)

    def __enter__(self) -> Self:
        assert not self._context_active, "recursive __enter__ in ContextObject"
        self._context_active = True
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        assert self._context_active, "__exit__ before __enter__"

        new_exc = False
        for ctx in reversed(self._contexts):
            try:
                if ctx.__exit__(exc_type, exc_val, exc_tb):
                    new_exc = False
                    exc_type = None
                    exc_val = None
                    exc_tb = None
            except Exception as e:
                # When raising an exception from a previously uncaught
                # exception. Make sure the cause is kept.
                #
                # Note that the __exit__ can have an exception cause-chain
                # already
                last_ex: BaseException = e
                while last_ex.__cause__ is not None:
                    last_ex = last_ex.__cause__
                last_ex.__cause__ = exc_val

                new_exc = True
                exc_type = type(e)
                exc_val = e
                exc_tb = e.__traceback__
        if new_exc and exc_val is not None:
            # If any context manager exit raised an exception, re-raise
            raise exc_val
        return exc_val is None
