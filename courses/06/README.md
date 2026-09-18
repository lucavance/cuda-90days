# Course 06: CUDA Optimization and Performance Analysis / 第六课：CUDA 优化与性能分析

## Goals, prerequisites, and verification boundary / 目标、前置知识与验证边界

**English:** This course develops a repeatable optimization method: describe the work, predict the bottleneck, change one mechanism, verify correctness, and measure the same quantity again. The central experiment is an out-of-place matrix transpose with a copy reference and three transpose implementations. It connects global-memory coalescing, shared-memory layout, bank conflicts, timing, and occupancy in one program. The goal is not to memorize a fastest kernel, but to explain which change affects which resource and what evidence would support that explanation.

**中文：** 本课建立可重复的优化方法：描述工作、预测瓶颈、改变一个机制、验证正确性，再次测量同一个量。核心实验是非原地矩阵转置，包括复制参考以及三个转置实现，用一个程序串联全局内存合并访问、共享内存布局、存储体冲突、计时与占用率。目标不是背下最快内核，而是能够解释每项改动影响哪种资源，以及什么证据能够支持这一解释。

**English:** Prerequisites are CUDA indexing, kernel launches, host/device allocation, synchronization, error checking, and C++ resource lifetimes. This is the primary course home for Days 005, 006, 008, 009, 013, and 014. The earlier [transpose implementation](../../kernels/cuda_cpp/matrix_transpose/transpose_bench.cu) remains a historical reference; the complete experiment here can be reproduced independently. Study the address calculations before the profiler commands, because a counter without a model rarely tells you which source-code change to make.

**中文：** 前置知识包括 CUDA 索引、内核启动、主机设备分配、同步、错误检查及 C++ 资源生命周期。本课是 Day005、Day006、Day008、Day009、Day013 和 Day014 的主要系统化归属。之前的[转置实现](../../kernels/cuda_cpp/matrix_transpose/transpose_bench.cu) 保留为历史参考，本章完整实验可以独立复现。建议先掌握地址计算，再使用分析工具，因为没有模型支撑的计数器通常无法告诉你该修改哪段源代码。

**English:** Verified on 2026-09-18: Ubuntu 26.04.1, CUDA Toolkit 13.3.73, Nsight Compute 2026.2.1, Nsight Systems 2026.1.3, and Compute Sanitizer 2026.2.1. The RTX 4060 has a driver/NVML mismatch. We compile CUDA code and run an independent CPU index model; we do not change drivers, execute GPU kernels, invent timings, or infer speedups. The [new CUDA 13.3 Programming Guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html) is version-pinned. Nsight pages are rolling documentation checked on that date, not a guarantee that every future metric name exists in the installed release.

**中文：** 核验日期为 2026 年 9 月 18 日：环境为 Ubuntu 26.04.1、CUDA Toolkit 13.3.73、Nsight Compute 2026.2.1、Nsight Systems 2026.1.3 和 Compute Sanitizer 2026.2.1。RTX 4060 存在驱动与 NVML 不匹配。本课编译 CUDA 代码并运行独立 CPU 索引模型，不修改驱动、不运行 GPU 内核、不编造时间或推断加速比。资料固定到[新版 CUDA 13.3 编程指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html)。Nsight 网页是当日核验的滚动文档，不保证未来所有指标名称都存在于本地版本。

## 1. Define useful work and the measurement scope / 定义有效工作与测量范围

**English:** A transpose preserves values while changing their positions. For an input with height H and width W stored in row-major order, input element `(y, x)` is at `y * W + x`; its output location is `x * H + y`. The output has height W and width H. No floating-point addition is required. This makes transpose a useful memory-system experiment: an implementation can perform exactly the same mathematical operation while generating very different memory traffic and synchronization costs.

**中文：** 转置保留数值，仅改变位置。输入高度为 H、宽度为 W，采用行主序时，输入元素 `(y, x)` 位于 `y * W + x`，输出位置为 `x * H + y`，输出高度变为 W、宽度变为 H。这个操作不需要浮点加法，因此适合观察内存系统：不同实现可以完成完全相同的数学操作，却产生差别很大的内存流量与同步成本。

**English:** Distinguish useful bytes from physical traffic. Reading N float elements and writing N float elements represents `2 * N * sizeof(float)` useful bytes for an out-of-place transpose. The memory hierarchy may move additional sectors, serve accesses from cache, or perform other internal transfers. Effective bandwidth divides the useful-byte count by elapsed time; a hardware DRAM traffic counter measures a different quantity. Comparing them is informative precisely because they are not interchangeable descriptions of the same measurement.

**中文：** 要区分有效字节与物理流量。非原地转置读取 N 个浮点元素并写出 N 个，代表 `2 * N * sizeof(float)` 个有效字节。但内存层级可能传输额外扇区、从缓存满足访问，或者发生其他内部搬运。有效带宽使用有效字节除以耗时，硬件显存流量计数器则测量另一个量。比较两者有价值，恰恰因为它们不能互相替代，也不是同一项测量的不同名称。

**English:** Keep units visible. Decimal GB/s uses one billion bytes per second; GiB/s uses a power-of-two denominator. CUDA event elapsed time is expressed in milliseconds, so divide milliseconds by one thousand before obtaining seconds. A factor-of-one-thousand mistake can look like a spectacular optimization. The program prints decimal GB/s and uses double precision for the bandwidth calculation. Its numerator excludes host transfers because its timed interval excludes those transfers as well. The numerator and denominator must describe the same work scope.

**中文：** 计量单位必须可见。十进制 GB/s 按每秒十亿字节计算，GiB/s 使用二进制分母。CUDA 事件耗时以毫秒表示，计算秒数前要除以一千。一个千倍的换算错误就可能伪装成惊人的优化。程序输出十进制带宽，并用双精度计算结果。分子不包含主机传输，因为计时间隔也不包含这些传输；分子和分母必须对应同一工作范围。

**English:** Application latency is broader than kernel time. Allocation, input preparation, host-to-device transfer, launch gaps, synchronization, device-to-host transfer, and result processing may dominate a small request. If a kernel occupies one tenth of total latency, halving it saves at most one twentieth of the original total under the unchanged-rest assumption. State the user-visible objective first, then decide whether a kernel microbenchmark answers it. This course measures device execution intervals; an end-to-end application study needs a separate host-clock experiment.

**中文：** 应用延迟比内核耗时范围更大。分配、输入准备、主机传输、启动间隙、同步、结果回传和后处理，都可能支配小请求。如果内核仅占总延迟十分之一，把它减半，在其他部分不变时最多节省原总时间的二十分之一。应先说明用户可见目标，再判断内核微基准能否回答问题。本课测量设备执行区间，完整应用研究需要另外设计主机时钟实验。

## 2. Coalescing is a property of a warp access / 合并访问属于一次线程束访问

**English:** Examine the addresses requested by active lanes of one warp for one memory instruction. Consecutive float addresses generally fit into fewer memory sectors than addresses separated by a large stride. Coalescing concerns that grouping, not whether each individual thread follows a sequential loop over time. A thread can access consecutive elements on successive iterations while neighboring threads access far-apart regions at each iteration. The latter arrangement can still waste transaction capacity despite looking sequential in scalar source code.

**中文：** 分析时应观察同一线程束的活跃线程，在同一条内存指令中请求哪些地址。连续浮点地址通常能落入更少的内存扇区，而大步长地址会分散。合并访问关注这种分组，不是每个线程在时间上是否按顺序循环。某个线程可以在连续迭代中读取相邻元素，但同一次迭代中，相邻线程却访问相距很远的区域。因此，标量源码看起来顺序访问，仍然可能浪费传输容量。

**English:** For a simplified aligned model, 32 lanes each reading four bytes cover 128 useful bytes. If those bytes occupy four aligned 32-byte sectors, the sector count is small; if every lane touches a different sector, many more sectors are needed. This is an address-counting model, not a universal instruction timing formula. Active masks, alignment, access width, caches, and architecture affect the realized cost. Use it to generate a hypothesis, then inspect the relevant memory workload evidence on the actual device.

**中文：** 在简化的对齐模型中，三十二个线程各读取四字节，共覆盖一百二十八个有效字节。如果落在四个对齐的三十二字节扇区中，请求数量较少；如果每个线程都落在不同扇区，就需要更多扇区。这是地址数量模型，不是适用于所有指令的时间公式。活跃掩码、对齐、访问宽度、缓存和架构都会影响实际成本。应先用模型提出假设，再在真实设备上检查相应内存证据。

**English:** Alignment changes the set of sectors even when lane addresses remain contiguous. A subview beginning one element later can straddle an additional boundary. Rows with an awkward leading dimension can repeat such offsets across the matrix. Therefore record shape, element size, and row stride together; shape alone does not determine memory layout. The main experiment intentionally uses both tidy and untidy widths to expose assumptions hidden by power-of-two inputs. It does not claim an exact bandwidth penalty from alignment without measurement.

**中文：** 即使线程地址连续，对齐也会改变涉及哪些扇区。子视图从后一个元素开始，就可能跨越额外边界。行跨度不规则时，这种偏移会在矩阵多行重复出现。因此，应同时记录形状、元素大小与行跨度，单有形状不能决定布局。主实验刻意包含整齐和不整齐宽度，用来暴露被二次幂输入隐藏的假设，但在没有测量时，不会断言对齐必然造成某个固定带宽损失。

