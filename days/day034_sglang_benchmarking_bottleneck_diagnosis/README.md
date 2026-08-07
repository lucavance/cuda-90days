# Day 034: SGLang Benchmarking and Bottleneck Diagnosis / SGLang 基准测试与瓶颈定位

Date / 日期: 2026-08-07

## Topic / 主题

**English:** SGLang serving benchmarks: controlled comparisons, TTFT, TPOT,
ITL, end-to-end latency, throughput, concurrency, request rate, warmup and
cache state, prefix-cache experiments, chunked prefill, CUDA Graph,
speculative decoding, and saturation diagnosis.

**中文：** SGLang 服务基准测试：受控对比、TTFT、TPOT、ITL、端到端延迟、
吞吐量、并发数、请求速率、预热与缓存状态、前缀缓存实验、chunked prefill、
CUDA Graph、推测解码以及容量饱和诊断。

## Goal / 目标

**English:** Learn to design a reproducible SGLang benchmark, interpret
latency and throughput metrics according to the workload, distinguish arrival
rate from in-flight concurrency, and use metric patterns to form and validate
a bottleneck hypothesis.

**中文：** 学会设计可复现的 SGLang benchmark，根据工作负载解释延迟与吞吐
指标，区分请求到达速率与在途并发量，并依据指标模式提出和验证瓶颈假设。

## Core Mental Model / 核心思维模型

**English:** A benchmark result is meaningful only when the workload and test
state are controlled. TTFT describes how quickly a response starts, TPOT and
ITL describe decode speed and streaming smoothness, end-to-end latency
describes completion time, and throughput describes system capacity. Changes
in these metrics must be interpreted together with queueing, cache state, GPU
utilization, and workload shape.

**中文：** 只有在工作负载与测试状态受到控制时，benchmark 结果才有意义。
TTFT 描述响应多快开始，TPOT 与 ITL 描述 decode 速度和流式输出平滑度，端到端
延迟描述完成时间，吞吐量描述系统容量。解释这些指标的变化时，必须同时考虑
排队、缓存状态、GPU 利用率与工作负载形态。

## 10 Concept Questions / 10 个概念问题

### 1. Controlled performance comparisons / 受控性能对比

**Question (English):** Configuration A reaches 1,000 tokens/s and
configuration B reaches 1,300 tokens/s, but the two runs use different input
lengths, output lengths, and concurrency levels. Can B be declared faster?
Why or why not?

**问题（中文）：** 配置 A 达到 1,000 tokens/s，配置 B 达到 1,300 tokens/s，
但两轮测试使用了不同的输入长度、输出长度与并发数。能否据此断定 B 更快？
为什么？

**Explanation (English):** Input length changes prefill work, output length
changes decode work, and concurrency changes batching, queueing, and resource
pressure. A throughput difference can therefore come from the workload rather
than the configuration being evaluated.

**解说（中文）：** 输入长度会改变 prefill 工作量，输出长度会改变 decode
工作量，并发数会改变 batching、排队与资源压力。因此吞吐量差异可能来自工作
负载，而不是被评估的配置本身。

**Correct Answer (English):** No. A valid A/B comparison keeps the model,
hardware, precision, input/output-length distribution, request order,
concurrency or request rate, cache state, warmup procedure, and measurement
duration consistent. The target configuration change should be the primary
independent variable, and repeated runs should be used to check variance.

**正确答案（中文）：** 不能。有效的 A/B 对比应保持模型、硬件、精度、输入与
输出长度分布、请求顺序、并发数或请求速率、缓存状态、预热过程和测量时长一致。
目标配置变化应是主要自变量，并通过多轮重复测试检查波动。

### 2. Throughput versus interactive latency / 吞吐量与交互延迟

**Question (English):** Under the same workload, A reaches 1,000 tokens/s
with 100 ms TTFT, while B reaches 1,300 tokens/s with 300 ms TTFT. Is B always
better? Which configuration may suit online chat and which may suit offline
batch inference?

**问题（中文）：** 在相同工作负载下，A 的吞吐量为 1,000 tokens/s、TTFT 为
100 ms；B 的吞吐量为 1,300 tokens/s、TTFT 为 300 ms。B 是否一定更好？在线
聊天与离线批量推理可能分别选择哪个配置？

