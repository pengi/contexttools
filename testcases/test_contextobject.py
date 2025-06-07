import pytest

from typing import Self, Tuple, List, Optional, Type
from types import TracebackType

from ctxs import ContextObject


class FixtureTraceException(Exception):
    tag: str

    def __init__(self, tag: str):
        super().__init__()
        self.tag = tag

    def __str__(self) -> str:
        cause_str = ''
        if self.__cause__ is not None:
            cause_str = ' ' + str(self.__cause__)
        return f'ex:{self.tag}{cause_str}'


class FixtureTrace:
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
        obj = ctx << FixtureTrace(log, 'a')
        assert obj.name == 'a'
        obj = ctx << FixtureTrace(log, 'b')
        assert obj.name == 'b'
        obj = ctx << FixtureTrace(log, 'c')
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
        obj = ctx << FixtureTrace(log, 'a', True)
        assert obj.name == 'a'

        raise FixtureTraceException('b')

    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_no_catch_ex() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(FixtureTraceException) as exc_info:
        with ContextObject() as ctx:
            obj = ctx << FixtureTrace(log, 'a', False)
            assert obj.name == 'a'

            raise FixtureTraceException('b')

    assert exc_info.value.tag == 'b'
    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_throw_ex_at_exit() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(FixtureTraceException) as exc_info:
        with ContextObject() as ctx:
            obj = ctx << FixtureTrace(
                log, 'a', False, FixtureTraceException('c'))
            assert obj.name == 'a'

            raise FixtureTraceException('b')

    assert str(exc_info.value) == 'ex:c ex:b'
    assert log == [
        ('enter', 'a', ''),
        ('exit', 'a', 'ex:b'),
    ]


def test_nexted_causes() -> None:
    log: List[Tuple[str, str, str]] = []
    with pytest.raises(FixtureTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << FixtureTrace(log, 'a', False, FixtureTraceException('A'))
            ctx << FixtureTrace(log, 'b', False, FixtureTraceException('B'))
            ctx << FixtureTrace(log, 'c', False, FixtureTraceException('C'))
            ctx << FixtureTrace(log, 'd', False, FixtureTraceException('D'))
            raise FixtureTraceException('end')

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
    with pytest.raises(FixtureTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << FixtureTrace(log, 'a', False, FixtureTraceException('A'))
            ctx << FixtureTrace(log, 'b', False, FixtureTraceException('B'))
            ctx << FixtureTrace(log, 'c', True)
            ctx << FixtureTrace(log, 'd', False, FixtureTraceException('D'))
            raise FixtureTraceException('end')

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
    with pytest.raises(FixtureTraceException) as exc_info:
        with ContextObject() as ctx:
            ctx << FixtureTrace(log, 'a', False, FixtureTraceException('A'))

            # Generate a B exception raised from B2

            ex: Optional[Exception] = None
            try:
                try:
                    raise FixtureTraceException('B2')
                except FixtureTraceException as e:
                    raise FixtureTraceException('B') from e
            except FixtureTraceException as e:
                ex = e
            ctx << FixtureTrace(log, 'b', False, ex)

            raise FixtureTraceException('end')

    assert str(exc_info.value) == 'ex:A ex:B ex:B2 ex:end'
    assert log == [
        ('enter', 'a', ''),
        ('enter', 'b', ''),
        ('exit', 'b', 'ex:end'),
        ('exit', 'a', 'ex:B ex:B2 ex:end'),
    ]
