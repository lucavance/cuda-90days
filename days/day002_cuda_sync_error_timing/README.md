# Day 002: CUDA Synchronization, Error Checking, and Timing / CUDA 同步、错误检查与计时

Date / 日期: 2026-06-06

## Topic / 主题

**English:** CUDA kernel-launch asynchrony, synchronization points, launch and
runtime errors, CUDA event timing, and the fixed overheads that affect small
GPU workloads.

**中文：** CUDA kernel launch 的异步特性、同步点、launch/runtime error、CUDA
event 计时，以及影响小规模 GPU 工作负载的固定开销。

## Goal / 目标

**English:** Understand why CUDA execution and timing cannot be reasoned about
like an ordinary synchronous CPU program.

**中文：** 理解为什么 CUDA 程序的执行、错误检查和性能计时不能照搬普通同步
CPU 程序的直觉。

## 10 Concept Questions / 10 个概念问题

### 1. Does a kernel launch wait for the GPU? / Kernel launch 是否等待 GPU

**Question (English):** After the CPU launches `vectorAdd` below, must it wait
for the entire kernel to finish before executing `printf`?

**问题（中文）：** 下面代码中，CPU 执行到 kernel launch 后，会不会一定等 GPU
把 `vectorAdd` 全部算完，再继续执行 `printf`？

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
printf("kernel launched\n");
~~~

**Explanation (English):** A kernel launch is the CPU submitting parallel work
to the GPU, not the CPU entering an ordinary function and waiting for it.

**解说（中文）：** kernel launch 可以理解为 CPU 向 GPU 提交一个并行任务，而
不是 CPU 像普通函数调用那样进入函数并等待执行完成。

**Correct Answer (English):** No. Kernel launches are normally asynchronous by
default, so the CPU continues after submitting the work. In Chinese,
`kernel launch` can be understood as “启动核函数” or “启动一个 GPU 核函数”.

**正确答案（中文）：** 不会一定等待。默认情况下，kernel launch 通常是异步的，
CPU 提交任务后会继续往下执行。`kernel launch` 中文可理解为“启动核函数”或
“启动一个 GPU 核函数”。

### 2. Does printf prove completion? / printf 是否证明 kernel 已完成

**Question (English):** If `after launch` is printed, does that prove
`vectorAdd` has completed successfully?

**问题（中文）：** 如果打印出 `after launch`，能不能说明 `vectorAdd` 已经
正确执行完成？

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
printf("after launch\n");
~~~

**Explanation (English):** The message only proves that the CPU reached the
statement after the launch; it says nothing about GPU completion.

**解说（中文）：** CPU 打印这行日志，只说明 CPU 已经执行到 launch 后面的语句，
并不代表 GPU 已经完成前面提交的工作。

**Correct Answer (English):** No. It proves only that the CPU submitted the
launch and continued. It does not prove completion, correctness, or the
absence of a runtime error.

**正确答案（中文）：** 不能。`printf` 被执行只能说明 CPU 已经提交 kernel
launch 并继续往后执行，不能证明 GPU 已完成 kernel，也不能证明结果正确或没有
运行时错误。

### 3. cudaDeviceSynchronize / cudaDeviceSynchronize

**Question (English):** What does `cudaDeviceSynchronize()` wait for, and why
is it useful while debugging?

**问题（中文）：** `cudaDeviceSynchronize()` 的作用是什么？它会让 CPU 等待
什么？为什么调试 CUDA 程序时经常需要它？

~~~cpp
cudaDeviceSynchronize();
~~~

**Explanation (English):** Asynchronous launches require an explicit point at
which the CPU waits for previously submitted GPU work.

**解说（中文）：** kernel launch 是异步的，因此 CPU 端需要一个同步点来等待
GPU 完成前面提交的任务。

**Correct Answer (English):** It makes the CPU wait for previously submitted
work on the current device. Runtime kernel errors often surface there. It does
not copy results to the CPU; a result in `d_c` still needs a
`cudaMemcpyDeviceToHost` transfer to `h_c`.

**正确答案（中文）：** `cudaDeviceSynchronize()` 会让 CPU 等待当前 device
前面提交的任务完成。kernel 运行时错误经常会在这里暴露。它不会自动把结果拷回
CPU；结果如果在 `d_c` 中，仍需要 `cudaMemcpyDeviceToHost` 拷回 `h_c`。

### 4. Deferred errors inside a kernel / Kernel 内部错误为何延迟出现

**Question (English):** If a thread writes to `c[n + 100]`, why might the CPU
not report the error on the launch line itself?

**问题（中文）：** 如果某个 thread 写了 `c[n + 100]`，为什么 CPU 端不一定会
在 kernel launch 这一行立刻报错？

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
~~~

