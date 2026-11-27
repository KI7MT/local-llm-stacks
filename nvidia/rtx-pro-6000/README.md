# RTX PRO 6000 Blackwell (96 GB)

One llama.cpp server in Docker, the whole model on the GPU. 96 GB holds a 120B-class
mixture-of-experts model at its full context, or a 70B dense model at 5 bits.

| `.env` example | Model | In use at context | Generation | Notes |
|---|---|---|---|---|
| `.env.example` | gpt-oss-120b (MXFP4) | 67 GiB at 131k | 194 tok/s | the lab's current choice |
| `.env.qwen3-coder-30b.example` | Qwen3-Coder-30B-A3B Q8 | 38 GiB at 131k | 235 tok/s (600 W) | fastest; failed the coding task |

Conditions for the numbers, and the other models tried, are in
[`../../docs/measured.md`](../../docs/measured.md).

## Run

Host setup first: [`../README.md`](../README.md).

```bash
cp .env.example .env
openssl rand -hex 32             # paste into LLAMA_API_KEY in .env
# download the model named in .env, into MODEL_DIR (about 65 GB for gpt-oss-120b)
docker compose up -d
docker compose logs -f           # loading takes minutes; wait for "server is listening"
```

Check it:

```bash
KEY=$(grep ^LLAMA_API_KEY .env | cut -d= -f2)
curl -s http://127.0.0.1:8080/v1/models -H "Authorization: Bearer $KEY"
nvidia-smi --query-gpu=memory.used,power.draw,power.limit --format=csv
```

## Notes from running it

- **One model at a time.** Switching is `docker compose down`, edit `.env`, `up -d`. Two models at
  once fit only when their sum, KV cache included, is under about 90 GiB; check with
  [`../../docs/sizing.md`](../../docs/sizing.md) first.
- **Reasoning models think before they answer.** gpt-oss and the Qwen3.x thinking models put that
  in `reasoning_content`. A reply with `finish_reason: length` and empty `content` means the token
  budget ran out while thinking: raise `max_tokens` in the client.
- **Power.** At 600 W this card can trip a UPS; all but one number here was taken capped at 400 W
  ([`../README.md`](../README.md#power)).