**Explanation (English):** Throughput measures aggregate capacity, whereas
TTFT measures how long a user waits before output begins. Improving one may
degrade the other because larger batches can increase GPU efficiency while
also adding queueing or scheduling delay.

**解说（中文）：** 吞吐量衡量系统总体容量，TTFT 衡量用户在输出开始前等待
多久。更大的 batch 可能提高 GPU 效率，同时增加排队或调度延迟，因此改善一个
指标可能会损害另一个指标。

**Correct Answer (English):** B is not unconditionally better. Latency-sensitive
online chat may prefer A because its response begins sooner. Offline batch
inference may prefer B because it completes more aggregate work per unit time.
The final choice must also respect TPOT, end-to-end latency, tail latency, and
the service-level objective.

**正确答案（中文）：** B 并非无条件更好。延迟敏感的在线聊天可能偏向 A，因为
它更快开始响应；离线批量推理可能偏向 B，因为它单位时间完成的总体工作更多。
最终选择还必须满足 TPOT、端到端延迟、尾延迟与服务等级目标。

### 3. Workload shape and metric selection / 工作负载形态与指标选择

**Question (English):** Request X has 4,000 input tokens and 50 output tokens.
Request Y has 100 input tokens and 1,000 output tokens. Which request is
prefill-heavy, which is decode-heavy, and which metrics deserve the most
attention for each?

**问题（中文）：** 请求 X 有 4,000 个输入 token 和 50 个输出 token；请求 Y 有
100 个输入 token 和 1,000 个输出 token。哪个请求偏 prefill 密集，哪个偏
decode 密集？测试两者时分别应重点观察哪些指标？

**Explanation (English):** Prefill processes the input prompt in parallel and
strongly influences when the first token can be returned. Decode generates
tokens autoregressively and repeats one step for each additional output token.

**解说（中文）：** Prefill 并行处理输入 prompt，并显著影响第一个 token 何时
返回。Decode 以自回归方式生成 token，每增加一个输出 token 都需要再执行一步。

**Correct Answer (English):** X is prefill-heavy, so TTFT and prefill
throughput are especially informative. Y is decode-heavy, so TPOT, ITL,
output-token throughput, and end-to-end latency are especially informative.
Both workloads should still report the full metric set rather than hiding a
trade-off.

**正确答案（中文）：** X 偏 prefill 密集，因此 TTFT 与 prefill 吞吐量尤其重要；
Y 偏 decode 密集，因此 TPOT、ITL、输出 token 吞吐量与端到端延迟尤其重要。
两种工作负载仍应报告完整指标集合，以免隐藏指标间的权衡。

### 4. Concurrency, request rate, and Little's Law / 并发数、请求速率与 Little 定律

**Question (English):** What does a concurrency level of 32 control, and what
does a request rate of 32 requests/s control? Why are they not equivalent?

**问题（中文）：** 并发数 32 控制什么？请求速率 32 requests/s 控制什么？
为什么两者并不等价？

**Explanation (English):** Concurrency is a stock: it counts requests that
have arrived but not yet completed. Request rate is a flow: it counts arrivals
per unit time. Latency links the two quantities.

**解说（中文）：** 并发量是一个存量，表示已经到达但尚未完成的请求数量；请求
速率是一个流量，表示单位时间内到达多少请求；延迟把这两个量联系起来。

**Correct Answer (English):** Concurrency 32 means up to or approximately 32
requests are simultaneously in flight, depending on the benchmark's closed-
loop policy. A rate of 32 requests/s means the workload generator attempts 32
arrivals each second, independent of how long earlier requests remain active.
In steady state, Little's Law gives:

**正确答案（中文）：** 并发数 32 表示根据 benchmark 的闭环策略，同时大约有或
最多有 32 个在途请求。32 requests/s 表示负载发生器每秒尝试送入 32 个请求，
与更早请求仍需运行多久无关。在稳态下，Little 定律给出：

```text
average concurrency ≈ arrival rate × average latency
```

**English:** At 32 requests/s and two seconds of average latency, the service
has about 64 requests in flight, not 32. Conversely, fixed concurrency 32 can
produce different completion rates as latency changes.

**中文：** 当请求速率为 32 requests/s、平均延迟为 2 秒时，服务中约有 64 个
在途请求，而不是 32 个。反过来，并发数固定为 32 时，延迟变化也会导致不同的
完成速率。

