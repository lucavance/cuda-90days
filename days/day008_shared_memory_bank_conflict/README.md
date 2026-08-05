# Day 008: Shared Memory Bank Conflicts / Shared memory 存储体冲突

Date / 日期: 2026-06-12

## Topic / 主题

**English:** Warps, shared-memory banks, contiguous and strided access, bank
conflicts, row-major indexing, padding, and the `tile[32][33]` transpose
pattern.

**中文：** warp、shared memory bank、连续与跨步访问、bank conflict、row-major
索引、padding，以及 transpose 中的 `tile[32][33]` 模式。

## Goal / 目标

**English:** Understand why a fast memory can still become slow under a poor
access pattern and how padding changes bank mapping.

**中文：** 理解高速 shared memory 为什么仍会因不良访问模式变慢，以及 padding
如何改变 bank 映射。

## 10 Concept Questions / 10 个概念问题

### 1. What is a shared-memory bank? / 什么是 shared memory bank

**Question (English):** Why is shared memory split into banks, and when do a
warp's accesses run in parallel or conflict?

**问题（中文）：** shared memory 为什么分成多个 bank？一个 warp 的访问何时能
并行，何时可能冲突？

**Explanation (English):** Shared memory is divided into independently
serviceable channels called banks, or “存储体”.

**解说（中文）：** shared memory 内部不是单通道整体，而是分成多个可并行访问的
bank，中文可理解为“存储体”。

**Correct Answer (English):** If a warp's 32 threads access data distributed
across different banks, the accesses can be served in parallel. If multiple
threads access different addresses in one bank, the operation may be split
into multiple transactions, creating a bank conflict.

**正确答案（中文）：** 一个 warp 的 32 个 thread 如果访问分布在不同 bank 的
数据，硬件可并行服务；多个 thread 同时访问同一 bank 的不同地址时，访问可能被
拆分，产生 bank conflict。

### 2. Why shared memory can still be slow / Shared memory 为何仍可能变慢

**Question (English):** Explain using `warp`, `bank`, parallel access, and
bank conflict.

**问题（中文）：** 请使用 `warp`、`bank`、并行访问和 bank conflict 解释
shared memory 为何也可能变慢。

**Explanation (English):** Shared memory's speed depends on whether its banks
can serve the warp in parallel.

**解说（中文）：** shared memory 的速度优势依赖访问能否由多个 bank 并行服务。

**Correct Answer (English):** Different-bank accesses can proceed in parallel.
Different addresses in one bank conflict and require serialization or split
transactions, reducing performance.

**正确答案（中文）：** 一个 warp 的 thread 访问不同 bank 时通常可并行；访问
同一 bank 的不同地址时会发生冲突，需要串行化或拆分，因此变慢。

### 3. Why contiguous float access is ideal / 连续 float 访问为何理想

**Question (English):** Assuming 32 banks and four-byte floats, why is this
pattern normally efficient?

**问题（中文）：** 假设有 32 个 bank 且 `float` 为 4 bytes，为什么下面访问
通常理想？

~~~cpp
__shared__ float s[32];

int tid = threadIdx.x;
float x = s[tid];
~~~

**Explanation (English):** Consecutive float elements commonly map to
consecutive banks.

**解说（中文）：** 常见情况下，连续 `float` 元素会依次映射到不同 bank。

**Correct Answer (English):** Threads 0–31 read `s[0]`–`s[31]`, which
normally map to banks 0–31 and can be served in parallel without a conflict.

**正确答案（中文）：** thread 0–31 分别访问 `s[0]`–`s[31]`，通常映射到
bank 0–31，因此可并行访问，通常没有 bank conflict。

### 4. Why stride 32 conflicts / Stride 32 为何容易冲突

**Question (English):** Why does this pattern create a severe conflict under
the simplified rule `bank_id = index % 32`?

**问题（中文）：** 按简化规则 `bank_id = index % 32`，为什么下面访问容易产生
严重冲突？

~~~cpp
__shared__ float s[32 * 32];

int tid = threadIdx.x;
float x = s[tid * 32];
~~~

**Explanation (English):** The index stride equals the number of banks.

**解说（中文）：** 访问 index 的 stride 正好等于 bank 数量。

**Correct Answer (English):** Threads access indices 0, 32, 64, and so on.
Every index modulo 32 is zero, so all threads target different addresses in
bank 0.

**正确答案（中文）：** thread 访问 `s[0]`、`s[32]`、`s[64]` 等 index，它们
对 32 取模都为 0，因此都落到 bank 0 的不同地址。

### 5. Why stride 33 reduces conflicts / Stride 33 为何减少冲突

**Question (English):** Why does changing the stride to 33 help?

**问题（中文）：** 为什么把 stride 改成 33 会明显减少冲突？

~~~cpp
__shared__ float s[32 * 33];

int tid = threadIdx.x;
float x = s[tid * 33];
~~~

**Explanation (English):** A stride of 33 rotates the mapping across 32 banks.

**解说（中文）：** stride 从 32 改为 33 后，bank 映射会与 32 个 bank 错开。

**Correct Answer (English):** Indices 0, 33, 66, and so on map to banks 0, 1,
2, and so on. The warp's accesses spread across all banks.

**正确答案（中文）：** index 0、33、66 等分别映射到 bank 0、1、2 等，一个
warp 的访问会分散到全部 bank。

### 6. Meaning of tile[32][33] / tile[32][33] 的意义

**Question (English):** What problem does the extra column avoid compared with
`tile[32][32]`?

**问题（中文）：** 与 `tile[32][32]` 相比，额外一列主要避免什么问题？

~~~cpp
__shared__ float tile[32][33];
~~~