**English:** The linear thread order in a multidimensional block increments the x coordinate first. With a `32 × 8` block, each warp stays within one y row and spans 32 x positions, which makes row-wise float loads easy to reason about. Changing block dimensions changes the mapping of lanes to rows even when the total thread count stays fixed. Never transfer a coalescing explanation from one block shape to another without recalculating the lane addresses. See the [SIMT kernel chapter](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html) for the execution model.

**中文：** 多维线程块的线性线程顺序优先增加横坐标。使用 `32 × 8` 线程块时，每个线程束处于同一纵坐标行，横跨三十二个横坐标，便于分析逐行浮点加载。改变线程块形状，即使总线程数不变，也会改变线程束与行的对应。不能不重新计算线程地址，就把一种块形状下的合并访问解释搬到另一种形状。执行模型参见[线程级内核章节](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html)。

## 3. Why direct transpose scatters one side / 直接转置为什么会分散一侧访问

**English:** In the naive transpose, adjacent x lanes read `in[y * W + x]`, so input reads are contiguous. They write `out[x * H + y]`, making adjacent lane addresses differ by H elements. For a large height, those writes are spread across distant locations. Swapping which coordinate varies with the lane merely trades scattered writes for scattered reads. A local reordering step is needed if both global-memory sides are to follow a contiguous lane pattern.

**中文：** 朴素转置中，相邻横坐标线程读取 `in[y * W + x]`，因此输入连续；写入 `out[x * H + y]` 时，相邻线程地址相差 H 个元素。高度较大时，写请求分散到远处。把随线程变化的坐标交换，只会把分散写入换成分散读取。若希望全局内存的读写两侧都保持连续线程访问，就需要在中间增加一次局部重排，而不是仅仅更换一个索引变量。

**English:** The algorithm does not require each output element to be written by the same thread that loaded its input. Threads in a block can cooperate: load a tile in input-row order, synchronize, then let different threads read the staged values in output-row order. The block collectively preserves the permutation even though individual threads change roles. This is the conceptual purpose of shared memory here. It reorganizes access rather than reducing the mathematical number of input and output elements.

**中文：** 算法并不要求每个输出元素必须由最初加载它的那个线程写出。块内线程可以合作：先按输入行顺序加载小块，同步之后，再由不同线程按输出行顺序读取暂存数值。虽然单个线程角色改变，整个线程块仍然保持正确置换。本实验共享内存的作用正是重排访问，而不是减少数学上必须读取和写出的元素数量，不能把这种收益简单解释成少读了一遍输入。

**English:** A copy kernel is a useful reference because it can make both global reads and writes contiguous without a transpose barrier or shared-memory exchange. It uses the same useful-byte numerator, so comparing bandwidth is convenient. It is not a strict theoretical ceiling: cache state, compiler choices, instruction mix, and measurement noise can make the observed relationship less tidy. Use it as an empirical reference under the same conditions, and investigate surprising results rather than forcing every transpose value below it.

**中文：** 复制内核是有用参考，因为它可以同时连续读写全局内存，不需要转置的屏障或共享内存交换。它采用相同的有效字节分子，因此方便比较带宽。但这不是严格理论上限：缓存状态、编译器选择、指令组合和测量噪声，都可能使实际关系不那么整齐。应把它当作相同条件下的经验参考，遇到意外结果继续调查，而不是强行要求所有转置测量都低于复制。

## 4. Shared memory introduces a cooperation protocol / 共享内存引入协作协议

**English:** Shared memory is storage visible to the threads of a block during its execution. Declaring a tile reserves storage; it does not copy global data automatically. Threads explicitly populate entries and later consume them. A block barrier separates these phases so a consumer does not race ahead of the producer whose entry it needs. The address space and the synchronization protocol are distinct responsibilities: fast storage alone does not establish visibility or ordering among cooperating threads.

**中文：** 共享内存是在一个线程块执行期间供块内线程访问的存储。声明小块只是预留空间，不会自动从全局内存复制数据。线程需要显式写入条目，再在后续阶段读取。块级屏障分隔两个阶段，防止消费者跑到生产者之前，读取尚未完成的条目。地址空间与同步协议是两项独立责任，存储较快并不自动建立协作线程之间的可见性和执行顺序。

**English:** Every thread participating in this block-level protocol must reach the barrier along compatible control flow. Boundary checks therefore surround memory accesses, not the barrier itself. Returning early merely because a lane is outside the matrix can leave other lanes waiting or invalidate the cooperation assumptions. The supplied tiled kernel keeps all threads in the block alive through the barrier, while invalid lanes skip their reads and writes. Avoid an apparently convenient guard that wraps the entire body including synchronization.

**中文：** 参与这个块级协议的线程必须沿兼容控制流到达屏障。因此，边界检查应该围绕内存访问，而不是围绕屏障。仅因为某线程越过矩阵范围就提前返回，可能让其他线程等待，或者破坏协作假设。给出的分块内核让块内所有线程都经过屏障，越界线程只跳过读写。不要为了看起来方便，把整个函数体连同同步一起放到某个依线程变化的条件里面。

**English:** The tile is `32 × 32`, but the block contains only `32 × 8` threads. Each thread processes four rows separated by eight positions, so 256 threads collectively stage 1024 elements. This amortizes thread-level setup while preserving a clear warp-row mapping. The tile dimensions and the thread-block dimensions serve different purposes and need not be identical. All four benchmark variants use this same block shape and per-thread row loop to avoid confounding the comparison with a different thread count.

**中文：** 小块是 `32 × 32`，线程块却只有 `32 × 8` 个线程。每个线程处理间隔为八的四行，因此二百五十六个线程共同暂存一千零二十四个元素。这能摊薄线程级设置开销，同时保留明确的线程束逐行映射。数据小块尺寸与线程块尺寸承担不同作用，不要求相同。四个基准版本统一采用这个线程形状和逐线程行循环，避免把线程数量变化混进比较。

**English:** Shared-memory tiling has costs: extra instructions, synchronization, storage consumption, and potentially fewer resident blocks. It is attractive only if it improves another limiting part enough to compensate. Transpose illustrates access reorganization; matrix multiplication additionally illustrates reuse. A kernel that reads each input once in an already efficient pattern may gain little from copying it through shared memory. Always state what is being reused or reorganized before introducing a tile, otherwise the extra stage may simply add work.

**中文：** 共享内存分块也有成本，包括额外指令、同步、存储消耗，以及可能减少驻留块数量。只有对其他限制因素的改善足以抵偿成本时，它才有吸引力。转置展示访问重组，矩阵乘法还涉及数据复用。若一个内核本来就只读一次输入且访问已经高效，再经过共享内存搬运可能收益很小。引入小块之前，应先说明要复用或重组什么，否则新增阶段可能只是增加工作。

## 5. Bank conflicts and why padding helps / 存储体冲突与填充原理

**English:** For the scalar 32-bit access pattern used here, a useful model maps a shared-memory word index to one of 32 banks using its index modulo 32. Different addresses in the same bank can require serialized service for that access pattern. This is separate from global-memory coalescing: a tiled kernel may improve global transactions while introducing shared-memory conflicts. The model is specific to access width and layout; wider values and different instructions require a fresh analysis rather than blindly applying the same formula.

**中文：** 对本课使用的三十二位标量访问模式，可以用字索引模三十二，近似映射到三十二个存储体。同一存储体中的不同地址，在这种访问模式下可能需要串行服务。这与全局内存合并访问不同：分块内核可以改善全局事务，同时引入共享内存冲突。模型与访问宽度和布局有关，更宽数值或不同指令需要重新分析，不能不加区分地套用同一公式。

**English:** In `float tile[32][32]`, a row access by consecutive x lanes has consecutive word indices and spreads across banks. A column access `tile[lane][column]` has index `lane * 32 + column`, so all lanes map to the same bank while requesting different words. The transpose exchange changes which index varies across lanes, exposing this conflict. The source declaration itself is not inherently good or bad; the declaration and the simultaneous access pattern together determine the problem.

**中文：** 对 `float tile[32][32]`，相邻横坐标线程访问同一行时，字索引连续并分散到不同存储体。按列访问 `tile[lane][column]` 时，索引为 `lane * 32 + column`，所有线程请求不同字，却映射到同一存储体。转置交换改变了随线程变化的索引，因此暴露冲突。声明本身没有绝对好坏，声明与同一时刻的访问模式共同决定问题。

**English:** Changing the physical row width to 33 gives index `lane * 33 + column`, whose bank index cycles through all 32 banks for a full warp. The extra column is storage padding, not another mathematical matrix column. Threads still load and write only the original 32-by-32 tile. The price is 128 additional bytes of shared memory per block for float values. This small layout change specifically targets bank mapping; it does not alter the global output shape or the useful-byte count.

**中文：** 把物理行宽改成三十三之后，索引变为 `lane * 33 + column`，一个完整线程束的存储体索引会遍历全部三十二个存储体。多出的一列是存储填充，不是数学矩阵增加了一列，线程仍只加载和写出原来的小块。浮点数据下，每块增加一百二十八字节共享内存。这个小布局改动专门针对存储体映射，不改变全局输出形状，也不改变有效字节数量。

**English:** Do not confuse multiple lanes reading the same shared word with multiple lanes reading distinct words in one bank. Supported broadcast behavior makes the first situation different. Nor should a predicted conflict multiplicity be translated directly into an identical whole-kernel slowdown: other instructions, global traffic, occupancy, and scheduling remain involved. The unpadded-versus-padded comparison tests a causal hypothesis. Bank-related metrics and execution time together provide stronger evidence than either a formula or a speed ratio alone.

