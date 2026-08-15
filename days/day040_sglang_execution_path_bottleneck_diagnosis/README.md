# Day 040: SGLang Execution Path and Layered Bottleneck Diagnosis / SGLang 执行路径与分层瓶颈定位

Date / 日期: 2026-08-15

## Topic / 主题

**English:** A concept study of the SGLang request execution path, including
request preprocessing, scheduling, prefill and decode batches, model execution,
attention backends, paged KV-cache access, CUDA Graph replay, CPU–GPU overlap,
timeline analysis, and layered bottleneck diagnosis.

**中文：** 概念学习 SGLang 的请求执行路径，包括请求预处理、调度、prefill 与
decode batch、模型执行、attention backend、分页式 KV cache 访问、CUDA Graph
replay、CPU–GPU 重叠、时间线分析与分层瓶颈定位。

## Goal / 目标

**English:** Learn to follow one request from the service boundary to GPU
execution and back to streamed output, assign each responsibility to the
correct runtime layer, and turn a latency or throughput symptom into a
testable bottleneck hypothesis.

**中文：** 学会沿着一次请求从服务入口追踪到 GPU 执行，再回到流式输出；把每项
职责归到正确的 runtime 层，并把延迟或吞吐异常转化为可验证的瓶颈假设。

## Core Mental Model / 核心思维模型

**English:** Treat inference serving as a pipeline whose adjacent layers
exchange both data and control: the request layer parses and tokenizes work;
the scheduler selects runnable sequences and manages token and cache budgets;
the model runner prepares a forward batch; attention and other operator
backends launch GPU work; completion data is sampled, decoded, and streamed.
A delay observed at the API boundary is the sum of waiting, CPU preparation,
GPU execution, synchronization, and output-delivery time, so no single metric
identifies a layer by itself.

**中文：** 把推理服务看作相邻层之间同时传递数据与控制信息的 pipeline：请求层
解析请求并完成 tokenization；scheduler 选择可运行序列并管理 token 与 cache
预算；model runner 准备 forward batch；attention 与其他算子 backend 启动 GPU
工作；完成后的数据再经过采样、解码与流式返回。API 边界观察到的延迟，是排队、
CPU 准备、GPU 执行、同步与输出传输时间之和，因此单个指标不能独自确定瓶颈层。

## 10 Concept Questions / 10 个概念问题

### 1. End-to-end request path / 端到端请求路径

**Question (English):** Put these activities into a reasonable execution
order: scheduling, tokenization, model forward, request parsing, token
sampling, GPU-kernel execution, detokenization, and streaming the result. Which
activities are primarily control-plane work, and which perform the numerical
model computation?

**问题（中文）：** 请把以下活动按合理执行顺序排列：scheduling、tokenization、
model forward、请求解析、token sampling、GPU kernel 执行、detokenization 与
流式返回结果。哪些活动主要属于控制面工作，哪些活动执行模型数值计算？

**Explanation (English):** Following the data transformations prevents a
common category error: the scheduler decides what should run, while the model
and its kernels perform the selected numerical work. Real implementations may
pipeline or overlap neighboring activities, but the logical dependencies
remain.

**解说（中文）：** 沿数据转换过程追踪，可以避免一种常见的分类错误：scheduler
决定哪些工作应当运行，模型及其 kernel 执行已经选中的数值计算。真实实现可能让
相邻活动形成 pipeline 或相互重叠，但逻辑依赖关系仍然存在。

**Correct Answer (English):** A reasonable logical order is: parse and
validate the request, tokenize the input, enqueue and schedule the request,
prepare and execute a model forward whose operators launch GPU kernels, sample
the next token, detokenize the result, and stream it to the client. Scheduling
and batch construction are primarily control-plane work. The model forward,
including attention, matrix multiplication, and related GPU kernels, performs
the main numerical computation. Sampling and tokenization or detokenization
sit at the boundaries and may use CPU or GPU implementations depending on the
configuration.

