# PyTorch and Custom Operators / PyTorch 与自定义算子

## 1. Purpose, Prerequisites, and Version Scope / 目标、前置知识与版本范围

**English:** This course connects a mathematical tensor operation to its actual storage, framework dispatch, compiled execution, and CUDA implementation. The main skill is specifying what an operator promises before optimizing it. You should be able to explain why two tensors with the same shape may need different indexing, why a numerically correct CUDA function may still be an incomplete PyTorch operator, and why a faster isolated kernel may fail to improve a model service. These questions connect the tensor foundations in Days 025 and 028 to the repository's planned extension and compiler work. They also provide a common vocabulary for understanding how an inference framework calls lower-level implementations.

**中文：** 本课把数学上的张量运算与实际存储、框架分发、编译执行以及 CUDA 实现联系起来。核心能力是在优化之前准确说明算子承诺什么。你应能解释：为什么形状相同的两个张量可能需要不同索引，为什么数值正确的 CUDA 函数仍可能不是完整的 PyTorch 算子，以及为什么单独 kernel 变快却未必改善模型服务。这些问题将 Day025、Day028 的张量基础连接到仓库规划中的扩展与编译工作，也为后续理解推理框架怎样调用底层实现提供共同语言。

**English:** Prerequisites are Python data handling, C++ resource basics, and CUDA indexing and synchronization from Courses 02, 03, and 05. Performance conclusions additionally depend on Course 06. We focus on inference and a small out-of-place affine operator, not on implementing a complete deep-learning framework. Autograd and batching transformations are discussed as explicit interface obligations: a course may intentionally exclude them from an example, but an implementation must not silently claim support that was never registered or tested. An explicit scope tells callers when they can rely on the operator and when they need another path.

**中文：** 前置知识包括课程 02 的 Python 数据处理、课程 03 的 C++ 资源基础，以及课程 05 的 CUDA 索引和同步；讨论性能结论还需要课程 06。本课聚焦推理和一个小型非原地仿射算子，并不尝试实现完整深度学习框架。自动求导和批处理变换会作为明确接口义务讨论：示例可以有意不支持某项能力，但实现不能在没有注册、没有测试时默默声称已经支持。说明范围不是降低标准，而是让使用者知道何时可以依赖该算子，何时必须选择其他路径。

**English:** Primary documentation was checked on 2026-09-18. The current stable documentation redirects to PyTorch 2.14, which is the teaching API baseline. CPU examples use an isolated PyTorch 2.14.0 environment; a CUDA extension requires a CUDA-enabled PyTorch build and a compatible compiler and toolkit combination, not the CPU wheel. The host's installed CUDA Toolkit is 13.3, and its driver/NVML mismatch blocks GPU validation. Course 10 pins its own serving dependencies; do not merge the environments merely because both use PyTorch.

**中文：** 一手资料核验日期为 2026-09-18，当前 stable 文档跳转至 PyTorch 2.14，因此本课以该版本接口作为教学基线。CPU 示例使用隔离的 PyTorch 2.14.0 环境；CUDA 扩展需要启用 CUDA 的 PyTorch 构建，以及兼容的编译器和 Toolkit 组合，CPU wheel 不能替代这种构建。本机已安装 CUDA Toolkit 13.3，但驱动与 NVML 不匹配阻止了 GPU 验证。课程 10 会固定自己的推理服务依赖，不能因为两门课都使用 PyTorch，就直接合并环境并假定所有版本彼此兼容。

## 2. Tensor Metadata Is Part of the Contract / 张量元数据也是契约

**English:** A tensor is not simply a Python list with a GPU flag. Shape describes the logical index space, dtype determines how element bits are interpreted, device identifies the execution and storage placement, and layout information maps logical indices to storage. The number of elements is the product of dimensions, but a tensor view may expose only part of a larger allocation. Understanding that distinction prevents mistaken memory estimates based only on the apparent size of one small view. If a view retains the underlying storage, deleting the original large tensor binding may not free the allocation; its lifetime depends on all objects still retaining that storage.

**中文：** 张量并不是在 Python 列表上加一个 GPU 标志。形状描述逻辑索引空间，数据类型决定如何解释元素位模式，设备标识执行与存储位置，布局信息则将逻辑索引映射到存储。元素数量通常是各维度大小的乘积，但张量视图可能只暴露较大分配中的一部分。理解这个区别，可以避免仅根据一个小视图表面大小就估算内存占用。如果视图仍然保留底层存储，删除原来的大张量变量也不一定释放整块分配，真正决定寿命的是所有仍然引用该存储的对象。

**English:** Dtype is a numerical and implementation choice. A value stored in half precision has different representable values and rounding behavior from float32; changing storage dtype is not merely changing the number of bytes transferred. Some kernels accumulate in a wider dtype than their inputs, and mixed-precision policies can choose implementations without changing every user-visible tensor in the same way. State input, output, and accumulation dtypes separately when reproducing an experiment or comparing a custom implementation with a reference. Otherwise, an apparent optimization may merely enable another precision-dependent execution path or change the acceptable error range.

**中文：** 数据类型同时影响数值和实现。半精度存储与 float32 具有不同的可表示数值和舍入行为，改变存储类型不只是减少传输字节数。有些 kernel 使用比输入更宽的累加类型，混合精度策略也可能选择特定实现，而不以相同方式改变所有用户可见张量。复现实验或比较自定义实现与基线时，应分别说明输入类型、输出类型和累加类型。否则，一个看似来自优化的差异，可能只是改变精度后允许了另一条计算路径，甚至已经改变误差范围。

**English:** Device identity includes the specific device, not just whether the tensor is on CUDA. Two CUDA tensors on different GPUs are not automatically interchangeable inputs to one kernel. A host pointer and a device pointer also carry different accessibility assumptions. Check the actual devices at an operator boundary and select a device context compatible with the input. Implicitly copying an input to make a call succeed can hide a large cost and change the ownership or synchronization behavior expected by the caller. The teaching example rejects unsupported input instead of hiding expensive transfers inside an apparently cheap operator call.

**中文：** 设备身份不仅包括是否使用 CUDA，还包括具体是哪一块设备。位于不同 GPU 的两个 CUDA 张量，不会自动成为同一个 kernel 可以互换访问的输入。主机指针和设备指针也具有不同可访问性前提。算子边界应检查真实设备，并选择与输入相符的设备上下文。为了让调用成功而隐式复制输入，可能隐藏巨大的成本，也可能改变调用方所期待的所有权和同步行为。课程示例宁可明确拒绝不支持的输入，也不把昂贵的数据迁移藏进看似便宜的算子调用里。

**English:** A tensor's rank is the number of dimensions; a scalar tensor has rank zero and can still contain one element. An empty tensor may have a zero dimension and contain no elements. These cases affect launch configuration, reduction identities, and result shapes. For an elementwise operator, empty input should usually return a correctly shaped empty output without launching a zero-block CUDA grid. Avoid writing shape checks that accidentally classify every scalar as invalid or every empty tensor as a null-pointer bug. Define boundary semantics in the contract and cover them with tests before a real model happens to trigger them.

**中文：** 张量的秩是维度数量，零维标量张量仍然可以包含一个元素；空张量可能有某个维度为零，因此没有元素。这些情况会影响启动配置、归约单位元以及输出形状。对逐元素算子而言，空输入通常应返回形状正确的空输出，而不启动块数为零的 CUDA 网格。编写形状检查时，不要误把所有标量都当作非法输入，也不要把所有空张量都看成空指针错误。边界语义应先写进契约，再由测试覆盖，而不是等待真实模型偶然触发后才决定行为。

**English:** Broadcasting aligns dimensions from the right and permits compatible singleton expansion. It describes logical repetition, which does not require physically duplicating values. Before applying a broadcasting formula, write the intended semantic axes. An expression can be shape-compatible while applying a feature bias along a batch axis by accident. Naming the meaning of each dimension in a test makes this class of bug easier to detect than merely checking that the final shape is accepted by the framework. Equal batch and feature sizes can hide an incorrect broadcast, so deliberately choose unequal dimensions in tests.

**中文：** 广播从右侧对齐维度，并允许兼容的单元素维度扩展。它描述逻辑上的重复，不要求真实复制数据。使用广播公式前，应先写清各轴的业务含义。一个表达式可能在形状上完全兼容，却把特征偏置误加到了批次轴上。测试中明确每个维度代表什么，比只检查最终形状能被框架接受更容易发现此类错误。尤其当批次大小恰好等于特征数时，错误广播可能被一组过于整齐的数据掩盖，因此测试维度应有意识地取不同数值。