**Explanation (English):** The launch submits work rather than waiting for
the GPU to execute all of it. Runtime failures are commonly observed later.

**解说（中文）：** kernel launch 主要负责提交任务，而不是等待 GPU 完整执行。
kernel 内部运行时错误往往要到后续同步点才暴露。

**Correct Answer (English):** The GPU executes the kernel asynchronously while
the CPU continues. An illegal memory access may therefore be discovered at a
later synchronization point such as `cudaDeviceSynchronize()` or
`cudaMemcpy()`.

**正确答案（中文）：** 因为 kernel 在 GPU 端异步执行，CPU 提交 launch 后继续
执行。非法内存访问等运行时错误可能在 `cudaDeviceSynchronize()`、
`cudaMemcpy()` 等同步点才被发现。

### 5. cudaGetLastError / cudaGetLastError

**Question (English):** What is `cudaGetLastError()` better suited to check?

**问题（中文）：** `cudaGetLastError()` 通常更适合检查什么？

~~~text
A. kernel launch 配置或启动阶段的错误
B. kernel 内部运行完成后的所有计算结果是否正确
~~~

**Explanation (English):** Despite its broad-sounding name, the function
reports the latest runtime error state and cannot prove numerical correctness.

**解说（中文）：** `cudaGetLastError()` 的名字容易误导。它检查 CUDA runtime
记录的最近一次错误，但不能证明 kernel 的计算结果正确。

**Correct Answer (English):** A. It is commonly called after a launch to
detect configuration, argument, or launch failures. Numerical correctness
requires copying results to the host and comparing them with a reference.

**正确答案（中文）：** 选 A。`cudaGetLastError()` 常用于 kernel launch 后检查
启动阶段错误，例如配置非法、参数错误、launch 失败等。计算结果是否正确需要把
结果拷回 Host 后做 correctness check。

### 6. Launch error versus runtime error / Launch error 与 runtime error

**Question (English):** What does each of the following checks primarily
detect?

**问题（中文）：** 下面两段检查分别主要检查什么？

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
cudaError_t err = cudaGetLastError();
~~~

~~~cpp
cudaError_t err = cudaDeviceSynchronize();
~~~

**Explanation (English):** Debugging CUDA requires distinguishing whether a
kernel failed to launch or failed while running.

**解说（中文）：** CUDA 调试时要区分 kernel 是否成功启动，以及 kernel 运行
期间是否出错。

**Correct Answer (English):** `cudaGetLastError()` is commonly used for a
kernel launch error. `cudaDeviceSynchronize()` waits for submitted GPU work
and can reveal a kernel runtime error.

**正确答案（中文）：** `cudaGetLastError()` 检查最近一次 CUDA runtime 错误，
常用于检查 kernel launch error。`cudaDeviceSynchronize()` 等待 GPU 前面
提交的工作完成，常用于暴露 kernel runtime error。

### 7. Why cudaMemcpy can expose an earlier error / cudaMemcpy 为何暴露早先错误

**Question (English):** Why can this `cudaMemcpy` report an error caused by
an earlier kernel?

**问题（中文）：** 为什么下面这行 `cudaMemcpy` 有时会暴露前面 kernel 的
错误？

~~~cpp
cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);
~~~

**Explanation (English):** A synchronous device-to-host copy in the default
stream normally waits for earlier work in that stream before returning data.

**解说（中文）：** 对于默认 stream 中的同步拷贝，
`cudaMemcpyDeviceToHost` 通常需要等待同一 stream 中前面的 kernel 完成。

**Correct Answer (English):** The copy can be a synchronization point.
Asynchronous failures such as an illegal memory access may not appear at the
launch line and instead surface at a later `cudaMemcpy` or synchronization.

**正确答案（中文）：** 因为 `cudaMemcpy` 可能成为同步点。前面 kernel 中发生
的异步错误，例如 illegal memory access，可能不会在 launch 行立刻出现，而是在
后续 `cudaMemcpy` 或 `cudaDeviceSynchronize` 时暴露。

### 8. Why ordinary CPU timing is inaccurate / 普通 CPU 计时为何不准

**Question (English):** Why does this code normally fail to measure the actual
kernel execution time?

**问题（中文）：** 为什么下面这种普通 CPU 计时方式通常不能准确测量 kernel
真正执行耗时？

~~~cpp
auto start = std::chrono::high_resolution_clock::now();

vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);

auto end = std::chrono::high_resolution_clock::now();
~~~

**Explanation (English):** When the CPU records `end`, the asynchronously
launched kernel may still be running.

**解说（中文）：** 由于 kernel launch 通常是异步的，CPU 记录 `end` 时，GPU
kernel 可能还没有执行完成。

**Correct Answer (English):** The interval mainly measures CPU launch
submission overhead, not GPU execution. CPU timing needs at least a
`cudaDeviceSynchronize()` after the launch; CUDA events are the usual tool for
kernel timing.

