# Day 006: Shared Memory Basics / 共享内存基础

Date / 日期: 2026-06-11

## Topic / 主题

**English:** CUDA shared memory, block-local cooperation, data reuse,
`__shared__` storage, `__syncthreads()`, tiled transpose, and occupancy
trade-offs.

**中文：** CUDA shared memory、block 内协作、数据复用、`__shared__` 存储、
`__syncthreads()`、分块转置以及 occupancy 权衡。

## Goal / 目标

**English:** Understand how shared memory differs from global memory, when
block-local caching is valuable, and what synchronization and resource costs
it introduces.

**中文：** 理解 shared memory 与 global memory 的区别、block 内缓存何时有价值，
以及它带来的同步和资源成本。

## 10 Concept Questions / 10 个概念问题

### 1. What is shared memory? / 什么是 shared memory

**Question (English):** Explain shared memory in terms of CPU/GPU location,
speed, sharing scope, and suitability for long-term large storage.

**问题（中文）：** 请从 CPU/GPU 位置、速度、共享范围，以及是否适合长期保存
大量数据几个角度解释 shared memory。

**Explanation (English):** Shared memory is high-speed temporary GPU storage
used for cooperation among threads in one block.

**解说（中文）：** shared memory 是 GPU 内存层级中的高速临时存储，常用于一个
block 内的 thread 协作。

**Correct Answer (English):** It is GPU-side, normally much faster than global
memory, shared only among threads in one block, and too limited for large
long-lived storage. Think of it as a block's fast temporary workspace.

**正确答案（中文）：** shared memory 位于 GPU 侧，通常比 global memory 快，只
在一个 block 的 thread 间共享，不适合长期保存大量数据。可以把它记作 block 内
thread 共享的高速临时工作区。

### 2. Why is shared memory faster? / Shared memory 为什么更快

**Question (English):** Why is shared memory normally faster than global
memory?

**问题（中文）：** 为什么 shared memory 通常比 global memory 快？

**Explanation (English):** GPU storage closer to compute units is normally
smaller but has lower latency.

**解说（中文）：** GPU 内存层级中，离计算单元越近，容量通常越小，但访问延迟
更低。

**Correct Answer (English):** Shared memory is physically closer to the SM's
compute resources, with low latency and high bandwidth but small capacity.
Global memory is larger and farther away, with higher latency.

**正确答案（中文）：** shared memory 更靠近 SM 计算单元，延迟低、带宽高但容量
小；global memory 位于显存，容量大但距离更远、延迟更高。

### 3. Block scope / Shared memory 的 block 作用范围

**Question (English):** Why is shared memory block-local rather than
grid-wide, and why can different blocks not use it for direct communication?

**问题（中文）：** 为什么 shared memory 的作用范围是一个 block，而不是整个
grid？为什么不同 block 不能直接通过它通信？

**Explanation (English):** Every block receives an independent shared-memory
allocation. Blocks can run on different SMs and in an unspecified order.

**解说（中文）：** 每个 block 都有独立的 shared memory。block 可能在不同 SM
上执行，执行顺序也不保证。

**Correct Answer (English):** Blocks cannot access one another's shared
memory. Cross-block communication normally uses global memory, separate
kernel launches, atomics, or specialized cooperative-group mechanisms.

**正确答案（中文）：** shared memory 是 block-local 的，各 block 的存储彼此
独立。跨 block 通信通常需要 global memory、多个 kernel launch、atomic 或
cooperative groups 等机制。

### 4. Declaring a shared tile / 声明 shared tile

**Question (English):** Explain `__shared__`, `tile`, `256`, accessibility,
and lifetime in this declaration:

**问题（中文）：** 解释下面声明中的 `__shared__`、`tile`、`256`、访问范围和
生命周期：

~~~cpp
__shared__ float tile[256];
~~~

**Explanation (English):** `__shared__` declares storage in the block's
shared-memory allocation.

**解说（中文）：** `__shared__` 是 CUDA 中声明 shared memory 变量的关键字。

**Correct Answer (English):** `tile` is an array of 256 floats in shared
memory. Every thread in the current block can access it. It exists while that
block executes and is not preserved afterward.

**正确答案（中文）：** `tile` 是 shared memory 中包含 256 个 `float` 的数组。
当前 block 内所有 thread 都能访问它；它通常只在该 block 执行期间存在，结束后
内容不再保留。

### 5. Why load data into shared memory? / 为什么先加载到 shared memory

**Question (English):** Why can it help to cache global-memory data that
multiple block threads will read repeatedly?

**问题（中文）：** 如果 block 内多个 thread 会重复读取同一段 global memory
数据，为什么可以先把它加载到 shared memory？

**Explanation (English):** One global load followed by repeated shared-memory
reads can replace many slow global-memory accesses.

**解说（中文）：** global memory 访问慢，shared memory 访问快。缓存可能减少
重复 global memory 访问。

**Correct Answer (English):** Cooperative loading pays the global-memory cost
once, after which threads reuse the faster block-local copy. It is beneficial
when reuse savings exceed loading and synchronization overhead.

**正确答案（中文）：** 可以先从 global memory 读一次到 shared memory，后续
thread 复用更快的 block-local 副本。当复用收益超过加载与同步开销时，这种方式
才有价值。

### 6. __syncthreads / __syncthreads

**Question (English):** Why is `__syncthreads()` common around shared-memory
work?

**问题（中文）：** 使用 shared memory 时，为什么经常看到
`__syncthreads()`？

~~~cpp
__syncthreads();
~~~

**Explanation (English):** If some threads load data that others consume, the
consumers must not run before all required writes complete.

**解说（中文）：** 一些 thread 写入 shared memory、其他 thread 随后读取时，
读取前必须确保写入完成。

