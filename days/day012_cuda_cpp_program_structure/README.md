# Day 012: CUDA C++ Program Structure / CUDA C++ 程序结构

Date / 日期: 2026-06-26

## Topic / 主题

**English:** Host and device code, `__global__` kernels, launch syntax,
global indexing, host/device allocation, copy directions, asynchronous
execution, error checks, and the minimal CUDA C++ control flow.

**中文：** Host/Device code、`__global__` kernel、launch 语法、全局索引、
Host/Device 分配、拷贝方向、异步执行、错误检查与最小 CUDA C++ 控制流。

## Goal / 目标

**English:** Connect C++ host-side orchestration with GPU-side parallel
execution in a complete minimal CUDA C++ program.

**中文：** 结合 C++/Python 学习背景，把 CPU 端流程编排与 GPU 端并行执行连接成
一个完整的最小 CUDA C++ 程序。

## 10 Concept Questions / 10 个概念问题

### 1. Where main and a kernel execute / main 与 kernel 在哪里执行

**Question (English):** Which function runs on the CPU and which runs on the
GPU?

**问题（中文）：** 下面两个函数分别在 CPU 还是 GPU 上运行？

~~~cpp
int main() {
    // ...
}
~~~

~~~cpp
__global__ void vectorAdd(float* a, float* b, float* c, int n) {
    // ...
}
~~~

**Explanation (English):** CUDA source contains both host and device code.
Their execution locations determine allocation, copies, and launch behavior.

**解说（中文）：** CUDA 源码同时包含 Host code 与 Device code。理解执行位置是
理解分配、拷贝和 launch 的基础。

**Correct Answer (English):** `main()` is host code on the CPU.
`vectorAdd` is a `__global__` kernel launched by the host and executed in
parallel by GPU threads.

**正确答案（中文）：** `main()` 是运行在 CPU 上的 Host code；
`__global__` 修饰的 `vectorAdd` 由 Host 发起 launch，函数体由大量 GPU
thread 并行执行。

### 2. Parts of a kernel launch / Kernel launch 的组成

**Question (English):** Explain each part:

**问题（中文）：** 解释下面 launch 的各组成部分：

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
~~~

**Explanation (English):** `<<<...>>>` is CUDA launch configuration, not a
normal function argument list.

**解说（中文）：** `<<<...>>>` 是 CUDA 特有的 launch 配置，不是普通函数参数。

**Correct Answer (English):** `vectorAdd` is the kernel name;
`<<<numBlocks, blockSize>>>` specifies blocks and threads per block; and
`d_a, d_b, d_c, n` are kernel arguments, normally three device pointers and
an element count.

**正确答案（中文）：** `vectorAdd` 是 kernel 名；
`<<<numBlocks, blockSize>>>` 指定 block 数与每 block 的 thread 数；
`d_a, d_b, d_c, n` 是函数体实参，通常是三个 Device pointer 和元素数量。

### 3. Meaning of __global__ / __global__ 的含义

**Question (English):** Who calls a `__global__` function, and where does it
execute?

**问题（中文）：** `__global__` 函数由谁调用、在哪里执行？

~~~cpp
__global__ void vectorAdd(float* a, float* b, float* c, int n)
~~~

**Explanation (English):** CUDA qualifiers describe call and execution
locations.

**解说（中文）：** CUDA 使用函数修饰符区分调用位置与执行位置。

**Correct Answer (English):** A `__global__` function is launched from host
code and executes on the device. The CPU uses
`kernel<<<...>>>(...)`; GPU threads run the body.

**正确答案（中文）：** `__global__` 表示函数由 Host 调用并在 Device 执行。
CPU 使用 `kernel<<<...>>>(...)` 发起 launch，GPU thread 执行函数体。

### 4. Same code, different elements / 同一份代码处理不同元素

**Question (English):** Why do threads executing the same function process
different array elements?

**问题（中文）：** 为什么每个 thread 执行同一个函数体，却处理不同数组元素？

~~~cpp
__global__ void vectorAdd(float* a, float* b, float* c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}
~~~

