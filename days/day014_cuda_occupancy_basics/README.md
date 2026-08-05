# Day 014: CUDA Occupancy Basics / CUDA Occupancy 基础

Date / 日期: 2026-07-06

## Topic / 主题

**English:** CUDA occupancy, SM resource limits, resident blocks and warps,
register/shared-memory pressure, and warp-level latency hiding.

**中文：** CUDA occupancy、SM 资源限制、驻留 block/warp、register/shared
memory 压力，以及 warp 级延迟隐藏。

## Goal / 目标

**English:** Understand how block scheduling and finite SM resources determine
occupancy, why more resident warps can hide latency, and why maximum occupancy
does not guarantee maximum performance.

**中文：** 理解 block 调度与有限 SM 资源如何决定 occupancy，更多驻留 warp
为何能隐藏延迟，以及最高 occupancy 为何不保证最高性能。

## 10 Concept Questions / 10 个概念问题

### 1. SM and block scheduling / SM 与 block 调度

**Question (English):** What is an SM? Do all launched blocks run at once?

**问题（中文）：** 什么是 SM？kernel 启动很多 block 后，它们会同时执行吗？

**Explanation (English):** An SM is a Streaming Multiprocessor. Blocks are
assigned to available SM execution resources.

**解说（中文）：** SM 是 Streaming Multiprocessor。GPU 有多个 SM，block 会在
资源可用时被调度到 SM。

**Correct Answer (English):** Blocks run in batches as capacity becomes
available. Each block is assigned to one SM, which executes the block's warps.

**正确答案（中文）：** block 会分批调度到 SM。一个 block 被分配给一个 SM，
由该 SM 执行其内部 warps。

### 2. Occupancy definition / Occupancy 定义

**Question (English):** What does occupancy describe?

**问题（中文）：** CUDA occupancy 描述什么资源使用情况？

**Explanation (English):** It compares active resident warps with the
architecture's maximum resident-warp capacity.

**解说（中文）：** occupancy 比较 SM 上活跃驻留 warp 与架构最大驻留 warp
容量。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
occupancy = active warps per SM / maximum resident warps per SM
~~~

**English:** It describes how many warps are available to help hide latency.

**中文：** 它描述 SM 上有多少 warp 可用于隐藏延迟。

### 3. Can a block span SMs? / 一个 block 能否跨 SM

**Question (English):** Can parts of one 256-thread block run on different
SMs?

**问题（中文）：** 一个 256-thread block 能否一部分运行在 SM0、另一部分运行在
SM1？

**Explanation (English):** A block is the unit of SM scheduling and resource
allocation.

**解说（中文）：** block 是 SM 调度与资源分配的基本单位。

**Correct Answer (English):** No. One block and all its threads, warps,
register allocation, and shared memory belong to one SM. This enables
block-level barriers and shared memory.

**正确答案（中文）：** 不能。一个 block 的 thread、warp、register 分配与
shared memory 都属于一个 SM，这也是 block 内同步与共享内存成立的基础。

### 4. Warps per block and resident blocks / 每 block warp 数与驻留 block

**Question (English):** If an SM supports at most 64 resident warps, how many
warps are in a 256-thread block and how many such blocks fit by the warp limit
alone?

**问题（中文）：** SM 最多驻留 64 个 warp 时，256-thread block 有多少 warp？
仅考虑 warp 限制，一个 SM 最多放多少个这种 block？

**Explanation (English):** One warp normally contains 32 threads.

**解说（中文）：** 一个 warp 通常包含 32 个 thread。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
warps per block = 256 / 32 = 8
max blocks from warp limit = 64 / 8 = 8
~~~

**English:** The warp limit alone permits at most eight blocks.

**中文：** 仅按 warp 限制，一个 SM 最多驻留 8 个这样的 block。

### 5. Other residency limits / 其他驻留限制

**Question (English):** Name at least two resources besides resident-warps
that can limit blocks per SM.

**问题（中文）：** 除最大驻留 warp 数外，至少说出两个限制每 SM 驻留 block 数
的资源。

**Explanation (English):** Several hardware limits constrain residency
simultaneously.

**解说（中文）：** 多项硬件上限会同时约束 occupancy。

**Correct Answer (English):**

**正确答案（中文）：**

- **English:** Maximum resident blocks and warps per SM.
  **中文：** 每 SM 最大驻留 block 数与 warp 数。
- **English:** Registers and shared memory per SM.
  **中文：** 每 SM 的 register 与 shared memory。
- **English:** Threads per block and other architecture limits.
  **中文：** 每 block thread 数以及其他架构限制。

### 6. Register pressure / Register 使用与 occupancy

**Question (English):** Why can high register use per thread lower occupancy?

**问题（中文）：** 为什么每 thread 使用很多 register 会降低 occupancy？

**Explanation (English):** A block's register demand accumulates across all
its threads.

**解说（中文）：** register 虽然是 per-thread 资源，但 block 总需求是所有 thread
需求之和。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
block register usage = registers per thread * threads per block
~~~

**English:** Large blocks with high per-thread use can exhaust the SM register
file, reducing resident blocks and active warps.

**中文：** 每 thread 用量高时，一个 block 消耗更多 SM register file，可能减少
驻留 block 与活跃 warp。

