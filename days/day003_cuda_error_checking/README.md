# Day 003: CUDA Error Checking / CUDA 错误检查

Date / 日期: 2026-06-09

## Topic / 主题

**English:** CUDA Runtime API return values, readable error messages, a safe
`CUDA_CHECK` macro, kernel launch/runtime checks, and synchronization policy
for debugging versus benchmarking.

**中文：** CUDA Runtime API 返回值、可读错误信息、安全的 `CUDA_CHECK` 宏、
kernel launch/runtime 检查，以及调试与 benchmark 中不同的同步策略。

## Goal / 目标

**English:** Turn the first two days' concepts about launches,
synchronization, and deferred errors into a minimal engineering discipline for
checking every CUDA operation.

**中文：** 把前两天关于 kernel launch、同步和延迟错误的概念落成最小工程习惯：
检查 CUDA API 返回值，并在调试阶段正确区分 launch error 与 runtime error。

## 10 Concept Questions / 10 个概念问题

### 1. cudaError_t and cudaSuccess / cudaError_t 与 cudaSuccess

**Question (English):** Explain `cudaError_t`, `cudaSuccess`, and
`err != cudaSuccess` in this call:

**问题（中文）：** 解释下面代码中的 `cudaError_t`、`cudaSuccess` 和
`err != cudaSuccess`：

~~~cpp
cudaError_t err = cudaMalloc(&d_a, size);
~~~

**Explanation (English):** CUDA Runtime APIs normally report success or
failure through their return values.

**解说（中文）：** CUDA Runtime API 通常通过返回值报告调用是否成功。理解这个
返回值，是编写错误检查逻辑的基础。

**Correct Answer (English):** `cudaError_t` is the CUDA Runtime error type;
`cudaSuccess` means the call succeeded; and `err != cudaSuccess` means the
API call failed.

**正确答案（中文）：** `cudaError_t` 是 CUDA Runtime API 返回的错误类型；
`cudaSuccess` 表示调用成功；`err != cudaSuccess` 表示返回值不是成功状态，
也就是 CUDA API 调用失败。

### 2. Why cudaMalloc must be checked / 为什么必须检查 cudaMalloc

**Question (English):** What error-checking problem exists in this code?

**问题（中文）：** 下面代码从错误检查角度看有什么问题？

~~~cpp
float* d_a;
cudaMalloc(&d_a, size);

vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);
~~~

**Explanation (English):** `cudaMalloc` can fail. Continuing with an invalid
pointer makes later failures harder to locate.

**解说（中文）：** `cudaMalloc` 可能失败。如果失败后继续使用 `d_a`，后面的
kernel 可能触发更难定位的问题。

**Correct Answer (English):** The return value is ignored. Initialize the
pointer, save the result, and check it:

**正确答案（中文）：** 代码没有检查 `cudaMalloc` 的返回值。应初始化指针、
保存并检查 `cudaError_t`：

~~~cpp
float* d_a = nullptr;

cudaError_t err = cudaMalloc(&d_a, size);
if (err != cudaSuccess) {
    printf("cudaMalloc failed: %s\n", cudaGetErrorString(err));
    return;
}
~~~

### 3. cudaGetErrorString / cudaGetErrorString

**Question (English):** What does `cudaGetErrorString(err)` do, and why is it
more useful than printing only an error code?

**问题（中文）：** `cudaGetErrorString(err)` 的作用是什么？为什么比只打印
错误码更有用？

~~~cpp
printf("cudaMalloc failed: %s\n", cudaGetErrorString(err));
~~~

**Explanation (English):** `cudaError_t` is an enum-like error value; a
readable message is easier to diagnose.

**解说（中文）：** `cudaError_t` 是错误枚举值。调试时，可读文本通常比数字或
枚举名更直接。

**Correct Answer (English):** It converts the CUDA error to text such as
`out of memory`, `invalid argument`, or `invalid device pointer`, making the
failure easier to understand and locate.

**正确答案（中文）：** 它会把 CUDA 错误转换成可读字符串，例如
`out of memory`、`invalid argument`、`invalid device pointer`，使错误更
容易理解和定位。

### 4. Why use CUDA_CHECK? / 为什么使用 CUDA_CHECK

**Question (English):** Why do many CUDA programs wrap repetitive API error
checking in a `CUDA_CHECK(...)` macro?

**问题（中文）：** 为什么很多 CUDA 程序会用 `CUDA_CHECK(...)` 宏封装重复的
API 错误检查？

**Explanation (English):** CUDA programs make many API calls. Repeating the
same check is noisy and makes omissions likely.