**中文：** 不要混淆多个线程读取同一个共享字，与多个线程读取同一存储体内不同字。受支持的广播行为使前一种情况不同。也不能把预测的冲突倍数直接当成整个内核的减速倍数，因为其他指令、全局流量、占用率与调度仍在参与。无填充和有填充的比较是在检验因果假设。存储体相关指标与执行时间共同变化，比单独公式或单独加速比更能支持解释。

## 6. Prove the boundary mapping before timing / 计时前先证明边界映射

**English:** After loading an input tile at block coordinates `(bx, by)`, the output tile belongs at exchanged block coordinates. Output x ranges along the original input y direction, and output y ranges along the original input x direction. Inside the tile, the consumer reads the transposed shared indices. Both the block-coordinate exchange and the local-index exchange are required. A kernel that performs only one exchange may look correct for selected patterns while moving whole tiles or their interiors incorrectly.

**中文：** 在块坐标 `(bx, by)` 加载输入小块之后，输出小块应放到交换后的块坐标。输出横坐标沿原输入纵坐标方向变化，输出纵坐标沿原输入横坐标方向变化；小块内部，消费者读取交换后的共享索引。块坐标交换和局部索引交换缺一不可。只做其中一种交换的内核，对某些输入模式可能看起来正确，却把整个小块或内部元素放到了错误位置。

**English:** Edge tiles contain invalid positions, but valid output consumers must only read entries produced by valid input loads. In the supplied mapping, the output guards `out_x < H` and `out_y < W` are exactly the original input-coordinate bounds of the shared entry being consumed. Thus a valid output corresponds to an initialized tile cell, even if nearby cells were skipped. This correspondence is the proof obligation; merely initializing all shared memory to zero would hide the indexing mistake instead of establishing the correct permutation.

**中文：** 边缘小块包含无效位置，但有效输出消费者只能读取由有效输入加载产生的条目。本课映射中，输出边界条件恰好对应所读取共享条目的原输入坐标边界，因此有效输出一定对应已经初始化的小块单元，即使邻近位置被跳过。需要证明的是这种对应关系；简单把共享内存全部清零，可能掩盖索引错误，却不能证明置换正确，更不能让本来缺失的数据凭空出现。

**English:** Test shapes that attack assumptions: one element, a single row, a single column, dimensions just below and just above 32, a rectangular odd shape, and a large aligned square. A square alone hides confusion between width and height; a multiple-of-32 case hides missing boundary checks. Data should vary across positions rather than fill the matrix with one constant. The CPU reference computes the mathematical permutation independently, and the device output is filled with a sentinel before validation so missed writes cannot borrow old correct values.

**中文：** 测试形状要主动攻击假设：一个元素、单行、单列、略小于和略大于三十二的尺寸、长宽不同的奇数矩形，以及大对齐方阵。只测方阵会隐藏宽高混淆，只测三十二倍数会隐藏边界检查缺失。数据要随位置变化，不能整块填同一个常量。CPU 参考独立计算数学置换，设备输出在验证前填入哨兵，防止漏写位置借用上次留下的正确值蒙混通过。

## 7. Timing repeated work without changing the question / 重复计时但不偷换问题

**English:** CUDA launches are asynchronous with respect to the host, so a CPU timer surrounding only a launch mostly observes submission. Device events recorded around work in the same stream give a device timeline interval once the stop event has completed. The program synchronizes the stop event before reading elapsed time and checks launch and completion errors. The [event API reference](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html) defines these operations. A host timer is appropriate for end-to-end latency only when its interval includes the intended completion condition.

**中文：** CUDA 启动相对主机异步，因此只在启动前后使用 CPU 计时器，主要观察提交开销。把设备事件放在同一条流中包围工作，等结束事件完成后，就能取得设备时间线区间。程序在读取耗时前同步结束事件，并检查启动和完成错误。这些操作依据[事件接口文档](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html)。主机时钟适合端到端延迟，但区间必须包含预期的完成条件。

**English:** Warmup removes some first-use effects from the chosen steady-state question, such as initialization and module loading, but does not make all runs identical. Temperature, clocks, cache contents, competing processes, and operating conditions can still vary. The experiment performs five warmup launches and seven measured batches, then reports the median batch-average time with minimum and maximum. Record those conditions with the result. If the user cares about first-request latency, measure it separately rather than calling warmup an automatic improvement in measurement truth.

**中文：** 预热可以从所选择的稳态问题中排除部分首次使用影响，例如初始化和模块加载，但不会让所有运行完全相同。温度、频率、缓存、竞争进程与运行条件仍可能变化。实验预热五次，再测七批，报告批平均耗时的中位数及最小最大值。记录结果时应附上条件。如果用户关注首个请求延迟，应另外测量，不能把预热当作无条件提升真实性的操作，因为它已经改变所回答的问题。

**English:** Repeating launches between two events amortizes event timing overhead, but host submission gaps can still appear on the device timeline when kernels are very short. Dividing by the repetition count yields the average interval per submitted kernel under this protocol, not a magical isolation of every kernel instruction. A timeline profiler can reveal whether the GPU waits between launches. Comparing CUDA Graph replay would be a separate experiment with a different submission mechanism, not a silent replacement of the benchmark halfway through a comparison.

**中文：** 两个事件之间重复启动可以摊薄事件计时开销，但内核很短时，主机提交间隙仍可能进入设备时间线。除以重复次数得到的是当前协议下每次提交工作的平均区间，不是神奇地剥离所有其他因素后的纯指令时间。时间线工具可以判断启动之间 GPU 是否等待。若比较图重放，应作为另一种提交机制的独立实验，不能在两个实现比较到一半时，悄悄替换其中一个的基准方式。

**English:** Reusing the same input and output allocations favors a warm-cache experiment. If the working set fits relevant caches, effective bandwidth can exceed a simple DRAM specification comparison without violating physics. To study streaming DRAM behavior, deliberately vary working-set size or rotate buffers and document that protocol. Do not label the current experiment as a cold-memory test. Profiled replay may also change cache state, so preserve ordinary timing results separately from timings collected under profiling.

**中文：** 重复使用相同输入输出分配，更接近热缓存实验。如果工作集能容纳在相关缓存中，有效带宽可能超过简单对照的显存规格，而没有违反物理规律。研究流式显存行为时，应主动改变工作集大小或轮换缓冲区，并记录协议。不能把当前实验标成冷内存测试。分析器重放也可能改变缓存状态，所以应把普通运行计时与分析器下的时间分开保留，避免混合不同测量条件。

## 8. Occupancy and the register tradeoff / 占用率与寄存器权衡

**English:** Theoretical occupancy describes resident active warps relative to the architecture's maximum resident warps per multiprocessor. Block size, registers, shared memory, and block limits can constrain residency. It does not count how many warps are ready to issue useful work at every moment. A kernel can have many resident warps that all wait on the same dependency, or perform well with fewer warps because it exposes independent instructions and efficient accesses. The denominator belongs to the actual architecture, not a memorized number from another GPU.

**中文：** 理论占用率描述每个多处理器驻留活跃线程束数量，相对于架构允许最大驻留数量的比例。线程块大小、寄存器、共享内存和块数上限都可能限制驻留。它不表示每个时刻有多少线程束准备好发射有效工作。大量驻留线程束可能等待同一类依赖；较少线程束也可能因指令独立性和访问效率而表现良好。分母必须来自实际架构，不能套用记忆中另一块 GPU 的数字。

**English:** Registers allow a thread to keep values close to execution, but more registers per thread can reduce the number of simultaneously resident blocks. Artificially limiting registers may raise occupancy while forcing spills to local memory, which is backed by the memory hierarchy rather than a free private scratchpad. Therefore compare elapsed time, register count, spill evidence, and occupancy together. A lower register count is not itself success, just as a higher occupancy percentage is not an application objective.

**中文：** 寄存器让线程把数值保存在接近执行的位置，但每线程使用更多寄存器，可能减少同时驻留的线程块。人为限制寄存器可能提高占用率，却迫使数值溢出到局部内存；局部内存由内存层级支撑，不是免费的线程私有暂存区。因此应同时比较耗时、寄存器数量、溢出证据和占用率。寄存器少不自动代表成功，占用率高也不是应用目标本身。

**English:** Padding increases static shared memory from 4096 to 4224 bytes in this example. The change is small, but residency limits are discrete: crossing a resource threshold can reduce active blocks abruptly. Compiler-generated register differences may matter too. The program queries function attributes and an occupancy estimate rather than inferring identical residency from similar source code. The [occupancy API](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__OCCUPANCY.html) provides a resource-based estimate, not a replacement for measured performance.

**中文：** 本例填充把静态共享内存从四千零九十六字节增加到四千二百二十四字节。变化虽小，驻留限制却是离散的，跨过某个资源阈值就可能突然减少活跃块数。编译器产生的寄存器差异也可能重要。程序查询函数属性和占用率估计，不会因为源码相似就假定驻留一样。[占用率接口](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__OCCUPANCY.html) 给出基于资源的估计，不能替代实际性能测量。

**English:** Begin tuning with a small parameter set and an explicit hypothesis. For example, changing rows-per-block changes how many elements each thread handles, instruction overhead, thread count, and perhaps registers. That is a new family of kernels, so preserve the original comparison before exploring it. Use compiler resource reports to screen implausible choices, then benchmark valid candidates. Avoid trying every flag at once, because a faster result with no attributable mechanism is difficult to maintain or reproduce on another architecture.

**中文：** 调优应从少量参数和明确假设开始。例如，改变每块线程行数，会同时改变每线程处理元素数、指令开销、线程数量，甚至寄存器用量。这已经是新的一组内核，因此探索前要先保留原始对照。可以通过编译资源报告筛掉不合理选项，再测量有效候选。不要一次修改所有选项，否则即使变快，也很难把原因归属于具体机制，更难在另一种架构上维护和复现。