**English:** Aliasing means different tensor objects can access the same storage. In-place updates can therefore become visible through views that were created earlier. Out-of-place output normally provides a fresh result, but the exact aliasing promise belongs to the operation's contract. Do not infer independence from different Python object identities. A correct test should modify one value and inspect the expected aliases, or inspect supported metadata, instead of relying on a coincidental representation string or memory address printed by a debugger. This matters for caches, reusable buffers, and multistage inference: which owned storage changed can matter more than which object was returned.

**中文：** 别名表示不同张量对象可能访问同一份存储，因此原地更新可能通过先前创建的视图被观察到。非原地输出通常提供新的结果，但具体的别名承诺属于算子契约，不能仅凭 Python 对象身份不同就推断存储独立。正确测试可以修改一个值并检查预期别名，或检查受支持的元数据，而不是依赖调试器偶然打印的表示字符串或地址。对于缓存、复用缓冲区和多阶段推理，这种区分尤其重要：修改了谁拥有的存储，往往比返回了哪个对象更关键。

## 3. Shape, Stride, and Views / 形状、步幅与视图

**English:** For a strided tensor, a logical index maps to an element offset using the storage offset plus the sum of each index multiplied by its stride. Strides are normally expressed in elements, not bytes. A row-major two-dimensional tensor can have strides `(columns, 1)`, while transposing its axes changes the logical mapping without necessarily moving any elements. The kernel must either honor that mapping or explicitly require a layout it knows how to index. Shape alone does not supply enough information. Across Python, C++, and CUDA boundaries, obtaining a contiguous address range is not a reason to ignore the original logical ordering.

**中文：** 对步幅张量而言，逻辑索引对应的元素偏移由存储偏移加上各轴索引与步幅乘积之和确定。步幅通常以元素为单位，而不是字节。一个按行排列的二维张量可能具有 `(列数, 1)` 步幅；转置其坐标轴可以改变逻辑映射，而不必搬动任何元素。kernel 必须遵守该映射，或者明确要求自己能够索引的布局。单独提供 shape 并不够，尤其是跨越 Python、C++ 与 CUDA 边界后，不能因为拿到了连续地址就忽略张量原来的逻辑顺序。

**English:** A view reuses storage while changing how it is interpreted. Operations such as transpose and many slicing operations can be inexpensive metadata transformations, but downstream work may become more expensive because the resulting accesses are strided. Measuring only the view creation can therefore miss the real cost. In a pipeline, inspect the consumer's memory-access pattern and whether a later operation materializes a contiguous copy. A cheap producer can shift cost to an expensive consumer without changing the visible mathematical expression. Follow adjacent operators when optimizing layout; a nearly free transpose statement does not make the entire transpose-related path free.

**中文：** 视图复用存储并改变其解释方式。转置和许多切片操作可以只是较便宜的元数据转换，但后续工作可能因为跨步访问而变贵。因此，只测视图创建过程容易遗漏真正成本。在流水线中，应观察消费者的访存方式，以及之后是否有操作物化为连续副本。一个便宜的生产者可能把成本转移给昂贵的消费者，而用户看到的数学表达式没有变化。优化布局时必须跟踪相邻算子，不能因为某一行转置几乎没有耗时，就认为整条转置相关路径没有代价。

