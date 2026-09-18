# Course 09: Candle and Rust Inference Frameworks / 第九课：Candle 与 Rust 推理框架

## Goals, prerequisites, and pinned environment / 目标、前置知识与固定环境

**English:** This course builds a small, auditable Rust inference pipeline with Candle. You will create a tokenizer, configuration, and safetensors checkpoint locally; load them; execute embedding, pooling, linear projection, and activation; and compare the result with a hand calculation. A second experiment implements a CPU custom operator with explicit dtype and layout restrictions. The goal is to connect Rust ownership and CUDA knowledge to framework behavior without hiding the reasoning behind a large downloaded model.

**中文：** 本课用 Candle 建立一个小型、可审查的 Rust 推理流水线。你会在本地创建分词器、配置和张量权重文件，再加载它们，执行嵌入、池化、线性投影及激活，并与手算结果比较。第二项实验实现明确限定数据类型与布局的 CPU 自定义算子。目标是把 Rust 所有权和 CUDA 知识连接到框架行为，而不是下载巨大模型，把关键推理隐藏在复杂依赖背后。

**English:** Prerequisites are Rust modules, ownership, borrowing, `Result`, basic tensor shapes, matrix multiplication, and the distinction between CPU and GPU execution. [The Candle track](../../frameworks/candle/README.md) supplies the repository context. This chapter emphasizes model execution and extension boundaries; serving schedulers and request management belong to the SGLang course. A working tensor computation is one component of an inference application, so every example names its input semantics and resource assumptions rather than treating a tensor shape as the whole contract.

**中文：** 前置知识包括 Rust 模块、所有权、借用、结果类型、基础张量形状、矩阵乘法，以及 CPU 与 GPU 执行差异。[Candle 主线](../../frameworks/candle/README.md) 提供仓库背景。本章强调模型执行和扩展边界，服务调度与请求管理交给 SGLang 课程。能运行的张量计算只是推理应用的一部分，因此每个例子都要说明输入语义和资源假设，不能把张量形状当作完整契约。

