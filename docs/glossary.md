# Glossary / 术语表

**English:** This document collects stable concepts from the study of CUDA,
GPUs, LLM inference, and AI infrastructure. Daily learning records belong in
`days/`; this glossary contains definitions worth revisiting.

**中文：** 本文件用于沉淀 CUDA、GPU、LLM inference 和 AI Infra 学习中的稳定
概念。每日学习记录放在 `days/`，这里保存后续会反复查阅的术语解释。

## CUDA and GPU / CUDA 与 GPU

### Kernel

**English:** A CUDA kernel is a function entry point that runs on the GPU and
is executed in parallel by many threads. The CPU launches it with kernel-launch
syntax such as:

**中文：** CUDA kernel 是运行在 GPU 上、由大量 thread 并行执行的函数入口。
CPU 端通过 kernel launch 启动它，例如：

```cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
```

**English:** A kernel is not an ordinary synchronous CPU function call. By
default, the CPU normally continues after submitting the kernel.

**中文：** kernel 不是普通的 CPU 同步函数调用。默认情况下，CPU 提交 kernel
后通常会继续执行后续代码。

### Kernel Launch / Kernel 启动

**English:** A kernel launch is the CPU submitting and starting a kernel task
on the GPU. It resembles:

**中文：** kernel launch 指 CPU 向 GPU 提交并启动一个 kernel 任务。它更像：

```text
CPU submits an asynchronous task to the GPU.
CPU 向 GPU 提交异步任务。
```

**English:** It does not mean that the CPU enters the function and waits for it
to finish.

**中文：** 它并不表示 CPU 自己进入函数并等待执行完成。

### Thread, Block, and Grid / Thread、Block 与 Grid

**English:** CUDA uses this parallel hierarchy:

**中文：** CUDA 使用以下并行层级：

```text
grid -> block -> thread
```

- Thread: one parallel instance executing kernel code / 执行 kernel 代码的一份并行实例
- Block: a group of threads / 一组 thread
- Grid: all blocks created by one kernel launch / 一次 kernel launch 启动的全部 block

### Global Thread Index / 全局线程索引

**English:** A one-dimensional kernel commonly calculates its global index as
follows:

**中文：** 一维 kernel 通常使用以下方式计算全局索引：

```cpp
int idx = blockIdx.x * blockDim.x + threadIdx.x;
```

- `blockIdx.x`: Current block index in the x dimension / 当前 block 在 x 维度上的索引
- `blockDim.x`: Threads per block in the x dimension / 每个 block 在 x 维度上的 thread 数量
- `threadIdx.x`: Current thread index inside its block / 当前 thread 在 block 内 x 维度上的索引
- `idx`: Common one-dimensional global thread index / 一维场景下常用的全局 thread 索引

### Boundary Check / 边界检查

**English:** CUDA kernels commonly guard memory access like this:

**中文：** CUDA kernel 通常使用如下条件保护内存访问：

```cpp
if (idx < n) {
    c[idx] = a[idx] + b[idx];
}
```

**English:** This prevents extra threads from accessing memory out of bounds.
Because the block count is normally rounded up, the total thread count may be
larger than the actual data length.

**中文：** 这样可以避免多出来的 thread 访问越界内存。因为 block 数通常向上
取整，所以总 thread 数可能大于真实数据长度。

### Host and Device / Host 与 Device

- Host: the CPU side, which prepares data, allocates GPU memory, and launches kernels / CPU 端，负责准备数据、分配 GPU 内存并启动 kernel
- Device: the GPU side, which executes kernels / GPU 端，负责执行 kernel
- Host memory: memory used by the CPU / CPU 使用的内存
- Device memory: memory used by the GPU / GPU 使用的显存

### Global Memory / 全局内存

**English:** In CUDA, global memory usually means global memory on the GPU
device, normally backed by VRAM. A pointer such as `d_a`, allocated below,
points to device global memory:

**中文：** 在 CUDA 中，global memory 通常指 GPU device 侧的全局内存，一般由
显存承载。下面分配的 `d_a` 指向 device global memory：

```cpp
cudaMalloc(&d_a, size);
```

**English:** Kernel threads can access global memory, but an ordinary host
pointer cannot be used directly as a device-global-memory pointer.

**中文：** kernel thread 可以访问 global memory，但不能把普通 host 指针直接
当作 device global memory 指针使用。

### `cudaMalloc`

**English:** `cudaMalloc` allocates space in device/global memory:

**中文：** `cudaMalloc` 用于在 device/global memory 中分配空间：

```cpp
float* d_a = nullptr;
cudaMalloc(&d_a, size);
```

**English:** A common naming convention is:

**中文：** 常见命名习惯是：

```text
h_a = a on the host / host 上的 a
d_a = a on the device / device 上的 a
```

### `cudaMemcpy`

**English:** `cudaMemcpy` copies data between host memory and device memory.
Host to device:

**中文：** `cudaMemcpy` 用于在 host memory 和 device memory 之间复制数据。
Host 到 device：

```cpp
cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
```

**English:** Device to host:

**中文：** Device 到 host：

```cpp
cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);
```

**English:** `size` normally means a number of bytes, not a number of elements.

**中文：** `size` 通常是字节数，而不是元素个数。

### `cudaDeviceSynchronize`

**English:** `cudaDeviceSynchronize()` makes the CPU wait for previously
submitted work on the current device to finish. It is useful during debugging
because kernel runtime errors often surface here. It does not copy results from
device memory back to host memory.

**中文：** `cudaDeviceSynchronize()` 会让 CPU 等待当前 device 上此前提交的任务
完成。它常用于调试，因为 kernel 运行时错误经常会在这里暴露。它不会自动把
device memory 中的结果复制回 host memory。

### `cudaGetLastError`

**English:** `cudaGetLastError()` checks the latest error recorded by the CUDA
Runtime and is commonly called immediately after a kernel launch to detect
launch errors. A typical debugging pattern is:

**中文：** `cudaGetLastError()` 用于检查 CUDA Runtime 记录的最近一次错误，通常
在 kernel launch 后立即调用，以检测启动错误。典型调试模板是：

```cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);

CUDA_CHECK(cudaGetLastError());       // Launch error / 启动错误
CUDA_CHECK(cudaDeviceSynchronize());  // Runtime error; debug only / 运行时错误；仅调试
```

### `cudaGetErrorString`

**English:** `cudaGetErrorString(err)` converts a `cudaError_t` value into a
readable message, for example:

**中文：** `cudaGetErrorString(err)` 会把 `cudaError_t` 值转换成可读消息，例如：

```text
out of memory
invalid argument
invalid device pointer
```

### `cudaError_t` and `cudaSuccess` / `cudaError_t` 与 `cudaSuccess`

**English:** `cudaError_t` is the error type returned by the CUDA Runtime API.

**中文：** `cudaError_t` 是 CUDA Runtime API 返回的错误类型。

```text
cudaSuccess        -> success / 成功
err == cudaSuccess -> no error / 没有错误
err != cudaSuccess -> an error occurred / 发生错误
```

### `CUDA_CHECK`

**English:** `CUDA_CHECK` is a common host-side C/C++ macro that packages
repeated CUDA API error-checking logic. For example:

**中文：** `CUDA_CHECK` 是常见的 host 端 C/C++ 宏，用于封装重复的 CUDA API
错误检查逻辑。例如：

```cpp
#define CUDA_CHECK(call)                                      \
    do {                                                      \
        cudaError_t err = (call);                             \
        if (err != cudaSuccess) {                             \
            fprintf(stderr, "CUDA error at %s:%d: %s\n",      \
                    __FILE__, __LINE__,                       \
                    cudaGetErrorString(err));                 \
            exit(1);                                          \
        }                                                     \
    } while (0)
```