### 5. Warmup and cache-state fairness / 预热与缓存状态公平性

**Question (English):** A is measured immediately after model startup. B is
measured after warmup and with reusable prefixes already stored in the radix
cache. If B has lower TTFT, does this prove that B's configuration is better?
How should the experiment be corrected?

**问题（中文）：** A 在模型刚启动后立即测量；B 在完成预热且 radix cache 已有
可复用前缀后测量。如果 B 的 TTFT 更低，能否证明 B 的配置更好？应该怎样修正
实验？

**Explanation (English):** Startup work, lazy initialization, kernel or graph
preparation, memory allocation, and cache hits can all improve later requests
without any configuration advantage. Benchmark state is therefore part of the
controlled workload.

**解说（中文）：** 启动工作、惰性初始化、kernel 或 graph 准备、显存分配与
缓存命中，都可能让后续请求更快，而不代表配置本身更好。因此 benchmark 状态也
属于必须控制的工作负载条件。

**Correct Answer (English):** No. Both configurations need the same warmup
requests and warmup count. Each measured run must either start from an
equivalent cold cache or receive the same prefix sequence to build an
equivalent warm cache. Cold-cache and warm-cache results should be reported
separately, and the experiment should be repeated.

**正确答案（中文）：** 不能。两个配置需要使用相同的预热请求与预热次数。每轮
测量都应从等价的冷缓存开始，或者用相同的前缀序列建立等价的热缓存。冷缓存与
热缓存结果应分开报告，并重复执行实验。

### 6. Prefix-cache A/B experiment / 前缀缓存 A/B 实验

**Question (English):** Requests share a 2,000-token system prompt but contain
different user questions. How can an A/B experiment isolate the effect of the
SGLang prefix cache, and which metrics should improve?

**问题（中文）：** 一组请求共享 2,000-token 的 system prompt，但包含不同的
用户问题。如何通过 A/B 实验隔离 SGLang prefix cache 的效果？哪些指标应该
改善？

**Explanation (English):** A cached exact token prefix allows later requests
to reuse previously computed KV states and skip repeated prefill work. The
first cold request cannot reuse a prefix that has not yet been computed.

**解说（中文）：** 完全一致的 token 前缀被缓存后，后续请求可以复用已经计算的
KV 状态，跳过重复 prefill。第一个冷请求无法复用尚未计算的前缀。

**Correct Answer (English):** Keep the model, request sequence, lengths,
concurrency, and other settings fixed. In A, disable prefix reuse or begin each
request from an equivalent cold state. In B, enable prefix reuse and warm the
shared prefix before measuring later requests. Prefix caching should primarily
reduce later-request TTFT and prefill work, and it may improve request
throughput. It does not directly accelerate each normal decode step, so TPOT
may change little. Cache memory consumption must also be measured.

**正确答案（中文）：** 保持模型、请求序列、长度、并发数及其他设置一致。在 A
中关闭前缀复用，或让每个请求都从等价冷状态开始；在 B 中开启前缀复用，并在
测量后续请求前预热共享前缀。Prefix cache 应主要降低后续请求的 TTFT 与 prefill
工作量，并可能提高请求吞吐量。它不会直接加速每个正常 decode step，因此 TPOT
可能变化很小；同时还必须测量缓存的显存占用。

### 7. Chunked prefill and streaming smoothness / Chunked prefill 与流式平滑度

**Question (English):** Several short requests are decoding when a request
with a 20,000-token prompt arrives. What can happen to the short requests' ITL
if the entire prefill runs at once? How does chunked prefill help, and what
trade-off does it introduce?

**问题（中文）：** 多个短请求正在 decode，此时一个带有 20,000-token prompt
的请求到达。如果完整 prefill 一次执行，短请求的 ITL 可能发生什么变化？
Chunked prefill 如何改善问题，又会引入什么权衡？

**Explanation (English):** A long uninterrupted prefill can occupy a GPU
execution interval and delay the next decode step of requests that are already
streaming. Splitting prefill creates scheduling points where decode work can
run.

**解说（中文）：** 一次长时间、不间断的 prefill 会占用 GPU 执行机会，并推迟
正在流式输出请求的下一次 decode。拆分 prefill 会创造调度点，让 decode 工作
可以穿插运行。

