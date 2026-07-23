"""Fire-and-forget PostHog analytics. Set POSTHOG_KEY env var to enable."""
from __future__ import annotations
import hashlib, os, threading


def track(server: str, tool: str, props: dict | None = None) -> None:
    api_key = os.environ.get("POSTHOG_KEY", "")
    if not api_key:
        return
    _props = dict(props or {})
    ip = _props.pop("_ip", "unknown")
    distinct_id = hashlib.sha256(ip.encode()).hexdigest()[:16]
    payload = {
        "api_key": api_key,
        "event": tool,
        "distinct_id": distinct_id,
        "properties": {"server": server, "tool": tool, **_props},
    }

    def _send() -> None:
        try:
            import httpx
            httpx.post("https://us.i.posthog.com/capture/", json=payload, timeout=2.0)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()
