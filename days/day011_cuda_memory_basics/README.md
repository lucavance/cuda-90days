# Day 011: CUDA Memory Basics / CUDA 内存基础

Date / 日期: 2026-06-25

## Topic / 主题

**English:** Host memory, device/global memory, shared memory, registers,
pointer access rules, lifetimes, block communication, and synchronization.

**中文：** Host memory、Device/global memory、shared memory、register、指针
访问规则、生命周期、block 通信与同步。

## Goal / 目标

**English:** Distinguish the location, visibility, speed, lifetime, and common
uses of CUDA's main memory spaces.

**中文：** 区分 CUDA 主要内存空间的位置、访问范围、速度、生命周期与典型用途。

## 10 Concept Questions / 10 个概念问题

### 1. Host memory and device memory / Host memory 与 Device memory

**Question (English):** What does each term mean, and why can a GPU kernel not
normally consume an ordinary CPU array directly?

**问题（中文）：** 两种内存分别是什么？为什么 GPU kernel 通常不能直接使用
CPU 普通数组？

**Explanation (English):** CPU code prepares data in one address space and
GPU kernels normally execute against another, requiring explicit transfers.

**解说（中文）：** CUDA 程序通常由 CPU 准备数据、GPU 执行 kernel，两端通常
使用不同内存空间，需要显式拷贝。

**Correct Answer (English):** Host memory is CPU-side memory; device memory is
GPU-side memory. A host array must normally be copied to device memory with
`cudaMemcpy` before a kernel can access it.

**正确答案（中文）：** Host memory 是 CPU 侧内存，Device memory 是 GPU 侧
内存。CPU 普通数组位于 Host memory，通常需要用 `cudaMemcpy` 拷到 Device
memory 后才能供 kernel 使用。

### 2. A pointer returned by cudaMalloc / cudaMalloc 返回的指针

**Question (English):** Where does `d_a` point after
`cudaMalloc(&d_a, size)`, and how can CPU and GPU code use it?

**问题（中文）：** `cudaMalloc(&d_a, size)` 后的 `d_a` 指向哪里？CPU 与 GPU
代码分别如何使用它？

**Explanation (English):** CPU code can hold a device-pointer value without
being able to dereference it like host memory.

**解说（中文）：** CPU 可以保存 Device pointer 的数值，但不能把它当普通 Host
pointer 直接解引用。

**Correct Answer (English):** It points to GPU device memory. Host code can
store it and pass it to CUDA APIs or a kernel launch, but normally cannot read
`d_a[0]` directly. A GPU kernel can dereference it.

**正确答案（中文）：** `d_a` 指向 GPU Device memory。CPU 可以保存、传递它，
并传给 `cudaMemcpy` 或 kernel launch，但通常不能直接访问 `d_a[0]`；GPU
kernel 可以直接读写。

### 3. Global memory versus device memory / Global memory 与 Device memory

**Question (English):** Is global memory identical to the broader term device
memory?

**问题（中文）：** global memory 与更宽泛的 Device memory 完全相同吗？

**Explanation (English):** Device memory broadly describes GPU-side memory;
global memory is its main large, device-wide address space.

**解说（中文）：** Device memory 是较宽泛的 GPU 侧内存说法；global memory 是
其中最常用的一类。

**Correct Answer (English):** Global memory is the large VRAM-backed space
accessible to all blocks and threads, and `cudaMalloc` allocations are
normally treated as global memory. “Device memory” can refer more generally
to GPU-side memory.

**正确答案（中文）：** global memory 是所有 block/thread 都能访问的主要显存
空间，`cudaMalloc` 分配通常可理解为 global memory。Device memory 则可能泛指
GPU 侧内存。

### 4. Shared versus global memory / Shared memory 与 global memory

**Question (English):** Compare visibility, speed, and lifetime.

**问题（中文）：** 比较 shared memory 与 global memory 的访问范围、速度和
生命周期。

