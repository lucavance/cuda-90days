# Day 001: Vector Add Basics / 向量加法基础

Date / 日期: 2026-06-05

## Topic / 主题

**English:** CUDA vector-add fundamentals: thread hierarchy, global indexing,
boundary checks, host/device memory, memory copies, kernel launch
configuration, and the end-to-end execution flow.

**中文：** CUDA 向量加法基础：线程层级、全局索引、边界检查、Host/Device
内存、内存拷贝、kernel launch 配置以及端到端执行流程。

## Goal / 目标

**English:** Keep the first CUDA session lightweight while building a correct
mental model of the basic concepts in a vector-add program through ten
interactive questions.

**中文：** 保持第一次 CUDA 学习轻量，通过 10 个交互式问题建立对 vector add
程序基础概念的正确思维模型。

## 10 Concept Questions / 10 个概念问题

### 1. Thread, block, and grid / Thread、block 与 grid

**Question (English):** In CUDA, what do `thread`, `block`, and `grid`
represent, and how are they related?

**问题（中文）：** 在 CUDA 里，`thread`、`block`、`grid` 分别代表什么？
它们之间是什么关系？

**Explanation (English):** Launching a CUDA kernel creates many parallel
execution instances. Their hierarchy is the foundation for understanding
kernel launches.

**解说（中文）：** CUDA kernel 启动后，会产生大量并行执行实例。理解这些执行
实例的层级，是理解 kernel launch 的基础。

**Correct Answer (English):** A thread is one parallel instance executing the
kernel code. A block is a group of threads. A grid is the complete collection
of blocks launched by one kernel invocation. The hierarchy is
`grid -> block -> thread`.

**正确答案（中文）：** thread 是执行 kernel 代码的一份并行实例；block 是一组
thread；grid 是一次 kernel launch 启动出来的全部 block。层级关系是
`grid -> block -> thread`。

### 2. Global thread index / 全局线程索引

**Question (English):** Explain `blockIdx.x`, `blockDim.x`,
`threadIdx.x`, and `idx` in the following code:

**问题（中文）：** 解释下面代码中的 `blockIdx.x`、`blockDim.x`、
`threadIdx.x` 和 `idx`：

~~~cpp
int idx = blockIdx.x * blockDim.x + threadIdx.x;
~~~

**Explanation (English):** Every thread needs to determine which data element
it owns. This expression combines a block index and an in-block thread index
into one global linear index.

**解说（中文）：** 每个 thread 都需要知道自己负责处理哪个数据元素。这个表达式
把 block 编号和 block 内 thread 编号组合成一个全局线性索引。

**Correct Answer (English):** `blockIdx.x` is the current block's index in
the x dimension; `blockDim.x` is the number of threads per block in that
dimension; `threadIdx.x` is the current thread's in-block x index; and
`idx` is the commonly used one-dimensional global thread index.

**正确答案（中文）：** `blockIdx.x` 是当前 block 在 x 维度上的索引；
`blockDim.x` 是每个 block 在 x 维度上的 thread 数量；`threadIdx.x` 是当前
thread 在 block 内 x 维度上的索引；`idx` 是一维场景下常用的全局 thread
索引。

### 3. Boundary check / 边界检查

**Question (English):** Why do kernels often use `if (idx < n)`? What can
happen if the check is omitted?

**问题（中文）：** 为什么 kernel 里经常写 `if (idx < n)`？如果不写会发生
什么？

~~~cpp
if (idx < n) {
    c[idx] = a[idx] + b[idx];
}
~~~

**Explanation (English):** CUDA programs normally round the thread count up
to cover every element, so the total number of launched threads may exceed the
actual data length.

**解说（中文）：** CUDA 程序通常会向上取整启动 thread 数，保证覆盖所有数据
元素。因此总 thread 数可能大于真实数据长度。

**Correct Answer (English):** The check prevents threads from accessing
memory outside the valid range. Without it, extra threads may read or write
out of bounds, produce incorrect results, trigger an illegal memory access, or
crash the program.

**正确答案（中文）：** `if (idx < n)` 用来避免 thread 访问越界内存。如果
不写，超出 `n` 的 thread 可能读越界、写越界、产生错误结果，甚至触发
illegal memory access 或程序崩溃。

### 4. Host and device / Host 与 Device

**Question (English):** Explain `host`, `device`, `host memory`, and
`device memory`.

**问题（中文）：** 解释 `host`、`device`、`host memory`、`device memory`。

**Explanation (English):** The CPU normally orchestrates a CUDA program while
the GPU executes parallel kernels. The two sides usually have different
memory spaces.

**解说（中文）：** CUDA 程序通常由 CPU 负责调度，由 GPU 负责执行并行 kernel。
两端通常拥有不同的内存空间。

