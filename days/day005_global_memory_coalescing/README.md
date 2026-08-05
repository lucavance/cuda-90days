# Day 005: Global Memory and Coalescing / 全局内存与合并访问

Date / 日期: 2026-06-10

## Topic / 主题

**English:** CUDA global memory, contiguous and strided access, memory
coalescing, memory transactions, effective bandwidth, and bandwidth-bound
kernels.

**中文：** CUDA global memory、连续与跨步访问、memory coalescing、memory
transaction、有效带宽以及 memory bandwidth-bound kernel。

## Goal / 目标

**English:** Build the intuition that GPUs prefer neighboring threads to
access global memory in regular, contiguous patterns, without memorizing
low-level hardware details yet.

**中文：** 暂不背诵底层硬件细节，先建立 GPU 喜欢相邻 thread 以规则、连续方式
访问 global memory 的基础直觉。

## 10 Concept Questions / 10 个概念问题

### 1. What is global memory? / 什么是 global memory

**Question (English):** In CUDA, what does `global memory` normally mean?
Explain its CPU/GPU location, relation to VRAM, kernel accessibility, and
whether an ordinary host pointer can address it.

**问题（中文）：** 在 CUDA 中，`global memory` 通常指什么？请从 CPU/GPU
位置、是否属于显存、kernel thread 能否访问，以及 Host 普通指针能否直接使用
几个角度解释。

**Explanation (English):** Host memory and device global memory are distinct
address spaces. Their placement and access rules are prerequisites for
reasoning about performance.

**解说（中文）：** Host memory 与 Device global memory 是不同的内存空间。
理解它们的位置和访问权限，是后续理解性能的前提。

**Correct Answer (English):** Global memory normally means device-wide GPU
memory, usually backed by VRAM. Kernel threads can access it. An ordinary host
pointer is not a global-memory pointer; a device pointer such as `d_a`
returned by `cudaMalloc` refers to device global memory.

**正确答案（中文）：** global memory 通常指 GPU Device 侧的全局内存，一般是
显存的一部分。kernel thread 可以访问它。Host 普通指针不能直接作为 global
memory 指针；`cudaMalloc` 返回的 `d_a` 这类 Device pointer 才指向 Device
global memory。

### 2. Why copy data to global memory? / 为什么把数据拷到 global memory

**Question (English):** Why is this allocation-and-copy sequence common?

**问题（中文）：** 为什么 CUDA 程序经常执行下面的分配与拷贝？

~~~cpp
cudaMalloc(&d_a, size);
cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
~~~

**Explanation (English):** Input prepared by the CPU normally resides in host
memory, while GPU threads need data in device global memory.

**解说（中文）：** CPU 准备的数据通常位于 Host memory，而 GPU kernel thread
需要访问 Device global memory。

**Correct Answer (English):** `cudaMalloc` allocates space for `d_a` in
device global memory. `cudaMemcpyHostToDevice` copies `h_a` from host memory
into that allocation, after which kernel threads can read or write it.

**正确答案（中文）：** `cudaMalloc(&d_a, size)` 在 Device global memory 中为
`d_a` 分配空间；`cudaMemcpyHostToDevice` 把 Host memory 中的 `h_a` 拷贝到
`d_a`，随后 kernel thread 才能读写对应显存数据。

### 3. Why is global memory slow? / Global memory 为什么慢

**Question (English):** Relative to which GPU storage locations is global
memory considered slow?

**问题（中文）：** 为什么说 global memory 访问通常比较慢？这里的“慢”主要是
相对于哪些存储位置？

**Explanation (English):** GPU storage is hierarchical. Global memory has
large capacity but relatively high access latency.

**解说（中文）：** GPU 内部有不同层级的存储。global memory 容量大，但访问
延迟相对高。

**Correct Answer (English):** Global memory is much slower than registers and
shared memory. Registers are fastest and thread-private; shared memory is fast
and block-shared; global memory is large and device-wide but has higher
latency.

**正确答案（中文）：** global memory 通常比 register 和 shared memory 慢。
直觉上 register 最快且 thread 私有；shared memory 很快且 block 内共享；global
memory 容量大、所有 thread 可访问，但延迟高。

