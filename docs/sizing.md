# What fits

GPU memory has to hold two things: the **weights** and the **KV cache**. Forgetting the second is
the usual mistake; it is how a model that "should fit" fails at load, or loads and then fails on the
first long prompt.

## Weights

Roughly the size of the GGUF file. As a rule of thumb, per billion parameters:

| Quantization | Bits per weight (about) | GB per billion parameters |
|---|---|---|
| Q8_0 | 8.5 | 1.06 |
| Q5_K_M | 5.7 | 0.71 |
| Q4_K_M | 4.8 | 0.60 |
| MXFP4 (gpt-oss) | 4.25 | 0.53 |

So a 14B model at Q5_K_M is about 10 GB, and a 70B at Q5_K_M about 50 GB. The file size on the
download page is the better number when you have it.

## KV cache

Grows linearly with context, and depends on the model's shape, not its parameter count:

```
KV bytes = 2 × layers × kv_heads × head_dim × context × bytes_per_value
```

`bytes_per_value` is 2 for f16 and about 1.06 for the `q8_0` cache these stacks use, which halves
the cache for a quality cost that is hard to see. The model's `config.json` (or the GGUF metadata)
gives `num_hidden_layers`, `num_key_value_heads` and `head_dim`.

Example: a model with 48 layers, 8 KV heads and a head dimension of 128, at 32k context with a
`q8_0` cache: 2 × 48 × 8 × 128 × 32768 × 1.06 ≈ 3.4 GB.

## Headroom

Leave 1 to 2 GB for the CUDA context and compute buffers. On a 16 GB card that means about 14 GB
for weights plus cache.

## Mixture-of-experts models

A mixture-of-experts model needs memory for **all** its parameters but reads only the **active**
ones per token. gpt-oss-120b has about 5B active, Qwen3-Coder-30B-A3B about 3B. That is why they
generate far faster than dense models of the same size, and why "120B" on a 96 GB card is
practical at all.

## Unified memory (Apple Silicon)

macOS lets the GPU use only part of unified memory by default, about 75% on machines with more than
64 GB, and the system and your applications share the rest. On a 96 GB Mac, plan on 60 to 70 GB for
the model and its cache. The limit can be raised (`sudo sysctl iogpu.wired_limit_mb=<MB>`, until
reboot), at the expense of everything else on the machine.

## Check before you download

The server prints what it allocated when it loads. After loading, `nvidia-smi` shows the total in
use, and llama.cpp's `/props` endpoint reports the context it actually got (`n_ctx`). If `n_ctx` is
lower than you asked for, or the memory in use is less than the file size, the model did not load
as configured.