**English:** `do { ... } while (0)` makes a multi-line macro behave
syntactically like one ordinary statement.

**中文：** `do { ... } while (0)` 让多行宏在语法上表现得像一条普通语句。

### CUDA Event Timing / CUDA Event 计时

**English:** CUDA events can measure GPU kernel time. The basic sequence is:

**中文：** CUDA event 可以用于测量 GPU kernel 时间。基本顺序是：

```text
cudaEventCreate(start / stop)
cudaEventRecord(start)
kernel launch
cudaEventRecord(stop)
cudaEventSynchronize(stop)
cudaEventElapsedTime(...)
```

**English:** For the ordering exercise used in the learning record, this is:

**中文：** 对应学习记录中的顺序题，答案是：

```text
B -> E -> D -> A -> F -> C
```

### Register / 寄存器

**English:** Registers are among the fastest storage resources on a GPU and
are normally private to one thread. They are very fast but limited in capacity.

**中文：** register 是 GPU 中最快的存储资源之一，通常由单个 thread 私有使用。
它访问速度很快，但容量有限。

### Shared Memory / 共享内存

**English:** Shared memory is fast temporary GPU memory shared by the threads
in one block. It is usually much faster than global memory but has limited
capacity.

**中文：** shared memory 是 GPU 上由一个 block 内的 thread 共享的高速临时
内存。它通常比 global memory 快很多，但容量有限。

```text
Fast / 快
Small / 小
Short-lived / 生命周期短
Block scope / 作用范围是 block
```

**English:** It is useful for caching data reused by multiple threads in the
same block. It is not simply faster global memory; it is a high-speed workspace
for cooperation and data reuse within a block.

**中文：** 它适合缓存同一个 block 内多个 thread 会重复使用的数据。它并不是
“更快的 global memory”，而是 block 内 thread 协作与复用数据的高速工作区。

### `__shared__`

**English:** `__shared__` declares a shared-memory variable. For example:

**中文：** `__shared__` 用于声明 shared memory 变量。例如：

```cpp
__shared__ float tile[256];
```

**English:** This means that `tile` resides in the current block's shared
memory, is accessible to every thread in that block, and normally lives until
the block finishes.

**中文：** 这表示 `tile` 位于当前 block 的 shared memory 中，同一个 block 的
所有 thread 都可以访问它，其生命周期通常持续到该 block 执行结束。

### `__syncthreads`

**English:** `__syncthreads()` is a synchronization barrier for threads in one
block. Every thread in that block must reach the barrier before any of them can
continue.

**中文：** `__syncthreads()` 是 block 内 thread 的同步屏障。同一个 block 中的
所有 thread 都到达这里之后，才会继续向后执行。

```cpp
tile[threadIdx.x] = input[idx];

__syncthreads();

float x = tile[some_index];
```

**English:** Without synchronization, some threads might read shared memory
before others finish writing it, producing stale or uninitialized values.
`__syncthreads()` synchronizes only threads in the same block, not different
blocks.

**中文：** 如果没有同步，有些 thread 可能在其他 thread 完成 shared memory
写入之前就开始读取，从而读到旧值或未初始化值。`__syncthreads()` 只能同步同一
block 内的 thread，不能同步不同 block。

### SM / Streaming Multiprocessor

**English:** An SM is a Streaming Multiprocessor. It can initially be understood
as a cluster of compute resources that actually executes thread blocks inside
the GPU. A GPU normally contains multiple SMs:

**中文：** SM 是 Streaming Multiprocessor，中文常译为流式多处理器。可以先把
它理解为 GPU 中真正执行 thread block 的计算资源集群。一个 GPU 通常包含多个
SM：

```text
GPU
├── SM 0
├── SM 1
├── SM 2
└── ...
```