### 7. Shared-memory pressure / Shared memory 使用与 occupancy

**Question (English):** How does large shared-memory use per block affect
occupancy, and how does it differ from register pressure?

**问题（中文）：** 每 block 使用大量 shared memory 如何影响 occupancy？它与
register 限制有何异同？

**Explanation (English):** Every resident block reserves part of the finite
shared memory on its SM.

**解说（中文）：** shared memory 是有限的 per-SM 资源，每个驻留 block 都保留
自己的份额。

**Correct Answer (English):** More shared memory per block allows fewer blocks
to fit. Both registers and shared memory limit residency; registers are
normally allocated per thread and accumulate, while shared memory is allocated
per block and shared within it.

**正确答案（中文）：** 每 block 用量越大，SM 能容纳的 block 越少。两者都是有限
SM 资源；register 通常按 thread 分配后累积为 block 总量，shared memory 则按
block 分配并在 block 内共享。

### 8. Is higher occupancy always better? / Occupancy 越高是否一定越好

**Question (English):** Must performance improve when occupancy rises from
50% to 100%?

**问题（中文）：** occupancy 从 50% 提升到 100% 时，性能一定提高吗？

**Explanation (English):** Occupancy exposes ready warps; it is not a direct
performance guarantee.

**解说（中文）：** occupancy 的作用是提供足够 ready warp，而不是直接保证性能。

**Correct Answer (English):** No. More warps help only when latency hiding is
needed. Chasing occupancy can cause register spilling, smaller tiles, worse
memory access, or poor block sizes while another bottleneck remains.

**正确答案（中文）：** 不一定。更多 warp 只在需要隐藏延迟时有帮助。盲目追求
occupancy 可能导致 register spilling、更小 tile、更差访问模式或不良 block
size，而真正瓶颈仍在别处。

### 9. Occupancy and memory latency / Occupancy 与 global memory 延迟

**Question (English):** Why can higher occupancy help a
global-memory-latency-bound kernel?

**问题（中文）：** 为什么更高 occupancy 可能帮助受 global memory latency
限制的 kernel？

**Explanation (English):** While one warp waits for a load, an SM can issue
instructions from another ready warp.

**解说（中文）：** 一个 warp 等待 global memory load 时，SM 可以执行另一个
ready warp。

**Correct Answer (English):** More active warps increase the chance that some
warp is ready when others wait, hiding memory latency and improving SM
utilization.

**正确答案（中文）：** 更多活跃 warp 提高了在部分 warp 等待时找到 ready warp
的机会，从而隐藏延迟并提高 SM 利用率。

### 10. Putting the model together / 综合关系

**Question (English):** Summarize occupancy, register/shared-memory limits,
and warp latency hiding.

**问题（中文）：** 总结 occupancy、register/shared-memory 限制与 warp 延迟
隐藏的关系。

**Explanation (English):** Resource limits determine residency; residency is
useful because it exposes runnable warps.

**解说（中文）：** 资源限制决定驻留量；驻留量的价值在于提供可运行 warp。

**Correct Answer (English):** Registers and shared memory limit resident
blocks and warps. Occupancy compares active warps with the architecture
maximum. More active warps can hide waits by switching to ready work, but high
occupancy alone does not guarantee high performance.

**正确答案（中文）：** register 与 shared memory 限制驻留 block/warp。
occupancy 比较活跃 warp 与硬件最大值。更多 warp 可在等待时切换到 ready work
来隐藏延迟，但高 occupancy 本身不保证高性能。

## Summary / 总结

- **English:** SMs receive blocks in batches, and one block never spans SMs.
  **中文：** SM 分批接收 block，一个 block 不会跨 SM。
- **English:** Occupancy measures active resident warps relative to the
  architecture maximum.
  **中文：** occupancy 衡量活跃驻留 warp 相对架构最大值的比例。
- **English:** Per-thread registers and per-block shared memory both constrain
  residency.
  **中文：** per-thread register 与 per-block shared memory 都约束驻留量。
- **English:** Ready warps hide latency, but maximum occupancy is not always
  the fastest configuration.
  **中文：** ready warp 能隐藏延迟，但最高 occupancy 不一定最快。

## Common Mistakes / 常见错误

- **English:** Calling an SM a “stream multiprocessor” instead of Streaming
  Multiprocessor.
  **中文：** 把 SM 说成 stream multiprocessor，而不是 Streaming
  Multiprocessor。
- **English:** Using current warp count rather than architectural maximum as
  the occupancy denominator.
  **中文：** 把当前 warp 数而不是架构最大驻留 warp 数作为分母。
- **English:** Confusing maximum resident warp and block counts.
  **中文：** 混淆最大驻留 warp 数与 block 数。
- **English:** Assuming warps never wait for memory.
  **中文：** 误以为 warp 不会等待 memory。
- **English:** Assuming higher occupancy guarantees higher throughput.
  **中文：** 误以为更高 occupancy 保证更高 throughput。

## Next Step / 下一步

**English:** Study block-size selection and occupancy-calculator intuition:
how block sizes such as 128, 256, and 512 interact with registers, shared
memory, and warp count.

**中文：** 学习 block-size 选择与 occupancy calculator 直觉：128、256、512
等 block size 如何与 register、shared memory 和 warp 数共同决定 occupancy。