**Explanation (English):** Shared memory is a block-cooperation tool and
often caches a small subset of global-memory data.

**解说（中文）：** shared memory 是 block 内协作工具，常用于缓存 global
memory 的一小块数据。

**Correct Answer (English):** Global memory is large, high-latency, visible
device-wide, and persists until freed. Shared memory is small, fast,
block-local on-chip storage that exists only while a block runs.

**正确答案（中文）：** global memory 容量大、延迟高、所有 block/thread 可见，
直到 `cudaFree` 才释放；shared memory 容量小、速度快、每 block 独有，随
block 执行而存在和消失。

### 5. Cross-block communication / Block 间通信

**Question (English):** Why can different blocks not exchange data directly
through shared memory, and what is the usual alternative?

**问题（中文）：** 为什么不同 block 不能直接用 shared memory 交换数据？通常
应通过什么内存？

**Explanation (English):** Every block has a separate shared-memory instance.

**解说（中文）：** shared memory 是 per-block 的，每个 block 都有独立实例。

**Correct Answer (English):** Blocks cannot see one another's shared memory.
They normally exchange results through global memory. A common global
synchronization boundary is the end of one kernel followed by another launch.

**正确答案（中文）：** 不同 block 的 shared memory 相互独立。跨 block 结果
通常写入 global memory，并常用一个 kernel 结束、后续 kernel 启动作为全局同步
边界。

### 6. Registers / Register 的用途与范围

**Question (English):** What typically lives in registers, and how does their
visibility differ from shared memory?

**问题（中文）：** register 通常存放什么？它与 shared memory 的访问范围有何
不同？

**Explanation (English):** Registers are the fastest thread-private storage
and are normally assigned by the compiler.

**解说（中文）：** register 是最快的 thread-private 存储，通常由编译器分配。

**Correct Answer (English):** Registers hold local variables, temporary
results, and frequently used scalars. A register belongs to one thread;
shared memory belongs to one block and is visible to its threads.

**正确答案（中文）：** register 通常保存局部变量、临时结果和频繁使用的小标量。
register 属于单个 thread；shared memory 属于一个 block，可由 block 内 thread
共同访问。

### 7. Ordinary local variables / 普通局部变量

**Question (English):** Where is this scalar normally stored, and how many
instances exist?

**问题（中文）：** 下面标量通常存在哪里？它是每 thread 一份还是每 block 一份？

~~~cpp
float sum = 0.0f;
~~~

**Explanation (English):** Ordinary local scalars are thread-private.

**解说（中文）：** 普通局部标量是 thread-private 的，每个 thread 执行 kernel
时都有自己的实例。

**Correct Answer (English):** It is normally stored in a register, with one
independent `sum` per thread. A 256-thread block normally has 256 instances.

**正确答案（中文）：** `sum` 通常位于 register，每个 thread 有一份。一个
256-thread block 通常有 256 份彼此独立的 `sum`。

### 8. A __shared__ array / __shared__ 数组

**Question (English):** Is this tile per thread or per block, and what problem
does it normally solve?

**问题（中文）：** 下面的 tile 是每 thread 一份还是每 block 一份？通常用于
解决什么问题？

~~~cpp
__shared__ float tile[32][32];
~~~

**Explanation (English):** `__shared__` explicitly declares block-shared
storage for reuse and cooperation.

**解说（中文）：** `__shared__` 显式声明 shared memory，常用于 block 内数据
复用和协作计算。

**Correct Answer (English):** There is one tile per block, shared by all its
threads. It caches global-memory data and supports transpose, reduction,
stencil, and other cooperative computations.

**正确答案（中文）：** 每个 block 有一份 `tile`，由 block 内所有 thread 共享。
它用于缓存 global memory 数据并支持 transpose、reduction、stencil 等协作计算。

### 9. Shared memory and __syncthreads / Shared memory 与 __syncthreads

**Question (English):** Why is a barrier often required between shared-memory
writes and reads?

