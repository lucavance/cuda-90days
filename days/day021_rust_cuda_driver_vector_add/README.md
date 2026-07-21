# Day 021: Rust CUDA Driver API Vector Add / Rust CUDA Driver API 向量加法

Date / 日期: 2026-07-21

## Topic / 主题

**English:** Rust and the CUDA Driver API for vector addition: end-to-end host
sequence, context versus stream, PTX modules and `CUfunction`, host/device
memory separation, launch bounds and boundary checks, asynchronous launch and
synchronization, `unsafe` boundaries, buffer lifetimes, deferred errors, and
narrow safe wrappers.

**中文：** 使用 Rust 与 CUDA Driver API 完成向量加法：端到端 Host 流程、
Context 与 Stream、PTX module 与 `CUfunction`、Host/Device 内存分离、启动配置
与边界检查、异步启动与同步、`unsafe` 边界、buffer 生命周期、延迟错误，以及窄
安全封装。

## Goal / 目标

**English:** Build a practical mental model for driving a bounds-checked
vector-add kernel from Rust through the CUDA Driver API, and for containing
required `unsafe` operations behind a narrow safe interface.

**中文：** 建立一套实用思维模型，能够通过 CUDA Driver API 从 Rust 驱动带边界
检查的向量加法 kernel，并把必要的 `unsafe` 操作限制在狭窄的安全接口之后。

## 10 Concept Questions / 10 道概念题

### 1. End-to-end Driver API sequence / Driver API 端到端顺序

**Question (English):** When using the CUDA Driver API from Rust for vector
add (instead of Runtime API `<<<>>>` launches), what is a sensible order for:
creating a context, creating a stream, loading a PTX module, allocating device
memory, host-to-device copy, launching the kernel, synchronizing,
device-to-host copy, and releasing resources? Which steps may be reordered,
and which must not?

**问题（中文）：** 在用 Rust 调用 CUDA Driver API（而不是 Runtime API 的
`<<<>>>`）做 vector add 时，创建 context、创建 stream、加载 PTX module、分配
device 内存、H2D 拷贝、launch kernel、同步、D2H 拷贝、释放资源，大致应按什么
顺序完成？哪些步骤可以调换顺序？哪些绝对不能调换？为什么？

**Explanation (English):** Nearly all Driver API work depends on an
established CUDA context. After that, stream creation, module loading, and
device allocation are often interchangeable, but data movement and launch have
harder dependencies.

**解说（中文）：** 几乎所有 Driver API 工作都依赖已建立的 CUDA context。在此
之后，创建 stream、加载 module 和分配 device 内存常常可以互调，但数据搬运与
launch 有更硬的依赖关系。

**Correct Answer (English):** A stable order is: create or activate a context;
then create a stream, load the PTX module, and allocate device buffers in any
order among themselves; copy inputs host-to-device; launch the kernel; wait for
completion; copy outputs device-to-host; and finally release resources.
Context must come first. Allocation must precede the corresponding H2D copy.
The module/function must be ready before launch. Input H2D must precede a
kernel that reads those inputs. Free only after all queued uses complete.
Context and stream must not be swapped: streams require a context.

**正确答案（中文）：** 较稳妥的顺序是：创建或激活 context；随后在 stream、
加载 PTX module、分配 device buffer 之间常可互调；再做输入的 H2D；launch
kernel；等待完成；D2H 拷回输出；最后释放资源。context 必须最先建立。分配必须
在对应的 H2D 之前。module/function 必须在 launch 之前就绪。若 kernel 要读输入，
H2D 必须在 launch 之前。只有在所有已排队使用结束后才能释放。context 与 stream
不能对调：创建 stream 依赖 context。

### 2. Context versus stream / Context 与 Stream

**Question (English):** What do a CUDA context and a CUDA stream each manage?
Can a program still complete vector add correctly using only the default
stream? What is the main cost or limitation?

**问题（中文）：** CUDA Context（如 `CUcontext`）和 Stream（如 `CUstream`）
分别管什么？如果只用默认 stream、不显式创建 stream，程序还能不能正确跑完一次
vector add？代价或限制是什么？

**Explanation (English):** A context is the CUDA execution environment for a
device. A stream is a queue of GPU work, not a mechanism for creating threads.

**解说（中文）：** Context 是某个设备上的 CUDA 执行环境。Stream 是一条 GPU
任务队列，而不是用来创建 thread 的机制。