**正确答案（中文）：** 一个合理的逻辑顺序是：解析并校验请求、对输入进行
tokenization、把请求入队并调度、准备并执行 model forward（其中各算子启动 GPU
kernel）、采样下一个 token、detokenization，最后把结果流式返回客户端。
Scheduling 与 batch 构建主要属于控制面工作；model forward 中的 attention、
矩阵乘法及相关 GPU kernel 执行主要数值计算。采样与
tokenization/detokenization 位于边界，其实现会根据配置运行在 CPU 或 GPU 上。

### 2. Scheduler and model-runner responsibilities / Scheduler 与 Model Runner 的职责

**Question (English):** Why should the scheduler not be described as the
component that “runs the transformer”? What information does it produce for
the model runner, and what result does the model runner return?

**问题（中文）：** 为什么不应把 scheduler 描述成“运行 transformer”的组件？
它会为 model runner 产生哪些信息，model runner 又会返回什么结果？

**Explanation (English):** Separating policy from execution makes diagnosis
more precise. Queue order, admission, batch composition, token budgets, and
KV-cache availability belong to scheduling policy; tensor preparation and
operator execution belong to the model-execution path.

**解说（中文）：** 把策略与执行分开，可以让诊断更精确。队列顺序、请求准入、
batch 组成、token budget 与 KV cache 可用量属于调度策略；tensor 准备与算子执行
属于模型执行路径。

**Correct Answer (English):** The scheduler selects requests, decides whether
the next work is prefill, decode, or another supported forward mode, reserves
the required token and cache capacity, and constructs metadata describing the
batch. The model runner consumes tensors and this metadata, invokes the model
and its operator backends, and returns outputs such as logits or hidden states
needed by sampling and later runtime steps. The scheduler orchestrates the
transformer execution but does not itself implement every transformer
operator.

**正确答案（中文）：** Scheduler 选择请求，决定下一批工作属于 prefill、decode
还是其他受支持的 forward mode，预留所需 token 与 cache 容量，并构造描述 batch
的 metadata。Model runner 消费 tensor 与这些 metadata，调用模型及其算子
backend，再返回采样和后续 runtime 步骤所需的 logits、hidden state 等输出。
Scheduler 编排 transformer 执行，但并不亲自实现每个 transformer 算子。

### 3. Prefill or extend versus decode / Prefill 或 Extend 与 Decode

**Question (English):** Why do an input-heavy prefill batch and a decode batch
with the same number of requests produce different tensor shapes and
performance behavior? Why might an attention backend expose separate extend
and decode paths?

**问题（中文）：** 为什么请求数相同的输入密集型 prefill batch 与 decode batch
会产生不同的 tensor shape 和性能表现？Attention backend 为什么可能分别提供
extend 与 decode 路径？

**Explanation (English):** Request count alone does not describe the amount or
shape of work. Prefill or extend can process many new query tokens per request,
whereas ordinary autoregressive decode usually advances each active request by
one token while reading its existing KV cache.

**解说（中文）：** 仅凭请求数无法描述工作量及其形态。Prefill 或 extend 可以为
每个请求处理许多新的 query token；普通自回归 decode 通常让每个活跃请求只推进
一个 token，同时读取其已有 KV cache。

**Correct Answer (English):** Prefill or extend batches may contain a large
and uneven number of new tokens, creating larger matrix operations and more
parallel work while writing KV states for those tokens. A normal decode batch
typically has one new query token per active sequence, repeatedly reads a much
larger history from the KV cache, and often becomes sensitive to memory access,
launch overhead, and batch size. Separate paths let an attention backend use
phase-appropriate metadata layouts and kernels instead of forcing both shapes
through one implementation.

**正确答案（中文）：** Prefill 或 extend batch 可能包含大量且长度不均的新
token，形成更大的矩阵运算与更多并行工作，同时写入这些 token 的 KV state。普通
decode batch 通常每个活跃序列只有一个新 query token，却要反复读取更长的历史
KV cache，因此常对显存访问、launch overhead 与 batch size 更敏感。分离路径让
attention backend 能为不同阶段使用合适的 metadata 布局与 kernel，而不必强行用
同一种实现处理两类 shape。

