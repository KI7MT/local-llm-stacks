# local-llm-stacks

Local LLM inference stacks, one per hardware variant: the configurations used for the self-hosted
inference described in the KI7MT Sovereign AI Lab papers, written up so anyone with the same card can
run the same thing.

Every stack serves an **OpenAI-compatible API** (`/v1/chat/completions`, `/v1/models`), so any
client that speaks that API works against it: OpenCode, Open WebUI, `curl`, the OpenAI SDKs with a
changed base URL.

| Hardware | Memory | Engine | How it runs | Status |
|---|---|---|---|---|
| NVIDIA RTX 5080 | 16 GB GDDR7 | llama.cpp (CUDA) | Docker Compose | run in the lab |
| NVIDIA RTX 5090 | 32 GB GDDR7 | llama.cpp (CUDA) | Docker Compose | same stack as the 5080, **not measured yet** |
| NVIDIA RTX PRO 6000 Blackwell | 96 GB GDDR7 | llama.cpp (CUDA) | Docker Compose | run and measured in the lab |
| Apple M3 Ultra | 96 GB unified | MLX (`mlx-lm`) | native, launchd | run in the lab |

## Layout

```
nvidia/                      host setup shared by every NVIDIA variant
  rocky-9/                   building Rocky Linux 9 for Blackwell: driver, DKMS, the pitfalls
  blackwell-consumer/        RTX 5080 and RTX 5090: one Compose file, an .env per card
  rtx-pro-6000/              RTX PRO 6000 Blackwell 96 GB
macos/
  apple-silicon-mlx/         Apple Silicon with MLX, plus an optional auth proxy
docs/
  sizing.md                  what fits: weights + KV cache, context, quantization
  measured.md                what we measured, and under which conditions
  security.md                the defaults here, and why
```

## Quick start (NVIDIA)

1. Prepare the host once: [`nvidia/README.md`](nvidia/README.md) (driver, NVIDIA Container
   Toolkit, Docker Compose); on Rocky Linux 9, start with [`nvidia/rocky-9/`](nvidia/rocky-9/README.md).
2. Pick your card's directory, copy its `.env` example, download the model it names, set a key:

   ```bash
   cd nvidia/rtx-pro-6000
   cp .env.example .env            # then edit MODEL_DIR and LLAMA_API_KEY
   docker compose up -d
   curl -s http://127.0.0.1:8080/v1/models -H "Authorization: Bearer $(grep ^LLAMA_API_KEY .env | cut -d= -f2)"
   ```

On a Mac, Docker cannot reach the GPU (Metal), so the Apple Silicon stack runs natively:
[`macos/apple-silicon-mlx/README.md`](macos/apple-silicon-mlx/README.md).

## Defaults that matter

- **Listens on `127.0.0.1` only** and **requires an API key.** Opening it to a LAN is a deliberate
  edit; see [`docs/security.md`](docs/security.md). Never forward these ports to the internet.
- **Images are pinned by digest**, so the server that comes back after a reboot or a pull is the
  one you tested. Upgrading is a deliberate edit too.
- **Everything is offloaded to the GPU** (`--n-gpu-layers 999`); a model that does not fit is a
  wrong model choice, not something to spill to the CPU quietly. [`docs/sizing.md`](docs/sizing.md)
  shows how to check before downloading.

## Papers

- *Sovereign Infrastructure*: the lab these stacks run in.
  [doi:10.5281/zenodo.21003263](https://doi.org/10.5281/zenodo.21003263)

## License

Apache-2.0. The models are not part of this repository; each has its own license, which you
accept when you download it.