**English:** `view` requires the requested shape to be compatible with the existing stride structure. `reshape` may return a view when possible or create a copy when necessary. Its convenience does not promise zero-copy behavior. `contiguous` returns a tensor in the requested contiguous memory format and may return the original tensor when it already meets that format. Do not assume that calling it always creates independent storage; use an explicit clone when independence is the intended semantic requirement. [Tensor views](https://docs.pytorch.org/docs/2.14/tensor_view.html). Determine whether a transformation copies from its contract, actual layout, and observations rather than its name.

**中文：** `view` 要求目标形状与现有步幅结构兼容；`reshape` 在能够复用存储时可以返回视图，必要时也可以产生复制，因此便利接口并不承诺零拷贝。`contiguous` 返回符合所请求连续内存格式的张量，如果原张量已经满足要求，也可能直接返回原对象。不能假定调用它总会产生独立存储；如果语义要求存储独立，就应明确使用克隆。[张量视图说明](https://docs.pytorch.org/docs/2.14/tensor_view.html)。判断一个变换是否复制，应同时考虑契约、实际布局和验证结果，而不是凭函数名猜测。

**English:** Expansion can represent repeated logical values with a zero stride. Several logical indices then refer to one physical element. Such a tensor is useful for reading broadcast parameters but dangerous as a target for unrestricted parallel writes. Writing one result per logical index does not guarantee one unique destination per thread. A custom operator must either reject unsupported overlap, materialize a suitable output, or implement precisely defined behavior. A generic flat pointer loop over `numel` cannot correctly process every expanded input. Both memory safety and mathematical correctness require understanding the mapping from logical elements to physical storage.

**中文：** 扩展可以通过零步幅表示重复的逻辑数值，使多个逻辑索引指向同一物理元素。这样的张量适合读取广播参数，却不适合作为没有限制的并行写入目标。每个逻辑索引写一个结果，并不保证每个线程都有独一无二的目的地址。自定义算子必须拒绝不支持的重叠、物化合适输出，或者实现精确定义的行为。简单按照 `numel` 对裸指针做线性循环，无法正确处理所有扩展输入。访存安全和数学正确性都需要知道逻辑元素与真实存储之间的对应关系。

**English:** A slice may have a nonzero storage offset. PyTorch's `data_ptr` refers to the tensor's first logical element, so an extension must not blindly add the storage offset again when indexing from that pointer. Conversely, an implementation that starts from the underlying storage base needs to account for the offset. These are different coordinate systems. Write down which pointer your code receives and derive indexing from that point; mixing the two systems can produce an apparently consistent shift that only appears for sliced inputs. Testing only contiguous tensors starting at offset zero usually misses this defect.

**中文：** 切片可能具有非零存储偏移。PyTorch 的 `data_ptr` 指向张量的第一个逻辑元素，因此扩展如果从这个指针开始索引，就不能盲目再次加上存储偏移。相反，如果实现从底层存储基址开始计算，则需要考虑该偏移。这是两套不同坐标系。应先写明代码取得的是哪一种指针，再从相应起点推导索引；混用坐标系可能造成看起来始终一致的错位，而错误只在切片输入上出现。只测试从零开始的连续张量，通常发现不了这种缺陷。

**English:** Memory format is another reason to avoid reducing every layout question to one boolean. A tensor can be contiguous in a supported alternative format while failing the default contiguous check. An operator may intentionally support only the default format, but the error should say so. General support can be added through stride-aware kernels or dedicated implementations, and then tested independently. Treat each additional layout as an extension of the contract with correctness and performance obligations, not as a harmless change to input validation. For this lab, explicitly rejecting non-contiguous input gives a more reliable baseline than pretending to support every layout.

**中文：** 内存格式进一步说明，布局问题不能全部归结为一个布尔值。张量可能在受支持的另一种格式下连续，却不满足默认连续检查。算子可以有意只支持默认格式，但错误信息应明确这一限制。要支持更多格式，可以编写感知步幅的 kernel 或专门实现，再分别测试。每增加一种布局，都是扩展契约并增加正确性与性能义务，不能把它当作放宽输入校验这样一个无关紧要的改动。对于本课实验，清楚拒绝非连续输入比假装支持所有布局更便于建立可靠基线。

## 4. Build a Numerical Oracle / 建立数值正确性基线

**English:** A reference implementation should be simpler to trust than the optimized implementation. For a small affine transform, the expression `x * scale + bias` is readable and sufficient. For a reduction, a higher-precision CPU calculation can expose accumulation errors, although it is not automatically the exact bit pattern required by the production contract. Explain whether the comparison tests mathematical accuracy, compatibility with a specific framework implementation, or exact reproducibility. Different questions can legitimately require different oracles. A framework result does not define every possible correctness requirement, and a small deviation from a higher-precision reference must be judged against the application's numerical tolerance.

**中文：** 参考实现应当比优化实现更容易获得信任。小型仿射变换可以使用容易阅读的 `x * scale + bias`；归约则可以借助更高精度的 CPU 计算暴露累加误差，但它不自动等于生产契约要求的精确位模式。必须说明比较是在测试数学精度、与某个框架实现的兼容性，还是逐位可复现。不同问题可能合理地使用不同基线。不要把“来自框架”的结果无条件视为一切正确性的定义，也不要因为自己实现与高精度参考略有差异，就忽略目标业务允许的数值误差。

**English:** Floating-point addition is not associative, and a fused multiply-add can round differently from two separate instructions. Parallel reduction order, tensor-core paths, and compiler choices can therefore change results without necessarily introducing a bug. However, a tolerance is not permission to conceal indexing errors. Choose absolute and relative tolerances for the expected scale and dtype, test values near zero and across different magnitudes, and investigate structured errors such as one wrong row or periodic mismatches instead of simply increasing tolerance. Numerical validation needs both floating-point reasoning and enough sensitivity to expose actual implementation errors.

**中文：** 浮点加法不满足结合律，融合乘加与分开的两条指令也可能产生不同舍入。因此，并行归约顺序、张量核心路径和编译器选择可能改变结果，而不一定引入错误。但是容差并不是掩盖索引缺陷的许可。应根据量级和数据类型选择绝对与相对容差，测试接近零和不同数量级的数值；遇到整行错误或周期性错位等结构化误差，应调查原因，而不是直接放大容差。数值验证既需要理解浮点规律，也需要保留足够敏感性，以发现真正的实现问题。

**English:** Correctness includes metadata and behavior as well as element values. Check shape, dtype, device, supported strides, mutation of inputs, and the promised independence of the output. An implementation can produce the expected values once while returning an alias that corrupts a later pipeline stage. Include repeated calls and mutations after the call in the test design. Small deterministic inputs make failures interpretable; randomized tests broaden coverage but should save the seed and failing configuration. A claim of ten thousand random tests without the failing configuration does not let another engineer reproduce a specific defect.

**中文：** 正确性不只包括元素数值，也包括元数据和行为。需要检查形状、数据类型、设备、支持的步幅、输入是否被修改，以及输出承诺的独立性。某个实现可能第一次产生正确数值，却返回一个会破坏后续流水线的别名。测试设计中应包含重复调用，以及调用后继续修改相关对象的场景。小型确定性输入有助于解释失败，随机测试则可以扩展覆盖面，但必须保存随机种子和失败配置。只保留“随机测过一万次”的结论，无法帮助其他人复现一条具体错误。

**English:** `torch.testing.assert_close` can compare tensors with explicit tolerances and metadata checks. It does not certify the operator's stream behavior, mutation schema, or autograd registration. Conversely, `torch.library.opcheck` checks important registration behavior but is not a numerical proof against the intended formula. Use these tools for their distinct purposes, and report both. A green registration check cannot compensate for an incorrect CUDA formula, and numerical agreement cannot establish that graph compilation understands an operation's metadata effects. Map each acceptance check to its contract rather than reducing every result to one unexplained green status.

**中文：** `torch.testing.assert_close` 可以使用明确容差并结合元数据检查比较张量，但不会认证算子的流行为、修改声明或自动求导注册。相反，`torch.library.opcheck` 检查重要的注册行为，却不是相对于目标数学公式的数值证明。应分别使用这两类工具，并报告各自结果。注册检查通过不能弥补错误的 CUDA 公式，数值一致也不能证明图编译理解了算子的元数据影响。一个可靠验收表应列出每项检查对应的契约，而不是把所有测试压缩成一个无法解释的绿色标记。

**English:** Inference mode and module evaluation mode solve different problems. `model.eval()` changes the behavior of modules that distinguish training and evaluation, such as dropout. It does not by itself disable gradient recording. `no_grad` and `inference_mode` control autograd-related behavior, with different restrictions and overhead characteristics. A benchmark must record the chosen mode. Comparing one implementation with gradient tracking to another in inference mode is not a clean test of kernel optimization. Even for an inference-only application, record how unnecessary mechanisms were disabled so framework configuration is not mistaken for a lower-level improvement.

**中文：** 推理模式与模块评估模式解决不同问题。`model.eval()` 改变区分训练和评估的模块行为，例如 dropout，但不会单独关闭梯度记录。`no_grad`、`inference_mode` 控制与自动求导相关的行为，两者具有不同限制和开销特征。基准必须记录实际使用的模式。一边保留梯度跟踪、另一边使用推理模式，并不是对 kernel 优化的干净比较。即使最终业务只做推理，也需要说明测试时如何关闭不需要的机制，避免把框架配置差异误归因为底层实现差异。

## 5. An Operator Is More Than a Pointer Call / 算子不只是一次指针调用

**English:** Calling a native function through a binding can compute values correctly while remaining opaque to framework transformations. PyTorch's dispatcher connects an operator schema to backend implementations. The schema identifies argument and result types and, when applicable, mutation and aliasing behavior. The CPU and CUDA implementations can share one public operation while using different code. This separation lets callers express what operation they want without hard-coding one device implementation into every call site. Passing a device pointer into C++ alone does not establish all higher-level framework capabilities.

**中文：** 通过绑定调用原生函数，可能正确计算数值，却仍然对框架变换不可理解。PyTorch 分发器把算子 schema 与后端实现连接起来。schema 标明参数、结果类型，以及适用时的修改和别名行为。CPU 和 CUDA 实现可以共享一个公开算子，同时使用不同代码。这样，调用者表达的是需要执行什么操作，而不必在每个调用点写死设备实现。框架集成工作的重要部分正是维护这层约定，不能认为只要把一个设备地址传进 C++ 函数，所有高层能力就自然成立。

**English:** For the lab, the contract is deliberately narrow: a contiguous float32 tensor on a supported CPU or CUDA device, two scalar parameters, a fresh tensor with the same shape and dtype, and no input mutation. Gradient-requiring inputs are rejected because this inference-only teaching operator does not register a backward formula. A production extension can add more dtypes, layouts, and transformations, but each addition needs an implementation strategy and independent tests. Narrow, explicit support is preferable to accidentally reading unsupported storage as float32. An explicit supported range also lets callers choose appropriate preprocessing or an alternative implementation.

**中文：** 本实验有意采用较窄契约：输入是在受支持 CPU 或 CUDA 设备上的默认连续 float32 张量，加两个标量参数；输出具有相同形状与类型、使用新存储，并且不修改输入。要求梯度的输入会被拒绝，因为这个仅用于推理教学的算子没有注册反向公式。生产扩展可以增加类型、布局和变换支持，但每增加一项都需要实现策略和独立测试。清楚说明支持范围，比误把不支持的存储按 float32 读取更可靠，也更容易让调用方采取正确的预处理或替代路径。

**English:** A fake implementation computes output metadata without reading real tensor values. It helps transformations reason about shape, dtype, device, and layout. The fake path must agree with the real path's supported inputs and output metadata. If the real operator always returns a contiguous result but the fake path invents arbitrary strides, compilation may reason about a different operation. A fake kernel is not a slow numerical fallback, and returning plausible values from it is not the task. This separates numerical failures from missing compiler metadata rules.

**中文：** fake 实现不读取真实张量数值，而是计算输出元数据，以帮助变换理解形状、数据类型、设备和布局。fake 路径必须与真实路径支持的输入和产生的输出元数据一致。如果真实算子始终返回连续结果，而 fake 路径虚构任意步幅，编译阶段理解的就可能是另一个操作。fake kernel 不是较慢的数值备用实现，它的任务也不是返回看起来合理的数据。理解这一点，有助于把“数学计算失败”和“编译器缺少形状推理规则”分成不同问题处理。

**English:** Mutation and aliasing declarations affect optimization legality. If an operation mutates an input but claims to be functional, the compiler may reorder or eliminate work based on a false model. Conversely, unnecessarily declaring mutation can block useful transformations. Start by specifying which storage locations may change and which outputs can share storage with which inputs. Then implement and test that exact contract. An aliasing bug can remain invisible when tests only compare output values immediately after one call. Framework correctness includes state before and after calls and combinations of operators, beyond the local observation at one return.

**中文：** 修改和别名声明会影响优化是否合法。如果操作修改输入却声称自己是纯函数，编译器就可能基于错误模型重排或消除工作；反过来，不必要地声明修改也可能阻碍有价值的变换。应先规定哪些存储位置可能变化，哪些输出可以与哪些输入共享存储，再实现并测试该契约。如果测试只在单次调用后立即比较输出数值，别名错误可能长期隐藏。框架层的正确性需要考虑调用前后状态以及多个算子的组合，而不仅是一个函数返回时的局部观察。

**English:** CUDA integration must honor the framework's current device and stream. Launching on a hard-coded default stream can violate dependencies when the caller uses another stream. Allocating an output and launching a kernel should remain ordered with the caller's work. A launch check catches immediate launch failures; it does not prove that asynchronous execution has finished correctly. Synchronize at deliberate validation boundaries, not automatically inside every operator call, unless synchronous completion is an explicit part of the API. The choice affects composability and execution overlap, making it part of operator design rather than merely a timing convenience.

**中文：** CUDA 集成必须遵守框架当前设备和流。若调用方使用其他流，算子却硬编码默认流启动，就可能破坏依赖关系。输出分配与 kernel 执行应当与调用方工作保持正确顺序。启动检查可以捕获直接的启动失败，却不能证明异步执行已经正确完成。应在明确的验证边界同步，而不是在每次算子调用内部自动同步，除非同步完成本来就是接口承诺。这个选择会影响可组合性与并发重叠，因此属于算子设计的一部分，不能只当成计时方便与否的问题。

**English:** Compilation and loading introduce a separate compatibility layer. A system CUDA compiler, the CUDA runtime associated with a PyTorch wheel, the driver, C++ ABI choices, and GPU architecture flags are related but not identical version settings. Record them independently. Build failures should first be classified as missing toolchain, incompatible headers or libraries, ABI mismatch, or unsupported architecture rather than attributed to the kernel formula. Avoid globally changing the machine's toolkit merely to satisfy one temporary experiment. Global toolchain changes can undermine reproduction of other courses and existing projects; prefer an isolated build environment and recorded versions.

**中文：** 编译和加载还引入一层独立兼容性。系统 CUDA 编译器、PyTorch wheel 关联的 CUDA 运行库、驱动、C++ ABI 选择和 GPU 架构标志彼此相关，却不是同一个版本设置，应该分别记录。构建失败时，先分类为工具链缺失、头文件或库不兼容、ABI 不匹配、架构不支持等问题，不要直接归咎于 kernel 数学公式。为了满足一个临时实验而修改整台机器的工具链，会让其他课程和既有项目失去可复现性；隔离构建环境和保留版本记录通常更合适。

## 6. Graph Capture and Compilation / 图捕获与编译

**English:** `torch.compile` changes how compatible regions of a program are executed. It observes Python execution, captures supported tensor computation, and uses a backend to generate or select implementations. Python-side behavior that cannot be captured can lead to graph breaks or other handling depending on the configuration. A compiled wrapper does not mean every instruction in the function became one GPU kernel. Inspect graph boundaries and backend behavior before claiming that compilation eliminated Python overhead or fused an entire model. In a service, the benefit depends on the captured portion of end-to-end work and whether changing inputs repeatedly disrupt a stable execution path.

**中文：** `torch.compile` 改变程序中兼容区域的执行方式：观察 Python 执行，捕获受支持的张量计算，再由后端生成或选择实现。无法捕获的 Python 行为可能导致图中断，或者根据配置采取其他处理。函数套上编译包装，并不表示其中每条指令都变成一个 GPU kernel。声称编译消除了 Python 开销、融合了整个模型之前，应查看图边界和后端行为。对于推理系统，实际收益取决于被捕获部分在端到端请求中占多少比例，以及输入变化是否不断破坏稳定执行路径。

**English:** Inductor is a compiler backend that lowers captured computation toward executable implementations. Triton is one tool used for GPU kernel programming and generation in relevant paths; it is not synonymous with the whole PyTorch compiler. Native library calls and other generated code can also be involved. Learn the boundaries first: Python capture, graph transformations, operator lowering, kernel execution, and runtime scheduling. This decomposition helps locate a failure without treating every compiler message as a CUDA programming error. Follow an actual call path when reading source instead of treating familiarity with project names as understanding of the whole system.

**中文：** Inductor 是将捕获计算进一步降低到可执行实现的编译后端。Triton 是相关 GPU 路径中用于 kernel 编程与生成的一种工具，并不等于整个 PyTorch 编译器；原生库调用和其他生成代码也可能参与执行。首先应理解各层边界：Python 捕获、图变换、算子降低、kernel 执行和运行时调度。这样可以定位失败发生在哪一层，而不把所有编译器信息都当成 CUDA 编程错误。学习源码时也应围绕一个实际调用路径展开，避免仅靠记住多个项目名称形成似懂非懂的整体印象。

**English:** Guards encode assumptions under which a compiled region is reusable. Shape, stride, dtype, device, and relevant Python values can affect those assumptions. A new input pattern may trigger recompilation or a different path. Dynamic-shape support can reduce specialization in some cases, but it does not make all input variation free. Test the distribution of production-like inputs rather than timing one fixed shape forever. Record cold compilation, warm execution, and the number of observed recompilations as separate outcomes. Otherwise, a favorable fixed-shape speedup can conceal repeated compilation costs under variable-length service requests.

**中文：** guard 表达编译区域可以复用时成立的假设，形状、步幅、类型、设备及相关 Python 值都可能影响这些假设。新的输入模式可能触发重新编译或另一条路径。动态形状支持能够在部分情形减少特化，但不会让所有输入变化都没有成本。应测试接近真实业务的输入分布，而不是永远计时一个固定形状。首次编译、热态执行和观察到的重新编译次数应分别记录，否则某个固定尺寸下漂亮的加速比例，可能掩盖真实服务面对变长请求时频繁付出的编译代价。

**English:** A custom operator is often an intentional opaque boundary. Providing a fake implementation lets the compiler reason about its outputs, but does not necessarily let it fuse through the operator's internal CUDA code. If the operation is naturally expressible as existing PyTorch operators, keeping that composition may expose more optimization opportunities than wrapping it in a custom op. Write custom operators for a concrete missing capability or integration boundary, and measure whether the resulting boundary helps the actual workload. A custom kernel beating one isolated baseline does not establish that replacing a composed expression beats the compiler's joint optimization of adjacent operations.

**中文：** 自定义算子往往是有意建立的不透明边界。提供 fake 实现让编译器能够推理输出，却不一定允许它穿过算子内部 CUDA 代码继续融合。如果操作本来可以自然表达为已有 PyTorch 算子的组合，保留这种组合有时比封装为自定义算子暴露更多优化机会。应为了明确缺失的能力或集成边界编写自定义算子，并测量该边界是否帮助实际负载。不能仅因为自写 kernel 比单个基线快，就默认它替换之后一定优于编译器对相邻运算进行整体优化的结果。

**English:** Separate compiler debugging from numerical and hardware debugging. First run eager mode on a tiny input and compare with a reference. Then test registration and fake behavior. Next use a capture-oriented backend to isolate graph handling, and finally exercise the intended optimizing backend. If failure appears only in the last stage, preserve the smallest reproducer with versions and input metadata. Disabling compilation can be a diagnostic step, but it should not silently change the benchmark being compared. A useful failure record should identify mathematics, metadata, capture, code generation, or environment as the affected boundary rather than simply saying compilation does not work.

**中文：** 编译器排错应与数值和硬件排错分开。先用小输入在 eager 模式运行并比较参考，再检查注册和 fake 行为；接着通过偏重图捕获的后端隔离图处理，最后执行目标优化后端。如果问题只在最后阶段出现，就保留包含版本和输入元数据的最小复现。关闭编译可以是诊断步骤，但不能悄悄改变正在比较的基准。有效的故障记录应该让其他人判断问题属于数学实现、元数据契约、图捕获、代码生成还是运行环境，而不是只得到一句“compile 不能用”。

## 7. Lab A: Observe Layout Instead of Guessing / 实验 A：观察布局而非猜测

**English:** Use an isolated CPU environment for the first experiment. Save the program as `layout.py`. Every assertion targets a specific storage or metadata fact, so the experiment can run without a GPU. The transposed tensor intentionally fails a particular `view` operation; the lesson is not that every non-contiguous tensor makes every possible view invalid. The clone and reshaped copy checks establish independence for these particular inputs, while the expanded tensor demonstrates a zero-stride mapping. Match each assertion to the preceding formulas, predict the result, and then run it. Revise an incorrect storage model rather than changing assertions to fit observed output.

**中文：** 第一个实验使用隔离的 CPU 环境，将程序保存为 `layout.py`。每项断言针对具体存储或元数据事实，因此不需要 GPU。转置张量会故意使特定的 `view` 操作失败，但这并不是说每个非连续张量的所有 view 都无效。克隆和 reshape 副本检查证明的是这些特定输入下的独立性，扩展张量则演示零步幅映射。实验时应把每项断言与前文公式对应，先预测结果，再执行验证；如果预测错误，优先修正对存储关系的理解，而不是修改断言去迎合程序输出。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python layout.py
```

```python
import torch

x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
t = x.t()
assert x.stride() == (4, 1)
assert t.shape == (4, 3) and t.stride() == (1, 4)
assert t.data_ptr() == x.data_ptr()
t[1, 2] = 99
assert x[2, 1].item() == 99
try:
    t.view(-1)
except RuntimeError:
    pass
else:
    raise AssertionError("this transpose cannot be flattened by view")

flat = t.reshape(-1)
flat[0] = -100
assert x[0, 0].item() == 0
same = x.contiguous()
assert same.data_ptr() == x.data_ptr()
independent = x.clone()
independent[0, 0] = 100
assert x[0, 0].item() == 0

expanded = x[:1].expand(3, 4)
assert expanded.stride()[0] == 0
assert expanded[0].data_ptr() == expanded[2].data_ptr()
sliced = x[1:]
assert sliced.storage_offset() == 4
assert sliced.data_ptr() == x.data_ptr() + 4 * x.element_size()
assert torch.tensor(3.0).ndim == 0
assert torch.empty((0, 4)).numel() == 0
print("shape, strides, offsets, aliasing, and empty/scalar cases: passed")
```

**English:** Extend the experiment by changing a dimension so that batch size no longer equals feature size. Compare adding a vector of feature biases with adding a column of batch offsets. Both can be meaningful, but they are different formulas. Write a hand-computed two-dimensional expected result before using a framework reference. This catches semantic axis mistakes that two identical implementations would otherwise reproduce together. An oracle is useful only when it is sufficiently independent of the suspected bug. Elementwise agreement cannot establish the intended semantics if the reference and optimized version both copy the same incorrect indexing logic.

**中文：** 可以改变某个维度，使批次大小不再等于特征数，再比较加入特征偏置向量与加入批次偏移列的区别。两者都可能有业务意义，但公式不同。使用框架参考前，先手算一个二维期望结果，可以发现两份相似实现可能共同复制的语义轴错误。正确性基线只有在足够独立于被怀疑的缺陷时才真正有用。如果基线和优化实现都从同一段错误索引逻辑改写，即使逐元素完全一致，也不能证明它们满足预期业务含义。

## 8. Lab B: Register an Affine Operator / 实验 B：注册仿射算子

**English:** Create a separate working directory containing `affine.cpp`, `affine_cuda.cu`, and `check_affine.py` exactly as shown. The default run builds only the CPU source, allowing the schema, numerical behavior, fake registration, and graph integration to be checked without a functioning CUDA driver. The optional CUDA run adds the device source. A C++ compiler and Ninja are prerequisites; the extension loader compiles against the active Python environment's PyTorch installation. Put all three files in one directory and run there, so a source-path mistake is not misclassified as a compiler or framework incompatibility.

**中文：** 在独立工作目录中按下面内容创建 `affine.cpp`、`affine_cuda.cu` 和 `check_affine.py`。默认运行只构建 CPU 源文件，因此可以在没有可用 CUDA 驱动的情况下检查 schema、数值行为、fake 注册和图集成；可选 CUDA 运行才加入设备源文件。前置工具包括 C++ 编译器与 Ninja，扩展加载器会针对当前 Python 环境安装的 PyTorch 编译。三个文件应放在同一目录，并从该目录运行，避免把源文件路径错误误判为编译器或框架不兼容。

**English:** CPU implementation and shared schema, `affine.cpp`:

**中文：** CPU 实现与共享 schema，`affine.cpp`：

```cpp
#include <ATen/ATen.h>
#include <torch/library.h>

at::Tensor affine_cpu(const at::Tensor& x, double scale, double bias) {
    TORCH_CHECK(x.is_cpu(), "CPU tensor required");
    TORCH_CHECK(x.scalar_type() == at::kFloat, "float32 required");
    TORCH_CHECK(x.is_contiguous(), "default contiguous layout required");
    TORCH_CHECK(!x.requires_grad(), "this teaching op is inference-only");
    auto y = at::empty_like(x);
    const float* src = x.const_data_ptr<float>();
    float* dst = y.mutable_data_ptr<float>();
    const float a = static_cast<float>(scale);
    const float b = static_cast<float>(bias);
    for (int64_t i = 0; i < x.numel(); ++i) dst[i] = src[i] * a + b;
    return y;
}

TORCH_LIBRARY(course08, m) {
    m.def("affine(Tensor x, float scale, float bias) -> Tensor");
}
TORCH_LIBRARY_IMPL(course08, CPU, m) {
    m.impl("affine", &affine_cpu);
}
```

**English:** CUDA implementation, `affine_cuda.cu`. Its empty-input return avoids an invalid zero-block launch. The grid-stride loop bounds the grid size while supporting larger tensors. The device guard and current stream preserve the caller's execution context. The code checks launch status without forcing all work on the device to finish. This source is an executable extension component, not a standalone `.cu` program with a `main` function. Link it with the preceding file because the public schema is registered in that translation unit; compiling device code alone is not complete framework integration.

**中文：** CUDA 实现保存在 `affine_cuda.cu`。空输入直接返回，避免无效的零块启动；grid-stride 循环在限制网格大小的同时支持较大张量；设备 guard 和当前流维持调用方执行上下文。代码检查启动状态，但不会强制设备上的所有工作完成。它是可执行扩展中的一个组成部分，不是带有 `main` 的独立 `.cu` 程序。构建时必须与前一个文件共同链接，因为公开 schema 在另一个翻译单元中注册，单独编译设备代码无法代替完整框架集成。

```cpp
#include <ATen/ATen.h>
#include <torch/library.h>
#include <c10/cuda/CUDAGuard.h>
#include <c10/cuda/CUDAStream.h>
#include <c10/cuda/CUDAException.h>
#include <algorithm>

__global__ void affine_kernel(const float* x, float* y, int64_t n,
                              float scale, float bias) {
    int64_t i = static_cast<int64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    const int64_t step = static_cast<int64_t>(blockDim.x) * gridDim.x;
    for (; i < n; i += step) y[i] = x[i] * scale + bias;
}

at::Tensor affine_cuda(const at::Tensor& x, double scale, double bias) {
    TORCH_CHECK(x.is_cuda(), "CUDA tensor required");
    TORCH_CHECK(x.scalar_type() == at::kFloat, "float32 required");
    TORCH_CHECK(x.is_contiguous(), "default contiguous layout required");
    TORCH_CHECK(!x.requires_grad(), "this teaching op is inference-only");
    const c10::cuda::CUDAGuard guard(x.device());
    auto y = at::empty_like(x);
    const int64_t n = x.numel();
    if (n == 0) return y;
    const int threads = 256;
    const int blocks = static_cast<int>(std::min<int64_t>((n - 1) / threads + 1, 4096));
    auto stream = c10::cuda::getCurrentCUDAStream(x.get_device());
    affine_kernel<<<blocks, threads, 0, stream.stream()>>>(
        x.const_data_ptr<float>(), y.mutable_data_ptr<float>(), n,
        static_cast<float>(scale), static_cast<float>(bias));
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    return y;
}
TORCH_LIBRARY_IMPL(course08, CUDA, m) {
    m.impl("affine", &affine_cuda);
}
```

**English:** Loader and checks, `check_affine.py`. The fake implementation mirrors the real dtype, layout, and gradient restrictions. Device support comes separately from dispatcher registrations: passing fake metadata checks does not prove that a real kernel for that device has been built. Numerical tests cover a scalar, empty input, an odd element count, and a matrix. Three deliberate rejection cases cover unsupported dtype, non-contiguous layout, and gradient-requiring input. The capture-only and optimizing compiler checks are labeled separately so their results cannot be confused. If a stage fails, report the check, input shape, and exact exception before narrowing the cause; deleting a failed assertion does not validate the extension.

**中文：** 加载器和检查程序为 `check_affine.py`，fake 实现对应真实实现的数据类型、布局和梯度限制。设备支持则由分发器注册另行提供：通过 fake 元数据检查，并不能证明相应设备的真实 kernel 已经构建。数值测试覆盖标量、空输入、奇数元素数量和矩阵；三个有意拒绝的情况覆盖不支持的数据类型、非连续布局和要求梯度的输入。图捕获检查与优化编译器检查分别标记，使结果不被混淆。若某一阶段失败，应先报告是哪一项检查、输入形状是什么以及具体异常，再缩小问题范围，而不是删除失败断言后宣称整个扩展已经验证。

```python
import os
from pathlib import Path
import torch
from torch.utils.cpp_extension import load

root = Path(__file__).resolve().parent
use_cuda = os.environ.get("COURSE08_CUDA") == "1"
if use_cuda and (torch.version.cuda is None or not torch.cuda.is_available()):
    raise RuntimeError("CUDA-enabled PyTorch and a working GPU driver are required")
sources = [str(root / "affine.cpp")]
if use_cuda:
    sources.append(str(root / "affine_cuda.cu"))
load(name="course08_affine_cuda" if use_cuda else "course08_affine_cpu",
     sources=sources, is_python_module=False, with_cuda=use_cuda,
     extra_cflags=["-O2"], extra_cuda_cflags=["-O2"], verbose=False)

@torch.library.register_fake("course08::affine")
def affine_fake(x, scale, bias):
    torch._check(x.dtype == torch.float32)
    torch._check(x.is_contiguous())
    torch._check(not x.requires_grad)
    return torch.empty_like(x)

op = torch.ops.course08.affine.default
device = "cuda" if use_cuda else "cpu"
torch.manual_seed(7)
for shape in [(), (0,), (257,), (3, 5)]:
    x = torch.randn(shape, dtype=torch.float32, device=device)
    before = x.clone()
    y = op(x, 1.5, -0.25)
    torch.testing.assert_close(y, x * 1.5 - 0.25, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(x, before, rtol=0, atol=0)
    if x.numel():
        assert y.data_ptr() != x.data_ptr()
    torch.library.opcheck(op, (x, 1.5, -0.25))

for invalid in [torch.ones(4, dtype=torch.float64, device=device),
                torch.ones((3, 5), device=device).t(),
                torch.ones(4, device=device, requires_grad=True)]:
    try:
        op(invalid, 1.5, -0.25)
    except RuntimeError:
        pass
    else:
        raise AssertionError("unsupported input should be rejected")

def pipeline(x):
    return torch.relu(op(x, 1.5, -0.25))

x = torch.randn((3, 5), device=device)
for backend in ["eager", "inductor"]:
    compiled = torch.compile(pipeline, backend=backend, fullgraph=True)
    torch.testing.assert_close(compiled(x), pipeline(x), rtol=1e-5, atol=1e-6)
    print(f"compiled backend={backend}: passed")

if use_cuda:
    stream = torch.cuda.Stream()
    with torch.cuda.stream(stream):
        stream_input = torch.randn((257,), device="cuda")
        stream_output = op(stream_input, 1.5, -0.25)
        stream_reference = stream_input * 1.5 - 0.25
    stream.synchronize()
    torch.testing.assert_close(stream_output, stream_reference, rtol=1e-5, atol=1e-6)
print(f"numerics, registration, rejection, and compilation on {device}: passed")
```

```bash
MAX_JOBS=1 .venv/bin/python check_affine.py
```

**English:** Run the CUDA variant only in a separate, compatible CUDA-enabled PyTorch environment. Confirm the wheel's CUDA version, toolkit support, and working driver before using the command below. The architecture setting matches the inspected RTX 4060; use the actual target architecture on another machine. Failure of this preflight is an environment result, not a numerical result. The CPU-only environment created for Lab A is intentionally insufficient for this command. Do not remove the availability check to force execution. Preserve the completed CPU validation and list the CUDA evidence that remains missing.

**中文：** CUDA 变体必须在另一个兼容且启用 CUDA 的 PyTorch 环境中运行，执行下面命令前，先确认 wheel 的 CUDA 版本、工具链支持情况和驱动可用性。架构设置对应已检查到的 RTX 4060，换机器时应使用真实目标架构。预检查失败属于环境结果，不是数值结果。实验 A 创建的 CPU 环境有意不满足这个命令的要求，不能通过删除可用性检查来强行继续。环境尚未就绪时，应保留已通过的 CPU 验证，并清楚列出尚未建立证据的 CUDA 部分。

```bash
COURSE08_CUDA=1 TORCH_CUDA_ARCH_LIST=8.9 MAX_JOBS=1 python check_affine.py
```

## 9. Measure the Right Boundary / 测量正确的边界

**English:** Decide whether the measurement covers kernel execution, operator invocation, a compiled pipeline, or an end-to-end request. These boundaries include different costs. A kernel event measurement can exclude Python dispatch, layout conversion, allocation outside the region, and network time. A host timer without CUDA synchronization may measure submission instead of completion. Write the start and end events in words before writing the timer code, then verify that the chosen mechanism observes those events on the relevant stream. This avoids comparing two values both called latency that actually measure different intervals.

**中文：** 先决定测量边界是 kernel 执行、算子调用、编译后流水线，还是端到端请求，因为它们包含不同成本。kernel 事件计时可能排除 Python 分发、布局转换、区域之外的分配和网络时间；没有正确 CUDA 同步的主机计时，则可能只测到提交而非完成。编写计时代码之前，先用文字写清开始和结束事件，再检查计时机制是否在相关流上观察到了这些事件。这个步骤虽然简单，却能防止最常见的错误：两组数字都叫“延迟”，实际上测量的不是同一件事。

**English:** Warm-up must match the intended steady state. Compilation, allocator growth, module loading, and cache behavior can all affect early iterations. Excluding them is reasonable for a stated warm-execution question, but startup and cold-request behavior may matter separately. Report both when the service is frequently restarted or receives rare shapes. Do not hide a long compilation cost inside an unreported warm-up and then imply that every user request enjoys the measured warm latency. Record warmup count, warmup inputs, and whether measured execution reuses the same state.

**中文：** 预热必须与目标稳定状态相符。编译、分配器扩容、模块加载和缓存行为都可能影响前几次执行。如果问题明确是热态性能，排除这些开销可以合理，但启动和冷请求行为也可能需要单独评估。服务频繁重启或经常出现罕见形状时，应该同时报告两者。不能把很长的编译时间隐藏进未报告的预热，再暗示每条用户请求都具有测得的热态延迟。描述基准时，预热次数、预热输入和正式测量是否复用同一份状态都属于必要信息。

**English:** A simple affine kernel is primarily an integration exercise. It is not expected to beat every framework path, especially a compiler that fuses adjacent elementwise operations. If a custom operator prevents fusion with a following activation, a locally efficient kernel can increase total launches and memory traffic. Compare the whole expression under equivalent numerical and execution settings. A negative result is useful when it identifies the lost optimization opportunity and explains why the custom boundary is not suitable for that workload. The engineering result is a defensible decision process, not a speedup greater than one at any cost.

**中文：** 简单仿射 kernel 主要用于学习集成，并不预期战胜所有框架路径，尤其不能默认优于能够融合相邻逐元素运算的编译器。如果自定义算子阻止与后续激活融合，即使局部 kernel 高效，也可能增加总启动次数和内存流量。应在等价数值与执行设置下比较整个表达式。没有加速的结果同样有价值，只要能够指出失去了什么优化机会，并解释该自定义边界为什么不适合此类负载。工程成果是可信的判断过程，而不是无论如何都得到一个大于一的加速倍数。

**English:** Allocation and layout conversion should be visible in the experiment. If the custom path requires contiguous input, benchmark both already-contiguous input and the complete path that converts a representative non-contiguous input. The latter must include the conversion cost. Similarly, compare output allocation policies fairly: a version reusing a preallocated buffer and a version allocating every call answer different questions. Record peak memory and retained storage when a throughput gain could be purchased through extra copies or caching. Hiding one side of the time-memory tradeoff prevents others from judging suitability for their device and service capacity.

**中文：** 分配与布局转换应该在实验中可见。如果自定义路径要求连续输入，就分别测量已经连续的输入，以及对代表性非连续输入进行转换的完整路径，后者必须包含转换成本。输出分配策略也应公平比较：复用预分配缓冲区与每次重新分配，回答的是不同问题。如果吞吐提升可能来自额外复制或缓存，就同时记录峰值内存和被保留的存储。性能优化涉及时间与空间取舍，隐去其中一边会让其他人无法判断结果是否适合自己的设备和服务容量。

**English:** Use profiling to test a hypothesis, not to decorate a report. If you suspect a stream error, inspect ordering and run a non-default-stream correctness case. If you suspect dispatch overhead, compare small and large tensors and examine CPU activity. If you suspect memory traffic, inspect the actual kernels and layout conversions before applying a bandwidth formula. Keep the workload, version, dtype, shape, and device constant for an A/B comparison. An optimization conclusion should identify which observation changed and which possible explanations were controlled. A single timeline screenshot neither identifies a bottleneck automatically nor proves that a change caused a speedup.

**中文：** 性能分析工具应当用于检验假设，而不是装饰报告。怀疑流错误，就检查顺序并运行非默认流正确性案例；怀疑分发开销，就比较大小张量并观察 CPU 活动；怀疑内存流量，就在套用带宽公式之前查看实际 kernel 和布局转换。A/B 比较应保持负载、版本、类型、形状和设备一致。优化结论需要指出哪项观察改变了，以及哪些其他解释已经被控制。单张时间线截图既不能自动说明瓶颈，也不能证明一项改动造成了性能提升。

## 10. Ten Exercises with Answers / 十道习题与参考答案

### 1. Shape Is Not Layout / 形状不等于布局

**English:** Question: two tensors have shape `(4, 3)`, but one is a transpose. Can a flat pointer loop necessarily process both? Answer: no. Shape defines logical coordinates, while strides and storage relationships define where values live. Either support the actual indexing or reject unsupported layout. A test using only freshly allocated contiguous tensors cannot establish general support. Include a transpose, an offset slice, and an expanded input to expose different assumptions; rejecting some cases is valid when that restriction is explicit. Accepting input and accessing it under false assumptions is the defect.

**中文：** 问题：两个张量形状都是 `(4, 3)`，其中一个来自转置，线性指针循环一定能同时处理它们吗？答案：不能。形状定义逻辑坐标，步幅与存储关系定义数值实际位置。实现应支持真实索引，或者拒绝不支持的布局。只用新分配的连续张量测试，无法建立通用支持的证据。应加入转置、带偏移切片和扩展输入以暴露不同假设；只要限制写得明确，拒绝其中一些情况是有效设计，错误的是接收了输入却按照不成立的前提访问数据。

### 2. Reshape Cost / reshape 的成本

**English:** Question: why can replacing `view` with `reshape` remove an error while introducing a performance regression? Answer: reshape may materialize a copy when a view is impossible. The resulting values and shape can be correct while the new allocation and data movement affect latency and memory. Inspect the original layout and measure the full consumer path. Do not label reshape as universally slow either: for compatible strides it may reuse storage. The behavior depends on the input and the documented contract. After repairing a layout error, revisit the performance path; runnable code does not prove that the original performance assumptions still hold.

**中文：** 问题：为什么把 `view` 换成 `reshape` 可能消除错误，却引入性能退化？答案：无法建立视图时，reshape 可能物化副本。结果形状和数值虽然正确，新增分配与数据移动仍会影响延迟和内存。应检查原布局并测量完整消费者路径。也不能因此把 reshape 一概称为慢操作，因为步幅兼容时它可能复用存储。行为取决于输入和契约。修复一个布局错误后，应重新检查性能路径，而不是把“代码可以运行”直接当作原性能假设仍然成立的证明。

### 3. Broadcasting and Writes / 广播与写入

**English:** Question: why is an expanded input a poor assumption for one-thread-per-logical-element in-place writes? Answer: a zero stride can make several logical indices share a physical destination. Independent logical work does not imply independent storage. Use a non-overlapping output or a specifically defined reduction/update algorithm. This is a storage-conflict issue, not merely a shape issue. A mathematically broadcastable expression does not authorize arbitrary parallel mutation of the broadcast view. Test actual alias relationships, not just agreement between input and output logical element counts.

**中文：** 问题：为什么不能默认对扩展输入按每个逻辑元素一个线程进行原地写入？答案：零步幅可能让多个逻辑索引共享物理目的地址，逻辑工作独立不等于存储独立。应使用不重叠的输出，或者采用具有明确定义的归约或更新算法。这是存储冲突问题，不只是形状问题。某个表达式在数学上允许广播，并不授权对广播视图进行任意并行修改。测试应检查实际别名关系，而不只是确认输出元素数量与输入逻辑元素数量相同。

### 4. Fake Implementation / fake 实现

**English:** Question: should the fake implementation read the input and calculate approximate numerical output? Answer: no. It describes output metadata under the same input contract as the real implementation, without depending on actual values. Shape, dtype, device, and layout must agree. If the output shape depends on data, a more appropriate supported mechanism is needed instead of inventing a constant shape. Passing ordinary numerical tests does not validate this metadata contract. Separate the abstract information needed by compilation from real execution data; code that returns a plausible tensor can still model the operator incorrectly.

**中文：** 问题：fake 实现是否应该读取输入并计算近似数值输出？答案：不应该。它在与真实实现相同的输入契约下描述输出元数据，不依赖真实数值。形状、类型、设备和布局必须一致。如果输出形状依赖数据，就需要使用适当且受支持的机制，而不是虚构一个固定形状。普通数值测试通过，并不能验证元数据契约。理解 fake 的用途后，就能把编译所需的抽象信息与实际执行所需的数据分开，避免用看起来能返回张量的代码掩盖错误建模。

### 5. Numerical Tests and opcheck / 数值测试与 opcheck

**English:** Question: does passing `opcheck` prove the affine formula is correct? Answer: no. Registration checks and a reference comparison establish different properties. Keep an explicit formula comparison, input-mutation checks, unsupported-input checks, and registration checks. When one fails, record its category. Adding more random inputs to a numerical test does not replace checking a wrong mutation declaration, just as a correct declaration does not fix an off-by-one index in the CUDA kernel. Complete validation maps distinct checks to real contracts and keeps those distinctions in the report instead of relying on one function for every conclusion.

**中文：** 问题：通过 `opcheck` 能否证明仿射公式正确？答案：不能。注册检查与参考比较建立不同性质。应同时保留明确公式比较、输入修改检查、不支持输入检查和注册检查，失败时记录类别。给数值测试增加更多随机输入，不能替代对错误修改声明的检查；同样，声明正确也不能修复 CUDA kernel 中差一位的索引。完整验证不是寻找一个包办所有结论的函数，而是让多种检查分别对应真实契约，并在报告中保持这种区别。

### 6. Evaluation Mode / 评估模式

**English:** Question: is `model.eval()` sufficient to ensure no gradients are recorded? Answer: no. Evaluation mode changes relevant module behavior, while gradient recording is controlled separately. State whether inference mode or no-grad is active in a benchmark. Otherwise comparing two runs may mix module-state differences, autograd overhead, and kernel changes. For the teaching operator, gradient-requiring inputs are rejected rather than implicitly receiving an unimplemented backward behavior. Express the inference contract at entry rather than relying on the unenforced assumption that callers probably will not train.

**中文：** 问题：`model.eval()` 是否足以保证不记录梯度？答案：不足以。评估模式改变相关模块行为，梯度记录则单独控制。基准中应说明是否使用推理模式或 no-grad，否则两次运行可能混合模块状态差异、自动求导开销与 kernel 改动。本教学算子明确拒绝要求梯度的输入，而不是让调用方隐式得到未实现的反向行为。面向推理的契约应在入口就清楚表达，不能依赖“实际调用者大概不会训练”这样没有约束力的假设。

### 7. Diagnose a Stream Bug / 排查流错误

**English:** Question: an extension works in a default-stream test but intermittently reads stale values in a larger pipeline. What should be checked first? Answer: the device guard, launch stream, and dependency ordering. Test producer and consumer work on the framework's non-default current stream, then synchronize at a deliberate observation boundary. A blanket device synchronization may hide the ordering defect and destroy overlap. Repair the stream contract rather than declaring the problem solved because additional synchronization made the symptom disappear. Validate correctness and performance impact separately, including whether the promise survives callers using multiple devices and streams.

**中文：** 问题：扩展在默认流测试中正常，放入较大流水线后却偶尔读到旧值，应先检查什么？答案：设备 guard、启动流和依赖顺序。让生产者与消费者工作在框架当前的非默认流上，再在明确观察边界同步。粗暴增加整设备同步可能隐藏顺序缺陷并破坏重叠执行。应修复流契约，而不是因为加入同步后现象消失就宣布问题解决。正确性修复与性能影响需要分别验证，尤其要确保算子在调用方使用多个设备和流时仍然保持同样的承诺。

### 8. Diagnose Compilation Cost / 排查编译成本

**English:** Question: one fixed shape is fast after warm-up, but real variable-length requests are slow. What evidence is missing? Answer: input-distribution coverage, guard behavior, recompilation counts, and cold-path timing. Test representative shapes and layouts and report compilation separately from steady-state execution. Dynamic shapes may help some cases, but enabling them is a hypothesis to verify, not proof. The fastest repeated fixed-shape result does not establish the latency of a service handling a changing workload. Also check queueing outside the framework so admission delay and recompilation are not merged into a vague claim that the model is slow.

**中文：** 问题：固定形状预热后很快，真实变长请求却慢，缺少什么证据？答案：缺少输入分布覆盖、guard 行为、重新编译次数和冷路径计时。应测试有代表性的形状与布局，并把编译开销与稳定执行分别报告。动态形状可能帮助某些情况，但启用它只是待验证假设，不是证明。固定形状反复运行得到的最好结果，不能建立变化负载下服务延迟的结论。还应检查请求是否在框架外排队，避免把入口等待与重新编译都混进一个含糊的“模型慢”判断。

### 9. Design an Extension Test Matrix / 设计算子测试矩阵

**English:** Question: propose the minimum meaningful matrix for this operator. Answer: CPU and available CUDA backends; scalar, empty, odd-sized, and ordinary multidimensional inputs; supported float32 and rejected dtype/layout cases; input preservation and fresh output; fake and registration checks; eager and compiled execution; and a non-default CUDA stream. Numerical tolerances should be stated. Add gradient tests only after defining and implementing that capability; rejection is the intended current contract. Expand this matrix whenever support expands so each new capability has independent evidence.

**中文：** 问题：为本算子提出最小且有意义的测试矩阵。答案：包括 CPU 和可用的 CUDA 后端，标量、空输入、奇数尺寸和普通多维输入，支持的 float32 与被拒绝类型及布局，输入保持和新输出，fake 与注册检查，eager 与编译执行，以及非默认 CUDA 流。数值容差必须明确。只有定义并实现梯度能力后再增加相应通过测试，目前的契约是明确拒绝。扩展支持范围时，也应同步扩展这张矩阵，使新的能力有独立证据，而不是沿用旧测试掩盖新风险。

### 10. Decide Whether to Keep a Custom Kernel / 判断是否保留自定义 kernel

**English:** Question: the custom affine kernel is faster in isolation, but the compiled affine-plus-activation pipeline is slower. What should the report conclude? Answer: the local kernel improvement did not translate to the measured pipeline, possibly because the custom boundary prevented fusion or added traffic. Verify that explanation with profiling and equivalent settings. Keep the kernel only if another concrete requirement or workload justifies it. A useful engineering result can be a well-supported decision not to deploy an optimization. Report limits and counterexamples instead of selecting one favorable size and presenting a local observation as a general performance advantage.

**中文：** 问题：自定义仿射 kernel 单独更快，但编译后的仿射加激活流水线更慢，报告应如何结论？答案：局部 kernel 改善没有转化为所测流水线收益，可能因为自定义边界阻止融合或增加流量。需要用性能分析和等价设置验证这一解释。只有其他具体需求或负载能够支持时，才保留它作为部署选择。工程上有价值的结果也可以是基于证据决定不部署某项优化；应报告适用边界和反例，而不是挑选唯一有利尺寸，把局部现象包装成普遍性能优势。

## 11. Acceptance and Next Steps / 验收与后续学习

**English:** Completion means being able to derive a tensor's logical-to-physical mapping, state the teaching operator's exact contract, and reproduce the supported checks while explaining every deliberate rejection. You should distinguish numerical correctness, registration correctness, compilation compatibility, stream correctness, and performance. A failure in one category does not erase evidence from another, but a successful category cannot stand in for an untested one. Preserve source, environment, command, input metadata, and results so another engineer can independently repeat the argument. Such evidence shows understanding of framework and implementation boundaries more clearly than a callable extension alone.

**中文：** 完成本课意味着能够推导张量从逻辑到物理的映射，准确描述教学算子的契约，并复现受支持的检查，同时解释每一项有意拒绝。你应该区分数值正确性、注册正确性、编译兼容性、流正确性和性能。一类失败不会抹掉另一类已有证据，但一类成功也不能代替另一类尚未执行的测试。保留源代码、环境、命令、输入元数据和结果，才能让其他工程师独立重复论证。这样的材料比只展示一个可调用的扩展函数，更能证明你理解框架与底层实现之间的边界。

**English:** Read Course 09 to compare these ideas with Candle's Rust abstractions, and Course 10 to see how operator execution fits into a serving scheduler. Use Course 06 when the remaining problem is inside a kernel, and Course 12 when the experiment needs stronger measurement design. Do not assume that a working PyTorch extension is automatically callable from every inference runtime. Runtime integration, supported model paths, tensor ownership, stream conventions, and build systems must be checked at each new boundary. The value of custom-operator work includes identifying these implicit conditions and establishing verifiable connections, beyond making a computation execute.

**中文：** 阅读课程 09 可以将这些思想与 Candle 的 Rust 抽象对照，课程 10 则展示算子执行如何嵌入推理调度。当剩余问题位于 kernel 内部时，参考课程 06；实验需要更严格度量设计时，参考课程 12。不能假定能工作的 PyTorch 扩展可以自动被所有推理运行时调用。每跨入一个新边界，都需要检查运行时集成、受支持模型路径、张量所有权、流约定和构建系统。学习自定义算子的价值，正是在能够完成计算之外，还能识别这些隐含条件并建立可验证的连接。

## Validation Record / 验证记录

**English:** On 2026-09-18, the examples were extracted from this Markdown into a temporary directory. In an isolated CPython 3.14 environment with PyTorch 2.14.0+cpu, the layout assertions passed, the C++ CPU extension built and loaded, numerical and registration checks passed for four shape cases, all three unsupported-input cases were rejected, and both `eager` and `inductor` compilation checks passed. A missing-NumPy warning appeared, but no example uses NumPy. The CUDA extension and non-default CUDA-stream test were not built or run in a CUDA-enabled PyTorch environment; their correctness remains unverified by execution.

**中文：** 2026-09-18，示例从本 Markdown 提取至临时目录。在隔离的 CPython 3.14、PyTorch 2.14.0+cpu 环境中，布局断言通过，C++ CPU 扩展构建并加载成功，四种形状的数值和注册检查通过，三种不支持输入均按预期拒绝，`eager` 与 `inductor` 编译检查都通过。运行出现未安装 NumPy 的警告，但示例没有使用 NumPy。CUDA 扩展和非默认 CUDA 流测试尚未在启用 CUDA 的 PyTorch 环境中构建或运行，其正确性仍未获得执行验证。

## References / 参考资料

**English:** Primary sources checked on 2026-09-18. Explanations and examples are original teaching material. Follow versioned API references for reproducibility and review current release notes before changing the pinned environment.

**中文：** 以下一手资料核验于 2026-09-18，讲解与示例为原创教学材料。为保持复现，应使用带版本的 API 资料；修改固定环境前再检查当前发布说明。

- [Tensor views / 张量视图](https://docs.pytorch.org/docs/2.14/tensor_view.html)
- [Custom operator overview / 自定义算子概述](https://docs.pytorch.org/tutorials/advanced/custom_ops_landing_page.html)
- [Custom C++ and CUDA operators / 自定义 C++ 与 CUDA 算子](https://docs.pytorch.org/tutorials/advanced/cpp_custom_ops.html)
- [Operator registration APIs / 算子注册接口](https://docs.pytorch.org/docs/2.14/library.html)
- [torch.compile tutorial / torch.compile 教程](https://docs.pytorch.org/tutorials/intermediate/torch_compile_tutorial)
- [CUDA semantics / CUDA 语义](https://docs.pytorch.org/docs/2.14/notes/cuda.html)
- [Numerical accuracy / 数值精度](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html)
- [C++ extension loader / C++ 扩展加载器](https://docs.pytorch.org/docs/2.14/cpp_extension.html)
- [NVIDIA CUDA 13.3 programming guide / NVIDIA CUDA 13.3 编程指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-programming-guide/index.html)