## 9. Use the two profilers for different questions / 用两类分析器回答不同问题

**English:** Nsight Systems is the first tool for a whole-application timeline: when the CPU submits work, when copies and kernels execute, where synchronization occurs, and whether streams overlap. It helps decide whether kernel optimization is relevant to the application bottleneck. Long GPU-idle intervals may reflect host preparation or dependency scheduling rather than a slow kernel. The [Systems user guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) is rolling documentation, so record the installed tool version and supported trace options with a saved report.

**中文：** Nsight Systems 首先用于整个应用的时间线：CPU 何时提交，复制和内核何时执行，哪里同步，以及多条流是否重叠。它帮助判断内核优化是否对应用瓶颈有意义。长时间 GPU 空闲可能来自主机准备或依赖调度，而不是某个内核太慢。[Systems 用户指南](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) 持续更新，因此保存报告时应同时记录本地工具版本及受支持的跟踪选项。

**English:** Nsight Compute examines selected kernels in detail: memory workload, execution resources, scheduling, instructions, and limiting pipelines. Start from a small section set and one representative launch rather than collecting every possible metric for the entire application. Some metrics require replay, which can perturb timing and cache state. Read the [profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html) to understand that measurement process, and confirm available sections locally before constructing a command from a newer webpage.

**中文：** Nsight Compute 详细观察选中的内核，包括内存工作负载、执行资源、调度、指令和受限流水线。应先用少量分析章节及一个代表性启动，而不是为整个应用收集所有可能指标。部分指标需要重放，会影响时间和缓存状态。应通过[分析指南](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html) 理解测量过程，在照搬较新网页命令之前，先确认本地有哪些可用章节。

**English:** Tie each report to a falsifiable claim. If shared tiling fixes scattered global writes, inspect sectors or traffic relative to useful bytes and compare time. If padding fixes bank conflicts, inspect shared-memory conflict or excessive-wavefront evidence while checking that global work remains equivalent. If occupancy changes, identify the limiting resource. A report containing many percentages is not yet an explanation; the explanation connects an address pattern, a hardware consequence, and an observed timing change under controlled conditions.

**中文：** 每份报告都应对应可被推翻的判断。若认为共享分块修复了分散全局写入，就检查相对有效字节的扇区或流量，并比较时间；若认为填充修复冲突，就检查共享内存冲突或额外波次证据，同时确认全局工作等价；若占用率变化，就指出限制资源。很多百分比堆在一起不构成解释，解释需要把地址模式、硬件后果和受控条件下的时间变化连接起来。

**English:** Profiling permission failures are environment findings, not kernel performance findings. Preserve the exact error, tool version, target executable, and requested sections. Do not silently change machine-wide performance-counter permissions or drivers as part of this lesson. Likewise, a sanitizer failure invalidates performance conclusions for that program until corrected. The correct sequence is build, validate functional behavior, check relevant memory/synchronization properties, measure ordinary execution, then use profiling to explain the result.

**中文：** 分析权限失败属于环境发现，不属于内核性能发现。应保留原始错误、工具版本、目标程序与请求章节。本课不会悄悄修改整机性能计数器权限或驱动。同样，检测器报错意味着在修复前，该程序的性能结论没有可靠基础。正确顺序是构建、验证功能、检查相关内存与同步性质、测量普通执行，最后用分析报告解释结果，而不是跳过正确性直接追求漂亮数字。

## 10. Roofline and reduction as reasoning exercises / Roofline 与归约推理

**English:** Arithmetic intensity is useful operations divided by bytes transferred at a specified memory level. A roofline model bounds attainable throughput by the smaller of a compute limit and bandwidth multiplied by intensity. The word specified matters: a DRAM roofline uses DRAM traffic, while an L2-oriented analysis concerns another boundary. Mixing a useful-byte numerator from source code with an unrelated measured memory level can produce a misleading point. State precision, operation-count convention, memory level, and whether ceilings are measured or theoretical.

**中文：** 算术强度是在指定内存层级下，有效运算数量除以传输字节。Roofline 模型用计算上限与带宽乘强度中的较小者，约束可达到的吞吐。指定层级非常重要：显存模型使用显存流量，二级缓存分析对应另一条边界。把源码有效字节与不相干层级的测量混用，会画出误导性位置。必须说明数值精度、运算计数规则、内存层级，以及上限来自实测还是理论规格。

**English:** Transpose performs essentially no useful floating-point arithmetic, so a FLOP/s chart is not its most informative primary display. Its useful-byte bandwidth and transaction efficiency are clearer. An FMA-heavy matrix multiplication has a different intensity and may approach a compute roof. Do not conclude that every low-intensity kernel saturates DRAM: insufficient parallel work, instruction overhead, latency, or dependencies may keep it far below the bandwidth ceiling. Roofline supplies a bound and a classification aid, not a complete causal diagnosis.

**中文：** 转置基本没有有效浮点运算，因此以浮点吞吐图作为主要展示并不合适，有效带宽和事务效率更清楚。大量融合乘加的矩阵乘法具有不同强度，可能接近计算上限。也不能推断所有低强度内核都能吃满显存带宽：并行工作不足、指令开销、延迟或依赖，都可能让它远低于带宽上限。Roofline 提供边界与分类帮助，却不是完整的因果诊断。

**English:** A sum reduction reads many values and produces fewer values. A first stage can assign contiguous input regions to blocks, accumulate per-thread partial sums, then combine them within a block. A second stage combines block results. Count the intermediate writes and later reads when calculating useful bytes for the complete algorithm; counting only the original input understates the work. Conversely, charging the full input to every reduction stage exaggerates traffic. Draw each stage and its input/output sizes before deriving an intensity estimate.

**中文：** 求和归约读取很多数值，产生较少结果。第一阶段可以把连续输入区域交给线程块，先逐线程累积，再在块内合并；第二阶段合并各块结果。计算完整算法有效字节时，要包含中间写入及后续读取，仅计最初输入会低估工作。反过来，把完整输入流量算到每个归约阶段又会高估。应先画出每阶段及输入输出尺寸，再推导强度，而不是记忆一个万能归约字节公式。

**English:** Optimizing reduction exposes additional tradeoffs. More values per thread can reduce block count and synchronization, but may increase dependency-chain length or register use. Warp shuffles can replace some shared exchanges, but participating lanes and masks must match the algorithm, especially for partial warps. Floating-point addition is not associative, so changing the tree can change rounding. Validate with a reference and a justified tolerance, not the exact-equality check appropriate for our value-preserving transpose. These are algorithm-specific correctness requirements, not profiling details.

**中文：** 优化归约会暴露更多权衡。每线程处理更多数值，可以减少块数和同步，却可能增加依赖链长度或寄存器使用。线程束交换可以替代部分共享交换，但参与线程和掩码必须符合算法，尤其是非完整线程束。浮点加法不满足结合律，因此改树形会改变舍入。应采用参考结果与合理容差，不能照搬本课保值转置的精确相等检查。这些属于算法正确性要求，而不是分析器细节。

## 11. Complete transpose experiment / 完整转置实验

**English:** The following block creates one source file in a fresh temporary directory and compiles for `sm_89`, the target used for the RTX 4060 study. An explicit architecture avoids runtime discovery during compilation. It does not establish that the current driver can execute the result. The three transpose kernels and the copy reference share block shape, grid coverage, input, output allocation, and timing protocol. The only padding difference is the shared-memory leading dimension in the two instantiations of `tiled_transpose`.

**中文：** 下方代码块在新临时目录创建一个源文件，并针对 RTX 4060 研究使用的 `sm_89` 编译。显式架构避免编译期间依赖运行时设备发现，但不证明当前驱动能执行结果。三个转置内核与复制参考共享线程形状、网格覆盖、输入、输出分配和计时协议。两种分块实例之间，填充差异只体现在共享内存的行跨度，便于把比较聚焦到具体布局机制。