**Explanation (English):** CUDA follows a many-threads, same-code model, with
differences supplied by built-in indices.

**解说（中文）：** CUDA 是 many threads execute the same code 的模型，各 thread
的差异主要来自内置索引变量。

**Correct Answer (English):** Each thread has different `blockIdx.x` and/or
`threadIdx.x` values, producing a different global `idx` and therefore a
different element.

**正确答案（中文）：** 各 thread 的 `blockIdx.x` 和/或 `threadIdx.x` 不同，
因此计算出不同全局 `idx`，对应不同数组元素。

### 5. Minimal program order / 最小程序步骤顺序

**Question (English):** Order these host-side steps:

**问题（中文）：** 排列下面 Host 端步骤：

~~~text
A. cudaMemcpy 把输入从 host 拷到 device
B. cudaMalloc 在 device 上分配内存
C. 在 host 上准备输入数据
D. 启动 kernel
E. cudaMemcpy 把结果从 device 拷回 host
F. cudaFree 释放 device memory
~~~

**Explanation (English):** Data dependencies require preparation and
allocation before transfer and compute, followed by result transfer and
cleanup.

**解说（中文）：** 数据依赖决定先准备和分配，再拷入、计算、拷回，最后释放。

**Correct Answer (English):** `C -> B -> A -> D -> E -> F`:

**正确答案（中文）：** `C -> B -> A -> D -> E -> F`：

~~~text
prepare -> allocate -> copy in -> compute -> copy out -> cleanup
~~~

### 6. new versus cudaMalloc / new 与 cudaMalloc

**Question (English):** Where does each allocation live, and who can directly
access it?

**问题（中文）：** 下面两种分配分别在哪里，谁能直接访问？

~~~cpp
float* h_a = new float[n];
cudaMalloc(&d_a, n * sizeof(float));
~~~

**Explanation (English):** CUDA programs contain both host and device
pointers, which must not be confused.

**解说（中文）：** CUDA 程序同时存在 Host pointer 与 Device pointer，必须区分。

**Correct Answer (English):** `new` allocates `n` floats in CPU host memory,
directly accessible to CPU code. `cudaMalloc` allocates bytes in GPU
device/global memory, directly accessible to kernels; host code normally
cannot dereference it like an array.

**正确答案（中文）：** `new float[n]` 在 CPU Host memory 分配 `n` 个
`float`；`cudaMalloc` 在 GPU Device/global memory 分配字节。CPU 能直接访问
前者，GPU kernel 能直接访问后者；CPU 通常不能把 Device pointer 当普通数组
解引用。

### 7. Copy direction / cudaMemcpy 为何指定方向

**Question (English):** Why does `cudaMemcpy` require a direction, and what
can happen if it is wrong?

**问题（中文）：** 为什么 `cudaMemcpy` 需要指定方向？方向写反可能怎样？

~~~cpp
cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);
cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);
~~~

**Explanation (English):** Source and destination can belong to different
address spaces.

**解说（中文）：** 源地址与目标地址可能属于不同内存空间，必须明确数据方向。

**Correct Answer (English):** The signature is
`cudaMemcpy(dst, src, size, direction)`. A mismatched direction can return an
API error, produce incorrect data, or overwrite the wrong buffer.

**正确答案（中文）：** 参数顺序是 `cudaMemcpy(dst, src, size, direction)`。
方向写反可能导致 API 错误、错误结果，或用错误数据覆盖目标缓冲区。

### 8. Asynchronous kernel launch / Kernel launch 的异步性

**Question (English):** Does the CPU normally wait after this launch?

**问题（中文）：** CPU 执行下面 launch 后通常会等待 GPU 完成吗？

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
~~~

**Explanation (English):** Host and device timelines are not inherently
synchronized.

**解说（中文）：** Host code 与 Device work 的时间线并不天然同步。

**Correct Answer (English):** The launch is normally asynchronous to the host.
The CPU continues until a synchronization point such as
`cudaDeviceSynchronize()` or a synchronous device-to-host copy.