**Correct Answer (English):** The host is the CPU side, which prepares data,
allocates GPU memory, and launches kernels. The device is the GPU side, which
executes kernels. Host memory is used by the CPU; device memory is GPU memory.

**正确答案（中文）：** host 是 CPU 端，负责准备数据、分配 GPU 内存、发起
kernel；device 是 GPU 端，负责执行 kernel；host memory 是 CPU 使用的内存；
device memory 是 GPU 使用的显存。

### 5. cudaMalloc / cudaMalloc

**Question (English):** Why does a CUDA program normally call
`cudaMalloc(&d_a, size)` instead of passing an ordinary CPU array `h_a`
directly to a kernel?

**问题（中文）：** 为什么 CUDA 程序里通常要先用 `cudaMalloc(&d_a, size)`，
而不是直接把 CPU 上的普通数组 `h_a` 传给 kernel 使用？

**Explanation (English):** An ordinary CPU array resides in host memory, while
a kernel runs on the GPU and needs an address in device memory.

**解说（中文）：** 普通 CPU 数组位于 host memory，而 kernel 在 GPU 上运行，
需要访问 device memory 中的地址。

**Correct Answer (English):** `cudaMalloc` allocates device memory and
returns a pointer such as `d_a` that the GPU can access. The input in `h_a`
must then be copied from host memory to `d_a` with `cudaMemcpy`.

**正确答案（中文）：** 需要用 `cudaMalloc` 在 device memory 中分配内存，
得到 GPU 可访问的指针 `d_a`。然后再用 `cudaMemcpy` 把 host memory 中的
`h_a` 拷贝到 device memory 中的 `d_a`。

### 6. Host-to-device copy / Host 到 Device 拷贝

**Question (English):** Explain `d_a`, `h_a`, `size`, and
`cudaMemcpyHostToDevice` in this call:

**问题（中文）：** 解释下面这行代码中的 `d_a`、`h_a`、`size` 和
`cudaMemcpyHostToDevice`：

~~~cpp
cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
~~~

**Explanation (English):** `cudaMemcpy` needs an explicit destination,
source, byte count, and transfer direction.

**解说（中文）：** `cudaMemcpy` 需要明确目标地址、源地址、拷贝大小和拷贝
方向。

**Correct Answer (English):** `d_a` is the destination in device memory;
`h_a` is the source in host memory; `size` is the number of bytes; and
`cudaMemcpyHostToDevice` declares the direction `h_a -> d_a`.

**正确答案（中文）：** `d_a` 是 device memory 中的目标地址；`h_a` 是 host
memory 中的源地址；`size` 是拷贝的字节数；`cudaMemcpyHostToDevice` 表示
数据方向是 host memory 到 device memory，也就是 `h_a -> d_a`。

### 7. Device-to-host copy / Device 到 Host 拷贝

**Question (English):** The kernel result is stored in `d_c`. Which copy
direction completes this call to return it to `h_c` on the CPU?

**问题（中文）：** kernel 计算结果在 `d_c` 中，想把结果拿回 CPU 端的
`h_c`，应该补全什么方向？

~~~cpp
cudaMemcpy(h_c, d_c, size, ???);
~~~

**Explanation (English):** A result in device memory must be copied back to
host memory before ordinary CPU code can inspect or use it.

**解说（中文）：** kernel 计算结果在 device memory 中，CPU 端要检查或使用
结果，需要把数据拷回 host memory。

**Correct Answer (English):** Use `cudaMemcpyDeviceToHost`:

**正确答案（中文）：** 使用 `cudaMemcpyDeviceToHost`：

~~~cpp
cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);
~~~

**English:** The direction is device memory to host memory, or `d_c -> h_c`.

**中文：** 数据方向是 device memory 到 host memory，也就是 `d_c -> h_c`。

### 8. Kernel launch configuration / Kernel launch 配置

**Question (English):** Explain `numBlocks`, `blockSize`, and
`<<<numBlocks, blockSize>>>` in this launch:

**问题（中文）：** 解释下面 kernel launch 中的 `numBlocks`、`blockSize` 和
`<<<numBlocks, blockSize>>>`：

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
~~~

**Explanation (English):** CUDA's `<<<...>>>` syntax specifies how much
parallel execution capacity a kernel launch creates.

**解说（中文）：** `<<<...>>>` 是 CUDA 的 kernel launch 配置语法，用来指定
启动多少并行执行资源。

**Correct Answer (English):** `numBlocks` is the number of blocks;
`blockSize` is the number of threads in each block, not a byte count. The
launch creates `numBlocks` blocks with `blockSize` threads per block.

**正确答案（中文）：** `numBlocks` 是启动的 block 数量；`blockSize` 是每个
block 中的 thread 数量，不是字节数；`<<<numBlocks, blockSize>>>` 表示启动
`numBlocks` 个 block，每个 block 中有 `blockSize` 个 thread。