**Correct Answer (English):** The short requests can suffer large ITL spikes
and visibly uneven streaming. Chunked prefill divides the long prompt and
interleaves decode between chunks, reducing head-of-line blocking and
stabilizing tail ITL. The long request may receive a higher TTFT, while smaller
chunks can add scheduling and kernel-launch overhead or reduce prefill
efficiency. Chunk size therefore expresses a fairness-versus-efficiency
trade-off.

**正确答案（中文）：** 短请求可能出现较大的 ITL 尖峰，流式输出明显不均匀。
Chunked prefill 拆分长 prompt，并在 chunk 之间穿插 decode，从而缓解队头阻塞并
稳定尾部 ITL。长请求自身的 TTFT 可能升高；较小 chunk 还可能增加调度与 kernel
launch 开销，或降低 prefill 效率。因此 chunk 大小体现了公平性与效率之间的
权衡。

### 8. CUDA Graph with dynamic decode batches / CUDA Graph 与动态 Decode Batch

**Question (English):** Why can CUDA Graph reduce TPOT when each decode step
contains many short GPU operations? Why does a continuously changing decode
batch make CUDA Graph integration difficult?

**问题（中文）：** 当每个 decode step 包含许多短 GPU 操作时，CUDA Graph 为何
能够降低 TPOT？持续变化的 decode batch 又为什么会增加 CUDA Graph 集成难度？

**Explanation (English):** When GPU work per operation is short, CPU framework
and kernel-launch overhead can occupy a meaningful fraction of each decode
step. CUDA Graph records a launch sequence so that the CPU can replay it with
less per-operation submission overhead.

**解说（中文）：** 当单个 GPU 操作很短时，CPU framework 与 kernel launch
开销会占据每个 decode step 的显著比例。CUDA Graph 记录一组启动序列，使 CPU
能够以更少的逐操作提交开销重复执行它。

**Correct Answer (English):** Replaying a captured CUDA Graph reduces repeated
CPU dispatch work and gaps between kernels, which can lower TPOT. A captured
graph generally expects stable operation structure, tensor shapes, batch size,
and memory addresses, while continuous batching changes membership and size as
requests arrive and finish. A runtime can capture graphs for multiple batch
sizes, pad an actual batch to a supported size, use stable memory pools, and
fall back to eager execution for unsupported shapes. These techniques trade
extra memory and implementation complexity for lower launch overhead.

**正确答案（中文）：** 重放已经捕获的 CUDA Graph 可以减少重复 CPU dispatch
工作与 kernel 之间的空隙，从而降低 TPOT。被捕获的 graph 通常要求稳定的操作
结构、tensor shape、batch size 与内存地址，而 continuous batching 会随着请求
到达和结束改变成员与大小。Runtime 可以为多个 batch size 预先捕获 graph，将
实际 batch padding 到支持的大小，使用稳定的内存池，并对不支持的 shape 回退到
eager execution。这些方法以额外显存与实现复杂度换取更低的启动开销。

### 9. Speculative decoding and acceptance rate / 推测解码与接受率

**Question (English):** A fast draft mechanism proposes several tokens and
the target model verifies them together. When can this reduce TPOT
substantially? What happens when proposed tokens are frequently rejected?

**问题（中文）：** 一个快速 draft 机制先提出多个 token，再由目标大模型一起
验证。什么情况下它能显著降低 TPOT？如果候选 token 经常被拒绝，会发生什么？

**Explanation (English):** Autoregressive decoding is sequential because the
next accepted token normally requires another target-model step. Speculation
is useful when one target-model verification advances the sequence by several
accepted tokens.

**解说（中文）：** 自回归 decode 具有串行性，因为通常每接受下一个 token 都要
再执行一次目标模型。若一次目标模型验证能够让序列前进多个被接受的 token，推测
才会产生收益。

**Correct Answer (English):** TPOT can improve when the draft path is much
cheaper than the target model and its acceptance rate is high, so each target
verification accepts multiple tokens on average. With low acceptance, draft
computation, verification, synchronization, and scheduling overhead are spent
for little forward progress. Performance can then match or underperform normal
decoding. A benchmark must report accepted tokens per verification together
with TPOT, throughput, and resource usage.