### 4. Asynchronous GPU execution and timing / GPU 异步执行与计时

**Question (English):** A CPU-side log reports that a model-forward function
returned in 0.2 ms, but a profiler shows 8 ms of GPU work launched by that
function. Is either measurement necessarily wrong? What boundary must be
defined before interpreting the 0.2 ms value?

**问题（中文）：** CPU 端日志显示一次 model-forward 函数在 0.2 ms 内返回，但
profiler 显示该函数启动了 8 ms 的 GPU 工作。两个测量中是否必有一个错误？解释
0.2 ms 之前必须先定义什么边界？

**Explanation (English):** CUDA launches are normally asynchronous with
respect to the host. A host timer can measure enqueue or submission time while
GPU work continues after the function returns. An implicit or explicit
synchronization later may absorb the outstanding time.

**解说（中文）：** CUDA launch 相对于 host 通常是异步的。Host timer 可能只测到
入队或提交时间，而 GPU 工作会在函数返回后继续执行；之后某个显式或隐式同步点
可能承担尚未完成的等待时间。

**Correct Answer (English):** Both measurements can be correct. The 0.2 ms
value may measure only CPU preparation and asynchronous launch submission,
while the GPU timeline measures actual device execution. Before interpreting
the host value, define whether the interval ends at launch submission, at a
CUDA event on the relevant stream, or after synchronization. Use CUDA events
or a timeline profiler for device duration, and include synchronization only
when it matches the latency boundary being investigated.

**正确答案（中文）：** 两个测量都可能正确。0.2 ms 可能只包含 CPU 准备与异步
launch 提交，而 GPU 时间线测量的是实际 device 执行。解释 host 计时前，必须明确
区间是结束于 launch 提交、相关 stream 上的 CUDA event，还是同步完成之后。测量
device 时长应使用 CUDA event 或时间线 profiler；只有当同步符合待调查的延迟
边界时，才应把同步时间计入。

### 5. CUDA Graph replay with dynamic batches / 动态 Batch 下的 CUDA Graph Replay

**Question (English):** What overhead can CUDA Graph replay reduce during
decode? Why do changing batch shapes, graph capture sizes, or padding mean that
enabling graphs does not guarantee a speedup?

**问题（中文）：** CUDA Graph replay 在 decode 期间可以减少什么开销？为什么
不断变化的 batch shape、graph capture size 或 padding 意味着启用 graph 并不保证
加速？

**Explanation (English):** A graph replays a captured sequence of GPU
operations with lower repeated host launch overhead. It does not automatically
make the captured kernels faster, and replay requires inputs and metadata to
fit a compatible captured shape and memory arrangement.

**解说（中文）：** Graph 以较低的重复 host launch overhead 回放一段已捕获的 GPU
操作序列。它不会自动让被捕获的 kernel 本身变快，而且 replay 要求输入与 metadata
适配兼容的 capture shape 和内存布局。

**Correct Answer (English):** CUDA Graph replay can reduce Python or C++ host
dispatch, per-kernel launch, and repeated graph-construction overhead on a
stable decode path. A dynamic batch may need a compatible captured size,
padding to a larger size, or an eager fallback. Too few captured sizes can
waste GPU work through padding or cause frequent fallbacks; too many can add
capture time and memory cost. Graph benefit is largest when launch overhead is
material and replay coverage is high, so graph usage, padded batch size, and
fallback frequency must be measured together with TPOT and throughput.

**正确答案（中文）：** CUDA Graph replay 可以减少稳定 decode 路径上的 Python
或 C++ host dispatch、逐 kernel launch 以及重复构图开销。动态 batch 可能需要
匹配某个已捕获尺寸、padding 到更大尺寸，或者回退到 eager 执行。捕获尺寸过少会
因 padding 浪费 GPU 工作或产生频繁 fallback；捕获过多又会增加 capture 时间与
显存成本。只有当 launch overhead 占比较大且 replay 覆盖率高时，graph 收益才
明显，因此必须把 graph 使用情况、padding 后 batch size、fallback 频率与 TPOT、
吞吐量一起测量。