**Correct Answer (English):** The context owns the device execution environment
in which modules, allocations, and launches are associated. A stream orders
kernels, copies, and related work submitted to that queue. Thread, block, and
grid counts come from the launch configuration, not from stream creation.
Using only the default stream can still run a correct sequential vector add.
The main limitation is weaker control over concurrency and overlap: compute and
transfers are harder to pipeline, and default-stream semantics can serialize
with other CUDA work. For a single simple experiment, speed is often similar;
the cost shows up in concurrent or high-throughput designs.

**正确答案（中文）：** Context 负责设备上的 CUDA 执行环境，module、内存分配和
launch 都关联到它。Stream 负责在该队列上按序提交 kernel、拷贝等相关工作。
thread / block / grid 由 launch 配置决定，不是由创建 stream 决定。只用默认
stream 仍然可以正确跑完一次串行 vector add。主要限制是并发与重叠控制变弱：
计算与传输更难流水线化，默认 stream 语义也更容易与其它 CUDA 工作串行化。对
单次简单实验，速度常常差不多；代价更多体现在并发或高吞吐设计中。

### 3. PTX module and `CUfunction` / PTX module 与 `CUfunction`

**Question (English):** After loading PTX through the Driver API, programs
usually obtain a function handle such as `CUfunction` and then call something
like `cuLaunchKernel`. What problem does loading the PTX module solve, and
what problem does obtaining the launchable function solve? Why can the loaded
PTX not be invoked like an ordinary Rust function?

**问题（中文）：** Driver API 里加载 PTX 后，通常还会拿到一个函数句柄（如
`CUfunction`），再用类似 `cuLaunchKernel` 启动。加载 PTX module 和拿到可
launch 的 function 分别解决什么问题？为什么不能「加载完 PTX 就直接当普通
Rust 函数调用」？

**Explanation (English):** PTX is NVIDIA's Parallel Thread eXecution
intermediate representation for GPU code. A module is a loaded package of
device code; a function is one entry point inside that package.

**解说（中文）：** PTX 是 NVIDIA 面向 GPU 代码的 Parallel Thread eXecution
中间表示。module 是已加载的一包 Device 代码；function 是其中的一个入口。

**Correct Answer (English):** Loading the PTX module gives the driver a package
of device code, which it may JIT-compile for the current GPU. Obtaining
`CUfunction` selects one named kernel entry from that module for launch. The
loaded code cannot be called as an ordinary Rust function because it targets
the GPU and must be submitted asynchronously through the Driver API with grid,
block, arguments, and stream information. Ordinary Rust calls follow the CPU
calling convention and do not perform CUDA launches.

**正确答案（中文）：** 加载 PTX module 是把一包 Device 代码交给驱动，驱动可能
再针对当前 GPU 做 JIT 编译。拿到 `CUfunction` 是从该 module 中按名字取出某个
可启动入口。已加载代码不能当作普通 Rust 函数调用，因为它面向 GPU，必须通过
Driver API 异步提交，并带上 grid、block、参数和 stream 等信息。普通 Rust 调用
遵循 CPU 调用约定，不会执行 CUDA launch。

### 4. Host `Vec` versus device pointers / Host `Vec` 与 Device 指针

**Question (English):** Why can a program generally not pass `&vec` or
`vec.as_ptr()` directly to a kernel as a device pointer? What are the three
minimal steps for the correct approach?

**问题（中文）：** 做 Rust vector add 时，Host 上常有 `Vec<f32>`，Device 上是
`CUdeviceptr` 一类指针。为什么一般不能把 `&vec` 或 `vec.as_ptr()` 直接传给
kernel 当 device 指针用？正确做法的最小步骤是哪三步？

**Explanation (English):** Ordinary host pointers address CPU memory. Kernel
code normally dereferences device-accessible addresses.

**解说（中文）：** 普通 Host 指针指向 CPU 内存；kernel 代码通常解引用 Device
可访问地址。

**Correct Answer (English):** A host `Vec` allocation lives in CPU memory, so
its pointer is not a valid ordinary device address for the kernel. The minimal
sequence is: allocate device memory, copy the host data to that device buffer
(H2D), then pass the device pointer as a kernel argument and launch. Passing
arguments before the input copy would leave the kernel reading uninitialized
device memory.

**正确答案（中文）：** Host 上的 `Vec` 分配位于 CPU 内存，其指针通常不是
kernel 可用的普通 Device 地址。最小步骤是：分配 device 内存，把 Host 数据
H2D 拷入该 buffer，再把 device 指针作为 kernel 参数并 launch。若在输入拷贝前
就 launch，kernel 会读到未初始化的 device 内存。

### 5. Launch geometry and boundary checks / 启动几何与边界检查