```bash
COURSE06_DIR=$(mktemp -d /tmp/course06.XXXXXX)
cd "$COURSE06_DIR"
cat > transpose.cu <<'CUDA'
#include <cuda_runtime.h>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int TILE = 32;
constexpr int ROWS = 8;

void check(cudaError_t status, const char* expression) {
    if (status != cudaSuccess)
        throw std::runtime_error(std::string(expression) + ": " +
                                 cudaGetErrorString(status));
}
#define CHECK(call) check((call), #call)

void cleanup(cudaError_t status, const char* operation) noexcept {
    if (status != cudaSuccess)
        std::fprintf(stderr, "cleanup %s: %s\n", operation,
                     cudaGetErrorString(status));
}

struct DeviceArray {
    float* data = nullptr;
    explicit DeviceArray(std::size_t bytes) { CHECK(cudaMalloc(&data, bytes)); }
    ~DeviceArray() { if (data) cleanup(cudaFree(data), "cudaFree"); }
    DeviceArray(const DeviceArray&) = delete;
    DeviceArray& operator=(const DeviceArray&) = delete;
};

struct Stream {
    cudaStream_t value{};
    Stream() { CHECK(cudaStreamCreateWithFlags(&value, cudaStreamNonBlocking)); }
    ~Stream() { cleanup(cudaStreamDestroy(value), "cudaStreamDestroy"); }
    Stream(const Stream&) = delete;
    Stream& operator=(const Stream&) = delete;
};

struct Event {
    cudaEvent_t value{};
    Event() { CHECK(cudaEventCreate(&value)); }
    ~Event() { cleanup(cudaEventDestroy(value), "cudaEventDestroy"); }
    Event(const Event&) = delete;
    Event& operator=(const Event&) = delete;
};

__global__ void copy_rows(const float* input, float* output, int width, int height) {
    const int x = blockIdx.x * TILE + threadIdx.x;
    const int y = blockIdx.y * TILE + threadIdx.y;
    for (int j = 0; j < TILE; j += ROWS)
        if (x < width && y + j < height) {
            const std::size_t i = std::size_t(y + j) * width + x;
            output[i] = input[i];
        }
}

__global__ void naive_transpose(const float* input, float* output,
                                int width, int height) {
    const int x = blockIdx.x * TILE + threadIdx.x;
    const int y = blockIdx.y * TILE + threadIdx.y;
    for (int j = 0; j < TILE; j += ROWS)
        if (x < width && y + j < height)
            output[std::size_t(x) * height + y + j] =
                input[std::size_t(y + j) * width + x];
}

template<int PAD>
__global__ void tiled_transpose(const float* input, float* output,
                                int width, int height) {
    __shared__ float tile[TILE][TILE + PAD];
    const int input_x = blockIdx.x * TILE + threadIdx.x;
    const int input_y = blockIdx.y * TILE + threadIdx.y;
    for (int j = 0; j < TILE; j += ROWS)
        if (input_x < width && input_y + j < height)
            tile[threadIdx.y + j][threadIdx.x] =
                input[std::size_t(input_y + j) * width + input_x];

    __syncthreads();

    const int output_x = blockIdx.y * TILE + threadIdx.x;
    const int output_y = blockIdx.x * TILE + threadIdx.y;
    for (int j = 0; j < TILE; j += ROWS)
        if (output_x < height && output_y + j < width)
            output[std::size_t(output_y + j) * height + output_x] =
                tile[threadIdx.x][threadIdx.y + j];
}

void verify(const std::vector<float>& actual, const std::vector<float>& expected) {
    for (std::size_t i = 0; i < actual.size(); ++i)
        if (!std::isfinite(actual[i]) || actual[i] != expected[i])
            throw std::runtime_error("result mismatch at element " +
                                     std::to_string(i));
}

template<class Kernel>
void benchmark(const char* name, Kernel kernel, const DeviceArray& input,
               DeviceArray& output, const std::vector<float>& reference,
               std::vector<float>& actual, int width, int height,
               int repetitions, cudaStream_t stream, const cudaDeviceProp& prop) {
    const std::size_t bytes = reference.size() * sizeof(float);
    const dim3 block(TILE, ROWS);
    const dim3 grid((width + TILE - 1) / TILE, (height + TILE - 1) / TILE);
    auto launch = [&] {
        kernel<<<grid, block, 0, stream>>>(input.data, output.data, width, height);
    };

    CHECK(cudaMemsetAsync(output.data, 0xff, bytes, stream));
    launch();
    CHECK(cudaGetLastError());
    CHECK(cudaStreamSynchronize(stream));
    CHECK(cudaMemcpy(actual.data(), output.data, bytes, cudaMemcpyDeviceToHost));
    verify(actual, reference);

    for (int i = 0; i < 5; ++i) launch();
    CHECK(cudaGetLastError());
    CHECK(cudaStreamSynchronize(stream));

    Event start, stop;
    std::vector<double> samples;
    for (int batch = 0; batch < 7; ++batch) {
        CHECK(cudaEventRecord(start.value, stream));
        for (int i = 0; i < repetitions; ++i) launch();
        CHECK(cudaGetLastError());
        CHECK(cudaEventRecord(stop.value, stream));
        CHECK(cudaEventSynchronize(stop.value));
        float elapsed_ms = 0;
        CHECK(cudaEventElapsedTime(&elapsed_ms, start.value, stop.value));
        if (!(elapsed_ms > 0))
            throw std::runtime_error("nonpositive timing; increase repetitions");
        samples.push_back(double(elapsed_ms) / repetitions);
    }
    CHECK(cudaMemcpy(actual.data(), output.data, bytes, cudaMemcpyDeviceToHost));
    verify(actual, reference);
    std::sort(samples.begin(), samples.end());
    const double median_ms = samples[samples.size() / 2];
    const double bandwidth = (2.0 * double(bytes)) / (median_ms * 1.0e6);

    cudaFuncAttributes attributes{};
    CHECK(cudaFuncGetAttributes(&attributes, kernel));
    int active_blocks = 0;
    CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(
        &active_blocks, kernel, TILE * ROWS, 0));
    const double occupancy = 100.0 * active_blocks * TILE * ROWS /
                             prop.maxThreadsPerMultiProcessor;
    std::cout << width << ',' << height << ',' << name << ','
              << std::fixed << std::setprecision(6) << median_ms << ','
              << samples.front() << ',' << samples.back() << ','
              << std::setprecision(3) << bandwidth << ','
              << attributes.numRegs << ',' << attributes.sharedSizeBytes << ','
              << occupancy << ",pass\n";
}

int parse_positive(const char* text, int maximum) {
    std::size_t consumed = 0;
    const std::string value(text);
    const long result = std::stol(value, &consumed);
    if (consumed != value.size() || result < 1 || result > maximum)
        throw std::invalid_argument("argument outside accepted range");
    return static_cast<int>(result);
}

int main(int argc, char** argv) {
    try {
        if (argc > 5)
            throw std::invalid_argument("usage: transpose width height repetitions variant");
        const int width = argc > 1 ? parse_positive(argv[1], 8192) : 1024;
        const int height = argc > 2 ? parse_positive(argv[2], 8192) : 1024;
        const int repetitions = argc > 3 ? parse_positive(argv[3], 100000) : 50;
        const std::string variant = argc > 4 ? argv[4] : "all";
        if (variant != "all" && variant != "copy" && variant != "naive" &&
            variant != "tiled" && variant != "padded")
            throw std::invalid_argument("variant must be all/copy/naive/tiled/padded");

        CHECK(cudaSetDevice(0));
        cudaDeviceProp prop{};
        CHECK(cudaGetDeviceProperties(&prop, 0));
        std::cerr << "device=" << prop.name << " cc=" << prop.major << '.'
                  << prop.minor << " repetitions=" << repetitions
                  << " warmup=5 batches=7\n";

        const std::size_t count = std::size_t(width) * height;
        const std::size_t bytes = count * sizeof(float);
        std::vector<float> input(count), reference(count), actual(count);
        for (std::size_t i = 0; i < count; ++i)
            input[i] = float((i * 37u + i / width) % 1048573u);
        for (int y = 0; y < height; ++y)
            for (int x = 0; x < width; ++x)
                reference[std::size_t(x) * height + y] =
                    input[std::size_t(y) * width + x];

        Stream stream;
        DeviceArray device_input(bytes), device_output(bytes);
        CHECK(cudaMemcpy(device_input.data, input.data(), bytes, cudaMemcpyHostToDevice));
        std::cout << "width,height,variant,median_ms,min_ms,max_ms,effective_GBps,"
                     "registers,static_shared_bytes,estimated_occupancy_pct,correct\n";
        auto selected = [&](const char* name) { return variant == "all" || variant == name; };
        if (selected("copy"))
            benchmark("copy", copy_rows, device_input, device_output, input,
                      actual, width, height, repetitions, stream.value, prop);
        if (selected("naive"))
            benchmark("naive", naive_transpose, device_input, device_output, reference,
                      actual, width, height, repetitions, stream.value, prop);
        if (selected("tiled"))
            benchmark("tiled", tiled_transpose<0>, device_input, device_output, reference,
                      actual, width, height, repetitions, stream.value, prop);
        if (selected("padded"))
            benchmark("padded", tiled_transpose<1>, device_input, device_output, reference,
                      actual, width, height, repetitions, stream.value, prop);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
CUDA
nvcc -std=c++17 -O3 -lineinfo -arch=sm_89 -Xptxas=-v transpose.cu -o transpose
```

**English:** The program validates arguments before its first CUDA Runtime call, caps dimensions to keep arithmetic bounded, and uses size-based offsets for element indexing. Every device output is compared with a CPU result both before and after timing. Exact comparison is appropriate because these kernels move exactly representable finite float values without arithmetic. The byte sentinel is expected to look non-finite when a float output is missed, but the independent element comparison remains the primary correctness check.

**中文：** 程序在第一次 CUDA Runtime 调用之前验证参数，通过尺寸上限约束算术范围，并用适合尺寸的类型计算元素偏移。每个设备输出在计时前后都与 CPU 结果逐元素比较。这些内核只移动可精确表示的有限浮点数，不进行数值运算，因此适合精确比较。字节哨兵预期让漏写的浮点输出表现为非有限值，但独立的逐元素参考比较仍然是主要正确性检查，不能只靠哨兵判断。

**English:** Resource wrappers pair allocations, streams, and events with cleanup. Normal timed batches complete before result copies and eventual release. Cleanup failures are printed rather than thrown from destructors. This is enough scaffolding for a bounded experiment, not a complete production recovery strategy after arbitrary device failures. The printed occupancy is a theoretical resource estimate, and the printed bandwidth is the effective-byte measure defined earlier. The output deliberately does not contain an invented physical DRAM throughput estimate. Physical DRAM throughput would require separate hardware measurements.

**中文：** 资源包装把分配、流和事件与清理配对。正常计时批次在结果复制和最终释放前完成，析构清理失败时打印错误而不抛出。这些支撑适用于范围受控的实验，不是任意设备故障后的完整生产恢复策略。输出的占用率是理论资源估计，带宽是前面定义的有效字节口径。程序刻意不从这些数值杜撰物理显存吞吐，因为那需要另外的硬件测量。

