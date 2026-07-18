# Day 020: Rust CUDA Host-Device Integration / Rust CUDA 主机与设备集成

Date / 日期: 2026-07-18

## Topic / 主题

**English:** Rust and CUDA integration: host and device execution, memory
transfer, asynchronous kernels, unsafe launch boundaries, device pointers,
resource lifetimes, deferred errors, PTX, and the end-to-end execution flow.

**中文：** Rust 与 CUDA 集成：Host 与 Device 执行、内存传输、异步 kernel、
不安全启动边界、Device 指针、资源生命周期、延迟错误、PTX 以及端到端执行流程。

## Goal / 目标

**English:** Build a practical mental model for safely coordinating Rust host
code with CUDA device code, especially across separate memory spaces and
asynchronous execution.

**中文：** 建立一套实用思维模型，能够安全地协调 Rust Host 代码与 CUDA Device
代码，尤其理解独立内存空间和异步执行带来的要求。

## 10 Concept Questions / 10 道概念题

### 1. Host and device execution / Host 与 Device 执行

**Question (English):** In a Rust CUDA program, where do the Rust host program
and CUDA kernel run? Can an ordinary Rust function be launched directly as a
CUDA kernel?

**问题（中文）：** 在 Rust CUDA 程序中，Rust Host 主程序和 CUDA kernel 分别在
哪里运行？普通 Rust 函数能否直接作为 CUDA kernel 启动？

**Explanation (English):** Host and device code target different processors
and execution models. Code must be compiled for the processor that executes
it.

**解说（中文）：** Host 代码与 Device 代码面向不同的处理器和执行模型，代码
必须针对实际执行它的处理器进行编译。

**Correct Answer (English):** The Rust host program normally runs on the CPU,
while a CUDA kernel runs on the GPU. An ordinary Rust host function is compiled
to CPU machine code and cannot be launched directly on the GPU. A kernel must
be compiled by a device-capable toolchain into PTX or another CUDA device-code
format before the host program can load and launch it.

**正确答案（中文）：** Rust Host 主程序通常运行在 CPU 上，CUDA kernel 运行在
GPU 上。普通 Rust Host 函数会被编译成 CPU 机器码，不能直接在 GPU 上启动。
kernel 必须通过支持 Device 的工具链编译为 PTX 或其他 CUDA Device 代码格式，
然后才能由 Host 程序加载和启动。

### 2. Host and device memory / Host 与 Device 内存

**Question (English):** Why can a CUDA kernel not normally access the elements
of a Rust `Vec<f32>` directly? What steps are generally required before launch?

**问题（中文）：** 为什么 CUDA kernel 通常不能直接访问 Rust `Vec<f32>` 的元素？
启动 kernel 前一般需要执行哪些步骤？

**Explanation (English):** A normal `Vec` owns an allocation in host memory,
whereas a kernel normally dereferences addresses in device-accessible memory.

**解说（中文）：** 普通 `Vec` 拥有的是 Host 内存分配，而 kernel 通常解引用
Device 可访问内存中的地址。

**Correct Answer (English):** Allocate a sufficiently large device buffer,
copy the elements from host memory to it, and pass its device pointer to the
kernel. Unified memory and mapped pinned memory are special alternatives, but
an ordinary `Vec` allocation should not be treated as device memory.

**正确答案（中文）：** 首先分配足够大的 Device buffer，把元素从 Host 内存复制
进去，再将其 Device 指针传给 kernel。统一内存和映射的页锁定内存属于特殊方案，
但不能把普通 `Vec` 的内存分配直接当作 Device 内存。

### 3. Asynchronous execution and synchronization / 异步执行与同步

**Question (English):** Does the CPU always wait for a launched CUDA kernel to
finish? Why may synchronization be required before reading the result?

**问题（中文）：** CPU 启动 CUDA kernel 后是否总会等待其执行完成？读取结果前
为什么可能需要同步？

**Explanation (English):** A kernel launch normally enqueues work and returns
control to the host before the GPU has completed that work.

**解说（中文）：** kernel 启动通常只是把任务加入执行队列，并在 GPU 完成任务前
就把控制权交还给 Host。