**Question (English):** Vector-add kernels often use
`if (idx < n) { c[idx] = a[idx] + b[idx]; }` together with
`grid_size = ceil(n / block_size)`. Why launch with `grid * block >= n` and
still write `if (idx < n)`? What can go wrong if the boundary check is omitted
when `n` is not a multiple of `block_size`?

**问题（中文）：** vector add kernel 里通常有 `if (idx < n) { ... }`，以及
`grid_size = ceil(n / block_size)`。为什么经常让 `grid * block >= n`，却又在
kernel 里写 `if (idx < n)`？若故意不写边界检查，且 `n` 不是 `block_size` 的
整数倍，可能出什么问题？

**Explanation (English):** Rounding up ensures coverage of every element. The
last block then contains idle threads whose global indices fall past `n`.

**解说（中文）：** 向上取整保证每个元素都有 thread 覆盖；最后一个 block 中会
出现全局索引超过 `n` 的空闲 thread。

**Correct Answer (English):** `grid * block >= n` guarantees at least one
thread per element. `if (idx < n)` stops the extra threads in the last partial
block from touching memory beyond the arrays. Without the check, those threads
may perform out-of-bounds reads or writes, corrupting other device memory or
triggering illegal GPU accesses.

**正确答案（中文）：** `grid * block >= n` 保证每个元素至少对应一个 thread。
`if (idx < n)` 拦住最后一个不完整 block 中多出来的 thread，避免访问数组之外
的内存。若省略检查，这些 thread 可能越界读或越界写，破坏其它显存，甚至触发
GPU 非法访问。

### 6. Asynchronous launch completion / 异步启动与完成

**Question (English):** After `cuLaunchKernel` returns success, can the host
immediately treat the GPU vector add as finished and perform D2H plus result
checks? Why or why not, and what kind of operation is usually required?

**问题（中文）：** `cuLaunchKernel` 成功返回后，能否立刻认为 GPU 上的 vector
add 已经算完，并马上做 D2H、检查结果？为什么能或不能？正确做法通常要加哪一类
操作？

**Explanation (English):** A successful launch primarily means the work was
enqueued. Completion is a separate property.

**解说（中文）：** launch 成功主要表示任务已入队；是否执行完成是另一回事。

**Correct Answer (English):** No. `cuLaunchKernel` success means the launch was
accepted into a queue, not that the GPU finished the computation. The host
should synchronize, for example with `cuStreamSynchronize` or
`cuCtxSynchronize`, or rely on an operation with the needed wait semantics such
as a blocking device-to-host copy. Synchronization establishes completion; a
D2H transfer is still required to bring results back to the CPU.

**正确答案（中文）：** 不能。`cuLaunchKernel` 成功只表示启动请求已被接受入队，
不表示 GPU 已算完。Host 应进行同步，例如 `cuStreamSynchronize` 或
`cuCtxSynchronize`，或依赖具备所需等待语义的操作（如阻塞式 D2H）。同步确认
完成；要把结果拿回 CPU，仍然需要 D2H（或等价读回）。

### 7. Why CUDA Driver calls need `unsafe` / 为何 Driver 调用需要 `unsafe`

**Question (English):** When wrapping CUDA Driver calls in Rust, which of the
following usually belong in `unsafe`, and why can Rust's type system not prove
them safe on its own: passing a `CUdeviceptr` into a kernel launch; calling
`cuMemFree` while a kernel may still use that memory; passing a host
`*const f32` as if it were a device pointer?

**问题（中文）：** 在 Rust 里封装 CUDA Driver 调用时，下面哪些通常必须放在
`unsafe` 里？为什么 Rust 无法单靠类型系统保证它们安全：传递 `CUdeviceptr` 并
launch kernel；在 kernel 可能仍在使用某块 device 内存时 `cuMemFree`；把 Host
的 `*const f32` 误当成 device 指针传入？

**Explanation (English):** Device pointers, asynchronous lifetimes, and
cross-address-space addresses are runtime invariants outside ordinary Rust
borrowing.

**解说（中文）：** Device 指针、异步生命周期以及跨地址空间的地址，都属于普通
Rust 借用之外的运行时不变量。

**Correct Answer (English):** All three are unsafe in substance, and the FFI
Driver calls themselves are also typically invoked from `unsafe`. A
`CUdeviceptr` is essentially an opaque handle or address integer; Rust cannot
prove validity, aliasing, or length. Freeing while work is still queued ignores
asynchronous lifetimes the borrow checker does not track. Host and device
pointers may look similar as raw pointers, so the type system cannot reliably
distinguish address spaces. Narrow safe wrappers and RAII are used to re-establish
these invariants at API boundaries.

