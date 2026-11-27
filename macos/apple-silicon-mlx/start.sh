#!/usr/bin/env bash
# Start mlx-lm's OpenAI-compatible server on localhost. Run by the LaunchAgent in mlx-server.plist,
# or by hand.
set -euo pipefail

ROOT="${MLX_ROOT:-$HOME/.local/share/mlx-server}"
MODEL="${MLX_MODEL:-mlx-community/Qwen3-Coder-Next-4bit}"
PORT="${MLX_PORT:-8081}"
MAX_TOKENS="${MLX_MAX_TOKENS:-32768}"

# 127.0.0.1 only: mlx_lm.server has no API key. For other machines, use auth-proxy/.
exec "$ROOT/.venv/bin/mlx_lm.server" \
    --model "$MODEL" \
    --host 127.0.0.1 \
    --port "$PORT" \
    --max-tokens "$MAX_TOKENS"