### 6. Attention-backend boundaries / Attention Backend 边界

**Question (English):** What problem does an attention backend solve between
the model runner and GPU kernels? Why is it unsafe to claim that one backend is
always the fastest for every SGLang deployment?

**问题（中文）：** Attention backend 在 model runner 与 GPU kernel 之间解决什么
问题？为什么不能断言某个 backend 对所有 SGLang 部署都始终最快？

**Explanation (English):** The backend turns phase-specific attention inputs,
KV-cache page tables, sequence lengths, and other metadata into supported
kernel calls. Its best implementation depends on compatibility as well as
performance.

**解说（中文）：** Backend 把不同阶段的 attention 输入、KV cache page table、
序列长度及其他 metadata 转化为受支持的 kernel 调用。最佳实现不仅取决于性能，
也取决于兼容性。

**Correct Answer (English):** An attention backend adapts the runtime's
logical attention operation and batch metadata to concrete prefill, decode, or
verification kernels and manages any backend-specific workspace or planning.
Performance can vary with GPU architecture, CUDA and library versions, model
attention type, data type, head dimensions, context distribution, batch
shape, KV-cache layout, and CUDA Graph support. Compatibility must be checked
first, then candidate backends should be benchmarked on the actual workload;
automatic selection is a useful default, not proof of universal optimality.

**正确答案（中文）：** Attention backend 把 runtime 的逻辑 attention 操作与
batch metadata 适配为具体的 prefill、decode 或 verification kernel，并管理
backend 专用 workspace 或规划过程。性能会随 GPU 架构、CUDA 与库版本、模型
attention 类型、data type、head dimension、上下文分布、batch shape、KV cache
布局和 CUDA Graph 支持而变化。应先检查兼容性，再用真实工作负载测试候选
backend；自动选择是有用的默认值，但不能证明其普遍最优。

### 7. Logical tokens and physical KV-cache pages / 逻辑 Token 与物理 KV Cache Page

**Question (English):** A request logically owns a sequence of tokens, but its
KV states may occupy non-contiguous physical pages. What metadata lets an
attention kernel find those states, and what changes when an exact prefix is
reused?

**问题（中文）：** 一个请求在逻辑上拥有一段连续 token 序列，但对应 KV state
可能位于不连续的物理 page。Attention kernel 依靠什么 metadata 找到这些状态？
复用完全一致的前缀时又会发生什么变化？

**Explanation (English):** Paged allocation separates logical sequence order
from physical storage. This reduces the need for one large contiguous
allocation per request, but the execution path must construct and consume a
correct logical-to-physical mapping.

**解说（中文）：** 分页分配把逻辑序列顺序与物理存储位置分离，减少了为每个请求
申请大块连续空间的需求，但执行路径必须正确构造并使用逻辑到物理的映射。

**Correct Answer (English):** Runtime metadata such as request-to-token
mappings, page indices, offsets, and sequence lengths tells the attention
backend which physical KV pages correspond to each logical position. When an
exact cached prefix is reused, the new request can reference the existing
prefix pages and allocate or compute KV states only for its unmatched suffix.
Those shared pages cannot be reclaimed while an active request still depends
on them; inactive cached pages become eviction candidates under memory
pressure.

**正确答案（中文）：** Request-to-token 映射、page index、offset 与 sequence
length 等 runtime metadata 会告诉 attention backend：每个逻辑位置对应哪些物理
KV page。复用完全一致的缓存前缀时，新请求可以引用已有前缀 page，只为未匹配
suffix 分配或计算 KV state。只要仍有活跃请求依赖，共享 page 就不能回收；在显存
压力下，不活跃的缓存 page 才会成为淘汰候选。

### 8. Overlapping CPU scheduling with GPU work / CPU 调度与 GPU 工作重叠

**Question (English):** Suppose the GPU executes batch N while the CPU prepares
batch N+1. What latency can this overlap hide, what dependency must still be
respected, and how would you test whether overlap helps?

