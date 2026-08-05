# Day 007: SGLang Serving Workflow / SGLang 服务流程

Date / 日期: 2026-06-11

## Topic / 主题

**English:** The request path through an LLM serving runtime, token-aware
scheduling, prefill/decode workload shapes, batching, KV-cache pressure, and
throughput/latency trade-offs.

**中文：** LLM serving runtime 中的请求路径、token-aware 调度、prefill/decode
负载形态、batching、KV-cache 压力以及吞吐/延迟权衡。

## Goal / 目标

**English:** Understand how scheduler, batching, KV cache, TTFT, TPOT,
throughput, and latency interact after a request enters SGLang.

**中文：** 理解请求进入 SGLang 后，scheduler、batching、KV cache、TTFT、TPOT、
throughput 与 latency 如何共同影响在线服务。

## 10 Concept Questions / 10 个概念问题

### 1. Request flow / 请求进入 runtime 的顺序

**Question (English):** Put these serving steps in a reasonable order:

**问题（中文）：** 将下面的 serving 步骤按合理顺序排列：

~~~text
A. 模型逐 token 生成输出
B. 请求进入 server
C. tokenizer 把文本变成 tokens
D. prefill 处理 prompt 并建立 KV cache
E. scheduler 决定请求什么时候运行、是否和其他请求 batch
~~~

**Explanation (English):** Models consume tokens rather than raw text, and
the scheduler normally needs token counts and resource estimates before making
batching decisions.

**解说（中文）：** 模型不能直接处理原始文本，需要先 tokenization。scheduler
通常需要 token 数量和资源需求等信息才能排队与 batching。

**Correct Answer (English):** `B -> C -> E -> D -> A`: receive the request,
tokenize it, schedule and batch it, prefill the prompt and build KV cache, then
decode output tokens.

**正确答案（中文）：** `B -> C -> E -> D -> A`：请求进入 server，tokenizer
把文本变成 tokens，scheduler 决定何时运行及如何 batch，prefill 建立 KV cache，
最后 decode 逐 token 生成输出。

### 2. Why the scheduler needs token counts / Scheduler 为何需要 token 数

**Question (English):** Why does prompt length matter to scheduling?

**问题（中文）：** 为什么 scheduler 需要知道 prompt 的 token 数量？

**Explanation (English):** Token count is a resource estimate, not merely
request metadata.

**解说（中文）：** prompt token 数量不是普通元数据，而是调度的重要资源估计。

**Correct Answer (English):** It influences prefill compute, KV-cache memory,
batch composition, and TTFT. Longer prompts are normally more expensive to
prefill, retain more K/V state, and take longer to produce a first token.

**正确答案（中文）：** token 数量影响 prefill 成本、KV cache 显存、batching
策略和 TTFT。prompt 越长，prefill 越重，需要保存的 K/V 越多，首 token 延迟
通常也越长。

### 3. Short versus long prompts / 短 prompt 与长 prompt

**Question (English):** How do these requests differ in system pressure?

**问题（中文）：** 下面两个请求对 serving 系统的压力有什么不同？

~~~text
Request A: prompt 长度 20 tokens
Request B: prompt 长度 8000 tokens
~~~

**Explanation (English):** A long prompt affects not only its own latency but
also memory capacity and scheduling for other requests.

**解说（中文）：** 长 prompt 不只让单个请求变慢，也影响显存占用和其他请求调度。

**Correct Answer (English):** A has light prefill, small KV cache, and usually
short TTFT. B has expensive prefill, large KV cache, and usually long TTFT; it
may need admission limits, queueing, or separate treatment.

**正确答案（中文）：** A 的 prefill 轻、KV cache 小、TTFT 通常短，容易与其他
请求调度。B 的 prefill 重、KV cache 大、TTFT 通常长，可能需要限制、排队或
单独处理。

### 4. Prefill-heavy versus decode-heavy / Prefill-heavy 与 decode-heavy