**正确答案（中文）：** 三者在实质上都不安全，且 FFI/Driver 调用本身通常也在
`unsafe` 中发起。`CUdeviceptr` 本质上是不透明句柄或地址整数，Rust 无法证明其
有效性、别名关系或长度。在工作仍排队时释放，忽略了借用检查器跟踪不到的异步
生命周期。Host 与 Device 指针作为裸指针可能形态相似，类型系统无法可靠区分地址
空间。因此要用窄安全封装和 RAII，在 API 边界上重新确立这些不变量。

### 8. RAII buffer lifetime versus async use / RAII buffer 寿命与异步使用

**Question (English):** Suppose `DeviceBuffer` calls `cuMemFree` in `Drop`. If
code enqueues a kernel that uses the buffer, immediately drops the buffer, and
only later calls `stream.synchronize()`, what can go wrong? What condition
should a safer release satisfy?

**问题（中文）：** 假设封装了在 `Drop` 里调用 `cuMemFree` 的 `DeviceBuffer`。
若代码是：enqueue kernel（用到这块 buffer）→ 立刻 `drop(buffer)` → 稍后才
`stream.synchronize()`，可能出什么问题？更安全的释放时机应满足什么条件？

**Explanation (English):** Drop runs on the host timeline. GPU work may still
reference the allocation after the host has freed it.

**解说（中文）：** `Drop` 发生在 Host 时间线上；GPU 工作仍可能在 Host 释放之后
继续引用那块分配。

**Correct Answer (English):** The kernel may still read or write the memory
after `cuMemFree`, causing a GPU-side use-after-free: illegal access, silent
corruption if the memory is reused, or other undefined behavior. The failure is
not that synchronize itself becomes unable to access the buffer; the free
happened too early relative to queued device work. Safer release requires that
every queued GPU operation using the buffer has completed before free, for
example by synchronizing the relevant stream first or tying ownership to
completion.

**正确答案（中文）：** kernel 可能在 `cuMemFree` 之后仍读写该内存，造成 GPU
侧 use-after-free：非法访问、内存被复用后的静默破坏，或其他未定义行为。问题
不是 synchronize 本身无法访问内存，而是相对于已排队的 Device 工作，释放太早。
更安全的释放要求：在 free 之前，所有使用该 buffer 的已入队 GPU 操作都已完成，
例如先同步相关 stream，或把所有权绑定到完成之后。

### 9. Deferred CUDA errors / CUDA 延迟错误

**Question (English):** Some CUDA errors are deferred: `cuLaunchKernel` may
return success, yet a fault such as an out-of-bounds access appears only later
at synchronization. Why can errors surface late? If a Rust wrapper checks only
the launch return value and never checks synchronize, what is missed?

**问题（中文）：** CUDA 里有一类延迟错误：`cuLaunchKernel` 当时返回成功，但
kernel 里越界等错误可能到后面同步时才暴露。为什么错误会「延后」出现？如果只
检查 launch 的返回值、从不检查 synchronize 的返回值，会漏掉什么？

**Explanation (English):** Launch acceptance and device execution are separated
in time. Many device-side failures are reported when the host waits or queries
error state.

**解说（中文）：** 接受 launch 与 Device 真正执行在时间上是分开的；许多 Device
侧失败会在 Host 等待或查询错误状态时才被报告。

**Correct Answer (English):** Errors can appear late because the host returns
from launch before the GPU executes the work; faults that occur during later
device execution are reported at synchronization or error-query points. Checking
only launch success misses device-side failures such as illegal memory access,
sticky context error states, and silently wrong results produced while the
program continues. Launch success is not execution success; synchronization
points must also be checked.

**正确答案（中文）：** 错误会延后，是因为 Host 在 GPU 执行前就从 launch 返回；
随后 Device 执行中出现的故障会在同步或错误查询点才报告。只检查 launch 成功会
漏掉非法访存等 Device 侧失败、上下文可能进入的粘性错误状态，以及程序继续运行
时给出的沉默错误结果。launch 成功不等于执行成功；同步点也必须检查错误。

### 10. Narrow safe `device_vector_add` wrapper / 窄安全 `device_vector_add` 封装

**Question (English):** For a narrow safe interface such as
`let c = device_vector_add(&a, &b)?;`, what 5 to 7 internal steps should the
function guarantee in order? Which step is the best place to keep `unsafe`
behind the boundary?

**问题（中文）：** 若安全函数希望长成 `let c = device_vector_add(&a, &b)?;`，
其内部按顺序至少应保证哪几件事？（列出 5～7 步即可）其中哪一步最适合作为把
`unsafe` 挡在内部的边界？