**English:** A block is scheduled onto an SM. Each SM contains execution
resources such as CUDA cores, registers, shared memory, and warp schedulers.
Because total shared memory per SM is limited, a block that consumes more
shared memory normally reduces the number of blocks that can reside on the SM
at the same time.

**中文：** block 会被调度到某个 SM 上执行。每个 SM 包含 CUDA core、register、
shared memory、warp scheduler 等执行资源。由于每个 SM 的 shared memory 总量
有限，如果一个 block 使用更多 shared memory，同一 SM 上能够同时驻留的 block
数量通常会减少。

### Occupancy / 占用率

**English:** Occupancy is roughly the ratio of active resident warps or blocks
on an SM to the corresponding hardware limit. Higher occupancy often gives the
GPU more opportunities to hide memory latency by running another warp.

**中文：** occupancy 可以粗略理解为一个 SM 上实际驻留的活跃 warp 或 block
相对于硬件上限的比例。较高的 occupancy 通常让 GPU 更有机会运行其他 warp，
从而隐藏 memory latency。

**English:** Higher occupancy does not guarantee higher performance. Shared
memory usage, register usage, and block size all affect occupancy. Optimization
must balance resource consumption against measured performance.

**中文：** occupancy 并不是越高就一定越快。shared memory 用量、register
用量和 block size 都会影响 occupancy；优化时需要在资源占用与实测性能之间
权衡。

### Memory Bandwidth / 内存带宽

**English:** Memory bandwidth is the amount of data memory can transfer per
unit of time. On a GPU, it is the upper limit on how quickly data can be read
from or written to global memory, commonly measured in GB/s or TB/s.

**中文：** memory bandwidth 表示单位时间内内存能够传输的数据量。在 GPU 中，
它可以理解为从 global memory 读取或向其中写入数据的速度上限，常见单位是
GB/s 或 TB/s。

```text
VRAM = warehouse / 显存 = 仓库
GPU cores = workers / GPU core = 工人
Memory bandwidth = transport capacity / memory bandwidth = 运输能力
```

**English:** A kernel that spends most of its time moving data rather than
performing arithmetic is usually memory-bandwidth-bound.

**中文：** 如果一个 kernel 的大部分时间用于搬运数据而不是计算，它通常受
memory bandwidth 限制。

### Memory-Bandwidth-Bound / 受内存带宽限制

**English:** A memory-bandwidth-bound kernel is limited primarily by memory
bandwidth rather than arithmetic throughput. Vector addition is a common
example:

**中文：** memory-bandwidth-bound 表示 kernel 性能主要受内存带宽限制，而不是
受计算能力限制。向量加法是常见例子：

```cpp
c[idx] = a[idx] + b[idx];
```

**English:** Each element requires only one addition but two reads and one
write, so global-memory bandwidth is normally the limiting resource.

**中文：** 每个元素只有一次加法，却需要读取 `a[idx]`、读取 `b[idx]` 并写入
`c[idx]`，因此瓶颈通常是 global memory bandwidth。

### Memory Transaction / 内存事务

**English:** A memory transaction is one transaction generated when the GPU
accesses global memory. With good coalescing, accesses from adjacent threads
can be combined into fewer transactions.

**中文：** memory transaction 可以理解为 GPU 访问 global memory 时产生的一次
内存事务。coalescing 良好时，相邻 thread 的访问可以合并成更少的 transaction。

### Memory Coalescing / 内存合并访问

**English:** Memory coalescing combines accesses from a group of adjacent
threads to consecutive global-memory addresses into fewer memory transactions.

**中文：** memory coalescing 指 GPU 将一组相邻 thread 对连续 global memory
地址的访问合并成更少的 memory transaction。

- Reduce the number of memory transactions / 减少 memory transaction 数量
- Improve global-memory-bandwidth utilization / 提高 global memory bandwidth 利用率
- Reduce time waiting for global memory / 减少等待 global memory 的时间

**English:** In short, GPUs prefer adjacent threads to access adjacent global
memory addresses.