**Explanation (English):** This is padding: one extra element per row changes
the stride of a column access.

**解说（中文）：** 这是 padding 技巧，每行多一个元素，用来改变按列访问的
stride。

**Correct Answer (English):** A 32-float row makes column access stride by 32
and repeatedly hit one bank. A 33-float row changes the stride to 33, rotating
the bank mapping and reducing conflicts.

**正确答案（中文）：** `tile[32][32]` 按列访问时 stride 为 32，容易落在同一
bank；`tile[32][33]` 每行 padding 一个元素，使 stride 变成 33，bank 映射
错开，从而减少冲突。

### 7. Row-major access comparison / Row-major 访问比较

**Question (English):** Which access is more conflict-prone for
`float tile[32][32]`, and why?

**问题（中文）：** 对 `float tile[32][32]`，下面哪个访问更容易冲突？为什么？

~~~cpp
// A
float x = tile[threadIdx.x][0];

// B
float x = tile[0][threadIdx.x];
~~~

**Explanation (English):** In row-major layout, `tile[row][col]` has linear
index `row * 32 + col`.

**解说（中文）：** row-major 布局中，`tile[row][col]` 的线性 index 是
`row * 32 + col`。

**Correct Answer (English):** A. Its index is `tid * 32` and repeatedly maps
to one bank. B accesses a contiguous row and normally spreads across banks
0–31.

**正确答案（中文）：** A 更容易冲突。它的 index 是 `tid * 32`，容易全部映射
到同一 bank；B 连续访问一行，通常分散到 bank 0–31。

### 8. How padding improves column access / Padding 如何改善按列访问

**Question (English):** Explain why this access improves with
`tile[32][33]`:

**问题（中文）：** 请解释为什么改为 `tile[32][33]` 后，下面访问会好很多：

~~~cpp
float x = tile[threadIdx.x][0];
~~~

~~~text
index = row * 33 + col
bank_id = index % 32
~~~

**Explanation (English):** The same column in neighboring rows is now 33
floats apart instead of 32.

**解说（中文）：** 相邻行同一列不再相隔 32 个 `float`，而是 33 个。

**Correct Answer (English):** Rows 0, 1, and 2 produce indices 0, 33, and 66,
which map to banks 0, 1, and 2. The warp spreads its accesses across banks.

**正确答案（中文）：** row 0、1、2 的 index 分别为 0、33、66，对应 bank 0、
1、2；一个 warp 的访问因此分散到不同 bank。

### 9. Cost of padding / Padding 的代价

**Question (English):** What resource does `tile[32][33]` consume compared
with `tile[32][32]`, and when can that matter?

**问题（中文）：** 与 `tile[32][32]` 相比，`tile[32][33]` 多使用什么资源？
什么时候需要注意？

**Explanation (English):** Padding trades a small amount of extra shared
memory for a better access pattern.

**解说（中文）：** padding 用额外 shared memory 换取更好的访问模式。

**Correct Answer (English):** It adds one float per row, or 32 floats total.
The cost is normally small, but in a kernel already using substantial shared
memory it can reduce occupancy.

**正确答案（中文）：** 每行多一个 `float`，总共多 32 个。代价通常很小，但
kernel 的 shared memory 用量本来很高时，可能降低 occupancy。

### 10. Core intuition / 核心直觉

**Question (English):** Why do bank conflicts slow a warp, and how does
padding help?

**问题（中文）：** 为什么 bank conflict 会让 warp 变慢？padding 如何缓解？

**Explanation (English):** A conflict means the warp's accesses were not
distributed effectively across independent banks.

**解说（中文）：** bank conflict 的本质是一个 warp 的访问没有良好分散到多个
bank。

**Correct Answer (English):** A stride can map many threads to different
addresses in one bank, forcing split or serialized service. Padding changes
the stride so accesses spread across banks and regain parallelism.

**正确答案（中文）：** stride 可能让多个 thread 落到同一 bank 的不同地址，
迫使访问拆分或串行化；padding 改变 stride，让访问分散到多个 bank 并恢复并行。

## Summary / 今日总结

- **English:** A warp normally contains 32 threads, and shared memory is
  divided into banks for parallel service.
  **中文：** warp 通常包含 32 个 thread，shared memory 被划分成多个 bank 以
  支持并行访问。
- **English:** Contiguous float access usually spreads across banks; stride 32
  tends to collapse onto one bank.
  **中文：** 连续 float 访问通常分散到各 bank；stride 32 容易集中到一个 bank。
- **English:** Row-major indexing explains why column access creates a
  problematic stride.
  **中文：** row-major 索引解释了按列访问为何产生问题 stride。
- **English:** `tile[32][33]` adds padding to rotate the bank mapping.
  **中文：** `tile[32][33]` 通过 padding 旋转 bank 映射。

## Common Mistakes / 易错点

- **English:** Assuming every same-bank access conflicts; reading the same
  address may be broadcast.
  **中文：** 误以为访问同一 bank 一定冲突；访问同一地址时可能 broadcast。
- **English:** Saying `tile[32][33]` adds only one float rather than one per
  row.
  **中文：** 误以为 `tile[32][33]` 只多一个元素，而不是每行多一个。
- **English:** Treating padding as free even when shared-memory pressure is
  high.
  **中文：** 在 shared-memory 压力很高时仍把 padding 当作无成本优化。

## Next Steps / 下一步

- **English:** Implement naive, unpadded shared, and padded shared matrix
  transpose variants.
  **中文：** 实现 naive、无 padding shared、padding shared 三种 transpose。
- **English:** Compare performance and inspect bank-conflict metrics with a
  profiler.
  **中文：** 对比性能，并用 profiler 观察 bank-conflict 指标。