**问题（中文）：** 假设 GPU 正在执行 batch N，而 CPU 同时准备 batch N+1。这种
重叠可以隐藏什么延迟？仍必须遵守哪项依赖？应如何测试 overlap 是否有帮助？

**Explanation (English):** Pipelining helps when independent CPU preparation
would otherwise leave a visible gap before the next GPU batch. It does not
remove true data dependencies, and incorrect buffer reuse can create
read-after-write or write-after-read hazards.

**解说（中文）：** 当独立的 CPU 准备工作会在下一批 GPU 工作前留下明显空隙时，
pipeline 可以隐藏这段时间。它不能消除真实数据依赖，而且错误复用 buffer 可能
产生 read-after-write 或 write-after-read hazard。

**Correct Answer (English):** Overlap can hide scheduler decisions, batch
metadata construction, and some host dispatch behind the current GPU forward.
Batch N+1 must not consume results that batch N has not produced, and the CPU
must not overwrite buffers the GPU is still reading; streams, events, or
equivalent barriers enforce those dependencies. Compare otherwise identical
runs with overlap enabled and disabled, then inspect CPU gaps, GPU idle gaps,
TPOT, throughput, and correctness. It helps most when CPU preparation is on
the critical path and there is enough independent work to overlap.

**正确答案（中文）：** Overlap 可以把 scheduler 决策、batch metadata 构建与
部分 host dispatch 隐藏在当前 GPU forward 背后。Batch N+1 不能消费 batch N
尚未产生的结果，CPU 也不能覆写 GPU 仍在读取的 buffer；这些依赖需要由 stream、
event 或等价 barrier 保证。应在其他条件相同的情况下对比开启与关闭 overlap，
同时检查 CPU gap、GPU idle gap、TPOT、吞吐量与正确性。当 CPU 准备位于关键路径
且存在足够独立工作可供重叠时，收益最大。

### 9. Reading a CPU–GPU timeline / 阅读 CPU–GPU 时间线

**Question (English):** A timeline repeatedly shows 3 ms of CPU activity,
followed by a 2 ms GPU idle gap, followed by 6 ms of dense GPU kernels. Which
layer is the first bottleneck candidate? What evidence would change the
hypothesis toward a slow GPU kernel instead?

**问题（中文）：** 一条时间线反复出现 3 ms CPU 活动、随后 2 ms GPU idle gap、
再随后 6 ms 密集 GPU kernel。首先应怀疑哪一层？什么证据会让假设转向 GPU kernel
本身过慢？

**Explanation (English):** A timeline provides causal ordering that utilization
averages hide. A GPU gap preceded by unfinished host work suggests starvation
or synchronization; a continuously busy GPU with one dominant kernel suggests
a device-side limit.

**解说（中文）：** 时间线能提供平均利用率所隐藏的因果顺序。若 GPU gap 前仍有
未完成的 host 工作，通常提示供给不足或同步等待；若 GPU 持续繁忙且某个 kernel
占据主要时间，则更像 device 侧限制。

**Correct Answer (English):** First investigate the CPU-to-GPU handoff:
scheduler or metadata preparation, tokenization or sampling, launch overhead,
blocking synchronization, and overlap effectiveness. Correlate named CPU
ranges with CUDA launches and determine why no ready GPU work exists during
the 2 ms gap. Shift the hypothesis toward a GPU-kernel bottleneck if the idle
gap disappears, GPU occupancy remains high, and a particular attention, GEMM,
communication, or memory kernel dominates iteration time and scales poorly
with its workload. Kernel-level analysis should then inspect achieved
throughput, memory traffic, occupancy, and launch shape.

**正确答案（中文）：** 首先调查 CPU 到 GPU 的交接路径：scheduler 或 metadata
准备、tokenization 或 sampling、launch overhead、阻塞同步与 overlap 效果。把有
名称的 CPU range 与 CUDA launch 对齐，查清 2 ms gap 期间为什么没有可执行的 GPU
工作。如果 idle gap 消失、GPU occupancy 仍然很高，而且某个 attention、GEMM、
通信或 memory kernel 占据大部分 iteration 时间并随工作量扩展不佳，才应把假设
转向 GPU kernel 瓶颈。随后用 kernel 级分析检查实际吞吐、memory traffic、
occupancy 与 launch shape。

