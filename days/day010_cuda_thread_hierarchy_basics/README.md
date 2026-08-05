# Day 010: CUDA Thread Hierarchy Basics / CUDA 线程层级基础

Date / 日期: 2026-06-24

## Topic / 主题

**English:** CUDA's `grid -> block -> thread` hierarchy, one-dimensional
global indexing, launch geometry, boundary guards, warp-aligned block sizes,
and SM resource limits.

**中文：** CUDA 的 `grid -> block -> thread` 层级、一维全局索引、launch
geometry、边界保护、warp-aligned block size 以及 SM 资源限制。

## Goal / 目标

**English:** Understand CUDA thread organization and the standard global-index
formula used to process one-dimensional arrays.

**中文：** 通过 10 个交互问题理解 CUDA 线程组织，以及处理一维数组时常用的
全局线程索引公式。

## 10 Concept Questions / 10 个概念问题

### 1. Why a hierarchy? / 为什么使用线程层级

**Question (English):** Why are kernel threads organized into
`grid -> block -> thread` rather than one flat list?

**问题（中文）：** 为什么 kernel 的大量 thread 不放在一个“大列表”中，而要
组织成 `grid -> block -> thread`？

**Explanation (English):** CUDA must map massive parallel work to hardware.
Blocks are important scheduling and resource-allocation units tied to SMs,
registers, and shared memory.

**解说（中文）：** CUDA 需要把大量 thread 映射到 GPU 硬件。block 是与 SM、
register、shared memory 密切相关的调度和资源分配单位。

**Correct Answer (English):** The hierarchy supports hardware scheduling,
resource allocation, and programmer-visible data partitioning. One launch
creates a grid containing blocks, each containing threads.

**正确答案（中文）：** 该层级既方便硬件调度和资源分配，也方便表达数据划分。
一次 launch 产生一个 grid，grid 包含多个 block，每个 block 包含多个 thread。

### 2. One-dimensional global index / 一维全局线程索引

**Question (English):** What does this formula compute?

**问题（中文）：** 下面公式计算什么？

~~~cpp
int idx = blockIdx.x * blockDim.x + threadIdx.x;
~~~

**Explanation (English):** `threadIdx.x` is unique only inside one block; a
grid-wide index also needs the block's offset.

**解说（中文）：** `threadIdx.x` 只表示当前 block 内的局部编号。得到整个 grid
中的唯一编号还需要 block 偏移。

**Correct Answer (English):** It computes the current thread's global
one-dimensional index. `blockIdx.x * blockDim.x` counts thread positions in
earlier blocks, and `threadIdx.x` adds the local offset.

**正确答案（中文）：** 它计算当前 thread 在整个 grid 中的一维全局编号。
`blockIdx.x * blockDim.x` 表示前面 block 占用的位置，`threadIdx.x` 是当前
block 内偏移。

### 3. Number of blocks / 计算 block 数

**Question (English):** For `N = 1000` and 256 threads per block, how many
blocks are needed and why?

**问题（中文）：** 处理 `N = 1000` 的数组、每 block 256 个 thread 时，需要
多少 block？为什么？

**Explanation (English):** The block count is rounded up so every element is
covered.

**解说（中文）：** block 数需要向上取整，保证所有元素都有 thread 覆盖。

**Correct Answer (English):** Four blocks, because `4 * 256 = 1024` covers
all 1000 elements:

**正确答案（中文）：** 需要 4 个 block，因为 `4 * 256 = 1024` 能覆盖全部
1000 个元素：

~~~cpp
int blocks = (N + blockSize - 1) / blockSize;
~~~

### 4. Why a boundary guard? / 为什么需要边界判断

**Question (English):** Why does a rounded-up launch need this check?

**问题（中文）：** 向上取整启动 thread 后，为什么需要下面判断？

~~~cpp
if (idx < N) {
    out[idx] = in[idx] * 2;
}
~~~

**Explanation (English):** Four blocks launch 1024 threads for 1000 elements,
leaving 24 extra threads.

**解说（中文）：** 1000 个元素配 256 threads/block 会启动 1024 个 thread，
多出 24 个。

**Correct Answer (English):** The guard prevents those extra threads from
reading or writing beyond the arrays and causing incorrect results or an
illegal memory access.

**正确答案（中文）：** 它阻止多余 thread 访问 `in[N]`、`out[N]` 之后的非法
位置，避免错误结果或 illegal memory access。

### 5. blockDim.x versus threadIdx.x / blockDim.x 与 threadIdx.x

**Question (English):** What does each value represent?

**问题（中文）：** `blockDim.x` 与 `threadIdx.x` 分别表示什么？

**Explanation (English):** One is a dimension; the other is the current
thread's coordinate.

**解说（中文）：** 一个表示数量，另一个表示当前 thread 的编号。

**Correct Answer (English):** `blockDim.x` is the number of threads in the
block's x dimension. `threadIdx.x` is the current thread's x index, normally
`0..255` when `blockDim.x = 256`.

**正确答案（中文）：** `blockDim.x` 是每个 block 在 x 方向的 thread 数；
`threadIdx.x` 是当前 thread 在 block 内的 x 编号。`blockDim.x = 256` 时，
`threadIdx.x` 通常为 `0..255`。

### 6. Launch configuration / Kernel launch 配置

**Question (English):** What do 4 and 256 mean here?

**问题（中文）：** 下面 launch 中的 4 和 256 分别表示什么？

