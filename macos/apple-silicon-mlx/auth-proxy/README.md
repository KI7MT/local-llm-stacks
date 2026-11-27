# Auth proxy for mlx_lm.server

`mlx_lm.server` cannot check an API key. This proxy does it in front of the server: the server
stays on `127.0.0.1:8081`, the proxy listens on the address you choose and forwards `/v1/*` to the
server only for requests carrying the right `Authorization: Bearer <key>`. Streaming responses
pass through as they arrive.

The key lives in the macOS Keychain, not in a file or an environment variable.

## Install

```bash
cd ~/.local/share/mlx-server
cp -r <this repo>/macos/apple-silicon-mlx/auth-proxy .
.venv/bin/pip install -r auth-proxy/requirements.txt

openssl rand -hex 32                                   # the key; give it to your clients
.venv/bin/python -m keyring set mlx-server api-key     # paste it at the prompt
```

## Run

```bash
cd ~/.local/share/mlx-server/auth-proxy
UPSTREAM_PORT=8081 ../.venv/bin/uvicorn proxy:app --host <this Mac's LAN address> --port 8000
```

Check it from another machine:

```bash
curl -s http://<mac>:8000/v1/models -H "Authorization: Bearer <key>"   # 200
curl -s -o /dev/null -w "%{http_code}\n" http://<mac>:8000/v1/models  # 401
```

Then limit who can reach port 8000 with the macOS firewall or your network's, and read
[`../../../docs/security.md`](../../../docs/security.md). The proxy authenticates; it does not
make the server safe to put on the internet.

The first time the proxy reads the Keychain, macOS asks whether Python may read the item; allow it
(**Always Allow** if it runs under launchd).