**Question (English):** Which requests are prefill-heavy, and which are
decode-heavy?

**问题（中文）：** 什么请求更 prefill-heavy？什么请求更 decode-heavy？

**Explanation (English):** Input length determines prefill pressure, while
output length determines decode pressure.

**解说（中文）：** 判断 prefill-heavy 主要看输入侧；判断 decode-heavy 主要看
输出侧。

**Correct Answer (English):** Long prompts, document context, or multimodal
inputs tend to be prefill-heavy. Requests generating many output tokens are
decode-heavy. An image increases input-side work but does not by itself imply
long decode.

**正确答案（中文）：** 长 prompt、长文档上下文或多模态输入更 prefill-heavy；
需要生成很多输出 token 的请求更 decode-heavy。图片增加输入侧成本，但不一定
代表 decode-heavy。

### 5. Why long outputs retain resources / 长输出为何持续占用资源

**Question (English):** Why does a decode-heavy request keep consuming
resources?

**问题（中文）：** 为什么 decode-heavy 长输出请求会持续占用系统资源？

**Explanation (English):** Decode advances one token at a time, with another
model step for every token.

**解说（中文）：** decode 不是一次完成，而是逐 token 生成，每一步都需要模型
继续运行。

**Correct Answer (English):** The request repeatedly joins decode batches,
retains its KV cache until completion, and performs one dependent step per
token. Higher TPOT extends the period for which those resources remain held.

**正确答案（中文）：** 请求每生成一个 token 都运行一次 decode step，持续加入
decode batch，且完成前不能释放 KV cache。TPOT 越高，资源占用时间越长。

### 6. Batching trade-offs / Batching 的吞吐与延迟权衡

**Question (English):** Why can batching improve throughput yet increase some
request latencies?

**问题（中文）：** 为什么 batching 能提高吞吐，却也可能增加某些请求的延迟？

**Explanation (English):** Batching fills GPU parallel capacity but can add
waiting and interference among heterogeneous requests.

**解说（中文）：** batching 更充分利用 GPU 并行能力，但等待和混合不同请求也会
产生延迟代价。

**Correct Answer (English):** Running requests together can raise utilization
and throughput. However, requests may wait for a batch; short work may be
delayed by long work; and a heavy prefill can increase TTFT for others.

**正确答案（中文）：** 多个请求一起运行可提高 GPU 利用率与吞吐，但请求可能等待
凑 batch，短请求可能被长请求拖慢，重 prefill 也可能增加其他请求的 TTFT。

### 7. Throughput versus latency / Throughput 与 latency

**Question (English):** What does each metric describe?

**问题（中文）：** throughput 和 latency 分别描述什么？

**Explanation (English):** One measures work completed per unit time; the
other measures time experienced by an individual request or stage.

**解说（中文）：** 一个看单位时间处理多少工作，另一个看单个请求或阶段花费多久。

**Correct Answer (English):** Throughput includes requests/s or tokens/s.
Latency includes TTFT, TPOT, and end-to-end request time. Larger batches may
raise throughput while increasing individual latency.

**正确答案（中文）：** throughput 是单位时间处理的工作量，例如 requests/s、
tokens/s；latency 是单个请求或阶段耗时，例如 TTFT、TPOT、end-to-end latency。
大 batch 可能提高 throughput，也可能增加 latency。

### 8. KV cache as resource management / KV cache 是资源管理问题

**Question (English):** Why is KV cache both an optimization and a resource
management concern?

**问题（中文）：** 为什么 KV cache 不只是性能优化，也是资源管理问题？

**Explanation (English):** KV cache trades GPU memory for less repeated
computation; it does not reduce memory use.

**解说（中文）：** KV cache 用显存换计算，并不是减少显存占用。

**Correct Answer (English):** More concurrent requests and longer contexts or
outputs retain more cache. The scheduler must admit, queue, reuse, or release
state under a finite memory budget.