### CPU-only mapping check / 仅使用 CPU 的映射检查

**English:** The independent Python model below assigns each input a unique integer identity, simulates tile producers and consumers, and rejects any valid output that reads an uninitialized tile cell. It also verifies one write per output and compares the final permutation with the mathematical reference. This catches indexing and boundary reasoning mistakes without a GPU. It cannot validate device barriers, generated instructions, bank-conflict timing, or driver behavior, because it deliberately executes phases sequentially on the CPU.

**中文：** 下面的独立 Python 模型给每个输入分配唯一整数身份，模拟小块生产者与消费者，并拒绝任何有效输出读取未初始化单元的情况。它还验证每个输出恰好写一次，并与数学参考置换比较。这能在没有 GPU 时发现索引和边界推理错误，但不能验证设备屏障、生成指令、冲突耗时或驱动行为，因为它明确在 CPU 上顺序执行两个阶段，不能冒充并发硬件实验。

```bash
cat > check_mapping.py <<'PY'
from collections import Counter


def check(width, height, pad):
    result = [None] * (width * height)
    writes = [0] * len(result)
    for by in range((height + 31) // 32):
        for bx in range((width + 31) // 32):
            tile = [[None] * (32 + pad) for _ in range(32)]
            for ty in range(8):
                for tx in range(32):
                    for j in range(0, 32, 8):
                        x, y = bx * 32 + tx, by * 32 + ty + j
                        if x < width and y < height:
                            tile[ty + j][tx] = y * width + x
            for ty in range(8):
                for tx in range(32):
                    for j in range(0, 32, 8):
                        x, y = by * 32 + tx, bx * 32 + ty + j
                        if x < height and y < width:
                            value = tile[tx][ty + j]
                            assert value is not None
                            index = y * height + x
                            result[index] = value
                            writes[index] += 1
    expected = [y * width + x for x in range(width) for y in range(height)]
    assert result == expected
    assert all(count == 1 for count in writes)


shapes = [(1, 1), (1, 65), (65, 1), (31, 33), (33, 65), (257, 129)]
for shape in shapes:
    for padding in (0, 1):
        check(*shape, padding)
for leading in (32, 33):
    banks = Counter((lane * leading) % 32 for lane in range(32))
    print(f"leading={leading}, distinct_banks={len(banks)}, max_words={max(banks.values())}")
print("CPU index model: 12 shape/layout checks passed; no GPU timing")
PY
python3 check_mapping.py

if ./transpose 0 33 10 all; then
    printf '%s\n' 'ERROR: invalid width was accepted'
    exit 1
else
    printf '%s\n' 'Expected argument rejection before any CUDA Runtime call'
fi
```

**English:** Expected CPU model output follows. The bank counts describe the simplified 32-bit column-address model; they are not measured conflict counters or a prediction that the padded kernel will be exactly 32 times faster. The invalid-width command checks the host argument path and returns before device initialization. These are the only executable runs performed for this chapter in the current environment; the compiled GPU paths remain unexecuted. They therefore have no measured GPU correctness or performance results.

**中文：** 下方是 CPU 模型的预期输出。存储体数量描述简化的三十二位列地址模型，不是实测冲突计数器，也不预测填充版恰好快三十二倍。零宽度命令检查主机参数路径，在设备初始化之前返回。当前环境下，本章实际执行的仅是这些 CPU 路径；已经编译的 GPU 路径仍未运行，因此不能给它们填写实际正确性或性能结论。

```text
leading=32, distinct_banks=1, max_words=32
leading=33, distinct_banks=32, max_words=1
CPU index model: 12 shape/layout checks passed; no GPU timing
```

### GPU runs when the runtime is available / 运行环境可用之后的 GPU 实验

**English:** The next commands are a runbook for a working CUDA machine, not results from this session. Start with the edge cases and sanitizer checks, then run the larger timing cases. Keep dimensions and repetition counts alongside the output files. The program accepts one variant for profiler isolation and `all` for a direct comparison. When testing another GPU architecture, rebuild with the appropriate target rather than assuming the compiled `sm_89` binary is universally portable.

**中文：** 接下来的命令是可用 CUDA 机器上的运行手册，不是本次会话结果。先跑边界案例和检测器，再运行较大的计时案例。保存输出时，同时保留尺寸和重复次数。程序支持选择单个版本以隔离分析，也支持一次对比全部版本。测试其他架构时应重新选择适当目标构建，不能假定针对 `sm_89` 生成的程序能够无条件在所有设备运行。

```bash
./transpose 1 1 20 all
./transpose 1 65 20 all
./transpose 65 1 20 all
./transpose 31 33 20 all
./transpose 33 65 20 all
./transpose 257 129 50 all
compute-sanitizer --tool memcheck ./transpose 33 65 1 all
compute-sanitizer --tool racecheck ./transpose 33 65 1 padded
compute-sanitizer --tool synccheck ./transpose 33 65 1 padded
./transpose 1024 1024 100 all > transpose_1024.csv
./transpose 4096 4096 100 all > transpose_4096.csv
./transpose 4099 2053 100 all > transpose_odd.csv
```

**English:** Use a results table that separates evidence categories. `TBD` means no device measurement exists; it is not zero, an estimate, or a failed performance result. Preserve the raw CSV before summarizing speed ratios, and attach GPU model, architecture, clocks or power conditions where available, toolkit, driver, flags, and the cache/repetition protocol. If two runs differ substantially, repeat under understood conditions and report the range rather than selecting the most flattering number.

**中文：** 结果表应区分证据类别。`TBD` 表示尚无设备测量，不是零、估计值，也不是性能失败。计算加速比之前先保存原始 CSV，并附上 GPU 型号、架构、可获得的频率或功耗条件、工具包、驱动、选项，以及缓存与重复协议。如果两次结果差异明显，应在理解条件之后重测并报告范围，而不是挑一个最好看的数值。真实空白比伪造精度更有分析价值。

| Variant / 版本 | GPU correctness / GPU 正确性 | Median ms / 中位耗时 | Effective GB/s / 有效带宽 | Evidence / 证据 |
| --- | --- | --- | --- | --- |
| Copy / 复制 | TBD | TBD | TBD | Compiled only / 仅编译 |
| Naive / 朴素转置 | TBD | TBD | TBD | Compiled only / 仅编译 |
| Tiled / 无填充分块 | TBD | TBD | TBD | CPU index model only / 仅 CPU 索引模型 |
| Padded / 有填充分块 | TBD | TBD | TBD | CPU index model only / 仅 CPU 索引模型 |

## 12. Profiling runbook and failure analysis / 分析工具手册与失败分析

**English:** Inspect installed section names before collecting detailed Compute data. The commands use a single selected variant so the first launch of the process is representative of that implementation. A launch count of one avoids collecting every benchmark repetition; its profiling conditions differ from the ordinary seven-batch timer. For comparable kernel-counter studies, use the same capture position and cache-control policy for all variants. Use the [Compute CLI reference](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html) for version-specific filtering and replay options. Do not substitute a single profiled launch time for the ordinary benchmark median.

**中文：** 收集详细 Compute 数据之前，先检查本地章节名称。命令只选择一个实现，因此进程中的第一次启动就属于该实现。限制一次启动，避免收集所有基准重复，但其分析条件与普通七批计时不同。比较内核计数器时，各版本应使用相同捕获位置和缓存控制策略。版本相关的过滤与重放选项参见 [Compute 命令行文档](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html)，不能把分析器下的一次启动时间直接替代普通基准中位数。

```bash
nsys --version
ncu --version
ncu --list-sections
nsys profile --trace=cuda --sample=none -o transpose_timeline \
    ./transpose 4096 4096 20 padded
nsys stats transpose_timeline.nsys-rep
ncu --set basic --launch-count 1 -o transpose_naive \
    ./transpose 4096 4096 20 naive
ncu --set basic --launch-count 1 -o transpose_tiled \
    ./transpose 4096 4096 20 tiled
ncu --set basic --launch-count 1 -o transpose_padded \
    ./transpose 4096 4096 20 padded
```

**English:** After confirming local availability, add focused memory-workload, occupancy, and speed-of-light sections through the interface or `--section`. Avoid hard-coding a long list of low-level counter names from a different chip. First compare global transaction efficiency between naive and tiled, then shared-memory behavior between tiled and padded. If padding changes time without the expected shared-memory evidence, consider occupancy, compilation differences, cache effects, and experimental variance. A good optimization explanation survives this attempt to find competing causes.

**中文：** 确认本地存在之后，可以通过界面或章节选项添加针对性的内存工作负载、占用率与理论资源利用章节。不要从另一款芯片抄来很长的底层计数器名称。先比较朴素与分块的全局事务效率，再比较无填充与有填充的共享行为。如果填充改变时间，却没有预期共享证据，应考虑占用率、编译差异、缓存及实验波动。好的优化解释应当经得起寻找竞争原因，而不是只接受支持自己的数字。

**English:** Diagnose common failures by their first reliable symptom. A mismatch only on rectangles suggests swapped dimensions or output stride; failures only on edge tiles suggest guards or producer/consumer correspondence; synchronization diagnostics suggest divergent barriers; unrealistically high bandwidth suggests units, cache scope, or an incomplete interval. A missing GPU or driver mismatch stops device validation before any of these performance hypotheses can be tested. Record the limitation and retain compilation and CPU-model evidence as separate, narrower accomplishments.