**English:** Verified on 2026-09-18. The executable course uses published `candle-core = 0.11.0`, `candle-nn = 0.11.0`, and `tokenizers = 0.22.2`, with CPU execution only. The local compiler is Rust 1.100.0-nightly, dated 2026-09-17. The host is Ubuntu 26.04.1 with CUDA Toolkit 13.3.73, but the RTX 4060 driver/NVML mismatch prevents GPU validation. The [0.11.0 release](https://github.com/huggingface/candle/releases/tag/0.11.0) and its source are the API baseline; newer main-branch cuTile integration is discussed separately at a fixed commit.

**中文：** 核验日期为 2026 年 9 月 18 日。可执行课程固定使用已发布的核心库 0.11.0、神经网络库 0.11.0 和分词器 0.22.2，仅在 CPU 执行。本地编译器是日期为 2026 年 9 月 17 日的 Rust 1.100.0-nightly。主机为 Ubuntu 26.04.1，工具包为 CUDA 13.3.73，但 RTX 4060 的驱动与 NVML 不匹配，无法验证 GPU。接口基线是 [0.11.0 发布版](https://github.com/huggingface/candle/releases/tag/0.11.0) 及对应源码；较新的主分支 cuTile 集成另用固定提交讨论。

## 1. Locate Candle in the execution stack / 确定 Candle 在执行栈中的位置

**English:** Candle provides Rust tensor operations and model-building components. `candle-core` contains tensors, storage, devices, and operator dispatch; `candle-nn` supplies layers and parameter-loading helpers; `candle-transformers` contains implementations of selected model architectures. Tokenization and checkpoint formats are related components with their own contracts. Understanding this separation lets you identify whether a failure belongs to text preprocessing, model construction, an operator, or the device backend instead of calling every problem a model-loading error.

**中文：** Candle 提供 Rust 张量操作与模型构建组件。核心库包含张量、存储、设备和算子分发，神经网络库提供层与参数加载助手，模型库包含部分架构实现。分词与权重格式则是各有契约的相关组件。理解这些分层，就能判断故障属于文本预处理、模型构造、某个算子还是设备后端，而不是把所有问题统称为模型加载失败，再盲目更换权重或依赖版本。

**English:** A tensor framework describes and executes mathematical operations; a kernel toolchain produces device programs; a serving runtime schedules requests and manages long-lived resources. These layers can cooperate without being substitutes. Rust can implement a server around Candle, while a Candle CUDA backend can call established GPU libraries and custom kernels. Neither fact implies that every inference feature appears automatically. Decide which layer owns batching, caching, stream ordering, and cancellation before adding more components to the stack.

**中文：** 张量框架描述并执行数学操作，内核工具链生成设备程序，服务运行时调度请求并管理长期资源。它们可以协作，但不是互相替代。Rust 可以在 Candle 外面实现服务，Candle 的 CUDA 后端也可以调用成熟 GPU 库和自定义内核，但这不代表全部推理能力自动出现。向执行栈加入组件之前，应先决定由哪一层负责批处理、缓存、流顺序和取消，避免职责在层间模糊漂移。

**English:** A small Rust binary can be attractive for integration, but language choice alone does not establish lower latency or higher throughput. A large matrix multiplication may spend most of its time in the same device library regardless of the host language. Conversely, preprocessing, allocation patterns, synchronization, and request handling can matter greatly for small operations. Compare equivalent workloads and completed execution intervals. The course's tiny model is a correctness laboratory, not evidence that one framework is faster than another.

**中文：** 小型 Rust 程序可能便于集成，但语言选择本身不能证明延迟更低或吞吐更高。大型矩阵乘法无论主机使用什么语言，都可能主要耗时于相同设备库；小操作则可能明显受到预处理、分配方式、同步和请求处理影响。应比较等价工作负载及已经完成的执行区间。本课小模型用于研究正确性，不构成一个框架比另一个更快的性能证据，也不应被包装成部署优越性的结论。

## 2. A tensor has more than a shape / 张量不只有形状

**English:** Treat a tensor as values plus metadata and an execution location. Shape gives dimensions; dtype gives element interpretation; device gives the backend location; layout gives strides and a starting offset into storage. Two tensors with equal shapes can describe different element orders or reside on different devices. Before debugging a numerical mismatch, print or inspect those properties at the operation boundary. A shape match is necessary for many operations but does not prove that both operands represent the intended data.

**中文：** 应把张量理解为数值、元数据和执行位置。形状给出维度，数据类型决定元素解释，设备决定后端位置，布局描述跨度和存储起始偏移。形状相同的两个张量，可能表示不同元素顺序，也可能位于不同设备。排查数值不一致之前，应在算子边界检查这些属性。很多操作确实需要形状匹配，但形状符合并不能证明两个操作数代表预期数据，更不能证明内存解释一致。

**English:** Dimensions need semantic names. An embedding table shaped `[vocabulary, hidden]` is not interchangeable with a sequence activation shaped `[tokens, hidden]`, even if the numbers happen to coincide. For a batched model, identify the batch, sequence, feature, and head axes explicitly. A valid reshape preserves element count but may discard the meaning you intended. Write down the semantic shape at each forward step before using inferred dimensions to shorten the code.

**中文：** 维度需要语义名称。形状为词表乘隐藏维度的嵌入表，与序列长度乘隐藏维度的激活不是同一种东西，即使数字偶然相等也不能互换。批处理模型还应明确批次、序列、特征和注意力头各轴。合法变形保留元素数量，却可能丢掉你原先想表达的意义。使用自动推导维度来缩短代码之前，先写出每一步前向计算的语义形状，避免只顾数字能相乘。

**English:** Cloning a Candle tensor handle is not a request for an independent elementwise copy. The pinned implementation shares internal ownership, which makes passing and retaining views convenient. The actual lifetime of storage can therefore extend beyond the lifetime of one variable. Rust dropping one handle does not imply immediate reclamation if other handles or framework dependencies remain. When memory usage grows, examine retained tensor graphs, model fields, output queues, and caches rather than assuming lexical scope alone determines every allocation's last owner.

**中文：** 克隆 Candle 张量句柄不表示逐元素复制出独立数据。固定版本实现共享内部所有权，因此传递和保留视图很方便，但存储生命周期也可能超出单个变量。Rust 销毁一个句柄时，如果还有其他句柄或框架依赖，资源就不一定立即回收。内存增长时，应检查保留的张量关系、模型字段、输出队列与缓存，不能只依据某个变量的词法作用域，就认定所有分配都已失去最后所有者。

**English:** Reading a tensor into a Rust vector materializes host-visible values. On CPU this may copy data; on GPU it also crosses an execution and transfer boundary. Such conversion is useful for tests and small final outputs but can dominate an inner inference loop. Keep intermediate tensors in their execution domain, and extract only the data needed by the caller. The main experiment deliberately calls `to_vec2` at validation points so the observed result is completed data rather than a merely submitted operation.

**中文：** 把张量读取为 Rust 向量，会得到主机可见数值。在 CPU 上这可能复制数据，在 GPU 上还会跨越执行与传输边界。这种转换适合测试和少量最终输出，却可能主导推理内层循环。应让中间张量停留在执行域内，只提取调用者真正需要的数据。主实验故意在验证位置转成二维向量，以便观察已经完成的数值，而不是把提交成功误认为结果已经可用。

## 3. Device selection and backend support / 设备选择与后端支持

**English:** Choosing `Device::Cpu` makes the experiment explicit and independent of GPU discovery. A CUDA-enabled build additionally needs compatible compiled features, runtime libraries, a usable driver, and a supported device. These are separate conditions. Cargo successfully building a CPU path says nothing about CUDA execution; enabling a CUDA feature says nothing about driver health. Record the actual device used, especially when an application supports fallback, otherwise a seemingly successful GPU experiment may have run entirely on the CPU.

**中文：** 显式选择 CPU 设备，让实验不依赖 GPU 发现。启用 CUDA 的构建还需要兼容编译特性、运行库、可用驱动与受支持设备，这是不同条件。CPU 路径成功构建，不能说明 CUDA 执行；启用 CUDA 特性，也不能证明驱动正常。应用允许回退时尤其要记录实际设备，否则一个看似成功的 GPU 实验，可能从头到尾都运行在 CPU 上，最终性能解释完全偏离事实。

**English:** Model parameters and activations must satisfy the device requirements of the operations combining them. Moving only token IDs to a GPU does not move the embedding weights, and moving an output after computation does not make the computation GPU-resident. Choose the device before loading or constructing model tensors where practical. Treat device transfers as visible pipeline stages with costs, rather than scattering them around individual operations until errors disappear. Mixed-device failures often reveal incomplete ownership of the deployment policy.

**中文：** 模型参数与激活必须满足组合算子的设备要求。只把词元编号搬到 GPU，不会顺便搬走嵌入权重；计算之后再移动输出，也不能让前面的计算变成 GPU 执行。实际中尽量先选择设备，再加载或构造模型张量。把设备传输当成具有成本的明确流水线阶段，不要为了让错误消失，就在每个算子周围随意添加转换。混合设备错误往往暴露部署策略没有统一负责者。

**English:** Backend support is operator-specific. The presence of a dtype in an enumeration does not guarantee that every operation supports it on every device. A CPU reference and a CUDA implementation may also take different computational paths. Test the actual layer sequence and input shapes intended for deployment, including error behavior, instead of treating one successful tensor allocation as proof of full-model support. This distinction becomes particularly important when introducing quantized weights or a new custom operator. Otherwise an unsupported case may remain hidden until its particular execution branch is reached.

**中文：** 后端支持需要逐算子判断。数据类型出现在枚举中，不保证每个设备上的每项操作都支持它。CPU 参考与 CUDA 实现还可能走不同计算路径。应测试真正准备部署的层序列和输入形状，包括失败行为，不能把一次张量分配成功当作整个模型受支持的证明。引入量化权重或新自定义算子时，这种区别尤其重要，否则问题可能直到某个具体分支执行时才暴露。

## 4. Dtypes, numerical policy, and token IDs / 数据类型、数值策略与词元编号

**English:** Token IDs are categorical indices, not floating-point activations. The experiment constructs them as U32 because that is the chosen embedding-index path. Converting IDs to F32 for consistency with weights would change their role and violate the operator's type contract. Conversely, embedding outputs and linear weights use F32 so the hand calculation is transparent. State dtype per tensor role rather than trying to make the entire model use one type indiscriminately.

**中文：** 词元编号是类别索引，不是浮点激活。实验把它们构造为无符号三十二位整数，因为选用的嵌入索引路径接收这种类型。为了与权重一致就把编号转成单精度，会改变其角色并违反算子类型契约。嵌入输出和线性权重则使用单精度，便于手算。应按张量角色规定类型，而不是不加区分地要求整个模型所有张量使用同一种类型，这样的统一反而会制造错误。

**English:** Lower precision affects range, rounding, storage size, and supported kernels. A blanket conversion to a smaller floating-point type is not a complete inference optimization plan. Some reductions or normalization steps may need a deliberate accumulation policy; final outputs need a tolerance appropriate to the workload. Establish an F32 reference first, then change precision while measuring both numerical error and performance. The tiny values here are exactly representable, which justifies exact checks for this limited experiment but not for arbitrary neural networks.

**中文：** 降低精度会影响范围、舍入、存储大小及可用内核。把所有数据统一转成较小浮点类型，不构成完整推理优化计划。某些归约或归一化步骤需要明确累积策略，最终输出需要符合任务的容差。应先建立单精度参考，再改变精度，同时测量数值误差和性能。本实验小数恰好能够精确表示，因此可以采用精确检查，但不能把这个条件推广到任意神经网络，要求所有实现逐位相同。

**English:** Quantization is more than a dtype cast. A quantized checkpoint can include packed values, scales, grouping rules, and a specialized operator contract. The loader and execution implementation must agree on that representation. File suffixes and parameter names alone cannot prove compatibility. When evaluating a quantized model, identify the original model revision, quantization scheme, supported backend path, and quality check. This course creates ordinary F32 safetensors weights specifically to isolate loading and execution from those additional variables.

**中文：** 量化不只是数据类型转换。量化权重可能包含打包数值、比例因子、分组规则及专用算子契约，加载器与执行实现必须认同这种表示。文件后缀和参数名称不能独立证明兼容。评估量化模型时，应明确原模型修订、量化方案、受支持后端路径与质量检查。本课特意创建普通单精度权重，以便把加载和执行问题与这些额外变量分开，避免把某个量化格式问题误判成基础框架错误。

## 5. Layout, transpose, and materialization / 布局、转置与物化

**English:** Candle's [0.11.0 Layout source](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/layout.rs) stores shape, strides in elements, and a starting offset. For a contiguous two-by-three matrix, the usual strides are `[3, 1]`; a transpose can describe the same storage with shape `[3, 2]` and strides `[1, 3]`. The values have not necessarily been physically reordered. This is why an operator receiving storage must also inspect layout instead of reading the first element-count values as though every tensor were contiguous.

**中文：** Candle 的 [0.11.0 布局源码](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/layout.rs) 保存形状、以元素为单位的跨度及起始偏移。连续的两行三列矩阵通常跨度为 `[3, 1]`，转置可以用三行两列及 `[1, 3]` 描述同一存储，而不一定真正重排数值。因此，接收存储的算子还必须检查布局，不能把前若干个元素直接当作所有张量的逻辑顺序读取。

**English:** A contiguous view can still begin at a nonzero offset. Selecting the second row of the two-by-three matrix gives three contiguous elements starting after the first row. A custom operator that checks only contiguity and then starts at storage index zero will silently process the wrong row. The supplied operator uses `contiguous_offsets` to obtain the exact range. Its dedicated offset test exists because an ordinary full-tensor test would never expose this bug.

**中文：** 连续视图仍然可以从非零偏移开始。选择两行三列矩阵的第二行，会得到三个连续元素，但起点位于第一行之后。自定义算子如果只检查连续性，然后从存储索引零开始，就会悄悄处理错误行。本课算子通过连续范围接口取得准确区间，并专门测试偏移。普通完整张量测试根本不会暴露这个缺陷，所以只验证默认输入，很容易把错误的连续假设带进真实模型。

**English:** Calling `contiguous()` requests a tensor with a contiguous logical layout. It can reuse an already suitable representation or materialize reordered values when needed; do not equate every call with a mandatory copy. Materialization can simplify custom kernels, but it has memory and execution costs. Put that choice at an explicit boundary and measure it with the operator when evaluating end-to-end benefit. A fast custom kernel preceded by an expensive hidden layout conversion may fail to improve the original model path. Reporting only kernel time would hide that conversion cost.

**中文：** 连续化请求得到逻辑布局连续的张量；已有表示合适时可以复用，需要时才物化重排数值，不能把每次调用都等同于必然复制。物化可以简化自定义内核，但具有内存和执行成本。应在明确边界做出选择，评估端到端收益时把转换与算子一起测量。一个很快的自定义内核，如果前面隐藏着昂贵布局转换，未必能改善原模型路径，单独报告内核时间会掩盖这一点。

**English:** Reshape and transpose answer different questions. Reshape changes dimensional interpretation while preserving logical element order; transpose changes the mapping between axes. Equal element counts are necessary for a reshape but do not guarantee a zero-copy path or preserve semantic axis names. When a matrix multiplication fails after several views, inspect intermediate dimensions and strides one step at a time. Adding `contiguous` everywhere may hide the origin of the mismatch while increasing copies, so use it only when its role is understood.

**中文：** 变形与转置回答不同问题。变形改变维度解释但保持逻辑元素顺序，转置则改变轴之间的映射。元素数量相等是变形前提，却不保证零复制，也不会自动保留语义轴名。经过多个视图后矩阵乘法失败，应逐步检查中间维度与跨度。到处添加连续化，可能掩盖不一致从哪里开始，同时增加复制，因此只有理解其作用时才使用，不能把它当成万能修复按钮。

## 6. A model artifact is a coordinated set / 模型产物是一组协同文件

**English:** A checkpoint supplies named tensor values; configuration describes architectural choices; a tokenizer maps text into IDs; model code determines how those tensors and IDs are interpreted. Safetensors alone does not specify a complete executable model. The [official format documentation](https://huggingface.co/docs/safetensors/index) describes tensor serialization, while architecture and preprocessing remain application-level responsibilities. Loading every tensor successfully therefore does not establish that the correct computation is being performed.

**中文：** 权重文件提供具名张量数值，配置描述架构选择，分词器把文本映射为编号，模型代码决定如何解释这些张量与编号。单独一个权重容器不能定义完整可执行模型。[官方格式文档](https://huggingface.co/docs/safetensors/index) 说明张量序列化，而架构与预处理仍由应用负责。因此，即使全部张量都能加载，也不能证明计算正确；还需要检查它们是否与配置、分词规则及具体实现对应。

**English:** Parameter names act as a schema. This experiment expects `embedding.weight`, `head.weight`, and `head.bias` with specific shapes. `VarBuilder` resolves names under prefixes and checks requested shapes while constructing layers. A prefix mistake is not repaired by changing the tensor's numerical values. When importing a real checkpoint, compare key names, shapes, dtype, layer count, and architectural options before attempting inference. A small inventory often explains a loader failure more directly than rerunning a download. A complete file and a file compatible with the intended model are different conditions.

**中文：** 参数名称相当于模式。本实验要求三个指定名称及各自形状。变量构建器在前缀下解析名称，构造层时检查请求形状。前缀写错不能靠改变张量数值修复。导入真实权重时，应先比较键名、形状、数据类型、层数及架构选项，再开始推理。简短的参数清单往往比重新下载更能解释加载失败，因为文件完整与文件符合目标模型是两个问题，不能相互替代。

**English:** Linear weights conventionally have shape `[output_features, input_features]` in the layer used here, and forward computes input times the transposed weight plus bias. Storing the same numbers in the opposite orientation can produce a shape error or a wrong but valid computation if dimensions coincide. Read the [pinned linear implementation](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/linear.rs) rather than guessing from another library's serialization. Our two-output, three-input choice intentionally makes the orientation visible.

**中文：** 本课线性层权重采用输出特征乘输入特征的形状，前向计算是输入乘权重转置，再加偏置。把相同数值按相反方向保存，可能直接形状错误，也可能在维度恰好相等时形成合法但错误的计算。应阅读[固定版本线性实现](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/linear.rs)，不要从另一库的存储习惯猜测。本例特意使用两个输出、三个输入，让方向区别清晰可见。

**English:** Buffered loading reads the file into owned bytes and avoids introducing a memory-mapping safety discussion into the first experiment. The pinned builder also offers memory-mapped loading with an unsafe interface inherited from mapping assumptions. Mapping can reduce certain host copying or allocation costs, but does not imply that GPU weights need no transfer or that files may be modified arbitrarily during use. Choose loading strategy deliberately and keep the files, mappings, and device allocations alive according to their actual contracts. A zero-copy claim must identify the boundary to which it applies.

**中文：** 缓冲加载把文件读进拥有所有权的字节，避免在第一个实验中额外引入内存映射安全讨论。固定版本也提供继承映射前提的不安全加载接口。映射可能减少某些主机复制或分配成本，但不表示 GPU 权重无需传输，也不允许使用期间任意修改文件。应主动选择加载策略，按实际契约维持文件、映射及设备分配生命周期，不能看到零复制宣传就忽略它针对的是哪一层边界。

## 7. Tokenization defines the model's input meaning / 分词决定模型输入含义

**English:** A tokenizer is a pipeline rather than a vocabulary lookup alone. Normalization, pre-tokenization, the tokenization model, post-processing, and decoding can each change behavior. The [official tokenization pipeline guide](https://huggingface.co/docs/tokenizers/pipeline) separates these stages. A real model may depend on special tokens, whitespace handling, byte-level behavior, or a chat template. Matching the number of vocabulary entries while changing any of these rules can still feed semantically different IDs into otherwise correct model weights. The resulting output can be wrong without any tensor-shape error.

**中文：** 分词器是一条流水线，不只是词表查找。规范化、预分词、分词模型、后处理和解码都可能改变行为。[官方分词流水线指南](https://huggingface.co/docs/tokenizers/pipeline) 区分这些阶段。真实模型可能依赖特殊词元、空白处理、字节级规则或对话模板。即使词表条目数量相同，改变这些规则仍可能把语义不同的编号送入本来正确的权重，导致错误输出，却没有任何张量形状异常。

**English:** The local WordLevel tokenizer is deliberately simple: unknown text maps to ID zero, and the words `rust`, `cuda`, and `tensor` have fixed IDs. No special tokens are automatically added in the encode call. This makes a two-token example reproducible without network access or a pretrained language model. The simplicity is a teaching choice, not a claim that whitespace word tokenization is adequate for production language models or multilingual text. For a real model, use the complete tokenizer artifact paired with its weights rather than extending this toy vocabulary as a substitute.

**中文：** 本地词级分词器刻意保持简单：未知文本映射到零号，三个示例词分别具有固定编号，编码调用不自动加入特殊词元。这样无需联网或预训练语言模型，就能复现两词元案例。这种简单是教学选择，不表示按空白进行词级切分足以服务生产语言模型或多语言文本。迁移到真实模型时，应换成与权重配套的完整分词产物，而不是继续扩展这个玩具词表冒充真实处理流程。

**English:** Empty input, unknown tokens, and out-of-range IDs are different cases. The tokenizer can intentionally produce a valid unknown ID; an empty sequence makes mean pooling undefined for this model; ID 99 is outside the four-row embedding table. The experiment checks all three paths separately. A service should decide which are user-visible validation errors and which indicate an internal mismatch. Treating every failure as an allocation problem would obscure the actual input contract and make debugging much harder. It also prevents giving the caller a meaningful corrective action.

**中文：** 空输入、未知词元和超范围编号是不同情况。分词器可以有意产生有效未知编号；空序列使本模型的平均池化缺少定义；九十九号则超出四行嵌入表。实验分别检查这三条路径。服务应决定哪些属于用户可见输入错误，哪些说明内部产物不匹配。若把全部失败统称为资源分配问题，就会遮蔽真正的输入契约，也无法向调用者提供有意义的修正方法。

## 8. Trace the forward computation / 跟踪前向计算

**English:** Our model takes a rank-one sequence of token IDs. Embedding returns `[tokens, hidden]`; averaging along the token axis returns `[hidden]`; adding a batch dimension gives `[1, hidden]`; the linear head returns `[1, output]`; ReLU clips negative values to zero. This is a tiny pooling model, not an autoregressive transformer. It is large enough to exercise artifacts and layers while remaining small enough that every intermediate value can be computed manually.

**中文：** 模型接收一维词元编号序列。嵌入得到词元数乘隐藏维度，沿词元轴平均得到隐藏向量，增加批次轴后得到一行隐藏特征，线性头返回一行输出，最后由激活把负值截成零。这是一个小型池化模型，不是自回归变换器。它足以覆盖模型产物与层调用，同时仍然足够小，能够手算每个中间值，避免只能相信最终打印结果，却不知道具体哪一步出错。

**English:** For IDs `[1, 2]`, the embedding rows are `[1, 2, 3]` and `[4, 5, 6]`, so their mean is `[2.5, 3.5, 4.5]`. The first linear output is `2.5 - 4.5 + 0.5 = -1.5`; the second is `0.5 * 2.5 + 3.5 - 1 = 3.75`. ReLU therefore returns `[0, 3.75]`. This derivation identifies the axis and weight orientation, so it catches errors that a shape-only test would miss.

**中文：** 编号 `[1, 2]` 选出两行嵌入，分别为 `[1, 2, 3]` 与 `[4, 5, 6]`，平均得到 `[2.5, 3.5, 4.5]`。第一个线性输出为 `2.5 - 4.5 + 0.5 = -1.5`，第二个为 `0.5 * 2.5 + 3.5 - 1 = 3.75`，激活后为 `[0, 3.75]`。这个推导明确平均轴与权重方向，因此能发现仅检查形状无法发现的错误。

**English:** Separate model construction from per-request forward execution. Load immutable weights and tokenizer assets once, then pass validated request inputs into a reusable model. Re-reading files on every call mixes initialization into latency and adds avoidable I/O. Request-specific state should be explicit rather than stored accidentally in model fields. This design also makes tests clearer: artifact validation, forward correctness, and concurrent request behavior can be evaluated independently before they are combined into a service.

**中文：** 应把模型构造与每请求前向分开。权重和分词产物加载一次，再把经过验证的请求输入交给可复用模型。每次调用重读文件，会把初始化混入延迟并增加不必要读写。请求状态应明确存在，而不是意外留在模型字段。这样测试也更清楚：可以分别评估产物验证、前向正确性和并发请求行为，再把它们组合成服务，避免在一个巨大入口中同时排查所有问题。

**English:** Autoregressive decoding adds state that our pooling model does not have. Prefill processes the prompt; later decode steps generate new tokens while reusing attention state such as a KV cache. Cache position, request identity, sequence length, and model revision must stay consistent. A working single forward pass does not prove that a multi-step generation loop resets or reuses state correctly. When extending Candle model examples, trace state updates and termination conditions alongside tensor operations. In particular, accidental cache reuse across requests can produce wrong content without a crash.

**中文：** 自回归解码增加了本池化模型没有的状态。预填充处理提示，后续解码生成新词元并复用注意力状态，例如键值缓存。缓存位置、请求身份、序列长度及模型修订必须保持一致。单次前向能够运行，不证明多步生成循环正确重置或复用状态。扩展 Candle 模型例子时，应与张量操作一起跟踪状态更新和终止条件，尤其防止不同请求之间意外复用缓存，导致没有崩溃却输出错误内容。

## 9. Custom operators start with a complete contract / 自定义算子从完整契约开始

**English:** The pinned [CustomOp1 interface](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/custom_op.rs) receives storage and layout separately and returns output storage and shape. Its CPU forward method is required; device methods and backward support have explicit behavior. Implementing one CPU method does not automatically create a CUDA kernel or a derivative. The experiment uses `apply_op1_no_bwd` because it is an inference-only demonstration, and it leaves unsupported device paths unsupported rather than silently copying through the CPU.

**中文：** 固定版本的[一元自定义算子接口](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/custom_op.rs) 分别接收存储与布局，返回输出存储及形状。CPU 前向方法是必需项，设备方法和反向支持也各有明确行为。实现一个 CPU 方法不会自动生成 CUDA 内核或导数。实验采用无反向接口，因为它只演示推理，并让不支持的设备路径明确保持不支持，不会悄悄来回搬到 CPU 冒充设备执行。

**English:** Our affine operator computes `2*x + 1` only for contiguous F32 input, respecting a nonzero starting offset. Its output is a new contiguous storage with the same logical shape. Noncontiguous input and F64 input return errors. This narrow contract is preferable to an apparently general operator that silently reads the wrong memory. A later stride-aware implementation could accept more layouts, but it would need new indexing logic and tests rather than merely deleting the contiguity check.

**中文：** 本课仿射算子只接受连续单精度输入，并尊重非零起始偏移，计算两倍输入加一。输出是逻辑形状相同的新连续存储。非连续输入和双精度输入会返回错误。这样清楚但有限的契约，优于看似通用却悄悄读错内存的算子。未来可以实现识别跨度的版本，接受更多布局，但需要新的索引逻辑和测试，不能仅删除连续性检查，就声称已经支持任意视图。

**English:** A CUDA custom operator adds obligations beyond the arithmetic formula: obtain the correct device storage, account for offsets, allocate output through compatible ownership, launch on the appropriate stream, maintain dependencies, and return a shape/dtype combination the framework expects. A raw device pointer alone carries none of those guarantees. The [official release custom-op example](https://github.com/huggingface/candle/blob/0.11.0/candle-examples/examples/custom-ops/main.rs) is a concrete integration reference, but its assumptions must be read before adapting its launch code to another kernel toolchain.

**中文：** CUDA 自定义算子在算术公式之外还有责任：取得正确设备存储，处理偏移，采用兼容所有权分配输出，在合适流上启动，维护依赖，并返回框架期望的形状和数据类型。一个裸设备指针不携带这些保证。[发布版官方自定义算子示例](https://github.com/huggingface/candle/blob/0.11.0/candle-examples/examples/custom-ops/main.rs) 提供具体集成参考，但把启动代码改接另一工具链之前，必须先理解它的前提，不能只找到指针就直接调用。

**English:** Validate extensions with adversarial layouts and failures as well as the happy path. Use a full contiguous tensor, a contiguous subview with offset, a transpose, an unsupported dtype, and a shape mismatch. For a GPU implementation, also test nonmultiple launch sizes and stream dependency behavior on a working device. Compare against a simple reference before measuring speed. An extension boundary is where the framework's guarantees meet your code, so a short clear rejection can be better engineering than unsupported apparent flexibility.

**中文：** 扩展验证应覆盖刻意刁难的布局与失败路径，不只是正常输入。需要完整连续张量、带偏移连续子视图、转置、不支持类型和形状不匹配。GPU 实现还应在可用设备上测试非整齐启动规模和流依赖。测速前先对照简单参考。扩展边界正是框架保证与自写代码交接之处，因此简短明确地拒绝某类输入，可能比没有正确实现支撑的表面灵活更可靠，也更容易维护。

## 10. CUDA, cuTile, and release boundaries / CUDA、cuTile 与版本边界

**English:** The [0.11.0 feature manifest](https://github.com/huggingface/candle/blob/0.11.0/candle-core/Cargo.toml) has CUDA support through its existing backend dependencies, but no `cutile` feature. At the separately inspected main snapshot `ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a`, the [manifest](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/Cargo.toml) adds that opt-in integration. Main still showing the same workspace version string does not make its new source identical to the published crate. Distinguish a package release from a Git revision whenever reproducing a feature claim.

**中文：** [0.11.0 特性清单](https://github.com/huggingface/candle/blob/0.11.0/candle-core/Cargo.toml) 通过原有后端依赖支持 CUDA，但没有 cuTile 特性。另行检查的主分支固定快照，其[清单](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/Cargo.toml) 才加入这项可选集成。即使主分支工作区仍显示相同版本字符串，也不表示新源码与已发布软件包相同。复现功能声明时必须区分发行包与 Git 修订，不能只看版本数字。

**English:** The snapshot's [cuTile setup guide](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-book/src/guide/cutile.md) requires Rust 1.89+, CUDA 13.2+, an appropriate r580-or-newer driver, compute capability 8.0+, clang/libclang, and `tileiras`. It recommends CUDA 13.3 and distinguishes toolkit support across architectures. These requirements are not a report that our installation works. The CPU release experiment does not enable this feature, and the broken driver prevents validating the full device path even though a suitable toolkit is installed.

**中文：** 快照的 [cuTile 设置指南](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-book/src/guide/cutile.md) 要求 Rust 至少 1.89、CUDA 至少 13.2、符合工具包条件的 r580 或更新驱动、至少 8.0 计算能力，以及 clang/libclang 和 `tileiras` 工具。指南推荐 CUDA 13.3，并区分架构支持。这些要求不等于本机可用报告。CPU 发布版实验没有启用它，驱动故障仍阻止完整设备路径验证，不能因工具包版本合适就宣称兼容通过。

**English:** The inspected [cuTile custom-op example](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/examples/cutile.rs) uses Candle's re-exported cuTile version, checks shapes and contiguity, and works through a context/stream bridge and guarded storage access. Its length restriction is explicit. This is evidence that integration needs more than obtaining raw pointers. When adapting the example, preserve its device, stream, dependency, and guard-lifetime relationships; replacing its launcher without understanding those relationships can invalidate otherwise correct kernel arithmetic.

**中文：** 检查过的 [cuTile 自定义算子例子](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/examples/cutile.rs) 使用 Candle 重新导出的版本，检查形状和连续性，通过上下文流桥接与受保护存储访问工作，并明确限制长度。这证明集成不只是拿到裸指针。改写例子时必须保留设备、流、依赖与访问保护生命周期关系；若不理解这些关系就替换启动器，内核算术即使正确，整体也可能无效。

**English:** `cuda-oxide` is likewise not an automatic plug-in for every Candle release. To assess a bridge, identify the produced code format, parameter ABI, supported architecture, current CUDA context, stream, allocation ownership, and completion protocol. Then implement and test an adapter against pinned versions. A kernel succeeding in its own example does not prove that another framework can safely borrow its buffers or observe its writes. This chapter makes no claim that such an adapter has been implemented or validated.

**中文：** `cuda-oxide` 同样不是能够自动插入所有 Candle 版本的组件。评估桥接时，需要明确产物格式、参数二进制约定、支持架构、当前上下文、流、分配所有权及完成协议，再针对固定版本实现和测试适配层。内核在自身示例成功，不证明另一框架能够安全借用缓冲区或观察写入。本章没有声称已经实现或验证这种适配器，只给出判断接入是否成立时必须回答的问题。

**English:** JIT compilation adds a lifecycle stage distinct from model loading and kernel execution. A service may need to prepare the specializations it actually uses before latency-sensitive traffic, while retaining a policy for unseen shapes. Separate first-use compilation, warmed execution, and end-to-end request latency in reports. A precompile call that avoids launching a kernel still may need device/context information and an operational toolchain. Therefore even a mode named compile-only should be inspected before treating it as safe to validate on an unavailable GPU environment.

**中文：** 即时编译增加了区别于模型加载和内核执行的新生命周期阶段。服务可能需要在延迟敏感流量到来前准备实际使用的特化，同时保留处理未知形状的策略。报告应分开首次编译、预热后执行和端到端请求延迟。即使某个预编译调用不启动内核，也可能需要设备上下文信息和可用工具链。因此，即便模式名字叫仅编译，也要先检查其行为，不能直接认定它适合在 GPU 不可用环境验证。

## 11. Compare roles with PyTorch and SGLang / 对照 PyTorch 与 SGLang 的职责

**English:** Candle and PyTorch can express the same small tensor computation, which makes PyTorch a useful numerical reference. Compare semantic axes, parameter orientation, dtype, activation, and preprocessing before comparing speed. The Rust example uses U32 indices while the PyTorch reference uses its conventional integer index tensor; matching mathematical IDs matters more than forcing identical enum names. A correct comparison acknowledges each API's contract rather than translating source syntax mechanically.

**中文：** Candle 与 PyTorch 可以表达相同小型张量计算，因此后者适合提供数值参考。比较速度之前，先对齐语义轴、参数方向、数据类型、激活与预处理。Rust 例子使用无符号编号，PyTorch 对照使用它惯常的整数索引张量；重要的是数学编号相同，而不是强迫枚举名称一致。正确对照尊重各自接口契约，不能机械翻译源码语法，然后把类型差异造成的问题误认为框架结果不同。

**English:** The [PyTorch linear-layer contract](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Linear.html) matches the weight orientation used in this experiment. We use an inference context for the reference and supply identical constants, not separately randomized initialization. If the outputs diverge, compare embedding rows and pooled features before investigating the final projection. Layerwise comparison localizes the earliest mismatch and avoids attributing a tokenizer or axis mistake to floating-point differences between frameworks. Numerical tolerances become meaningful only after the semantic paths agree.

**中文：** [PyTorch 线性层契约](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Linear.html) 与本实验权重方向一致。对照使用推理上下文和完全相同常量，而不是分别随机初始化。若输出不同，应先比较选中的嵌入行和池化特征，再调查最终投影。逐层比较能够定位最早差异，避免把分词器或坐标轴错误归咎于框架浮点差别。只有语义路径确认相同之后，数值容差讨论才真正有意义。

**English:** SGLang emphasizes a serving runtime and inference-system capabilities such as request scheduling and efficient execution for supported models. Its [official documentation](https://docs.sglang.io/) describes that system role. A Candle `forward` method does not automatically provide continuous batching, admission control, streaming responses, cancellation, or production observability. You can build such surrounding components in Rust, but they remain engineering work with their own tests. Conversely, using a serving runtime does not replace learning tensor layout or kernel bottlenecks.

**中文：** SGLang 侧重服务运行时与推理系统能力，例如请求调度和受支持模型的高效执行，[官方文档](https://docs.sglang.io/) 描述这一系统角色。Candle 的前向方法不会自动提供持续批处理、准入控制、流式响应、取消或生产可观测性。可以用 Rust 构建这些外围组件，但它们仍然是需要独立测试的工程工作。反过来，使用服务运行时也不能替代学习张量布局和内核瓶颈，两类知识处于不同层次。

**English:** Choose a stack by the work you need to own. A small embedded inference component may value a Rust API and explicit integration; a high-concurrency language-model service may value an established scheduler and cache management. Neither choice follows solely from the kernel author's preferred language. A useful portfolio can connect them: reproduce a model block numerically, profile one bottleneck, and explain the adapter or serving boundary. That demonstrates transferable systems reasoning more clearly than naming several libraries without a reproducible result.

**中文：** 选择执行栈取决于你需要负责的工作。小型嵌入式推理组件可能重视 Rust 接口与明确集成，高并发语言模型服务可能更重视成熟调度器及缓存管理。两者都不能仅由内核作者偏好的语言决定。有价值的实践作品可以把它们连接起来：复现一个模型块的数值，分析一个瓶颈，再解释适配或服务边界。这比罗列多个库名却没有可复现结果，更能展示可以迁移的系统推理能力。

## 12. Complete CPU experiment / 完整 CPU 实验

**English:** Run the following setup in a fresh temporary directory. It downloads Rust dependencies but no model weights, creates all model artifacts locally, and uses no CUDA feature. The generated `Cargo.lock` records resolved transitive versions; retain it with results and use `--locked` for subsequent runs. Pinning the three principal crates fixes their APIs, while a newly generated lockfile at a later date may resolve other compatible dependencies differently. The development profile disables debug information and incremental build artifacts to limit temporary disk use. The program keeps its validation assertions enabled.

**中文：** 请在新的临时目录运行下方设置。它下载 Rust 依赖，但不下载模型权重，全部模型产物在本地创建，也不启用 CUDA。生成的锁文件记录传递依赖版本，应与结果一起保留，后续运行使用锁定选项。固定三个主要软件包能够固定它们的接口，但以后重新生成锁文件时，其他兼容依赖仍可能变化。开发配置关闭调试信息与增量构建产物，减少临时磁盘占用，同时保留程序中的验证断言。

```bash
COURSE09_DIR=$(mktemp -d /tmp/course09.XXXXXX)
cd "$COURSE09_DIR"
mkdir src
cat > Cargo.toml <<'TOML'
[package]
name = "course09-candle"
version = "0.1.0"
edition = "2021"
[dependencies]
candle-core = { version = "=0.11.0", default-features = false }
candle-nn = { version = "=0.11.0", default-features = false }
tokenizers = { version = "=0.22.2", default-features = false, features = ["onig"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
[profile.dev]
debug = 0
incremental = false
TOML
cat > src/main.rs <<'RUST'
use candle_core::{CpuStorage, CustomOp1, DType, Device, Layout, Module, Shape, Tensor};
use candle_nn::{Embedding, Linear, VarBuilder};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, error::Error, fs};
use tokenizers::Tokenizer;

type AnyResult<T> = Result<T, Box<dyn Error + Send + Sync>>;

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    vocab_size: usize,
    hidden_size: usize,
    output_size: usize,
}

struct TinyModel {
    embedding: Embedding,
    head: Linear,
}

impl TinyModel {
    fn load(config: &Config, vb: VarBuilder<'_>) -> candle_core::Result<Self> {
        Ok(Self {
            embedding: candle_nn::embedding(
                config.vocab_size, config.hidden_size, vb.pp("embedding"))?,
            head: candle_nn::linear(
                config.hidden_size, config.output_size, vb.pp("head"))?,
        })
    }

    fn forward(&self, ids: &Tensor) -> candle_core::Result<Tensor> {
        if ids.rank() != 1 || ids.elem_count() == 0 {
            candle_core::bail!("expected a nonempty rank-one token sequence")
        }
        let embedded = self.embedding.forward(ids)?;
        let pooled = embedded.mean(0)?.unsqueeze(0)?;
        self.head.forward(&pooled)?.relu()
    }
}

struct Affine;
impl CustomOp1 for Affine {
    fn name(&self) -> &'static str { "course-affine-f32" }
    fn cpu_fwd(&self, storage: &CpuStorage, layout: &Layout)
        -> candle_core::Result<(CpuStorage, Shape)> {
        let source = storage.as_slice::<f32>()?;
        let (start, end) = match layout.contiguous_offsets() {
            Some(range) => range,
            None => candle_core::bail!("custom affine requires contiguous input"),
        };
        let output = source[start..end].iter().map(|x| 2.0 * x + 1.0).collect();
        Ok((CpuStorage::F32(output), layout.shape().clone()))
    }
}

fn main() -> AnyResult<()> {
    let device = Device::Cpu;
    let config = Config { vocab_size: 4, hidden_size: 3, output_size: 2 };
    fs::write("config.json", serde_json::to_vec_pretty(&config)?)?;
    let tokenizer_json = r#"{
      "version":"1.0", "truncation":null, "padding":null, "added_tokens":[],
      "normalizer":null, "pre_tokenizer":{"type":"Whitespace"},
      "post_processor":null, "decoder":null,
      "model":{"type":"WordLevel", "vocab":{"[UNK]":0,"rust":1,"cuda":2,"tensor":3},
               "unk_token":"[UNK]"}
    }"#;
    fs::write("tokenizer.json", tokenizer_json)?;
    let mut weights: HashMap<String, Tensor> = HashMap::new();
    weights.insert("embedding.weight".into(), Tensor::new(
        &[[0f32, 0., 0.], [1., 2., 3.], [4., 5., 6.], [-1., 0., 1.]], &device)?);
    weights.insert("head.weight".into(), Tensor::new(
        &[[1f32, 0., -1.], [0.5, 1., 0.]], &device)?);
    weights.insert("head.bias".into(), Tensor::new(&[0.5f32, -1.], &device)?);
    candle_core::safetensors::save(&weights, "tiny.safetensors")?;
    drop(weights);

    let config: Config = serde_json::from_slice(&fs::read("config.json")?)?;
    let tokenizer = Tokenizer::from_file("tokenizer.json")?;
    let encoded = tokenizer.encode("rust cuda", false)?;
    assert_eq!(encoded.get_ids(), &[1, 2]);
    assert_eq!(tokenizer.encode("unknown", false)?.get_ids(), &[0]);
    assert_eq!(tokenizer.decode(encoded.get_ids(), false)?, "rust cuda");
    let ids = Tensor::new(encoded.get_ids(), &device)?;
    assert_eq!(ids.dtype(), DType::U32);
    let vb = VarBuilder::from_buffered_safetensors(
        fs::read("tiny.safetensors")?, DType::F32, &device)?;
    let model = TinyModel::load(&config, vb.clone())?;
    let output = model.forward(&ids)?.to_vec2::<f32>()?;
    assert_eq!(output, vec![vec![0.0, 3.75]]);
    assert!(vb.get((2, 4), "head.weight").is_err());
    assert!(vb.get((2, 3), "missing.weight").is_err());
    assert!(model.forward(&Tensor::new(&[] as &[u32], &device)?).is_err());
    let wrong_ids = Tensor::new(&[99u32], &device)?;
    assert!(model.forward(&wrong_ids).is_err());
    println!("tokens={:?}, output={output:?}", encoded.get_ids());

    let base = Tensor::arange(0f32, 6f32, &device)?.reshape((2, 3))?;
    let transposed = base.t()?;
    assert!(!transposed.is_contiguous());
    assert_eq!(transposed.stride(), &[1, 3]);
    assert!(transposed.apply_op1_no_bwd(&Affine).is_err());
    let fixed = transposed.contiguous()?.apply_op1_no_bwd(&Affine)?;
    assert_eq!(fixed.to_vec2::<f32>()?, vec![vec![1., 7.], vec![3., 9.], vec![5., 11.]]);
    let offset_view = base.narrow(0, 1, 1)?;
    let offset_output = offset_view.apply_op1_no_bwd(&Affine)?;
    assert_eq!(offset_output.to_vec2::<f32>()?, vec![vec![7., 9., 11.]]);
    assert!(base.to_dtype(DType::F64)?.apply_op1_no_bwd(&Affine).is_err());
    assert!(base.reshape((4, 2)).is_err());
    assert!(base.matmul(&Tensor::zeros((4, 2), DType::F32, &device)?).is_err());
    println!("layout: transpose rejected, contiguous fixed, nonzero offset respected");
    println!("failures: missing/shape/dtype/empty/invalid-id checks passed");
    println!("CPU only: no GPU execution or performance claim");
    Ok(())
}
RUST
cargo generate-lockfile
cargo run --locked
```

**English:** This experiment performs a real file round trip. The initial tensors are written to `tiny.safetensors`, the temporary map is dropped, and the model is reconstructed through the loader. Configuration and tokenizer are also read from files. These operations verify the boundary between serialized artifacts and executable model code, but the constants are educational weights, not a pretrained model. The program intentionally creates files in its working directory, which is why the setup begins by entering a fresh temporary directory. Preserve this inspectable boundary; an object that already exists in memory is not evidence of a successful disk restore.

**中文：** 本实验执行真实文件往返。初始张量写入权重文件后，临时映射被释放，再由加载器重建模型；配置和分词器也从文件读取。这验证了序列化产物与可执行模型代码之间的边界，但常量只是教学权重，不是预训练模型。程序会有意在工作目录创建文件，因此设置步骤首先进入全新的临时目录。研究加载过程时应保留这种可检查的边界，不要把内存中已有对象误当成磁盘恢复成功的证据。

**English:** Follow the exact arithmetic. The two IDs select rows `[1,2,3]` and `[4,5,6]`; averaging along the token axis gives `[2.5,3.5,4.5]`. The first projection is `2.5 - 4.5 + 0.5 = -1.5`; the second is `0.5 * 2.5 + 3.5 - 1 = 3.75`. ReLU gives `[0,3.75]`. These particular values are exactly representable, so the experiment uses equality. General floating-point models need an explicit tolerance justified by dtype, accumulation, and the reference calculation, rather than copying this equality rule indiscriminately.

**中文：** 应逐步核对算术。两个编号选择第一、第二个非未知词嵌入行，分别为一二三与四五六；沿词元轴平均，得到二点五、三点五、四点五。第一个投影加偏置后为负一点五，第二个为三点七五，整流激活之后得到零与三点七五。这些特定数值可以精确表示，所以实验使用相等断言。一般浮点模型需要根据数据类型、累加方式及参考计算制定明确容差，不能不加区分地照搬本例相等判断。

**English:** The negative cases are part of the executable contract. A missing weight tests the namespace; a wrong requested shape tests architecture agreement; empty input tests a model-level precondition; and ID 99 tests embedding bounds. The custom operator separately rejects F64 and a transposed noncontiguous view. These are expected `Result` failures, and the assertions verify that they occur. In a service, propagate typed or contextual errors to the appropriate boundary rather than replacing input validation with process-terminating assertions.

**中文：** 失败场景是可执行契约的一部分。缺失权重检查名称空间，错误请求形状检查架构一致性，空输入检查模型级前置条件，越界编号检查嵌入索引范围。自定义算子还分别拒绝双精度类型和转置产生的不连续视图。它们是预期的结果类型错误，断言用于证明错误确实发生。真实服务应把有类型或有上下文的错误传到适当边界，不能用会终止进程的断言代替面向请求的输入验证。

**English:** The offset test prevents a subtler bug than simple noncontiguity. Narrowing to the second row preserves contiguous logical values, but they begin at storage offset three. Reading the whole storage or starting at zero would incorrectly produce the first row's transformed values. `contiguous_offsets` supplies the relevant half-open storage range. The transpose test then shows a separate policy: reject the unsupported layout explicitly, materialize it with `contiguous`, and retry. Supporting arbitrary strides would require a different indexing implementation and its own tests.

**中文：** 偏移测试防止一种比不连续更隐蔽的错误。截取第二行之后，逻辑数值仍然连续，却从底层存储的第三个偏移位置开始。若读取全部存储或总从零开始，就会错误得到第一行的变换值。连续区间接口给出需要访问的左闭右开范围。转置测试展示另一个策略：明确拒绝不支持的布局，再连续化后重试。若要支持任意跨度，需要设计另一套索引实现，并为它建立独立验证，不能删掉检查就宣称兼容。

**English:** The following output was observed from `cargo run --locked` on the pinned CPU setup. The run also passed the reshape element-count and matrix inner-dimension failures. Compilation initially encountered the shared user's disk quota; rebuilding with debug information and incremental output disabled completed successfully, and the regenerable target directory was removed after validation. That resource incident does not change the numerical result. No CUDA feature build, GPU forward pass, GPU custom operator, or speed comparison was validated in this course.

**中文：** 下方输出是在固定 CPU 配置执行锁定运行命令后实际观察到的；运行也通过了变形元素数量错误和矩阵内维度错误检查。最初编译遇到共享用户磁盘配额问题，关闭调试信息及增量产物后重新构建成功，验证后删除可重新生成的构建目录。这项资源故障不改变数值结论。本课没有验证 CUDA 特性构建、GPU 前向执行、GPU 自定义算子或任何速度对比，应始终保留这个证据边界。

```text
tokens=[1, 2], output=[[0.0, 3.75]]
layout: transpose rejected, contiguous fixed, nonzero offset respected
failures: missing/shape/dtype/empty/invalid-id checks passed
CPU only: no GPU execution or performance claim
```

## 13. Independent PyTorch reference / 独立 PyTorch 对照

**English:** Run the next block in a Python environment that already has PyTorch 2.14 installed; the CPU environment from the PyTorch course is sufficient. It uses no NumPy, downloaded checkpoint, CUDA device, or tokenizer package. Supplying the already verified token IDs deliberately isolates tensor arithmetic from preprocessing. On the inspected `2.14.0+cpu` installation it printed the same output and passed the assertion. The use of an inference context and constant weights makes the comparison reproducible, but it is still a correctness check rather than a benchmark. Running each tiny program once and comparing impressions would not establish performance.

**中文：** 下方程序可以在已经安装 PyTorch 2.14 的 Python 环境运行，PyTorch 课程的 CPU 环境即可。它不使用数组扩展库、下载权重、CUDA 设备或分词器软件包。直接提供已经验证的编号，是为了把张量算术与预处理隔离。在核验过的 CPU 版本中，它打印相同输出并通过断言。推理上下文与常量权重使对照可复现，但这仍是正确性检查，不能根据两个小程序各运行一次的感觉判断性能。

```python
import torch
import torch.nn.functional as F

print("torch", torch.__version__)
e = torch.tensor(
    [[0., 0., 0.], [1., 2., 3.], [4., 5., 6.], [-1., 0., 1.]],
    dtype=torch.float32,
)
w = torch.tensor([[1., 0., -1.], [.5, 1., 0.]], dtype=torch.float32)
b = torch.tensor([.5, -1.], dtype=torch.float32)
ids = torch.tensor([1, 2], dtype=torch.int64)
with torch.inference_mode():
    pooled = F.embedding(ids, e).mean(dim=0).unsqueeze(0)
    output = F.relu(F.linear(pooled, w, b))
assert output.tolist() == [[0., 3.75]]
print("output", output.tolist())
```

**English:** A useful next mutation is to change one embedding constant in both implementations, recompute the hand reference, and require all three results to agree. Then change only one implementation and confirm that the check detects the mismatch. This verifies that the comparison is sensitive to model data rather than merely confirming a hard-coded printout. For larger models, compare intermediate tensors on small deterministic inputs, use stated tolerances, and report the first divergent stage before changing backend or precision settings. This avoids changing too many variables simultaneously.

**中文：** 有用的后续变体是同时修改两种实现中的一个嵌入常量，重新手算，并要求三个结果一致；然后只修改其中一种实现，确认检查能够发现差异。这能验证比较确实对模型数据敏感，而不是只是在确认硬编码输出。对于更大模型，应在小型确定性输入上逐层比较中间张量，使用明确容差，先报告最早发生差异的阶段，再考虑改变后端或精度设置，避免同时修改过多变量。

## 14. Turn a forward pass into an application / 从前向计算走向应用

**English:** Load and validate immutable model artifacts once when practical, then distinguish them from per-request state. Sharing model parameters does not mean sharing a mutable sequence cache between unrelated users. An autoregressive application's cache belongs to a sequence or a precisely defined shared-prefix policy, with ownership and invalidation rules. Even the tiny example benefits from this distinction: tokenizer and model construction are startup work, while encoding input and producing an output are request work. Measuring both together answers a different question from warmed inference latency.

**中文：** 条件允许时，应在启动阶段一次加载并验证不可变模型产物，再把它们与每个请求的状态区分。共享模型参数不代表可以让无关用户共用可变序列缓存。自回归应用的缓存属于特定序列，或者属于定义明确的共享前缀策略，并需要所有权和失效规则。即使本课小例子也受益于这种区分：分词器和模型构造属于启动工作，输入编码与输出生成属于请求工作；把两者一起计时，回答的是不同于预热推理延迟的问题。

**English:** Bound queues and retained outputs as carefully as tensor allocations. A producer that submits requests faster than a consumer finishes them can exhaust memory even if every individual tensor is dropped correctly. Cancellation also has layers: the client may stop waiting while already submitted device work remains active. Reclaiming buffers must respect that work's completion protocol. Rust ownership helps express resource relationships, but an adapter must still connect those relationships to external asynchronous execution; a dropped future is not universal proof that a GPU has stopped using its arguments.

**中文：** 应像约束张量分配一样约束队列和保留输出。生产者提交请求的速度持续超过消费者完成速度，即使每个张量都正确释放，也可能耗尽内存。取消同样分层：客户端可以停止等待，但已提交设备工作仍在运行。回收缓冲区必须遵循工作完成协议。Rust 所有权有助于表达资源关系，适配器仍须把这些关系连接到外部异步执行；一个异步任务被销毁，不能普遍证明 GPU 已停止使用它的参数。

**English:** Profile the actual question you intend to answer. Startup includes file reads and model construction; text handling includes encoding and decoding; model execution may include device transfers, operator launches, and output synchronization. A language-model service further distinguishes prefill and decode, and must state its batch and sequence lengths. Record the version, device, workload, warmup, repetition policy, and correctness reference before publishing a latency. A framework name alone neither explains a bottleneck nor makes two reported measurements comparable. It also cannot replace an explicit description of the completion boundary.

**中文：** 性能分析应对应真正想回答的问题。启动包含文件读取和模型构造，文本处理包含编码与解码，模型执行可能包含设备传输、算子启动和输出同步。语言模型服务还区分预填充与逐词生成，并必须说明批次及序列长度。公开延迟之前，应记录版本、设备、工作负载、预热、重复策略和正确性参考。框架名称本身既不能解释瓶颈，也不能让两份测量自动具备可比性，更不能替代对完成边界的说明。

## 15. Exercises and reference answers / 练习与参考答案

### Exercise 1: Shared tensor ownership / 练习一：张量共享所有权

**English:** You clone a tensor handle, drop the original variable, and observe that memory remains allocated. Does this prove a leak? Explain what you would inspect before changing allocation code.

**中文：** 克隆张量句柄后释放原变量，却发现内存仍然保留，这能证明泄漏吗？修改分配代码之前，你会检查哪些关系？

**English:** Reference answer: No. A clone can share ownership of the same storage, and retained views, model fields, graphs, or queued outputs can keep that storage alive. Inspect the remaining owners and the lifetime of the request or cache containing them. Also distinguish allocator-reserved memory from live tensor data when the backend exposes that distinction. A leak claim needs evidence that resources remain unreachable or grow beyond the intended retention policy; the death of one local name is insufficient evidence. Blindly copying data can increase memory pressure instead.

**中文：** 参考答案：不能。克隆可能共享相同存储所有权，保留的视图、模型字段、张量关系和排队输出都可能延长存活时间。应检查其他所有者以及容纳它们的请求或缓存生命周期。后端提供相关信息时，还应区分分配器保留内存与活跃张量数据。只有资源已经不可达，或增长超过预期保留策略等证据，才能支持泄漏判断；某个局部变量消失本身并不充分，盲目复制数据反而可能增加压力。

### Exercise 2: Layout and offset / 练习二：布局与偏移

**English:** Why does the custom operator reject the transpose but accept a narrowed second row? Why would reading from storage index zero be incorrect even for the accepted input?

**中文：** 为什么自定义算子拒绝转置，却接受截取后的第二行？对于已经接受的输入，为什么从底层存储零位置读取仍可能错误？

**English:** Reference answer: The operator implements one contiguous logical interval. The transpose changes strides and interleaves logical rows, so its values do not meet that contract until materialized. The narrowed row remains contiguous, but starts after the first row in shared storage. The layout's interval carries both offset and length. Using only the shape or assuming a zero offset ignores part of the contract. The expected transformed second row is `[7,9,11]`; a zero-based read would return values derived from the wrong row. Both contiguity checking and offset handling are necessary.

**中文：** 参考答案：算子只实现单个连续逻辑区间。转置改变跨度，使逻辑行在存储中交错，因此需要先实体化才能满足契约。截取后的行仍然连续，但起点位于共享存储中第一行之后，布局区间同时携带偏移和长度。只看形状或假设起点为零，都遗漏了契约的一部分。第二行变换结果应为七、九、十一；从零开始会得到错误行的值。这说明连续性检查和偏移处理缺一不可。

### Exercise 3: Token IDs / 练习三：词元编号

**English:** A tensor has three elements, so a developer converts three floating-point values into token IDs and feeds them to the embedding layer. What information is still missing from this argument?

**中文：** 一个张量有三个元素，于是开发者把三个浮点数转换为词元编号送入嵌入层。这项论证仍然缺少什么信息？

**English:** Reference answer: Element count does not establish that the values are valid vocabulary indices. The IDs must come from the intended tokenizer and vocabulary revision, fit the operator's supported integer dtype, and lie within the embedding table's bounds. Special-token insertion and truncation must also match the model protocol. An integer conversion can silently turn unrelated numbers into valid-looking indices while preserving the wrong meaning. Validate preprocessing and the vocabulary-to-row mapping, not just tensor shape and conversion success. Type safety can reject some mistakes, but cannot infer the application meaning of token IDs.

**中文：** 参考答案：元素数量不能证明数值是有效词表索引。编号必须来自预期分词器和词表版本，使用算子支持的整数类型，并处于嵌入表范围内。特殊词元插入与截断规则也要符合模型协议。整数转换可能把无关数值变成表面合法的索引，却保留错误语义。因此应验证预处理及词表到行号的映射，而不只是检查形状与转换成功。类型安全能够排除部分错误，但不能自动理解文本编号的业务含义。

### Exercise 4: Checkpoint completeness / 练习四：权重文件的完整性

**English:** Can a safetensors file alone tell the application how to tokenize text, construct the network, and interpret outputs? Name the additional agreements required by the experiment.

**中文：** 一个安全张量权重文件能否独自告诉应用如何分词、构建网络和解释输出？本实验还需要哪些相互一致的约定？

**English:** Reference answer: It stores named tensor data, not the complete application protocol. The code must implement the architecture, the configuration must supply compatible dimensions, the tokenizer must map text into the expected vocabulary, and the loader must agree on parameter names and orientation. Output interpretation is another contract: this experiment returns two nonnegative features, not a next-token probability distribution. Using a recognized file format protects the serialization boundary but does not prove that all these semantic agreements are satisfied. A real model release should manage these artifacts as a consistent versioned set.

**中文：** 参考答案：它保存具名张量数据，不等于完整应用协议。代码必须实现架构，配置必须给出兼容维度，分词器必须把文本映射到预期词表，加载器必须采用一致参数名称和方向。输出解释也是另一层契约：本实验返回两个非负特征，并不是下一词元概率分布。使用已知文件格式有助于明确序列化边界，却不能证明全部语义约定已经满足；真实模型发布应把这些产物作为一致版本管理。

### Exercise 5: Derive the forward result / 练习五：推导前向结果

**English:** Derive the output for `rust cuda` without running either framework. State the intermediate shape and value after embedding, pooling, and the linear layer, then apply the activation.

**中文：** 不运行任何框架，推导输入文本的输出。说明嵌入、池化和线性层之后的中间形状及数值，再应用激活。

**English:** Reference answer: IDs `[1,2]` select a `[2,3]` embedding matrix with rows `[1,2,3]` and `[4,5,6]`. Mean over axis zero produces shape `[3]` and values `[2.5,3.5,4.5]`; adding the batch axis gives `[1,3]`. Multiplying by the transposed `[2,3]` weight and adding bias gives `[1,2]` with `[-1.5,3.75]`. ReLU changes only the negative component, producing `[[0,3.75]]`. Averaging over the feature axis would instead change the shape and invalidate the intended projection.

**中文：** 参考答案：两个编号取出两行三列的嵌入矩阵，行分别为一二三和四五六。沿零轴平均后得到长度为三的向量，数值为二点五、三点五、四点五；添加批次轴后为一行三列。它与两行三列权重的转置相乘，再加偏置，得到一行两列的负一点五与三点七五。整流只修改负分量，结果为零与三点七五。若沿特征轴平均，会改变形状，破坏预期投影，这不是可随意替换的实现细节。

### Exercise 6: Diagnose loading errors / 练习六：诊断加载错误

**English:** Explain why a missing `head.weight` and an existing `head.weight` of the wrong shape suggest different first investigations. Should either error be fixed by blindly reshaping the checkpoint?

**中文：** 为什么缺少权重名称与名称存在但形状错误，应优先进行不同调查？是否应该盲目变形权重来修复其中任意一种错误？

**English:** Reference answer: A missing key first suggests a prefix, naming, shard, or artifact-version mismatch. A shape mismatch suggests incompatible architecture dimensions, parameter orientation, or a different model variant. Inspect the published model contract and the actual checkpoint keys and shapes before modifying data. Blind reshaping preserves element count but can scramble semantic axes and cannot create missing parameters. A conversion tool is appropriate only when the source and destination conventions are known and the converted model is numerically verified. Making the loader stop reporting errors does not by itself restore the intended model semantics.

**中文：** 参考答案：名称缺失首先提示前缀、命名、分片或产物版本不一致；形状错误则提示架构维度、参数方向或模型变体不兼容。修改数据之前，应检查模型约定以及实际键名和形状。盲目变形虽然可能保留元素数量，却会打乱语义轴，也无法创造缺失参数。只有明确知道源端和目标端约定，并验证转换后模型数值时，转换工具才是合理手段。让加载不再报错，并不等于恢复了模型含义。

### Exercise 7: Custom operator coverage / 练习七：自定义算子覆盖范围

**English:** After implementing `cpu_fwd`, can you claim that an operator supports CUDA tensors, F64, noncontiguous inputs, and training? Explain the minimum evidence for each extension.

**中文：** 实现 CPU 前向方法之后，能否声称算子支持 CUDA 张量、双精度、不连续输入和训练？扩展每一项分别至少需要什么证据？

**English:** Reference answer: No. CUDA needs an implemented device path with correct context, stream, storage, and completion handling. F64 needs a supported typed implementation; arbitrary strides need indexing that honors layout; training needs a correct backward rule and the intended graph integration. Each extension needs numerical and failure tests on representative inputs. The experiment intentionally uses `apply_op1_no_bwd` and limits the CPU contract. Its successful affine result establishes only that specified forward behavior, not a general capability inferred from the operator's name. A default error implementation is not automatic support.

**中文：** 参考答案：不能。CUDA 需要真正实现设备路径，并正确处理上下文、流、存储和完成关系；双精度需要对应类型实现；任意跨度需要遵守布局的索引；训练需要正确反向规则及计算关系接入。每项扩展都需要代表性输入的数值与失败测试。本例有意使用无反向记录调用，并限制 CPU 契约。仿射结果成功只能证明指定前向行为，不能从算子名字推导出通用能力，也不能把默认报错当成自动实现。

### Exercise 8: Device validation / 练习八：设备验证

**English:** A program builds with a CUDA feature but silently falls back to CPU when device construction fails. Its output matches a reference. What can and cannot be concluded from this run?

**中文：** 程序启用 CUDA 特性后构建成功，但设备创建失败时静默回退 CPU，最终输出符合参考值。这次运行可以证明什么，又不能证明什么？

**English:** Reference answer: It can establish the numerical behavior of the path actually executed for those inputs. It cannot establish GPU availability, CUDA operator coverage, device timing, or GPU speedup. Record the selected device and the construction error, and make the fallback policy visible to the caller or experiment log. GPU validation requires a successful device path and completed, checked results. In this environment the driver/NVML mismatch remains a stated limitation; changing the report to say CUDA-enabled does not overcome it.

**中文：** 参考答案：它能证明实际执行路径对这些输入的数值行为，不能证明 GPU 可用、CUDA 算子覆盖、设备计时或 GPU 加速。应记录所选设备与创建错误，使回退策略对调用者或实验日志可见。GPU 验证需要成功进入设备路径，并得到完成且检查过的结果。本环境驱动与管理库不匹配仍是明确限制；把报告名称改成启用 CUDA，并不能消除限制，也不能把 CPU 正确性结果升级成设备执行证据。

### Exercise 9: Release versus main / 练习九：发布版与主分支

**English:** A main-branch guide documents a cuTile feature, but the pinned published Candle crate rejects that feature name. What should you verify before changing the dependency or asserting a documentation bug?

**中文：** 主分支指南介绍 cuTile 特性，而固定发布包拒绝该特性名。在修改依赖或断言文档错误之前，应该核对什么？

**English:** Reference answer: Compare the guide's commit with the release's manifest and source. The inspected published 0.11.0 and later main snapshot are different source states even when a workspace version string is unchanged. Either retain the release contract or deliberately pin the newer Git revision and assess its toolchain, driver, architecture, and transitive requirements. Record that decision in the reproduction instructions. Do not mix current examples with older crates while describing them as one validated environment, and do not assume a feature's presence proves runtime compatibility.

**中文：** 参考答案：比较指南所属提交与发布版清单及源码。检查过的已发布版本和较晚主分支快照属于不同源码状态，即使工作区版本字符串没有变化。可以保留发布版契约，也可以有意识固定新的 Git 修订，并评估工具链、驱动、架构和传递依赖要求；必须在复现说明记录选择。不能混用当前例子与旧软件包，却把它们描述成同一套已验证环境，也不能因特性名称存在就认定运行时兼容。

### Exercise 10: Choose the system boundary / 练习十：选择系统边界

**English:** Your task is a high-concurrency language-model service. Does writing a Candle forward pass solve scheduling and cache management? Propose a fair comparison with a serving runtime such as SGLang.

**中文：** 任务是高并发语言模型服务，写出 Candle 前向计算是否就解决了调度与缓存管理？请提出与 SGLang 这类服务运行时进行公平比较的方法。

**English:** Reference answer: A forward pass supplies model execution, while scheduling, admission control, batching, sequence caches, streaming, and cancellation still need an implementation or an existing runtime. Compare equivalent models, tokenizer behavior, precision, hardware, request distributions, and completed output quality. Separate startup, prefill, decode, and end-to-end latency, and measure throughput under stated concurrency and memory limits. Explain which layer owns each responsibility. A host-language comparison without those controls is not evidence about the capacity of the complete service. A single tiny-model computation cannot be generalized into a production-service conclusion.

**中文：** 参考答案：前向计算提供模型执行，调度、准入、批处理、序列缓存、流式响应和取消仍需实现或使用现成运行时。比较时应对齐模型、分词行为、精度、硬件、请求分布与完成输出质量，区分启动、预填充、生成和端到端延迟，并在明确并发与内存限制下测量吞吐。还应解释各层职责归属。缺少这些控制条件的主机语言对比，不足以证明完整服务容量，更不能把小模型单次计算推广为生产结论。

## Summary and acceptance / 总结与验收

**English:** You should now be able to trace text through tokenizer IDs, configuration, named weights, semantic tensor shapes, and a completed model output. Explain separately what Rust ownership guarantees, what the tensor layout describes, and what a device backend must implement. Reproduce the CPU output and every expected failure, then point to the exact source version that defines the APIs. These are observable acceptance criteria; merely recognizing the names Candle, CUDA, and cuTile is not equivalent to being able to integrate them.

**中文：** 学完后应能够沿着文本、分词编号、配置、具名权重、张量语义形状和已完成输出追踪全过程，并分别解释 Rust 所有权保障、张量布局描述以及设备后端必须实现的内容。需要复现 CPU 输出与全部预期失败，再指出定义接口的确切源码版本。这些是可观察验收条件；仅认识几个框架和工具名称，并不等于已经能够集成它们，也不能替代可运行实验提供的证据。

**English:** Before advancing, retain the manifest, generated lockfile, source, artifact schema, observed output, and environment record. Be able to explain the nonzero-offset test, derive the linear result, and distinguish the release baseline from the newer main snapshot. The next useful project is a small real model with a pinned tokenizer and checkpoint revision, layerwise correctness checks, and explicit startup/request timing. Add a GPU backend only when its environment can be validated, then preserve the same correctness boundary while investigating performance.

**中文：** 进入下一阶段之前，应保留清单、生成的锁文件、源码、产物结构、观察输出和环境记录，并能解释非零偏移测试、推导线性结果、区分发布基线与较新主分支。下一项有用实践是选择小型真实模型，固定分词器及权重修订，建立逐层正确性检查，并明确启动与请求计时。只有环境能够验证时再加入 GPU 后端，然后在研究性能时继续保留相同正确性边界，逐步扩大证据范围。

## Official references / 官方参考资料

**English:** Release and implementation references: [Candle 0.11.0 release](https://github.com/huggingface/candle/releases/tag/0.11.0), [release feature manifest](https://github.com/huggingface/candle/blob/0.11.0/candle-core/Cargo.toml), [tensor implementation](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/tensor.rs), [layout implementation](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/layout.rs), [custom operator traits](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/custom_op.rs), [parameter loader](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/var_builder.rs), and [linear layer](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/linear.rs). These fixed release links define the executable experiment's API contract.

**中文：** 发布与实现资料包括 [Candle 0.11.0 发布页](https://github.com/huggingface/candle/releases/tag/0.11.0)、[发布版特性清单](https://github.com/huggingface/candle/blob/0.11.0/candle-core/Cargo.toml)、[张量实现](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/tensor.rs)、[布局实现](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/layout.rs)、[自定义算子接口](https://github.com/huggingface/candle/blob/0.11.0/candle-core/src/custom_op.rs)、[参数加载器](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/var_builder.rs) 和[线性层](https://github.com/huggingface/candle/blob/0.11.0/candle-nn/src/linear.rs)。这些固定发布链接定义可执行实验的接口契约。

**English:** Adjacent specifications and comparison references: [safetensors documentation](https://huggingface.co/docs/safetensors/index), [Tokenizers pipeline](https://huggingface.co/docs/tokenizers/pipeline), [PyTorch 2.14 Linear](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Linear.html), and [SGLang documentation](https://docs.sglang.io/). The separate current-source discussion is pinned to [the inspected cuTile guide](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-book/src/guide/cutile.md) and [its custom-op example](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/examples/cutile.rs). Rolling documentation was checked on 2026-09-18; it does not retroactively change the pinned CPU validation.

**中文：** 相邻规范及对照资料包括 [safetensors 文档](https://huggingface.co/docs/safetensors/index)、[分词流水线](https://huggingface.co/docs/tokenizers/pipeline)、[PyTorch 2.14 线性层](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Linear.html) 和 [SGLang 文档](https://docs.sglang.io/)。另行讨论的当前源码固定于[检查过的 cuTile 指南](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-book/src/guide/cutile.md) 及[自定义算子例子](https://github.com/huggingface/candle/blob/ddf1b879dc3a1760cbcb3f3c4a7c6467850cec4a/candle-core/examples/cutile.rs)。滚动文档核验于 2026 年 9 月 18 日，不会追溯改变固定 CPU 实验的验证范围。
