"""
Tests for executor heartbeat functionality.

Covers:
- _with_heartbeat closes source generator on normal completion
- _with_heartbeat closes source generator on early consumer exit
- _with_heartbeat explicitly calls aclose() on the source iterator
- Heartbeat events emitted during long-running execution
- Heartbeat events contain elapsed_s field
"""

import asyncio

import pytest

from autocode.core.planning.executor import _with_heartbeat
from tests.unit.core.planning.conftest import _parse_sse


# ============================================================================
# TEST: HEARTBEAT CLOSES SOURCE GENERATOR (Commit 5)
# ============================================================================


class TestHeartbeatClosesSourceGenerator:
    """_with_heartbeat should close the source generator in its finally block."""

    @pytest.mark.asyncio
    async def test_source_generator_closed_on_normal_completion(self):
        """Source async generator's aclose is called after normal iteration."""
        closed = []

        async def tracked_source():
            try:
                yield "item1"
                yield "item2"
            finally:
                closed.append(True)

        items = []
        async for item in _with_heartbeat(tracked_source(), interval=10):
            items.append(item)

        assert "item1" in items
        assert "item2" in items
        assert closed, "Source generator should be closed after _with_heartbeat completes"

    @pytest.mark.asyncio
    async def test_source_generator_closed_on_early_exit(self):
        """Source async generator is closed even if consumer breaks early."""
        closed = []

        async def infinite_source():
            try:
                while True:
                    yield "item"
                    await asyncio.sleep(0.01)
            finally:
                closed.append(True)

        count = 0
        async for item in _with_heartbeat(infinite_source(), interval=10):
            if not isinstance(item, str) or "heartbeat" not in item:
                count += 1
            if count >= 2:
                break

        # Give cleanup a moment
        await asyncio.sleep(0.05)
        assert closed, "Source generator should be closed when consumer breaks early"

    @pytest.mark.asyncio
    async def test_heartbeat_explicitly_calls_aclose_on_source(self):
        """_with_heartbeat must call aclose() explicitly on the source, not rely on GC.

        Async generators are cleaned up by CPython's reference counting — but
        async *iterators* (classes that implement __anext__) are NOT automatically
        closed when the consuming async for loop exits early. Without an explicit
        await async_gen.aclose() in _with_heartbeat's finally block, any resource-
        holding async iterator (DB cursors, file handles, network connections) will
        NOT be deterministically released.

        This test uses a plain async iterator class (not async def + yield) so that
        Python's async generator finalizer machinery does NOT trigger automatically.
        The only way for aclose_calls to be populated is if _with_heartbeat calls
        aclose() explicitly.
        """
        aclose_calls = []

        class ResourceHoldingIterator:
            """Async iterator simulating a resource holder (e.g., DB cursor, file handle).

            NOTE: This is an async *iterator* (class with __anext__), NOT an async
            generator (async def + yield). Python's async for loop does NOT call
            aclose() on plain async iterators — only _with_heartbeat's explicit
            call would trigger it.
            """

            def __aiter__(self):
                self._items = iter(["a", "b", "c", "d", "e"])
                return self

            async def __anext__(self):
                try:
                    return next(self._items)
                except StopIteration:
                    raise StopAsyncIteration

            async def aclose(self):
                aclose_calls.append(True)

        count = 0
        async for item in _with_heartbeat(ResourceHoldingIterator(), interval=10):
            count += 1
            if count >= 2:
                break

        assert aclose_calls, (
            "_with_heartbeat must explicitly call aclose() on the source iterator. "
            "Without this, resource-holding async iterators (DB cursors, file handles, "
            "network connections) are NOT deterministically released when the consumer "
            "breaks early. This relies on CPython GC for async generators but fails "
            "for plain async iterators that implement aclose()."
        )


# ============================================================================
# TEST: HEARTBEAT
# ============================================================================


class TestHeartbeat:
    """Heartbeat events are emitted during long-running execution."""

    @pytest.mark.asyncio
    async def test_heartbeat_emitted_during_execution(self):
        """Heartbeat wrapper emits heartbeat events interleaved with source."""
        emitted = []

        async def slow_source():
            yield "first"
            await asyncio.sleep(0.15)  # Trigger heartbeat
            yield "second"

        async for item in _with_heartbeat(slow_source(), interval=0.05):
            emitted.append(item)

        # Should have: "first", possibly heartbeat(s), "second"
        assert "first" in emitted
        assert "second" in emitted
        heartbeats = [e for e in emitted if isinstance(e, str) and "heartbeat" in e]
        assert len(heartbeats) >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_contains_elapsed_s(self):
        """Heartbeat events contain elapsed_s field."""

        async def slow_source():
            await asyncio.sleep(0.15)
            yield "done"

        heartbeats = []
        async for item in _with_heartbeat(slow_source(), interval=0.05):
            if isinstance(item, str) and "heartbeat" in item:
                heartbeats.append(_parse_sse(item))

        assert len(heartbeats) >= 1
        assert "elapsed_s" in heartbeats[0]["data"]
        assert heartbeats[0]["data"]["elapsed_s"] >= 0
