"""
Request-scoped ambient memoization.

Values live only while a ``stash_scope()`` is open (typically for the duration
of one HTTP request or a deferred ``TemplateResponse`` render). Nothing is
stored across requests, threads, or processes.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

from asgiref.local import Local

T = TypeVar("T")

_local = Local()
_MISSING = object()


def _scope_map() -> dict[str | None, list[dict[str, Any]]]:
    scopes = getattr(_local, "scopes", None)
    if scopes is None:
        scopes = {}
        _local.scopes = scopes
    return scopes


def _frames(scope: str | None) -> list[dict[str, Any]] | None:
    return _scope_map().get(scope)


def enabled(*, scope: str | None = None) -> bool:
    """Return whether a stash scope is active for this execution context."""
    return bool(_frames(scope))


def get(key: str, default: Any = None, *, scope: str | None = None) -> Any:
    """Return a stashed value, or ``default`` on miss / when no scope is active."""
    stack = _frames(scope)
    if not stack:
        return default
    for frame in reversed(stack):
        if key in frame:
            return frame[key]
    return default


def set(key: str, value: Any, *, scope: str | None = None) -> None:
    """
    Store ``value`` under ``key`` in the innermost block of ``scope``.

    No-op when that scope is not active (avoids sticky process-level state).
    """
    stack = _frames(scope)
    if not stack:
        return
    stack[-1][key] = value


def clear(key: str | None = None, *, scope: str | None = None) -> None:
    """
    Clear one key, or the current innermost block when ``key`` is omitted.

    ``clear("k")`` removes ``k`` from every nested block of ``scope``.
    """
    stack = _frames(scope)
    if not stack:
        return
    if key is None:
        stack[-1].clear()
        return
    for frame in stack:
        frame.pop(key, None)


def get_or_set(key: str, loader: Callable[[], T], *, scope: str | None = None) -> T:
    """
    Return a stashed value, or call ``loader``, stash the result, and return it.

    When no scope is active, always calls ``loader()`` and does not store.
    """
    stack = _frames(scope)
    if not stack:
        return loader()

    value = get(key, default=_MISSING, scope=scope)
    if value is not _MISSING:
        return value

    loaded = loader()
    stack[-1][key] = loaded
    return loaded


@contextmanager
def stash_scope(name: str | None = None) -> Iterator[None]:
    """
    Open a stash scope for a block of work.

    Nested calls with the same name stack; inner writes stay in the inner
    block.
    """
    scopes = _scope_map()
    stack = scopes.setdefault(name, [])
    stack.append({})
    try:
        yield
    finally:
        current = _scope_map().get(name)
        if current is stack and stack:
            stack.pop()
            if not stack:
                _scope_map().pop(name, None)