**正确答案（中文）：** kernel launch 对 Host 通常异步。CPU 会继续执行，直到
`cudaDeviceSynchronize()` 或同步的 Device-to-Host 拷贝等同步点。

### 9. Launch and runtime checks / Launch 与 runtime 检查

**Question (English):** What does each function primarily reveal?

**问题（中文）：** 下面两个函数分别主要检查什么？

~~~cpp
cudaGetLastError();
cudaDeviceSynchronize();
~~~

**Explanation (English):** Some failures are available immediately after
launch; others occur during execution.

**解说（中文）：** 一些错误会在 launch 后立即出现，另一些在执行过程中才发生。

**Correct Answer (English):** `cudaGetLastError()` commonly detects immediate
launch failures such as invalid configuration. `cudaDeviceSynchronize()`
waits for completion and can reveal runtime failures such as illegal memory
access.

**正确答案（中文）：** `cudaGetLastError()` 通常检查配置非法等即时 launch
error；`cudaDeviceSynchronize()` 等待任务完成并暴露 illegal memory access
等 runtime error。

### 10. Complete host-side flow / 完整 Host 端流程

**Question (English):** Summarize the host-side flow from data preparation to
cleanup.

**问题（中文）：** 总结从数据准备到资源释放的最小 CUDA C++ Host 端流程。

**Explanation (English):** The CPU orchestrates while the GPU performs
parallel computation.

**解说（中文）：** CPU 负责流程编排，GPU 负责并行计算。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
prepare -> allocate -> copy in -> compute -> copy out -> cleanup
~~~

~~~cpp
// 1. Prepare host data / Host 准备数据
float* h_a = new float[n];

// 2. Allocate device memory / Device 分配内存
cudaMalloc(&d_a, size);

// 3. Host -> device
cudaMemcpy(d_a, h_a, size, cudaMemcpyHostToDevice);

// 4. Launch kernel / 启动 kernel
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);

// 5. Device -> host
cudaMemcpy(h_c, d_c, size, cudaMemcpyDeviceToHost);

// 6. Release resources / 释放资源
cudaFree(d_a);
delete[] h_a;
~~~

## Summary / 今日总结

- **English:** `main()` orchestrates on the CPU; `__global__` kernels execute
  on the GPU.
  **中文：** `main()` 在 CPU 编排；`__global__` kernel 在 GPU 执行。
- **English:** `<<<...>>>` is launch configuration, while the following
  parentheses contain kernel arguments.
  **中文：** `<<<...>>>` 是 launch 配置，后续圆括号才包含 kernel 实参。
- **English:** Host and device allocation and explicit copy directions form
  the data path.
  **中文：** Host/Device 分配与显式拷贝方向构成数据路径。
- **English:** Launches are asynchronous and need distinct launch/runtime
  checks.
  **中文：** launch 是异步的，需要分别检查 launch/runtime error。

## Common Mistakes / 易错点

- **English:** Treating `<<<...>>>` as ordinary kernel arguments.
  **中文：** 把 `<<<...>>>` 当成 kernel 普通参数。
- **English:** Treating `n` as the maximum valid index instead of the element
  count; valid indices are `0..n-1`.
  **中文：** 把 `n` 当最大有效索引，而不是元素数；有效索引是 `0..n-1`。
- **English:** Expecting `cudaGetLastError()` to wait for kernel completion.
  **中文：** 误以为 `cudaGetLastError()` 会等待 kernel 完成。
- **English:** Dereferencing a device pointer from ordinary CPU code.
  **中文：** 在普通 CPU 代码中直接解引用 Device pointer。

## Next Steps / 下一步

- **English:** Write and run a complete `vectorAdd.cu` with reusable CUDA
  error checking.
  **中文：** 编写并运行完整 `vectorAdd.cu`，加入可复用 CUDA error checking。
- **English:** Compare Python loops, C++ loops, and CUDA kernels as execution
  models.
  **中文：** 对比 Python for loop、C++ for loop 与 CUDA kernel 的执行模型。