### 10. Building a layered bottleneck experiment / 构建分层瓶颈实验

**Question (English):** Under high concurrency, TTFT rises sharply, TPOT rises
slightly, the waiting queue grows, GPU utilization stays above 95%, and no
large CPU-to-GPU gaps appear. What is the leading hypothesis, and which
controlled measurements distinguish queueing or admission pressure from a
decode-kernel regression?

**问题（中文）：** 在高并发下，TTFT 大幅升高、TPOT 仅小幅升高、等待队列持续
增长、GPU 利用率保持在 95% 以上，而且没有明显 CPU 到 GPU gap。最优先的假设
是什么？哪些受控测量可以区分排队或准入压力与 decode kernel 退化？

**Explanation (English):** Diagnosis should begin with the complete symptom
pattern, map it to one or more layers, and then change one workload dimension
at a time. A large TTFT change with nearly stable TPOT often points before the
steady-state decode path.

**解说（中文）：** 诊断应从完整的指标模式出发，把现象映射到一个或多个执行层，
再一次只改变一个工作负载维度。TTFT 大幅变化而 TPOT 基本稳定，通常说明问题位于
稳态 decode 路径之前。

**Correct Answer (English):** The leading hypothesis is capacity saturation:
requests spend longer waiting for admission or prefill because the busy GPU
cannot serve incoming work at the offered rate. Hold model, token-length
distribution, cache state, and generation settings constant; sweep request
rate or concurrency around the saturation knee while separately recording
queue time, prefill time, TPOT or inter-token latency, throughput, batch sizes,
token usage, and GPU time per decode iteration. If queue time and TTFT collapse
when load is reduced while per-iteration decode time and TPOT remain stable,
the evidence supports queueing. If decode iteration time or TPOT regresses at
the same batch shape even without a queue, compare attention backends, graph
coverage, kernel traces, and software versions to investigate a decode-path
regression.

**正确答案（中文）：** 最优先的假设是容量饱和：GPU 已经繁忙，无法以当前到达
速率处理新工作，因此请求在准入或 prefill 前等待更久。固定模型、token 长度
分布、cache 状态与生成设置，在饱和拐点附近扫描 request rate 或 concurrency，
并分别记录 queue time、prefill time、TPOT 或 inter-token latency、吞吐量、
batch size、token usage 与每次 decode iteration 的 GPU 时间。如果降低负载后
queue time 和 TTFT 快速回落，而逐 iteration decode 时间与 TPOT 保持稳定，则支持
排队假设。如果即使没有队列，相同 batch shape 下的 decode iteration 时间或 TPOT
仍然退化，再通过对比 attention backend、graph 覆盖率、kernel trace 与软件版本
调查 decode 路径回归。

## Summary / 总结

- **English:** A request crosses request-processing, scheduling,
  model-execution, GPU-kernel, sampling, and output-delivery boundaries.
  **中文：** 一个请求会跨越请求处理、调度、模型执行、GPU kernel、采样与输出
  传输等边界。
- **English:** The scheduler chooses and describes work; the model runner and
  operator backends execute the selected tensor computation.
  **中文：** Scheduler 选择并描述工作；model runner 与算子 backend 执行已经
  选中的 tensor 计算。
- **English:** Prefill or extend and decode have different token shapes,
  cache-access patterns, and performance limits.
  **中文：** Prefill 或 extend 与 decode 具有不同的 token shape、cache 访问
  模式与性能上限。
- **English:** Host launch time, GPU execution time, and synchronized latency
  are different measurement boundaries.
  **中文：** Host launch 时间、GPU 执行时间与同步后的延迟属于不同测量边界。
- **English:** CUDA Graph and CPU–GPU overlap primarily reduce orchestration
  gaps; they do not automatically accelerate every GPU kernel.
  **中文：** CUDA Graph 与 CPU–GPU overlap 主要减少编排空隙，并不会自动加速
  每一个 GPU kernel。
