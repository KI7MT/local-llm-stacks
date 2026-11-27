# Apple Silicon with MLX

`mlx-lm`'s server, running natively on the Mac. Docker is not an option here: containers on macOS
run in a Linux VM with no access to the Metal GPU, so a model in Docker on a Mac runs on the CPU.

Run in the lab on an M3 Ultra with 96 GB, `mlx-lm` 0.32.2.

| Model (Hugging Face) | On disk | Notes |
|---|---|---|
| `mlx-community/Qwen2.5-72B-Instruct-4bit` | 38 GB | general reasoning |
| `mlx-community/Qwen3-Coder-Next-4bit` | 42 GB | coding |
| `mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit` | 37 GB | reasoning, thinks before answering |

A 96 GB Mac gives the GPU about 72 GB by default and shares the rest with everything else; see
[`../../docs/sizing.md`](../../docs/sizing.md#unified-memory-apple-silicon).

## Install

```bash
mkdir -p ~/.local/share/mlx-server && cd ~/.local/share/mlx-server
python3 -m venv .venv                     # Python 3.12 works; use Homebrew's or uv's
.venv/bin/pip install "mlx-lm==0.32.2"
```

The model downloads into `~/.cache/huggingface` the first time the server starts.

## Run it by hand

```bash
.venv/bin/mlx_lm.server --model mlx-community/Qwen3-Coder-Next-4bit \
  --host 127.0.0.1 --port 8081 --max-tokens 32768
```

Check it:

```bash
curl -s http://127.0.0.1:8081/v1/models
```

## Run it at login (launchd)

[`start.sh`](start.sh) starts the server; [`mlx-server.plist`](mlx-server.plist) is a LaunchAgent
that runs it at login and restarts it if it stops.

```bash
cp start.sh ~/.local/share/mlx-server/ && chmod +x ~/.local/share/mlx-server/start.sh
sed "s|__HOME__|$HOME|g" mlx-server.plist > ~/Library/LaunchAgents/local.mlx-server.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.mlx-server.plist
```

Stop it with `launchctl bootout gui/$(id -u)/local.mlx-server`. The model is set in `start.sh` or
by `MLX_MODEL` in the plist.

## No API key: keep it on localhost

`mlx_lm.server` has no API-key option, and its own documentation says it is not meant for
production. Left on `127.0.0.1`, only programs on this Mac can use it, which is the setup here.

To reach it from other machines, do not just bind it to the LAN. Put the small authenticating
proxy in [`auth-proxy/`](auth-proxy/) in front: the server stays on localhost, the proxy listens on
the LAN and checks a Bearer key held in the macOS Keychain. Then follow
[`../../docs/security.md`](../../docs/security.md) for the firewall.
