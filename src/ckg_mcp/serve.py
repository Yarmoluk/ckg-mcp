"""Remote HTTP entry point — runs ckg-mcp as a hosted MCP server (Render-compatible)."""
from __future__ import annotations

import os
import time
import uuid
import threading
from collections import defaultdict

from .server import mcp
from .analytics import track

_VERSION = "0.7.9"
_FREE_LIMIT = 5
_TRIAL_LIMIT = 100
_STRIPE_PRO = "https://buy.stripe.com/fZu9ATccIgCg4FO9iQ1kA06"
_CAL_LINK = "https://cal.com/daniel-yarmoluk-sjmnub/30min"
_TALLY_LINK = "https://tally.so/r/b5Ep4g"

_call_counts: dict = defaultdict(lambda: {"count": 0, "reset": time.time() + 86400})
_trial_keys: dict = {}


def _get_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host or "unknown")


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    state = _call_counts[ip]
    if now > state["reset"]:
        state["count"] = 0
        state["reset"] = now + 86400
    if state["count"] >= _FREE_LIMIT:
        return False
    state["count"] += 1
    return True


def _send_trial_email(email: str, key: str) -> None:
    resend_key = os.environ.get("RESEND_KEY", "")
    if not resend_key:
        return
    try:
        import httpx
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}"},
            json={
                "from": "Graphify.md <noreply@graphifymd.com>",
                "to": [email],
                "subject": "Your CKG trial key",
                "html": (
                    f"<p>Thanks for registering!</p>"
                    f"<p><strong>Trial key:</strong> <code>{key}</code></p>"
                    f"<p>Add to your MCP client as the <code>X-License-Key</code> header. "
                    f"Gives you 100 calls on the ckg-mcp endpoint (97 domains).</p>"
                    f"<p>Endpoint: <code>https://ckg-mcp.onrender.com/mcp</code></p>"
                    f"<p>Pro access (all 97 domains, unlimited): "
                    f"<a href='{_STRIPE_PRO}'>graphifymd.com/pro</a></p>"
                    f"<p>— Graphify.md</p>"
                ),
            },
            timeout=5.0,
        )
    except Exception:
        pass


_LANDING = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ckg-mcp — 97-Domain Knowledge Graph MCP Server</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 640px; margin: 80px auto; padding: 0 24px; color: #13201c; background: #fbfbf9; }}
  h1 {{ font-size: 1.4rem; font-weight: 700; color: #0f6e56; }}
  code {{ background: #e8f0ee; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
  pre {{ background: #f0f4f2; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.88em; }}
  a {{ color: #0f6e56; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-top: 2rem; }}
  .badge {{ background: #0f6e56; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; }}
</style>
</head>
<body>
<h1>ckg-mcp <span class="badge">v{_VERSION}</span></h1>
<p>97 domains · 1,055+ nodes · deterministic graph traversal · 11× fewer tokens than RAG</p>
<p>F1 0.471 · 4× RAG · $7.81 vs $76.23 per 1k queries</p>

<h2>Endpoint</h2>
<pre>https://ckg-mcp.onrender.com/mcp</pre>
<p>Add to Claude Desktop, claude.ai, or Cursor — paste the URL above.</p>

<h2>Free tier</h2>
<p>{_FREE_LIMIT} calls/day · no key required · <a href="{_TALLY_LINK}">get 100-call trial key</a></p>

<h2>Pro</h2>
<p>All 97 domains · unlimited · <a href="{_STRIPE_PRO}">$99/mo →</a></p>

<p class="meta">
  <a href="https://graphifymd.com">graphifymd.com</a> ·
  <a href="https://github.com/Yarmoluk/ckg-mcp">GitHub</a> ·
  <a href="https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf">Benchmark paper</a> ·
  Built by Graphify.md · Patent pending
</p>
</body>
</html>"""


def main():
    import uvicorn
    from starlette.applications import Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, JSONResponse
    from starlette.routing import Mount, Route

    port = int(os.environ.get("PORT", 8000))

    class RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path.startswith("/mcp"):
                ip = _get_ip(request)
                license_key = request.headers.get("X-License-Key", "").strip()
                if license_key:
                    entry = _trial_keys.get(license_key)
                    if entry is None or entry["calls"] >= _TRIAL_LIMIT:
                        return JSONResponse(
                            {"error": "Trial limit reached.", "upgrade": _STRIPE_PRO},
                            status_code=402,
                        )
                    entry["calls"] += 1
                    track("ckg-mcp", "mcp_request", {"key_type": "trial", "_ip": ip})
                else:
                    if not _check_rate_limit(ip):
                        track("ckg-mcp", "rate_limit_hit", {"_ip": ip})
                        return JSONResponse(
                            {
                                "error": f"Free tier limit reached ({_FREE_LIMIT} calls/day).",
                                "get_trial_key": _TALLY_LINK,
                                "upgrade": _STRIPE_PRO,
                            },
                            status_code=402,
                        )
                    track("ckg-mcp", "mcp_request", {"key_type": "free", "_ip": ip})
            return await call_next(request)

    async def homepage(request: Request):
        return HTMLResponse(_LANDING)

    async def server_card(request: Request):
        return JSONResponse({
            "name": "ckg-mcp",
            "version": _VERSION,
            "description": "97-domain Compressed Knowledge Graph — NVIDIA, Finance, Healthcare, Enterprise AI, and more",
            "publisher": "Graphify.md",
            "publisher_url": "https://graphifymd.com",
        })

    async def register(request: Request):
        email = ""
        if request.method == "POST":
            try:
                body = await request.json()
                if "data" in body and "fields" in body["data"]:
                    for field in body["data"]["fields"]:
                        if "email" in (field.get("label") or "").lower() or field.get("type") == "INPUT_EMAIL":
                            email = field.get("value", "")
                            break
                else:
                    email = body.get("email", "")
            except Exception:
                email = request.query_params.get("email", "")
        else:
            email = request.query_params.get("email", "")

        if not email or "@" not in email:
            return JSONResponse({"error": "valid email required"}, status_code=400)

        key = uuid.uuid4().hex[:24]
        _trial_keys[key] = {"email": email, "calls": 0}
        track("ckg-mcp", "trial_register", {"email": email})
        threading.Thread(target=_send_trial_email, args=(email, key), daemon=True).start()
        return JSONResponse({
            "key": key,
            "email": email,
            "limit": _TRIAL_LIMIT,
            "header": "X-License-Key",
            "endpoint": "https://ckg-mcp.onrender.com/mcp",
        })

    mcp_app = mcp.streamable_http_app()
    app = Starlette(routes=[
        Route("/", homepage),
        Route("/.well-known/mcp/server-card.json", server_card),
        Route("/register", register, methods=["GET", "POST"]),
        Mount("/mcp", app=mcp_app),
    ])
    app.add_middleware(RateLimitMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