**Explanation (English):** The public API should accept host slices and return
host data or an error, while hiding device pointers and Driver launch details.

**解说（中文）：** 对外 API 应接受 Host slice 并返回 Host 数据或错误，同时隐藏
device 指针和 Driver launch 细节。

**Correct Answer (English):** A solid internal sequence is: validate lengths
such as `a.len() == b.len()`; ensure a CUDA context and needed stream are ready;
load PTX and obtain `CUfunction` if not already cached; allocate device buffers
for `a`, `b`, and `c`; copy inputs host-to-device; launch the bounds-checked
kernel with a correct grid and block configuration; synchronize and check
errors; copy the output device-to-host; and release resources, often via RAII
`Drop` after completion. The best `unsafe` boundary is the safe wrapper itself:
callers only see something like
`device_vector_add(&[f32], &[f32]) -> Result<Vec<f32>>`, while pointer handling,
`cuLaunchKernel`, and free stay in narrow internal `unsafe` blocks.

**正确答案（中文）：** 较完整的内部顺序是：校验长度（如 `a.len() == b.len()`）；
确保 CUDA context 及所需 stream 就绪；按需加载 PTX 并取得 `CUfunction`（可缓存）；
为 `a` / `b` / `c` 分配 device buffer；H2D 拷贝输入；以正确的 grid/block 启动
带边界检查的 kernel；同步并检查错误；D2H 得到输出；在完成后释放资源（常用
RAII `Drop`）。最适合挡住 `unsafe` 的边界就是这层安全封装本身：调用方只看到
类似 `device_vector_add(&[f32], &[f32]) -> Result<Vec<f32>>`，而指针处理、
`cuLaunchKernel` 和 free 留在内部狭窄的 `unsafe` 中。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** A practical Driver API sequence starts with context, then
  prepares stream/module/buffers, copies inputs, launches, synchronizes, copies
  outputs, and releases. **中文：** 实用的 Driver API 顺序从 context 开始，再
  准备 stream/module/buffer，拷贝输入，launch，同步，拷贝输出，最后释放。
- **English:** Context is the CUDA environment; stream is a work queue, not a
  thread factory. **中文：** Context 是 CUDA 环境；stream 是任务队列，不是
  thread 工厂。
- **English:** PTX modules package device code; `CUfunction` selects one
  launchable entry. **中文：** PTX module 打包 Device 代码；`CUfunction` 选出
  一个可启动入口。
- **English:** Host `Vec` pointers are not ordinary device addresses; allocate,
  H2D, then pass device pointers. **中文：** Host `Vec` 指针不是普通 Device
  地址；应先分配、H2D，再传 device 指针。
- **English:** Launch with coverage `grid * block >= n`, and guard with
  `idx < n`. **中文：** 用 `grid * block >= n` 覆盖全部元素，并用 `idx < n`
  做边界守卫。
- **English:** Launch success means enqueued, not completed; check
  synchronization errors as well. **中文：** launch 成功表示已入队而非已完成；
  同步点的错误也必须检查。

### Common Mistakes / 常见错误

- **English:** Swapping context and stream creation order.
  **中文：** 把创建 context 与创建 stream 的顺序对调。
- **English:** Treating a stream as the thing that creates threads.
  **中文：** 把 stream 当成创建 thread 的机制。
- **English:** Passing host pointers to kernels, or launching before H2D.
  **中文：** 把 Host 指针传给 kernel，或在 H2D 之前就 launch。
- **English:** Dropping/freeing device buffers while queued kernels still need
  them. **中文：** 在已排队 kernel 仍需要 buffer 时就 Drop/释放。
- **English:** Checking only launch return codes and ignoring deferred errors at
  synchronize. **中文：** 只检查 launch 返回值，忽略同步时的延迟错误。

### Next Step / 下一步

**English:** Implement a minimal Rust Driver API vector-add: load PTX, allocate
buffers, launch a bounds-checked kernel, synchronize with error checks, copy
results back, and hide the required `unsafe` behind
`device_vector_add(&[f32], &[f32]) -> Result<Vec<f32>>`, preferably with RAII
`DeviceBuffer` that frees only after completion.

**中文：** 实现一个最小的 Rust Driver API 向量加法：加载 PTX、分配 buffer、
启动带边界检查的 kernel、带错误检查地同步、拷回结果，并把必要的 `unsafe`
隐藏在 `device_vector_add(&[f32], &[f32]) -> Result<Vec<f32>>` 之后，最好配合
仅在完成后释放的 RAII `DeviceBuffer`。