### 4. Contiguous access in vector add / Vector add 中的连续访问

**Question (English):** What address pattern do neighboring threads normally
produce in this vector-add kernel?

**问题（中文）：** 在下面的 vector add 中，相邻 thread 通常访问怎样的地址？

~~~cpp
int idx = blockIdx.x * blockDim.x + threadIdx.x;
c[idx] = a[idx] + b[idx];
~~~

**Explanation (English):** The one-dimensional global index grows
consecutively with neighboring threads.

**解说（中文）：** 一维 vector add 中，全局索引 `idx` 通常随 thread 连续增长。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
thread 0 -> a[0]
thread 1 -> a[1]
thread 2 -> a[2]
thread 3 -> a[3]
~~~

**English:** Neighboring threads access neighboring addresses, which is
favorable for coalescing.

**中文：** 相邻 thread 访问相邻内存地址，这种模式更容易产生 coalescing。

### 5. Memory coalescing / 内存合并访问

**Question (English):** What is a useful high-level definition of memory
coalescing, and why are adjacent addresses efficient?

**问题（中文）：** 如何粗略理解 memory coalescing？为什么相邻 thread 访问
相邻 global memory 地址通常更高效？

**Explanation (English):** Global memory is serviced through memory
transactions. Regular neighboring accesses are easier for hardware to combine.

**解说（中文）：** GPU 通过 memory transaction 访问 global memory。一组
thread 的访问整齐连续时，硬件更容易合并请求。

**Correct Answer (English):** Coalescing combines a group of neighboring
threads' accesses to contiguous global-memory addresses into fewer memory
transactions, improving effective bandwidth and reducing waiting.

**正确答案（中文）：** memory coalescing 是把同一组相邻 thread 对连续 global
memory 地址的访问合并成更少的 memory transaction，从而提高有效带宽并减少
等待。

### 6. Contiguous versus strided access / 连续访问与跨步访问

**Question (English):** Which pattern is more coalescing-friendly?

**问题（中文）：** 下面哪种访问模式更有利于 coalescing？

~~~cpp
// A
int idx = blockIdx.x * blockDim.x + threadIdx.x;
x = a[idx];

// B
int idx = blockIdx.x * blockDim.x + threadIdx.x;
x = a[idx * 16];
~~~

**Explanation (English):** The key question is whether neighboring threads
access neighboring addresses.

**解说（中文）：** 是否有利于 coalescing，关键看相邻 thread 是否访问相邻地址。

**Correct Answer (English):** A. Its threads access `a[0]`, `a[1]`,
`a[2]`, and so on. B accesses `a[0]`, `a[16]`, `a[32]`, and so on, making
it harder to combine requests into a small number of transactions.

**正确答案（中文）：** A 更有利。A 中相邻 thread 访问连续地址；B 中相邻 thread
访问 `a[0]`、`a[16]`、`a[32]` 等跨步地址，硬件更难用少量 memory
transaction 合并访问。

### 7. Why strided access is slower / 为什么 stride access 更慢

**Question (English):** Why can `a[idx * 16]` reduce global-memory
performance?

**问题（中文）：** 为什么 `a[idx * 16]` 这种 stride access 可能让 global
memory 访问变慢？

**Explanation (English):** Strided access places a fixed gap between
neighboring accesses instead of keeping them contiguous.

**解说（中文）：** stride access 是跨步访问，相邻访问之间有固定间隔，而不是
连续地址。

**Correct Answer (English):** Neighboring threads touch far-apart addresses,
which may require more memory transactions with less useful data in each.
Effective global-memory bandwidth therefore falls.

**正确答案（中文）：** 相邻 thread 访问不相邻地址，硬件可能需要更多 memory
transaction，且每次事务的有效数据利用率更低，因此 global memory bandwidth
利用率下降。

### 8. Why vector add is bandwidth-bound / Vector add 为何受内存带宽限制

**Question (English):** Why is this kernel normally memory bandwidth-bound?

**问题（中文）：** 为什么下面的 vector add 通常是 memory bandwidth-bound
kernel？

~~~cpp
c[idx] = a[idx] + b[idx];
~~~

