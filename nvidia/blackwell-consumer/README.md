# GeForce Blackwell: RTX 5080 and RTX 5090

One llama.cpp server in Docker, everything on the GPU. The 5080 and the 5090 are the same
architecture (compute capability 12.0), so they share `compose.yaml`; only the model and context
differ, in `.env`.

| Card | Memory | Example model | Context | Status |
|---|---|---|---|---|
| RTX 5080 | 16 GB | Qwen2.5-14B-Instruct Q5_K_M (10.5 GB) | 32k | run in the lab |
| RTX 5090 | 32 GB | Qwen3-Coder-30B-A3B-Instruct Q4_K_M (about 18.6 GB) | 64k | not measured yet |

## Run

Host setup first: [`../README.md`](../README.md).

```bash
cp .env.5080.example .env        # or .env.5090.example
openssl rand -hex 32             # paste into LLAMA_API_KEY in .env
# download the model named in .env, into MODEL_DIR
docker compose up -d
docker compose logs -f           # wait for "server is listening"
```

Check it:

```bash
KEY=$(grep ^LLAMA_API_KEY .env | cut -d= -f2)
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hello in five words."}]}'
```

## Did the whole model load?

A server can answer while a model only partly fit. Check that the memory in use is at least the
model file's size:

```bash
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
curl -s http://127.0.0.1:8080/props -H "Authorization: Bearer $KEY" | grep -o '"n_ctx":[0-9]*'
```

`n_ctx` should equal `CTX` from `.env`.

## Picking another model

16 GB holds a dense model up to about 14B at 4 to 5 bits with a modest context; 32 GB holds about
32B dense, or a mixture-of-experts model like the one above. The arithmetic, so you can check
before a long download: [`../../docs/sizing.md`](../../docs/sizing.md).