~~~cpp
myKernel<<<4, 256>>>();
~~~

**Explanation (English):** In a one-dimensional launch, the first value is
the block count and the second is threads per block.

**解说（中文）：** 一维 `<<<...>>>` 配置中，第一个参数是 block 数，第二个是
每个 block 的 thread 数。

**Correct Answer (English):** `gridDim.x = 4` and `blockDim.x = 256`, for a
total of 1024 launched threads.

**正确答案（中文）：** `gridDim.x = 4`，`blockDim.x = 256`，总共启动 1024
个 thread。

### 7. Using only threadIdx.x / 只使用 threadIdx.x

**Question (English):** What breaks when multiple blocks compute
`idx = threadIdx.x`?

**问题（中文）：** 多个 block 都使用 `idx = threadIdx.x` 时会出现什么问题？

**Explanation (English):** Local thread indices repeat in every block.

**解说（中文）：** `threadIdx.x` 只在当前 block 内唯一，会在不同 block 中
重复。

**Correct Answer (English):** Every block processes the same indices, such as
0–255. Work is duplicated and later array elements are omitted.

**正确答案（中文）：** 每个 block 都重复处理 0–255 等相同位置，造成重复访问，
并漏掉后续数据。

### 8. Why block size is limited / Block 的线程数为何有限

**Question (English):** Why can a block not contain unlimited threads?

**问题（中文）：** 为什么一个 block 的 thread 数不能无限大？

**Explanation (English):** An SM is a Streaming Multiprocessor, not shared
memory. It schedules blocks using finite hardware resources.

**解说（中文）：** SM 指 Streaming Multiprocessor，不是 shared memory。它
使用有限硬件资源调度 block。

**Correct Answer (English):** Registers, shared memory, maximum threads, and
resident-block limits constrain a block and its SM. A common architectural
maximum is 1024 threads per block, but exact limits depend on the GPU.

**正确答案（中文）：** SM 的 register、shared memory、最大 thread 数和最大
驻留 block 数都有限。常见硬件上限是每 block 1024 个 thread，具体取决于 GPU。

### 9. Why common block sizes are multiples of 32 / 为什么常用 128、256、512

**Question (English):** Why are 128, 256, and 512 common block sizes rather
than an arbitrary value such as 300?

**问题（中文）：** 为什么常选 128、256、512，而不是随便选 300？

**Explanation (English):** Hardware schedules threads in warps, normally 32
threads each.

**解说（中文）：** CUDA 的线程调度基本单位是 warp，一个 warp 通常有 32 个
thread。

**Correct Answer (English):** Those sizes contain 4, 8, and 16 complete warps
and usually use execution resources cleanly. 300 is valid, but its last warp
has inactive lanes.

**正确答案（中文）：** 这些值都是 32 的倍数，对应 4、8、16 个完整 warp，更
贴合执行方式。300 也能用，但最后一个 warp 只有部分 lane 有效。

### 10. Four built-in variables / 四个常用内置变量

**Question (English):** Define `threadIdx.x`, `blockIdx.x`,
`blockDim.x`, and `gridDim.x`.

**问题（中文）：** 分别说明 `threadIdx.x`、`blockIdx.x`、`blockDim.x`、
`gridDim.x` 的含义。

**Explanation (English):** These variables form the basis of
one-dimensional indexing.

**解说（中文）：** 这四个变量是一维 CUDA kernel 索引的基础。

**Correct Answer (English):**

**正确答案（中文）：**

~~~cpp
threadIdx.x  // Current thread's x index in its block / 当前 thread 在 block 内的 x 编号
blockIdx.x   // Current block's x index in the grid / 当前 block 在 grid 内的 x 编号
blockDim.x   // Threads per block in x / 每个 block 在 x 方向的 thread 数
gridDim.x    // Blocks in the grid's x dimension / grid 在 x 方向的 block 数
~~~

## Summary / 今日总结

- **English:** CUDA organizes execution as `grid -> block -> thread`, with
  blocks as scheduling and resource units.
  **中文：** CUDA 按 `grid -> block -> thread` 组织执行，block 是调度和资源
  单位。
- **English:** The standard 1D global index combines block offset and local
  thread index.
  **中文：** 标准一维全局索引结合 block 偏移和局部 thread 编号。
- **English:** Ceiling division plus a boundary check covers arbitrary array
  lengths safely.
  **中文：** 向上取整加边界检查可安全覆盖任意数组长度。
- **English:** Block sizes that are multiples of 32 align naturally with
  warps, subject to SM resource constraints.
  **中文：** 32 的倍数自然对齐 warp，但仍受 SM 资源约束。

## Common Mistakes / 易错点

- **English:** Confusing `blockDim.x` with the number of blocks.
  **中文：** 把 `blockDim.x` 当成 block 数；block 数由 `gridDim.x` 表示。
- **English:** Treating a local thread index as a grid-wide index.
  **中文：** 把 block 内局部 thread 索引当成 grid 全局索引。
- **English:** Explaining multiples of 32 using byte size instead of warp
  scheduling.
  **中文：** 用字节位数解释 32 的倍数，而不是 warp 调度。

## Next Steps / 下一步

- **English:** Study global, shared, and register memory and their relation to
  SM resources.
  **中文：** 学习 global/shared/register memory 及其与 SM 资源的关系。
- **English:** Explore how warp count and block size affect performance.
  **中文：** 观察 warp 数与 block size 如何影响性能。