**中文：** 诊断常见失败时，应从第一个可靠症状出发。仅矩形错误，提示宽高或输出跨度混淆；仅边缘小块错误，提示边界条件或生产消费对应；同步诊断提示分歧屏障；高得不合理的带宽提示单位、缓存范围或计时未覆盖完成。找不到 GPU 或驱动不匹配，则会在检验这些性能假设之前阻止设备验证。应记录限制，把编译与 CPU 模型证据保留为范围更窄的独立成果。

## 13. Ten exercises with reference solutions / 十道练习与参考解答

### Exercise 1: Count useful bytes / 练习一：计算有效字节

**English:** Exercise: A 1024-by-1024 float transpose takes a hypothetical 0.10 milliseconds. Compute useful bytes and decimal effective GB/s. Does that number describe host-to-device traffic or prove a specific physical DRAM throughput? The timing is an exercise input, not a measurement.

**中文：** 练习：一个宽高均为一千零二十四的浮点转置，假设耗时零点一毫秒。计算有效字节与十进制有效带宽。该数值是否描述主机传输，或证明具体显存吞吐？这里的耗时仅为计算题输入，不是测量。

**English:** Reference solution: There are 1,048,576 elements and 4,194,304 bytes in one matrix. One read plus one write gives 8,388,608 useful bytes. Dividing by 0.0001 seconds and by one billion gives 83.88608 GB/s. This excludes host transfers and counts algorithmic useful traffic, not hardware DRAM transactions. A different cache state could change physical traffic without changing this numerator. Label the value as a hypothetical effective-bandwidth calculation and do not insert it into the experiment's results table.

**中文：** 参考解答：共有一百零四万八千五百七十六个元素，单矩阵为四百一十九万四千三百零四字节。一读一写产生八百三十八万八千六百零八个有效字节，除以零点零零零一秒，再除以十亿，得到 83.88608 GB/s。它不含主机传输，统计算法有效流量而非显存事务。缓存变化可能改变物理流量，却不改变这个分子。应明确标为假设计算，不能填进实际实验结果表。

### Exercise 2: Analyze one warp rather than one thread / 练习二：分析线程束而非单线程

**English:** Exercise: Thread t reads `input[t * stride + k]` as k increases through a loop. Every thread reads consecutive elements over time. Explain why a large stride can still give poor coalescing, and which addresses you should list to reason about one load instruction.

**中文：** 练习：线程按自身编号乘跨度再加循环变量来读取，每个线程随循环推进读取连续元素。为什么大跨度仍可能造成合并访问不佳？分析一条加载指令时应该列出哪些地址？

**English:** Reference solution: Hold k fixed and list the addresses for active lanes t in one warp. They differ by stride elements, so they can occupy many sectors despite each thread's temporal continuity. Then include element width and starting alignment before estimating the sector set. The relevant unit is simultaneous lane access for one instruction, not a thread's entire history. To improve the layout, consider assigning adjacent lanes adjacent elements and moving the remaining dimension into the per-thread loop, while preserving bounds and output correctness.

**中文：** 参考解答：固定循环变量，列出同一线程束活跃线程的地址，它们相差跨度个元素，所以即使每线程在时间上连续，也可能涉及很多扇区。然后结合元素宽度和起始对齐估计扇区集合。相关单位是一条指令的同时线程访问，而不是单线程全部历史。改进时可以考虑让相邻线程负责相邻元素，把剩余维度放进逐线程循环，但必须同时保持边界和输出正确，不能只追求连续地址。

### Exercise 3: Explain shared memory's role / 练习三：解释共享内存的作用

**English:** Exercise: Both naive and tiled transpose logically read each input once and write each output once. Why can tiling help even though it does not reduce that useful-byte count? Name two costs that can offset the benefit.

**中文：** 练习：朴素和分块转置在逻辑上都对输入读一次、输出写一次。既然有效字节没有减少，分块为什么仍可能有益？请指出两项可能抵消收益的成本。

**English:** Reference solution: A cooperative tile changes which threads perform output writes, allowing both global sides to use more contiguous lane patterns. The useful-byte count stays fixed while transaction efficiency can improve. Extra shared loads/stores, a block barrier, additional instructions, and resource-limited residency are costs. Therefore the hypothesis is better global access efficiency, not fewer logical elements. Compare transaction evidence and elapsed time, then examine whether the added shared stage introduced another bottleneck before declaring the transformation successful.

**中文：** 参考解答：协作小块改变负责输出写入的线程，使全局读写两侧都能采用更连续的线程地址模式。有效字节不变，但事务效率可能提高。额外共享读写、块屏障、新增指令和资源约束导致的驻留变化都是成本。因此假设是改善全局访问效率，而不是减少逻辑元素数量。应同时比较事务证据和耗时，再检查新增共享阶段是否造成别的瓶颈，不能仅看到使用了共享内存就宣布优化成功。

### Exercise 4: Derive the padding map / 练习四：推导填充映射

**English:** Exercise: Under the scalar 32-bit, 32-bank model, derive the bank indices for column access with physical row widths 32 and 33. Is an access by all lanes to exactly the same shared word the same problem? Can you infer a 32-fold kernel speedup?

**中文：** 练习：在三十二位标量、三十二存储体模型下，推导物理行宽为三十二和三十三的列访问映射。所有线程读同一个共享字是否属于同样问题？能否推断内核加速三十二倍？

**English:** Reference solution: For column c, the bank is `(lane * leading + c) % 32`. Leading 32 makes the bank constant while addresses differ; leading 33 makes it `(lane + c) % 32`, distributing lanes across banks. Same-word reads have supported broadcast behavior and must be distinguished. Whole-kernel speed depends on all stages, so a conflict-count change is not an equal speedup prediction. The model motivates the padded implementation; device measurements must establish its actual effect under the tested workload.

**中文：** 参考解答：列号固定时，存储体为线程号乘物理行宽加列号，再模三十二。行宽三十二使存储体恒定但地址不同；行宽三十三则等价于线程号加列号再取模，让线程分散。读取完全相同的字具有受支持的广播行为，必须区别。整个内核还受所有阶段共同影响，因此冲突数量变化不能直接当作同倍数加速。模型为填充实现提供动机，真实影响仍要由设备测量确认。

### Exercise 5: Repair an edge-tile barrier / 练习五：修复边缘屏障

**English:** Exercise: A programmer returns immediately when a thread's input coordinate is outside the matrix, before the tiled kernel's barrier. Why is that dangerous? Describe the safe control-flow structure and the proof needed for valid output reads.

**中文：** 练习：程序员发现线程输入坐标超出矩阵，就在分块屏障之前立即返回。为什么危险？请描述安全控制流，并说明有效输出读取需要什么证明。

**English:** Reference solution: Threads in the same block can disagree about the boundary condition, disrupting the collective synchronization protocol. Keep all participating threads through the barrier and predicate only their input and output accesses. Then show that each valid output coordinate maps to a shared entry written by a valid input producer. The output shape has swapped width and height, so reusing the input guard mechanically is insufficient. The CPU model verifies this mapping sequentially; a real GPU sanitizer run is still needed for device synchronization evidence.

**中文：** 参考解答：同一块内线程可能对边界条件有不同判断，从而破坏集体同步协议。应让参与线程都经过屏障，只给输入输出访问添加条件。之后证明每个有效输出坐标映射到的共享条目，已经由有效输入生产者写入。输出宽高已经交换，机械沿用输入条件不够。CPU 模型能顺序验证这种对应，却仍需真实 GPU 检测器提供设备同步证据，不能把模型通过当作并发行为验证完成。

### Exercise 6: Choose the right timer / 练习六：选择合适计时器

**English:** Exercise: A CPU timer immediately around a kernel launch reports less time than the device-event interval. Is that contradictory? Explain what synchronization is needed for each intended measurement and why repeated launches do not eliminate every submission effect.

**中文：** 练习：仅包围内核启动的 CPU 计时，比设备事件区间更短，这矛盾吗？请解释两种测量各自需要什么同步，以及为何重复启动不能消除全部提交影响。

**English:** Reference solution: The host launch can return before GPU execution completes, so it measures submission rather than completed work. Device events must bracket work in the intended stream and the stop event must complete before elapsed time is consumed. A host end-to-end interval must include the intended completion wait. Repetition amortizes some timing overhead, but a fast GPU may still wait for the CPU to submit subsequent kernels. Use a timeline to detect gaps and label the measured quantity accurately instead of assuming every timer reports the same latency.

**中文：** 参考解答：主机启动可以在 GPU 完成前返回，因此测的是提交，而不是已完成工作。设备事件要在目标流中包围工作，读取耗时前要等结束事件完成。主机端到端区间则必须包含所需完成等待。重复能摊薄部分计时开销，但速度快的 GPU 仍可能等待 CPU 提交后续内核。应通过时间线检查间隙，并准确标注测量对象，不能假设所有计时器都在报告同一种延迟。

### Exercise 7: Interpret high effective bandwidth / 练习七：解释很高的有效带宽

**English:** Exercise: A small repeated transpose reports effective bandwidth above the device's advertised DRAM bandwidth. List plausible explanations and a follow-up experiment that distinguishes cache reuse from a unit conversion mistake.

**中文：** 练习：一个小规模重复转置报告的有效带宽高于设备标称显存带宽。请列出可能原因，并设计后续实验，区分缓存复用与单位换算错误。

