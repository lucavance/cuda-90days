# Day 004: SGLang Basics / SGLang 基础

Date / 日期: 2026-06-09

## Topic / 主题

**English:** SGLang's role in LLM/VLM serving, offline versus online
inference, prefill and decode, KV cache, scheduling, TTFT/TPOT, prefix reuse,
and the relationship between runtime and CUDA optimization.

**中文：** SGLang 在 LLM/VLM serving 中的定位、离线与在线推理、prefill 与
decode、KV cache、调度、TTFT/TPOT、前缀复用，以及 runtime 与 CUDA 优化的
关系。

## Goal / 目标

**English:** Build a lightweight conceptual map of an LLM serving runtime
without diving into SGLang source code yet.

**中文：** 暂不深入 SGLang 源码，先建立 LLM serving runtime 的轻量概念地图。

## 10 Concept Questions / 10 个概念问题

### 1. SGLang's role / SGLang 的定位

**Question (English):** Which category best describes SGLang, and what
problems does it primarily solve?

**问题（中文）：** SGLang 大致属于哪一类工具？它主要解决什么问题？

~~~text
A. CUDA kernel 编译器
B. Python 数据分析库
C. LLM / VLM 推理与 serving 框架
D. 操作系统调度器
~~~

**Explanation (English):** SGLang sits between models and service systems. It
is neither a low-level CUDA compiler nor a general data-analysis library.

**解说（中文）：** SGLang 位于模型和服务系统之间，不是底层 CUDA 编译器，也
不是通用数据分析库。

**Correct Answer (English):** C. SGLang is an LLM/VLM inference and serving
framework. It accepts and schedules requests, manages KV cache, organizes
prefill/decode execution, exposes APIs, and improves throughput and latency.

**正确答案（中文）：** 选 C。SGLang 是面向 LLM/VLM 的推理与 serving 框架，
用于接收和调度请求、管理 KV cache、组织 prefill/decode、提供 API 服务，并
改善吞吐与延迟。

### 2. Offline inference versus online serving / 离线推理与在线服务

**Question (English):** What is the difference between `offline inference`
and `online serving`?

**问题（中文）：** 在 LLM serving 中，`offline inference` 和
`online serving` 有什么区别？

**Explanation (English):** Both run model inference, but offline work is
batch-oriented while online serving is request- and latency-oriented.

**解说（中文）：** 两者都运行模型推理，但离线推理偏批处理，在线 serving 偏
服务化和请求调度。

**Correct Answer (English):** Offline inference processes a prepared batch of
prompts and emphasizes total throughput. Online serving exposes an API and
waits for user requests, emphasizing latency, concurrency, stability, and
scheduling.

**正确答案（中文）：** offline inference 一次性离线处理一批 prompt，更关注
总吞吐；online serving 部署 API 服务等待用户请求，更关注延迟、并发、稳定性和
请求调度。

### 3. Prefill and decode / Prefill 与 decode

**Question (English):** What does each phase do during LLM inference?

**问题（中文）：** LLM 推理中的 `prefill` 和 `decode` 分别做什么？

**Explanation (English):** Processing the prompt and generating output use
different computation patterns.

**解说（中文）：** prompt 输入和输出生成不是同一种计算形态。prompt 通常先被
整体处理，随后模型逐 token 生成答案。

**Correct Answer (English):** Prefill processes the prompt tokens together
and builds the initial KV cache. Decode reuses that cache and generates output
one token at a time.

**正确答案（中文）：** prefill 阶段整体处理 prompt tokens 并建立初始 KV
cache；decode 阶段复用已有 KV cache，逐 token 生成输出。

### 4. Why distinguish prefill from decode? / 为什么区分 prefill 与 decode

**Question (English):** How do the phases differ computationally, and why does
the runtime care?

**问题（中文）：** 两个阶段在计算特征上有什么不同？为什么 runtime 要特别区分
它们？

**Explanation (English):** Their input sizes, available parallelism, and
bottlenecks differ, so they benefit from different scheduling decisions.

**解说（中文）：** prefill 与 decode 的输入规模、并行度和性能瓶颈不同，因此
runtime 调度策略也不同。

**Correct Answer (English):** Prefill handles many input tokens at once, has
higher parallelism, resembles large matrix work, and strongly affects first
token latency. Decode generates one dependent token per step, has less
parallelism, repeats model execution, and strongly affects TPOT.