**中文：** 简单来说，GPU 喜欢相邻 thread 访问相邻的 global memory 地址。

### Stride Access / 跨步访问

**English:** Stride access means consecutive accesses are separated by a fixed
distance instead of addressing consecutive elements. A contiguous access is:

**中文：** stride access 指相邻访问之间存在固定间隔，而不是访问连续元素。
连续访问示例：

```cpp
a[idx]
```

```text
Adjacent threads / 相邻 thread: a[0], a[1], a[2], a[3]
```

**English:** A strided access is:

**中文：** 跨步访问示例：

```cpp
a[idx * 16]
```

```text
Adjacent threads / 相邻 thread: a[0], a[16], a[32], a[48]
```

**English:** Strided access usually reduces the effectiveness of memory
coalescing.

**中文：** stride access 通常会降低 memory coalescing 的效果。

## LLM Inference and SGLang / LLM 推理与 SGLang

### LLM

**English:** LLM stands for Large Language Model. It primarily processes text
input and produces text output.

**中文：** LLM 是 Large Language Model，即大语言模型。它主要处理文本输入并
生成文本输出。

### VLM

**English:** VLM stands for Vision-Language Model. It can process images or
video together with text and produce text output.

**中文：** VLM 是 Vision-Language Model，即视觉语言模型。它可以处理图像或
视频与文本的组合输入，并输出文本。

### SGLang

**English:** SGLang is a high-performance inference and serving framework for
LLMs and VLMs. It receives and schedules requests, manages the KV cache,
organizes prefill and decode, exposes APIs, and improves throughput and latency.

**中文：** SGLang 是面向 LLM/VLM 的高性能推理与 serving 框架。它负责接收并
调度请求、管理 KV cache、组织 prefill 与 decode、提供 API 服务，并改善吞吐与
延迟表现。

**English:** SGLang is a high-level inference runtime and serving system;
CUDA kernels are its low-level compute units.

**中文：** SGLang 属于上层推理 runtime/serving 系统，CUDA kernel 则是底层
计算执行单元。

### Offline Inference / 离线推理

**English:** Offline inference processes a batch of prompts and collects the
results without serving interactive requests. It usually prioritizes aggregate
throughput.

**中文：** offline inference 会批量处理一组 prompt 并获取结果，不直接服务交互
请求，通常更关注总吞吐。

### Online Serving / 在线推理服务

**English:** Online serving deploys inference as an API that waits for user
requests. It emphasizes latency, concurrency, stability, and request
scheduling.

**中文：** online serving 通常把推理部署为等待用户请求的 API 服务，更关注延迟、
并发、稳定性和请求调度。

### Prefill / 预填充

**English:** The prefill phase processes all tokens in the input prompt and
builds the initial KV cache. It usually has a strong effect on TTFT.

**中文：** prefill 阶段处理输入 prompt 中的全部 token，并建立初始 KV cache。
它通常会显著影响 TTFT。

### Decode / 解码

**English:** The decode phase uses the existing KV cache to generate output one
token at a time. It usually has a strong effect on TPOT and streaming
smoothness.

**中文：** decode 阶段基于已有 KV cache，逐个 token 生成输出。它通常会显著
影响 TPOT 和流式输出的流畅度。

### Attention / 注意力

**English:** Attention can be understood intuitively as deciding which context
tokens matter most while processing the current token. More concretely, the
current token's Query is matched against historical Keys, and the corresponding
Values are combined using the resulting weights.

**中文：** attention 可以直观地理解为：模型处理当前 token 时，判断上下文中的
哪些 token 更值得关注。更工程化地说，当前 token 的 Query 与历史 token 的 Key
进行匹配，再按得到的权重汇总相应的 Value。

**English:** Attention is fundamentally a mechanism for routing and weighted
aggregation of information among tokens.

**中文：** attention 本质上是 token 之间的信息路由与加权聚合机制。

### Query, Key, and Value / Query、Key 与 Value

