import pytest

from typing import Self, Tuple, List, Optional, Type
from types import TracebackType

from ctxs import ContextObject


class TestCtxTraceException(Exception):
    tag: str

    def __init__(self, tag: str):
        super().__init__()
        self.tag = tag

    def __str__(self) -> str:
        cause_str = ''
        if self.__cause__ is not None:
            cause_str = ' ' + str(self.__cause__)
        return f'ex:{self.tag}{cause_str}'


class TestCtxTrace:
    catch_ex: bool
    raise_ex: Optional[Exception]

    def __init__(
        self,
        log: List[Tuple[str, str, str]],
        name: str,
        catch_ex: bool = False,
        raise_ex: Optional[Exception] = None
    ):
        self.log = log
        self.name = name
        self.catch_ex = catch_ex
        self.raise_ex = raise_ex

    def __enter__(self) -> Self:
        self.log.append(('enter', self.name, ''))
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        self.log.append(('exit', self.name, str(exc_val)))
        if self.raise_ex is not None:
            raise self.raise_ex
        return self.catch_ex


def test_attach_order() -> None:
    log: List[Tuple[str, str, str]] = []
    with ContextObject() as ctx:
        obj = ctx << TestCtxTrace(log, 'a')
        assert obj.name == 'a'
        obj = ctx << TestCtxTrace(log, 'b')
        assert obj.name == 'b'
        obj = ctx << TestCtxTrace(log, 'c')
        assert obj.name == 'c'
    assert log == [
        ('enter', 'a', ''),
        ('enter', 'b', ''),
        ('enter', 'c', ''),
        ('exit', 'c', 'None'),
        ('exit', 'b', 'None'),
        ('exit', 'a', 'None'),
    ]


def test_catch_ex() -> None:
    log: List[Tuple[str, str, str]] = []
    with ContextObject() as ctx:
        obj = ctx << TestCtxTrace(log, 'a', True)
        assert obj.name == 'a'

        raise TestCtxTraceException('b')

    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_no_catch_ex() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(TestCtxTraceException) as exc_info:
        with ContextObject() as ctx:
            obj = ctx << TestCtxTrace(log, 'a', False)
            assert obj.name == 'a'

            raise TestCtxTraceException('b')

    assert exc_info.value.tag == 'b'
    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_throw_ex_at_exit() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(TestCtxTraceException) as exc_info:
        with ContextObject() as ctx:
            obj = ctx << TestCtxTrace(
                log, 'a', False, TestCtxTraceException('c'))
            assert obj.name == 'a'

            raise TestCtxTraceException('b')

    assert str(exc_info.value) == 'ex:c ex:b'
    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_nexted_causes() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(TestCtxTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << TestCtxTrace(log, 'a', False, TestCtxTraceException('A'))
            ctx << TestCtxTrace(log, 'b', False, TestCtxTraceException('B'))
            ctx << TestCtxTrace(log, 'c', False, TestCtxTraceException('C'))
            ctx << TestCtxTrace(log, 'd', False, TestCtxTraceException('D'))
            raise TestCtxTraceException('end')

    assert str(exc_info.value) == 'ex:A ex:B ex:C ex:D ex:end'
    assert log == [
        ('enter', 'a', ''),
        ('enter', 'b', ''),
        ('enter', 'c', ''),
        ('enter', 'd', ''),
        ('exit', 'd', 'ex:end'),
        ('exit', 'c', 'ex:D ex:end'),
        ('exit', 'b', 'ex:C ex:D ex:end'),
        ('exit', 'a', 'ex:B ex:C ex:D ex:end'),
    ]


def test_nexted_causes_with_catch() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(TestCtxTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << TestCtxTrace(log, 'a', False, TestCtxTraceException('A'))
            ctx << TestCtxTrace(log, 'b', False, TestCtxTraceException('B'))
            ctx << TestCtxTrace(log, 'c', True)
            ctx << TestCtxTrace(log, 'd', False, TestCtxTraceException('D'))
            raise TestCtxTraceException('end')

    assert str(exc_info.value) == 'ex:A ex:B'
    assert log == [
        ('enter', 'a', ''),
        ('enter', 'b', ''),
        ('enter', 'c', ''),
        ('enter', 'd', ''),
        ('exit', 'd', 'ex:end'),
        ('exit', 'c', 'ex:D ex:end'),
        ('exit', 'b', 'None'),
        ('exit', 'a', 'ex:B'),
    ]


def test_nexted_throw() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(TestCtxTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << TestCtxTrace(log, 'a', False, TestCtxTraceException('A'))

            # Generate a B exception raised from B2

            ex: Optional[Exception] = None
            try:
                try:
                    raise TestCtxTraceException('B2')
                except TestCtxTraceException as e:
                    raise TestCtxTraceException('B') from e
            except TestCtxTraceException as e:
                ex = e
            ctx << TestCtxTrace(log, 'b', False, ex)

            raise TestCtxTraceException('end')

    assert str(exc_info.value) == 'ex:A ex:B ex:B2 ex:end'
    assert log == [
        ('enter', 'a', ''),
        ('enter', 'b', ''),
        ('exit', 'b', 'ex:end'),
        ('exit', 'a', 'ex:B ex:B2 ex:end'),
    ]