### 9. Rounding numBlocks up / 向上取整 numBlocks

**Question (English):** Why is `numBlocks` commonly calculated with the
following expression instead of `n / blockSize`? Explain with `n = 1000` and
`blockSize = 256`.

**问题（中文）：** 为什么经常这样计算 `numBlocks`，而不是直接写
`n / blockSize`？请用 `n = 1000`、`blockSize = 256` 举例解释。

~~~cpp
int numBlocks = (n + blockSize - 1) / blockSize;
~~~

**Explanation (English):** Integer division rounds down. If `n` is not
divisible by `blockSize`, a simple division leaves some elements without a
thread.

**解说（中文）：** 如果 `n` 不能被 `blockSize` 整除，直接使用整数除法会
向下取整，导致部分数据没有 thread 处理。

**Correct Answer (English):** The expression performs ceiling division.
`1000 / 256` gives 3 with a remainder of 232, so three blocks cover only 768
elements. Rounding up launches four blocks and 1024 threads; the extra threads
are made safe by `if (idx < n)`.

**正确答案（中文）：** 这个公式用于向上取整。以 `n = 1000`、
`blockSize = 256` 为例，`1000 / 256 = 3` 余 `232`。如果只启动 3 个
block，只有 `3 * 256 = 768` 个 thread，无法覆盖全部数据。向上取整得到 4 个
block，总 thread 数是 1024，多出来的 thread 通过 `if (idx < n)` 避免越界。

### 10. Vector-add program flow / Vector add 程序流程

**Question (English):** Put these CUDA vector-add steps in the correct order
and briefly explain them:

**问题（中文）：** 将完整 CUDA vector add 程序的步骤按正确顺序排列，并简单
解释：

~~~text
A. cudaMemcpy 把结果从 device 拷回 host
B. 在 host 上准备输入数据
C. cudaMalloc 在 device 上分配内存
D. 启动 kernel
E. cudaMemcpy 把输入从 host 拷到 device
F. cudaFree 释放 device memory
~~~

**Explanation (English):** A CUDA program normally prepares data on the CPU,
moves it to the GPU, launches computation, returns the result, and releases
resources.

**解说（中文）：** CUDA 程序通常先在 CPU 端准备数据，再把数据传到 GPU，启动
kernel 计算，最后把结果拿回 CPU 并释放资源。

**Correct Answer (English):** The order is `B -> C -> E -> D -> A -> F`:
prepare host data, allocate device memory, copy inputs to the device, launch
the kernel, copy results back to the host, and free device memory.

**正确答案（中文）：** 顺序是 `B -> C -> E -> D -> A -> F`。完整流程是：
host 准备数据，device 分配内存，把输入从 host 拷到 device，启动 kernel，
结果从 device 拷回 host，最后释放 device memory。

## Summary / 今日总结

- **English:** The CUDA hierarchy is `grid -> block -> thread`.
  **中文：** CUDA 的层级关系是 `grid -> block -> thread`。
- **English:** A global thread index maps a thread to its data element, and a
  boundary check protects rounded-up launches.
  **中文：** 全局 thread 索引把 thread 映射到数据元素，边界检查保护向上取整后
  多出的 thread。
- **English:** Host and device normally use separate memory, connected through
  explicit allocation and copies.
  **中文：** Host 与 Device 通常使用不同的内存空间，通过显式分配和拷贝连接。
- **English:** A complete vector-add flow covers host preparation, device
  allocation, H2D, launch, D2H, and cleanup.
  **中文：** 完整 vector add 流程包括 Host 数据准备、Device 分配、H2D、
  kernel launch、D2H 和资源释放。

## Common Mistakes / 易错点

- **English:** A kernel is a GPU function entry executed in parallel by many
  threads.
  **中文：** kernel 是运行在 GPU 上、由大量 thread 并行执行的函数入口。
- **English:** `blockSize` is the thread count per block, not a byte count.
  **中文：** `blockSize` 是每个 block 中的 thread 数量，不是字节数。
- **English:** The `size` argument to `cudaMemcpy` is normally measured in
  bytes, not elements.
  **中文：** `cudaMemcpy` 的 `size` 通常是字节数，不是元素个数。

## Next Steps / 下一步

- **English:** Understand why a GPU implementation is not always faster than
  its CPU counterpart.
  **中文：** 理解为什么 GPU 版本不一定比 CPU 快。
- **English:** Learn `cudaGetLastError` and `cudaDeviceSynchronize`.
  **中文：** 学习 `cudaGetLastError` 和 `cudaDeviceSynchronize`。
- **English:** Study global-memory access and minimal Nsight/`nvidia-smi` use.
  **中文：** 学习 global memory 访问以及 Nsight/`nvidia-smi` 的最小使用。