**Correct Answer (English):** Kernel launches are normally asynchronous with
respect to the CPU. The program must establish completion before consuming the
output, for example by synchronizing a stream, waiting for an event, or using
an operation that provides the required synchronization. A synchronous
device-to-host copy may wait implicitly; an asynchronous copy requires an
appropriate later completion check.

**正确答案（中文）：** 相对于 CPU，kernel 启动通常是异步的。程序必须在使用输出
前确认任务已经完成，例如同步 stream、等待 event，或使用能够提供所需同步语义的
操作。同步的 Device-to-Host 复制可能隐式等待；异步复制则需要在之后进行适当的
完成检查。

### 4. The `unsafe` launch boundary / `unsafe` 启动边界

**Question (English):** Why is a CUDA kernel launch from Rust commonly
`unsafe`? Which conditions can the Rust compiler not verify?

**问题（中文）：** 为什么从 Rust 启动 CUDA kernel 通常需要 `unsafe`？Rust
编译器无法验证哪些条件？

**Explanation (English):** CUDA execution crosses a foreign-function and
device boundary that is outside Rust's normal type, borrow, and lifetime
analysis.

**解说（中文）：** CUDA 执行跨越了外部函数与 Device 边界，超出了 Rust 常规的
类型、借用和生命周期分析范围。

**Correct Answer (English):** The compiler generally cannot prove that kernel
argument types and layouts match, raw pointers refer to valid device memory,
allocations are large enough and correctly aligned, indexing stays in bounds,
device accesses are race-free, or asynchronously used resources remain alive.
The caller must uphold these conditions at the `unsafe` boundary.

**正确答案（中文）：** 编译器通常无法证明 kernel 参数的类型和布局完全匹配、
裸指针指向有效 Device 内存、内存大小和对齐正确、索引不会越界、Device 访问没有
数据竞争，以及异步使用的资源始终存活。调用者必须在 `unsafe` 边界保证这些条件。

### 5. Copying Rust types to the device / 将 Rust 类型复制到 Device

**Question (English):** Can the following structure be copied byte-for-byte to
the GPU and safely used by a kernel? Which kinds of Rust values are suitable
kernel arguments?

**问题（中文）：** 能否把下面的结构体按字节复制到 GPU 并由 kernel 安全使用？
哪些 Rust 值适合作为 kernel 参数？

```rust
struct Job {
    values: Vec<f32>,
    scale: f32,
}
```

**Explanation (English):** Copy semantics, ownership semantics, and a
device-compatible binary representation are separate properties.

**解说（中文）：** 复制语义、所有权语义和与 Device 兼容的二进制表示是三种不同
的属性。

**Correct Answer (English):** No. A `Vec` contains host-side ownership metadata,
including a pointer to its separately allocated elements. Copying the structure
does not copy those elements and leaves the GPU with an unsuitable host pointer.
Kernel arguments should normally use scalars, fixed-size plain-data arrays, or
layout-stable structures such as `#[repr(C)]` records containing plain values
and valid device pointers. `f32` implements `Copy`, but that does not make a
structure containing `Vec<f32>` device-copyable.

**正确答案（中文）：** 不能。`Vec` 包含 Host 端的所有权元数据，其中包括指向
独立元素分配的指针。复制结构体并不会复制这些元素，GPU 得到的仍是不合适的 Host
指针。kernel 参数通常应使用标量、固定大小的纯数据数组，或布局稳定的结构体，
例如只包含纯数据和有效 Device 指针的 `#[repr(C)]` 结构体。`f32` 实现了 `Copy`，
但这并不会让包含 `Vec<f32>` 的结构体变得可以安全复制到 Device。

### 6. Device-pointer safety conditions / Device 指针的安全条件

**Question (English):** Even with a layout-stable argument structure, which
conditions must a device pointer and its associated length satisfy before a
kernel launch?

**问题（中文）：** 即使参数结构体的布局稳定，在启动 kernel 前，Device 指针及其
关联长度仍必须满足哪些条件？

**Explanation (English):** A raw pointer carries no allocation size, ownership,
lifetime, alignment, or synchronization proof.

**解说（中文）：** 裸指针本身不携带内存分配大小、所有权、生命周期、对齐或同步
证明。