**正确答案（中文）：** 当 draft 路径远比目标模型便宜且接受率较高时，每次目标
模型验证平均可以接受多个 token，从而改善 TPOT。接受率低时，draft 计算、验证、
同步与调度开销只换来很少的序列推进，性能可能与普通 decode 持平甚至更差。
Benchmark 必须同时报告每次验证接受的 token 数、TPOT、吞吐量与资源占用。

### 10. Diagnosing queueing and capacity saturation / 诊断排队与容量饱和

**Question (English):** At concurrency 8, a service has 100 ms TTFT, 25 ms
TPOT, and 55% GPU utilization. At concurrency 64, it has 2,000 ms TTFT, 28 ms
TPOT, 95% GPU utilization, and a growing waiting queue. What is the leading
bottleneck hypothesis, why is slower decode not the best first conclusion,
and how can the hypothesis be tested?

**问题（中文）：** 并发数为 8 时，服务的 TTFT 为 100 ms、TPOT 为 25 ms、GPU
利用率为 55%；并发数为 64 时，TTFT 为 2,000 ms、TPOT 为 28 ms、GPU 利用率
为 95%，且等待队列持续增长。最优先的瓶颈假设是什么？为什么不应首先断定
decode 变慢？如何验证这一假设？

**Explanation (English):** TTFT includes time spent waiting for admission as
well as prefill and response-delivery work. When demand exceeds service
capacity, queueing time can grow rapidly even though the decode rate of an
admitted request remains nearly stable.

**解说（中文）：** TTFT 不仅包含 prefill 与响应传输，还包含等待准入的时间。当
需求超过服务容量时，即使已准入请求的 decode 速度几乎稳定，排队时间也会快速
增长。

**Correct Answer (English):** The leading hypothesis is capacity saturation
and queueing: the GPU is nearly fully utilized, arrivals or in-flight demand
exceed the current service rate, and new requests wait much longer for
admission or prefill. TPOT rises only from 25 to 28 ms, so decode execution is
not the dominant source of the 1,900 ms TTFT increase. Hold the workload shape
constant and sweep request rate or concurrency downward while recording queue
time, prefill time, throughput, TTFT, and TPOT. A rapid TTFT recovery with
nearly unchanged TPOT supports the queueing hypothesis. A complementary test
can shorten inputs to determine how much prefill capacity contributes.

**正确答案（中文）：** 最优先的假设是容量饱和与排队：GPU 已接近满负载，请求
到达量或在途需求超过当前服务速率，新请求等待准入或 prefill 的时间大幅增加。
TPOT 仅从 25 ms 增至 28 ms，因此 decode 执行并不是 TTFT 增加 1,900 ms 的主要
来源。保持工作负载形态不变，逐级降低请求速率或并发数，同时记录排队时间、
prefill 时间、吞吐量、TTFT 与 TPOT；若 TTFT 快速恢复而 TPOT 几乎不变，就支持
排队假设。还可缩短输入，进一步判断 prefill 容量的影响。

## Summary / 总结

- **English:** A meaningful A/B benchmark controls the workload, system state,
  and measurement procedure while changing one primary variable.
  **中文：** 有意义的 A/B benchmark 会控制工作负载、系统状态与测量过程，只
  改变一个主要变量。
- **English:** TTFT represents startup responsiveness, TPOT represents average
  post-first-token generation time, ITL reveals streaming gaps and jitter,
  and end-to-end latency represents total completion time.
  **中文：** TTFT 表示响应启动速度，TPOT 表示首 token 之后的平均生成时间，
  ITL 揭示流式输出间隔与抖动，端到端延迟表示总完成时间。
- **English:** Input-heavy workloads emphasize prefill and TTFT, while
  output-heavy workloads emphasize decode, TPOT, ITL, and output throughput.
  **中文：** 输入密集型工作负载更强调 prefill 与 TTFT；输出密集型工作负载更
  强调 decode、TPOT、ITL 与输出吞吐量。
- **English:** Concurrency and request rate describe different load dimensions
  and are linked by latency rather than being interchangeable.
  **中文：** 并发数与请求速率描述不同的负载维度，两者通过延迟联系，并不能
  互换。
