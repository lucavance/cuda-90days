# Day 023: SGLang Runtime Core Concepts / SGLang 运行时核心概念

Date / 日期: 2026-07-24

## Topic / 主题

**English:** A concept-only study of SGLang request admission, continuous
batching, prefill/decode scheduling, chunked prefill, paged KV-cache
management, prefix caching, RadixAttention, and cache eviction.

**中文：** 纯概念学习 SGLang 的请求准入、continuous batching、prefill/decode
调度、chunked prefill、分页式 KV cache 管理、前缀缓存、RadixAttention 与缓存
淘汰。

## Goal / 目标

**English:** Build a coherent mental model of how an SGLang runtime admits
requests, shares limited GPU and KV-cache resources, reuses exact token
prefixes, and balances TTFT, TPOT, throughput, and fairness without performing
installation or coding experiments.

**中文：** 在不安装环境、不编写代码和不运行实验的前提下，建立一套连贯的
SGLang 运行时思维模型：理解请求如何被准入、如何共享有限的 GPU 与 KV cache
资源、如何复用完全相同的 token 前缀，以及如何权衡 TTFT、TPOT、吞吐与公平性。

## 10 Concept Questions / 10 道概念题

### 1. Request lifecycle and admission / 请求生命周期与准入

**Question (English):** In an SGLang serving runtime, how do the `waiting`,
`running`, and `finished` states differ? What conditions allow a waiting
request to become running?

**问题（中文）：** 在 SGLang serving runtime 中，`waiting`、`running` 和
`finished` 三种状态有什么区别？一个等待中的请求需要满足哪些条件才能进入
运行状态？

**Explanation (English):** Admission is more than taking the next item from a
queue. The scheduler must consider the scheduling policy, token budget, batch
capacity, and available KV-cache or GPU memory. Batching keeps requests as
separate sequences; it does not merge their meanings or outputs.

**解说（中文）：** 请求准入不只是从队列里取出下一项。scheduler 还要考虑调度
策略、token budget、batch 容量以及可用的 KV cache 或 GPU 显存。batching 只是
让多个独立序列共享一次 GPU 执行，并不会把它们的语义或输出合并成一个请求。

**Correct Answer (English):** A waiting request is queued but has not yet been
admitted to GPU execution. A running request has been admitted, has the
required runtime resources, and is participating in prefill or decode. A
finished request has reached a stop condition, completed, been cancelled, or
failed; its active resources can then be released, although reusable prefix
cache entries may be retained. A waiting request can run when its scheduling
priority is selected and sufficient token, batch, and KV-cache capacity is
available.

**正确答案（中文）：** `waiting` 表示请求仍在队列中，尚未获准进入 GPU 执行；
`running` 表示请求已经被准入、获得所需运行时资源，并正在参与 prefill 或
decode；`finished` 表示请求已经完成、命中停止条件、被取消或失败，活跃资源随后
可以释放，但可复用的前缀缓存可能继续保留。等待请求只有在调度策略选中它，且
token、batch 与 KV cache 容量足够时，才能进入运行状态。

### 2. Fixed batching versus continuous batching / 固定批处理与连续批处理

**Question (English):** What is the difference between fixed batching and
continuous batching? Why is continuous batching better suited to LLM requests
whose output lengths differ?

**问题（中文）：** fixed batching 与 continuous batching 有什么区别？为什么
continuous batching 更适合输出长度不同的 LLM 请求？

**Explanation (English):** LLM requests rarely finish at the same decode
iteration. If the batch composition cannot change until every sequence ends,
completed slots sit idle while long sequences continue.

**解说（中文）：** LLM 请求很少在同一次 decode iteration 中同时结束。如果必须
等整批序列全部完成后才能更换 batch，短请求结束后留下的位置会在长请求继续生成
期间闲置。

**Correct Answer (English):** Fixed batching forms a batch and generally keeps
that group together until the batch completes. Continuous batching updates the
running batch at iteration boundaries: finished requests leave and eligible
waiting requests can enter. This prevents short completed requests from
leaving GPU capacity unused while long requests continue, improving
utilization and throughput.

**正确答案（中文）：** fixed batching 先组成一批请求，并通常保持这一组直到整批
结束。continuous batching 会在推理迭代边界更新运行 batch：已经完成的请求离开，
符合准入条件的等待请求可以加入。这样短请求完成后不会让 GPU 容量长期空闲，而
长请求仍可继续运行，从而提升利用率和吞吐。

### 3. Updating a decode batch / 更新 decode batch

**Question (English):** A running batch contains requests A, B, and C. After
one decode step, A finishes while D is waiting. What can the scheduler do in
the next iteration, and must B and C restart computation?

**问题（中文）：** 当前运行 batch 包含 A、B、C。一次 decode 后 A 已完成，而 D
正在等待。下一轮 scheduler 可以怎样处理？B、C 是否需要从头计算？

**Explanation (English):** Continuous batching changes batch membership, not
the logical history of requests that remain. Each running sequence keeps its
own state and KV cache.

**解说（中文）：** continuous batching 改变的是 batch 成员，而不是保留请求的
逻辑历史。每个仍在运行的序列都保存自己的状态与 KV cache。

**Correct Answer (English):** The scheduler removes A and may admit D if the
scheduling policy and resource budgets permit it. B and C continue from their
existing KV caches and do not recompute their earlier tokens. D must first
complete prefill for the part of its prompt that is not already cached before
it can perform normal token-by-token decode.

**正确答案（中文）：** scheduler 会移除 A，并可在调度策略与资源预算允许时准入
D。B、C 依靠各自已有的 KV cache 继续运行，不需要重新计算历史 token。D 必须先
对 prompt 中尚未缓存的部分完成 prefill，之后才能进入正常的逐 token decode。

### 4. Long prefill competing with decode / 长 prefill 与 decode 竞争

**Question (English):** B and C are steadily decoding while a new request D
arrives with a 4,000-token prompt. If the scheduler executes D's entire
prefill at once, what can happen to B and C's TPOT, and why?

**问题（中文）：** B、C 正在稳定 decode，此时带有 4000-token prompt 的新请求 D
到达。如果 scheduler 一次性执行 D 的完整 prefill，B、C 的 TPOT 可能发生什么
变化？为什么？

**Explanation (English):** Prefill and decode have different computation
shapes, but they still compete for GPU execution time. A long, uninterrupted
prefill can delay the next decode iteration of requests that are already
streaming output.

**解说（中文）：** prefill 与 decode 具有不同的计算形态，但仍然竞争 GPU 执行
时间。一次长时间、不被打断的 prefill 会推迟正在流式输出请求的下一轮 decode。

**Correct Answer (English):** B and C can experience a large TPOT increase or
an inter-token latency spike because their next decode step must wait while D's
large prefill occupies the GPU execution opportunity. The system does not need
to wait for D's final generated response, but it must wait for this long
prefill operation to yield execution capacity.

**正确答案（中文）：** B、C 的 TPOT 可能明显增加，或者出现 token 间延迟尖峰，
因为 D 的大规模 prefill 占用了 GPU 执行机会，使它们的下一轮 decode 被推迟。系统
不必等到 D 生成最终回答，但必须等这段长 prefill 让出执行资源。

### 5. Chunked prefill and its trade-off / Chunked prefill 及其权衡

**Question (English):** If D's 4,000-token prefill is split into four smaller
chunks and B and C decode between those chunks, which latency problem can
improve, and what cost can this introduce?

**问题（中文）：** 如果把 D 的 4000-token prefill 拆成四个较小的 chunk，并在
chunk 之间穿插 B、C 的 decode，可以改善哪个延迟问题？又可能引入什么代价？

**Explanation (English):** Chunking prevents one long prompt from monopolizing
an extended execution interval, but splitting and interleaving work changes
the completion time and execution efficiency of that prefill.

**解说（中文）：** 分块可以避免一个长 prompt 长时间独占执行机会，但拆分与穿插
也会改变这次 prefill 的完成时间和执行效率。

**Correct Answer (English):** Interleaving decode between prefill chunks can
stabilize B and C's TPOT and reduce head-of-line blocking. D's own prefill and
TTFT may take longer because it yields between chunks. Chunking can also add
scheduling or kernel-launch overhead and may be less efficient than one large
prefill operation. It trades some long-request efficiency for better latency
fairness.

**正确答案（中文）：** 在 prefill chunk 之间穿插 decode，可以让 B、C 的 TPOT
更加稳定，并缓解队头阻塞。D 会在各 chunk 之间让出执行机会，因此它自己的
prefill 与 TTFT 可能变长；分块还可能增加调度或 kernel launch 开销，并且不如一次
大规模 prefill 高效。这是在牺牲部分长请求效率与改善延迟公平性之间做权衡。

### 6. Paged KV-cache management / 分页式 KV cache 管理

**Question (English):** If every request must allocate one large contiguous
KV-cache region even though context and output lengths vary, what GPU-memory
problems can occur? How do fixed-size pages or blocks help?

**问题（中文）：** 如果每个请求都必须申请一块很大的连续 KV cache，而请求的
上下文与输出长度各不相同，会产生哪些显存问题？固定大小的 page/block 如何缓解
这些问题？

**Explanation (English):** Requests arrive and finish at different times, and
their KV caches grow by different amounts. Large contiguous allocations can
waste reserved capacity and leave free memory split into unusable holes.

**解说（中文）：** 请求在不同时间到达和结束，KV cache 的增长量也不同。大块连续
分配既可能浪费预留但未使用的容量，也可能把空闲显存切成难以使用的小洞。

**Correct Answer (English):** Contiguous, over-provisioned allocations can
cause external fragmentation and waste memory reserved for tokens that are
never generated. Paged allocation gives requests fixed-size blocks on demand
and uses a page table to form one logically continuous sequence from
non-contiguous physical blocks. Freed pages can be reused by other requests.
The final partially filled page can still introduce a small amount of internal
fragmentation.

**正确答案（中文）：** 连续且过度预留的分配会造成外部碎片，也会浪费为最终没有
生成的 token 预留的显存。分页分配按需为请求提供固定大小的 block，并通过 page
table 将物理上不连续的 block 组织成逻辑上连续的序列；释放的 page 可以立即供其他
请求复用。不过最后一个没有装满的 page 仍可能产生少量内部碎片。

### 7. Per-request KV cache versus prefix cache / 单请求 KV cache 与前缀缓存

**Question (English):** Requests X and Y contain the same 1,000-token system
prompt but different user questions. Without prefix caching, what work is
repeated? With prefix caching, what can be reused and what is saved?

**问题（中文）：** 请求 X、Y 包含相同的 1000-token system prompt，但用户问题
不同。没有 prefix cache 时会重复哪些工作？有 prefix cache 后可以复用什么、节省
什么？

**Explanation (English):** The key benefit is not merely faster memory
allocation. Attention layers have already computed Key and Value states for
the shared token sequence, and repeating that prefill is expensive.

**解说（中文）：** 核心收益不只是更快地分配显存。attention 各层已经为共享 token
序列计算过 Key 和 Value 状态，重复执行这段 prefill 才是主要浪费。

**Correct Answer (English):** Without prefix caching, X and Y independently
prefill the same 1,000 tokens and may store duplicate KV data. With prefix
caching, Y can match the exact token prefix and reuse the previously computed
KV-cache blocks, computing only its unmatched suffix. This reduces duplicate
GPU computation and can lower TTFT. Prefix caching itself still consumes GPU
memory, and semantically similar but token-different text cannot be reused
directly.

**正确答案（中文）：** 没有 prefix cache 时，X、Y 会各自对相同的 1000 个 token
执行 prefill，并可能保存重复 KV 数据。有 prefix cache 后，Y 可以匹配完全相同的
token 前缀并复用已经计算好的 KV cache block，只计算未匹配的后缀，从而减少重复
GPU 计算并降低 TTFT。prefix cache 本身仍会占用显存；仅仅语义相似但 token 序列
不同的文本不能直接复用。

### 8. Organizing shared prefixes with RadixAttention / 用 RadixAttention 组织共享前缀

**Question (English):** Consider these requests:

```text
A = system prompt + document 1 + question A
B = system prompt + document 1 + question B
C = system prompt + document 2 + question C
```

Which parts can they share in a radix tree, and where do branches occur?

**问题（中文）：** 考虑下面三个请求：

```text
A = system prompt + 文档 1 + 问题 A
B = system prompt + 文档 1 + 问题 B
C = system prompt + 文档 2 + 问题 C
```

它们在 radix tree 中可以共享哪些部分？分支分别发生在哪里？

**Explanation (English):** A radix tree represents common token prefixes once
and creates branches only where token sequences diverge. Longer shared paths
represent more reusable KV-cache computation.

**解说（中文）：** radix tree 只保存一次公共 token 前缀，并在 token 序列开始不同
的位置创建分支。共享路径越长，能够复用的 KV cache 计算越多。

**Correct Answer (English):** All three requests share the system-prompt path.
After that path, the tree branches into document 1 and document 2. A and B
continue to share the document-1 path and branch again at question A versus
question B. C follows the document-2 branch and then question C:

```text
system prompt
├── document 1
│   ├── question A
│   └── question B
└── document 2
    └── question C
```

**正确答案（中文）：** 三个请求共同共享 system prompt 路径；随后树在文档 1 与
文档 2 之间产生第一次分支。A、B 继续共享文档 1 路径，并在问题 A 与问题 B 之间
再次分支；C 则进入文档 2，再连接问题 C：

```text
system prompt
├── 文档 1
│   ├── 问题 A
│   └── 问题 B
└── 文档 2
    └── 问题 C
```

### 9. Cache eviction under memory pressure / 显存压力下的缓存淘汰

**Question (English):** The KV cache is full. Candidate P is an old unique
prefix, Q is a recently and frequently reused common prefix, and R belongs to
a currently running request. Which should be evicted first, which cannot be
evicted yet, and why?

**问题（中文）：** KV cache 已满。P 是很久未使用的独有前缀，Q 是近期频繁复用
的公共前缀，R 属于当前正在运行的请求。应该优先淘汰谁？谁暂时不能淘汰？为什么？

**Explanation (English):** Eviction must free memory without destroying state
required for active decode. Cache entries also differ in their expected future
reuse value.

**解说（中文）：** 淘汰策略既要释放显存，也不能破坏活跃 decode 所需的状态；
不同缓存项未来可能被复用的价值也不同。

**Correct Answer (English):** P is the best eviction candidate because it is
old, unique, and has low expected reuse value. Q should usually be retained
because many requests may benefit from it. R cannot be evicted while the
running request depends on it. A typical radix-cache policy therefore evicts
inactive, old leaf entries before active or valuable shared paths.

**正确答案（中文）：** P 是最合适的淘汰候选，因为它长期未使用、只属于独有
前缀，预期复用价值较低。Q 通常应该保留，因为许多请求都可能从中获益。R 在运行
请求仍然依赖它时不能被淘汰。典型 radix cache 策略会先淘汰不活跃的旧叶子节点，
而不是活跃缓存或高价值共享路径。

### 10. Integrated scheduling decision / 综合调度决策

**Question (English):** B and C are decoding. D has a long prompt whose first
2,000 tokens are already in the prefix cache. E is a new short request. KV
cache is nearly full, and P is an old unique cache entry. How can the scheduler
combine continuous batching, prefix caching, chunked prefill, and eviction to
balance TTFT and TPOT?

**问题（中文）：** B、C 正在 decode；D 是长 prompt，但前 2000 个 token 已经存在
于 prefix cache；E 是新的短请求；KV cache 接近满载，P 是长期未使用的独有缓存。
scheduler 可以怎样结合 continuous batching、prefix cache、chunked prefill 与缓存
淘汰，在 TTFT 与 TPOT 之间取得平衡？

**Explanation (English):** This scenario combines admission, active-state
protection, prefix reuse, prefill/decode interference, and memory pressure. A
good decision is a sequence of coordinated actions rather than one batching
choice.

**解说（中文）：** 这个场景同时包含请求准入、活跃状态保护、前缀复用、
prefill/decode 竞争与显存压力。合理方案不是单独选择一种 batching，而是一组相互
配合的决策。

**Correct Answer (English):** First evict inactive entry P to free KV pages
while protecting B and C's active cache. Keep B and C decoding. Match D's
2,000-token cached prefix and prefill only the unmatched suffix; split that
remaining prefill into chunks when necessary and interleave B and C's decode
steps so their TPOT remains stable. At an iteration boundary, admit short
request E as soon as token and memory budgets permit—it need not wait for B or
C to finish completely. After D finishes its remaining prefill, it joins the
decode batch. The scheduler thereby avoids duplicate prefill, limits TPOT
spikes, gives E a reasonable TTFT, and continues using GPU capacity through
continuous batching.

**正确答案（中文）：** 首先淘汰不活跃的 P，释放 KV page，同时保护 B、C 正在使用
的缓存。B、C 继续 decode。D 先匹配并复用已有的 2000-token 前缀，只对未匹配后缀
执行 prefill；必要时将剩余 prefill 分块，并在 chunk 之间穿插 B、C 的 decode，令
它们的 TPOT 保持稳定。在某个迭代边界，只要 token 与显存预算允许，就尽快准入短
请求 E，它不必等 B 或 C 完全结束。D 完成剩余 prefill 后再加入 decode batch。
这样既避免了重复 prefill，也限制了 TPOT 尖峰、照顾了 E 的 TTFT，并通过
continuous batching 持续利用 GPU 容量。

## Summary / 总结

**English:** This session established the following concepts:

- Request admission depends on scheduling policy and resource budgets, not
  merely queue order.
- Continuous batching changes batch membership at iteration boundaries while
  preserving each request's KV-cache state.
- A long prefill can delay active decode and cause TPOT spikes.
- Chunked prefill trades some long-request efficiency or TTFT for better
  inter-token latency and fairness.
- Paged KV-cache allocation reduces contiguous-allocation pressure and allows
  freed blocks to be reused.
- Prefix caching reuses previously computed KV states for an exact token
  prefix and avoids duplicate prefill computation.
- RadixAttention represents shared token-prefix paths, branches at divergence,
  and supports cache lookup and eviction.
- Cache eviction must protect active state and should prefer inactive,
  low-reuse entries.
- End-to-end scheduling balances TTFT, TPOT, throughput, memory capacity, and
  fairness rather than optimizing one metric in isolation.

**中文：** 本次学习建立了以下概念：

- 请求准入取决于调度策略与资源预算，而不只是队列顺序。
- continuous batching 在迭代边界改变 batch 成员，同时保留每个请求的 KV cache
  状态。
- 长 prefill 会推迟活跃 decode，并造成 TPOT 尖峰。
- chunked prefill 用部分长请求效率或 TTFT，换取更好的 token 间延迟与公平性。
- 分页式 KV cache 分配降低连续分配压力，并允许释放后的 block 被其他请求复用。
- prefix cache 为完全相同的 token 前缀复用已经计算的 KV 状态，避免重复 prefill。
- RadixAttention 表达共享 token 前缀路径，在序列分歧处产生分支，并支持缓存查找
  与淘汰。
- 缓存淘汰必须保护活跃状态，并应优先选择不活跃、低复用价值的条目。
- 端到端调度需要同时权衡 TTFT、TPOT、吞吐、显存容量与公平性，而不是孤立优化
  某一个指标。

## Common Mistakes and Weak Points / 常见错误与薄弱点

**English:**

- Treating batching as merging several user requests into one logical request.
- Assuming a waiting request must wait for an entire running request to finish;
  continuous batching can admit work at iteration boundaries when budgets
  allow.
- Thinking prefix caching mainly saves allocation time instead of repeated
  prefill computation.
- Confusing paged KV-cache allocation with prefix reuse: paging manages
  physical memory, while the radix cache decides which token prefixes can
  share computed state.
- Forgetting that a prefix match must be token-identical, not merely
  semantically similar.
- Treating chunked prefill as a free optimization; it can increase the long
  request's TTFT and introduce scheduling or launch overhead.

**中文：**

- 把 batching 误解成将多个用户请求合并为一个逻辑请求。
- 认为等待请求必须等某个运行请求完全结束；continuous batching 可以在迭代边界
  且资源预算允许时准入新工作。
- 认为 prefix cache 主要节省分配时间，而忽略它真正减少的是重复 prefill 计算。
- 混淆分页式 KV cache 分配与前缀复用：分页管理物理显存，而 radix cache 决定哪些
  token 前缀可以共享已计算状态。
- 忘记前缀匹配要求 token 序列完全一致，而不只是语义相似。
- 把 chunked prefill 当作没有代价的优化；它可能增加长请求的 TTFT，并引入调度或
  kernel launch 开销。

## Next Steps / 下一步

**English:** Continue with a concept-only session on the execution layer below
the scheduler:

1. Why decode is a good candidate for CUDA Graph capture and replay.
2. How SGLang chooses among attention backends such as FlashInfer and Triton.
3. How speculative decoding reduces the number of expensive target-model
   decode steps.
4. How these mechanisms affect TTFT, TPOT, memory use, and hardware
   compatibility.

**中文：** 下一次继续学习 scheduler 下方的执行层概念：

1. 为什么 decode 适合使用 CUDA Graph capture 与 replay。
2. SGLang 如何在 FlashInfer、Triton 等 attention backend 之间选择。
3. speculative decoding 如何减少昂贵的目标模型 decode 次数。
4. 这些机制如何影响 TTFT、TPOT、显存占用与硬件兼容性。

## References / 参考资料

- [SGLang repository and runtime feature overview](https://github.com/sgl-project/sglang)
- [RadixAttention: automatic KV-cache reuse](https://www.lmsys.org/blog/2024-01-17-sglang/)
- [SGLang attention backend documentation](https://docs.sglang.io/docs/advanced_features/attention_backend)
