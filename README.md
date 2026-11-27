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

## Models by hardware and task

Starting points, not a leaderboard. **Run** means the lab served it on that hardware; **measured**
means numbers are in [`docs/measured.md`](docs/measured.md); **suggested** means it fits by size
(file sizes from the download pages) and has not been run here yet. Every GGUF listed loads in the
pinned llama.cpp build.

Most current models think before answering (gpt-oss, Qwen3.5 and later, the R1 distills); they
are listed under reasoning when that is their strength, but they code too.

### RTX 5080, 16 GB

| Task | Model | File | Size | Status |
|---|---|---|---|---|
| General | Qwen2.5-14B-Instruct | `bartowski/Qwen2.5-14B-Instruct-GGUF` Q5_K_M | 10.5 GB | run |
| Reasoning | gpt-oss-20b | `ggml-org/gpt-oss-20b-GGUF` MXFP4 | 12.1 GB | suggested |
| Coding | Qwen3.5-9B | `unsloth/Qwen3.5-9B-GGUF` Q8_0 | 9.5 GB | suggested |

### RTX 5090, 32 GB

| Task | Model | File | Size | Status |
|---|---|---|---|---|
| Coding | Qwen3.6-35B-A3B | `unsloth/Qwen3.6-35B-A3B-GGUF` UD-Q4_K_M | 22.1 GB | suggested |
| Coding | Qwen3-Coder-30B-A3B-Instruct | `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` Q4_K_M | 18.6 GB | suggested |
| Reasoning, general | Qwen3.8-27B | `unsloth/Qwen3.8-27B-GGUF` UD-Q5_K_M | 19.8 GB | suggested |
| Reasoning | gpt-oss-20b, full 131k context | `ggml-org/gpt-oss-20b-GGUF` MXFP4 | 12.1 GB | suggested |

### RTX PRO 6000 Blackwell, 96 GB

| Task | Model | File | Size | Status |
|---|---|---|---|---|
| Coding, reasoning | gpt-oss-120b | `unsloth/gpt-oss-120b-GGUF` F16 (MXFP4 experts) | 65 GB | measured: passed the coding task in 95 s, 194 tok/s |
| Coding | Qwen3.8-Flash-Next | `unsloth/Qwen3.8-Flash-Next-GGUF` UD-Q3_K_XL | 89 GB in 4 files * | measured: the cleanest code, 112 tok/s |
| Reasoning | Qwen3.5-122B-A10B | `unsloth/Qwen3.5-122B-A10B-GGUF` UD-Q4_K_XL | 77 GB in 3 files | measured: 119 tok/s |
| General | Llama-3.3-70B-Instruct | Q5_K_M | about 50 GB | run |
| Astronomy | AstroSage-70B | Q5_K_M | 50.4 GB | measured: about 30 tok/s |

\* Qwen3.8-Flash-Next keeps part of its weights (an n-gram embedding) in system RAM under
llama.cpp, so it used 61 GiB of GPU memory at 131k context despite the file size. Give the host
plenty of RAM.

### Apple M3 Ultra, 96 GB unified (MLX)

| Task | Model | Hugging Face | On disk | Status |
|---|---|---|---|---|
| Coding | Qwen3-Coder-Next | `mlx-community/Qwen3-Coder-Next-4bit` | 42 GB | run |
| Coding | Qwen3.6-35B-A3B | `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` | 21.6 GB | suggested |
| Reasoning | DeepSeek-R1-Distill-Llama-70B | `mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit` | 37 GB | run |
| General | Qwen2.5-72B-Instruct | `mlx-community/Qwen2.5-72B-Instruct-4bit` | 38 GB | run |

Check the license on each model's page before you use it; they differ, and some restrict
commercial use.

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