**正确答案（中文）：** prefill 一次处理很多输入 token，并行度较高，更像大批量
矩阵计算，通常影响首 token 延迟；decode 每步生成一个依赖前一步的 token，
并行度相对低，需要反复调用模型，通常影响 TPOT。

### 5. What is KV cache? / 什么是 KV cache

**Question (English):** What does KV cache store, and why is decode especially
dependent on it?

**问题（中文）：** KV cache 缓存什么？为什么 decode 阶段特别依赖它？

**Explanation (English):** Every token produces key/value representations in
Transformer attention. Recomputing all historical representations on every
decode step would be wasteful.

**解说（中文）：** Transformer attention 中每个 token 都会产生 Key/Value
表示。如果每一步都重新计算历史 token 的 K/V，会非常浪费。

**Correct Answer (English):** It stores previously computed key/value states
for historical tokens. Each decode step reuses them and computes only the new
token's states, avoiding repeated work over the full context.

**正确答案（中文）：** KV cache 保存已经计算过的历史 token 的 Key/Value
表示。decode 每步复用历史 K/V，只计算新 token 的状态，避免重复处理完整上下文。

### 6. Why KV cache consumes GPU memory / KV cache 为何占用显存

**Question (English):** Why can KV cache consume substantial GPU memory?
Consider batch size, sequence length, layers, heads/hidden size, and dtype.

**问题（中文）：** 为什么 KV cache 会占用大量显存？请从 batch size、sequence
length、layer 数、heads/hidden size 和 dtype 等角度解释。

**Explanation (English):** KV cache contains per-layer, per-request, per-token
intermediate state rather than one small object.

**解说（中文）：** KV cache 不是单个小对象，而是每层、每个请求、每个历史 token
都要保存的中间状态。

**Correct Answer (English):** Its size grows with batch size, sequence length,
layer count, attention dimensions, and bytes per value. In serving systems it
can become a major memory consumer alongside model weights.

**正确答案（中文）：** KV cache 显存占用会随 batch size、sequence length、
layer 数、hidden size/attention heads 和 dtype 增长。在 serving 系统中，它
可能与模型权重一样成为主要显存压力。

### 7. Why a scheduler is needed / 为什么需要 scheduler

**Question (English):** Why not immediately run every arriving request by
itself?

**问题（中文）：** 为什么不简单地“来一个请求，立刻单独跑一个请求”？

**Explanation (English):** Online requests vary in count, length, and phase,
while GPU compute and memory are limited.

**解说（中文）：** 在线请求的数量、长度和阶段都不同，而 GPU 显存与计算资源
有限，需要在吞吐和延迟间权衡。

**Correct Answer (English):** The scheduler decides which requests run
together and when. Batching improves throughput; coordinated prefill/decode
execution and KV-memory management balance request latency, GPU utilization,
and system throughput.

**正确答案（中文）：** scheduler 决定哪些请求在何时一起运行。它通过 batching
提高吞吐，协调 prefill/decode，管理 KV cache 显存，并在请求延迟、GPU 利用率和
系统吞吐之间做决策。

### 8. TTFT and TPOT / TTFT 与 TPOT

**Question (English):** What do the two common serving metrics mean?

**问题（中文）：** LLM serving 中常见的 TTFT 和 TPOT 分别是什么意思？

**Explanation (English):** Interactive generation must measure both when the
first response appears and how smoothly later tokens arrive.

**解说（中文）：** 在线生成式服务既要关注用户何时看到第一个 token，也要关注
后续 token 输出是否流畅。

**Correct Answer (English):** TTFT is Time To First Token, from request
submission to the first output token. TPOT is Time Per Output Token during
decode. TTFT determines perceived startup delay; TPOT determines generation
smoothness.

**正确答案（中文）：** TTFT 是 Time To First Token，表示请求发出到收到第一个
输出 token 的时间；TPOT 是 Time Per Output Token，表示 decode 阶段平均每个
输出 token 的耗时。TTFT 影响“何时开始响应”，TPOT 影响输出流畅度。

### 9. RadixAttention and prefix cache / RadixAttention 与 prefix cache

**Question (English):** What problem does prefix reuse solve, and why is
reusing an identical prefix valuable?

**问题（中文）：** RadixAttention/prefix cache 大致解决什么问题？为什么复用
相同前缀有价值？