- **English:** Attention backends translate runtime metadata into
  phase-specific kernel execution, and their suitability depends on the full
  deployment configuration.
  **中文：** Attention backend 把 runtime metadata 转化为不同阶段的 kernel
  执行，其适用性取决于完整部署配置。
- **English:** A trustworthy diagnosis combines API metrics, queue and batch
  state, CPU–GPU timelines, and kernel evidence in a controlled experiment.
  **中文：** 可信的诊断会在受控实验中结合 API 指标、队列与 batch 状态、
  CPU–GPU 时间线及 kernel 证据。

## Common Mistakes / 常见错误

- **English:** Saying that the scheduler performs the transformer math instead
  of distinguishing orchestration from model execution.
  **中文：** 把 scheduler 说成执行 transformer 数值计算，而没有区分编排与模型
  执行。
- **English:** Comparing prefill and decode using request count alone while
  ignoring new-token count and sequence lengths.
  **中文：** 只用请求数比较 prefill 与 decode，却忽略新 token 数和序列长度。
- **English:** Treating an asynchronous host timer as GPU-kernel duration.
  **中文：** 把异步 host timer 的结果当作 GPU kernel 时长。
- **English:** Assuming CUDA Graph makes kernels faster rather than measuring
  launch savings, padding, coverage, and fallbacks.
  **中文：** 误以为 CUDA Graph 会让 kernel 本身变快，而不测量 launch 节省、
  padding、覆盖率与 fallback。
- **English:** Choosing an attention backend from a generic ranking without
  checking hardware, model, data type, phase, and workload compatibility.
  **中文：** 根据通用排名选择 attention backend，却不检查硬件、模型、data
  type、执行阶段与工作负载兼容性。
- **English:** Treating logical token order as one contiguous physical
  KV-cache allocation.
  **中文：** 误以为逻辑 token 顺序必然对应一块连续物理 KV cache。
- **English:** Reading average GPU utilization without examining idle gaps,
  queue growth, batch composition, and the critical path.
  **中文：** 只看平均 GPU 利用率，而不检查 idle gap、队列增长、batch 组成与
  关键路径。
- **English:** Changing concurrency, cache state, backend, and graph settings
  in one experiment, making the result impossible to attribute.
  **中文：** 在一次实验中同时改变 concurrency、cache 状态、backend 与 graph
  设置，导致结果无法归因。

## Next Steps / 下一步建议

1. **English:** Start one reproducible SGLang configuration and annotate a
   single request from arrival through prefill, first-token delivery, several
   decode iterations, and completion.
   **中文：** 启动一套可复现的 SGLang 配置，标注单个请求从到达、prefill、
   首 token 返回、若干次 decode iteration 到完成的全过程。
2. **English:** Capture a CPU–GPU timeline with named ranges for request
   processing, scheduler preparation, model forward, sampling, and output
   handling.
   **中文：** 捕获一条 CPU–GPU 时间线，并为请求处理、scheduler 准备、model
   forward、sampling 与输出处理添加命名 range。
3. **English:** Compare graph-enabled and eager decode while recording replay
   coverage, padded batch sizes, fallback count, TPOT, and throughput.
   **中文：** 对比启用 graph 与 eager decode，并记录 replay 覆盖率、padding 后
   batch size、fallback 次数、TPOT 与吞吐量。
4. **English:** Compare compatible attention backends on one fixed prefill-
   heavy workload and one fixed decode-heavy workload.
   **中文：** 在一个固定 prefill-heavy 工作负载和一个固定 decode-heavy 工作
   负载上，对比兼容的 attention backend。
5. **English:** Select one dominant GPU kernel from the timeline and use
   kernel-level profiling to connect its shape, memory behavior, and achieved
   throughput back to the serving metric it affects.
   **中文：** 从时间线选择一个占主导的 GPU kernel，使用 kernel 级 profiling
   把它的 shape、内存行为与实际吞吐关联回受其影响的 serving 指标。