**Correct Answer (English):** The pointer must refer to a live allocation that
the active CUDA context can access, be correctly aligned for the element type,
and cover at least the number of elements claimed by the length. The allocation
must remain alive until all queued accesses finish, indexes must stay within
that length, and concurrent reads and writes must follow a race-free design.

**正确答案（中文）：** 指针必须指向当前 CUDA context 可访问且仍然有效的内存
分配，满足元素类型的对齐要求，并至少覆盖长度所声明的元素数量。在所有已排队访问
完成前，这块内存必须保持存活；索引必须位于该长度范围内，并发读写也必须采用不会
产生数据竞争的设计。

### 7. Device-buffer lifetime / Device buffer 生命周期

**Question (English):** What can happen if an asynchronously used device buffer
goes out of scope and is released before the kernel finishes? How should the
program keep this safe?

**问题（中文）：** 如果异步 kernel 完成前，正在使用的 Device buffer 已离开作用域
并被释放，可能发生什么？程序应如何保证安全？

**Explanation (English):** Rust's automatic cleanup occurs according to host
scope, but asynchronous device work may outlive the function that enqueued it.

**解说（中文）：** Rust 根据 Host 作用域自动清理资源，但异步 Device 任务可能比
提交它的函数存活得更久。

**Correct Answer (English):** Premature release can leave the GPU accessing an
invalid or reused allocation, causing corrupt output or an illegal memory
access. Keep the buffer's owner alive until the relevant stream completes, and
establish completion with stream synchronization, an event, or a library
abstraction that tracks the asynchronous resource lifetime.

**正确答案（中文）：** 过早释放可能让 GPU 继续访问已经失效或被复用的内存，导致
结果损坏或非法内存访问。应让 buffer 的所有者存活到相关 stream 完成，并通过
stream 同步、event 或能够跟踪异步资源生命周期的库抽象来确认任务完成。

### 8. Deferred CUDA errors / 延迟出现的 CUDA 错误

**Question (English):** Why can a kernel launch return success while a later
stream synchronization reports an illegal memory access?

**问题（中文）：** 为什么 kernel 启动可以返回成功，而之后同步 stream 时才报告
非法内存访问？

**Explanation (English):** Submitting work successfully and executing that work
successfully are separate stages in an asynchronous system.

**解说（中文）：** 在异步系统中，成功提交任务和成功执行任务属于两个不同阶段。

**Correct Answer (English):** The launch result can report that the request was
accepted and that immediately checkable launch parameters were valid. The GPU
executes the kernel later, so an out-of-bounds access occurs later as well. A
synchronization, copy, or another CUDA API boundary may be the first point at
which the host observes that execution error.

**正确答案（中文）：** 启动结果可以表示请求已被接受，并且能够立即检查的启动参数
有效。GPU 会在稍后执行 kernel，因此越界访问也发生在稍后。同步、复制或另一个
CUDA API 边界可能是 Host 首次观察到该执行错误的位置。

### 9. PTX and GPU code / PTX 与 GPU 代码

**Question (English):** What is PTX, and why can the GPU not execute the address
of an ordinary Rust host function?

**问题（中文）：** PTX 是什么？为什么 GPU 不能执行普通 Rust Host 函数的地址？

**Explanation (English):** CPU and GPU code use different instruction sets,
address spaces, calling conventions, and parallel execution models.

**解说（中文）：** CPU 与 GPU 代码使用不同的指令集、地址空间、调用约定和并行
执行模型。

**Correct Answer (English):** PTX is NVIDIA's virtual instruction-set and
intermediate representation for GPU programs. The CUDA driver can JIT-compile
PTX for the current GPU, while CUBIN contains binary device code for selected
GPU architectures. An ordinary Rust host function contains CPU instructions,
so GPU execution requires a separately compiled device kernel rather than a
host function pointer.

**正确答案（中文）：** PTX 是 NVIDIA 面向 GPU 程序的虚拟指令集和中间表示。
CUDA 驱动可以针对当前 GPU 即时编译 PTX，而 CUBIN 包含面向指定 GPU 架构的
Device 二进制代码。普通 Rust Host 函数包含 CPU 指令，因此 GPU 执行需要单独
编译的 Device kernel，不能使用 Host 函数指针。

### 10. End-to-end execution flow / 端到端执行流程

**Question (English):** In execution order, how does a Rust CUDA program
multiply every element of a host array by `2.0` and return the results to the
CPU?