- **English:** Warmup and cache state can materially change measurements and
  must be controlled or reported separately.
  **中文：** 预热与缓存状态会显著改变测量结果，必须受到控制或分开报告。
- **English:** Prefix caching, chunked prefill, CUDA Graph, and speculative
  decoding target different costs and introduce different trade-offs.
  **中文：** Prefix cache、chunked prefill、CUDA Graph 与推测解码针对不同成本，
  也会引入不同权衡。
- **English:** Metric patterns should lead to a testable bottleneck hypothesis;
  high TTFT with nearly stable TPOT can indicate queueing rather than slow
  decode.
  **中文：** 指标模式应转化为可验证的瓶颈假设；TTFT 很高而 TPOT 几乎稳定，
  可能表示排队而非 decode 变慢。

## Common Mistakes / 常见错误

- **English:** Comparing throughput from workloads with different lengths,
  concurrency, cache state, or warmup history.
  **中文：** 对比输入输出长度、并发数、缓存状态或预热历史不同的工作负载吞吐量。
- **English:** Treating the highest throughput configuration as universally
  best without checking latency objectives.
  **中文：** 不检查延迟目标，便把吞吐量最高的配置视为普遍最优。
- **English:** Confusing in-flight concurrency with requests arriving per
  second.
  **中文：** 混淆在途并发量与每秒到达请求数。
- **English:** Reporting average TPOT alone and overlooking P95 or P99 ITL
  spikes that make streaming feel uneven.
  **中文：** 只报告平均 TPOT，忽略导致流式输出不均匀的 P95 或 P99 ITL 尖峰。
- **English:** Attributing a warm prefix-cache result entirely to a runtime
  configuration change.
  **中文：** 把热前缀缓存带来的结果完全归因于 runtime 配置变化。
- **English:** Assuming prefix caching directly accelerates every decode step.
  **中文：** 误以为 prefix cache 会直接加速每一次 decode step。
- **English:** Assuming smaller prefill chunks are always better without
  measuring long-request TTFT and execution overhead.
  **中文：** 误以为 prefill chunk 越小总是越好，而不测量长请求 TTFT 与执行开销。
- **English:** Treating CUDA Graph or speculative decoding as guaranteed
  acceleration for every batch shape and workload.
  **中文：** 把 CUDA Graph 或推测解码视为适用于所有 batch shape 与工作负载的
  必然加速。
- **English:** Calling a large TTFT increase a decode regression without
  separating queue, prefill, and decode time.
  **中文：** 未拆分排队、prefill 与 decode 时间，就把 TTFT 大幅增加称为 decode
  性能退化。

## Next Steps / 下一步建议

1. **English:** Launch an SGLang service and record a reproducible single-GPU
   baseline with fixed model, precision, prompt distribution, output length,
   warmup, and random seed.
   **中文：** 启动一个 SGLang 服务，在固定模型、精度、prompt 分布、输出长度、
   预热方式与随机种子的条件下记录可复现的单 GPU baseline。
2. **English:** Sweep concurrency or request rate and plot throughput, TTFT,
   TPOT, P99 ITL, end-to-end latency, queue time, GPU utilization, and peak
   memory to identify the saturation knee.
   **中文：** 扫描并发数或请求速率，绘制吞吐量、TTFT、TPOT、P99 ITL、端到端
   延迟、排队时间、GPU 利用率与显存峰值，找出容量饱和拐点。
3. **English:** Run a controlled shared-prefix experiment and report cold-cache
   and warm-cache results separately, including memory cost.
   **中文：** 运行受控的共享前缀实验，分别报告冷缓存与热缓存结果，并包含显存
   成本。
4. **English:** Compare chunked-prefill settings with mixed long-prefill and
   active-decode traffic, focusing on long-request TTFT and P99 ITL.
   **中文：** 在长 prefill 与活跃 decode 混合流量下比较不同 chunked-prefill
   设置，重点观察长请求 TTFT 与 P99 ITL。
5. **English:** Trace one decode iteration through the SGLang scheduler,
   CUDA-Graph path, attention backend, and GPU kernels, then connect each
   execution layer to the metric it can affect.
   **中文：** 沿 SGLang scheduler、CUDA Graph 路径、attention backend 与 GPU
   kernel 追踪一次 decode iteration，并把每个执行层与它可能影响的指标联系起来。
