# What we measured

Numbers from the lab's own runs. Each comes with its conditions, because a tokens-per-second
figure without them cannot be compared with anything. A blank or "not measured" means exactly that:
nothing here is estimated.

## RTX PRO 6000 Blackwell (96 GB): five models on one coding task (2026-11-20)

**Conditions.** llama.cpp build b11058 (the image pinned in `nvidia/rtx-pro-6000/compose.yaml`),
all layers on the GPU, q8_0 KV cache, flash attention on. Card capped at 400 W unless marked.
Generation speed: one request at a time, a code-writing prompt of about 600 tokens and about 1,400
tokens generated. "In use" is GPU memory in use with the model loaded at that context.

**The task.** Each model was the backend for the OpenCode coding agent and given the same job:
write a small Rust crate that parses an ADIF (amateur-radio log) file and computes Maidenhead-grid
distance and bearing, with tests. The result was then checked independently of the model: `cargo
build`, `cargo test`, `cargo clippy -D warnings`, the program's real output against a known value
(DN13 to FN31: 3571.8 km at 78.1°), and whether the model had weakened a test to make it pass.

| Model | Quantization | Result | Time | Generation | In use at context |
|---|---|---|---|---|---|
| gpt-oss-120b | MXFP4 | pass | 95 s | 194 tok/s | 67 GiB at 131k |
| Qwen3.8-Flash-Next | UD-Q3_K_XL | pass, the cleanest code | 6.6 min | 112 tok/s | 61 GiB at 131k |
| Qwen3.5-122B-A10B | UD-Q4_K_XL | pass, but loosened a test * | 16 min | 119 tok/s | 80 GiB at 131k |
| Devstral 2 123B | Q4_K_M | fail at the 60 min limit * | 60 min | 11 tok/s | 83 GiB at 64k |
| Qwen3-Coder-30B-A3B | Q8_0 | fail, parsed 0 records * | | 235 tok/s at 600 W | 38 GiB at 131k |

\* These three runs were given a wrong expected distance (3413.7 km). Qwen3.5 computed the right
value and quietly loosened the test to pass; the others chased the wrong number. The prompt was
corrected before the gpt-oss-120b and Qwen3.8 runs. So the failures are partly the test's fault,
and the table should be read with that in mind.

What we took from it: gpt-oss-120b was right and about four times faster than the next model that
was right, so it became the default. The dense 123B model (Devstral 2) is an order of magnitude
slower than the mixture-of-experts models of similar size, because every token reads all of its
weights.

## RTX PRO 6000 Blackwell: 70B dense models (2026, earlier build)

From the *Sovereign Infrastructure* paper (doi:10.5281/zenodo.21003263), llama.cpp, single request:

| Model | Quantization | Size | Generation |
|---|---|---|---|
| AstroSage-70B | Q5_K_M | 50.4 GB | 29.7 to 30.8 tok/s |
| Llama-3.1-70B | Q5_K_M | about 50 GB | about 30 tok/s |

## RTX 5080 (16 GB)

Qwen2.5-14B-Instruct Q5_K_M at 32k context ran as a lab service. Speed not measured.

## RTX 5090 (32 GB)

Not measured. The lab had a 5090 before the RTX PRO 6000, but no inference numbers from it were
kept.

## Apple M3 Ultra (96 GB), MLX

Ran as a lab service with `mlx-lm` 0.32.2 and `mlx` 0.32.4: Qwen2.5-72B-Instruct 4-bit (38 GB on
disk), Qwen3-Coder-Next 4-bit (42 GB) and DeepSeek-R1-Distill-Llama-70B 4-bit (37 GB). Speed not
measured.
