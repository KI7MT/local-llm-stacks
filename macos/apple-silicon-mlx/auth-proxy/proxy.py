"""Bearer-key proxy in front of mlx_lm.server, which has no API-key option.

mlx_lm.server stays on 127.0.0.1. This proxy listens where other machines can reach it, checks
the Authorization header, and forwards /v1/* to the server unchanged, streaming included.

The key is read once at startup from the macOS Keychain (via the `keyring` package), never from
an argument or an environment variable, and is never logged. Store it first:

    python -m keyring set mlx-server api-key
"""

from __future__ import annotations

import hmac
import json
import os
import sys

import httpx
import keyring
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

KEYCHAIN_SERVICE = "mlx-server"
KEYCHAIN_ACCOUNT = "api-key"


def _load_key() -> str:
    key = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT)
    if not key or not key.strip():
        sys.exit(
            f"no API key in the Keychain under service '{KEYCHAIN_SERVICE}', "
            f"account '{KEYCHAIN_ACCOUNT}'. Store one with: "
            f"python -m keyring set {KEYCHAIN_SERVICE} {KEYCHAIN_ACCOUNT}"
        )
    return key.strip()


_API_KEY = _load_key()
_UPSTREAM = f"http://127.0.0.1:{int(os.environ.get('UPSTREAM_PORT', '8081'))}"
# Long reads: a large model can think for minutes before the first token.
_TIMEOUT = httpx.Timeout(connect=10.0, read=900.0, write=30.0, pool=10.0)
# Headers that describe this hop, or carry the key, and must not be forwarded.
_DROP = {"host", "authorization", "content-length", "connection"}

app = FastAPI(title="mlx-server auth proxy")


def _require_bearer(request: Request) -> None:
    """401 for a missing or malformed header, 403 for a wrong key. Never a 500."""
    parts = request.headers.get("authorization", "").split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="missing Bearer token")
    if not hmac.compare_digest(parts[1].strip().encode(), _API_KEY.encode()):
        raise HTTPException(status_code=403, detail="invalid token")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness of the proxy only. Needs no key and does not touch the model server."""
    return {"status": "ok"}


@app.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def forward(path: str, request: Request) -> Response:
    _require_bearer(request)
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _DROP}
    url = f"{_UPSTREAM}/v1/{path}"

    streaming = False
    if body:
        try:
            streaming = bool(json.loads(body).get("stream", False))
        except (ValueError, AttributeError):
            streaming = False

    if streaming:
        client = httpx.AsyncClient(timeout=_TIMEOUT)
        upstream = await client.send(
            client.build_request(request.method, url, content=body, headers=headers),
            stream=True,
        )

        async def relay():
            try:
                async for chunk in upstream.aiter_raw():
                    yield chunk
            finally:
                await upstream.aclose()
                await client.aclose()

        return StreamingResponse(
            relay(),
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "text/event-stream"),
        )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        upstream = await client.request(request.method, url, content=body, headers=headers)
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )
