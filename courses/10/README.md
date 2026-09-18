# Course 10: SGLang Inference Systems / 第十课：SGLang 推理系统

## Objectives, prerequisites, and evidence / 目标、前置知识与证据

**English:** This course develops the concepts from Days 004, 007, 023, 034, and 040 into a reproducible serving investigation. You will trace a request through tokenization, scheduling, prefill, decode, and response delivery; explain KV-cache capacity and prefix reuse; and design experiments that distinguish queueing, CPU preparation, GPU execution, and output transport. The deliverable is a deployment recipe plus an auditable client and interpretation procedure. A working endpoint is the beginning of the investigation, not proof that the system is fast or that its bottleneck has been identified. Acceptance emphasizes causal explanations and evidence, not just printing one model answer.

**中文：** 本课把第四、七、二十三、三十四和四十天的概念组织成可复现的推理服务调查。你将跟踪请求经过分词、调度、预填充、解码和响应返回的路径，解释键值缓存容量与前缀复用，并设计能够区分排队、主机准备、设备执行和输出传输的实验。交付物包括部署方法、可审计的客户端和结果解释流程。接口能够响应，只是调查开始，并不证明系统已经足够快，也不表示已经识别出瓶颈。验收重点是因果解释与证据，而不仅是成功打印一次模型回答。

**English:** Prerequisites are Python file handling and testing, Linux processes and sockets, and the basic distinction between host code and asynchronous GPU work. The teaching machine is recorded as having an RTX 4060 and CUDA toolkit 13.3, but NVML initialization currently fails. Consequently this chapter contains no measured GPU latency, throughput, or memory result. Its standard-library client and aggregation tests run on CPU against an explicitly synthetic local protocol fixture. Server commands are checked against official documentation and release source; model deployment remains to be validated on a working GPU environment. Passing protocol tests does not replace model-loading, computational-correctness, or device-performance validation.

**中文：** 前置知识包括 Python 文件处理与测试、Linux 进程和网络接口，以及主机代码与异步 GPU 工作的基本区别。教学机器记录为 RTX 四〇六〇和 CUDA 工具链十三点三，但当前 NVML 初始化失败，因此本章没有实测显卡延迟、吞吐或显存结果。标准库客户端和聚合测试在处理器上连接明确标记的人造本地协议服务运行。服务命令依据官方文档和发行版源码核对，模型部署仍需要在显卡工作正常的环境验证。协议测试通过不能替代模型加载、计算正确性或设备性能验证。

**English:** The verification date is 2026-09-18. The recipe pins SGLang `0.5.19`, whose [official release](https://github.com/sgl-project/sglang/releases/tag/v0.5.19) was published on 2026-09-05, and pins `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` to revision `ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562`. This is an older small dense distilled teaching model, not the latest full DeepSeek model or a large MoE deployment. Rolling documentation can describe newer defaults, so the [versioned server argument source](https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/srt/server_args.py) is the reference for the flags used here. A fixed name alone is insufficient: pin code and model revisions to avoid silently changing weights, tokenizer settings, or serving behavior during reproduction.

**中文：** 核验日期为二〇二六年九月十八日。部署固定使用九月五日发布的 SGLang 零点五点十九，并把指定的一点五十亿参数蒸馏模型固定到上述提交版本。它是较早的小型稠密教学模型，不是最新完整 DeepSeek 模型，也不是大型混合专家部署。滚动文档可能已经描述更新默认值，因此本课用指定发行版的服务参数源码核对命令。固定名称不够，代码版本与模型修订也要固定，才能避免复现时悄悄换成另一套权重、分词配置或服务行为。

## 1. Follow the complete request / 跟踪完整请求

**English:** A model server converts application requests into coordinated model execution. The client first constructs and sends a request; the HTTP layer parses it; tokenization produces token identifiers; admission and scheduling decide when work can run; model execution produces token candidates; sampling chooses output; and detokenization plus transport delivers text. Some stages overlap, occur in separate processes, or use different backends. The sequence is a causal map rather than a claim that every stage occupies one uninterrupted block on one thread. Follow data dependencies to locate waits instead of guessing execution placement from process or function names.

**中文：** 模型服务把应用请求转换成协调执行的模型工作。客户端先构造并发送请求，接口层解析输入，分词产生词元编号，准入与调度决定何时执行，模型计算给出候选，采样选择输出，再由反分词和网络传输把文本交给调用方。部分阶段可能重叠，分布在不同进程，或采用不同后端。因此这条顺序是因果关系图，而不是声称每个阶段都在单一线程上占据一整块连续时间。诊断时必须沿数据依赖定位等待，不能仅凭进程名称或函数名称猜测执行位置。

**English:** First-token latency includes much more than prefill. A request can wait in the client, the network, an admission queue, or a scheduler before any of its tokens reach the device. It can also wait after the first token is computed because of buffering or detokenization. Define the timestamp boundary explicitly: the client in this chapter starts immediately before its HTTP request and observes the first streamed event reporting a positive output-token count. This is client-observed first-token latency, not a direct GPU event duration or a pure prefill measurement. An ambiguous boundary can make even correct statistics describe a metric that was never actually measured.

**中文：** 首词元延迟远不只是预填充时间。请求在任何词元到达设备之前，就可能等待客户端、网络、准入队列或调度器；第一词元算出之后，还可能因缓冲或反分词继续等待。必须明确时间戳边界：本课客户端在发出网络请求之前启动计时，观察第一次报告正输出词元数的流事件。这是客户端观察到的首词元延迟，不是 GPU 事件耗时，也不是纯粹的预填充测量。边界一旦含糊，后续即使统计方法完全正确，也可能在解释一种没有实际测量的指标。

**English:** Consider a request that finishes tokenization quickly but cannot obtain enough KV capacity. Its waiting time belongs before active execution, even though GPU utilization may already be high because other requests are running. Optimizing that request's tokenizer cannot remove the capacity wait. Conversely, a nearly idle GPU with long gaps before launches can point to insufficient host-side preparation. Identical end-to-end latency can arise from these different paths. The experiment must preserve queue state, workload shape, and an execution timeline so that the same headline number does not hide different causes. Equal total durations do not imply equal bottlenecks, and one utilization figure cannot determine an optimization direction.

**中文：** 假设某请求很快完成分词，却无法获得足够键值缓存容量，它的等待发生在活跃执行之前；此时显卡可能因为其他请求而保持繁忙。优化这个请求的分词器，不能消除容量等待。反过来，显卡接近空闲、任务启动之前存在长空隙，则可能是主机准备不足。相同端到端延迟可以来自完全不同路径，所以实验要保留队列状态、负载形状和执行时间线。不能因为两次总耗时相同，就认定它们具有相同瓶颈，也不能只凭一个利用率数字决定优化方向。

**English:** A client timeout means the client stopped waiting; it does not by itself prove the server stopped computing. Disconnect handling, cancellation propagation, and resource reclamation are separate behaviors that need verification in the deployed version. During a benchmark, retain timeouts and failed requests in the report instead of silently retrying them until all rows look successful. A retry changes offered load and may repeat expensive prefill. For service design, record a request identifier across the client and server so that cancellation and remaining work can be traced together. Otherwise, device work may keep consuming resources after the user sees a failure while separate client and server logs conceal the connection.

**中文：** 客户端超时只说明调用方停止等待，并不能单独证明服务器已经停止计算。断连处理、取消传播和资源回收是不同的行为，需要在部署版本中验证。基准实验应保留超时与失败请求，不应偷偷重试到每行都显示成功；重试会改变送入系统的负载，也可能重复昂贵的预填充。设计服务时，应让请求编号跨越客户端和服务器，便于关联取消事件与后续剩余工作。否则用户端已经看到失败，设备仍继续消耗资源，却很难从两边各自的日志发现问题。

## 2. Prefill and decode as different workloads / 不同负载形态的预填充与解码

**English:** Prefill evaluates the prompt and constructs the initial attention state. Many prompt positions can be processed together, so larger matrix operations and substantial parallel work are possible. The logits produced at the prompt boundary normally support selecting the first output token. Decode then repeatedly extends the sequence using its accumulated state. This explanation is more precise than counting the first token as an additional identical decode step in every implementation. Chunking, backend fusion, and scheduling can change the visible kernel boundaries without changing the dependency between successive generated tokens. Understand phase responsibilities from data dependencies rather than counting calls mechanically.

**中文：** 预填充计算输入提示，并建立初始注意力状态。多个输入位置可以一起处理，因此可能形成较大的矩阵运算和较多并行工作；提示边界产生的预测分布通常可以用于选择第一个输出词元。之后解码利用累积状态反复扩展序列。这样的说明，比把第一词元在所有实现里都算作额外的相同解码步更准确。分块、后端融合和调度会改变可见核函数边界，却不会改变后续生成词元之间的依赖关系。理解阶段职责应从数据依赖出发，而不是机械计算调用次数。

**English:** Long input and long output stress different resources. Increasing input length raises initial processing work and retained context, while increasing output length keeps a request active through more sequential generation steps and grows its state further. A short question that requests a long answer can therefore occupy resources longer than a large document with a short response. Measure input and output in model tokens, not characters or UTF-8 bytes. The benchmark workload builder passes exact token identifiers, so input length is known without relying on approximate text length.

**中文：** 长输入和长输出给系统施加的压力不同。增加输入长度会提高初始处理量与保留上下文；增加输出长度，则让请求经历更多连续生成步骤，持续占用资源并继续扩大状态。一个要求长答案的短问题，可能比只需短回复的大文档占用资源更久。长度必须按模型词元计算，不能用字符数或文本字节数替代。主实验构造器直接传入确定长度的词元编号，因此输入规模是已知条件，不必把近似文本长度当成准确实验参数。

**English:** Prefill is often associated with higher arithmetic intensity, and small-batch decode often exposes memory movement and launch overhead. These are starting hypotheses, not permanent labels. Larger decode batches can improve weight reuse, long contexts increase attention-state traffic, and a particular implementation can be limited by launch shape, synchronization, or a backend choice. Before declaring a phase compute-bound or bandwidth-bound, inspect actual kernel durations, bytes moved, achieved throughput, and the workload dimensions. The phase name alone cannot identify the limiting hardware resource. The phase label is also insufficient to choose an optimization.

**中文：** 预填充常与较高算术强度相关，小批量解码则更容易暴露数据搬运和启动开销，但这些只是起始假设，不是永远成立的标签。更大的解码批次可以改善权重复用，长上下文增加注意力状态访问，而具体实现还可能受启动形状、同步或后端选择限制。宣称某阶段受算力或带宽约束之前，应检查真实核函数耗时、数据量、实际吞吐以及工作负载维度。单靠阶段名字，无法识别真正限制性能的硬件资源，也不足以选择合适优化方法。

**English:** Chunked prefill divides a long prompt into smaller units of scheduled work. This can reduce a single prompt's uninterrupted demand and improve interaction with active decoding, but it introduces its own scheduling decisions and may change throughput. A smaller chunk is not universally better. In a controlled comparison, retain the same total input tokens, output cap, concurrency, and cache condition while changing only the chunk setting. Inspect both long-request latency and the experience of short concurrent requests, because a policy can improve fairness while reducing the best isolated throughput. One isolated request cannot fully evaluate scheduling policy, and a gain on one workload does not establish a gain for all service traffic.

**中文：** 分块预填充把长提示拆成较小的调度单位，可能减少单个提示连续占用资源的时间，改善与正在解码请求的交互，但也会引入新的调度决策并影响吞吐，因此块越小并非越好。受控比较中，应保持总输入词元、输出上限、并发和缓存条件相同，只改变分块设置。同时观察长请求延迟和并发短请求体验，因为一种策略可能改善公平性，却降低最佳单独吞吐。只测单个请求无法充分评价调度政策，更不能把一种负载上的收益直接推广到所有服务流量。

## 3. KV cache, pages, and prefix reuse / 键值缓存、页面与前缀复用

**English:** KV cache stores attention key and value states, not a lookup table from one token to the next token. Decode still performs new computation: it forms the new query and state, reads relevant historical state, applies attention, and executes the remaining model layers. Reuse avoids recomputing prior states but does not eliminate reading or attending to them. Keeping this distinction clear explains why a cache hit can reduce prefill work while a long retained context can still make decoding expensive. Evaluate a cache by the work it actually avoids; a hit does not make the entire request computation-free.

**中文：** 键值缓存保存注意力的键和值状态，不是从一个词元查到下一个词元的映射表。解码仍要执行新计算，包括形成当前查询与状态、读取相关历史、计算注意力，并执行模型其他层。复用避免重新计算旧状态，却不意味着无需读取旧状态或对其执行注意力。理解这一点，就能解释为什么命中前缀可以减少预填充，而保留的长上下文仍可能让解码昂贵。缓存的价值需要按它真正省去的工作衡量，不能把缓存命中等同于整个请求无需计算。

**English:** For ordinary full-attention KV storage, a useful first estimate is `2 × layers × stored_tokens × KV_heads × head_dimension × bytes_per_value`. The factor two represents keys and values. Use KV heads rather than query heads for grouped-query attention. This omits allocator padding, metadata, temporary buffers, model weights, and other runtime memory. It is a capacity estimate, not the exact number that a monitoring tool must report. Different architectures and compressed representations require a different accounting model, so do not transfer this formula unchanged to every model called DeepSeek.

**中文：** 对普通完整注意力的键值存储，可以先用两倍的层数、已存词元数、键值头数、头维度和每值字节数相乘估计容量，其中两倍代表键和值。分组查询注意力应使用键值头数，而不是查询头数。该估计没有计入分配器补齐、元数据、临时缓冲、模型权重及其他运行时内存，所以它是容量估算，不是监控工具必须显示的精确数字。不同架构和压缩表示需要不同核算方式，不能因为模型名字都带某个品牌，就把同一个公式原样套用。

**English:** The pinned teaching [model configuration](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B/blob/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562/config.json) specifies 28 layers, 12 query heads, 2 KV heads, and hidden size 1536, giving head dimension 128. At two bytes per cached value, the estimate is 28 KiB per stored token and 56 MiB for 2048 tokens in one independent sequence. This is arithmetic derived from configuration, not observed GPU memory. Shared prefixes can reduce duplicated state, while page allocation and workspaces can increase total allocation beyond this simple per-sequence estimate. Use the estimate as an explanatory starting point rather than presenting it as device measurement.

**中文：** 固定版本的教学模型配置给出二十八层、十二个查询头、两个键值头以及一千五百三十六的隐藏维度，因此每头维度是一百二十八。缓存每值两字节时，每个已存词元约需要二十八千二进制字节，一个独立序列的两千零四十八词元约需要五十六兆二进制字节。这只是根据配置计算的估计，不是观察到的显存结果。共享前缀可以减少重复状态，而页面分配和工作空间又会增加总分配量，所以估算应作为解释起点，不能冒充设备实测。

```python
bytes_per_token = 2 * 28 * 2 * 128 * 2
assert bytes_per_token == 28 * 1024
assert bytes_per_token * 2048 == 56 * 1024 * 1024
```

**English:** Logical sequence order need not match physically contiguous storage. Runtime metadata maps a request's token positions to the pages holding its KV states. Several requests can reference the same cached prefix while having different suffix pages. Pages needed by active requests must remain valid; inactive cached prefixes may be eviction candidates under memory pressure. This separates the questions “is the request finished?” and “is its reusable state still cached?” Memory policy therefore affects both admission capacity and future reuse, rather than simply freeing everything at the end of every response. Memory not dropping immediately after a request therefore does not by itself establish a leak.

**中文：** 序列逻辑顺序不要求物理存储连续，运行时元数据负责把请求词元位置映射到保存键值状态的页面。多个请求可以引用相同缓存前缀，同时拥有不同后缀页面。活跃请求仍依赖的页面必须有效，不活跃的缓存前缀才可能在内存压力下被淘汰。因此请求是否结束，与可复用状态是否仍保留，是两个不同问题。内存政策同时影响准入容量和未来复用，而不是简单地在每个响应结束时释放全部内容。检查显存没有立刻下降时，也不能直接断言出现泄漏。

**English:** RadixAttention organizes prefix sharing around token sequences. Equal-looking text does not guarantee the same token prefix when templates, whitespace, special tokens, model revision, or adapter context differ. Shared content at the end of a prompt is not an identical leading prefix. The [SGLang paper](https://arxiv.org/abs/2312.07104) explains the radix-tree reuse design; this course tests the observable consequence rather than reproducing the paper's performance claims. A useful experiment sends a common long prefix with varied suffixes and compares the same workload with prefix caching disabled. The comparison then isolates a specific mechanism rather than two accidentally different datasets.

**中文：** 前缀复用围绕词元序列组织。即使文本看起来相同，只要模板、空格、特殊词元、模型修订或适配上下文不同，也不能保证拥有相同词元前缀；位于提示末尾的共同内容，更不是相同的开头前缀。上述原始论文解释了基数树复用设计，本课只测试可观察后果，不复述其性能收益作为自己的结果。合适实验是发送共享长前缀、后缀不同的请求，再用关闭前缀缓存的同一负载对照，从而让比较对应一个明确机制，而不是两个碰巧不同的数据集。

## 4. Scheduling, queues, and load shape / 调度、队列与负载形状

**English:** Continuous batching allows the active set to change as requests finish and new work becomes eligible. It avoids waiting for every request in a fixed batch to finish before admitting another batch, but admission still depends on compute and memory constraints. Client concurrency, queued requests, running requests, and tokens in a scheduled batch are different quantities. Eight concurrent clients do not guarantee an eight-request decode batch. Some may be tokenizing, queued, prefilling, finished, or temporarily unable to obtain state capacity. State which population is observed when explaining batching gains so a client parameter is not mistaken for the actual device execution shape.

**中文：** 连续批处理允许活跃集合随着请求结束和新工作就绪而变化，避免固定批次必须全部完成才能接纳下一批，但准入仍受到计算与内存约束。客户端并发数、排队请求数、正在运行的请求数，以及某次调度批次的词元数，是不同量。八个并发客户端不保证形成八请求解码批次，其中一些可能仍在分词、排队、预填充，已经结束，或暂时无法获得状态容量。解释批处理收益时必须说明观测的是哪个集合，否则容易把客户端参数当成设备实际执行形状。

**English:** Raising concurrency usually increases available work until another limit dominates. Beyond that point, throughput may flatten while queueing and tail latency rise. The useful operating point depends on the latency budget and error rate, not simply the largest token-per-second value. A server accepting every request can appear busy while providing an unusable experience. In a production design, bounded admission, backpressure, and clear overload responses are part of performance engineering because they control how much waiting the system permits. Removing all admission limits does not increase capacity, and an indefinitely growing queue is not successful scaling.

**中文：** 增加并发通常会提供更多可执行工作，直到其他限制开始主导；超过该点，吞吐可能不再增长，排队和尾延迟却继续上升。可用运行点取决于延迟预算和失败率，不只是最大的每秒词元数。服务器即使接受全部请求并看起来很忙，也可能提供无法使用的体验。因此生产设计中的有界准入、背压和明确过载响应，本来就是性能工程的一部分，它们决定系统允许积累多少等待。不能把拒绝所有限制等同于提高容量，也不能把队列无限增长视为成功扩展。

**English:** The provided client uses a fixed-size thread pool. A worker submits its next request only after the previous request finishes, so the workload is closed-loop. When the server slows down, the client naturally sends fewer new requests per second. That is suitable for a concurrency sweep but can hide overload behavior under an independently fixed arrival rate. An open-loop test schedules arrivals independently and measures missed deadlines and queue growth. Record the load model with the results instead of treating all tests with the same nominal concurrency as equivalent. For capacity comparisons, determine whether completions or an external clock trigger new requests; confusing them can underestimate congestion.

**中文：** 本课客户端使用固定大小线程池，工作线程只有在前一请求结束后才提交下一请求，因此属于闭环负载。服务器变慢时，客户端自然减少每秒新请求数量，这适合并发扫描，却可能隐藏独立固定到达率下的过载行为。开放环测试则独立安排到达时间，观察错过期限与队列增长。报告必须记录负载模型，不能把名义并发相同的所有测试视为等价。尤其在比较服务容量时，应先检查请求是由完成事件驱动，还是由外部时钟驱动，否则很容易低估拥塞。

**English:** CPU preparation can overlap device execution when the next batch's independent metadata work runs while the current batch is on the GPU. True dependencies still require coordination: the CPU cannot overwrite buffers the device is reading, and the next step cannot consume an unavailable result. Overlap may shorten idle gaps but does not make CPU work disappear. Test it as a separate change, keeping batch shape and other options fixed, and inspect both the timeline and output behavior. A faster isolated kernel can expose a previously hidden host bottleneck. A local optimization can therefore change the entire critical path.

**中文：** 当前批次在 GPU 执行时，处理器可以准备下一批不依赖当前结果的元数据，从而重叠主机与设备工作。但真实依赖仍需要协调：主机不能覆写设备正在读取的缓冲，下一步也不能消费尚未产生的结果。重叠可能缩短空闲间隙，却不会让主机工作消失。应把它作为单独变更测试，固定批次形状与其他选项，同时检查时间线和输出行为。某个核函数优化得更快之后，原本被遮住的主机瓶颈还可能浮现，所以局部优化改变的可能是整个关键路径。

## 5. Metrics and interpretation / 指标与解释

**English:** Keep request latency and aggregate throughput separate. End-to-end latency measures one request from submission to completion; throughput divides completed work by a clearly defined wall-clock interval. Summing per-request rates does not produce aggregate throughput because concurrent requests overlap. This client's denominator includes the whole workload interval, including failed requests and executor overhead, while its numerator counts output tokens only from successful streams. Retaining failure count alongside throughput prevents an apparently faster run from hiding an increase in dropped requests. State every denominator and keep it unchanged across a comparison.

**中文：** 单请求延迟与总体吞吐必须分开。端到端延迟衡量一次请求从提交到完成的时间；吞吐则用完成工作量除以明确的墙上时钟区间。由于并发请求互相重叠，把每个请求的速率相加不能得到总体吞吐。本客户端的分母包含整批负载持续时间、失败请求等待及执行器开销，分子只统计成功流的输出词元。吞吐旁边同时保留失败数，能够避免一个看起来更快的实验其实只是丢弃了更多请求。任何分母选择都应明示，不能在比较时悄悄改变。

**English:** Stream chunks are transport events, not guaranteed one-token units. An event can contain several new tokens, no visible characters, metadata only, or buffered text. The native API reports cumulative completion counts, which the client checks for monotonicity. It computes a client-observed TPOT only when each new-count event advances by exactly one and at least two tokens arrive; otherwise it leaves TPOT unavailable. Even the eligible estimate includes transport and scheduling effects. It is not a per-kernel decode duration, and chunk arrival gaps should not automatically be called inter-token latency.

**中文：** 流式块是传输事件，不保证一个块等于一个词元。一个事件可能包含多个新词元、没有可见字符、只有元数据，或带着缓冲后的文本。原生接口报告累积输出词元数，客户端检查其单调性；只有每次新增计数都恰好增加一、并且至少收到两个词元时，才计算客户端观察的平均输出间隔，否则保留为空。即使满足条件，该估计仍包括传输和调度影响，不是单个核函数的解码耗时。不能把任何块到达间隔都直接命名为词元间延迟。

**English:** Percentiles require both a definition and enough observations. This client uses the nearest-rank rule for p95, making its calculation explicit. With only four observations, p95 becomes the maximum; such a number is not a stable estimate of production tail behavior. Repeated runs, sufficient request counts, and preserved distributions matter more than printing several decimal places. Report warmup policy and sample size with every percentile, and examine whether a few timeouts or unusually long outputs are changing the tail. Raw records must remain available to recover information lost when a statistic compresses the distribution.

**中文：** 分位数既需要定义，也需要足够观测。本客户端使用最近秩规则计算百分之九十五分位，明确统计方法。只有四个观测时，该分位数就是最大值，这不能稳定代表生产尾部行为。重复运行、足够请求数和保留分布，比多打印几个小数位重要。每个分位数都应附带预热策略和样本规模，并检查少量超时或特别长的输出是否改变尾部。统计量可以把复杂数据压缩成便于比较的数，但压缩之后丢失的信息仍需要通过原始记录追溯。

**English:** Prefix-cache warmup is different from model warmup. Loading weights, initializing kernels, capturing graphs, or compiling a grammar can affect early requests even when their prefixes are unrelated. Replaying the measured workload can also prime its exact prefixes and change the experiment you intended to run. Separate a generic readiness request, a declared prefix-priming request, and the measured request set. For a cache comparison, restart the server between conditions or use a verified cache-reset mechanism; this course uses restart to avoid assuming undocumented reset behavior. Warmup is itself an experimental variable and must be recorded.

**中文：** 前缀缓存预热不同于模型预热。加载权重、初始化核函数、捕获计算图或编译语法，都可能影响早期请求，即使它们的前缀互不相关。直接重放测量负载，还会预先缓存完全相同的前缀，改变你原本想做的实验。因此应区分通用就绪请求、明确声明的前缀填充请求，以及正式测量集合。缓存对照需要在条件之间重启服务器，或使用已经核实的缓存重置机制；本课选择重启，避免假定某个未核实接口的清理行为。预热本身也是实验变量，必须记录。

## 6. Pinned deployment recipe / 固定版本部署流程

**English:** First verify driver access and a compatible execution environment. A toolkit version printed by `nvcc` does not prove that the driver can initialize a device, and an NVML failure cannot be repaired by adding model-serving flags. On this machine the GPU-dependent branch remains unexecuted. The commands below are a reproducible procedure for a healthy Linux NVIDIA environment; they do not claim that every dependency wheel supports every GPU or Python build. Save the resolved package list and server help output to document what was actually installed. Reading a toolkit version, importing a framework, and executing a model establish different validation levels and cannot substitute for one another.

**中文：** 首先验证驱动访问和兼容运行环境。编译器打印的工具链版本不能证明驱动能够初始化设备，NVML 失败也不能靠增加模型服务参数修复。本机依赖 GPU 的分支仍未执行。下列命令提供健康 Linux 英伟达环境中的复现流程，并不声称所有依赖轮子都支持任何显卡或 Python 构建。实际安装之后，应保存解析出的依赖列表和服务帮助信息，记录最终得到的环境。能够读取工具链版本、能够导入框架和能够执行模型，是不同层级的验证，不能互相代替。

```bash
nvidia-smi
nvcc --version
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --pre "sglang==0.5.19"
.venv/bin/python -m pip freeze > environment.lock.txt
.venv/bin/python -m sglang.launch_server --help > server-help.txt
```

**English:** The versioned release exists on PyPI; its dependency set includes PyTorch 2.13.0, while the rolling installation page may discuss later dependencies. Pinning the top-level package does not freeze every transitive dependency, which is why the generated lock record is retained. The [official installation guide](https://docs.sglang.io/docs/get-started/install) describes supported installation paths and hardware-specific alternatives. If resolution or startup fails, retain the complete error and investigate the specific wheel, driver, or backend mismatch rather than switching versions and presenting the resulting environment as the original experiment. An environment change may be a reasonable repair, but record it as a new condition so subsequent performance differences remain interpretable.

**中文：** 指定发行版在包索引中存在，其依赖包含 PyTorch 二点十三点零，而滚动安装文档可能讨论更晚依赖。固定顶层包不等于冻结全部间接依赖，所以还要保留实际解析的环境记录。官方安装指南说明了支持的安装路径和不同硬件方案。解析或启动失败时，应保存完整错误，调查具体轮子、驱动或后端不匹配，不能随意换版本之后又把新环境当成原实验。环境变更可以是合理修复，但必须作为新条件记录，否则之后的性能差异很难解释。

**English:** Save the following as `launch_server.sh` and run it from the same directory as the virtual environment. It binds only to loopback, uses one device, limits the teaching context and running requests, and disables both graph phases for a simpler initial baseline. The static-memory fraction includes weights and the KV pool; it is not a percentage assigned exclusively to KV cache. The chosen values are conservative starting conditions rather than a promise of fit or optimal performance on an RTX 4060. Additional arguments support controlled one-flag comparisons. Avoid stacking several changes at once and then guessing which produced a benefit.

**中文：** 把下列内容保存为 `launch_server.sh`，在虚拟环境所在目录执行。服务只绑定本地回环地址，使用单设备，限制教学上下文和同时运行请求，并关闭两个阶段的计算图以建立较简单初始基线。静态内存比例包括权重与键值池，不是专门分给键值缓存的百分比。所选数值只是较保守的起始条件，并不保证在指定显卡上必然装得下或性能最佳。脚本保留额外参数入口，用于每次只改变一个开关的对照实验；不要一次堆叠多个修改再猜测收益来源。

```bash
#!/usr/bin/env bash
set -euo pipefail
exec .venv/bin/python -m sglang.launch_server \
  --model-path deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --revision ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562 \
  --host 127.0.0.1 --port 30000 \
  --dtype float16 --context-length 2048 \
  --mem-fraction-static 0.70 --max-running-requests 4 \
  --attention-backend triton --sampling-backend pytorch \
  --grammar-backend xgrammar --reasoning-parser deepseek-r1 \
  --cuda-graph-backend-decode disabled \
  --cuda-graph-backend-prefill disabled \
  --enable-metrics "$@"
```

```bash
bash launch_server.sh > server-cache-on.log 2>&1
```

**English:** Keep the server in its own terminal and use another terminal for requests. Wait for successful initialization, then verify the local model endpoint and send an ordinary nonstreaming request before benchmarking. A readiness response alone does not guarantee generation works. Retain the returned model identifier, server log, and package record with your results. If generation fails, resolve that failure before changing concurrency or cache settings; otherwise a performance experiment may actually compare two different failure modes. The minimal successful request checks that computation and delivery connect; it cannot establish stable throughput or tail latency.

**中文：** 服务器放在独立终端，另开终端发送请求。等待初始化成功后，检查本地模型接口，并在基准之前完成一次普通非流式生成；就绪接口有响应，不保证生成路径能够工作。把返回模型标识、服务日志和依赖记录与结果一起保存。生成失败时，应先解决该失败，再改变并发或缓存设置，否则所谓性能实验可能只是在比较两种不同失败方式。最小成功请求的目的，是确认计算与输出路径连通，而不是从一次请求推导稳定吞吐或尾延迟。

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
curl --fail --silent --show-error http://127.0.0.1:30000/generate \
  -H 'Content-Type: application/json' \
  -d '{"text":"Name one primary color.","sampling_params":{"temperature":0,"max_new_tokens":32},"stream":false}'
```

## 7. Complete workload and client / 完整负载与客户端

**English:** Save the following builder as `build_workload.py`. It uses the pinned tokenizer to generate exact-length token arrays. In shared mode, request-specific text is placed near the end; in different mode, it appears near the beginning, shortening the common prefix. Different mode does not promise zero shared tokens, because markers can still begin alike. These synthetic token sequences are intended to control serving work, not evaluate answer quality. `ignore_eos` in the client forces the requested output budget, so the output may continue beyond a natural completion and must not be presented as normal conversational behavior. A controlled workload must also state which features of a real service it simplifies.

**中文：** 把下列构造器保存为 `build_workload.py`，它用固定版本分词器生成长度确定的词元数组。共享模式把各请求特有内容放在末尾附近；差异模式把它放在开头，缩短共同前缀。差异模式不保证完全没有共享词元，因为标记开头仍可能相同。这些人造序列用于控制服务计算量，不用于评价回答质量。客户端忽略自然结束标志以执行指定输出预算，因此文本可能在自然完成后继续生成，不能把它展示成普通对话行为。受控负载必须同时说明它简化了哪些真实服务特征。

```python
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
REVISION = "ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--input-tokens", type=int, default=256)
    parser.add_argument("--output-tokens", type=int, default=32)
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--prefix", choices=["shared", "different"], default="shared")
    args = parser.parse_args()
    if args.input_tokens < 64 or args.output_tokens < 1 or args.requests < 1:
        parser.error("input>=64, output>=1, requests>=1 required")
    if args.input_tokens + args.output_tokens > 2048:
        parser.error("input plus output must fit the 2048-token teaching context")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    unit = tokenizer.encode(" This is a controlled serving workload.",
                            add_special_tokens=False)
    filler = (unit * (args.input_tokens // len(unit) + 2))[:args.input_tokens]
    rows = []
    for index in range(args.requests):
        marker = tokenizer.encode(f"Request {index:08d}: ", add_special_tokens=False)
        if len(marker) > 32:
            raise ValueError("marker unexpectedly exceeds reserved space")
        suffix = (marker + filler)[:32]
        ids = (filler[:args.input_tokens - 32] + suffix
               if args.prefix == "shared"
               else suffix + filler[:args.input_tokens - 32])
        rows.append({"id": index, "condition": {"prefix": args.prefix,
                     "input_tokens": len(ids), "output_tokens": args.output_tokens,
                     "model": MODEL, "revision": REVISION},
                     "input_ids": ids, "output_tokens": args.output_tokens})
    with args.output.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
```

**English:** Save the client as `client.py`. It parses complete SSE events rather than assuming each socket read is a JSON object, requires a completion marker, preserves HTTP and parsing failures, and records cumulative output-token counts. It writes results exclusively to a new file. The evidence field intentionally remains `unverified_service_response`: an HTTP response alone cannot prove which hardware executed it. Pair real runs with server logs and environment records before interpreting them as GPU measurements. The client uses blocking worker threads, so it is a readable teaching load generator rather than a claim of maximum client scalability. A high-concurrency study must additionally check whether the client itself becomes the limit.

**中文：** 客户端保存为 `client.py`。它解析完整流事件，不假定每次网络读取就是一个 JSON 对象；要求结束标记，保留网络和解析失败，并记录累积输出词元数。结果只写入新文件。证据字段刻意保留为未核实服务响应，因为单独收到网络响应，不能证明由什么硬件执行。只有配合服务日志和环境记录，真实运行才可解释为显卡测量。客户端采用阻塞工作线程，是便于阅读的教学负载生成器，并不宣称具有最大的客户端扩展能力；高并发研究还要评估客户端本身是否成为限制。

```python
import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median


def sse_objects(response):
    parts = []
    for raw in response:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":
            if not parts:
                continue
            payload = "\n".join(parts)
            parts = []
            if payload == "[DONE]":
                return
            yield json.loads(payload)
        elif line.startswith("data:"):
            parts.append(line[5:].lstrip(" "))
    if parts:
        raise ValueError("unterminated SSE event")
    raise ValueError("stream ended without DONE")


def run_one(base_url, item, *, evidence):
    start = time.perf_counter()
    first = last = None
    previous_count = 0
    single_token_events = True
    last_object = None
    counts = []
    record = {"id": item["id"], "condition": item["condition"],
              "evidence": evidence, "success": False,
              "prompt_sha256": hashlib.sha256(json.dumps(
                  item["input_ids"], separators=(",", ":")).encode()).hexdigest()}
    payload = {"input_ids": item["input_ids"], "stream": True,
               "sampling_params": {"temperature": 0,
                                   "max_new_tokens": item["output_tokens"],
                                   "ignore_eos": True}}
    request = urllib.request.Request(base_url + "/generate",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            for obj in sse_objects(response):
                now = time.perf_counter()
                if "error" in obj:
                    raise ValueError(str(obj["error"]))
                count = obj.get("meta_info", {}).get("completion_tokens")
                if type(count) is not int or count < previous_count:
                    raise ValueError("missing or decreasing completion_tokens")
                if count > previous_count:
                    single_token_events &= count == previous_count + 1
                    if first is None:
                        first = now
                    last = now
                    counts.append(count)
                previous_count = count
                last_object = obj
        end = time.perf_counter()
        if last_object is None or first is None:
            raise ValueError("no output token event")
        if previous_count != item["output_tokens"]:
            raise ValueError("actual output count differs from fixed workload budget")
        meta = last_object["meta_info"]
        record.update(success=True, observed_ttft_ms=(first - start) * 1000,
            e2e_ms=(end - start) * 1000,
            observed_tpot_ms=((last - first) * 1000 / (previous_count - 1)
                             if single_token_events and previous_count > 1 else None),
            completion_tokens=previous_count,
            prompt_tokens=meta.get("prompt_tokens"),
            event_token_counts=counts,
            finish_reason=meta.get("finish_reason"),
            cached_tokens=meta.get("cached_tokens"),
            text=last_object.get("text", ""))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        record.update(error=f"{type(exc).__name__}: {exc}",
                      e2e_ms=(time.perf_counter() - start) * 1000)
    return record


def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    return values[max(0, math.ceil(fraction * len(values)) - 1)]


def summarize(rows, wall_seconds):
    good = [row for row in rows if row["success"]]
    ttft = [row["observed_ttft_ms"] for row in good]
    e2e = [row["e2e_ms"] for row in good]
    tpot = [row["observed_tpot_ms"] for row in good
            if row["observed_tpot_ms"] is not None]
    return {"requests": len(rows), "successful_requests": len(good),
            "failed_requests": len(rows) - len(good), "wall_seconds": wall_seconds,
            "output_tokens_per_second": sum(r["completion_tokens"] for r in good)
                                        / wall_seconds,
            "ttft_median_ms": median(ttft) if ttft else None,
            "ttft_p95_ms": percentile(ttft, 0.95),
            "e2e_p95_ms": percentile(e2e, 0.95),
            "tpot_median_ms": median(tpot) if tpot else None,
            "tpot_eligible_requests": len(tpot)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workload", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("concurrency must be positive")
    items = [json.loads(line) for line in args.workload.read_text().splitlines()]
    if not items:
        parser.error("workload must not be empty")
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        rows = list(pool.map(lambda item: run_one("http://127.0.0.1:30000", item,
                         evidence="unverified_service_response"), items))
    wall = time.perf_counter() - start
    report = {"label": args.label, "concurrency": args.concurrency,
              "summary": summarize(rows, wall), "rows": rows}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(report["summary"], indent=2))
    return 0 if all(r["success"] for r in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
```

**English:** Save the test suite as `test_client.py`. Its server is explicitly a protocol fixture with invented text and metadata; it performs no tokenization or model inference. The tests validate parsing, failure retention, quantile arithmetic, and the throughput denominator. They do not assert a latency threshold, because timing this synthetic server would say nothing about SGLang. A malformed stream without a completion marker must fail even if some text was already received, preventing a truncated response from being counted as a successful benchmark request. The fixture establishes selected client protocol behaviors, not real serving scheduling, memory use, backend behavior, or generation quality.

**中文：** 测试保存为 `test_client.py`。其中服务器明确是协议测试替身，返回人为文本和元数据，不执行分词或模型推理。测试验证解析、失败保留、分位数算术和吞吐分母，不断言延迟阈值，因为测量这个人造服务不能说明 SGLang 性能。即使已经收到部分文本，缺少完成标记的畸形流也必须失败，避免把截断响应算成一次成功基准请求。测试替身能证明客户端遵守某些协议行为，但它没有覆盖真实服务的调度、显存、后端与生成质量，这是两种不同证据范围。

```python
import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from client import percentile, run_one, sse_objects, summarize


class FixtureHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if payload["input_ids"] == [999]:
            self.send_error(400, "synthetic rejection")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for count in range(1, 4):
            obj = {"text": "x" * count, "meta_info": {"completion_tokens": count,
                   "prompt_tokens": len(payload["input_ids"]), "cached_tokens": 0,
                   "finish_reason": {"type": "length"} if count == 3 else None}}
            self.wfile.write(("data: " + json.dumps(obj) + "\n\n").encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *args):
        pass


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_successful_synthetic_stream(self):
        item = {"id": 0, "condition": "fixture", "input_ids": [1, 2],
                "output_tokens": 3}
        row = run_one(self.url, item, evidence="synthetic_protocol_test")
        self.assertTrue(row["success"], row)
        self.assertEqual(row["completion_tokens"], 3)
        self.assertEqual(row["event_token_counts"], [1, 2, 3])
        self.assertEqual(row["text"], "xxx")
        self.assertEqual(row["evidence"], "synthetic_protocol_test")

    def test_http_error_is_retained(self):
        row = run_one(self.url, {"id": 1, "condition": "fixture",
            "input_ids": [999], "output_tokens": 3}, evidence="synthetic_protocol_test")
        self.assertFalse(row["success"])
        self.assertIn("HTTPError", row["error"])

    def test_incomplete_stream_rejected(self):
        source = io.BytesIO(b'data: {"text":"x"}\n\n')
        with self.assertRaisesRegex(ValueError, "without DONE"):
            list(sse_objects(source))

    def test_quantile_and_failure_denominator(self):
        row = {"success": True, "observed_ttft_ms": 4, "e2e_ms": 10,
               "observed_tpot_ms": None, "completion_tokens": 3}
        result = summarize([row, {"success": False}], 2)
        self.assertEqual(result["output_tokens_per_second"], 1.5)
        self.assertEqual(result["failed_requests"], 1)
        self.assertEqual(result["tpot_eligible_requests"], 0)
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4)


if __name__ == "__main__":
    unittest.main()
```

```bash
python3 -m unittest -v test_client.py
.venv/bin/python build_workload.py shared-256-32.jsonl --input-tokens 256 --output-tokens 32 --prefix shared
.venv/bin/python build_workload.py different-256-32.jsonl --input-tokens 256 --output-tokens 32 --prefix different
.venv/bin/python client.py shared-256-32.jsonl cache-on-c1.json --concurrency 1 --label cache-on-c1
```

**English:** The first command is CPU-only and requires no SGLang installation. The builder requires the tokenizer dependencies from the serving environment and may download tokenizer assets, while the client command requires the live local model server. On the current machine, only the client tests and source-level checks were executed; the tokenizer download, server launch, and measured workload were not executed. Four client tests passed under CPython 3.14.4. No numeric output from that fixture is included as a model performance result. Mark execution status by stage so readers can distinguish completed validation from a complete procedure that remains to be run.

**中文：** 第一条命令只用处理器，不要求安装 SGLang；构造器需要服务环境中的分词器依赖，可能下载分词资源，而客户端命令需要正在运行的本地模型服务。本机只执行了客户端测试和源码级检查，没有执行分词资源下载、服务器启动或正式测量负载。四个客户端测试在 CPython 三点十四点四下全部通过，测试替身的任何计时数值都没有被列为模型性能结果。分阶段标记执行状态，能让读者清楚哪些内容已经实际验证，哪些仍然是待执行的完整操作流程。

## 8. Controlled comparison matrix / 受控对照矩阵

**English:** Passing `input_ids` deliberately removes server-side text tokenization from this measured request path. It makes token lengths reproducible, but these runs cannot diagnose tokenizer throughput. Compare a separate text-input workload if that stage is the hypothesis, retaining the same resulting token sequences where possible. Similarly, disabling radix caching removes cross-request prefix reuse, not the within-request KV state required for ordinary autoregressive decoding. Identify which work a control removes before explaining a measured difference; otherwise a well-controlled experiment can still be given the wrong causal interpretation.

**中文：** 直接传入词元编号，有意把服务端文本分词移出本次测量路径。它使词元长度可复现，但这些运行不能诊断分词器吞吐。如果假设指向分词阶段，应另外构造文本输入负载，并尽量保持最终词元序列相同。同样，关闭前缀缓存移除的是跨请求前缀复用，不是普通自回归解码仍然需要的请求内部键值状态。解释差异之前，必须确认控制变量究竟移除了哪项工作，否则即使实验控制严谨，也可能得到错误的因果解释。

**English:** First compare cache enabled and disabled using the same shared workload at concurrency one. Start a fresh server for each condition, perform the same generic readiness request, and preserve the first measured request separately because it may create the prefix cache used by later requests. Stop the server normally in its terminal, then restart with the extra flag below for the disabled condition. Repeat the pair in reversed order with new output filenames to reduce time-order confounding. Compare both the first request and the later distribution rather than reporting a single blended median without explanation. Record experiment order because it can affect the result.

**中文：** 首先在并发一条件下，用相同共享负载比较缓存开关。每个条件启动新服务器，执行相同通用就绪请求，并单独保留第一次正式请求，因为它可能建立后续请求使用的前缀缓存。在服务器终端正常停止进程，再用下面额外开关启动关闭缓存条件。随后采用新输出文件名，反向顺序重复这组对照，减少先后时间带来的混淆。既比较首个请求，也比较后续分布，不应把两者混成一个中位数却不说明。实验顺序本身可能影响结果，必须进入记录。

```bash
bash launch_server.sh --disable-radix-cache > server-cache-off.log 2>&1
```

```bash
.venv/bin/python client.py shared-256-32.jsonl cache-off-c1.json --concurrency 1 --label cache-off-c1
```

**English:** Next hold cache state and lengths fixed while sweeping concurrency through 1, 2, and 4. Use at least the builder's forty requests per condition, and repeat the complete sweep rather than presenting one short burst as a stable capacity estimate. The server's maximum running count remains four, so higher client concurrency would increasingly probe queueing rather than simply enlarging an unconstrained batch. Save failures, output-token counts, and eligible TPOT counts with each condition. A p95 improvement based on fewer successful requests is not directly comparable to a complete run. The population being summarized has changed.

**中文：** 下一步固定缓存状态与长度，把并发依次设为一、二、四。每个条件至少使用构造器默认的四十个请求，并重复完整扫描，不要把一次短突发当作稳定容量估计。服务器最多同时运行四个请求，所以继续提高客户端并发，会越来越多地探测排队，而不只是无限扩大计算批次。每组保留失败、输出词元数和符合平均输出间隔计算条件的请求数。如果某组成功请求更少，即使尾延迟看起来改善，也不能直接与完整运行比较，因为被统计的样本集合已经改变。

```bash
.venv/bin/python client.py shared-256-32.jsonl sweep-c2.json --concurrency 2 --label sweep-c2
.venv/bin/python client.py shared-256-32.jsonl sweep-c4.json --concurrency 4 --label sweep-c4
```

**English:** For the length study, compare inputs of 256 and 1024 tokens while keeping output at 32, then compare outputs of 32 and 128 while keeping input at 256. Use the same cache policy and concurrency for each pair. Input plus output must fit the 2048-token teaching context. Do not infer exact prefill or decode cost by subtracting two end-to-end medians: queueing, batching, and cache reuse may also change. Treat the differences as service-level effects, then use traces or targeted lower-level experiments to localize the contributing work. Correct subtraction alone does not give the quantities the desired causal meaning.

**中文：** 长度实验先固定输出三十二，比较输入二百五十六与一千零二十四；再固定输入二百五十六，比较输出三十二与一百二十八。每组对照使用相同缓存策略与并发，输入加输出必须落在教学上下文容量内。不要直接用两个端到端中位数相减，声称得到了准确预填充或解码成本，因为排队、批处理与缓存复用也可能变化。应先把差异解释为服务层效应，再用时间线或有针对性的低层实验定位贡献。减法本身正确，并不意味着被相减的量具有你希望的因果含义。

```bash
.venv/bin/python build_workload.py different-1024-32.jsonl --input-tokens 1024 --output-tokens 32 --prefix different
.venv/bin/python build_workload.py different-256-128.jsonl --input-tokens 256 --output-tokens 128 --prefix different
.venv/bin/python client.py different-256-32.jsonl length-base.json --concurrency 1 --label length-base
.venv/bin/python client.py different-1024-32.jsonl length-input.json --concurrency 1 --label length-input
.venv/bin/python client.py different-256-128.jsonl length-output.json --concurrency 1 --label length-output
```

**English:** Record cache effectiveness as an observation, not an assumption derived from a flag. Preserve any returned cached-token metadata and consult the actual metrics exposed by the pinned server. A missing metadata field means unavailable information, not zero hits. Even high hit rates need not improve latency if another stage dominates or cache retention reduces useful admission capacity. The [production metrics reference](https://docs.sglang.io/docs/references/production_metrics) helps locate queue, token, and cache indicators; save the endpoint output so later analysis can verify the names and units used in your environment. Do not copy someone else's metric names without checking that the deployed version exposes the same meaning.

**中文：** 缓存效果应当记录为观测，而不是由启动开关推断。保留返回的缓存词元元数据，并查看固定版本服务器实际暴露的指标；字段缺失表示信息不可用，不表示命中数为零。即使命中率高，如果其他阶段主导延迟，或缓存保留减少了有用准入容量，也不一定改善用户体验。上述生产指标参考帮助定位队列、词元和缓存指标，应保存接口实际输出，使后续分析能核对环境中的名称与单位。不能只复制别人使用的指标名，而不检查自己部署版本是否具有相同含义。

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/metrics > metrics-after.txt
```

## 9. Structured generation and its boundaries / 结构化生成及其边界

**English:** Structured generation constrains which token sequences are allowed, commonly through a JSON schema or grammar. It can reduce malformed output and simplify downstream parsing, but valid structure does not establish factual correctness or successful task execution. A schema permitting an integer answer still permits the wrong integer. Also distinguish a complete structured result from generation stopped at a token limit. Record finish reason, raw response, schema validation, and task validation separately rather than allowing successful JSON parsing to stand in for all four. Format constraints restrict expression; factual and application correctness still need independent checks, so a structured object is not automatically a trusted executable action.

**中文：** 结构化生成通过 JSON 模式或语法限制允许的词元序列，可以减少格式损坏并简化下游解析，但结构有效不代表事实正确或任务成功。模式允许整数答案时，错误整数仍然符合结构；完整结构化结果也不同于达到词元上限后被截断的生成。应分别记录结束原因、原始响应、模式校验和任务校验，不能用 JSON 能解析代替全部四项。格式约束解决的是表达空间问题，事实与业务正确性仍需要独立判断，尤其不能把结构化结果直接当成可以执行的可信操作。

**English:** Reasoning models add another boundary between reasoning text and the final structured answer. The recipe selects `deepseek-r1` as its reasoning parser and `xgrammar` as the grammar backend, matching the concepts in the [official reasoning-model structured-output guide](https://docs.sglang.io/docs/advanced_features/structured_outputs_for_reasoning_models). A small output budget may be consumed before the final answer is complete. Do not apply the fixed-length benchmark's `ignore_eos` policy to this functional test. The goal here is a normally completed, validated answer, not a fixed amount of generated work. Functional validation and workload control answer different questions; configure and interpret them separately instead of distorting application behavior for attractive statistics.

**中文：** 推理模型在推理文本与最终结构化答案之间又增加了一道边界。本部署选择对应推理解析器和语法后端，遵循官方推理模型结构化输出指南的概念。输出预算较小时，模型可能在最终答案完整之前就耗尽预算。这里不能沿用固定长度性能实验忽略自然结束标志的策略，因为本测试目标是正常完成并通过校验的答案，而不是固定生成工作量。功能验证与负载控制服务于不同问题，应分别设置参数并分别解释结果，避免为了漂亮统计破坏正常应用行为。

**English:** Save the following as `structured.py` and run it only after the local server works. It preserves the raw response before validation, requires normal completion, checks a small explicit schema, and verifies the factual answer independently. A truncation or backend error should remain a failed result for diagnosis. This example has been syntax-checked but not executed against the teaching model in the current GPU environment. If the chosen model and backend do not complete the constrained answer, report that observed limitation rather than replacing its output with an invented successful object. Runnable code and evidence of a successful run are distinct, and a complete tutorial should preserve actual validation status.

**中文：** 把下例保存为 `structured.py`，仅在本地服务器正常工作后执行。程序在校验之前保存原始响应，要求正常完成，检查小型明确模式，并独立验证事实答案。截断或后端错误应保留为失败结果用于诊断。本例已进行语法检查，但当前 GPU 环境没有执行教学模型请求。如果所选模型与后端无法完成约束答案，应报告该观察到的限制，不能用编造的成功对象替代模型输出。可运行代码与已经运行成功的证据必须分开，完整教程也不应掩盖实际验证状态。

```python
import json
import urllib.request
from pathlib import Path

schema = {"type": "object", "properties": {"answer": {"type": "integer"},
          "unit": {"type": "string", "enum": ["count"]}},
          "required": ["answer", "unit"], "additionalProperties": False}
payload = {"model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
           "messages": [{"role": "user", "content":
               "How many letters are in CUDA? Return answer and unit=count."}],
           "temperature": 0, "max_tokens": 512, "stream": False,
           "response_format": {"type": "json_schema", "json_schema": {
               "name": "letter_count", "schema": schema}}}
request = urllib.request.Request("http://127.0.0.1:30000/v1/chat/completions",
    data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, timeout=120) as response:
    raw = json.load(response)
with Path("structured-response.json").open("x", encoding="utf-8") as stream:
    json.dump(raw, stream, ensure_ascii=False, indent=2)
choice = raw["choices"][0]
if choice["finish_reason"] != "stop":
    raise ValueError(f"generation did not finish normally: {choice['finish_reason']}")
answer = json.loads(choice["message"]["content"])
if (not isinstance(answer, dict) or set(answer) != {"answer", "unit"}
        or type(answer["answer"]) is not int or answer["unit"] != "count"):
    raise ValueError("response violates the teaching schema")
if answer["answer"] != 4:
    raise ValueError("schema valid but factual answer is wrong")
print("syntax, schema, completion, and task checks passed")
```

```bash
.venv/bin/python structured.py
```

## 10. Diagnose the CPU–GPU boundary / 诊断主机与设备边界

**English:** Start diagnosis from the whole symptom pattern. Rising TTFT with roughly stable output pacing and a growing queue suggests admission or prefill pressure as an initial hypothesis. Long gaps between device launches suggest host preparation, synchronization, or unavailable work. A continuously busy device with a dominant attention or matrix kernel suggests a different investigation. None is a proof by itself. Correlate request identifiers, phase boundaries, queue observations, and the device timeline before changing a kernel, because the same utilization percentage can coexist with several different limiting mechanisms. Form a hypothesis, then seek evidence that could disprove it.

**中文：** 诊断应从整组症状出发。首词元延迟升高、后续输出节奏大致稳定且队列增长，可以先假设准入或预填充压力；设备任务之间出现长空隙，则应调查主机准备、同步或没有可执行工作；设备持续繁忙且某个注意力或矩阵核函数占主导，又对应另一条调查路径。这些都不是单独充分证明。修改核函数前，应关联请求编号、阶段边界、队列观测与设备时间线，因为相同利用率可能同时对应多种不同限制机制。先提出假设，再寻找能够推翻它的证据。

**English:** Nsight Systems can show host calls, CUDA activity, and NVTX ranges across the process tree, while a kernel profiler answers more specific device-efficiency questions. Use a short representative workload for tracing and a separate unprofiled run for service metrics, because instrumentation can change timing. The command below wraps the same launcher, preserving its model and flags. Nsight tooling and permissions must be available on the healthy GPU machine. No trace is claimed for the current NVML-failing environment; the [official profiling guide](https://docs.sglang.io/docs/developer_guide/benchmark_and_profiling) provides additional supported collection paths. Keep tool output with the actual collection command and workload so it can be interpreted.

**中文：** 系统级分析器可以跨进程展示主机调用、CUDA 活动与标记范围，而核函数分析器回答更具体的设备执行效率问题。采集时间线应使用短而有代表性的负载，服务指标则另做不带分析器的运行，因为插桩可能改变时间。下列命令包装同一个启动脚本，保留模型与参数；健康显卡机器还必须具备工具和采集权限。本课没有声称在当前 NVML 失败环境生成过时间线，更多受支持采集方式见官方分析指南。工具输出必须与实际采集命令和负载一起保存，才具备解释价值。

```bash
nsys profile --trace=cuda,nvtx,osrt --output=sglang-course10 bash launch_server.sh
```

**English:** When a CPU region precedes a GPU idle gap, inspect whether it actually lies on the critical path. Some CPU work may execute concurrently with useful device work and therefore be harmless to latency. Conversely, a short synchronization can block dispatch of an entire next batch. Follow dependencies and ready-work availability rather than summing all CPU durations. Change one candidate factor, such as overlap scheduling, and check whether the predicted gap and the service symptom both change. If only one changes, refine the hypothesis instead of declaring victory from a single faster number. Causal validation needs the mechanism and outcome to correspond.

**中文：** 如果某段主机活动出现在显卡空隙之前，应检查它是否真的位于关键路径。一部分主机工作可能与有效设备工作并行，对延迟没有影响；反过来，一个很短的同步也可能阻止整个下一批任务发出。应追踪依赖和就绪工作，而不是累加全部处理器时间。改变一个候选因素，例如重叠调度，再检查预测中的空隙与服务症状是否同时变化。如果只改变其中一个，就应修正假设，而不是看到一个数变快便宣告成功。因果验证要求机制与结果能够对应起来。

**English:** A useful final report states the hypothesis, fixed conditions, changed variable, measurements, counterevidence, and remaining uncertainty. For example, “prefix reuse reduced observed first-token latency after the first request under concurrency one” is a narrower claim than “the model is faster.” Do not extrapolate the small dense model's behavior to large MoE, multi-node, disaggregated prefill/decode, or another accelerator. The point of this course is to build a method that can be reapplied, with new evidence, when the system changes. Methods transfer, but each new conclusion needs evidence from its new environment.

**中文：** 有用的最终报告应写出假设、固定条件、改变变量、测量、反证和剩余不确定性。例如，在并发一条件下，首个请求之后的前缀复用降低了观察到的首词元延迟，比笼统声称模型变快更准确。不要把小型稠密模型结果外推到大型混合专家、多机、预填充与解码分离部署，或另一种加速器。本课要建立的是系统改变之后仍可重新应用的方法，而不是一份永远有效的参数答案。方法可以迁移，但每个新结论都需要对应环境中的新证据。

## 11. Ten exercises with reference answers / 十道习题与参考答案

### Exercise 1: First-token latency / 习题一：首词元延迟

**English:** Exercise: TTFT doubles while a directly measured prefill kernel takes the same time. Is the result contradictory? Reference answer: no. Queueing, admission, tokenization, host dispatch, or response buffering may have increased. Match the client timestamp interval to server phases and inspect the waiting queue before attributing the change to device computation. The two measurements have different boundaries. A useful follow-up changes offered load while keeping input length and cache condition fixed, then checks whether queue growth and TTFT move together. A complete answer proposes an experiment that distinguishes causes rather than only listing possibilities.

**中文：** 练习：首词元延迟翻倍，但直接测得的预填充核函数耗时不变，是否矛盾？参考答案：不矛盾，排队、准入、分词、主机发起或响应缓冲都可能增加。应把客户端时间区间与服务阶段对应，先检查等待队列，再归因到设备计算。这两个指标边界不同，不能直接互相替代。后续可以固定输入长度与缓存条件，只改变送入负载，观察队列增长和首词元延迟是否共同变化。完整答案应提出一个可区分原因的实验，而不只是列出很多可能性。

### Exercise 2: Input and output lengths / 习题二：输入与输出长度

**English:** Exercise: Which is more decode-heavy: a long document requesting one word, or a short question requesting a long explanation? Reference answer: the latter typically requires more sequential output steps, although total latency still depends on model and workload. The former emphasizes input processing and retained context. Count actual input and output tokens rather than using a document's file size or assuming the maximum output cap was reached. A request that stops early can invalidate an intended fixed-length comparison unless that behavior is controlled or reported. Judge phase pressure from completed work rather than how long the user's question looks on screen.

**中文：** 练习：长文档只要求一个词，与短问题要求长篇解释，哪种更偏重解码？参考答案：后者通常需要更多连续输出步骤，但总延迟仍取决于模型与负载；前者主要增加输入处理与保留上下文。应统计实际输入输出词元，而不是使用文档文件大小，或假定输出必然达到最大预算。提前停止的请求可能破坏原本的固定长度对照，除非明确控制或报告该行为。判断阶段压力应依据实际完成的工作量，而不能只看用户问题在屏幕上有多长。

### Exercise 3: KV memory estimate / 习题三：键值显存估算

**English:** Exercise: Why would using twelve query heads instead of two KV heads overestimate this model's KV storage by six times? Reference answer: grouped-query attention shares keys and values across groups of query heads, so cached state is indexed by the KV-head count. The simple formula counts stored K and V arrays, not all query computation. The resulting 56 MiB estimate for 2048 tokens excludes weights and runtime overhead. A monitoring value larger than that is therefore not automatically a leak; compare the accounted components before making that claim. An estimate is useful only when every term and deliberate omission is understood.

**中文：** 练习：为什么用十二个查询头代替两个键值头，会把本模型键值存储高估六倍？参考答案：分组查询注意力让多组查询头共享键和值，缓存状态由键值头数决定。简单公式计算保存的键值数组，而不是全部查询计算。两千零四十八词元约五十六兆二进制字节的估算，没有包含权重和运行时开销。监控值大于它不自动意味着泄漏，应先对照各组成部分的核算。估算有用的前提，是知道每一项代表什么以及哪些项被刻意省略。

### Exercise 4: Prefix identity / 习题四：前缀身份

**English:** Exercise: Two prompts end with the same large document but begin with different user-specific instructions. Should full document-prefix reuse be expected? Reference answer: no; reuse concerns an identical leading token sequence, and the differing beginning breaks that sequence before the shared document. Reordering content may improve reuse but can change prompt semantics, so it requires functional validation as well as timing. Compare token arrays and template application rather than judging identity from a visual inspection of the shared text. Changing model input for cache reuse changes application behavior too; verify that answers still satisfy the original task.

**中文：** 练习：两个提示末尾是相同大文档，开头却是不同用户指令，是否应该期待完整文档前缀复用？参考答案：不应该，复用关注相同的起始词元序列，而开头差异在文档之前就打断了它。重排内容可能改善复用，但也可能改变提示语义，因此需要功能校验与性能测试同时进行。应比较词元数组与模板应用结果，不要只看共享文本视觉上是否相同。为了提高缓存命中而改变模型输入，本质上也改变了应用行为，必须验证答案仍满足原任务要求。

### Exercise 5: Concurrency and capacity / 习题五：并发与容量

**English:** Exercise: Concurrency rises from two to four, throughput barely changes, and p95 latency rises sharply. Is four automatically the better setting? Reference answer: no. The system may already be saturated, so extra requests mainly wait. Examine success rate, queue length, token counts, and the latency objective. A lower concurrency can provide more useful completed work within the required deadline. The conclusion should state the observed load model because a closed-loop test does not establish behavior under an arbitrary fixed external arrival rate. Capacity evaluation must include timely completions and failures instead of selecting the largest throughput entry as the deployment setting.

**中文：** 练习：并发从二变四，吞吐几乎不变，尾延迟却明显上升，四是否自动更好？参考答案：不是，系统可能已经饱和，新增请求主要在等待。应检查成功率、队列长度、词元数量和延迟目标；较低并发可能在要求的期限内提供更多有用完成量。结论还要说明观察到的负载模型，因为闭环测试不能证明任意固定外部到达率下的行为。评价容量需要同时考虑按时完成与失败情况，不能只选一列最大的吞吐数作为最终部署设置。

### Exercise 6: Stream chunks / 习题六：流式块

**English:** Exercise: The first streamed event reports five output tokens. Can its arrival time and later chunk intervals produce exact token-level TTFT and ITL? Reference answer: no. The first five tokens may have been buffered together, and their individual creation or arrival times are unavailable. Preserve the event time as a client-observed chunk boundary and mark token-level estimates unavailable or explicitly approximate. This client's TPOT eligibility check rejects such grouped increments rather than silently treating one event as one token. Name metrics after what was actually observed, and preserve missing information as part of the result.

**中文：** 练习：第一个流事件报告五个输出词元，能否用它的到达时间和后续块间隔得到精确词元级首延迟与间隔？参考答案：不能，前五个词元可能被一起缓冲，单独生成或到达时间已经不可见。应保留事件时间作为客户端观察到的块边界，把词元级估计标成不可用或明确近似。本客户端的平均输出间隔资格检查会拒绝这种成组增长，不会悄悄把一个事件当成一个词元。指标命名必须跟随真正观测到的对象，缺失信息也应作为结果保留。

### Exercise 7: Structured correctness / 习题七：结构化正确性

**English:** Exercise: A generated object has integer `answer=5` and `unit="count"` for the number of letters in CUDA. Which checks pass? Reference answer: parsing and the small teaching schema can pass, while the task check fails because the answer is four. Normal completion must also be checked independently. Grammar constraints reduce the set of possible outputs but do not select a factually correct member of that set. Keep the raw response and classify the failure so that schema problems and model-answer problems are not combined into one ambiguous error rate. Accurate classification tells downstream systems whether to retry formatting, revise the task prompt, or reject the application result.

**中文：** 练习：模型对 CUDA 字母数量返回整数五和单位计数，哪些检查能够通过？参考答案：解析与教学模式检查可能通过，但任务检查失败，因为正确数量是四；是否正常完成还要另外检查。语法约束缩小可输出集合，却不会自动从中选择事实正确的一项。应保留原始响应并分类失败，避免把结构错误与模型答案错误混成一个含糊错误率。下游系统需要知道是重试格式、修改任务提示，还是拒绝业务结果，这些动作依赖准确的失败分类。

### Exercise 8: Host-side gaps / 习题八：主机侧空隙

**English:** Exercise: A timeline shows GPU idle intervals preceded by scheduler activity. Does that prove rewriting a CUDA attention kernel is the next step? Reference answer: no. Investigate whether ready device work is delayed by host preparation, synchronization, or resource admission. Correlate the scheduler range with launches and test one relevant change. If the gaps disappear and one device kernel then dominates, kernel analysis becomes better motivated. Optimize the currently supported bottleneck hypothesis instead of selecting a tool solely because the overall project uses a GPU. Let the diagnostic question determine the tool.

**中文：** 练习：时间线显示显卡空闲区间前有调度器活动，这是否证明下一步应重写注意力核函数？参考答案：不是，应调查已经就绪的设备工作是否被主机准备、同步或资源准入延迟。把调度范围与启动事件对应，再测试一个相关修改。如果空隙消失、某个设备核函数开始主导，进一步分析核函数才更有依据。优化应针对当前证据支持的瓶颈假设，不能因为整个项目使用 GPU，就预先认定所有问题都应由核函数代码解决。工具选择需要服从诊断问题。

### Exercise 9: Comparing cache runs / 习题九：比较缓存实验

**English:** Exercise: Cache-on is tested after several rehearsals, while cache-off is tested immediately after process startup. Why is the comparison weak? Reference answer: it mixes prefix reuse with initialization, kernel warmup, possibly grammar compilation, and time-order effects. Restart each condition, use the same generic readiness procedure, identify first-request behavior, and repeat in reverse order. Preserve the workload and version records. A lower median alone cannot identify which of these changed factors caused the difference, even if the desired cache explanation is plausible. A controlled experiment reduces these alternative explanations for the result.

**中文：** 练习：开启缓存条件在多次演练后测试，关闭条件却在进程刚启动时测试，比较为什么不可靠？参考答案：它混合了前缀复用、初始化、核函数预热、可能的语法编译，以及先后时间影响。应在每个条件重新启动，采用相同通用就绪流程，标识首请求行为，并反向重复顺序，保留负载与版本记录。即使缓存解释看起来合理，单独较低中位数也不能确定是哪项变化导致差异。受控实验的价值，正是减少这些同样可以解释结果的替代原因。

### Exercise 10: What was actually verified / 习题十：实际验证了什么

**English:** Exercise: All four local client tests pass, but NVML still fails. What can the report claim? Reference answer: the synthetic protocol parser, failure handling, and selected aggregation rules passed on the recorded CPU interpreter. It cannot claim that the model loaded, the pinned serving backend executed correctly, or any GPU speedup occurred. Preserve those remaining steps as unexecuted validation work and run them on a healthy device before adding numerical performance conclusions. Honest evidence boundaries make the completed CPU work useful without overstating it. This lets the CPU work be reused reliably without mistaking a protocol demonstration for acceptance of a complete inference system.

**中文：** 练习：四个本地客户端测试全部通过，但 NVML 仍失败，报告可以声称什么？参考答案：在记录的处理器解释器环境中，人造协议解析、失败处理和所选聚合规则通过测试；不能声称模型已加载、固定服务后端正确执行，或发生任何显卡加速。其余步骤应保留为未执行验证工作，在健康设备上完成之后才能加入数值性能结论。明确证据边界不会削弱已经完成的处理器工作，反而让它可以可靠复用，避免读者把协议演示误读成完整推理系统验收。

## Acceptance and next investigation / 验收与下一项调查

**English:** The CPU acceptance boundary is the four passing client tests, successful syntax checks of the builder and structured-output script, and hand verification of the KV estimate. GPU acceptance additionally requires a recorded environment, successful real generation, reproducible cache and concurrency comparisons, retained failures, and a trace supporting one explicit bottleneck hypothesis. The current document satisfies only the CPU and source-verification boundary. Keep the GPU result cells unmeasured until those procedures actually run; do not fill them with expected values or numbers from unrelated hardware. Unmeasured is an accurate status that identifies the evidence still needed, not a blank to conceal.

**中文：** 处理器侧验收边界包括四个客户端测试通过、负载构造器与结构化脚本语法检查成功，以及键值容量估算手算核对。显卡侧还需要环境记录、真实生成成功、可复现缓存与并发对照、保留失败，以及支持一个明确瓶颈假设的时间线。本文当前只达到处理器和源码核验边界。显卡结果在真正执行流程前应保持未测，不能用预期值或其他硬件数字填充。未测是一种准确状态，能够直接指出下一步需要取得什么证据，而不是需要掩盖的空白。

**English:** After a healthy baseline is available, choose one next investigation based on evidence: admission and queueing, prefix reuse, CPU scheduling overlap, or a dominant device kernel. Change one layer, retain the same workload contract, and check correctness as well as latency and throughput. Large-model deployment, multi-GPU communication, and disaggregated serving are separate future studies with new capacity and failure models. The transferable skill is connecting a user-visible symptom to an execution mechanism and designing a comparison that could disprove your explanation. This moves learning from remembering server flags toward independently diagnosing a real inference system.

**中文：** 获得健康基线之后，应依据证据选择下一项调查：准入排队、前缀复用、主机调度重叠，或主导设备核函数。每次改变一层，保留相同负载契约，同时检查正确性、延迟和吞吐。大型模型、多显卡通信以及分离式部署属于之后的独立研究，需要新的容量与故障模型。真正能够迁移的能力，是把用户可见症状连接到执行机制，并设计可能推翻自己解释的对照实验。这样学习才会从记住服务参数，走向能够独立诊断真实推理系统。

## Official references / 官方参考资料

**English:** These primary sources were checked on 2026-09-18. Versioned release and model files take precedence for reproducing this recipe; rolling documentation is useful for concepts and discovering changed interfaces. The original workload, client, and protocol tests above are teaching code, not an upstream performance benchmark result.

**中文：** 以下一手来源于二〇二六年九月十八日核验。复现本流程时优先使用固定发行版与模型文件，滚动文档用于理解概念和发现接口变化。上方原创负载、客户端和协议测试属于教学代码，不是上游性能基准结果。

- [SGLang v0.5.19 release / 固定发行版](https://github.com/sgl-project/sglang/releases/tag/v0.5.19)
- [Versioned server arguments / 固定版本服务参数](https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/srt/server_args.py)
- [Versioned sampling parameters / 固定版本采样参数](https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/srt/sampling/sampling_params.py)
- [Versioned dependencies / 固定版本依赖声明](https://github.com/sgl-project/sglang/blob/v0.5.19/python/pyproject.toml)
- [Model card / 模型说明](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B)
- [Pinned model configuration / 固定模型配置](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B/blob/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562/config.json)
- [Installation / 安装](https://docs.sglang.io/docs/get-started/install)
- [Sending requests / 发送请求](https://docs.sglang.io/docs/basic_usage/send_request)
- [Structured outputs / 结构化输出](https://docs.sglang.io/docs/advanced_features/structured_outputs)
- [Reasoning-model structured outputs / 推理模型结构化输出](https://docs.sglang.io/docs/advanced_features/structured_outputs_for_reasoning_models)
- [Production metrics / 生产指标](https://docs.sglang.io/docs/references/production_metrics)
- [Benchmarking and profiling / 基准与性能分析](https://docs.sglang.io/docs/developer_guide/benchmark_and_profiling)
- [Original SGLang paper / 原始研究论文](https://arxiv.org/abs/2312.07104)
