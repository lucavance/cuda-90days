# Course 05: CUDA Programming Foundations / 课程 05：CUDA 编程基础

## Goals, Prerequisites, and Version Boundary / 目标、前置知识与版本边界

**English:** This course teaches how to construct and justify a complete CUDA program. The target is more precise than making a kernel compile: every logical element must have an owner, every pointer must refer to suitable memory, every asynchronous use must fit within its resource lifetime, and every claimed result must follow a checked completion point. You will build a vector-add implementation, verify its indexing and reference calculation on the CPU, and distinguish compiled device code from device code that has actually run.

**中文：** 本课教你构造并解释一个完整的 CUDA 程序。目标比让 kernel 编译通过更具体：每个逻辑元素都必须有负责它的线程，每个指针都必须指向合适的内存，每次异步使用都必须处于资源生命周期之内，每项结果声明都必须建立在已经检查的完成点之后。你将构建向量加法实现，在 CPU 上验证索引与参考计算，并区分已经编译的设备代码和真正执行过的设备代码。

**English:** Prerequisites are basic C++ functions, arrays, pointers, error handling, and the Linux environment model from Course 01. Familiarity with RAII helps with cleanup, but the CUDA reasoning does not depend on advanced template knowledge. This course consolidates Days 001, 002, 003, 010, 011, and 012. It introduces only the memory hierarchy needed for correctness; coalescing, shared-memory optimization, bank conflicts, and systematic performance tuning belong to the next course. This separation prevents conflating a correct program with a faster program.

**中文：** 前置知识是基本的 C++ 函数、数组、指针、错误处理，以及课程一建立的 Linux 环境模型。熟悉 RAII 有助于理解清理过程，但 CUDA 推理并不依赖复杂模板知识。本课整合第一、第二、第三、第十、第十一、第十二天的内容。内存层级只讲到能够支持正确性判断的程度，合并访存、共享内存优化、bank conflict 和系统性能调优留给下一课，避免把程序正确与程序更快混为一谈。

**English:** Official references were checked on 2026-09-18. The implementation targets the installed CUDA Toolkit 13.3 and uses its versioned Runtime API and new Programming Guide. NVIDIA now marks the old CUDA C++ Programming Guide as legacy, so its familiar URL should not be mistaken for the actively maintained guide. Unversioned documentation may describe CUDA 13.4; that does not change which compiler was used here. [CUDA 13.3 Programming Guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html)

**中文：** 官方资料核验日期为二〇二六年九月十八日。实现以本机 CUDA Toolkit 13.3 为目标，使用对应版本的 Runtime API 和新版 Programming Guide。NVIDIA 已把旧版 CUDA C++ Programming Guide 标记为旧文档，因此不能因为链接熟悉，就把它当作仍在维护的最新版指南。无版本文档可能已经描述 CUDA 13.4，但这不会改变本课实际使用的编译器版本。[CUDA 13.3 编程指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html)