**Explanation (English):** Requests often share system prompts, tool
instructions, document context, or few-shot examples. Re-prefilling the same
tokens wastes compute.

**解说（中文）：** 很多请求共享 system prompt、工具说明、文档上下文或 few-shot
examples。每次从头 prefill 会浪费计算。

**Correct Answer (English):** Prefix caching reuses KV states for the same
token prefix, reducing repeated prefill, TTFT, and compute while improving
throughput. The intuition is: do not repeatedly process context already
processed.

**正确答案（中文）：** prefix cache 复用相同 token 前缀对应的 KV cache，减少
重复 prefill、降低 TTFT、提升吞吐并节省计算。直觉是：不要重复理解已经理解过的
上下文。

### 10. SGLang and CUDA optimization / SGLang 与 CUDA 优化

**Question (English):** Why should a CUDA learner understand SGLang, and how
are runtime optimization and kernel optimization related?

**问题（中文）：** 从 CUDA/GPU 学习角度看，为什么要了解 SGLang？serving
runtime 与底层 kernel 优化有什么关系？

**Explanation (English):** They optimize different layers of the same
end-to-end inference path. A faster isolated kernel may not improve the real
service if another layer dominates.

**解说（中文）：** CUDA kernel 优化和 serving runtime 优化处在同一条端到端
推理链路的不同层。只看单个 kernel，可能无法判断优化对真实服务是否有效。

**Correct Answer (English):** Kernels determine how individual operators run;
SGLang determines how requests enter the GPU, batch, consume KV cache, and
alternate between prefill and decode. Kernel work improves local operator
efficiency, while runtime work improves end-to-end serving efficiency.

**正确答案（中文）：** CUDA kernel 决定单个底层算子如何执行；SGLang 决定请求
如何进入 GPU、如何 batch、如何使用 KV cache，以及如何调度 prefill/decode。
kernel 优化解决局部算子效率，runtime 优化解决端到端推理效率。

## Summary / 今日总结

- **English:** SGLang is an LLM/VLM inference and serving framework rather
  than a CUDA compiler.
  **中文：** SGLang 是 LLM/VLM 推理与 serving 框架，而不是 CUDA 编译器。
- **English:** Prefill processes the prompt and initializes KV cache; decode
  reuses it while producing tokens.
  **中文：** prefill 处理 prompt 并建立 KV cache；decode 复用它逐 token 生成。
- **English:** KV cache capacity and scheduling couple memory, latency,
  concurrency, and throughput.
  **中文：** KV cache 容量与调度把显存、延迟、并发和吞吐联系起来。
- **English:** TTFT and TPOT describe startup and streaming latency.
  **中文：** TTFT 与 TPOT 分别描述启动响应与流式生成延迟。
- **English:** Prefix caching reduces repeated prefill for token-identical
  prefixes.
  **中文：** prefix cache 减少 token 完全相同前缀的重复 prefill。
- **English:** Runtime and kernel optimization are complementary layers of an
  end-to-end inference system.
  **中文：** runtime 优化与 kernel 优化是端到端推理系统中的互补层次。

## Common Mistakes / 易错点

- **English:** Treating SGLang as a kernel compiler.
  **中文：** 把 SGLang 当成 CUDA kernel 编译器。
- **English:** Describing KV cache as a mapping from the current token to the
  next token instead of stored key/value states.
  **中文：** 把 KV cache 当成“当前 token 到下一个 token 的映射”，而不是历史
  token 的 Key/Value 中间状态。
- **English:** Applying the same performance intuition to prefill and decode.
  **中文：** 用同一种性能直觉理解 prefill 和 decode。
- **English:** Treating scheduling as simple queue order rather than a
  resource and latency policy.
  **中文：** 把 scheduler 只理解为排队，而不是显存、计算、吞吐和延迟策略。

## Next Steps / 下一步

- **English:** Continue with CUDA global-memory access and coalescing.
  **中文：** 继续学习 CUDA global memory 与 coalescing。
- **English:** Run a minimal SGLang serving demo later.
  **中文：** 后续跑通最小 SGLang serving demo。
- **English:** Record model launch parameters, GPU-memory use, TTFT, and TPOT
  for one DeepSeek deployment.
  **中文：** 记录一次 DeepSeek 部署的启动参数、显存占用、TTFT 和 TPOT。