**Correct Answer (English):** It is a block-wide barrier: every thread in the
block must reach it before any proceeds. It commonly separates cooperative
loading from use of the completed shared tile.

**正确答案（中文）：** `__syncthreads()` 是 block 内同步屏障。只有同一 block
的所有 thread 都到达后才能继续，常用于确保 shared memory 数据加载完成后再
读取。

### 7. No reuse, no benefit / 没有复用时是否值得使用

**Question (English):** Is shared memory appropriate when every thread reads
`a[idx]` once, computes `c[idx] = a[idx] + 1`, and never reuses the input?

**问题（中文）：** 每个 thread 只读取一次 `a[idx]`、计算
`c[idx] = a[idx] + 1` 且不再复用时，适合使用 shared memory 吗？

**Explanation (English):** Shared memory is not free: it adds loading,
synchronization, capacity consumption, and complexity.

**解说（中文）：** shared memory 不是免费优化，会引入加载、同步、容量占用和
复杂度。

**Correct Answer (English):** Usually no. Without reuse, staging through
shared memory may be more complex or slower than loading directly from global
memory into a register.

**正确答案（中文）：** 通常不适合。没有 block 内复用时，先搬到 shared memory
再读取，可能比直接从 global memory 读到 register 更复杂甚至更慢。

### 8. Why matrix transpose uses shared memory / Matrix transpose 为何使用 shared memory

**Question (English):** What global-memory access problem can a transpose
create, and how does shared memory help?

**问题（中文）：** matrix transpose 可能产生什么 global memory 访问问题？
shared memory 如何帮助？

~~~text
input[row][col] -> output[col][row]
~~~

**Explanation (English):** A direct transpose often makes either reads or
writes contiguous and the other side strided.

**解说（中文）：** 直接 transpose 往往一侧连续、另一侧跨步，导致 coalescing
较差。

**Correct Answer (English):** A tile can be read contiguously into shared
memory, transposed within the tile, and written contiguously to global memory.
This reorganizes global access for better coalescing.

**正确答案（中文）：** 可以把 tile 连续读入 shared memory，在 tile 内交换行列，
再连续写回 global memory，从而改善 global memory access pattern 和
coalescing。

### 9. Resource cost of heavy shared-memory use / Shared memory 用量过大的影响

**Question (English):** How can large per-block shared-memory use affect
concurrency?

**问题（中文）：** 每个 block 使用很多 shared memory 时，可能如何影响并发
执行？

**Explanation (English):** Each SM has finite shared memory. Larger per-block
allocations allow fewer blocks to reside simultaneously.

**解说（中文）：** 每个 SM 的 shared memory 总量有限。每个 block 占用越多，
同一个 SM 上通常能同时驻留的 block 越少。

**Correct Answer (English):** Resident block and warp counts may fall,
reducing occupancy and the ability to hide memory latency. Performance can
therefore decline even though each shared-memory access is fast.

**正确答案（中文）：** 驻留 block 和 warp 数可能减少，occupancy 下降，隐藏
memory latency 的能力变弱，因此性能可能反而下降。

### 10. When shared memory is worthwhile / Shared memory 何时值得使用

**Question (English):** Summarize when shared memory is worthwhile.

**问题（中文）：** 用一句话总结 shared memory 什么时候值得使用。

**Explanation (English):** Its value comes from block-local reuse, balanced
against loading and synchronization costs.

**解说（中文）：** shared memory 的价值来自 block 内复用，但也有加载和同步
成本。

**Correct Answer (English):** It is worthwhile when multiple threads in one
block reuse the same global-memory data and the shared-memory plus
`__syncthreads()` overhead is lower than repeated global-memory access.

**正确答案（中文）：** 当一个 block 内多个 thread 重复使用同一批 global memory
数据，且 shared memory 加 `__syncthreads()` 的开销小于重复访问 global memory
时，shared memory 值得使用。

## Summary / 今日总结

- **English:** Shared memory is a fast, temporary, block-local GPU workspace.
  **中文：** shared memory 是 GPU 上高速、临时、block-local 的工作区。
- **English:** It is valuable for cooperative data reuse and access-pattern
  reorganization.
  **中文：** 它适合协作复用数据和重组访问模式。
- **English:** `__syncthreads()` coordinates producers and consumers within a
  block.
  **中文：** `__syncthreads()` 协调一个 block 内的数据生产者和消费者。
- **English:** Transpose uses tiled shared memory to make global reads and
  writes more coalesced.
  **中文：** transpose 使用 shared tile 让 global 读写更 coalesced。
- **English:** Excessive per-block use can reduce occupancy.
  **中文：** 每个 block 使用过多 shared memory 可能降低 occupancy。

## Common Mistakes / 易错点

- **English:** Treating shared memory as merely a faster global memory rather
  than a cooperative workspace.
  **中文：** 把 shared memory 只看成更快的 global memory，而不是协作工作区。
- **English:** Assuming it can be shared directly across blocks.
  **中文：** 误以为 shared memory 能跨 block 直接共享。
- **English:** Assuming `__syncthreads()` synchronizes the entire grid.
  **中文：** 误以为 `__syncthreads()` 能同步整个 grid。
- **English:** Staging one-use data through shared memory.
  **中文：** 把只使用一次的数据也搬进 shared memory。

## Next Steps / 下一步

- **English:** Study shared-memory bank conflicts.
  **中文：** 学习 shared memory bank conflict。
- **English:** Compare naive and shared-memory matrix transpose and observe
  the occupancy impact.
  **中文：** 对比 naive/shared-memory matrix transpose，并观察 occupancy
  影响。
- **English:** Expand the memory-hierarchy entries in the glossary.
  **中文：** 完善 glossary 中的 CUDA 内存层级术语。