**English:** Reference solution: Repeated data may be served by cache, so useful bytes do not equal DRAM bytes; alternatively milliseconds, bytes, or repetition count may be converted incorrectly. Verify the arithmetic from raw elapsed milliseconds first. Then vary working-set size, rotate buffers if studying streaming behavior, and inspect memory-level traffic with a consistent profiling protocol. Preserve the original warm-cache result as its own valid question if correctness and units hold. Do not edit the reported value merely to force agreement with a DRAM specification.

**中文：** 参考解答：重复数据可能来自缓存，因此有效字节不等于显存字节；也可能是毫秒、字节或重复次数换算错误。先用原始毫秒重新计算，再改变工作集大小，若研究流式行为则轮换缓冲区，并以一致分析协议观察不同内存层级流量。如果正确性和单位都成立，原热缓存结果可以作为独立问题保留。不能为了符合显存规格就修改数值，而应解释两种指标为什么不代表同一边界。

### Exercise 8: Evaluate an occupancy change / 练习八：评价占用率变化

**English:** Exercise: Limiting registers raises estimated occupancy from one configuration to another, but measured time becomes worse. Give a plausible mechanism and name the evidence needed before deciding whether to keep the change.

**中文：** 练习：限制寄存器使估计占用率提高，但实际耗时更差。请给出可能机制，并说明决定保留改动之前需要哪些证据。

**English:** Reference solution: The limit may cause spills, adding local-memory loads/stores and dependencies that outweigh added residency. It may also change instruction scheduling or reduce useful per-thread parallelism. Inspect compiler resource reports, spill-related behavior, register usage, occupancy limits, and ordinary timing under equivalent inputs. A higher percentage is not a success criterion. Keep the version that improves the relevant workload with verified correctness, and document where the tradeoff changes rather than treating one register cap as a universal setting.

**中文：** 参考解答：限制可能导致溢出，增加局部内存读写与依赖，其代价超过驻留增加的收益；也可能改变指令调度或减少逐线程有效并行。应检查编译资源报告、溢出相关行为、寄存器用量、占用率限制，以及相同输入条件下的普通计时。百分比更高不是成功标准。保留对目标工作负载确实更好且正确性通过的版本，并记录权衡在哪些条件改变，不能把某个寄存器上限当作通用最优设置。

### Exercise 9: Connect timeline and kernel counters / 练习九：连接时间线与内核指标

**English:** Exercise: A service's GPU is idle for long intervals, yet one kernel's Compute report shows inefficient writes. Which issue should be investigated first, and how can Systems and Compute results be combined without confusing application and kernel speedups?

**中文：** 练习：服务 GPU 有长时间空闲，同时某内核的 Compute 报告显示写入效率不佳。应先调查哪一问题？如何结合两类报告而不混淆应用与内核加速？

**English:** Reference solution: Start from the application objective and quantify time spent in idle intervals versus that kernel. Systems can reveal preparation, submission, copies, or synchronization causing the gaps. Compute can explain inefficient writes once that kernel is shown to matter. Improving both may be worthwhile, but their expected contributions differ. Estimate the fraction of end-to-end time affected by each change, validate separately, and remeasure the complete request. A large isolated kernel speedup cannot by itself establish a comparable service-latency improvement.

**中文：** 参考解答：从应用目标出发，先量化空闲区间与该内核各占多少时间。Systems 可定位准备、提交、复制或同步造成的间隙；确认该内核重要后，Compute 再解释低效写入。两者都可能值得改善，但预期贡献不同。应估计每项改动影响端到端时间的比例，分别验证，再重测完整请求。孤立内核的大幅加速不能单独证明服务延迟也同倍改善，报告必须保留这两个层级。

### Exercise 10: Transfer the method to reduction / 练习十：把方法迁移到归约

**English:** Exercise: A two-stage sum reduction reads N floats, writes B block sums, then reads B sums and writes one result. Derive the useful-byte count and explain two reasons why a transpose validation or performance conclusion cannot be copied directly to this reduction.

**中文：** 练习：两阶段求和读取 N 个浮点数，写出 B 个块结果，再读入这些结果并写一个最终值。推导有效字节，并说明为什么不能把转置的验证或性能结论直接搬到归约。

**English:** Reference solution: Under this stated algorithm, useful bytes are `(N + 2 * B + 1) * sizeof(float)`, excluding any additional passes or overhead introduced by a different implementation. Reduction performs arithmetic and changes the addition order, so floating-point tolerance must be justified. It also has reduction dependencies, synchronization, and a smaller later-stage parallel workload, so memory-layout success in transpose does not determine its bottleneck. Apply the same hypothesis-and-evidence process while deriving a new byte count, correctness contract, and resource model for the reduction itself.

**中文：** 参考解答：按题目指定算法，有效字节为 `(N + 2 * B + 1) * sizeof(float)`，不包括其他实现可能增加的遍历。归约执行算术并改变加法顺序，需要合理浮点容差；它还具有合并依赖、同步和后续阶段并行规模缩小等性质，因此转置布局成功不能决定归约瓶颈。可以迁移提出假设并寻找证据的方法，但必须为归约重新推导字节数量、正确性契约及资源模型。

## 14. Acceptance and next experiments / 验收与后续实验

**English:** Local evidence is deliberately bounded: all four CUDA kernels compile for `sm_89`; the compiler reports 18 registers for copy/naive and 22 for both tiled variants, with zero reported spills in this build. Static shared storage is 4096 and 4224 bytes for unpadded and padded respectively. These are compiler resource reports, not occupancy measurements or performance results. The CPU model passes twelve shape/layout combinations and the invalid argument is rejected before a CUDA Runtime call. GPU correctness, sanitizer runs, timing, and profiler collection remain pending.

**中文：** 本地证据范围明确：四个 CUDA 内核均能针对 `sm_89` 编译；本次编译报告复制与朴素版各使用十八个寄存器，两个分块版各二十二个，没有报告溢出；无填充与有填充分别使用四千零九十六和四千二百二十四字节静态共享内存。这是编译资源报告，不是占用率实测或性能结果。CPU 模型通过十二组形状布局，非法参数在 Runtime 调用前被拒绝。GPU 正确性、检测器、计时和分析采集仍待完成。

**English:** You have completed the conceptual course when you can derive the input and output indices, explain why all block threads cross the barrier, compute the bank map and bandwidth units, and state what theoretical occupancy does not tell you. Practical device completion additionally requires the edge-case runs, clean relevant sanitizer results, raw timing files, and a report comparing one memory hypothesis with its observed evidence. A compiled executable and a plausible performance story satisfy neither device correctness nor the measurement requirement.

**中文：** 能推导输入输出索引、解释为什么所有块内线程经过屏障、计算存储体映射和带宽单位，并指出理论占用率无法说明什么，才算完成概念课程。设备实践完成还需要边界案例、相关检测器通过、原始时间文件，以及把某个内存假设与实际证据对照的报告。得到可执行文件并讲出看似合理的性能故事，既不等于设备正确性通过，也不满足实际测量要求。

**English:** Continue with a controlled rows-per-block study, a streaming-versus-warm-cache comparison, or a small two-stage reduction. Choose one and preserve the current implementation as the baseline. For each change, write the predicted mechanism, the metric that should respond, and the correctness conditions before running. Later Rust CUDA experiments can reproduce the same shapes and measurement protocol, allowing language/toolchain comparisons to focus on generated behavior and engineering costs rather than mismatched workloads or selectively chosen results.

**中文：** 后续可以选择受控的线程行数研究、流式与热缓存对照，或小型两阶段归约，每次只选一个，并保留当前实现为基线。运行之前写下预计机制、应变化的指标和正确性条件。以后开展 Rust CUDA 实验时，可以复用相同形状和计量协议，使语言与工具链比较聚焦于生成行为和工程成本，而不是比较不同工作负载，或者选择性展示恰好有利的结果。

## Official references / 官方参考资料

**English:** Checked on 2026-09-18. The archived CUDA 13.3 Programming Guide is the newer guide organization; the old `cuda-c-programming-guide` is a legacy reference and is not presented here as the current guide. CUDA Runtime and Best Practices links are version-pinned. Nsight and Compute Sanitizer links are rolling references; consult local help for exact supported options. The chapter's experiment, index simulator, exercises, and interpretations are original teaching material rather than a translated copy of a vendor example.

**中文：** 核验日期为 2026 年 9 月 18 日。CUDA 13.3 归档采用新版编程指南结构，旧路径属于历史资料，本课不把它称为当前指南。CUDA Runtime 与最佳实践链接固定版本；Nsight 和 Compute Sanitizer 链接持续更新，准确选项应查本地帮助。本章实验、索引模拟器、习题与分析为原创教学内容，并非厂商示例的逐段翻译。

- [CUDA 13.3 Programming Guide / CUDA 13.3 编程指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html)
- [SIMT kernels / 线程级内核](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/writing-cuda-kernels.html)
- [Advanced kernel programming / 高级内核编程](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/03-advanced/advanced-kernel-programming.html)
- [Asynchronous execution / 异步执行](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/02-basics/asynchronous-execution.html)
- [Compute capabilities / 计算能力](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/05-appendices/compute-capabilities.html)
- [CUDA 13.3 Best Practices / CUDA 13.3 最佳实践](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-c-best-practices-guide/index.html)
- [CUDA event API / CUDA 事件接口](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__EVENT.html)
- [CUDA occupancy API / CUDA 占用率接口](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__OCCUPANCY.html)
- [Nsight Systems user guide / Nsight Systems 用户指南](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)
- [Nsight Compute profiling guide / Nsight Compute 分析指南](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
- [Nsight Compute CLI / Nsight Compute 命令行](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html)
- [Compute Sanitizer / 计算检测工具](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html)