**问题（中文）：** 按照执行顺序，Rust CUDA 程序如何把 Host 数组的每个元素乘以
`2.0`，并最终把结果交还给 CPU？

**Explanation (English):** Synchronization establishes completion, while a
device-to-host transfer moves the output into CPU-accessible memory. These are
related but distinct operations.

**解说（中文）：** 同步操作负责确认执行完成，Device-to-Host 传输则把输出移动到
CPU 可访问的内存中；二者相关但并不相同。

**Correct Answer (English):** Create the host input; initialize the CUDA
context and load the device module; allocate a sufficiently large device
buffer; copy the input from host to device; prepare valid arguments and launch
configuration; enqueue the kernel; wait for the relevant stream when required;
copy the output from device to host; and finally release the CUDA resources.
A blocking device-to-host copy can provide the required wait, but the output
transfer itself must still occur.

**正确答案（中文）：** 创建 Host 输入；初始化 CUDA context 并加载 Device module；
分配足够大的 Device buffer；把输入从 Host 复制到 Device；准备有效参数和启动配置；
提交 kernel；在需要时等待相关 stream；把输出从 Device 复制回 Host；最后释放
CUDA 资源。阻塞式 Device-to-Host 复制可以提供所需等待，但输出传输本身仍然必须
发生。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** Rust host code runs on the CPU and separately compiled kernels
  run on the GPU. **中文：** Rust Host 代码运行在 CPU 上，单独编译的 kernel
  运行在 GPU 上。
- **English:** Ordinary host and device memory are separate, so data normally
  requires explicit allocation and transfer. **中文：** 普通 Host 内存和 Device
  内存彼此独立，因此数据通常需要显式分配和传输。
- **English:** Kernel launches are asynchronous, and completion must be
  established before results or resources are used incorrectly. **中文：** kernel
  启动具有异步性，必须在错误使用结果或资源前确认任务完成。
- **English:** Device allocations must remain alive for every queued access.
  **中文：** 在所有已排队访问结束前，Device 内存分配必须保持存活。
- **English:** A successful launch submission does not prove successful device
  execution; errors may surface at synchronization. **中文：** 成功提交启动请求
  并不代表 Device 执行成功，错误可能在同步时才出现。
- **English:** PTX is device-oriented intermediate code that the CUDA driver
  can compile for a GPU. **中文：** PTX 是面向 Device 的中间代码，CUDA 驱动
  可以针对 GPU 对其进行编译。

## Common Mistakes / 常见错误

- **English:** Saying the CPU cannot manage GPU memory, instead of recognizing
  that Rust cannot statically verify CUDA pointer and lifetime invariants.
  **中文：** 误以为 CPU 无法管理 GPU 内存，而没有认识到真正的问题是 Rust 无法
  静态验证 CUDA 指针和生命周期约束。
- **English:** Treating a `Vec` as plain device-copyable data because its
  element type implements `Copy`. **中文：** 因为 `Vec` 的元素类型实现了 `Copy`，
  就误把整个 `Vec` 当作可直接复制到 Device 的纯数据。
- **English:** Confusing Rust move or `Copy` semantics with device-compatible
  memory layout. **中文：** 混淆 Rust 的移动或 `Copy` 语义与 Device 兼容的内存
  布局。
- **English:** Assuming synchronization automatically transfers results from
  device memory to host memory. **中文：** 误以为同步操作会自动把结果从 Device
  内存传输到 Host 内存。
- **English:** Releasing a buffer after enqueueing a kernel without accounting
  for asynchronous execution. **中文：** 提交异步 kernel 后立即释放 buffer，
  没有考虑异步执行所需的资源生命周期。

## Next Step / 下一步

**English:** Build a small Rust vector-addition program using a CUDA driver
binding: create a context and stream, load PTX, allocate device buffers, launch
a bounds-checked kernel, synchronize, copy the result back, and contain the
required `unsafe` operations behind a narrow safe interface.

**中文：** 使用 CUDA Driver 绑定编写一个小型 Rust 向量加法程序：创建 context
和 stream、加载 PTX、分配 Device buffer、启动带边界检查的 kernel、同步并复制
结果，同时把必要的 `unsafe` 操作限制在狭窄的安全接口之后。
