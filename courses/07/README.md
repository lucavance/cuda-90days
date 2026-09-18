# Course 07: Rust GPU and CUDA Interoperation / 第七课：Rust GPU 与 CUDA 互操作

## Goals, prerequisites, and version boundary / 目标、前置与版本边界

**English:** This course turns the host/device and FFI concepts from Day020 and Day021 into three concrete implementations of an affine transformation. After completing it, you should distinguish a Rust host that launches a CUDA kernel, a kernel written in native Rust SIMT, and a Rust embedded tile language. You should also be able to explain which component compiles each program, which component owns each allocation, and which event makes it safe to read or release a result. These explanations must correspond to the source rather than merely repeat project names.

**中文：** 本课把 Day020、Day021 中的宿主与设备、外部函数接口概念，落实为仿射变换的三种具体实现。完成后，你应能区分由 Rust 宿主启动 CUDA 内核、直接使用 Rust 编写线程级内核，以及嵌入 Rust 的分块计算语言。你还应能够解释每段程序由哪个组件编译、每块内存由哪个组件拥有，以及哪个完成事件允许程序读取结果或释放资源。这些解释必须能对应到源码，而不只是复述项目名称。

**English:** Prerequisites are course 01's Linux and dynamic-library diagnosis, course 04's ownership and asynchronous lifetimes, and course 05's CUDA indexing, launch, and synchronization model. Existing Android and Linux experience helps with handles, process boundaries, and cleanup, but a device operation introduces another execution timeline. A Rust function returning successfully does not by itself establish that the GPU has stopped touching its arguments. Draw both host call order and device execution order, then check where ownership ends.

**中文：** 前置知识包括第一课的 Linux 与动态库诊断、第四课的所有权与异步生命周期，以及第五课的 CUDA 索引、启动和同步模型。已有 Android 和 Linux 经验有助于理解句柄、进程边界与资源清理，但设备操作引入了另一条执行时间线。一个 Rust 函数成功返回，本身并不能证明 GPU 已停止访问它的参数。阅读本课时，请同时画出宿主调用顺序和设备执行顺序，再检查所有权的结束位置。

**English:** Sources and APIs were checked on 2026-09-18. The CUDA reference baseline is the 13.3 archive. The local machine has an RTX 4060, Ubuntu 26.04.1, and nvcc 13.3.73; the NVML library reports 610.57 while the loaded kernel driver reports 610.43.02. This mismatch prevents a trustworthy GPU execution check in this session. CPU tests and compilation are reported separately, and the lesson neither repairs drivers nor claims a successful device run.

**中文：** 本课资料与接口核验日期为 2026 年 9 月 18 日，CUDA 参考基线使用十三点三归档。本机为 RTX 4060、Ubuntu 26.04.1，编译器为 nvcc 13.3.73；NVML 库报告 610.57，而已加载的内核驱动报告 610.43.02。版本不一致使本次无法完成可靠的 GPU 执行验证。因此，课程分别报告 CPU 实验、编译和设备执行状态，不修复驱动，也不把任何编译成功表述为 GPU 已经运行成功。

**English:** Reproducibility uses cuda-oxide revision `b9847e9515ed3a23096f22567d3eaf0a6e3e440c`, whose toolchain file pins `nightly-2026-08-28`, and cutile-rs revision `d92c160949f58328ba6e96d81005e7110ba6f2b3`, whose workspace version is 0.4.0. The latter declares Rust 1.89 or later; this lesson tested host builds with 1.98.1. cuda-oxide's example currently uses cuda-core 0.3.1. These are separate dependency graphs: a newer runtime number does not authorize silently replacing the older one. [cuda-oxide source](https://github.com/NVlabs/cuda-oxide/tree/b9847e9515ed3a23096f22567d3eaf0a6e3e440c), [cutile-rs source](https://github.com/NVlabs/cutile-rs/tree/d92c160949f58328ba6e96d81005e7110ba6f2b3).

