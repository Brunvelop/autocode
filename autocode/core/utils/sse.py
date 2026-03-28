"""
SSE serialization utility shared across autocode modules.

Thin wrapper over ``refract.sse.format_sse`` that adds a single
responsibility: serialise the payload dict with ``ensure_ascii=False``
so that emojis and non-ASCII characters are preserved on the wire.

Both ``autocode.core.ai.streaming`` (chat) and
``autocode.core.planning.executor`` (plan execution) use this helper,
keeping the serialisation behaviour in one place.
"""

import json

from refract.sse import format_sse as _refract_format_sse


def format_sse_event(event: str, data: dict) -> str:
    """Format an SSE event from a dict payload.

    Thin wrapper over ``refract.sse.format_sse``: serialises the dict with
    ``ensure_ascii=False`` (preserves unicode / emojis) and delegates the
    SSE framing to refract, keeping a single source of truth for the wire
    format.

    Args:
        event: SSE event type (``"token"``, ``"status"``, ``"complete"``,
            ``"error"``, …)
        data: Event payload as a dict — will be JSON-serialised.

    Returns:
        SSE-formatted string ready to be yielded by a streaming response.

    Example::

        line = format_sse_event("status", {"message": "🛠️ processing"})
        # "event: status\\ndata: {\\"message\\": \\"🛠️ processing\\"}\\n\\n"
    """
    return _refract_format_sse(event, json.dumps(data, ensure_ascii=False))