**Explanation (English):** A bottleneck depends on the ratio of computation
to data movement.

**解说（中文）：** 判断 kernel 瓶颈要看它主要花时间计算，还是读写内存。

**Correct Answer (English):** Each element needs only one addition but two
global reads and one global write. Data movement dominates the small amount of
arithmetic, so performance is usually limited by global-memory bandwidth.

**正确答案（中文）：** 每个元素只有一次加法，却需要读 `a[idx]`、读
`b[idx]`、写 `c[idx]`。内存读写相对更突出，所以性能通常受 global memory
bandwidth 限制。

### 9. Optimization priority for bandwidth-bound kernels / 带宽受限 kernel 的优化重点

**Question (English):** Which direction should be prioritized?

**问题（中文）：** 如果 kernel 受 memory bandwidth 限制，应优先选择哪类优化？

~~~text
A. 减少不必要的 global memory 访问，提高 memory coalescing
B. 增加更多复杂数学计算，让 GPU 更忙
~~~

**Explanation (English):** Optimization should target the current bottleneck;
simple vector add is normally not compute-bound.

**解说（中文）：** 瓶颈在哪里，优化重点就应放在哪里；简单 vector add 的瓶颈
通常不是算力。

**Correct Answer (English):** A. Reduce unnecessary reads and writes, keep
accesses contiguous and coalesced, improve effective bandwidth, and avoid
repeated movement.

**正确答案（中文）：** 选 A。减少不必要的 global memory 访问，让访问更连续、
更 coalesced，提高有效带宽并避免重复读写。

### 10. Core intuition / 核心直觉

**Question (English):** In one sentence, why do GPUs prefer neighboring
threads to access neighboring global-memory addresses?

**问题（中文）：** 用一句话总结：为什么 GPU 喜欢相邻 thread 访问相邻 global
memory 地址？

**Explanation (English):** The benefit is not less allocation or necessarily
less memory capacity; it is easier combination of access requests.

**解说（中文）：** 关键不是减少 global memory 容量或 `cudaMalloc` 次数，而是
让访问请求更容易被合并。

**Correct Answer (English):** The pattern coalesces into fewer memory
transactions and therefore uses global-memory bandwidth more effectively.

**正确答案（中文）：** 这种模式更容易 coalescing，能减少 memory transaction
数量，提高 global memory bandwidth 利用率。

## Summary / 今日总结

- **English:** Global memory is large device-wide GPU memory, while registers
  and shared memory are faster and smaller.
  **中文：** global memory 是容量较大的 Device 全局内存；register 与 shared
  memory 更快但更小。
- **English:** Neighboring vector-add threads naturally access neighboring
  elements.
  **中文：** vector add 中相邻 thread 天然访问相邻元素。
- **English:** Coalescing reduces memory transactions and improves effective
  bandwidth.
  **中文：** coalescing 减少 memory transaction 并提高有效带宽。
- **English:** Strided access weakens coalescing.
  **中文：** stride access 会削弱 coalescing。
- **English:** Vector add is usually bandwidth-bound, so memory traffic is the
  primary optimization target.
  **中文：** vector add 通常受带宽限制，因此内存流量是主要优化目标。

## Common Mistakes / 易错点

- **English:** Locating device global memory on the CPU side.
  **中文：** 误以为 Device global memory 位于 CPU 侧。
- **English:** Treating an ordinary host pointer as a device pointer.
  **中文：** 把普通 Host pointer 当作 Device pointer。
- **English:** Calling strided access contiguous.
  **中文：** 把跨步访问当作连续访问。
- **English:** Believing coalescing reduces allocation count rather than
  memory transactions.
  **中文：** 误以为 coalescing 减少 `cudaMalloc` 次数，而不是 memory
  transaction。

## Next Steps / 下一步

- **English:** Benchmark contiguous access against multiple strides.
  **中文：** 对比连续访问与不同 stride 的 kernel time。
- **English:** Learn shared-memory fundamentals and inspect global load/store
  metrics with Nsight Compute.
  **中文：** 学习 shared memory 基础，并用 Nsight Compute 观察 global
  load/store 指标。