**问题（中文）：** 为什么 shared memory 写入和读取之间经常需要
`__syncthreads()`？

**Explanation (English):** Shared memory exchanges data among threads, so
consumers must wait for producers.

**解说（中文）：** shared memory 经常用于 thread 间交换数据，需要保证写入
完成后再读取。

**Correct Answer (English):** `__syncthreads()` is a block-wide barrier.
Without it, some threads can read before others finish writing and observe
old, uninitialized, or incomplete values.

**正确答案（中文）：** `__syncthreads()` 是 block 内屏障。没有同步时，某些
thread 可能在其他 thread 写完前读取，得到旧值、未初始化值或不完整数据。

### 10. Memory hierarchy summary / 内存层级总结

**Question (English):** Summarize location, visibility, speed, and use for
registers, shared memory, global memory, and host memory.

**问题（中文）：** 总结 register、shared memory、global memory 和 Host memory
的位置、访问者、速度与用途。

**Explanation (English):** A useful memory model combines all four
dimensions, not speed alone.

**解说（中文）：** 理解内存层级需要同时考虑位置、访问范围、速度和生命周期。

**Correct Answer (English):**

**正确答案（中文）：**

| Memory / 内存 | Location / 位置 | Visibility / 访问范围 | Relative speed / 相对速度 | Typical use / 典型用途 |
| --- | --- | --- | --- | --- |
| Register / 寄存器 | SM register file / SM 寄存器资源 | One thread / 单个 thread | Fastest / 最快 | Locals and temporaries / 局部变量与临时结果 |
| Shared memory / 共享内存 | On-chip SM storage / SM 片上存储 | One block / 一个 block | Very fast; bank conflicts matter / 很快；需注意 bank conflict | Tiles, reuse, cooperation / tile、复用与协作 |
| Global memory / 全局内存 | GPU VRAM / GPU 显存 | All blocks and threads / 所有 block 与 thread | High latency / 延迟较高 | Arrays, kernel I/O, cross-block exchange / 数组、kernel 输入输出、跨 block 交换 |
| Host memory / 主机内存 | CPU memory / CPU 内存 | Host code / Host 代码 | Not ordinary device-accessible storage / 不是 GPU 的普通高效访问空间 | Prepare inputs and receive results / 准备输入与接收结果 |

## Summary / 今日总结

- **English:** Host and device memory are distinct address spaces.
  **中文：** Host memory 与 Device memory 是不同地址空间。
- **English:** `cudaMalloc` returns global-memory device pointers that host
  code normally cannot dereference.
  **中文：** `cudaMalloc` 返回 global-memory Device pointer，Host 通常不能
  直接解引用。
- **English:** Registers are thread-private, while shared memory is
  block-private and cooperative.
  **中文：** register 是 thread-private；shared memory 是 block-private 且用于
  协作。
- **English:** Cross-block exchange normally uses global memory and a kernel
  boundary.
  **中文：** 跨 block 交换通常使用 global memory 与 kernel 边界。
- **English:** Shared-memory communication needs correct synchronization.
  **中文：** shared-memory 通信需要正确同步。

## Common Mistakes / 易错点

- **English:** Locating host memory on the GPU.
  **中文：** 把 Host memory 放到 GPU 侧理解。
- **English:** Treating shared memory as a partition of global memory rather
  than separate on-chip storage.
  **中文：** 把 shared memory 当作从 global memory 划出的一部分，而不是片上
  存储。
- **English:** Confusing thread-private registers with block-private shared
  memory.
  **中文：** 混淆 thread-private register 与 block-private shared memory。
- **English:** Assuming one local variable instance is shared by a block.
  **中文：** 误以为普通局部变量每 block 一份，而不是每 thread 一份。

## Next Steps / 下一步

- **English:** Study coalescing, warps, memory transactions, and practical
  shared-memory bank conflicts.
  **中文：** 学习 coalescing、warp、memory transaction，以及 shared-memory
  bank conflict 的实践表现。