**正确答案（中文）：** 并发越多、上下文或输出越长，KV cache 显存压力越大。
scheduler 必须在有限预算下决定哪些请求进入、等待，以及哪些 cache 复用或释放。

### 9. Latency sacrificed for throughput / 高吞吐可能牺牲的延迟

**Question (English):** Which latency metrics can worsen when a system
optimizes aggressively for tokens/s?

**问题（中文）：** 系统追求更高 throughput 时，哪些 latency 指标可能变差？

**Explanation (English):** Serving systems trade GPU utilization against
individual waiting time.

**解说（中文）：** serving 系统经常在 GPU 利用率和用户等待时间间权衡。

**Correct Answer (English):** TTFT, TPOT, end-to-end latency, and tail latency
can all increase. Waiting to form fuller batches may delay prefill and the
first token even while aggregate tokens/s improves.

**正确答案（中文）：** TTFT、TPOT、end-to-end latency 和 tail latency 都可能
上升。例如等待更多请求凑 batch 会推迟 prefill 和首 token，尽管总 tokens/s
提高。

### 10. Core serving-runtime intuition / Serving runtime 的核心直觉

**Question (English):** Why is a serving runtime more than “running a model”?

**问题（中文）：** 为什么 serving runtime 不只是“把模型跑起来”？

**Explanation (English):** Heterogeneous online requests must share finite GPU
compute and memory across different execution phases.

**解说（中文）：** 不同长度、不同阶段和不同输出需求的在线请求需要共享有限 GPU
计算与显存资源。

**Correct Answer (English):** SGLang uses a scheduler to manage batching, KV
cache, and GPU resources while balancing throughput, latency, TTFT, and TPOT.
It is fundamentally an online scheduling and resource-management system.

**正确答案（中文）：** SGLang 通过 scheduler 管理 batching、KV cache 与 GPU
资源，在 throughput/latency 间权衡并优化 TTFT、TPOT。它本质上是在线推理调度
与资源管理系统。

## Summary / 今日总结

- **English:** A request normally flows through server, tokenizer, scheduler,
  prefill, and decode.
  **中文：** 请求通常经历 server、tokenizer、scheduler、prefill 和 decode。
- **English:** Token counts estimate prefill cost, cache pressure, and TTFT.
  **中文：** token 数量用于估计 prefill 成本、cache 压力和 TTFT。
- **English:** Long input is prefill-heavy; long output is decode-heavy.
  **中文：** 长输入更 prefill-heavy；长输出更 decode-heavy。
- **English:** Batching and KV cache couple utilization, memory, throughput,
  and latency.
  **中文：** batching 与 KV cache 把利用率、显存、吞吐和延迟联系起来。
- **English:** Serving optimization must consider TTFT, TPOT, end-to-end, and
  tail latency rather than tokens/s alone.
  **中文：** serving 优化不能只看 tokens/s，还要看 TTFT、TPOT、端到端和尾延迟。

## Common Mistakes / 易错点

- **English:** Placing tokenization after prefill.
  **中文：** 把 tokenizer 放到 prefill 之后。
- **English:** Assuming KV cache reduces GPU-memory use.
  **中文：** 误以为 KV cache 减少显存占用。
- **English:** Treating multimodal input as necessarily decode-heavy.
  **中文：** 把多模态输入直接等同于 decode-heavy。
- **English:** Assuming a larger batch is always better.
  **中文：** 误以为 batch 越大越好。
- **English:** Optimizing throughput without measuring latency.
  **中文：** 只优化 throughput 而不测 latency。

## Next Steps / 下一步

- **English:** Add tokenizer, batching, throughput, latency, and tail-latency
  terms to the glossary.
  **中文：** 在 glossary 中补充 tokenizer、batching、throughput、latency 和
  tail latency。
- **English:** Run a minimal SGLang service and benchmark TTFT, TPOT, and
  throughput.
  **中文：** 跑通最小 SGLang 服务并测量 TTFT、TPOT 与 throughput。