**English:** Within attention:

**中文：** 在 attention 中：

- Query: what information the current token is looking for / 当前 token 想寻找什么信息
- Key: the index or features exposed by a historical token / 历史 token 提供的索引或特征
- Value: the content representation carried by a historical token / 历史 token 携带的内容表示

**English:** The current Query is compared with historical Keys, and the
similarity scores weight the aggregation of Values.

**中文：** 当前 Query 与历史 Key 计算相似度，再使用相似度权重对 Value 进行加权
汇总。

### KV Cache / KV 缓存

**English:** The KV cache stores previously computed Key and Value
representations for historical tokens in Transformer attention. It is not a
mapping from the current token to the next token; it is closer to the model's
intermediate computational memory of the preceding context.

**中文：** KV cache 缓存 Transformer attention 中已经计算过的历史 token 的
Key/Value 表示。它不是“当前 token 到下一个 token 的映射”，而更像模型针对既有
上下文保存的中间计算记忆。

**English:** Decode relies heavily on the KV cache because a new token can
reuse historical K/V instead of recomputing every previous token.

**中文：** decode 阶段尤其依赖 KV cache，因为新 token 可以复用历史 K/V，而不必
重新计算全部历史 token。

### Scheduler / 调度器

**English:** An LLM-serving scheduler decides which requests run together and
when. It balances GPU memory, compute resources, request latency, system
throughput, and KV-cache management.

**中文：** LLM serving scheduler 决定哪些请求在什么时间一起运行，并在 GPU
显存、计算资源、请求延迟、系统吞吐和 KV cache 管理之间进行权衡。

### TTFT

**English:** TTFT means Time To First Token: the time from sending a request to
receiving its first output token. It is commonly affected by queueing, prefill
time, prompt length, scheduling policy, and model size.

**中文：** TTFT 是 Time To First Token，表示从发出请求到收到第一个输出 token
的时间。它通常受排队时间、prefill 时间、prompt 长度、调度策略和模型大小影响。

### TPOT

**English:** TPOT means Time Per Output Token: the average time required for
each output token during generation. It more directly reflects decode speed.

**中文：** TPOT 是 Time Per Output Token，表示生成阶段平均每个输出 token 所需
的时间。它更直接地反映 decode 阶段速度。

### Radix / 基数树

**English:** In RadixAttention, radix refers to a radix tree or prefix tree: a
data structure that organizes strings or token sequences by shared prefixes.

**中文：** 在 RadixAttention 语境中，radix 指 radix tree 或 prefix tree，即按
公共前缀组织字符串或 token 序列的数据结构。

```text
radix = prefix-sharing data structure / 前缀共享数据结构
```

### RadixAttention

**English:** RadixAttention is SGLang's mechanism for shared prefixes and
KV-cache reuse. It organizes prompt or token sequences by common prefixes so
that the corresponding KV cache can be reused.

**中文：** RadixAttention 是 SGLang 中围绕共享前缀与 KV cache 复用的机制。它
按照公共前缀组织 prompt 或 token 序列，从而复用相同前缀对应的 KV cache。

- Reduce repeated prefill work / 减少重复 prefill
- Lower TTFT / 降低 TTFT
- Improve throughput / 提升吞吐
- Save compute resources / 节省部分计算资源

### Prefix Cache / 前缀缓存

**English:** A prefix cache stores and reuses the computed results—especially
KV-cache entries—for identical prefixes. Common use cases include:

**中文：** prefix cache 用于缓存并复用相同前缀的计算结果，尤其是相应的 KV
cache。常见场景包括：

- Identical system prompts / 相同 system prompt
- Identical tool descriptions / 相同工具说明
- Identical document context / 相同文档上下文
- Identical few-shot examples / 相同 few-shot examples

**English:** In short: do not recompute context the model has already
processed.

**中文：** 简单来说：不要重复计算模型已经处理过的上下文。