**解说（中文）：** CUDA API 调用很多，如果每次手写错误检查，代码会啰嗦，也
容易漏掉某次检查。

**Correct Answer (English):** The macro reduces boilerplate, makes missed
checks less likely, and centralizes reporting of the file, line, and readable
error message.

**正确答案（中文）：** `CUDA_CHECK(...)` 封装重复的 CUDA API 错误检查逻辑，
减少样板代码和漏检查，并统一打印文件名、行号与错误字符串。

### 5. The do-while-zero macro pattern / do-while-zero 宏写法

**Question (English):** Why is a multi-line macro commonly written as follows
instead of expanding to several bare statements?

**问题（中文）：** 为什么多行 `CUDA_CHECK` 宏经常写成下面形式，而不是直接
展开多条语句？

~~~cpp
#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = (call); \
        if (err != cudaSuccess) { \
            ... \
        } \
    } while (0)
~~~

**Explanation (English):** A macro that does not behave syntactically like one
statement can break surrounding `if/else` control flow.

**解说（中文）：** 如果宏展开后不像一条语句，容易破坏 `if/else` 等控制流
结构。

**Correct Answer (English):** `do { ... } while (0)` makes the expansion act
like one statement, safe in control-flow contexts and consistently terminated
by a semicolon at the call site.

**正确答案（中文）：** `do { ... } while (0)` 让多行宏在语法上表现得像一条
普通语句，可以安全用于 `if/else` 等上下文，并在调用处稳定地以分号结尾。

### 6. Can a kernel launch be passed to CUDA_CHECK? / Kernel launch 能否传给 CUDA_CHECK

**Question (English):** Can this expression directly check errors that occur
inside the kernel? What is wrong with it?

**问题（中文）：** 下面写法能否直接检查 kernel 内部运行错误？它本身有什么
问题？

~~~cpp
CUDA_CHECK(vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n));
~~~

**Explanation (English):** `CUDA_CHECK` expects an expression returning
`cudaError_t`. Kernel launch syntax is not such an ordinary function call.

**解说（中文）：** `CUDA_CHECK` 包装的是返回 `cudaError_t` 的 CUDA Runtime
API，而 kernel launch 语法不是这种普通函数调用。

**Correct Answer (English):** It is invalid. Launch the kernel first, then
check launch and runtime failures separately:

**正确答案（中文）：** 不能这样写。应先启动 kernel，再分别检查 launch error
和 runtime error：

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);

CUDA_CHECK(cudaGetLastError());
CUDA_CHECK(cudaDeviceSynchronize());
~~~

### 7. cudaGetLastError versus cudaDeviceSynchronize / cudaGetLastError 与 cudaDeviceSynchronize

**Question (English):** What does each line check, and why are both useful
during debugging?

**问题（中文）：** 下面两行分别检查什么？为什么调试阶段通常两行都写？

~~~cpp
CUDA_CHECK(cudaGetLastError());
CUDA_CHECK(cudaDeviceSynchronize());
~~~

**Explanation (English):** A kernel can fail during launch or launch
successfully and fail while executing.

**解说（中文）：** kernel 可能在启动阶段失败，也可能成功启动后在运行过程中
失败。调试时需要区分这两类错误。

**Correct Answer (English):** `cudaGetLastError()` commonly checks launch
configuration and submission failures. `cudaDeviceSynchronize()` waits and
exposes runtime failures such as an illegal memory access. Together they help
locate the failure phase.

**正确答案（中文）：** `cudaGetLastError()` 通常检查配置非法或启动失败等
launch error；`cudaDeviceSynchronize()` 等待 GPU 完成并暴露 illegal memory
access 等 runtime error。两者一起使用有助于定位错误阶段。

### 8. Why synchronization must be deliberate in benchmarks / Benchmark 中为何不能乱加同步

**Question (English):** Why should a benchmark not add
`cudaDeviceSynchronize()` after every kernel without a deliberate reason?

**问题（中文）：** 为什么 benchmark 中不能随意在每个 kernel 后加入
`cudaDeviceSynchronize()`？

~~~cpp
cudaDeviceSynchronize();
~~~

**Explanation (English):** Synchronization always makes the CPU wait,
regardless of whether an error occurred.

**解说（中文）：** `cudaDeviceSynchronize()` 不只在出错时产生影响；它始终会
让 CPU 等待 GPU 前面提交的工作完成。

**Correct Answer (English):** Unnecessary synchronization serializes
asynchronous work, destroys potential overlap or pipelining, and can include
extra waiting in a measurement. Debug builds benefit from eager
synchronization; performance tests should synchronize only at defined
measurement boundaries.