**English:** The recorded machine has Ubuntu 26.04.1 and an RTX 4060, but NVML 610.57 and the loaded NVIDIA module 610.43.02 currently disagree. Consequently, this course can verify host-side experiments and compilation without claiming a successful GPU execution. The RTX 4060 is listed with compute capability 8.9, so the build command names `sm_89` explicitly instead of asking a broken environment to infer a native target. No driver repair is part of these experiments. [NVIDIA compute-capability table](https://developer.nvidia.com/cuda/gpus)

**中文：** 记录的机器运行 Ubuntu 26.04.1，配有 RTX 4060，但当前 NVML 610.57 与已加载 NVIDIA 模块 610.43.02 不一致。因此，本课可以验证主机实验与编译，却不能声称 GPU 已成功执行。官方表格把 RTX 4060 列为计算能力八点九，所以构建命令明确指定 `sm_89`，不要求存在问题的环境推断本机目标。所有实验都不包含驱动修复操作。[NVIDIA 计算能力表](https://developer.nvidia.com/cuda/gpus)

## 1. Separate the Algorithm from Its Execution / 区分算法与执行方式

**English:** Vector addition defines a simple mathematical relationship: for each valid index, the output is the sum of the corresponding inputs. A CPU loop and a GPU kernel can implement that same relationship with different execution schedules. The algorithm does not require one GPU thread per element; that is one mapping choice. Keeping the mathematical contract separate lets you compare implementations without assuming that identical source structure is necessary for identical results. It also prepares you to understand mappings in which one thread processes several elements.

**中文：** 向量加法定义了一个简单的数学关系：对于每个有效索引，输出等于两个对应输入之和。CPU 循环与 GPU kernel 可以采用不同调度方式实现同一关系。算法本身并不要求每个元素对应一个 GPU 线程，这只是映射选择之一。把数学契约与执行方式分开，才能比较不同实现，而不会错误地认为源代码结构必须一致，结果才有可能一致，也便于以后理解一个线程处理多个元素的设计。

```text
Inputs:  a[0 .. N), b[0 .. N)
Output:  c[0 .. N)
Rule:    c[i] = a[i] + b[i], for every 0 <= i < N
```

**English:** The host starts the program, prepares inputs, selects a device, allocates resources, and submits work. Device code executes on the GPU. A `.cu` file can contain both kinds of code, so the filename does not mean that every statement runs on the GPU. In particular, `main()`, vector allocation, ordinary logging, and most Runtime API calls in this lesson run on the CPU. The kernel launch is the boundary that requests device execution. [CUDA C++ introduction](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html) It does not move the entire host call stack onto the GPU.

**中文：** 主机负责启动程序、准备输入、选择设备、分配资源和提交工作，设备代码则在 GPU 上执行。一个 `.cu` 文件可以同时包含两类代码，所以文件后缀并不意味着所有语句都运行在 GPU 上。本课中的 `main()`、向量分配、普通日志以及大多数 Runtime API 调用都在 CPU 上执行。kernel 启动是请求设备执行的边界，而不是把整个函数调用栈搬到显卡上。[CUDA C++ 入门](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html)

**English:** Think of a launch as a submission with an execution configuration and arguments. The host supplies how many blocks to create, how many threads each block contains, which stream receives the operation, and which memory the kernel should use. A correct argument list is only one part of correctness. The same kernel body can be correct for one launch configuration and incomplete or unsafe for another. The host and device sides therefore share one contract rather than being independently correct modules connected by punctuation.

**中文：** 可以把启动理解为一次携带执行配置和参数的提交。主机指定创建多少个 block、每个 block 包含多少线程、操作交给哪条 stream，以及 kernel 使用哪些内存。参数列表正确只是正确性的一部分。同一段 kernel 在一种启动配置下可能正确，在另一种配置下却可能遗漏元素或越界。因此，主机与设备共同履行一个契约，而不是两个各自正确、只靠特殊标点连接起来的独立模块。

**English:** A small vector-add program is valuable because it exposes the whole lifecycle with almost no mathematical distraction. It is not evidence that a GPU is useful for every small task. Allocation, initialization, transfers, and launch overhead can dominate a tiny addition. The first goal is to make the contract visible and testable. Only after correctness and measurement boundaries are clear should you ask whether the workload is large enough, sufficiently parallel, or already resident on the device to benefit from GPU execution.

**中文：** 小型向量加法的价值，在于几乎不需要复杂数学就能展示完整生命周期，并不是证明 GPU 适合所有小任务。分配、初始化、传输与启动开销，都可能超过一次很小的加法计算。第一目标是让契约变得可见且可验证。只有在正确性与计量边界清楚之后，才应讨论负载是否足够大、并行度是否足够，以及数据是否已经留在设备上，从而判断 GPU 执行是否有实际收益。

## 2. Threads, Blocks, Grids, and Hardware / 线程、Block、Grid 与硬件

**English:** A launch creates a grid of thread blocks, and each block contains threads. In a one-dimensional launch, `threadIdx.x` identifies a thread within its block, `blockIdx.x` identifies the block within the grid, and `blockDim.x` gives the block size. `gridDim.x` gives the number of blocks. These values describe the logical execution geometry, not a promise that every thread exists on a separate physical arithmetic unit at the same instant. [CUDA programming model](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/01-introduction/programming-model.html) Logical thread identity and simultaneous hardware residency are different concepts.

**中文：** 一次启动创建由多个线程块组成的 grid，每个 block 再包含线程。在一维启动中，`threadIdx.x` 表示线程在 block 内的位置，`blockIdx.x` 表示 block 在 grid 内的位置，`blockDim.x` 给出块大小，`gridDim.x` 给出块数量。这些值描述逻辑执行几何关系，并不承诺每个线程都在同一时刻占有一个独立物理运算单元。线程身份与硬件同时驻留数量是不同概念。[CUDA 编程模型](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/01-introduction/programming-model.html)

**English:** A block is executed within one streaming multiprocessor, usually abbreviated SM, while blocks from the grid are scheduled across available SMs. A grid can contain more blocks than can reside simultaneously. That scalability requires ordinary blocks to be independent of a particular scheduling order. A kernel that assumes block zero finishes before block one starts has introduced a dependency the ordinary launch contract does not provide. Use a later kernel launch in an ordered stream for a simple global phase boundary.

**中文：** 一个 block 在一个流式多处理器中执行，通常把这种处理器简称为 SM，而 grid 中的多个 block 会被安排到可用 SM 上。grid 可以包含远多于同时驻留容量的块。这种可扩展性要求普通线程块不能依赖特定调度次序。如果 kernel 假设零号块先完成、一号块再开始，就引入了普通启动契约没有提供的依赖。对于简单的全局阶段边界，可以在有序 stream 中使用后续 kernel 启动。

**English:** Threads are grouped into warps of 32 in the CUDA model used here. Choosing a block size that is a multiple of 32 is a common starting point, but it is not a universal performance proof and not a substitute for device limits. A block of 256 threads contains eight warps; four such blocks do not imply that all 32 warps must be resident together. Registers, shared memory, hardware limits, and other work affect residency, which later performance experiments will investigate.

**中文：** 在本课采用的 CUDA 模型中，线程组成每组三十二个线程的 warp。块大小取三十二的倍数是常用起点，却不是通用性能证明，也不能替代设备限制检查。一个二百五十六线程的 block 包含八个 warp，但四个这样的 block 并不意味着三十二个 warp 必须同时驻留。寄存器、共享内存、硬件限制和其他任务都会影响驻留情况，这些因素将在后续性能实验中进一步研究。

**English:** The three-dimensional index types are a convenience for describing data, not an automatic understanding of your tensor layout. For a matrix, you may map one dimension to columns and another to rows, but still need the correct row stride when computing an address. A transposed or sliced tensor can have a different stride from its apparent width. This course uses contiguous one-dimensional arrays so that indexing and lifetime are isolated before layout complexity is introduced. Isolating those issues helps distinguish thread-mapping mistakes from address-calculation mistakes.

**中文：** 三维索引类型只是描述数据的便利工具，不会自动理解张量布局。处理矩阵时，可以把一个维度映射到列、另一个映射到行，但计算地址仍需使用正确行步幅。转置或切片之后的张量，步幅可能与表面宽度不同。本课使用连续一维数组，目的是先把索引和生命周期独立讲清，再引入布局复杂性，避免同时出现多个变量时无法判断错误来自线程映射还是地址计算。

## 3. Prove the Index Mapping / 证明索引映射

**English:** For block size `B`, a thread's global one-dimensional index is `blockIdx.x * B + threadIdx.x`. The block term chooses a range and the thread term chooses a position within that range. If you use only `threadIdx.x`, every block repeats the same first range and later elements remain untouched. If you multiply by `gridDim.x` instead of `blockDim.x`, the ranges can overlap or leave gaps. Derive the expression from ownership rather than memorizing variable names.

**中文：** 对于块大小 `B`，线程的一维全局索引为 `blockIdx.x * B + threadIdx.x`。前半部分选择区间，后半部分选择区间内的位置。若只使用 `threadIdx.x`，每个块都会重复处理第一段，后面的元素则无人负责。若错把乘数写成 `gridDim.x`，区间可能重叠或者出现空洞。应从谁负责哪段数据推导公式，而不是仅仅背诵变量名，这样才能发现看起来相似却含义不同的错误。

**English:** Let the input length be 1003 and the block size 256. Three blocks provide only 768 thread positions, so truncating division loses 235 elements. Four blocks provide 1024 positions, leaving 21 positions outside the valid range. The correct design combines rounding the block count up with a guard `i < N`. These solve different problems: rounding establishes coverage, while the guard prevents the extra threads from accessing nonexistent elements. Neither can replace the other.

**中文：** 假设输入长度为一千零三，块大小为二百五十六。三个块只提供七百六十八个线程位置，因此整数除法向下取整会漏掉二百三十五个元素。四个块提供一千零二十四个位置，其中二十一个超过有效范围。正确设计要同时采用块数向上取整和 `i < N` 边界判断。它们解决不同问题：向上取整保证覆盖，边界判断防止额外线程访问不存在的元素，二者不能互相替代。

```text
B = 256
N = 1003
blocks = N / B + (N % B != 0) = 4
launched_positions = 4 * 256 = 1024
valid_indices = 0 .. 1002
guarded_indices = 1003 .. 1023
```

**English:** The common expression `(N + B - 1) / B` is mathematically convenient, but adding first can overflow a bounded integer type. The quotient-and-remainder form above avoids that addition when `B` is positive. Separately, widen the block index before multiplication if your indexing type requires it. Casting after an overflowing multiplication does not repair the value. A host launch helper must also reject a zero block size and check that the resulting grid fits the selected device's limits.

**中文：** 常见表达式 `(N + B - 1) / B` 在数学上很方便，但先做加法可能使有限位宽整数溢出。只要 `B` 为正，上面的商与余数写法就能避免这一加法。另外，如果索引类型需要更宽范围，应在乘法之前扩展 block 索引。乘法已经溢出后再强制转换，并不能修复结果。主机启动辅助函数还应拒绝零块大小，并检查得到的 grid 是否符合所选设备的限制。

**English:** An empty input is a useful contract test. Mathematically, there are no output elements to compute. The host can return an empty result without allocating device buffers or launching a zero-block grid. This is not a special GPU optimization; it is an explicit definition of behavior at a boundary. Treat empty input separately from a failed device initialization: a successful empty CPU-side result says nothing about whether the machine can execute a nonempty CUDA workload. Otherwise an empty test could incorrectly report GPU availability without ever invoking the device.

**中文：** 空输入是很好的契约测试。从数学上说，没有任何输出元素需要计算，因此主机可以直接返回空结果，不分配设备缓冲区，也不启动零块 grid。这不是某种特殊 GPU 优化，而是在边界上明确规定行为。还要把空输入与设备初始化失败区分开：空结果在 CPU 侧成功返回，并不能说明机器有能力执行非空 CUDA 工作负载，否则测试可能在完全没有调用设备的情况下误报 GPU 可用。

**English:** For the one-thread-per-element mapping, correctness can be stated as three properties: every valid index is reached, no valid index has multiple writers, and no invalid index is dereferenced. The first two are ownership properties; the third is a bounds property. These properties can be checked by a CPU model of the index arithmetic. Such a model is valuable but incomplete: it cannot prove that the device binary uses the expected instructions or that stream and memory interactions are correct at runtime.

**中文：** 对每个元素一个线程的映射，可以把正确性写成三个性质：每个有效索引都被覆盖，每个有效索引没有多个写入者，任何无效索引都不被解引用。前两项属于所有权性质，第三项属于边界性质。它们可以通过 CPU 上的索引算术模型检查。这种模型很有价值，但仍不完整：它无法证明设备二进制使用了预期指令，也不能证明运行时的 stream 与内存交互一定正确。

## 4. Memory Spaces and Pointer Meaning / 内存空间与指针含义

**English:** `std::vector<float>` owns ordinary host storage. `cudaMalloc` creates a device allocation and returns a pointer value that identifies that allocation. The pointer itself can be stored in a CPU variable, but that does not mean the CPU may dereference the allocation as ordinary host memory. Likewise, passing an ordinary host pointer to a kernel is not made valid merely because the parameter type is `float*`. Pointer type, accessibility, allocation origin, and lifetime are separate parts of the contract. [CUDA memory management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html)

**中文：** `std::vector<float>` 拥有普通主机存储，`cudaMalloc` 则创建设备分配，并返回标识该分配的指针值。这个指针可以保存在 CPU 变量里，却不意味着 CPU 可以把目标当作普通主机内存解引用。同样，把普通主机指针传给 kernel，不会因为参数类型恰好是 `float*` 就自动合法。指针类型、可访问性、分配来源与生命周期，是契约中彼此不同的部分。[CUDA 内存管理](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html)

**English:** Global memory provides device storage accessible to the appropriate GPU threads. Shared memory is associated with a block in the basic model and supports cooperation within that block. Registers usually hold thread-private values. CUDA's term local memory is especially easy to misread: it describes thread-local storage in the CUDA memory hierarchy, not a promise of an on-chip register. The compiler may place some thread-local objects or spills in device-backed local storage. [Writing SIMT kernels](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html) A source variable being local therefore does not establish its eventual storage location.

**中文：** Global memory 提供适当 GPU 线程可以访问的设备存储；在基础模型中，shared memory 属于 block，用于块内合作；寄存器通常保存线程私有值。CUDA 中的 local memory 特别容易误读：它描述内存层级中的线程局部存储，并不承诺使用片上寄存器。编译器可能把某些线程局部对象或溢出值放入由设备内存支持的局部存储。因此，源码变量是局部变量，与它最终位于哪里并不是同一个问题。[编写 SIMT kernel](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html)

**English:** Allocation size is expressed in bytes, while the algorithm's length is expressed in elements. For `N` floats, the required byte count is `N * sizeof(float)`, with an overflow check if arbitrary large lengths are accepted. Copying only `N` bytes initializes only part of the intended input. Copying `sizeof(pointer)` bytes confuses a handle with the storage it names. Keep names such as `elements` and `bytes` distinct, and verify the relationship at the boundary where an application shape becomes a memory operation.

**中文：** 分配大小使用字节表示，算法长度则使用元素表示。对于 `N` 个浮点数，需要 `N * sizeof(float)` 字节；如果接受任意大长度，还要检查乘法溢出。只复制 `N` 字节，会让预期输入只初始化一部分；复制 `sizeof(pointer)` 字节，则是把句柄本身与它指向的存储混淆。应使用清楚区分元素数和字节数的变量名，并在应用形状转换成内存操作的边界验证二者关系。

**English:** Unified addressing and managed memory provide additional capabilities, but neither makes synchronization optional. Accessibility depends on the allocation and the platform's supported behavior, and data can still be in use by another execution agent. This course deliberately uses explicit host and device buffers so that transfers and ownership remain visible. Later, when using a framework or managed allocation, ask which guarantees it adds and which completion obligations still remain yours. [Unified and system memory](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/understanding-memory.html) An abstraction can reduce code without removing the underlying lifetime obligations.

**中文：** 统一寻址与托管内存提供额外能力，但都不会让同步变成可有可无。可访问性取决于分配类型和平台支持行为，而且数据仍可能被另一个执行主体使用。本课特意采用显式主机与设备缓冲区，让传输和所有权保持可见。以后使用框架或托管分配时，也应继续追问：它增加了哪些保证，还有哪些完成义务仍然由自己承担。抽象层减少代码，并不意味着底层生命周期已经消失。[统一与系统内存](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/understanding-memory.html)

## 5. A Complete Dataflow Before Any Optimization / 优化之前先建立完整数据流

**English:** The basic lifecycle is prepare inputs, allocate device storage, copy inputs, launch the kernel, copy the result back after its dependencies, wait for the required completion, validate, and release resources. The exact API placement can vary, but the dependencies cannot be skipped. A result buffer on the CPU should not be inspected while a pending copy may still modify it. A device buffer should not be reused for a new request while an earlier kernel still reads it. Dataflow and resource lifetime must be designed together.

**中文：** 基本生命周期是准备输入、分配设备存储、复制输入、启动 kernel、在满足依赖后复制结果、等待必要操作完成、验证并释放资源。具体 API 的放置方式可以变化，但依赖不能省略。若一个待完成的复制仍可能修改 CPU 结果缓冲区，就不应提前读取它；若较早的 kernel 仍在读取设备缓冲区，就不应把同一块存储重新分配给下一条请求。数据流与资源寿命必须一起设计。

**English:** An input copy is not an initialization of every allocation in the program. `cudaMalloc` does not provide a useful algorithmic initial value for your output. A kernel that fails to write some output elements can therefore appear to work if validation happens to inspect only a few positions. In the main example, the output starts as NaN and is copied to device storage before the kernel runs. Unwritten positions then remain obvious to the finite-value comparison rather than depending on whatever bytes the allocator returned. Choose test data to expose missing writes deliberately instead of relying on chance.

**中文：** 复制输入并不等于初始化程序中的所有分配。`cudaMalloc` 不会为输出提供算法需要的初值。如果 kernel 漏写了一些输出，而验证又只检查少数位置，程序就可能看起来正常。主例把输出初始化为非数值，再复制到设备存储后启动 kernel。这样，没有被写入的位置会在有限值比较中明确失败，不需要依赖分配器原来返回的字节恰好是什么。测试数据的设计应主动暴露遗漏，而不是碰运气。

**English:** Use distinct input and output allocations until aliasing behavior is intentionally specified. Some elementwise operations permit an output to alias one input, but shifted overlap can create read-after-write dependencies between threads. A signature containing three pointers does not reveal whether overlap is allowed. State the policy and test it if the API supports it. The teaching implementation owns three independent device buffers, which removes aliasing from the proof and lets us focus on coverage, ordering, and lifetime.

**中文：** 在有意规定别名行为之前，先使用独立的输入输出分配。某些逐元素操作允许输出与一个输入完全重合，但带偏移的重叠可能在线程之间产生先读后写依赖。包含三个指针的函数签名，本身没有说明能否重叠。如果接口支持别名，就应明确策略并验证它。本课实现拥有三个独立设备缓冲区，把别名从证明中移除，从而集中研究覆盖、顺序和生命周期，而不是同时处理隐含的数据竞争。

## 6. Streams Express Order, Not Guaranteed Parallelism / Stream 表达顺序而非必然并行

**English:** A stream gives CUDA operations an ordering context. In the simple sequence used here, two input copies, an output initialization, the kernel, and the return copy are submitted to the same stream. Later operations respect the dependencies implied by that order. A stream is not a dedicated CPU thread, and creating many streams does not guarantee simultaneous device execution. Hardware capability, resource use, memory behavior, and explicit dependencies still determine what can overlap. [Asynchronous execution](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/asynchronous-execution.html) Use a stream first to express correct ordering, then investigate possible concurrency gains.

**中文：** Stream 为 CUDA 操作提供顺序上下文。本课的简单序列把两次输入复制、输出初始化、kernel 和结果返回复制提交到同一条 stream，后续操作遵守这一顺序所表达的依赖。Stream 不是专属 CPU 线程，创建很多 stream 也不保证设备同时执行。硬件能力、资源使用、内存行为和显式依赖，仍然决定哪些工作可以重叠。因此，应先用它描述正确顺序，再研究潜在并发收益。[异步执行](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/asynchronous-execution.html)

**English:** Kernel launches are normally asynchronous with respect to the host: returning from the launch does not prove completion. The word asynchronous on a memory-copy API also needs care. Host blocking behavior can depend on transfer direction and whether host memory is pageable or pinned; an `Async` name does not guarantee that a particular call immediately returns. Our vectors use ordinary pageable host memory, so the example makes no claim that copies overlap with CPU work. [Runtime API synchronization behavior](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/api-sync-behavior.html) The asynchronous interface is used here to make stream ordering explicit, not to announce a performance benefit.

**中文：** Kernel 启动通常相对于主机异步，启动语句返回不能证明计算已经结束。内存复制 API 中的异步名称也需要谨慎理解：主机是否阻塞，可能取决于传输方向，以及主机内存是可分页还是页锁定，名字里有 `Async` 并不保证某次调用立即返回。本例的向量使用普通可分页主机内存，所以不声称复制一定与 CPU 工作重叠。这里选择异步接口是为了明确 stream 顺序，而不是预先宣布性能收益。[Runtime API 同步行为](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/api-sync-behavior.html)

**English:** `cudaStreamSynchronize(stream)` waits for the preceding work in that stream and reports an error if the runtime encounters one. `cudaDeviceSynchronize()` is broader and is useful for simple debugging boundaries, but placing it after every operation can remove concurrency that you later want to measure. Use the narrowest completion condition that satisfies the resource dependency. The first implementation can be intentionally conservative; optimization should refine a known-correct dependency graph rather than delete waits at random. [Stream management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__STREAM.html)

**中文：** `cudaStreamSynchronize(stream)` 等待该 stream 先前的工作，并在运行时发现错误时报告失败。`cudaDeviceSynchronize()` 的范围更大，适合建立简单调试边界，但如果每项操作后都使用它，可能消除以后想要测量的并发。应采用能够满足资源依赖的最小完成条件。初版可以有意保守，后续优化再细化已知正确的依赖图，而不是随机删除等待，直到某次运行碰巧变快。[Stream 管理](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__STREAM.html)

**English:** Different streams need explicit dependencies when one consumes another's result. A common solution is to record an event after the producer and make the consumer stream wait on it. A host sleep is not such a dependency, because its duration says nothing reliable about device completion under a changing workload. Also avoid building correctness on accidental default-stream interactions. This course creates an explicit nonblocking stream so that its intended order is visible in the program rather than hidden in a global convention.

**中文：** 当一条 stream 消费另一条 stream 的结果时，需要明确依赖。常见做法是在生产者之后记录 event，再让消费者 stream 等待它。主机睡眠不是这样的依赖，因为负载变化时，睡眠时长无法可靠说明设备是否完成。也应避免把正确性建立在偶然的默认 stream 交互之上。本课创建显式非阻塞 stream，让预期顺序直接出现在程序里，而不是隐藏在某个全局约定中，便于阅读者审查。

## 7. Two Error Boundaries and One Result Contract / 两道错误边界与结果契约

**English:** Runtime functions generally report a `cudaError_t`; check the returned value at the call site and preserve operation context. A kernel launch expression is not itself a `cudaError_t` value that can be wrapped like `cudaMalloc`. After the launch, inspect the runtime's last-error state, then check a completion operation before claiming execution succeeded. A readable error name is more useful when accompanied by the operation, source location, input length, and launch geometry. [CUDA error handling](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__ERROR.html)

**中文：** Runtime 函数通常通过 `cudaError_t` 报告状态，应在调用位置检查返回值，并保留操作上下文。Kernel 启动表达式本身不是可以像 `cudaMalloc` 一样直接包装的 `cudaError_t`。启动之后应检查运行时的最近错误状态，再检查完成操作，才能声明执行成功。可读的错误名称如果同时附带操作、源代码位置、输入长度和启动几何信息，会更有诊断价值，而不是只给出一个孤立的失败字符串。[CUDA 错误处理](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__ERROR.html)

**English:** `cudaGetLastError()` returns and clears the calling host thread's last-error state, while `cudaPeekAtLastError()` observes it without clearing it. Neither is a device-completion wait. An illegal access during execution can surface at a later synchronization or another API boundary. Therefore, the operation that reports an error may not be the operation that caused it. During diagnosis, narrow the region between checked completion points, and keep the first useful failure instead of overwriting it with cleanup messages.

**中文：** `cudaGetLastError()` 返回并清除调用主机线程的最近错误状态，`cudaPeekAtLastError()` 则只观察而不清除。二者都不是等待设备完成的操作。执行中的非法访问可能在之后的同步或其他 API 边界才暴露，因此报告错误的位置不一定就是造成错误的位置。诊断时应缩小两个已检查完成点之间的区域，并保留第一条有价值的失败信息，避免让清理阶段的后续消息覆盖真正的起点。

**English:** Successful completion still does not prove the arithmetic is correct. A kernel can write the wrong values to valid addresses and trigger no CUDA error at all. The output must be compared with a reference under a stated numerical policy. Conversely, a failed environment initialization does not show that the index formula is wrong. Keep environment failures, launch failures, execution failures, and numerical mismatches in separate report fields so that each observation leads to the relevant next experiment. Calling every category CUDA unavailable would lose that diagnostic direction.

**中文：** 操作成功完成，仍不证明算术正确。Kernel 可以向合法地址写入错误值，而完全不触发 CUDA 错误，所以输出还必须按照明确的数值策略与参考结果比较。反过来，环境初始化失败也不能证明索引公式有错。应在报告中区分环境失败、启动失败、执行失败和数值不一致，让每种观察都能指向相关的下一项实验，而不是把所有问题统称为“CUDA 跑不了”，失去排查方向。

**English:** Cleanup must preserve the original failure and avoid pretending that resources have been safely reused. The sample uses a small owner that waits on its stream before releasing buffers, reports cleanup errors, and disallows copying. If a CUDA failure has made the execution context unusable, the example terminates rather than attempting to continue serving requests. This is a teaching ownership pattern, not a complete recovery architecture for a long-running inference service. Production recovery needs an explicit decision about the affected process and device state.

**中文：** 清理过程既要保留原始失败，也不能假装资源已经能够安全复用。示例使用一个小型拥有者，在释放缓冲区前等待自身 stream，报告清理错误，并禁止复制。如果 CUDA 失败导致执行上下文无法继续使用，示例会结束程序，而不是尝试继续提供请求服务。这是教学用所有权模式，并非长期运行推理服务的完整恢复架构。生产恢复还必须明确决定如何处理受影响的进程与设备状态。

## 8. CPU Laboratory: Coverage and Deliberate Index Bugs / CPU 实验：覆盖性与故意索引错误

**English:** The following complete experiment uses only Python. It enumerates the logical positions created by a launch and verifies coverage, uniqueness, and bounds after the guard. It also reproduces three mistakes: rounding the grid down, omitting the block offset, and allowing `i == N`. The reported failures are expected evidence that the checker can reject these mistakes. This is a model of the arithmetic, not a CUDA emulator and not a substitute for running the compiled kernel on a healthy device. It can still eliminate a class of logical defects while the device is unavailable.

**中文：** 下面的完整实验只使用 Python。它枚举一次启动创建的逻辑位置，并在边界判断之后验证覆盖、唯一性与合法范围。同时复现三种错误：块数向下取整、遗漏 block 偏移，以及允许 `i == N`。报告的失败是预期证据，说明检查器能够拒绝这些错误。这只是索引算术模型，并不是 CUDA 模拟器，也不能替代在正常设备上运行已经编译的 kernel，但能够在设备不可用时先排除一类逻辑缺陷。

```bash
# experiment: index-model
python3 - <<'PY'
from collections import Counter

def positions(n, block, variant="correct"):
    if n < 0 or block <= 0:
        raise ValueError("invalid shape")
    blocks = n // block + (n % block != 0)
    if variant == "round-down":
        blocks = n // block
    result = []
    for block_index in range(blocks):
        for thread_index in range(block):
            index = block_index * block + thread_index
            if variant == "no-block-offset":
                index = thread_index
            allowed = index <= n if variant == "inclusive-guard" else index < n
            if allowed:
                result.append(index)
    return result

def valid(n, indices):
    counts = Counter(indices)
    return set(counts) == set(range(n)) and all(count == 1 for count in counts.values())

sizes = (0, 1, 31, 32, 33, 255, 256, 257, 1003)
for size in sizes:
    assert valid(size, positions(size, 256))
print("correct_mapping_passed_sizes=", sizes)
for variant in ("round-down", "no-block-offset", "inclusive-guard"):
    indices = positions(1003, 256, variant)
    assert not valid(1003, indices), variant
    missing = len(set(range(1003)) - set(indices))
    invalid = sorted(set(indices) - set(range(1003)))
    duplicate_writes = len(indices) - len(set(indices))
    print(variant, {"missing": missing, "invalid": invalid, "duplicate_writes": duplicate_writes})
try:
    positions(10, 0)
except ValueError:
    print("zero_block_rejected")
else:
    raise AssertionError("zero block size was accepted")
PY
```

**English:** Boundary values are chosen for reasons: zero tests the no-work contract, one tests the smallest nonempty input, values around 32 exercise a warp boundary, and values around 256 exercise the block boundary. The length 1003 requires multiple blocks and leaves a partial final block. Testing only length 1024 with a block size of 256 would hide the round-down error. A test set should challenge the assumptions in the mapping instead of merely contain a large number of convenient sizes. A large count of convenient cases can otherwise create a false impression of coverage.

**中文：** 边界值都有选择理由：零检查无任务契约，一检查最小非空输入，三十二附近检查 warp 边界，二百五十六附近检查 block 边界。一千零三则既需要多个块，又留下不完整的最后一块。如果只测试长度一千零二十四、块大小二百五十六，块数向下取整的错误就会被隐藏。测试集合应主动挑战映射中的假设，而不是仅仅罗列很多方便整除的大小，让数量造成覆盖充分的错觉。

## 9. Complete Vector-Add Implementation / 完整向量加法实现

**English:** Save and build the following complete program with the block provided below. The source has a `--cpu-only` mode that checks the host reference and the numerical validator without calling CUDA APIs, a `--gpu` mode for future device validation, and a separate `--invalid-launch` demonstration. Device modes must remain unexecuted while the recorded driver mismatch is unresolved. The source is intentionally a correctness laboratory; it reports no benchmark number and makes no optimization claim.

**中文：** 请使用下面的完整代码块保存并构建程序。源代码包含 `--cpu-only` 模式，它不调用 CUDA API，只检查主机参考计算和数值验证器；另有供以后设备验证使用的 `--gpu`，以及独立的 `--invalid-launch` 演示。在已记录驱动不匹配尚未解决时，设备模式保持未执行。这个源文件有意定位为正确性实验，不输出基准数字，也不声明任何优化效果，避免把首次跑通与性能提升混淆。

```bash
# experiment: vector-build-cpu
COURSE05_DIR=$(mktemp -d /tmp/course05-vector-XXXXXX)
export COURSE05_DIR
cat > "$COURSE05_DIR/vector_add.cu" <<'CU'
#include <cuda_runtime.h>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

void cuda_check(cudaError_t status, const char* operation, int line) {
    if (status != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + " at line " +
            std::to_string(line) + ": " + cudaGetErrorString(status));
    }
}
#define CUDA_CHECK(operation) cuda_check((operation), #operation, __LINE__)

std::size_t grid_size(std::size_t n, unsigned block) {
    if (block == 0) throw std::invalid_argument("block must be positive");
    return n / block + (n % block != 0);
}

__global__ void vector_add(const float* a, const float* b, float* c, std::size_t n) {
    const std::size_t i = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

__global__ void no_op() {}

bool matches(const std::vector<float>& expected, const std::vector<float>& actual) {
    if (expected.size() != actual.size()) return false;
    for (std::size_t i = 0; i < expected.size(); ++i) {
        if (!std::isfinite(expected[i]) || !std::isfinite(actual[i])) return false;
        const double error = std::abs(static_cast<double>(actual[i]) - expected[i]);
        const double limit = 1e-6 + 1e-6 * std::abs(static_cast<double>(expected[i]));
        if (error > limit) return false;
    }
    return true;
}

struct DeviceWork {
    float* a = nullptr;
    float* b = nullptr;
    float* c = nullptr;
    cudaStream_t stream = nullptr;
    bool& cleanup_ok;
    explicit DeviceWork(bool& status) : cleanup_ok(status) {}
    DeviceWork(const DeviceWork&) = delete;
    DeviceWork& operator=(const DeviceWork&) = delete;
    void note(cudaError_t status, const char* operation) noexcept {
        if (status != cudaSuccess) {
            cleanup_ok = false;
            std::fprintf(stderr, "cleanup %s: %s\n", operation, cudaGetErrorString(status));
        }
    }
    ~DeviceWork() noexcept {
        if (stream) note(cudaStreamSynchronize(stream), "stream wait");
        if (c) note(cudaFree(c), "free c");
        if (b) note(cudaFree(b), "free b");
        if (a) note(cudaFree(a), "free a");
        if (stream) note(cudaStreamDestroy(stream), "destroy stream");
    }
};

void gpu_case(const std::vector<float>& a, const std::vector<float>& b,
              const std::vector<float>& reference, const cudaDeviceProp& properties) {
    const std::size_t n = a.size();
    if (b.size() != n || reference.size() != n) throw std::invalid_argument("shape mismatch");
    if (n == 0) return;
    if (n > std::numeric_limits<std::size_t>::max() / sizeof(float)) {
        throw std::overflow_error("byte count overflow");
    }
    constexpr unsigned block = 256;
    const std::size_t blocks = grid_size(n, block);
    if (block > static_cast<unsigned>(properties.maxThreadsPerBlock) ||
        block > static_cast<unsigned>(properties.maxThreadsDim[0]) ||
        blocks > static_cast<std::size_t>(properties.maxGridSize[0])) {
        throw std::runtime_error("launch geometry exceeds device limits");
    }
    const std::size_t bytes = n * sizeof(float);
    std::vector<float> result(n, std::numeric_limits<float>::quiet_NaN());
    bool cleanup_ok = true;
    {
        DeviceWork work(cleanup_ok);
        CUDA_CHECK(cudaStreamCreateWithFlags(&work.stream, cudaStreamNonBlocking));
        CUDA_CHECK(cudaMalloc(&work.a, bytes));
        CUDA_CHECK(cudaMalloc(&work.b, bytes));
        CUDA_CHECK(cudaMalloc(&work.c, bytes));
        CUDA_CHECK(cudaMemcpyAsync(work.a, a.data(), bytes, cudaMemcpyHostToDevice, work.stream));
        CUDA_CHECK(cudaMemcpyAsync(work.b, b.data(), bytes, cudaMemcpyHostToDevice, work.stream));
        CUDA_CHECK(cudaMemcpyAsync(work.c, result.data(), bytes, cudaMemcpyHostToDevice, work.stream));
        vector_add<<<static_cast<unsigned>(blocks), block, 0, work.stream>>>(work.a, work.b, work.c, n);
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaMemcpyAsync(result.data(), work.c, bytes, cudaMemcpyDeviceToHost, work.stream));
        CUDA_CHECK(cudaStreamSynchronize(work.stream));
        if (!matches(reference, result)) throw std::runtime_error("GPU numerical mismatch");
    }
    if (!cleanup_ok) throw std::runtime_error("GPU cleanup failed");
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::invalid_argument("use --cpu-only, --gpu, or --invalid-launch");
        const std::string mode = argv[1];
        if (mode != "--cpu-only" && mode != "--gpu" && mode != "--invalid-launch") {
            throw std::invalid_argument("unknown mode");
        }
        cudaDeviceProp properties{};
        if (mode != "--cpu-only") {
            CUDA_CHECK(cudaSetDevice(0));
            CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));
        }
        if (mode == "--invalid-launch") {
            no_op<<<1, properties.maxThreadsPerBlock + 1>>>();
            const cudaError_t status = cudaGetLastError();
            if (status == cudaSuccess) throw std::runtime_error("invalid launch was accepted");
            std::cout << "expected_launch_error=" << cudaGetErrorString(status) << '\n';
            return 0;
        }
        const std::size_t sizes[] = {0, 1, 31, 32, 33, 255, 256, 257, 1003, 1048579};
        for (const std::size_t n : sizes) {
            std::vector<float> a(n), b(n), reference(n);
            for (std::size_t i = 0; i < n; ++i) {
                a[i] = static_cast<float>(static_cast<int>(i % 251) - 125) * 0.25f;
                b[i] = static_cast<float>(static_cast<int>(i % 127) - 63) * 0.5f;
                reference[i] = a[i] + b[i];
            }
            if (!matches(reference, reference)) throw std::runtime_error("reference validation failed");
            if (n != 0) {
                auto corrupted = reference;
                corrupted.back() += 1.0f;
                if (matches(reference, corrupted)) throw std::runtime_error("wrong value was accepted");
                corrupted = reference;
                corrupted[0] = std::numeric_limits<float>::quiet_NaN();
                if (matches(reference, corrupted)) throw std::runtime_error("NaN was accepted");
            }
            if (mode == "--gpu") gpu_case(a, b, reference, properties);
            std::cout << "mode=" << mode << " n=" << n << " blocks=" << grid_size(n, 256)
                      << " status=pass\n";
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "failure: " << error.what() << '\n';
        return 1;
    }
}
CU
python3 - <<'PY'
import os
from pathlib import Path
import subprocess
root = Path(os.environ["COURSE05_DIR"])
subprocess.run(["nvcc", "-std=c++17", "-O2", "-lineinfo", "-arch=sm_89",
                str(root / "vector_add.cu"), "-o", str(root / "vector_add")], check=True)
subprocess.run([str(root / "vector_add"), "--cpu-only"], check=True)
print(f"artifacts={root}")
PY
```

**English:** The kernel body is short because it owns only one responsibility: compute one valid output element. The host side carries shape checks, allocation, transfers, ordering, validation, and cleanup. This asymmetry is normal in a small correctness program. Do not remove host-side checks merely to make the source resemble a compact tutorial slide. In a larger application, reusable owners and launch helpers can reduce repetition while preserving the same guarantees at a clear interface. Conciseness should come from encapsulation rather than omitted obligations.

**中文：** Kernel 主体很短，因为它只承担一个责任：计算一个有效输出元素。主机侧则负责形状检查、分配、传输、顺序、验证与清理。在小型正确性程序里，这种代码量不对称很正常。不要为了让源码看起来像一页简短教程，就删除主机检查。更大的应用可以通过可复用拥有者与启动辅助函数减少重复，但仍应在清楚的接口上保留同样保证，使简洁来自封装，而不是来自遗漏契约。

**English:** The result vector is created before `DeviceWork`, so it remains alive while the device owner is destroyed during normal exit or exception unwinding. Input vectors also outlive the call to `gpu_case`. The destructor makes a best-effort completion wait before freeing buffers and does not throw a second exception over the original one. Cleanup failures are reported separately and make an otherwise successful case fail. This ordering is worth drawing explicitly: C++ lexical scope alone is safe only when it encloses every asynchronous use.

**中文：** 结果向量在 `DeviceWork` 之前创建，所以在正常离开作用域或异常展开、设备拥有者析构时，它仍然存活。输入向量也比 `gpu_case` 调用活得更久。析构函数释放缓冲区前尽力等待完成，而且不通过第二个异常覆盖原始异常。清理失败会单独报告，并让原本成功的用例转为失败。这种顺序值得明确画出来：只有词法作用域包住所有异步使用时，C++ 的自动析构才足以支持安全生命周期。

**English:** The output-initialization copy adds traffic and the destructor includes a conservative wait, so this source is not a throughput benchmark. They make unwritten output and resource lifetime easier to inspect. A later benchmark can move allocation outside the timed region, reuse buffers, and establish a narrower cleanup policy after proving equivalent dependencies. Preserve the correctness mode as a separate tool so that performance edits cannot silently remove the checks that justified the program in the first place.

**中文：** 输出初始化复制增加了流量，析构函数也包含保守等待，所以这个源文件不是吞吐基准。这些设计让漏写输出与资源生命周期更容易检查。以后的基准可以把分配移出计时区间、复用缓冲区，并在证明依赖等价后使用更精细的清理策略。但应把正确性模式保留为独立工具，避免性能修改悄悄删除最初支撑程序正确性的检查，最后只剩下一组看起来更快却不知道是否可靠的数字。

## 10. Compilation, Targets, and Honest Validation / 编译目标与诚实验证

**English:** `nvcc` coordinates host and device compilation for a CUDA translation unit. The `-arch=sm_89` option specifies the device target for this example, while `-std=c++17` fixes the language dialect and `-lineinfo` retains useful source mapping for later device diagnosis. None of these options requires the GPU to execute the program during compilation. The toolchain can therefore produce a valid binary while the machine's driver path is unhealthy. [NVCC 13.3 manual](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html) Compilation and execution are distinct evidence layers and should be reported separately.

**中文：** `nvcc` 协调 CUDA 编译单元的主机与设备编译。示例中的 `-arch=sm_89` 指定设备目标，`-std=c++17` 固定语言标准，`-lineinfo` 保留供以后设备诊断使用的源代码映射。这些选项都不要求 GPU 在编译期间运行程序。因此，即使机器驱动路径存在问题，工具链仍可能生成有效二进制。编译与执行属于不同证据层次，应该在报告里分开记录。[NVCC 13.3 手册](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html)

**English:** Three validation statements must remain separate: the compiler accepted the program; CPU-side checks passed; the device computed the expected output. The first excludes some syntax, type, and build errors. The second validates the reference, selected boundary arithmetic, and checker behavior. Only the third tests the actual CUDA execution path. In the current environment, the first two are attainable, while the third remains pending. Do not label the combined result simply as all tests passed without naming the unexecuted device stage.

**中文：** 三种验证陈述必须分开：编译器接受程序，CPU 检查通过，设备计算得到预期输出。第一种排除部分语法、类型和构建错误；第二种验证参考计算、选定边界算术以及检查器行为；只有第三种测试实际 CUDA 执行路径。当前环境可以完成前两项，第三项仍待验证。不能笼统写成全部测试通过，却不指出没有执行的设备阶段，否则读者会把有限证据理解成完整成功。

**English:** A binary compiled only for the example's target is not a universal deployment artifact. Other devices may need different architecture settings or an intentional fat-binary policy. For this lesson, a single explicit target keeps the build reproducible and avoids accidental host-dependent selection. Before transferring the binary, record its build target and the destination device capability. A failure to find compatible device code is a deployment compatibility issue, distinct from an out-of-bounds access in a kernel that successfully launched.

**中文：** 只按本例目标编译的二进制，不是通用部署产物。其他设备可能需要不同架构设置，或者有意设计的多目标二进制策略。本课使用一个明确目标，是为了让构建可复现，并避免目标选择意外依赖主机。把二进制转移到别处之前，应记录构建目标和目标设备能力。找不到兼容设备代码属于部署兼容问题，它与成功启动之后的 kernel 越界是两种不同故障，需要不同调查方式。

## 11. Device Failure Experiments for a Healthy Environment / 正常设备环境下的失败实验

**English:** After the driver path is restored and separately validated, the commands below exercise normal GPU correctness and a deliberately oversized block. They assume `COURSE05_DIR` still identifies the directory created by the build block. In this lesson's execution record these commands are not run. The invalid-launch mode treats a rejected launch as the expected outcome and exits successfully only after observing a CUDA error; its process status therefore describes the experiment, not a successful kernel launch.

**中文：** 驱动路径恢复并经过独立验证后，可以使用下面的命令检查正常 GPU 正确性，以及故意过大的 block。它们假设 `COURSE05_DIR` 仍指向构建代码块创建的目录。在本课执行记录里，这些命令没有运行。非法启动模式把启动被拒绝作为预期结果，只有观察到 CUDA 错误后才成功退出，因此进程状态表达的是实验是否符合预期，而不是 kernel 已经成功启动，两个成功概念不能混用。

```bash
# pending: GPU execution requires a healthy driver / GPU 执行要求正常驱动
"$COURSE05_DIR/vector_add" --gpu
"$COURSE05_DIR/vector_add" --invalid-launch
compute-sanitizer --tool memcheck --error-exitcode 99 "$COURSE05_DIR/vector_add" --gpu
```

**English:** Compute Sanitizer can help identify device memory errors that ordinary output comparison may miss. A clean sanitizer run has its own scope: it covers the executed inputs and checked classes of behavior, and it is not a mathematical proof for every possible input. It also requires actual device execution. Compiling a binary with source line information prepares for this investigation but does not perform it. Keep sanitizer output and exit status with the workload configuration when the pending experiment becomes executable. [Compute Sanitizer manual](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html)

**中文：** Compute Sanitizer 有助于识别普通结果比较可能遗漏的设备内存错误。一次干净的检查也有范围限制：它覆盖实际执行的输入和检查的行为类别，并不是对所有可能输入的数学证明。而且它需要真正执行设备代码。编译时保留源代码行信息，只是在为这项调查做准备，并没有执行调查本身。以后能够运行这组待验证实验时，应把检查器输出、退出状态和负载配置一起保存。[Compute Sanitizer 手册](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html)

**English:** For a numerical failure experiment, change the copied laboratory source so that the guard reads `i + 1 < n`. This leaves the final output unwritten while avoiding an intentional invalid memory access. The NaN initialization should then make the GPU validator reject every nonempty case whose last element is omitted. Do not claim this outcome as observed until you run it. The CPU index model can already explain the missing ownership, while the future GPU test will verify that the compiled path exposes it as expected.

**中文：** 数值失败实验可以在复制出的临时源码里，把边界判断改成 `i + 1 < n`。这样会遗漏最后一个输出，却不需要故意制造非法内存访问。非数值初始化应使 GPU 验证器拒绝漏掉最后元素的非空用例。在真正运行之前，不能把这种结果写成已观察事实。CPU 索引模型已经能够解释缺少写入者的问题，而以后的 GPU 实验则验证编译后的实际路径是否按预期暴露它。

## 12. Validate the Validator and the Numerical Policy / 验证检查器与数值策略

**English:** A comparison such as `abs(actual - expected) > tolerance` can accidentally accept NaN because comparisons involving NaN do not behave like ordinary real-number comparisons. The sample first requires finite values for its deliberately finite test inputs. It then applies an absolute-plus-relative tolerance. This is a stated policy for this experiment, not a universal policy for kernels that intentionally produce infinities or NaNs. Those kernels need an explicit treatment of exceptional values in their reference contract.

**中文：** 类似 `abs(actual - expected) > tolerance` 的比较，可能意外接受非数值，因为涉及非数值的比较并不按照普通实数直觉工作。本例针对特意保持有限的测试输入，先要求结果都是有限值，再采用绝对误差加相对误差阈值。这是本实验明确规定的策略，并不是适用于所有 kernel 的通用策略。如果某种操作本来就允许产生无穷或非数值，就需要在参考契约里单独定义这些特殊结果如何比较。

**English:** Absolute tolerance controls error near zero, while relative tolerance scales with the reference magnitude. Neither should be increased merely to make a failing test pass. First determine whether the discrepancy comes from a wrong index, uninitialized memory, arithmetic ordering, or an intentional change in precision. Floating-point arithmetic is finite and implementation details can affect rounding, especially in more complex expressions. This course uses bounded values built from quarters and halves so that basic addition is easy to reason about. [Floating-point computation](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/05-appendices/mathematical-functions.html)

**中文：** 绝对误差约束零附近的偏差，相对误差则随参考值大小缩放。不能为了让失败测试通过，就随意增加任何一种容差。应先判断差异来自错误索引、未初始化内存、运算次序，还是有意降低精度。浮点运算精度有限，实现细节也可能影响舍入，尤其是在复杂表达式里。本课使用由四分之一和二分之一构成的有界输入，让基础加法容易推理，先减少数值分析以外的干扰因素。[浮点计算](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/05-appendices/mathematical-functions.html)

**English:** The CPU-only mode deliberately corrupts a reference value and injects NaN to confirm that the validator rejects both. This is a test of the test mechanism. It does not independently prove that the CPU reference implements the intended algorithm, so review the reference against the mathematical specification as well. For richer operators, use multiple kinds of evidence: a simple independent implementation, hand-computed tiny inputs, shape invariants, and a trusted framework where appropriate. Avoid duplicating the same indexing bug in both implementation and oracle.

**中文：** CPU 模式故意破坏一个参考值，并注入非数值，确认验证器能够拒绝这两种情况。这是在测试检查机制本身，却不能独立证明 CPU 参考实现符合预期算法，因此还要把参考代码与数学定义核对。面对更复杂算子，可以结合简单独立实现、手算的小输入、形状不变量以及合适的可信框架等多种证据。尤其要避免把同一个索引错误同时写进实现与参考，使两者一致地给出错误答案。

**English:** Random inputs are useful after boundary cases, but record the seed and distribution. A workload consisting only of zeros can conceal a missing computation, while a workload containing only positive values may miss sign-related mistakes in a more complex operator. The sample uses deterministic mixed-sign data and reports every tested size. A useful failure report identifies the first mismatch and its neighborhood, rather than dumping millions of elements and making the relevant index difficult to find. Test output should narrow the problem rather than merely demonstrate that the program produced many logs.

**中文：** 边界用例之后可以使用随机输入，但应记录随机种子与分布。全零负载可能掩盖遗漏计算，只有正值的负载也可能漏掉复杂算子中的符号错误。示例采用确定性的正负混合数据，并报告每个测试大小。有效的失败报告应指出首个不一致位置及其附近数据，而不是倾倒数百万个元素，让真正相关的索引反而难以寻找。测试输出应该帮助缩小问题，而不是仅仅证明程序生成了很多日志。

## 13. Completion and Timing Answer Different Questions / 完成与计时回答不同问题

**English:** A CPU timer around an asynchronous launch mainly measures the host submission interval unless a suitable completion condition is included. A device event interval measures a different region of work. End-to-end latency may include allocation, input transfer, kernel work, output transfer, and queueing. These numbers can all be legitimate if labeled correctly, but they cannot be substituted for one another. This course does not publish any of them because no GPU timing experiment was performed.

**中文：** 如果没有包含合适的完成条件，围绕异步启动放置的 CPU 计时器主要测量主机提交区间。设备 event 区间测量的是另一段工作，而端到端延迟又可能包括分配、输入传输、kernel、输出传输以及排队。只要标签准确，这些数字都可能有意义，但不能互相替代。本课没有发布任何一种 GPU 计时结果，因为没有执行相应实验。先把计量对象说清，比过早填入一列毫秒数字更重要。

**English:** CUDA events can mark positions in a stream, and elapsed-time calculation requires the recorded events to have completed under the relevant API contract. A typical kernel interval records a start event, launches the kernel, records an end event, waits for the end event, and obtains elapsed time. Warmup, repetitions, cache state, and host overhead require additional benchmark design. Copying this sequence into a program does not by itself produce a representative performance result. [CUDA event management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html) The sequence establishes only part of a representative measurement design.

**中文：** CUDA event 可以标记 stream 中的位置，计算经过时间则要求已记录事件按照相应 API 契约完成。典型 kernel 区间会记录开始事件、启动 kernel、记录结束事件、等待结束事件，再取得经过时间。预热、重复次数、缓存状态与主机开销还需要额外基准设计。把这串步骤复制进程序，并不自动得到有代表性的性能结果，它只解决了计时边界的一部分问题。[CUDA event 管理](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html)

**English:** A debugging synchronization can be the right tool for locating an error and the wrong boundary for a production throughput measurement. Keep diagnostic mode and performance mode explicit. When removing a broad wait, replace its dependency with a justified narrower mechanism rather than relying on good luck. The correctness tests should continue to pass across awkward sizes and repeated runs. If an apparent speedup disappears when outputs are actually consumed, the earlier measurement may have stopped before the work it claimed to measure. That is a measurement error, not evidence that the GPU suddenly became slower.

**中文：** 调试同步可能非常适合定位错误，却不适合作为生产吞吐测量边界。因此，应明确区分诊断模式与性能模式。去掉范围很大的等待时，要用有依据的更窄机制替代依赖，而不是依靠运气。正确性测试仍应在不规则大小和重复运行下通过。如果所谓加速在真正消费输出时消失，很可能是原来的测量在声称测量的工作完成之前就停止了，这属于计量错误，而不是 GPU 突然变慢。

## 14. Failure Classification for an Inference Engineer / 推理工程中的故障分类

**English:** If the program cannot initialize a device, investigate the environment boundary before changing the arithmetic. If a launch is rejected, inspect geometry, target compatibility, and resource requirements. If execution fails later, inspect accesses, lifetime, and dependencies. If execution completes but values differ, investigate indexing and numerical behavior. This classification does not guarantee the root cause, but it prevents unrelated experiments from obscuring the first informative observation.

**中文：** 如果程序无法初始化设备，应先调查环境边界，再考虑修改算术。如果启动被拒绝，就检查几何配置、目标兼容性与资源要求；如果之后执行失败，就检查访问、生命周期与依赖；如果执行完成但数值不同，则调查索引与数值行为。这种分类不能自动保证找到根因，却能防止不相关实验覆盖第一条有信息量的观察，让每次修改都针对尚未解决的具体问题，而不是在多个层次间盲目尝试。

**English:** In a framework extension, the host contract also includes tensor device, dtype, shape, stride, and current stream. A standalone example that allocates its own stream cannot simply be pasted into every framework without checking integration rules. The same vector-add arithmetic may need a different launch wrapper when called from PyTorch, Candle, or a serving runtime. The transferable skill is expressing ownership and ordering precisely, then adapting those contracts to the host framework rather than assuming the framework will repair an unsafe kernel.

**中文：** 在框架扩展里，主机契约还包括张量设备、数据类型、形状、步幅和当前 stream。一个自行创建 stream 的独立示例，不能不检查集成规则就粘贴进所有框架。同样的向量加法算术，从 PyTorch、Candle 或推理运行时调用时，可能需要不同启动包装。真正可迁移的能力，是准确表达所有权与顺序，再把契约适配到宿主框架，而不是假设框架会自动修复一个不安全的 kernel。

**English:** Your systems-development experience is directly useful here. A CUDA buffer resembles an asynchronously used service resource: allocation creates capacity, submission lends that capacity to work, and completion permits reuse. Stream dependencies resemble explicit ordering between pipeline stages. Error reporting resembles preserving the first failure across a process boundary. The GPU adds a new execution model, but disciplined resource ownership and evidence-based diagnosis remain familiar engineering responsibilities.

**中文：** 既有系统开发经验在这里可以直接发挥作用。CUDA 缓冲区类似被异步服务使用的资源：分配创建容量，提交把容量交给工作使用，完成才允许复用。Stream 依赖类似流水线阶段之间的显式顺序，错误报告则类似跨进程边界保留第一条失败信息。GPU 带来了新的执行模型，但清晰的资源所有权和基于证据的诊断，仍然是熟悉的工程职责，并不是需要把过去经验全部推倒重学。

## 15. Ten Exercises and Worked Answers / 十道练习与参考答案

### Exercise 1: The Missing Tail / 练习一：遗漏的尾部

**English:** A kernel uses the correct global index and `i < N`, but the host launches `N / 256` blocks for `N = 1003`. How many elements remain unwritten? Explain why a correct guard cannot repair the problem and state a block-count formula that avoids adding `B - 1` to a potentially large length.

**中文：** Kernel 使用正确全局索引和 `i < N`，但主机在长度一千零三时只启动 `N / 256` 个块。还有多少元素没有写入？为什么正确边界判断无法修复这个问题？请给出一种无需对潜在很大的长度加上 `B - 1` 的块数公式。

**English:** Three blocks cover 768 elements, leaving 235 unwritten. The guard can suppress invalid accesses but cannot create missing threads. For positive `B`, use `N / B + (N % B != 0)`, then check the resulting grid against device limits. Handle `N == 0` without launching. Coverage and bounds are separate proof obligations and both must be satisfied.

**中文：** 三个块覆盖七百六十八个元素，还剩二百三十五个未写入。边界判断可以阻止非法访问，却不能创造没有启动的线程。对于正数 `B`，可使用 `N / B + (N % B != 0)`，再检查 grid 是否符合设备限制。`N == 0` 单独处理而不启动。覆盖与边界是两项独立证明义务，必须同时满足，不能因为其中一项正确就忽略另一项。

### Exercise 2: Repeated Ownership / 练习二：重复的数据所有权

**English:** Four blocks each compute `i = threadIdx.x` and write `c[i]`. With a block size of 256 and a length of 1003, which part of the output has multiple writers and which part is untouched? Would adding `__syncthreads()` repair the mapping? Distinguish thread synchronization from ownership of output elements.

**中文：** 四个块都使用 `i = threadIdx.x` 并写入 `c[i]`，块大小二百五十六、长度一千零三。哪一段输出具有多个写入者，哪一段完全未被处理？增加 `__syncthreads()` 是否能够修复映射？请区分线程同步与元素归属这两个问题。

**English:** Indices zero through 255 have writers from all four blocks; indices 256 through 1002 are untouched. A block barrier does not change the address calculation or create ownership for the missing range. Include the block offset in the global index. Even if repeated writes happen to store the same value, that does not justify a mapping with overlapping unsynchronized writers and incomplete coverage.

**中文：** 零到二百五十五号索引都受到四个块写入，二百五十六到一千零二号则无人处理。块内屏障不会改变地址计算，也不会为缺失区间创造负责线程。应把 block 偏移加入全局索引。即使重复写入碰巧存储相同值，也不能据此认可存在未同步重叠写入且覆盖不完整的映射，更不能用一次结果看起来正确来替代所有权证明。

### Exercise 3: Pointer Type Is Not Accessibility / 练习三：指针类型不等于可访问性

**English:** A programmer passes `std::vector<float>::data()` to a kernel because the kernel expects `const float*`. Why is type compatibility insufficient in this course's explicit-memory model? What steps connect the host vector to a device-readable input without relying on managed-memory assumptions?

**中文：** 程序员因为 kernel 参数是 `const float*`，便把 `std::vector<float>::data()` 直接传进去。为什么在本课的显式内存模型中，类型相容仍然不够？不依赖托管内存假设时，应通过哪些步骤把主机向量连接为设备可以读取的输入？

**English:** The C++ pointer type does not establish where the allocation lives or which execution agent may access it. Allocate device storage of the checked byte size, copy the host input through an appropriate CUDA operation, and order the kernel after that copy. Keep the host source alive for the copy's required lifetime and the device allocation alive through kernel completion. Pass the resulting device pointer to the kernel.

**中文：** C++ 指针类型没有证明分配位于哪里，也没有证明哪个执行主体可以访问它。应按检查过的字节数分配设备存储，通过合适 CUDA 操作复制主机输入，并让 kernel 排在复制之后。主机源数据要覆盖复制所需的生命周期，设备分配则要保持到 kernel 完成。随后传入得到的设备指针，才能把类型、位置、顺序和寿命这些条件共同满足。

### Exercise 4: The Host Printed a Message / 练习四：主机打印了日志

**English:** A host log says `kernel submitted`, followed immediately by a successful `cudaGetLastError()`. May the program read the host result buffer and report numerical success? Identify the missing operations and explain what the two observations actually establish. An absence of immediate errors must not be equated with correct completion.

**中文：** 主机日志显示 `kernel submitted`，随后 `cudaGetLastError()` 也成功。程序能否马上读取主机结果缓冲区并报告数值成功？请指出缺少哪些操作，并分别解释这两个观察真正建立了什么证据，而不是把没有立即报错等同于已经正确完成。

**English:** No. The log shows host progress, and the error check does not wait for device completion. The result must be copied to host memory in an order that depends on the kernel, and the program must check the required completion point before inspecting it. Only then can a numerical comparison establish correctness for that input. Submission, completed transfer, and valid output are distinct milestones.

**中文：** 不能。日志只说明主机向前执行，错误检查也没有等待设备完成。结果必须按照依赖 kernel 的顺序复制到主机内存，程序还必须检查所需完成点，然后才能读取。此后才有资格通过数值比较确认该输入下的正确性。提交、传输完成与输出有效，是不同里程碑；任何一个缺失，都不能只凭前面的日志推断后面的状态。

### Exercise 5: Async Does Not Promise Overlap / 练习五：异步不承诺重叠

**English:** The sample uses `cudaMemcpyAsync` with ordinary vectors. A reviewer concludes that transfer and CPU execution must overlap because the function name contains `Async`. What is wrong with that conclusion, and what guarantee does placing the operations in the same stream actually provide? Separate host return behavior, operation ordering, and hardware concurrency.

**中文：** 示例对普通向量使用 `cudaMemcpyAsync`，审查者因为函数名带有 `Async`，便认为传输必然与 CPU 执行重叠。这个结论哪里有问题？把这些操作放进同一条 stream，真正提供的又是什么保证？请把主机返回行为、操作顺序和硬件并发分开。

**English:** Host blocking behavior depends on the transfer and memory category, including pageable versus pinned host storage. The name alone does not prove overlap. The single stream expresses the sequence of copies and kernel work, which is the correctness property used here. Demonstrating useful overlap would require suitable memory, hardware support, independent work, and a trace or measurement that actually observes concurrent progress.

**中文：** 主机阻塞行为取决于传输与内存类型，包括主机存储是否可分页或页锁定，名字本身不能证明重叠。单条 stream 表达复制和 kernel 工作的顺序，这是本例依赖的正确性性质。证明有用重叠则还需要合适内存、硬件支持、独立工作，以及真正观察到并发推进的时间线或测量。代码里使用异步接口，只是相关条件之一。

### Exercise 6: A Block Barrier Is Not a Grid Barrier / 练习六：块内屏障不是全网格屏障

**English:** Block zero writes a value in global memory and block one reads it after calling `__syncthreads()`. Why is this not a valid general cross-block protocol for an ordinary launch? Give a simple two-phase design that makes the dependency explicit without introducing advanced cooperative-launch features. Do not assume block identifiers specify execution order.

**中文：** 零号块向 global memory 写入一个值，一号块调用 `__syncthreads()` 后读取它。为什么这不是普通启动中普遍有效的跨块协议？请给出一种不依赖高级协作启动特性的两阶段设计，让这个依赖变得明确，而不是假设块编号代表执行顺序。

**English:** `__syncthreads()` coordinates threads of its own block; it does not wait for an unrelated block, whose execution order is unspecified. Use one kernel for the producer phase and a subsequent kernel in the same ordered stream for the consumer phase, with suitable storage retained between them. More advanced cross-block mechanisms exist, but they require their own capability and synchronization contracts and are outside this lesson. Those special capabilities cannot be assumed for an ordinary launch.

**中文：** `__syncthreads()` 协调的是自身 block 中的线程，不会等待执行次序没有保证的其他块。可以用第一个 kernel 完成生产阶段，再在同一有序 stream 中提交后续 kernel 完成消费阶段，并在两阶段之间保留适当存储。确实存在更高级跨块机制，但它们需要自己的能力与同步契约，超出本课范围，不能把这些特殊能力默认为普通启动已提供。

### Exercise 7: A Validator That Accepts NaN / 练习七：接受非数值的验证器

**English:** A test rejects a result only when `abs(actual - expected) > 1e-5`. The actual value is NaN and the expected value is finite. Explain the danger and state the policy used by the sample. Why should the policy be documented rather than assumed to fit every numerical operator?

**中文：** 一个测试仅在 `abs(actual - expected) > 1e-5` 时拒绝结果，而实际值是非数值，参考值是有限值。请解释风险，并说明本例采用什么策略。为什么应把这一策略写入文档，而不能认为它天然适合所有数值算子？

**English:** The comparison involving NaN can evaluate false and let the bad value pass. The sample requires finite expected and actual values before checking absolute-plus-relative error, and it injects NaN to verify rejection. Some operators legitimately produce exceptional values, so those need a separate defined comparison policy. Validation must reflect the operator's contract rather than a convenient expression copied without examining its edge cases. Otherwise the validator itself can conceal the error.

**中文：** 涉及非数值的比较可能得到假，从而让坏值通过。本例先要求参考与实际值都有限，再检查绝对加相对误差，并主动注入非数值来验证拒绝行为。有些算子合法地产生特殊值，因此需要另一套明确比较策略。验证必须反映算子契约，而不能只是复制一个方便表达式，却没有检查其边界行为，否则检查器本身会成为掩盖错误的来源。

### Exercise 8: Compiled Is Not Executed / 练习八：已编译不等于已执行

**English:** The source compiles for `sm_89`, and `--cpu-only` passes all sizes while the machine still reports a driver/library mismatch. Write the strongest justified validation statement. List two claims that would exceed the evidence and one useful task that can still proceed without repairing the driver.

**中文：** 源码按 `sm_89` 编译成功，`--cpu-only` 的全部大小通过，但机器仍报告驱动与库不匹配。请写出最强且有依据的验证陈述，列出两个超出证据的说法，并指出一项无需修复驱动也能继续完成的有用工作。

**English:** The source compiled under the recorded toolchain and its CPU reference and validator checks passed; GPU execution remains unverified. Claiming device correctness or a GPU speedup would exceed the evidence. You can still inspect launch geometry, run the independent index model, review lifetimes, and prepare the pending device test commands. These are useful engineering steps as long as they are not relabeled as successful hardware validation.

**中文：** 可以说源码在记录的工具链下编译成功，CPU 参考与验证器检查通过，GPU 执行仍未验证。声明设备结果正确，或者声明获得 GPU 加速，都超出证据。仍可检查启动几何、运行独立索引模型、审查生命周期，以及准备待执行设备命令。只要不把它们重新命名为硬件验证成功，这些都属于有价值的工程进展，不需要因为一个层次受阻就停止所有学习。

### Exercise 9: Resource Lifetime Across a Launch / 练习九：跨启动的资源生命周期

**English:** A helper creates host inputs and device buffers, submits asynchronous copies and a kernel, then returns a host output vector without waiting. Its local owners free the device buffers at function exit. What must be established before this interface can be correct, and why is returning a vector alone not a completion contract?

**中文：** 辅助函数创建主机输入和设备缓冲区，提交异步复制与 kernel，然后不等待就返回主机输出向量。局部拥有者在函数退出时释放设备缓冲区。这个接口要正确，必须先建立哪些条件？为什么返回一个向量本身不能充当完成契约？

**English:** Every input and buffer must remain valid until all operations that use it have completed, and the returned output must not be read before its final write completes. A synchronous interface can wait before returning. An asynchronous interface must return or retain an owner and completion mechanism that preserve those lifetimes. A vector only describes storage ownership; it does not automatically communicate whether another execution agent is still modifying that storage. The return interface must account for both data representation and asynchronous state, not merely choose a container type.

**中文：** 所有输入与缓冲区都必须存活到使用它们的操作全部完成，而返回输出也不能在最终写入结束前被读取。同步接口可以在返回前等待，异步接口则必须返回或保留能够维持生命周期的拥有者与完成机制。向量只描述存储所有权，不会自动表达另一个执行主体是否仍在修改这段存储。因此，接口返回值需要同时考虑数据形态和异步状态，而不只是选一个容器类型。

### Exercise 10: A Misleading Speedup / 练习十：误导性的加速结果

**English:** A GPU launch takes less host-clock time than a CPU loop, so a report declares the GPU faster. The GPU output is never copied back or checked, and no completion wait lies inside the timer. Identify the missing evidence and propose the measurements that should be labeled separately in a later benchmark. Avoid directly comparing submission time with computation time.

**中文：** GPU 启动所用主机时钟时间少于 CPU 循环，于是报告宣布 GPU 更快。但输出从未复制回去或检查，计时区间也没有完成等待。请指出缺少哪些证据，并提出以后基准里应分别标注的计量对象，避免把提交时间与计算时间直接比较。

**English:** The report lacks completed device execution, numerical correctness, and a comparable timed region. First validate the output after checked completion. Then distinguish host submission cost, device kernel time, transfer cost, and end-to-end latency under a stated workload. Warmup and repeated measurements are additional requirements for a representative benchmark. A faster submission does not establish that the requested computation finished faster. Stopping a timer before work finishes omits work rather than optimizing it.

**中文：** 报告缺少设备执行完成、数值正确和可比较计时区间的证据。先在检查完成之后验证输出，再在明确负载下区分主机提交成本、设备 kernel 时间、传输成本与端到端延迟。预热和重复测量也是建立有代表性基准的额外要求。提交更快，不代表请求的计算更快结束；如果工作还没完成，计时器停止得早只是遗漏了工作，而不是实现了优化。

## 16. Acceptance and Next Steps / 验收与下一步

**English:** The CPU-stage acceptance requires the index model to pass all intended sizes and reject each deliberate mistake, and the compiled host mode to reject corrupted values and NaN. You should explain the empty-input branch, the byte-count calculation, the widened index multiplication, and the order of resources in `gpu_case`. These explanations are part of the deliverable. They make it possible to review a future modification without rerunning the entire learning conversation.

**中文：** CPU 阶段验收要求索引模型通过所有预期大小，并拒绝每种故意错误，同时要求编译后的主机模式拒绝破坏值和非数值。你应能解释空输入分支、字节数计算、乘法之前的索引扩展，以及 `gpu_case` 中资源的先后关系。这些解释也属于交付内容，因为它们让别人能够审查未来修改，而不必重新经历整段学习对话，也避免把会运行命令误当成已经掌握程序契约。

**English:** Device-stage acceptance remains pending until normal initialization is available. It will require all GPU sizes to match the reference after checked completion, the oversized launch to be rejected as expected, and an appropriate sanitizer run to complete without reported memory errors for the tested cases. Record hardware, toolkit, driver state, build command, input set, and raw output. A failure should remain a first-class result with its category, not be deleted because it prevents the report from looking complete.

**中文：** 设备阶段验收要等正常初始化可用后才能完成。届时需要所有 GPU 大小在检查完成后与参考一致，过大的启动按预期被拒绝，并且针对已测试用例的适当内存检查没有报告错误。记录硬件、工具包、驱动状态、构建命令、输入集合与原始输出。失败也应作为带分类的一等结果保留下来，不能因为它使报告看起来不完整就删掉，否则下一步工作会失去最重要的事实依据。

**English:** The next course can now ask how the same correct computation accesses memory and uses device resources. You will retain the ownership and completion proof while changing layout, work distribution, or staging. This is the basis for meaningful optimization: a new implementation must satisfy the same output contract, and any speed claim must describe the same measured work. The foundation built here also prepares you to inspect framework-generated launches and inference-runtime traces without confusing CPU submission with GPU execution.

**中文：** 下一课可以在此基础上研究同一个正确计算如何访问内存和使用设备资源。改变布局、工作分配或暂存方式时，仍要保留所有权与完成证明。这正是有意义优化的基础：新实现必须满足相同输出契约，加速声明也必须描述相同计量工作。本课建立的基础还会帮助你阅读框架生成的启动和推理运行时时间线，不再把 CPU 提交与 GPU 执行混淆，为后续系统诊断提供可靠起点。

## Execution Record / 实际执行记录

**English:** On 2026-09-18, the CPU index laboratory passed nine boundary sizes and rejected all three deliberate mapping bugs plus a zero block size. The complete CUDA source compiled with `nvcc` 13.3.73 for `sm_89`, and its `--cpu-only` mode passed ten sizes from zero through 1,048,579, including rejection of corrupted values and NaN. The compiler and host tests do not validate GPU execution. The `--gpu`, `--invalid-launch`, and Compute Sanitizer commands remain unexecuted under the recorded driver mismatch.

**中文：** 二〇二六年九月十八日，CPU 索引实验通过九个边界大小，并拒绝三种故意映射错误和零块大小。完整 CUDA 源码使用 `nvcc` 13.3.73 面向 `sm_89` 编译成功，`--cpu-only` 模式通过从零到一百零四万八千五百七十九的十个大小，包括拒绝破坏值与非数值。编译和主机测试不能验证 GPU 执行。在已记录驱动不匹配条件下，`--gpu`、`--invalid-launch` 与 Compute Sanitizer 命令保持未执行。

**English:** The course-specific bilingual checker passed. The numerical results above are validation outcomes, not performance measurements. No driver package, module, or system configuration was changed. To extend the record later, append the actual device-run output and its environment after executing the pending commands on a healthy setup; do not replace the distinction between the original host-only evidence and the later GPU evidence. Preserving that chronology and evidence boundary keeps the complete learning record reviewable.

**中文：** 针对本课的双语检查通过。上面的数值描述验证结果，不是性能测量。没有修改驱动软件包、内核模块或系统配置。以后扩展记录时，应在正常环境执行待验证命令之后，追加真实设备输出及其环境，不要抹去最初只有主机证据与后来获得 GPU 证据之间的区别。保留这一时间与层次关系，才能让完整学习记录仍然可审查。

## Official References / 官方参考资料

**English:** These are upstream references checked on 2026-09-18. CUDA semantics and API links use the 13.3 archive where available, while the hardware table and sanitizer manual are maintained vendor pages. The examples and explanatory scenarios in this course are original, and the pending GPU commands do not constitute a record of successful execution.

**中文：** 以下为二〇二六年九月十八日核验的上游资料。CUDA 语义与 API 尽量使用十三点三版本归档，硬件表格和检查器手册则来自厂商维护页面。本课示例与分析情景为原创，列出的待执行 GPU 命令不构成成功运行记录，也不能替代后续实际采集的设备结果。

- [CUDA 13.3 Programming Guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html) / 新版编程指南。
- [CUDA programming model](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/01-introduction/programming-model.html) / 执行模型。
- [Introduction to CUDA C++](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html) / 程序结构。
- [Writing SIMT kernels](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html) / 线程与内存基础。
- [Asynchronous execution](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/asynchronous-execution.html) / 异步执行。
- [Unified and system memory](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/understanding-memory.html) / 内存可访问性。
- [Runtime memory management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html) / 分配与复制。
- [API synchronization behavior](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/api-sync-behavior.html) / API 同步条件。
- [Runtime error handling](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__ERROR.html) / 错误状态。
- [Stream management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__STREAM.html) / Stream 完成关系。
- [Event management](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html) / Event 计时。
- [Floating-point computation](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/05-appendices/mathematical-functions.html) / 浮点语义。
- [NVCC 13.3](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html) / 编译目标。
- [GPU compute capability](https://developer.nvidia.com/cuda/gpus) / 硬件能力。
- [Compute Sanitizer](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html) / 设备内存检查。