**中文：** 复现固定使用 cuda-oxide 的 `b9847e9515ed3a23096f22567d3eaf0a6e3e440c` 提交，其工具链文件指定 `nightly-2026-08-28`；cutile-rs 固定使用 `d92c160949f58328ba6e96d81005e7110ba6f2b3` 提交，工作区版本为零点四。后者声明最低 Rust 版本为一点八九，本课实际使用一点九八点一进行宿主构建。cuda-oxide 示例当前依赖 cuda-core 零点三点一。这是两套独立依赖图，不能因为另一个运行库版本更新，就自行替换已固定的旧版本。[cuda-oxide 源码](https://github.com/NVlabs/cuda-oxide/tree/b9847e9515ed3a23096f22567d3eaf0a6e3e440c)、[cutile-rs 源码](https://github.com/NVlabs/cutile-rs/tree/d92c160949f58328ba6e96d81005e7110ba6f2b3)。

## Three programming boundaries / 三种编程边界

**English:** In host interoperation, ordinary Rust is compiled for the CPU and calls the CUDA Driver API through a binding or wrapper. A separately compiled CUDA C++ function supplies PTX or cubin. Rust can own the device allocation and validate its shape without having compiled a single device instruction itself. This approach is useful when an existing kernel is already correct and the surrounding service benefits from Rust's ownership, concurrency, or integration facilities. A Rust project language does not make separately compiled device computation a Rust kernel.

**中文：** 在宿主互操作方案中，普通 Rust 被编译为 CPU 程序，通过绑定或封装调用 CUDA Driver API。单独编译的 CUDA C++ 函数提供 PTX 或 cubin。Rust 可以拥有设备分配并检查数据形状，却完全没有参与设备指令的编译。当已有内核已经正确，而外围服务需要 Rust 的所有权、并发或集成能力时，这种方案非常实用。不能因为工程主语言是 Rust，就把其中的设备计算也称为 Rust 内核。

**English:** cuda-oxide instead provides a Rust device compilation path. Its current compiler backend lowers Rust MIR through its intermediate representation infrastructure toward LLVM and PTX. A `#[cuda_module]` contains device functions, and a `#[kernel]` exposes a launchable entry. The programmer still reasons about CUDA threads, blocks, indices, and memory. Native Rust syntax does not remove hardware scheduling or make arbitrary standard-library facilities available inside a kernel. [Compiler project](https://github.com/NVlabs/cuda-oxide/tree/b9847e9515ed3a23096f22567d3eaf0a6e3e440c). Check support in the pinned device compiler rather than relying on the host compiler accepting the syntax.

**中文：** cuda-oxide 提供的是 Rust 设备代码编译路径。当前编译后端把 Rust 的中层表示，经项目的中间表示设施逐步降低到 LLVM 和 PTX。设备函数放在 `#[cuda_module]` 中，`#[kernel]` 标记能够启动的入口。程序员依然需要考虑 CUDA 线程、线程块、索引和内存。使用原生 Rust 语法并不会消除硬件调度，也不意味着内核可以任意使用标准库设施。判断功能是否支持，要查看该固定版本的设备编译器，而不能只看宿主 Rust 是否能接受语法。[编译器项目](https://github.com/NVlabs/cuda-oxide/tree/b9847e9515ed3a23096f22567d3eaf0a6e3e440c)。

**English:** cutile-rs captures a restricted Rust-shaped program through `#[cutile::module]` and expresses work in tiles. Its runtime compiles the tile representation for the GPU when the kernel is needed. The host crate building successfully verifies macro expansion and host-side types; it does not prove that a particular tile specialization has passed device JIT compilation or executed correctly. A tile's logical shape is also not a declaration of CUDA's physical block dimensions. [cuTile project](https://github.com/NVlabs/cutile-rs/tree/d92c160949f58328ba6e96d81005e7110ba6f2b3). First distinguish the units used to describe work, then discuss their mapping onto hardware.

**中文：** cutile-rs 通过 `#[cutile::module]` 捕获具有 Rust 外形的受限程序，以数据分块描述计算，并在运行时需要内核时为 GPU 编译相应表示。宿主包构建成功，只能验证宏展开和宿主侧类型，不能证明某种分块特化已经通过设备即时编译，更不能证明执行结果正确。一个分块的逻辑形状，也不是对 CUDA 物理线程块维度的直接声明。比较两种编程模型时，应先区分描述工作的单位，再讨论编译器如何映射到硬件。[cuTile 项目](https://github.com/NVlabs/cutile-rs/tree/d92c160949f58328ba6e96d81005e7110ba6f2b3)。

**English:** The shared mathematical operation is `output[i] = input[i] * scale + bias`. Keeping the arithmetic small makes the important differences visible: a raw Driver launch describes an ABI, the native Rust kernel describes individual element ownership, and the tile kernel describes a block of values. None is automatically faster. A defensible comparison must equalize input, precision, transfer accounting, warm-up, synchronization, and validation before interpreting timing differences. The examples in this course do not establish a performance ranking.

**中文：** 三种方案使用相同的数学操作：输出元素等于输入元素乘比例再加偏置。算术足够简单，才容易看见真正的差别：底层 Driver 启动描述参数二进制接口，原生 Rust 内核描述单个元素的访问责任，分块内核描述一组值的变换。任何方案都不会仅凭语言名称自动更快。要进行可信比较，必须先统一输入、精度、传输是否计时、预热、同步和结果校验，再解释时间差异；本课的示例不构成性能排名。

## The resource graph behind a launch / 启动背后的资源关系

**English:** A device ordinal selects a GPU visible to the process; a context establishes the Driver API execution environment for resources on that device. The reviewed cuda-core runtime retains the device's primary context. This differs from assuming that every wrapper creates a fresh independent context. Resource compatibility is determined by the actual context relationship, not merely by matching the integer device index printed in two parts of the application. [CUDA contexts](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__CTX.html). When mixing frameworks, first identify who creates or retains, binds, and releases the context before judging handle compatibility.

**中文：** 设备编号选择进程可见的一张 GPU，上下文则为该设备上的资源建立 Driver API 执行环境。本课审阅的 cuda-core 运行库保留并使用设备的主上下文，这与“每个封装都会创建一个全新独立上下文”的假设不同。资源能否一起使用，取决于实际上下文关系，而不是程序两个位置打印出来的设备编号恰好相同。与其他框架混合使用时，应首先识别谁创建或保留上下文、谁负责绑定和释放，再判断句柄是否兼容。[CUDA 上下文](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__CTX.html)。

**English:** A module owns loaded device code, and a function identifies an entry within that module. The reviewed runtime represents a function together with shared ownership of its module, and the module retains its context. This ownership chain keeps code and context handles alive while the function exists. It does not, by itself, keep every buffer passed to an asynchronous launch alive; code lifetime and data lifetime are separate obligations. [CUDA modules](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__MODULE.html). A shared pointer protecting a module does not prove that the whole launch is free of resource-release hazards.

**中文：** 模块拥有已经装入的设备代码，函数句柄标识模块中的一个入口。所审阅的运行库让函数持有模块的共享所有权，同时让模块保留上下文。这条所有权链能够在函数存在期间维持代码与上下文句柄的有效性，却不会自动维持异步启动所使用的所有缓冲区。代码生命周期和数据生命周期是两项独立义务。评审封装时，不能看到模块被共享指针保护，就推断整个调用已经没有资源释放风险。[CUDA 模块](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__MODULE.html)。

**English:** A stream orders submitted work, while a device buffer owns storage. In a simple single-stream path, input upload precedes the kernel and output download follows it. Work submitted to another stream requires an explicit dependency when it consumes the same data. Sharing an `Arc` establishes host ownership; it does not establish a device happens-before relation, and it does not prevent two kernels from concurrently writing the same address. [CUDA streams](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__STREAM.html). Drawing ownership and execution-dependency graphs separately often reveals omissions more clearly than a general thread-safety discussion.

**中文：** 流负责排列已提交工作的顺序，设备缓冲区负责拥有存储。在简单的单流路径中，输入上传位于内核之前，输出下载位于内核之后。如果另一条流要消费相同数据，就需要建立明确依赖。共享一个 `Arc` 建立的是宿主所有权关系，不是设备执行的先后关系，也不会阻止两个内核同时写入相同地址。把所有权图与执行依赖图分开绘制，通常比只讨论“线程安全”更容易发现遗漏。[CUDA 流](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__STREAM.html)。

**English:** Context binding also has a host-thread dimension. An async task may resume on a different executor thread after an await, so a cached assumption about the previously current context can become wrong. The reviewed wrapper binds the appropriate context for its operations; raw FFI code must honor the Driver API requirements itself. `Send` and `Sync` should follow a documented implementation argument, not the observation that an opaque handle fits in a machine word. [Rust Send and Sync](https://doc.rust-lang.org/nomicon/send-and-sync.html). Moving ownership between threads, permitting concurrent calls, and preventing conflicting device accesses are three distinct questions.

**中文：** 上下文绑定还涉及宿主线程。异步任务在等待后可能恢复到执行器的另一个线程，因此“之前已经设置过当前上下文”的缓存假设可能失效。本课审阅的封装会为相关操作绑定适当上下文，直接调用外部接口的代码则必须自行满足驱动要求。能否实现 `Send` 和 `Sync`，应由清楚的实现论证决定，而不是因为不透明句柄恰好能装进一个机器字。所有权可跨线程移动、操作可并发调用、设备访问无冲突，是三个不同问题。[Rust 的发送与共享约束](https://doc.rust-lang.org/nomicon/send-and-sync.html)。

**English:** Write the normal path as create context, load module, find function, allocate buffers, copy input, launch, wait, validate output, and release resources. Then inspect every early return. In particular, a launch error may occur after earlier copies were submitted. Cleanup must account for all outstanding work, not just whether the most recent API call returned an error. The examples explicitly attempt stream synchronization before propagating a launch result so that the completion boundary is visible to the reader. This also preserves an explicit cleanup opportunity on error paths.

**中文：** 正常路径可以写成建立上下文、加载模块、查找函数、分配缓冲区、复制输入、启动、等待、验证输出、释放资源。随后需要逐一检查提前返回路径。特别是，启动报错时，之前的复制操作可能已经提交，清理逻辑必须考虑全部尚未完成的工作，而不能只看最后一次接口调用是否失败。本课示例先尝试同步流，再传播启动结果，使读者能直接看见完成边界；这种写法也提醒你为错误路径保留必要的清理机会。

## ABI and memory obligations / 二进制接口与内存义务

**English:** A raw launch's parameter array contains host addresses of argument values. For a device pointer argument, one host variable stores the numeric device address, and the launch receives the address of that host variable. Passing the device address itself as a parameter-slot address confuses two levels of indirection. The host argument slots must survive the launch call, while the device allocations they describe must survive the later kernel execution. [CUDA execution control](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__EXEC.html). These lifetimes differ, so a single rule of releasing everything when the function returns cannot cover both.

**中文：** 底层启动接口的参数数组保存的是参数值在宿主内存中的地址。对于设备指针参数，一个宿主变量先保存设备地址的数值，启动接口再接收这个宿主变量的地址。如果把设备地址本身直接当成参数槽地址，就混淆了两层间接访问。宿主参数槽必须至少活到启动调用结束，而这些参数所描述的设备分配必须继续活到稍后的内核执行结束。两个生命周期长度不同，不能用同一条“函数返回后就释放”规则处理。[CUDA 执行控制](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__EXEC.html)。

**English:** The ABI must agree on order, width, alignment, and meaning. Our CUDA signature uses two pointers, an unsigned 32-bit count, and two 32-bit floats; the Rust side supplies those same representations. A `usize` is convenient for host indexing but is not an interchangeable spelling of every C integer. Convert deliberately, reject an unrepresentable length, and compute byte sizes with checked multiplication before allocating or copying. Similar-looking type names cannot replace checking the cross-language signature field by field.

**中文：** 二进制接口必须在参数顺序、宽度、对齐和含义上完全一致。本课 CUDA 签名包含两个指针、一个无符号三十二位长度和两个三十二位浮点数，Rust 侧必须提供对应表示。`usize` 适合宿主索引，却不是任意 C 整数的通用替代名称。应明确执行转换，拒绝无法表示的长度，并在分配或复制之前用受检查的乘法计算字节数。类型名称看起来相近，并不能代替跨语言接口的逐字段核对。

**English:** `#[repr(C)]` requests a layout compatible with the corresponding C representation; it does not make a value meaningful on a GPU. A structure containing a `Vec`, `String`, or reference still carries host allocation or lifetime assumptions. Even plain bytes require attention to padding, initialization, and valid bit patterns. A device-copy trait can centralize those assumptions, but an unsafe implementation of that trait is a proof obligation rather than a serialization mechanism. [Rust layout](https://doc.rust-lang.org/reference/type-layout.html), [FFI](https://doc.rust-lang.org/nomicon/ffi.html). Start with clear fixed-width scalars and separate buffers in the initial interface.

**中文：** `#[repr(C)]` 请求与相应 C 表示兼容的布局，却不会让一个值自然获得设备端含义。含有 `Vec`、`String` 或引用的结构体，仍然携带宿主分配或生命周期假设。即使看起来只是普通字节，也要注意填充、初始化以及位模式是否合法。设备可复制类型约束可以集中表达这些假设，但为该约束编写不安全实现，是新增一项需要证明的责任，而不是自动序列化机制。最初的接口应优先使用清楚的固定宽度标量与独立缓冲区。[Rust 布局](https://doc.rust-lang.org/reference/type-layout.html)、[外部函数接口](https://doc.rust-lang.org/nomicon/ffi.html)。

**English:** Module format and execution architecture are additional compatibility dimensions. PTX is a virtual instruction representation that the driver can compile for a device; cubin already contains device machine code for a target. A successful nvcc PTX build verifies its source compilation, but module loading can still fail because of a driver, PTX version, target, or symbol mismatch. Record the exact artifact and toolchain before diagnosing such a failure as a Rust ownership problem. Record compilation, loading, entry lookup, submission, and completion as separate stages.

**中文：** 模块格式与执行架构是另外两项兼容维度。PTX 是驱动可以继续为设备编译的虚拟指令表示，cubin 则已经包含针对目标生成的设备机器码。nvcc 成功产生 PTX，只验证了源代码编译；模块加载仍可能因为驱动、PTX 版本、目标架构或符号不匹配而失败。遇到问题时，应先记录具体产物和工具链，再定位失败阶段，而不要把所有加载失败都归因于 Rust 所有权。编译、加载、查找入口、启动和完成应分别记录。

## Safe interfaces across asynchronous work / 跨异步工作的安全接口

**English:** The Rust borrow checker follows relationships represented in Rust types. A raw device address is just a value from its perspective; a kernel submitted through FFI does not automatically extend a borrow until an event completes. A sound safe wrapper must encode that extension, keep ownership internally, or wait before returning control in a way that permits reuse. An `unsafe` block marks where this reasoning is required; it does not make the reasoning true. An interface review should state invariants rather than merely check that unsafe code is hidden inside a small function.

**中文：** Rust 借用检查器跟踪的是类型中表达出来的关系。对于它而言，一个原始设备地址只是某个值；经由外部接口提交内核，不会自动把借用延长到设备事件完成。可靠的安全封装必须编码这种延长关系、在内部持有所有权，或者在允许调用方重用数据之前完成等待。`unsafe` 代码块只标记需要承担这项论证的位置，并不会让论证自动成立。因此，接口评审需要写出不变量，而不能仅检查不安全代码是否被包在一个很小的函数中。

**English:** A useful launch contract names the device and context, shapes, element types, permitted aliases, launch geometry, stream dependencies, and lifetime end condition. For an elementwise output, each valid index must have one writer, every read must fall within its input, and trailing launched threads must do nothing. Equal buffer lengths are necessary for our kernel but are not enough if another outstanding kernel can write the input at the same time. The contract has both spatial and temporal dimensions.

**中文：** 有用的启动契约应明确设备与上下文、形状、元素类型、允许的别名、启动几何、流之间的依赖，以及生命周期的结束条件。对于逐元素输出，每个有效索引必须只有一个写入者，每次读取都必须位于输入范围内，多启动的尾部线程必须不做任何访问。本课内核要求输入输出长度相同，但如果另一个尚未结束的内核同时改写输入，仅有长度一致仍然不够。契约既包含空间范围，也包含时间范围。

**English:** An owned asynchronous operation can retain its input and output allocations until completion, then return them together with the result. This is easier to reason about than returning immediately while borrowing arbitrary caller memory. The reviewed cuTile API uses operations and synchronization helpers that express such sequencing. Nevertheless, an API's name alone does not establish its cancellation behavior; inspect what happens when a future is dropped, the executor stops, or an error occurs after submission. Cancelling a host task neither proves device execution has stopped nor immediately permits reclaiming its memory.

**中文：** 拥有资源的异步操作可以一直保留输入和输出分配，完成后再把这些资源与结果一起返回。这通常比立即返回、同时借用调用方任意内存更容易推理。本课使用的 cuTile 接口通过操作对象和同步辅助方法表达执行顺序。不过，接口名称本身并不能证明取消行为正确；还需要检查 Future 被丢弃、执行器停止，或提交后发生错误时的处理。宿主任务被取消，不等于设备已经停止执行，也不等于其访问的内存可以立即回收。

**English:** A borrowed guard whose destructor waits is not automatically a sound design. Safe Rust can call `mem::forget`, so destructors are not guaranteed to execute. If forgetting the guard allows a borrowed buffer to be reused while the GPU still accesses it, the abstraction is unsound. An owned guard may instead leak its owned allocation when forgotten, which can preserve memory safety at the cost of a leak. The full interface must remain safe under forgetting, not merely under ordinary scope exit. [Destructor limitations](https://doc.rust-lang.org/nomicon/destructors.html).

**中文：** “借用一个缓冲区，再让守卫的析构函数负责等待”并不自动构成可靠设计。安全 Rust 可以调用 `mem::forget`，因此析构函数不能保证执行。如果遗忘守卫之后，借用缓冲区就能被重新使用，而 GPU 仍在访问它，整个抽象便不可靠。拥有分配所有权的守卫被遗忘时，可以把资源一并泄漏，以内存泄漏的代价维持内存安全。完整接口必须在对象被遗忘时依然安全，而不能只在正常离开作用域时成立。[析构函数的限制](https://doc.rust-lang.org/nomicon/destructors.html)。

**English:** Likewise, zero-copy language claims require precision. Avoiding a Rust clone is different from avoiding a host-to-device transfer, and sharing an `Arc<DeviceBuffer<_>>` is different from permitting shared mutation. Page-locked host memory, unified memory, and explicit device memory have distinct access and synchronization rules. This course uses explicit allocations and clearly visible copies so that a learner can audit the execution path before adopting more implicit memory policies. A timeline and measurements should identify which transfer or wait an optimization actually removes.

**中文：** 关于零复制的说法也必须精确。避免一次 Rust 克隆，不等于避免一次宿主到设备的传输；共享 `Arc<DeviceBuffer<_>>`，也不等于允许共享修改。页锁定宿主内存、统一内存和显式设备内存，分别有不同的访问与同步规则。本课优先使用明确的设备分配和可见的复制操作，目的是让学习者先能审计执行路径，再采用更加隐式的内存策略。优化减少的是哪一次传输或哪一段等待，应能够用时间线和测量说明。

## CPU laboratory: shape and ownership contracts / CPU 实验：形状与所有权契约

**English:** The first laboratory needs only a working stable Rust compiler. It checks equal lengths, nonzero launch width, a bounded block width, integer conversion, and byte-size overflow, then exercises an operation that owns its input. This is a CPU model of selected interface obligations. It neither compiles a Rust GPU kernel nor proves CUDA execution safety, but it lets us test host validation even while the GPU driver is unavailable. This avoids postponing independently detectable errors until an expensive device run.

**中文：** 第一个实验只需要可用的稳定版 Rust 编译器。它检查长度一致、启动宽度非零、线程块宽度上限、整数转换以及字节大小溢出，然后执行一个拥有输入所有权的操作。这只是对部分接口义务建立的 CPU 模型，既没有编译 Rust GPU 内核，也不能证明 CUDA 执行安全。但即使 GPU 驱动当前不可用，我们仍然可以验证宿主参数检查，避免把本来能独立发现的错误留到昂贵的设备运行阶段。

```bash
COURSE07_CPU_DIR=$(mktemp -d /tmp/course07-cpu-XXXXXX)
export COURSE07_CPU_DIR
cat > "$COURSE07_CPU_DIR/contracts.rs" <<'RS'
use std::mem::size_of;

#[derive(Debug, PartialEq)]
struct Shape { n: u32, blocks: u32, bytes: usize }

fn byte_len(n: usize) -> Result<usize, &'static str> {
    n.checked_mul(size_of::<f32>()).ok_or("byte overflow")
}
fn plan(input: usize, output: usize, block: u32) -> Result<Shape, &'static str> {
    if input != output { return Err("shape mismatch"); }
    if block == 0 || block > 1024 { return Err("invalid block width"); }
    let n = u32::try_from(input).map_err(|_| "count overflow")?;
    Ok(Shape { n, blocks: n.div_ceil(block), bytes: byte_len(input)? })
}
struct OwnedCpuJob { input: Vec<f32>, scale: f32, bias: f32 }
impl OwnedCpuJob {
    fn finish(self) -> Vec<f32> {
        self.input.into_iter().map(|x| x * self.scale + self.bias).collect()
    }
}
fn main() {
    for n in [0_usize, 1, 33, 256, 257, 1003] {
        let shape = plan(n, n, 256).unwrap();
        assert_eq!(shape.bytes, n * size_of::<f32>());
        assert_eq!(shape.blocks as usize, n.div_ceil(256));
        let job = OwnedCpuJob {
            input: (0..n).map(|i| i as f32 * 0.25).collect(),
            scale: 1.5, bias: 2.0,
        };
        let result = job.finish();
        for (i, actual) in result.iter().copied().enumerate() {
            assert_eq!(actual, i as f32 * 0.25 * 1.5 + 2.0);
        }
    }
    assert_eq!(plan(7, 8, 256), Err("shape mismatch"));
    assert_eq!(plan(7, 7, 0), Err("invalid block width"));
    assert_eq!(plan(7, 7, 1025), Err("invalid block width"));
    assert_eq!(byte_len(usize::MAX), Err("byte overflow"));
    if usize::BITS > 32 {
        assert_eq!(plan(u32::MAX as usize + 1, u32::MAX as usize + 1, 256),
                   Err("count overflow"));
    }
    println!("CPU contracts: six shapes and five rejection cases passed");
}
RS
cat > "$COURSE07_CPU_DIR/borrow_failure.rs" <<'RS'
fn main() {
    let mut values = vec![1_f32, 2.0];
    let pending = &mut values;
    let conflicting = &mut values;
    println!("{} {}", pending.len(), conflicting.len());
}
RS
python3 - <<'PY'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_CPU_DIR"])
subprocess.run(["rustc", "--edition=2021", str(root / "contracts.rs"),
                "-o", str(root / "contracts")], check=True)
subprocess.run([str(root / "contracts")], check=True)
failure = subprocess.run(["rustc", "--edition=2021", str(root / "borrow_failure.rs"),
                          "-o", str(root / "borrow_failure")], capture_output=True, text=True)
assert failure.returncode != 0 and "E0499" in failure.stderr, failure.stderr
print("Expected borrow failure: E0499")
print("Artifacts:", root)
PY
```

**English:** The empty shape yields zero blocks and no elements to compute. The CPU planner accepts that as a valid empty operation, but a GPU wrapper must skip the launch instead of submitting a zero-sized grid. The upper block limit in this exercise is a deliberate host contract, not a substitute for querying all device and function-specific limits. A parameter checker should make its assumptions explicit rather than claim universal hardware validity. Distinguishing empty input from invalid launch geometry gives callers consistent empty-operation behavior.

**中文：** 空形状得到零个线程块，也没有需要计算的元素。CPU 规划器把它视为合法的空操作，但 GPU 封装必须跳过启动，而不能提交维度为零的网格。实验中的线程块宽度上限，是特意写入宿主契约的限制，不能代替设备与具体函数的全部限制查询。参数检查器应清楚说明自己的假设，而不是宣称它已经证明适用于所有硬件。这里把“输入为空”与“启动参数非法”分开，能让调用方获得一致的空输入行为。

**English:** The failing example keeps the first mutable borrow live by using it after the second borrow. That is why non-lexical lifetimes cannot simply shorten it away. Now imagine replacing the first borrow with a copied raw device pointer: the compiler loses that relationship and may accept later host code. This contrast identifies the work a GPU wrapper must perform. It does not mean Rust is ineffective; it means the device relationship must first be represented in the abstraction. Keep the expected compiler error identifier so that an unrelated compilation failure cannot masquerade as the intended protection.

**中文：** 失败示例在第二次借用之后继续使用第一次可变借用，因此非词法生命周期不能把它简单缩短掉。现在设想把第一次借用换成一个复制出来的原始设备指针：编译器便失去了这层关系，可能接受后续宿主代码。这个对照指出了 GPU 封装必须补充的工作。它并不意味着 Rust 的约束没有作用，而是说明设备执行关系首先需要被准确地表达进抽象。编译失败实验应保留明确的错误编号，防止把其他编译错误误认成预期保护。

## Reproducible source workspaces / 可复现源码工作区

**English:** The following preparation creates two temporary checkouts and verifies their exact revisions. Keeping the repositories separate preserves their own lockfiles and runtime versions. `CUDA_TOOLKIT_PATH` identifies the Toolkit used by these projects; it is not a driver repair setting. Before reproducing the builds, verify that the path contains the intended nvcc and that the required Rust toolchains are installed. The pinned cuda-oxide revision also documents LLVM/Clang 21 requirements and CUDA development headers. Do not bypass build errors by casually updating a lockfile, because the resulting dependency combination would differ from the one checked here.

**中文：** 以下准备步骤建立两个临时检出目录，并核对精确提交。保持仓库独立，可以保留各自的锁文件与运行库版本。`CUDA_TOOLKIT_PATH` 指定这些项目使用的工具包，不是修复驱动的设置。复现编译前，应确认该路径包含预期的 nvcc，并且相应 Rust 工具链已经安装。固定的 cuda-oxide 版本还说明了 LLVM 与 Clang 二十一及 CUDA 开发头文件要求。不要通过随意更新锁文件来绕过构建错误，否则后续结果就不再对应本课核验过的依赖组合。

```bash
COURSE07_WORK=$(mktemp -d /tmp/course07-work-XXXXXX)
export COURSE07_WORK
export CUDA_TOOLKIT_PATH=/usr/local/cuda
python3 - <<'PY'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_WORK"])
repos = {
    "cuda-oxide": "b9847e9515ed3a23096f22567d3eaf0a6e3e440c",
    "cutile-rs": "d92c160949f58328ba6e96d81005e7110ba6f2b3",
}
for name, revision in repos.items():
    path = root / name
    subprocess.run(["git", "clone", "https://github.com/NVlabs/" + name + ".git", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "checkout", "--detach", revision], check=True)
    actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    assert actual == revision
print("Workspaces:", root)
PY
```

**English:** The examples below write only into those temporary checkouts. The existing example packages provide the tested manifests and lockfiles, so the lesson does not invent an independent dependency combination. Stable 1.98.1 builds the cutile-rs host examples. The native path uses the exact nightly from cuda-oxide, not whatever `rustc` happens to be on the shell's default path. Compiler-internal backends are particularly sensitive to that distinction. Record full compiler version and commit information rather than saying only that the latest Rust was used.

**中文：** 下列示例只写入这些临时检出目录。现有示例包提供已核验的清单和锁文件，因此课程不另行拼凑一套依赖组合。稳定版一点九八点一用于构建 cutile-rs 的宿主示例；原生路径则使用 cuda-oxide 指定的精确 nightly，而不是当前命令行默认碰巧找到的 `rustc`。依赖编译器内部接口的后端尤其敏感于这种差别。记录工具链时，应保存完整版本与提交信息，而不能只写“使用最新版 Rust”。

## Laboratory: Rust host and CUDA PTX / 实验：Rust 宿主与 CUDA PTX

**English:** This complete program deliberately keeps the kernel in CUDA C++. The C entry name is stable, the count is explicitly 32-bit, and excess threads return without writing. The Rust program owns allocations and builds the raw parameter slots. Observe that neither `extern "C"` nor the Driver API checks the semantic agreement between the Rust slot array and the kernel declaration; maintaining that agreement is the responsibility of this small unsafe boundary. Concentrating this boundary lets reviewers inspect each signature and resource condition rather than hide the boundary.

**中文：** 这个完整程序特意把内核保留为 CUDA C++。入口使用稳定的 C 名称，长度明确为三十二位，多余线程不执行写入。Rust 程序拥有设备分配，并构建底层参数槽。请注意，`extern "C"` 和 Driver API 都不会替你检查 Rust 参数数组与内核声明之间的语义一致性；维持这种一致性，是这段小范围不安全边界的责任。将边界集中起来的意义，是让审阅者能够逐项验证签名与资源条件，而不是隐藏它的存在。

```bash
cat > "$COURSE07_WORK/affine.cu" <<'CU'
extern "C" __global__ void course07_affine(
    const float* input, float* output, unsigned int n, float scale, float bias) {
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) output[i] = input[i] * scale + bias;
}
CU
cat > "$COURSE07_WORK/cutile-rs/cutile-examples/examples/course07_driver.rs" <<'RS'
use cuda_core::{launch_kernel_on_stream, CudaContext, DeviceBuffer};
use std::ffi::c_void;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let context = CudaContext::new(0)?;
    let stream = context.default_stream();
    let module = context.load_module_from_ptx_src(include_str!(env!("COURSE07_PTX")))?;
    let function = module.load_function("course07_affine")?;
    let n = 1003_u32;
    let source: Vec<f32> = (0..n).map(|i| i as f32 * 0.25).collect();
    let input = DeviceBuffer::from_host(&stream, &source)?;
    let output = DeviceBuffer::<f32>::zeroed(&stream, n as usize)?;
    let mut input_pointer = input.cu_deviceptr();
    let mut output_pointer = output.cu_deviceptr();
    let mut count = n;
    let mut scale = 1.5_f32;
    let mut bias = 2.0_f32;
    let mut arguments = [
        (&mut input_pointer as *mut _ as *mut c_void),
        (&mut output_pointer as *mut _ as *mut c_void),
        (&mut count as *mut _ as *mut c_void),
        (&mut scale as *mut _ as *mut c_void),
        (&mut bias as *mut _ as *mut c_void),
    ];
    // SAFETY: slots match the fixed PTX signature; buffers are independent,
    // each holds n floats, and all owners survive same-stream completion.
    let submitted = unsafe {
        launch_kernel_on_stream(&function, (n.div_ceil(256), 1, 1), (256, 1, 1),
                                0, &stream, &mut arguments)
    };
    let completed = stream.synchronize();
    submitted?;
    completed?;
    let values = output.to_host_vec(&stream)?;
    for (index, actual) in values.iter().copied().enumerate() {
        let expected = source[index] * scale + bias;
        assert!(actual.is_finite() && (actual - expected).abs() <= 1e-5);
    }
    println!("Driver API affine: validated {} values", values.len());
    Ok(())
}
RS
python3 - <<'PY'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_WORK"])
ptx = root / "affine.ptx"
subprocess.run([str(pathlib.Path(os.environ["CUDA_TOOLKIT_PATH"]) / "bin/nvcc"),
                "-ptx", "-std=c++17", "-arch=compute_89", str(root / "affine.cu"),
                "-o", str(ptx)], check=True)
env = dict(os.environ, COURSE07_PTX=str(ptx))
subprocess.run(["cargo", "+1.98.1", "build", "--locked", "-p", "cutile-examples",
                "--example", "course07_driver"], cwd=root / "cutile-rs", env=env, check=True)
print("PTX and host binary compiled; no GPU execution requested")
PY
```

**English:** The stream synchronization is explicit even though this runtime's `to_host_vec` also waits for its copy to finish. The first wait establishes a clear kernel completion boundary and exposes asynchronous failures before inspecting results. The finite-value check matters: a comparison that only asks whether an absolute error is greater than a tolerance may accidentally accept NaN. Correctness evidence must include shape, initialization, completion, and numerical checks. Positive inputs, scale, and bias also prevent an unwritten zero from accidentally matching the expected result.

**中文：** 虽然当前运行库的 `to_host_vec` 也会等待复制完成，示例仍显式同步流。前一次等待建立清楚的内核完成边界，并在检查结果前暴露异步错误。有限值检查同样必要：如果验证器只判断绝对误差是否大于阈值，就可能意外接受非数值。正确性证据应同时包含形状、初始化、执行完成和数值检查。示例选择正的输入、比例与偏置，也避免把未执行写入后残留的零误认为正确结果。

**English:** On a healthy GPU environment, execute the built example from its checkout with the same `COURSE07_PTX` environment variable and `cargo +1.98.1 run --locked -p cutile-examples --example course07_driver`. Expected success is validation of 1003 values, not merely process creation. This command is intentionally separate from compilation because this session's driver mismatch blocks device validation. A module-load failure belongs to a different stage from an incorrect output value. A report should not collapse these distinct stages into an unspecified failure to run the example.

**中文：** 在 GPU 环境正常的机器上，可从该检出目录使用同一个 `COURSE07_PTX` 环境变量，通过 `cargo +1.98.1 run --locked -p cutile-examples --example course07_driver` 执行产物。预期成功条件是完成一千零三个元素的验证，而不只是进程被创建。执行命令与编译有意分开，因为本次驱动版本不一致阻断了设备验证。模块加载失败与输出数值错误处于不同阶段，记录实验时不能把二者合并成一句笼统的“示例跑不起来”。

## Laboratory: native Rust SIMT with cuda-oxide / 实验：cuda-oxide 原生 Rust 线程模型

**English:** The native example reuses cuda-oxide's standalone `vecadd` example package but replaces its source with an affine kernel. This keeps the package's local device and host crates aligned with the checked-out compiler backend. The filename is an existing build fixture, not a claim that affine transformation is vector addition. The public arithmetic interface has one immutable input, one disjoint output, and two scalar parameters, which makes its safety obligations small enough to inspect. The course deliberately avoids adding reductions, shared memory, and complex tensor layouts at the same time, which would obscure the language boundary.

**中文：** 原生示例复用 cuda-oxide 独立的 `vecadd` 示例包，把其中源码替换为仿射内核。这样可以让本地设备库、宿主库和检出的编译后端保持一致。沿用现有包名只是为了复用构建设施，并不表示仿射变换就是向量加法。公开算术接口包含一个不可变输入、一个可分离写入的输出，以及两个标量参数，因此安全义务足够小，可以逐项检查。课程刻意避免同时加入归约、共享内存和复杂张量布局，以免掩盖语言边界的问题。

**English:** `thread::index_1d()` returns a typed index token; `DisjointSlice` uses that token to constrain mutable element access. When the index lies outside the output, `get_mut` returns `None`, so trailing threads perform no input read either. Equal input and output lengths make a valid output index a valid input index. The host must still uphold the one-dimensional launch and independence assumptions; an extra grid dimension could repeat the same one-dimensional index across different threads. Device-side types express local constraints, while the raw host launch must still establish their prerequisites.

**中文：** `thread::index_1d()` 返回带类型的索引令牌，`DisjointSlice` 使用令牌约束可变元素访问。索引超过输出范围时，`get_mut` 返回 `None`，所以尾部线程连输入读取都不会执行。输入输出长度一致，使有效输出索引同时也是有效输入索引。宿主仍必须满足一维启动和访问独立性的假设；如果额外增加网格维度，不同线程可能重复得到同一个一维索引。设备侧的类型设计能够表达局部约束，但原始启动边界仍要确保这些约束成立。

```bash
cat > "$COURSE07_WORK/cuda-oxide/crates/rustc-codegen-cuda/examples/vecadd/src/main.rs" <<'RS'
use cuda_core::simt::LaunchConfig;
use cuda_core::{CudaContext, DeviceBuffer};
use cuda_device::{cuda_module, kernel, thread, DisjointSlice};

#[cuda_module]
mod kernels {
    use super::*;
    #[kernel]
    pub fn affine(input: &[f32], mut output: DisjointSlice<f32>, scale: f32, bias: f32) {
        let index = thread::index_1d();
        let offset = index.get();
        if let Some(element) = output.get_mut(index) {
            *element = input[offset] * scale + bias;
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let context = CudaContext::new(0)?;
    let stream = context.default_stream();
    let module = kernels::load(&context)?;
    for n in [1_usize, 33, 257, 1003] {
        let source: Vec<f32> = (0..n).map(|i| i as f32 * 0.25).collect();
        let input = DeviceBuffer::from_host(&stream, &source)?;
        let mut output = DeviceBuffer::<f32>::zeroed(&stream, n)?;
        let count = u32::try_from(n)?;
        // SAFETY: a one-dimensional launch gives each output one writer;
        // equal lengths cover every read, and all owners survive completion.
        let submitted = unsafe {
            module.affine(&stream, LaunchConfig::for_num_elems(count),
                          &input, &mut output, 1.5_f32, 2.0_f32)
        };
        let completed = stream.synchronize();
        submitted?;
        completed?;
        let values = output.to_host_vec(&stream)?;
        for (index, actual) in values.iter().copied().enumerate() {
            let expected = source[index] * 1.5 + 2.0;
            assert!(actual.is_finite() && (actual - expected).abs() <= 1e-5);
        }
        println!("cuda-oxide affine: validated {n} values");
    }
    Ok(())
}
RS
python3 - <<'PY'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_WORK"]) / "cuda-oxide"
subprocess.run(["cargo", "+nightly-2026-08-28", "oxide", "build", "vecadd",
                "--arch", "sm_89"], cwd=root, check=True)
print("Native build finished; GPU execution is a separate step")
PY
```

**English:** The toolchain must exist before that build. A reproducible optional installation is `rustup toolchain install nightly-2026-08-28 --profile minimal --component rust-src,rustc-dev,llvm-tools`; an isolated `RUSTUP_HOME` can keep it separate from everyday work. The compiler backend and its dependencies consume significant disk space. In this session, the pinned nightly installed successfully, but backend compilation stopped with `Disk quota exceeded`; therefore this native kernel is source-reviewed, not successfully compiled or GPU-tested here. Starting a build must not be reported as successfully completing its validation.

**中文：** 执行构建前，必须已经安装对应工具链。可复现的可选安装命令为 `rustup toolchain install nightly-2026-08-28 --profile minimal --component rust-src,rustc-dev,llvm-tools`，也可以使用独立的 `RUSTUP_HOME` 与日常环境隔离。编译后端及其依赖需要较多磁盘空间。本次指定 nightly 安装成功，但后端编译因 `Disk quota exceeded` 中断，因此这里的原生内核状态是已审阅源码，尚未成功完成编译，也没有经过 GPU 实测。不能把已经开始构建写成已经验证通过。

**English:** When the build succeeds on a suitable machine, `cargo +nightly-2026-08-28 oxide run vecadd --arch sm_89` executes the same example. Expected output validates lengths 1, 33, 257, and 1003. These sizes probe a single element, a partial warp-sized region, a block boundary, and a non-aligned tail. They do not cover every shape or architecture. Add an empty-input host branch before extending the public API to zero elements. Do not pass zero elements into a launch-configuration helper without checking its contract.

**中文：** 在具备条件的机器上构建成功后，可以执行 `cargo +nightly-2026-08-28 oxide run vecadd --arch sm_89` 运行同一个示例。预期依次验证长度为一、三十三、二百五十七和一千零三的数据。这些尺寸覆盖单元素、跨越常见线程束边界、跨线程块边界和不对齐尾部，但并不覆盖全部形状或架构。若要把公开接口扩展到零元素，应先在宿主增加空输入分支，而不是未经检查地将零长度传入启动配置生成函数。

**English:** cuda-oxide also provides launch-contract and prepared-launch facilities in the reviewed revision. Such facilities can move some checks into generated interfaces and reduce what each caller must prove. They are valuable precisely when their documented contract matches the kernel. They should not be presented as eliminating every unsafe concern: external memory, context compatibility, unsupported aliasing, and operations on other streams still require a coherent whole-program argument. First understand the explicit unsafe call here, then examine how generated safe interfaces cover those obligations.

**中文：** 所核验的 cuda-oxide 版本还提供启动契约和预备启动设施，可以把部分检查移入生成接口，减少每个调用者需要重复证明的条件。当文档中的契约确实匹配内核时，这些设施很有价值。但不能把它们描述成消除了所有不安全问题：外部内存、上下文兼容性、未支持的别名形式，以及其他流上的操作，仍需要完整一致的论证。学习时先读懂本课显式的不安全调用，再研究生成的安全接口如何覆盖这些义务，会更容易判断其边界。

## Laboratory: a tile transformation with cutile-rs / 实验：cutile-rs 分块变换

**English:** The tile example expresses the same affine equation over logical blocks of 128 elements. The input contains 1024 values, so every block is full. This deliberately avoids making an unsupported claim about arbitrary tail behavior. The pinned project's support matrix lists the sm8x family with CUDA 13.2 or later; the local Ada GPU and 13.3 Toolkit meet that documented architecture/toolkit pair, while the current driver mismatch still blocks execution. [Pinned requirements](https://github.com/NVlabs/cutile-rs/blob/d92c160949f58328ba6e96d81005e7110ba6f2b3/README.md). Being listed as supported hardware and successfully running on this particular machine today are different facts.

**中文：** 分块示例在每块一百二十八个元素的逻辑块上表达相同仿射公式。输入包含一千零二十四个值，因此每块都完整，刻意避免对任意尾部处理作出未经验证的承诺。固定项目版本的支持表列出 sm8x 系列需要 CUDA 十三点二或更高版本；本机 Ada 显卡与十三点三工具包符合该架构和工具包组合，但当前驱动版本冲突依然阻断执行。硬件被列入支持范围，与这台机器今天能成功运行，是两个不同层次的事实。[固定版本要求](https://github.com/NVlabs/cutile-rs/blob/d92c160949f58328ba6e96d81005e7110ba6f2b3/README.md)。

**English:** `partition([128])` associates the output with a tile shape. Inside the captured kernel, `load_like(output)` selects the corresponding input values, scalar broadcast creates shape-compatible factors and offsets, and `store` writes the transformed tile. The programmer does not calculate `blockIdx.x * blockDim.x + threadIdx.x`. That responsibility moves to the tile compiler's mapping, but bounds, layout, supported operations, and resulting resource usage remain real constraints. Reducing explicit indexing code can eliminate some mistakes but cannot replace validation of compilation and execution.

**中文：** `partition([128])` 为输出关联一个分块形状。在被捕获的内核中，`load_like(output)` 选择对应输入值，标量广播产生形状兼容的比例与偏置，`store` 写出变换后的分块。程序员不再亲自计算线程块编号乘线程块宽度再加线程编号。这项责任转移到分块编译器的映射过程中，但范围、布局、受支持操作以及最终资源使用仍是实际约束。减少显式索引代码能够降低某类错误，却不能代替对编译结果和执行行为的验证。

```bash
cat > "$COURSE07_WORK/cutile-rs/cutile-examples/examples/course07_affine.rs" <<'RS'
use cutile::prelude::*;

#[cutile::module]
mod kernels {
    use cutile::core::*;
    #[cutile::entry()]
    fn affine<const B: i32>(
        output: &mut Tensor<f32, { [B] }>,
        input: &Tensor<f32, { [-1] }>,
        scale: f32,
        bias: f32,
    ) {
        let values = input.load_like(output);
        let factors = scale.broadcast(output.shape());
        let offsets = bias.broadcast(output.shape());
        output.store(values * factors + offsets);
    }
}

fn main() -> Result<(), Error> {
    let input = api::arange::<f32>(1024);
    let output = api::zeros::<f32>(&[1024]).partition([128]);
    let (output, _input, _scale, _bias) =
        kernels::affine(output, input, 1.5_f32, 2.0_f32).sync()?;
    let values = output.unpartition().to_host_vec().sync()?;
    for (index, actual) in values.iter().copied().enumerate() {
        let expected = index as f32 * 1.5 + 2.0;
        assert!(actual.is_finite() && (actual - expected).abs() <= 1e-5);
    }
    println!("cutile affine: validated {} values", values.len());
    Ok(())
}
RS
python3 - <<'PY'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_WORK"]) / "cutile-rs"
subprocess.run(["cargo", "+1.98.1", "build", "--locked", "-p", "cutile-examples",
                "--example", "course07_affine"], cwd=root, check=True)
print("cuTile host binary compiled; device JIT and execution are unverified")
PY
```

**English:** The operation returns its runtime arguments after `.sync()` completes, including the output that was moved into it. This visibly connects ownership transfer with completion. `unpartition()` changes the host-side view before downloading; it does not magically remove computation or transfer costs. A future async service may await an operation instead, but should preserve the same lifetime and ordering argument and should document its cancellation and shutdown behavior. Do not return a buffer to its reuse pool early merely to make a request handler return sooner.

**中文：** 操作在 `.sync()` 完成后返回运行时参数，其中包括先前移动进去的输出。这种写法把所有权转移与完成事件明确关联起来。下载前的 `unpartition()` 改变宿主侧视图，并不会神奇地消除计算或传输开销。将来接入异步服务时，可以等待操作对象，但仍需要保留同样的生命周期与顺序论证，并记录取消和停机行为。不能为了让请求处理函数更快返回，就提前允许缓冲区回到复用池。

**English:** On a healthy environment, `cargo +1.98.1 run --locked -p cutile-examples --example course07_affine` triggers the runtime work, including the device compilation path when required. Expected success validates 1024 values. The first run may include compilation and initialization, so its latency cannot be reported as steady-state kernel time. The stable host toolchain requirement also does not imply that every Rust expression is supported inside the captured tile language. Locate unsupported syntax or operations in that language subset rather than immediately blaming the stable host compiler.

**中文：** 在环境正常的机器上，`cargo +1.98.1 run --locked -p cutile-examples --example course07_affine` 会触发实际运行工作，其中包括需要时执行的设备编译路径。预期成功条件是验证一千零二十四个值。第一次运行可能包含编译和初始化，因此它的延迟不能被报告为稳定状态的内核时间。宿主使用稳定版工具链，也不意味着捕获的分块语言支持所有 Rust 表达式。遇到语法或操作限制时，应定位到该语言子集，而不要直接推断稳定版编译器出了问题。

## GPU execution entry points / GPU 执行入口

**English:** Run this block only after the corresponding builds succeed and the driver environment is healthy. It supplies the PTX path and checkout directories explicitly, then runs all three examples with checked exit status. These are reproduction commands, not a record of commands executed in this session. A failing step stops the sequence so that later output cannot hide the first failure. Preserve each example's validation output and leave unreached steps marked unverified.

**中文：** 只有在相应构建成功且驱动环境正常后，才执行以下代码块。它明确提供 PTX 路径和检出目录，然后检查退出状态，依次运行三个示例。这些是复现命令，不是本次已经执行的命令记录。任何一步失败都会停止后续执行，避免后面的输出掩盖最初失败。应保存每个示例的验证输出，并将没有执行到的步骤继续标为未验证。

```bash
python3 - <<'PYRUN'
import os, pathlib, subprocess
root = pathlib.Path(os.environ["COURSE07_WORK"])
env = dict(os.environ, COURSE07_PTX=str(root / "affine.ptx"))
subprocess.run(["cargo", "+1.98.1", "run", "--locked", "-p", "cutile-examples",
                "--example", "course07_driver"], cwd=root / "cutile-rs", env=env, check=True)
subprocess.run(["cargo", "+nightly-2026-08-28", "oxide", "run", "vecadd",
                "--arch", "sm_89"], cwd=root / "cuda-oxide", check=True)
subprocess.run(["cargo", "+1.98.1", "run", "--locked", "-p", "cutile-examples",
                "--example", "course07_affine"], cwd=root / "cutile-rs", check=True)
PYRUN
```

## Failure analysis and engineering choices / 失败分析与工程选择

**English:** Separate four failure families: host compilation, device compilation or module loading, submission, and asynchronous execution or validation. A missing Rust component belongs to the first family; an unsupported device operation may appear in the second; an invalid launch shape belongs to submission; an illegal access may surface only at synchronization. Preserve the first meaningful diagnostic together with the stage, revision, compiler, Toolkit, driver, and target architecture. This lets another engineer reproduce the same boundary before investigating the cause, instead of guessing from mixed final diagnostics.

**中文：** 应把失败分成四类：宿主编译、设备编译或模块加载、提交，以及异步执行或验证。缺失 Rust 组件属于第一类，不支持的设备操作可能出现在第二类，非法启动形状属于提交阶段，非法访问则可能直到同步才浮现。保留第一条有意义的诊断，同时记录阶段、提交、编译器、工具包、驱动和目标架构。这样的报告允许别人先复现同一个边界，再调查根因，而不必从混杂的末尾错误信息中反向猜测。

**English:** A deliberately mismatched shape is best rejected before launch. In the CPU laboratory, changing output length from seven to eight yields a predictable error without touching a GPU. By contrast, intentionally launching a kernel with a shorter input can cause a device fault and contaminate later observations. Host validation provides a cleaner negative test for that API rule; device sanitizers remain useful later for mistakes that escape those checks. State which protection the experiment checks rather than creating an unlocalized crash just to observe failure.

**中文：** 刻意制造的形状不一致，最好在启动前被拒绝。CPU 实验把输出长度从七改成八，就能得到可预测错误，无须接触 GPU。相反，故意让内核读取更短输入，可能造成设备错误，干扰后续观察。对于这条接口规则，宿主参数验证提供了更清楚的失败测试；设备检查工具仍可在后续用于发现逃过宿主检查的问题。实验应说明自己正在验证哪项保护，而不是为了看到崩溃而制造无法定位的异常。

**English:** Disk exhaustion is an infrastructure failure, not evidence that the native Rust kernel is rejected by its compiler. Conversely, having installed the required nightly does not establish that the backend or kernel built successfully. Record the build stop point and retain source and revision information. Reclaim only temporary artifacts owned by the experiment, then reproduce later with sufficient quota; do not silently switch compiler versions to obtain an unrelated green result. Reliable learning records preserve both successful evidence and the exact boundaries not yet completed.

**中文：** 磁盘配额耗尽属于基础环境失败，不能据此声称原生 Rust 内核被编译器拒绝。反过来，安装好了指定 nightly，也不能证明后端或内核已经编译成功。应记录构建停止的位置，保留源码与提交信息，只清理实验自己创建的临时产物，随后在配额足够时复现。不要悄悄切换编译器版本，只为得到一个与原固定环境无关的绿色结果。可靠学习记录既保存成功证据，也准确保存尚未完成的边界。

**English:** Project choice should follow the work being delivered. Host interoperation minimizes migration when proven CUDA kernels already exist. Native SIMT is a direct route for learning per-thread indexing and writing device logic in Rust. A tile language is attractive when the workload is naturally expressed in tensor blocks and supported operations. Since both reviewed projects describe evolving interfaces, keep a small reproduction fixture and allocate maintenance time rather than promising stable production integration from a single successful example. Learning the boundaries of both approaches is more useful than immediately migrating every component.

**中文：** 项目选择应跟随实际交付工作。如果已经有经过验证的 CUDA 内核，宿主互操作能够降低迁移成本；如果要学习线程索引并使用 Rust 编写设备逻辑，原生线程模型更直接；如果计算天然适合张量分块，且需要的操作已被支持，分块语言很有吸引力。所审阅的两个项目都处于接口持续演进阶段，因此应保留小型复现工程并预留维护时间，而不能仅凭一个示例成功就承诺稳定的生产集成。学习两者的边界，比立即迁移全部代码更有价值。

**English:** A service boundary adds queueing and ownership transfer to the kernel boundary. Give each submitted operation an identifier, retain its inputs until completion, and return buffers to a pool only after the matching completion condition. If a request times out, decide separately whether to abandon the response, stop submitting further work, or wait for already submitted work during cleanup. An HTTP timeout cannot revoke a device pointer already passed to a running kernel. Connecting this logic to existing server-development experience approaches real engineering more closely than practicing isolated launches alone.

**中文：** 服务边界在内核边界之外，又增加了排队和所有权转移。应给每个已提交操作分配标识，在完成前保留其输入，并且只有在对应完成条件成立后，才把缓冲区归还资源池。如果请求超时，需要分别决定放弃响应、停止继续提交，以及清理时如何等待已经提交的工作。一个 HTTP 超时无法撤销已经交给运行中内核的设备指针。把这段逻辑与已有服务端开发经验联系起来，比只练习单次启动更接近实际工程。

**English:** Performance investigation comes after correctness and phase classification. For a small affine transform, allocation, transfer, compilation, or synchronization can dominate arithmetic. Compare repeated launches over reused buffers separately from end-to-end request latency. Record whether compilation is warm, whether input is already resident, and which stream event bounds the measurement. Without those conditions, a timing improvement may describe omitted work rather than a better kernel or programming model. Later performance courses develop this measurement method further.

**中文：** 性能调查应放在正确性和阶段划分之后。对于小型仿射变换，分配、传输、编译或同步可能远远超过算术开销。应把复用缓冲区的重复启动，与完整请求延迟分开比较，记录编译是否已经预热、输入是否已经驻留设备，以及测量由哪个流事件划定边界。缺少这些条件时，时间减少可能只是少算了一部分工作，而不是内核或编程模型更优秀。课程后续的性能主题会继续发展这种测量方法。

## Ten exercises with worked answers / 十道练习与参考解答

### 1. Classify the implementation / 判断实现类别

**English:** Exercise: A Rust program loads PTX produced by nvcc, allocates device buffers, and launches a function. Which parts are written and compiled as Rust, and what additional evidence would establish that its kernel is written in Rust? List the host language, device-source language, and device artifact separately.

**中文：** 练习：一个 Rust 程序加载 nvcc 产生的 PTX，分配设备缓冲区并启动函数。哪些部分使用 Rust 编写和编译？还需要什么额外证据，才能证明它的设备内核是使用 Rust 编写的？请把宿主语言、设备源码语言和设备产物分别列出。

**English:** Worked answer: The host resource management and launch logic are Rust, while the kernel remains CUDA C++ compiled to PTX. PTX is an output format, not proof of source language. Evidence for a Rust kernel includes the actual Rust device source, the selected device compiler path, a successful build of that source, and the corresponding produced artifact. A host-only `cargo build` cannot replace those device compilation records. Device execution still needs separate validation because producing an artifact does not establish a correct runtime result.

**中文：** 参考解答：宿主资源管理和启动逻辑是 Rust，内核仍然是经 nvcc 编译为 PTX 的 CUDA C++。PTX 是产物格式，不能证明源码语言。证明 Rust 内核，需要实际 Rust 设备源码、选定的设备编译路径、该源码成功构建的记录，以及对应生成产物。仅有宿主 `cargo build` 成功，不能代替设备编译记录。随后还应单独验证设备执行，因为生成产物并不保证运行结果正确。

### 2. Reconstruct the ownership graph / 重建所有权关系

**English:** Exercise: A function handle retains its module, and the module retains a context. Can the application now drop its output buffer immediately after launching? Explain what the existing ownership graph proves and what it does not prove.

**中文：** 练习：函数句柄保留模块，模块又保留上下文。应用程序能否在启动后立即释放输出缓冲区？请分别说明现有所有权关系已经证明了什么，以及还有哪条生命周期关系没有得到证明。

**English:** Worked answer: The chain keeps code and context resources alive while the function exists. It says nothing about the output allocation unless the operation also owns or borrows that allocation under a sound completion contract. The buffer must remain valid until all relevant device accesses finish. A wrapper can retain ownership inside the operation or wait before allowing release; merely retaining the function is insufficient. Draw separate edges for code, storage, and execution completion so that one protection is not mistaken for another.

**中文：** 参考解答：这条关系保证函数存在期间，代码和上下文资源仍然有效。除非操作还通过可靠的完成契约拥有或借用输出分配，否则它不能说明输出内存是否有效。缓冲区必须一直保留到所有相关设备访问结束。封装可以在操作内部持有所有权，也可以先等待再允许释放；仅保留函数句柄远远不够。画图时应为代码、存储和执行完成分别标注边，避免把一种保护误当成另一种保护。

### 3. Explain the parameter slots / 解释参数槽

**English:** Exercise: A kernel expects a device pointer as its first parameter. Should the raw launch parameter array contain the numeric device address directly, or the address of a host variable holding that value? How long must each object survive?

**中文：** 练习：内核的第一个参数是设备指针。底层启动参数数组应该直接包含设备地址数值，还是包含保存该数值的宿主变量地址？宿主变量与设备分配各自需要存活到什么时候？

**English:** Worked answer: The slot points to the host argument value, so it contains the address of the host variable holding the device pointer. The launch reads that argument representation during the call. The device allocation must remain valid for the later asynchronous kernel access, which can outlive the call by a substantial interval. Correct slot indirection cannot compensate for freeing the underlying device allocation too early. A live device allocation also cannot compensate for incorrect argument order or width; inspect representation and lifetime separately.

**中文：** 参考解答：参数槽指向宿主侧的参数值，因此应保存持有设备指针的宿主变量地址。启动调用在调用期间读取这个参数表示，设备分配则必须继续维持到稍后的异步内核访问完成，两者可能相差很长时间。参数槽层级正确，不能补偿设备分配被提前释放；设备分配仍然有效，也不能补偿参数顺序和宽度错误。接口检查应分别覆盖表示和生命周期。

### 4. Challenge destructor-only synchronization / 检查仅靠析构的同步

**English:** Exercise: A safe function borrows a buffer, launches asynchronous device work, and returns a guard whose destructor waits. Why does this description alone fail to establish soundness, even if normal scope exit always invokes the destructor? Name a safe Rust operation that can invalidate that argument.

**中文：** 练习：一个安全函数借用缓冲区、启动异步设备工作，并返回析构时执行等待的守卫。即使正常离开作用域总会调用析构，为什么这段描述仍不足以证明接口可靠？请给出安全 Rust 中能够破坏这个推理的操作。

**English:** Worked answer: Safe Rust may forget the guard, so soundness cannot rely on its destructor always running. If forgetting ends the represented borrow and lets the caller reuse storage while the GPU still accesses it, the interface is unsound. An owned operation can retain or leak its allocation when forgotten, avoiding that reuse. Another design may synchronize before a borrowed operation returns. The complete interface must cover cancellation, forgetting, and errors.

**中文：** 参考解答：安全 Rust 可以遗忘守卫，因此可靠性不能依赖析构一定发生。如果遗忘使类型中表达的借用结束，调用方就可能在 GPU 仍访问时重用存储，接口便不可靠。拥有资源的操作可以在被遗忘时连同分配一起保留或泄漏，从而避免重用；另一种设计是在借用操作返回前完成同步。完整接口必须考虑取消、遗忘和错误，而不仅是正常作用域结束这一条路径。

### 5. Separate sharing from ordering / 区分共享与顺序

**English:** Exercise: Two host tasks share an `Arc` to one device buffer. One stream writes it and a second stream reads it. What does the shared pointer guarantee, and which additional relationship is necessary before the read? Explain why host reference counting cannot replace this relationship.

**中文：** 练习：两个宿主任务通过 `Arc` 共享设备缓冲区，一条流写入，另一条流读取。共享指针能够保证什么？读取开始前还必须建立什么关系？为什么宿主引用计数不能替代这个关系？

**English:** Worked answer: The shared pointer can preserve host-side ownership of the allocation. It does not order operations in independent streams. The reader requires a dependency establishing that the write has completed, such as the appropriate event wait or a prior explicit synchronization. Simultaneous access also has to obey the intended aliasing and mutation contract. Shared lifetime, execution order, and permission to mutate must be checked separately. Even a nonzero reference count cannot prevent stale data or conflicting accesses when the required read/write order is absent.

**中文：** 参考解答：共享指针可以维持分配的宿主所有权，却不会排列独立流中的操作。读取者需要建立写入已经完成的依赖，例如适当的事件等待，或先执行明确同步。并发访问还必须符合预定的别名与修改契约。共享生命周期、执行顺序以及修改权限应分别检查。即使引用计数始终大于零，如果读写之间没有必要顺序，程序仍可能得到旧数据或产生访问冲突。

### 6. Audit the one-dimensional kernel / 审计一维内核

**English:** Exercise: In the native Rust example, why is checking only `output.get_mut(index)` sufficient for the input access under the documented contract? Which two changes would invalidate that argument? Explain how each change breaks the argument rather than saying only that an out-of-bounds access is possible.

**中文：** 练习：原生 Rust 示例只检查 `output.get_mut(index)`，为什么在文档契约下也能保证输入读取范围正确？请给出两种修改，说明它们分别如何破坏这项推理，而不是仅回答“可能越界”。

**English:** Worked answer: Input and output have equal lengths, so a valid output index is also valid for the input. The one-dimensional geometry gives each output index a unique writer. Shortening the input breaks the range implication. Introducing extra launch dimensions while retaining a one-dimensional token can create multiple writers for the same element and break the ownership argument. Both changes require revisiting the host contract and device implementation. The changes affect range and uniqueness respectively; preserving the old tail guard alone does not preserve the complete safety argument.

**中文：** 参考解答：输入输出长度相同，所以有效输出索引也是有效输入索引；一维启动几何则为每个输出索引提供唯一写入者。缩短输入会破坏范围推导，增加启动维度却继续使用同一个一维令牌，则可能让多个线程写同一元素，破坏所有权推导。两种修改分别影响范围和唯一性，都需要重新审阅宿主契约与设备实现。单独保留原来的尾部判断并不能维持完整安全论证。

### 7. Interpret tile build evidence / 判断分块构建证据

**English:** Exercise: The cutile-rs example passes `cargo build`. A report says its GPU kernel has compiled and all 1024 values are correct. Which parts of that report are supported, and what steps are still missing? Classify the claims separately under host build, device compilation, and result validation.

**中文：** 练习：cutile-rs 示例通过 `cargo build` 后，报告写道“GPU 内核已经编译，全部一千零二十四个值都正确”。哪些结论获得了支持？还缺哪些步骤？请按照宿主构建、设备编译和结果验证分别判断。

**English:** Worked answer: The successful command supports host build and macro/type processing for that program. The runtime device compilation path still has to be invoked for the required specialization, the operation must execute and complete, and the output must pass validation. A healthy driver is required for those stages. Until then, report host build success with device JIT and GPU execution explicitly unverified. Assertions present in source have not necessarily executed, and expected output is not an observation.

**中文：** 参考解答：成功命令支持该程序的宿主构建、宏处理和相应类型检查。之后仍需触发所需特化的运行时设备编译路径，让操作实际执行并完成，再检查输出。后面这些阶段需要正常驱动支持。在完成之前，应写成宿主构建通过，设备即时编译与 GPU 执行尚未验证。不能把源代码中写有断言，误认为断言已经运行，更不能把预期输出当作观测结果。

### 8. Design a clean negative test / 设计清楚的失败测试

**English:** Exercise: You want to verify that a public affine API rejects mismatched input and output lengths. Must the test deliberately cause a GPU illegal access? Design a smaller test and explain what it establishes. Explain both what the smaller test proves and what it does not prove.

**中文：** 练习：你想验证公开仿射接口会拒绝输入输出长度不一致，是否必须故意触发 GPU 非法访问？请设计一个更小的测试，并说明它能证明什么、又不能证明什么。

**English:** Worked answer: Call the host shape validator with lengths seven and eight and assert the documented mismatch error before allocation or launch. Add a matching-length success case so that a validator rejecting everything cannot pass. This proves the selected host validation behavior; it does not prove all device indexing is correct. Device execution tests and sanitizers address separate obligations once the environment is suitable. Separating test objectives helps localize failures and permits continued interface checks without a GPU.

**中文：** 参考解答：以七和八调用宿主形状验证器，断言它在分配或启动之前返回文档规定的不匹配错误。再加入长度相同的成功案例，防止一个拒绝所有输入的错误验证器也通过测试。这能够证明指定宿主检查行为，不能证明所有设备索引都正确。环境适合时，还需要设备执行测试和检查工具覆盖其他义务。把测试目标拆开，有助于定位失败，也能在没有 GPU 时持续验证一部分接口。

### 9. Compare the three implementations fairly / 公平比较三种实现

**English:** Exercise: One implementation reports a first-request duration and another reports a warmed kernel event interval. Can the smaller number establish a better language or compiler? Specify the conditions needed for a meaningful comparison. Identify which input conditions in this course's three examples also need to be equalized.

**中文：** 练习：一个实现报告首次请求耗时，另一个报告预热后内核事件区间。较小的数字能否证明语言或编译器更优秀？请列出让比较有意义所需的实验条件，并指出本课三个示例还需要统一哪些输入条件。

**English:** Worked answer: The intervals include different work, so they cannot support that conclusion. Equalize input values and lengths, precision, hardware, compiler versions, transfer accounting, allocation reuse, warm-up, and synchronization. The examples use different lengths and input generation, so normalize those first. Report both steady-state device time and end-to-end latency when relevant, and require identical correctness criteria before interpreting speed. A faster wrong answer or a time omitting uploads and downloads is not a deliverable optimization.

**中文：** 参考解答：两个区间包含的工作不同，不能支持该结论。需要统一输入值与长度、精度、硬件、编译器版本、传输计时、分配复用、预热和同步。本课示例的长度与输入生成方式不同，因此首先要统一这两项。必要时分别报告稳定状态设备时间和端到端延迟，并在解释速度前要求相同正确性标准。更快的错误结果，或遗漏上传下载的时间，并不是可交付的优化成果。

### 10. Plan a service integration / 规划服务集成

**English:** Exercise: An inference request times out after its GPU operation has been submitted. The service wants to recycle its buffers immediately. What should the resource owner do, and how would you make the decision observable? Specify observations distinguishing response termination from the end of device access.

**中文：** 练习：一个推理请求在 GPU 操作提交后超时，服务准备立即回收并复用缓冲区。资源拥有者应该怎样处理？你会记录哪些信息，让别人能够判断请求响应结束与设备访问结束之间的关系？

**English:** Worked answer: Separate abandoning the client response from completing or safely retaining submitted device work. Keep the buffers owned until the matching completion condition is satisfied; only then return them to the pool. Record request and operation identifiers, submission time, stream or event association, completion status, and reclamation time. Shutdown and cancellation must follow the same ownership rule, even when no caller remains to receive the result. This prevents premature reuse and provides a traceable explanation when resources remain retained.

**中文：** 参考解答：应把放弃客户端响应，与完成或安全保留已提交设备工作分开。缓冲区必须保持被拥有，直到对应完成条件成立，然后才能返回资源池。记录请求与操作标识、提交时间、关联的流或事件、完成状态以及回收时间。停机与取消也必须遵循同一所有权规则，即使已经没有调用者接收结果。这样既能避免过早复用，也能让资源滞留问题获得可追踪的解释。

## Completion criteria / 完成标准

**English:** First, explain each implementation without collapsing the host and device compilation stages. Draw a resource graph for one launch and mark where code, argument slots, and allocations may be released. Identify the one explicit completion condition that permits reading the output. If your explanation relies on “Rust is safe” without stating the FFI contract, revisit the unsafe boundary before adding more features. Completion requires reasoning that corresponds to the code rather than memorizing runtime-library names.

**中文：** 首先，应能分别解释三种实现，不把宿主与设备编译阶段混为一谈。为一次启动画出资源关系，标明代码、参数槽和设备分配分别可以何时释放，并指出允许读取输出的明确完成条件。如果解释仍然依赖“Rust 是安全的”，却说不出外部接口契约，就应先回到不安全边界重新检查，再增加功能。课程验收重视能与代码对应的推理，而不是能背诵多少运行库名称。

**English:** Second, reproduce the CPU successes and expected E0499 failure, compile the host/PTX example and tile host example, and preserve the exact version records. On a healthy GPU machine, complete the native compiler build, execute all device examples, and retain validation output separately from compiler logs. An unavailable stage should remain explicitly unavailable in the report instead of being replaced with a CPU simulation or a predicted success message. The next experiment can then build on trustworthy evidence instead of first reconstructing what previous claims meant.

**中文：** 其次，应复现 CPU 成功案例和预期的 E0499 失败，编译宿主与 PTX 示例以及分块宿主示例，并保存精确版本记录。在正常 GPU 机器上，继续完成原生编译器构建、执行全部设备示例，并把结果验证输出与编译日志分开保存。尚不可执行的阶段，必须在报告中明确保留为未完成，不能用 CPU 模拟或预测的成功消息替代。这样的记录才能让下一次实验接着推进，而不必重新判断已有证据是否可信。

**English:** Finally, choose one next step based on the problem you own: wrap an existing CUDA kernel behind a reviewed Rust host API, extend the native SIMT example with a checked shape contract, or evaluate a tile operation on a supported workload. Preserve a small fixture before pursuing framework integration. The transferable skill is maintaining the relationship between ownership, execution order, and observed correctness as the system grows. Continue inspecting boundaries after the first successful example.

**中文：** 最后，根据自己负责的问题选择下一步：把现有 CUDA 内核封装到经过审阅的 Rust 宿主接口后面，为原生线程示例扩展受检查的形状契约，或在受支持工作负载上评估分块操作。进入框架集成之前，应保留一个小型复现工程。真正能够迁移到更大系统的能力，是在系统扩展时持续维护所有权、执行顺序和观测正确性之间的关系，而不是一次性跑通示例后就停止检查边界。

## Verification record / 验证记录

**English:** On 2026-09-18, the CUDA C++ source compiled to PTX with nvcc 13.3.73. The Rust Driver host example and cuTile host example compiled successfully with Rust 1.98.1 against the pinned cutile-rs revision. The pinned cuda-oxide nightly installed, but backend compilation stopped because of disk quota exhaustion; its temporary compiler installation and failed build artifacts were removed. Native kernel compilation, cuTile device JIT, and all GPU executions remain unverified. No driver changes were performed.

**中文：** 二〇二六年九月十八日，CUDA C++ 源码使用 nvcc 13.3.73 成功编译为 PTX；Rust Driver 宿主示例与 cuTile 宿主示例使用 Rust 1.98.1，在固定 cutile-rs 提交上成功编译。指定 cuda-oxide nightly 安装成功，但后端编译因磁盘配额耗尽停止，其临时编译器安装和失败构建产物已经清理。原生内核编译、cuTile 设备即时编译和全部 GPU 执行均未验证，没有进行任何驱动修改。

**English:** The CPU contract script was extracted from this document and executed: all six shapes and five rejection cases passed, and the deliberate conflicting borrow failed with E0499. The single-course bilingual checker, all seven checker unit tests, and the file whitespace check passed. These results validate the listed CPU behavior and document structure; they do not change the unverified device status above.

**中文：** CPU 契约脚本从本文提取后实际执行，六种形状与五项拒绝案例全部通过，刻意制造的冲突借用以 E0499 失败。单课双语检查、检查器全部七项单元测试，以及文件空白检查通过。这些结果验证所列 CPU 行为和文档结构，不改变前述设备执行仍未验证的状态。

## Official references / 官方参考资料

**English:** Project behavior is grounded in the fixed revisions, while CUDA semantics use the versioned 13.3 Driver API. Rust language references describe host language guarantees; they do not certify a third-party GPU wrapper. When updating the lesson, recheck the exact toolchain, runtime dependencies, supported GPU matrix, and generated launch interfaces before replacing the recorded revisions.

**中文：** 项目行为依据固定提交，CUDA 语义依据版本化的十三点三 Driver API。Rust 语言资料描述宿主语言保证，并不为第三方 GPU 封装提供认证。更新课程时，应先重新核对精确工具链、运行库依赖、支持显卡表以及生成的启动接口，再替换所记录的提交。

- [cuda-oxide pinned source / cuda-oxide 固定源码](https://github.com/NVlabs/cuda-oxide/tree/b9847e9515ed3a23096f22567d3eaf0a6e3e440c)
- [cuda-oxide toolchain / cuda-oxide 工具链](https://github.com/NVlabs/cuda-oxide/blob/b9847e9515ed3a23096f22567d3eaf0a6e3e440c/rust-toolchain.toml)
- [cuda-oxide launch documentation / cuda-oxide 启动文档](https://github.com/NVlabs/cuda-oxide/blob/b9847e9515ed3a23096f22567d3eaf0a6e3e440c/cuda-oxide-book/gpu-programming/launching-kernels.md)
- [cuda-oxide safety model / cuda-oxide 安全模型](https://github.com/NVlabs/cuda-oxide/blob/b9847e9515ed3a23096f22567d3eaf0a6e3e440c/cuda-oxide-book/gpu-safety/the-safety-model.md)
- [cutile-rs pinned source / cutile-rs 固定源码](https://github.com/NVlabs/cutile-rs/tree/d92c160949f58328ba6e96d81005e7110ba6f2b3)
- [cuda-core launch implementation / cuda-core 启动实现](https://github.com/NVlabs/cutile-rs/blob/d92c160949f58328ba6e96d81005e7110ba6f2b3/cuda-core/src/simt/mod.rs)
- [cuda-core buffer implementation / cuda-core 缓冲区实现](https://github.com/NVlabs/cutile-rs/blob/d92c160949f58328ba6e96d81005e7110ba6f2b3/cuda-core/src/simt/device_buffer.rs)
- [CUDA 13.3 contexts / CUDA 十三点三上下文](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__CTX.html)
- [CUDA 13.3 modules / CUDA 十三点三模块](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__MODULE.html)
- [CUDA 13.3 execution control / CUDA 十三点三执行控制](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__EXEC.html)
- [CUDA 13.3 memory / CUDA 十三点三内存](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__MEM.html)
- [CUDA 13.3 streams / CUDA 十三点三流](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__STREAM.html)
- [CUDA 13.3 events / CUDA 十三点三事件](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-driver-api/group__CUDA__EVENT.html)
- [Rust FFI / Rust 外部函数接口](https://doc.rust-lang.org/nomicon/ffi.html)
- [Rust destructor limitations / Rust 析构限制](https://doc.rust-lang.org/nomicon/destructors.html)
- [Rust Send and Sync / Rust 发送与共享](https://doc.rust-lang.org/nomicon/send-and-sync.html)
- [Rust type layout / Rust 类型布局](https://doc.rust-lang.org/reference/type-layout.html)