**正确答案（中文）：** 随意同步会强行打断 GPU 异步执行，破坏 kernel 间可能的
重叠或流水，并把额外等待计入测量。调试阶段同步有价值，性能测试阶段应只在明确
的测量边界同步。

### 9. Minimal CUDA_CHECK condition / 最小 CUDA_CHECK 条件

**Question (English):** Complete the core failure condition:

**问题（中文）：** 补全最小 CUDA API 错误检查宏的核心条件：

~~~cpp
#define CUDA_CHECK(call)                         \
    do {                                         \
        cudaError_t err = (call);                \
        if (__________) {                        \
            fprintf(stderr, "CUDA error: %s\n",  \
                    cudaGetErrorString(err));    \
            exit(1);                             \
        }                                        \
    } while (0)
~~~

**Explanation (English):** `cudaSuccess` represents success, so failure means
the result differs from it.

**解说（中文）：** CUDA API 返回 `cudaSuccess` 表示成功，因此失败条件是返回值
不等于 `cudaSuccess`。

**Correct Answer (English):** Fill in `err != cudaSuccess`. When true, the
call failed and the program should report or handle the error.

**正确答案（中文）：** 空白处应写 `err != cudaSuccess`。含义是 CUDA API
返回值不是成功状态，需要打印错误并停止程序或进行错误处理。

### 10. Minimal debug launch template / 调试阶段最小 kernel 调用模板

**Question (English):** Write the minimal debugging sequence containing a
kernel launch, a launch-error check, and synchronization with a runtime-error
check.

**问题（中文）：** 按顺序写出包含 kernel launch、launch error 检查，以及同步
并检查 runtime error 的最小调试模板。

**Explanation (English):** Kernel arguments normally pass device pointers
such as `d_a` directly, not `&d_a`.

**解说（中文）：** 调试 CUDA kernel 时既要检查启动，也要让运行时错误尽早暴露。
kernel 参数通常直接传 device pointer，例如 `d_a`，而不是 `&d_a`。

**Correct Answer (English):**

**正确答案（中文）：**

~~~cpp
vectorAdd<<<numBlocks, blockSize>>>(d_a, d_b, d_c, n);

CUDA_CHECK(cudaGetLastError());       // launch error
CUDA_CHECK(cudaDeviceSynchronize());  // runtime error, debug only
~~~

**English:** Both checking functions return `cudaError_t` and can therefore
be wrapped in `CUDA_CHECK(...)`.

**中文：** 两个检查函数都返回 `cudaError_t`，因此可以被
`CUDA_CHECK(...)` 包装。

## Summary / 今日总结

- **English:** CUDA Runtime API return values must be checked, and
  `cudaGetErrorString` turns them into readable diagnostics.
  **中文：** CUDA Runtime API 返回值必须检查，`cudaGetErrorString` 可生成
  可读诊断。
- **English:** `CUDA_CHECK` centralizes repetitive host-side checks, and the
  do-while-zero pattern makes a multi-line macro safe.
  **中文：** `CUDA_CHECK` 集中封装 Host 端重复检查，do-while-zero 让多行宏
  更安全。
- **English:** A kernel launch is checked after submission, not passed
  directly to the macro.
  **中文：** kernel launch 应在提交后检查，不能直接传给宏。
- **English:** Launch and runtime failures require different checks.
  **中文：** launch error 与 runtime error 需要不同检查。
- **English:** Synchronization policy differs between debugging and
  performance measurement.
  **中文：** 调试与性能测量应采用不同的同步策略。

## Common Mistakes / 易错点

- **English:** Reading `err != cudaSuccess` as success instead of failure.
  **中文：** 把 `err != cudaSuccess` 误读为成功，而不是失败。
- **English:** Treating `CUDA_CHECK` as device-side logic.
  **中文：** 把 `CUDA_CHECK` 当成 Device 端逻辑；它是 Host 端 C/C++ 宏。
- **English:** Passing `&d_a` instead of the device pointer `d_a` to a
  kernel.
  **中文：** 把 `&d_a` 而不是 Device 指针 `d_a` 传给 kernel。
- **English:** Adding synchronization everywhere and changing benchmark
  semantics.
  **中文：** 到处加入同步，从而改变 benchmark 语义。

## Next Steps / 下一步

- **English:** Add `CUDA_CHECK` to the vector-add program and check every CUDA
  API call.
  **中文：** 把 `CUDA_CHECK` 加入 vector add，并检查每个 CUDA API 调用。
- **English:** Keep launch/runtime checks in the debug build, then continue to
  global-memory access and coalescing.
  **中文：** 在调试版本加入 launch/runtime 检查，再学习 global memory 访问与
  coalescing。
