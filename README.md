ctxs - extra helpers for python "with ..."
==========================================

The [with](https://docs.python.org/3/reference/compound_stmts.html#with)
statement available in python makes it possible to add context and cleanup to
resources, which is useful when working with shared resources that needs to be
released afterwards.

This adds some extra tools to make usage easier.

ContextObject
-------------

When working with multiple contexts at the same time, it is possible to use
multiple context managers in the same `with` statement:

```py

with ResourceA() as a, ResourceB() as b:
    a.do_something()
    b.do_something()

```

But if something needs to be added to the scope later, or dynamically add
resources to the same context, it is not possible.

`ContextObject()` managed the context, and new resources can be added later,
using the `<<`-operator.

The above statement is equivalent to:

```py
from ctxs import ContextObject

with ContextObject() as ctx:
    a = ctx << ResourceA()
    b = ctx << ResourceB()

    a.do_something()
    b.do_something()
```

with the addition that resources can be added later, and dynamically.


ContextThread
-------------

[threading](https://docs.python.org/3/library/threading.html) adds the
possibilty to create threads easily. However, synchronizing execution is still
based upon function calls to the thread object.

In many cases, some thread should be running only within the scope of a certain
block. For example, a temporary server thread only available when a system is
in a certain state.

`ContextThread` makes it possible to create a thread that is running within a
given context, with or without `ContextObject` above.

To create a `ContextThread`, extend the `ContextThread` and implement the
`run()` function, which is executed when the thread enters the context.

Within the context, the `self.is_running` is `True` while running, and when
exiting the context, it will be set to `False`.

```py
from ctxs import ContextThread
import time

class MyThread(ContextThread):
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        while self.is_running:
            print("Tick...")
            time.sleep(1.0)

# Create and run in parallel
with MyThread():
    for i in range(10):
        time.sleep(0.7)
        print("Tock...")

print("Has it stopped?")
time.sleep(4.0)
print("Who knows...")
```

Installation
------------

ctxs is available on [pypi](https://pypi.org/project/ctxs/)

To install:

```sh
pip install ctxs
```

Feedback
--------

The goal of this library is to keep as clean as possible, while still complement
the builtin behaviour.

If you have any thoughts about what it should added.


Roadmap / Ideas
---------------

- `ContextObject` initialized by collections, to make it possible to enter
  a set/list/dict of context managers.
- Add `ContextObject` to other objects, to support nested contexts. For example
  a server (implemented as a `ContextThread`) can spawn it's client threads
  within the parents context.