**正确答案（中文）：** 这段代码测到的主要是 CPU 提交 kernel launch 的开销，
而不是 GPU 执行 kernel 的耗时。如果用 CPU 计时，至少要在 kernel 后加
`cudaDeviceSynchronize()`；更常见的 GPU kernel 计时方式是 CUDA events。

### 9. CUDA event timing order / CUDA event 计时顺序

**Question (English):** Put these CUDA event operations in the correct order:

**问题（中文）：** 请排列 CUDA event 计时的大致流程：

~~~text
A. cudaEventRecord(stop)
B. cudaEventCreate(start / stop)
C. cudaEventElapsedTime(...)
D. kernel launch
E. cudaEventRecord(start)
F. cudaEventSynchronize(stop)
~~~

**Explanation (English):** Events are recorded before and after GPU work, and
the stop event must complete before elapsed time is queried.

**解说（中文）：** CUDA event 计时需要在 GPU 工作前后分别记录 event，并等待
stop event 完成后再计算 elapsed time。

**Correct Answer (English):** The order is `B -> E -> D -> A -> F -> C`:

**正确答案（中文）：** 正确顺序是 `B -> E -> D -> A -> F -> C`：

~~~cpp
cudaEventCreate(&start);
cudaEventCreate(&stop);

cudaEventRecord(start);
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
cudaEventRecord(stop);

cudaEventSynchronize(stop);
cudaEventElapsedTime(&ms, start, stop);
~~~

### 10. Why small GPU workloads can be slower / 小数据量 GPU 为何可能更慢

**Question (English):** Why can a small vector add be slower on a GPU than on
a CPU? Give at least two reasons.

**问题（中文）：** 为什么“小数据量”的 vector add，GPU 版本可能比 CPU 版本
还慢？至少说出两个原因。

**Explanation (English):** GPU work has launch, transfer, and synchronization
overheads. For small inputs, those fixed costs can exceed the benefit of
parallel execution.

**解说（中文）：** GPU 擅长大规模并行任务，但启动 GPU 工作、传输数据和同步
都有额外开销。小数据量时，这些固定开销可能超过并行计算收益。

**Correct Answer (English):** Common reasons include fixed kernel-launch
overhead, host/device transfer cost, insufficient parallelism to fill the GPU,
fast CPU-cache behavior for simple vector add, and extra synchronization
waiting.

**正确答案（中文）：** 常见原因包括：kernel launch 有固定开销；Host/Device
数据拷贝有开销；小数据量并行度不够，GPU 资源用不满；CPU cache 对简单 vector
add 很快；加入 `cudaDeviceSynchronize()` 还会产生同步等待开销。

## Summary / 今日总结

- **English:** Kernel launches are normally asynchronous, so CPU progress does
  not prove GPU completion.
  **中文：** kernel launch 通常是异步的，CPU 继续执行并不能证明 GPU 已完成。
- **English:** Launch errors and runtime errors surface through different
  checks and synchronization points.
  **中文：** launch error 与 runtime error 会通过不同检查和同步点暴露。
- **English:** A device-to-host copy can expose an earlier asynchronous kernel
  error.
  **中文：** Device-to-Host 拷贝可能暴露早先的异步 kernel 错误。
- **English:** CUDA events provide the normal sequence for measuring GPU
  execution time.
  **中文：** CUDA events 提供了测量 GPU 执行时间的常用流程。
- **English:** Fixed overheads can make a small GPU workload slower than its
  CPU counterpart.
  **中文：** 固定开销可能让小规模 GPU 工作负载慢于 CPU。

## Common Mistakes / 易错点

- **English:** Treating a kernel launch as a synchronous function call.
  **中文：** 把 kernel launch 当作普通同步函数调用。
- **English:** Assuming `cudaDeviceSynchronize()` also copies device results
  to host memory.
  **中文：** 误以为 `cudaDeviceSynchronize()` 会自动把 Device 结果拷回 Host。
- **English:** Treating `cudaGetLastError()` as proof of numerical
  correctness.
  **中文：** 误以为 `cudaGetLastError()` 能证明 kernel 计算结果正确。
- **English:** Blaming a later copy or synchronization line even though the
  underlying fault occurred in an earlier kernel.
  **中文：** 只看后续拷贝或同步处的报错，而忽略真正错误可能发生在前面的 kernel。

## Next Steps / 下一步

- **English:** Implement a minimal CUDA error-checking macro and use
  `cudaGetErrorString`.
  **中文：** 实现最小 CUDA 错误检查宏并使用 `cudaGetErrorString`。
- **English:** Learn the basic stream model and global-memory coalescing.
  **中文：** 学习 CUDA stream 基本模型以及 global memory coalescing。
