# Course 11: DeepSeek Models and Deployment Analysis / 第十一课：DeepSeek 模型与部署分析

## Objectives and verification boundary / 目标与验证边界

**English:** This course teaches how to read a model artifact as an engineering specification. You will connect Transformer execution to parameter storage, attention state, batch and context capacity, quantization, and deployment choices. The main experiment downloads only a pinned configuration file and computes explicitly labeled resource estimates on CPU. It does not download weights or execute model code. The goal is to explain which resource terms are known, which are assumptions, and which must be measured before deciding that a deployment is feasible. Model names, file sizes, and advertised parameter totals are clues, not substitutes for component accounting or promises of serving capacity.

**中文：** 本课学习如何把模型产物当作工程规格阅读。你将把变换器执行过程与参数存储、注意力状态、批次和上下文容量、量化以及部署选择联系起来。主实验只下载固定版本配置文件，在处理器上计算明确标记的资源估算，不下载权重，也不执行模型代码。目标是解释哪些资源项已经知道，哪些属于假设，哪些必须实测之后才能判断部署可行。模型名称、文件大小和营销参数规模只是线索，不能代替逐项核算，也不能直接给出服务容量承诺。

**English:** Prerequisites are basic matrix dimensions, bytes and binary units, Python dictionaries and tests, and the prefill/decode concepts from Course 10. The local machine is recorded as RTX 4060 with CUDA toolkit 13.3, but its NVML initialization currently fails. That does not prevent configuration arithmetic, but it prevents this chapter from presenting local GPU measurements. CPU tests establish the implemented formulas and rejection rules; they do not establish actual allocator behavior, backend compatibility, generation quality, or achievable tokens per second. Keep calculable structural information separate from empirical behavior that requires device execution.

**中文：** 前置知识包括基本矩阵维度、字节与二进制容量单位、Python 字典和测试，以及上一课的预填充与解码概念。本地机器记录为 RTX 四〇六〇和 CUDA 工具链十三点三，但 NVML 当前初始化失败。这不妨碍配置算术，却意味着本课不能提供本机显卡实测。处理器测试验证的是公式实现和拒绝规则，不证明真实分配器行为、后端兼容、生成质量或每秒词元能力。必须把可计算的结构信息与需要设备执行的经验信息分开，才能让已有工作保持可信。

**English:** Sources were checked on 2026-09-18. The newest official model found in this verification is [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash), whose official repository metadata records creation on 2026-09-10. Its card describes a multimodal MoE with a causal encoder-decoder organization and compressed sparse attention. V4 Flash and Pro, including their dated refreshes, remain useful architectural comparisons; V3 is historical context rather than the latest release. The hands-on model is deliberately the older dense `DeepSeek-R1-Distill-Qwen-1.5B`, which is small enough for transparent resource reasoning. Teaching convenience and choosing the newest advanced model are different criteria.

**中文：** 来源核验日期为二〇二六年九月十八日。本次查到的最新官方模型是上述四点一快速版本，官方仓库元数据记录创建于九月十日，模型说明描述其为多模态混合专家结构，采用因果编码解码组织与压缩稀疏注意力。第四代快速版、专业版及其日期更新版仍可作为架构比较，第三代属于历史背景，不再是最新发布。动手部分有意使用较早的小型稠密蒸馏模型，因为它便于透明地推导资源。教学便利与当前最先进模型是两个不同选择标准，不能混为一谈。

## 1. Model names are not complete specifications / 模型名称不是完整规格

**English:** Separate a model family, an architecture, a checkpoint, a serialization format, and a serving implementation. A family name identifies lineage or product positioning; the architecture defines operations and state; a checkpoint provides trained tensor values; a format determines how those values are represented on disk; and a runtime chooses execution and memory policies. Two artifacts with similar names can differ at any of these layers. A deployment comparison should therefore record all five rather than treating a familiar prefix as evidence of identical requirements. A claim of model support must identify the architecture, weight format, and execution mode before it can guide resource budgeting or diagnosis.

**中文：** 应区分模型家族、架构、检查点、序列化格式与服务实现。家族名称表示技术来源或产品定位，架构定义运算与状态，检查点提供训练后的张量值，格式决定磁盘如何表示这些值，运行时则选择执行与内存政策。名字相近的两个产物，可能在任何一层不同。部署比较因此应记录全部五层，而不是看见熟悉前缀就认为需求相同。所谓支持某模型，也要说明支持的是哪组架构、权重格式和运行方式，否则这句话无法直接指导资源预算或故障诊断。

**English:** Distillation transfers training behavior into a student model; it does not require copying the teacher's inference architecture. The selected R1 distillation checkpoint declares `Qwen2ForCausalLM` and `model_type="qwen2"`. Its resource accounting therefore follows that dense Qwen-style layout, not the full R1 or V3 MoE layout. The [R1 report](https://arxiv.org/abs/2501.12948) describes distillation as a training route. When estimating serving memory, inspect the actual student configuration and tensors instead of importing the teacher's expert count, latent-attention representation, or parameter total. The source of learned capabilities and the execution structure are related but distinct, which is a key reason a small-model exercise cannot represent full large-model deployment.

**中文：** 蒸馏把训练行为传递给学生模型，并不要求复制教师推理架构。所选检查点声明的是 Qwen 系列稠密因果语言模型，因此资源核算应遵循该结构，而不是完整第一代推理模型或第三代混合专家结构。上述研究报告描述蒸馏这一训练路线；估算服务内存时，应检查实际学生配置和张量，而不能继承教师的专家数量、潜在注意力表示或总参数数。能力来源与执行结构存在关联，却不是同一个概念，这也是小模型实验无法代表完整大模型部署的关键原因。

**English:** A model repository can change while keeping the same public name. Pin the immutable revision when collecting configuration, tokenizer, and weights, and save a checksum of the exact file used by an estimator. The main exercise fixes revision `ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562`. This makes a later disagreement inspectable: you can distinguish a changed model artifact from a changed formula. A local filename such as `config.json` provides no provenance by itself, especially after files have been copied between experiment directories. Provenance initially needs only the repository, revision, file checksum, and calculation command, but these must be retained at execution time.

**中文：** 模型仓库可以在保持公开名称不变的情况下更新。收集配置、分词器和权重时，应固定不可变修订，并保存估算器实际使用文件的校验值。主实验固定到上述提交，使之后出现差异时能够区分模型产物改变与公式改变。单独一个配置文件名不提供来源信息，尤其当文件已经在多个实验目录之间复制之后。可追溯性并不要求复杂平台，最初只需要准确记录仓库、版本、文件校验和计算命令，但这些信息必须在运行当时保留下来。

**English:** Read model cards as claims with scope. A supported context length is a capability or configuration limit, not a promise that every device can serve that length at useful concurrency. A benchmark score depends on prompts, evaluation rules, sampling, and budget. A provider's API label can describe a hosted service whose actual deployment is not exposed. For local engineering, translate each statement into a concrete requirement: which artifact, which input type, which memory representation, which backend, and which acceptance test would establish the property you need? Turning promotional descriptions into testable requirements supports deployment decisions more directly than comparing rankings alone.

**中文：** 阅读模型说明时，应把每个结论连同适用范围一起看。支持的上下文长度是能力或配置上限，不承诺任何设备都能在有用并发下服务该长度；评测分数取决于提示、规则、采样和预算；供应商接口名称也可能描述一个内部部署不可见的托管服务。做本地工程时，应把这些陈述转成具体要求：哪个产物、哪种输入、什么内存表示、哪个后端，以及什么验收测试能够证明所需性质。把宣传描述转换成可验证条件，比简单比较模型排名更接近实际部署决策。

## 2. Transformer execution and stored state / 变换器执行与存储状态

**English:** A token identifier selects an embedding vector, then a stack of layers transforms the sequence representation. Attention mixes information across positions under the model's causal rules, and feed-forward blocks transform each position through learned projections and nonlinearities. A final output projection produces vocabulary logits, from which the generation policy selects a token. This is a computational dependency graph, not a list of storage allocations that must all persist. Distinguishing temporary activations from persistent weights and reusable attention state is essential for a useful memory budget. Besides identifying operators, determine when each category of data comes into existence and when it can be released.

**中文：** 词元编号选择嵌入向量，随后多层结构转换序列表示。注意力按照因果规则混合不同位置的信息，前馈模块通过学习到的投影和非线性变换处理各位置，最终输出投影产生词表预测分布，再由生成政策选择词元。这是一张计算依赖图，不是一份所有分配都必须长期保留的存储清单。需要区分临时激活、持久权重和可复用注意力状态，才能建立有用的内存预算。知道模型包含哪些算子，只是第一步，还要知道每类数据从何时存在到何时可以释放。

**English:** Prefill processes prompt positions and builds the starting attention state; autoregressive decoding then advances using previously produced tokens. Output length therefore adds sequential work, while input length changes the initial work and retained history. The model's maximum context generally constrains the combined sequence, not an unlimited prompt plus an independent unlimited answer. For capacity planning, use the number of stored tokens at the relevant point in time. A request near completion can consume more cache than it did when admitted, so budgeting only its initial prompt can understate peak state. Average input length is not a substitute for worst-case or high-percentile combined length; service commitments must account for growth.

**中文：** 预填充处理提示位置并建立起始注意力状态，自回归解码再利用已生成词元逐步推进。输出长度增加连续工作，输入长度改变初始计算与保留历史。模型最大上下文通常限制组合后的序列，而不是允许无限输入再额外附加无限答案。容量规划应使用相关时刻实际保存的词元数量；请求接近完成时的缓存可能比准入时更多，因此只按最初提示估算，会低估状态峰值。平均输入长度也不能直接代替最坏或高分位组合长度，服务承诺需要明确考虑增长过程。

**English:** Attention heads divide representation work, but query heads and KV heads need not be equal. Ordinary multi-head attention has corresponding query, key, and value heads; grouped-query attention shares a smaller set of key/value heads among more query heads. This changes stored state and projection sizes without making all attention computation disappear. The selected configuration has hidden width 1536, twelve query heads, and two KV heads, so its head dimension is 128. Using twelve instead of two in the cache formula would overestimate this particular KV payload sixfold. Follow actual tensor dimensions rather than selecting an arbitrary field labeled head count.

**中文：** 注意力头划分表示工作，但查询头和键值头不一定相等。普通多头注意力具有对应查询、键和值头，分组查询注意力则让较少键值头供更多查询头共享。这会改变状态存储和投影规模，却不表示注意力计算全部消失。所选配置隐藏宽度为一千五百三十六，查询头十二个，键值头两个，因此头维度是一百二十八。若在缓存公式里把两个误写成十二个，就会把该模型键值负载高估六倍。推导必须跟随张量真实形状，而不是只看到头数便随意选取。

**English:** The [pinned configuration](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B/blob/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562/config.json) includes a sliding-window field but sets `use_sliding_window` to false. Reading one isolated field can therefore produce the wrong architecture model. The estimator checks the enabling condition and refuses a configuration that requests sliding-window behavior, because its full-history formula would then be the wrong storage model. More generally, interpret fields together with architecture code and feature gates; a number present in a configuration is not proof that the corresponding execution path is active. Similar issues arise with quantization, expert routing, and positional encoding: find the conditions selecting actual behavior instead of counting every visible field in the budget.

**中文：** 固定配置虽然包含滑动窗口字段，却把启用开关设为假，因此孤立读取某个字段可能得到错误架构理解。估算器检查启用条件，并拒绝请求滑动窗口行为的配置，因为完整历史公式此时不是正确存储模型。更一般地说，配置字段应与架构代码和功能开关一起解释；出现一个数值，不证明对应执行路径正在使用。类似问题也会出现在量化、专家路由和位置编码设置中。读配置应寻找决定实际行为的组合条件，而不是把所有看得见的字段一律计入预算。

## 3. Dense and mixture-of-experts models / 稠密模型与混合专家模型

**English:** In a dense feed-forward block, tokens use the same learned projections. In an MoE block, a router selects a subset of expert networks for each token, possibly alongside shared experts. Activated parameters describe the selected computational path, whereas total parameters describe a much larger inventory of learned tensors. Neither number alone gives full runtime cost: routing, dispatch, communication, load balance, and shared components also matter. Sparse activation can reduce per-token arithmetic while leaving the deployment responsible for storing or obtaining many more weights than one token activates. Multiplying activated parameters by bytes per value and calling that the entire model's VRAM is a common substantial underestimate.

**中文：** 稠密前馈模块让词元使用相同学习投影；混合专家模块则由路由器为每个词元选择部分专家网络，还可能包含共享专家。激活参数描述被选择的计算路径，总参数描述更大的学习张量集合，两者都不能单独给出完整运行成本，因为还存在路由、分发、通信、负载均衡和共享组件。稀疏激活可以减少单词元算术，却仍然要求部署存放或取得远多于该词元激活量的权重。把激活参数乘每值字节数直接作为整模型显存，是一种常见且影响很大的低估。

**English:** Suppose different tokens in one batch select different experts. The union of needed experts can grow even if each token activates a small fixed number. Small expert batches can also lead to inefficient matrix shapes, while uneven routing leaves some devices busy and others waiting. A capacity plan must consider the distribution of routed tokens, not just average activated parameters. This is why a small dense student is useful for learning request flow but cannot reproduce the communication and expert-balance problems of a full MoE service. A teaching model can explain shared mechanisms only when the system behavior it simplifies is stated explicitly.

**中文：** 假设同一批次不同词元选择不同专家，即使每个词元激活固定且很小的数量，整批所需专家并集仍可能扩大。小型专家批次还会形成不理想的矩阵形状，不均匀路由则让某些设备繁忙、其他设备等待。因此容量规划需要考虑词元路由分布，而不只是平均激活参数。小型稠密学生适合学习请求路径，却不能复现完整混合专家服务的通信与负载均衡问题。教学模型可以帮助理解一些共同机制，但必须清楚哪些系统行为已经被简化掉。

**English:** Expert parallelism distributes experts across devices; tensor parallelism partitions selected tensor operations; data parallelism replicates model-serving capacity; pipeline parallelism partitions layers or stages. These are different decompositions with different memory and communication consequences. Dividing total model bytes by device count assumes a perfectly partitionable inventory and ignores replicated tensors, buffers, imbalance, and communication state. Use that division only as an optimistic first bound, then inspect the runtime's actual partitioning and topology before converting it into a hardware recommendation. Equal aggregate device memory does not imply equal usable deployment capacity or communication performance.

**中文：** 专家并行把专家分配到不同设备，张量并行划分某些张量运算，数据并行复制服务能力，流水线并行划分层或阶段。这些分解方式具有不同内存和通信后果。把总模型字节简单除以设备数，假设所有内容都能完美切分，忽略复制张量、缓冲、不均衡和通信状态，因此最多只能作为乐观初步边界。给出硬件建议前，还要检查运行时真实切分与连接拓扑。设备总容量相同，不代表两个部署具备相同可用容量，更不意味着通信性能相同。

**English:** Offloading moves some storage or work to host memory or another tier, trading device capacity for transfer and scheduling costs. A model that can start through offloading may still miss the application's response-time target. Host memory, transfer bandwidth, page movement, and the access pattern of routed experts become part of the design. Do not label offloading a universal solution to insufficient VRAM. Evaluate it with the intended input/output lengths and concurrency, and report actual completion latency together with the reduction in resident device memory. Fitting is a capacity judgment; useful operation additionally requires throughput, latency, and stability evidence.

**中文：** 卸载把部分存储或工作移到主机内存或其他层级，用传输与调度成本交换设备容量。通过卸载能够启动的模型，仍可能无法满足应用响应目标，此时主机内存、传输带宽、页面移动和专家访问模式都进入设计范围。不能把卸载当作显存不足的通用解决办法。应使用目标输入输出长度和并发评价它，同时报告完成延迟与设备驻留内存降低幅度。装得下回答的是容量问题，运行得合用还需要吞吐、延迟和稳定性证据，这两个判断应分开进行。

## 4. Architectural evolution and formula limits / 架构演进与公式边界

**English:** The historical [DeepSeek-V3 report](https://arxiv.org/abs/2412.19437) describes an MoE design with Multi-head Latent Attention. A latent representation can change which attention states are persisted and how they are reconstructed or consumed. Therefore the ordinary per-layer key/value-head formula is not automatically the right memory model. To estimate such a system, identify the actual cached tensors, their dimensions and dtypes, and any backend-dependent expanded representation. The architecture paper provides a model, while implementation inspection determines what the chosen serving path actually stores. A mathematically compressed representation does not mean every backend stores it identically, and one implementation's allocation is not representative of an entire architecture family.

**中文：** 历史第三代技术报告描述了混合专家与多头潜在注意力设计。潜在表示会改变哪些注意力状态长期保存，以及它们如何被重建或使用，因此普通逐层键值头公式不自动适用。估算这种系统时，需要识别实际缓存张量、维度、精度，以及后端可能展开的表示。架构论文提供理论模型，实现检查则决定所选服务路径真实存放什么。不能因为某种表示在数学上可以压缩，就直接假定所有后端都以同样方式保存，也不能用一个实现的分配结果代表整个架构家族。

**English:** The official [V4 model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) describes hybrid compressed sparse and heavily compressed attention, and mixed weight precision for instruct checkpoints. These are further reasons to stop using a single full-attention formula across generations. In a comparison, state whether you mean ordinary retained KV, compressed attention state, indexing state, or the total allocated pool. A reduction reported for one component or one context setting does not automatically equal the same reduction in total device memory or end-to-end latency. Put a component-level resource change back into the full budget to judge its practical value.

**中文：** 第四代官方模型说明描述了混合压缩稀疏注意力与高度压缩注意力，并说明指令检查点采用混合权重精度，这进一步表明不能跨代使用单一完整注意力公式。比较时应说明对象是普通保留键值、压缩注意力状态、索引状态，还是整个已分配池。某个组件或某种上下文条件下的降低比例，不自动等于总显存或端到端延迟降低同样比例。资源优化可能只影响系统的一部分，必须把局部变化放回完整预算，才能判断实际价值。

**English:** V4.1's official description changes the organization again: a causal encoder-decoder arrangement and cross-layer compressed-state handling alter the relation between layer count and persistent cache. Its card also distinguishes prefill and decode activation. This chapter does not derive a V4.1 memory calculator from the Qwen student, and does not treat a generic model-page launch snippet as proof that the pinned SGLang version supports every V4.1 path. The architectural difference is established by the official card; backend support requires a separately verified model-version-hardware combination. Knowing that a model exists and having validated a deployment are different evidence states.

**中文：** 四点一版本的官方描述再次改变组织方式，因果编码解码结构与跨层压缩状态处理，改变了层数和持久缓存之间的关系，说明中也区分预填充与解码激活。本课不会从小型学生公式推导它的显存计算器，也不会把模型页面通用启动片段当作固定 SGLang 版本支持所有新路径的证明。官方说明可以确认架构差异，后端支持则需要单独核实模型、版本和硬件组合。已经知道模型存在，与已经验证某种部署成立，是不同的知识状态。

**English:** The [SGLang V4 cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4) distinguishes verified hardware combinations from derived or modified configurations. That distinction is more useful than copying an impressive device count. A recipe for a named V4 variant on a particular accelerator does not establish support for V4.1, a consumer GPU, or a changed quantization format. Preserve the recipe revision and verification badge, then validate any changed combination. Here the cookbook is evidence that deployment support is conditional, not a local benchmark or a universal resource requirement. Preserve a source's limits rather than expanding one true fact into an unsupported recommendation.

**中文：** SGLang 第四代部署指南区分已验证硬件组合与推导或修改后的配置，这种区分比抄录一个显得强大的设备数量更有用。某个第四代变体在特定加速器上的方案，不能证明四点一版本、消费级显卡或改变后的量化格式也受支持。应保存方案版本与验证状态，再验证发生变更的组合。这里引用指南，是说明部署支持具有条件，而不是提供本机基准或普遍资源要求。引用来源时保留其边界，才能避免把一条真实信息扩大成并没有证据支持的推荐。

## 5. Decompose the memory budget / 分解内存预算

**English:** Begin with separate terms for weight payload, quantization metadata, persistent attention state, temporary activations, operator workspaces, graph pools, allocator overhead, and communication buffers. Some terms scale with total parameters, some with batch and context, and some depend on implementation choices. A single “model size” number hides these differences. Keep unknown terms visible rather than setting them to zero without comment. The estimator uses an explicit assumed reserve for unmodeled terms, making uncertainty a parameter that can be varied instead of a hidden promise. A budget should expose dependencies and missing information rather than use precise decimals to imply complete knowledge of the system.

**中文：** 应分别列出权重负载、量化元数据、持久注意力状态、临时激活、算子工作空间、计算图池、分配器开销和通信缓冲。有些项随总参数增长，有些随批次与上下文变化，还有些取决于实现选择。一个模型大小数字隐藏了这些差异。未知项应保持可见，而不是没有说明就设为零。本估算器对未建模项使用显式假设余量，让不确定性成为可以改变的参数，而不是隐藏承诺。预算的价值在于暴露主要依赖和缺失信息，并非用一串精确小数制造已经完全了解系统的错觉。

**English:** Weight payload is approximately parameter count times bits per parameter divided by eight, but the parameter count must match the tensors being stored. Vocabulary embeddings and an untied output projection can contribute substantially in a small model. Biases, normalization parameters, shared tensors, and additional heads also affect exact counts. The student model's name contains “1.5B,” yet the specific Qwen layout and repository metadata yield 1,777,088,000 parameters. This is why the exercise derives the inventory from dimensions instead of multiplying a rounded product label. Precise arithmetic needs sufficiently precise inputs; otherwise it only computes a rough assumption precisely.

**中文：** 权重负载可以近似按参数数乘每参数位数再除以八计算，但参数数必须对应实际存放张量。小模型的词表嵌入与未绑定输出投影可能占据明显比例，偏置、归一化参数、共享张量和额外预测头也会影响精确计数。所选模型名字虽然包含一点五十亿，但特定结构和仓库元数据得到的计数是十七亿七千七百零八万八千。实验因此从维度推导清单，而不是拿四舍五入的产品标签直接相乘。精确算术应该建立在足够精确的输入上，否则只是精确计算了一个粗略假设。

**English:** For the stated Qwen2 layout, count the embedding table, the separate vocabulary output head, per-layer Q/K/V/O projections, Q/K/V biases, three feed-forward matrices, two per-layer normalization vectors, and the final normalization vector. The [versioned reference implementation](https://github.com/huggingface/transformers/blob/v4.48.2/src/transformers/models/qwen2/modeling_qwen2.py) establishes these structural assumptions. The arithmetic count is cross-checked against official repository tensor metadata without downloading weights. This is a structural consistency check, not validation of every stored tensor value or a measurement of loaded memory. This cross-check can expose missing or duplicated terms, while disk structure, logical parameters, and resident runtime representations can still differ.

**中文：** 对明确指定的结构，需要计算嵌入表、独立词表输出头、每层四个注意力投影、查询键值偏置、三个前馈矩阵、每层两个归一化向量和最终归一化向量。上述固定版本参考实现确认这些结构假设，算术结果又与官方仓库张量元数据核对，全程不下载权重。这只是结构一致性检查，不验证每个张量值，也不测量加载后的内存。通过这种核对可以发现漏算与重复计算，但仍要记住磁盘结构、逻辑参数和运行时驻留表示可能有所不同。

**English:** Units matter. Decimal gigabytes divide by one billion, while GiB divides by `1024**3`; mixing them can create an apparent capacity discrepancy. The experiment reports exact integer bytes and an explicitly named binary-unit conversion. Its default eight-GiB budget is a scenario supplied to the calculator, not a detected property of the current GPU. Similarly, one GiB of reserve is an assumption, not an empirically justified safety margin. Change both values when exploring a different machine, and keep their provenance beside the calculated terms. This prevents convenient example defaults from later being mistaken for hardware measurements.

**中文：** 单位同样重要，十进制吉字节按十亿相除，二进制吉字节按一千零二十四的三次方相除，混用会制造看似莫名的容量差异。实验报告精确整数字节，并明确给出二进制单位转换。默认八个二进制吉字节预算是计算场景，不是检测到的本机显卡属性；一个二进制吉字节余量也是假设，不是经过经验验证的安全边界。探索不同机器时应修改这两个输入，并把来源与计算项一起保留，避免后来把方便演示的默认值误当成真实硬件测量。

## 6. Quantization is a format and execution choice / 量化是格式与执行选择

**English:** Reducing weight precision can reduce the packed payload, but scales, zero points, grouping, padding, and unquantized tensors remain. A four-bit label does not mean every byte in the artifact contributes exactly two model parameters. Mixed-precision models require component-wise accounting. The estimator's low-bit scenario deliberately models an ideal packed payload plus one small scale per group; it omits zero points and per-tensor alignment. This is a transparent sensitivity calculation, not a claim that a particular quantization package or checkpoint has that exact layout. Explicit simplifications make an estimate useful; naming an ideal lower bound as actual file size would mislead deployment selection.

**中文：** 降低权重精度可以减少打包负载，但比例因子、零点、分组、补齐以及未量化张量仍然存在。四位标签不代表产物中的每个字节都恰好贡献两个模型参数，混合精度模型还需要按组件核算。估算器的低位场景刻意采用理想打包负载加每组一个小比例因子，省略零点和逐张量对齐。这是透明的敏感性计算，不声称某个具体量化包或检查点采用完全相同布局。明确简化项可以让估算有用，而把理想下界直接命名为实际文件大小则会误导部署选择。

**English:** Weight precision and KV precision are independent controls. Quantizing weights does not automatically reduce attention-state bytes; reducing KV precision does not automatically shrink the model's matrices. A long-context deployment can remain cache-limited after a large weight reduction. Conversely, a short-context service may gain little capacity from a smaller cache representation if weights dominate. The main experiment varies the two independently and tests that changing weight bits leaves its modeled KV payload unchanged. This prevents an implementation from accidentally using one dtype multiplier for every resource category. Account for each category's representation instead of assigning the whole model one precision label.

**中文：** 权重精度与键值精度是独立控制。量化权重不会自动减少注意力状态字节，降低键值精度也不会自动缩小模型矩阵。长上下文部署在权重大幅减少后，仍可能受缓存容量限制；短上下文服务如果权重占主导，缩小缓存表示带来的容量收益可能很小。主实验独立改变两者，并测试权重位数改变时，建模的键值负载保持不变。这能防止实现误用一个精度乘数计算全部资源类别。正确估算需要知道每项数据采用什么表示，而不是给整个模型贴一个统一精度标签。

**English:** A smaller representation is not automatically faster. Quantized execution may require unpacking, scale application, different kernels, or temporary expansion. Whether it improves latency depends on the device, batch shape, arithmetic support, memory traffic, and implementation. Quality also changes independently of memory savings. Compare the same task set and serving workload before and after quantization, keeping generation policy and evaluation criteria fixed. A reduction in stored bytes can be established analytically, while a speedup and acceptable answer quality require separate measurements. Halving an estimated capacity term does not establish doubled throughput, and successful loading is not evidence of unchanged quality.

**中文：** 更小表示不自动更快，量化执行可能需要解包、应用比例因子、采用不同核函数或临时展开。延迟是否改善取决于设备、批次形状、算术支持、访存和实现；质量变化也独立于存储收益。比较量化前后，应使用相同任务集和服务负载，固定生成政策与评价标准。存储字节降低可以通过算术建立，而速度提升和可接受回答质量需要分别测量。不能因为容量估算减少一半，就宣称吞吐翻倍，更不能把能够加载作为质量没有退化的证据。

**English:** Backend support must include the exact quantization format and hardware path. Names such as FP8 or FP4 describe families of representations, not a guarantee that all kernels accept the same tensor layout, scaling scheme, or accumulator type. The verified V4 recipes include hardware-specific choices, which illustrates why copying only the model name is insufficient. For the teaching calculator, one-byte KV values are a hypothetical storage scenario. The output intentionally does not assert that the local GPU and pinned runtime can execute that scenario correctly or efficiently. Confirm separately that a model permits a representation, an artifact uses it, and the device has an effective execution path for it.

**中文：** 后端支持必须具体到量化格式和硬件路径。八位或四位浮点名称描述一类表示，不保证所有核函数接受相同张量布局、缩放方案或累加类型。已经验证的第四代部署方案包含针对硬件的选择，这正说明只复制模型名为什么不够。教学计算器的一字节键值，只是假设存储场景；输出有意不声称本地显卡与固定运行时能正确或高效执行它。模型允许某种表示、文件采用某种表示和设备拥有有效执行路径，是三个需要分别确认的问题。

## 7. Complete CPU resource experiment / 完整处理器资源实验

**English:** Work in a new directory containing only the following three scripts. The fetch script reads a single 679-byte configuration, checks its known SHA-256, and refuses to overwrite an existing file. No framework import, weight download, GPU initialization, or remote model code is involved. This makes the experiment useful even while the device environment is unavailable. The expected checksum comes from the pinned official artifact; a mismatch should stop the exercise for inspection rather than trigger automatic acceptance of changed input. Small metadata experiments establish resource provenance before deciding whether costly weight downloads and real deployment are worthwhile.

**中文：** 在新目录中保存下面三个脚本。获取脚本只读取一个六百七十九字节的配置，检查已知校验值，并拒绝覆盖已有文件；全过程不导入模型框架、不下载权重、不初始化显卡，也不执行远程模型代码。因此即使设备环境暂不可用，实验仍然有价值。预期校验来自固定官方产物，发生不匹配时应停止检查，而不是自动接受变化后的输入。小型元数据实验可以先建立可追溯的资源理解，再决定是否值得进行成本更高的权重下载和真实部署。

### Fetch the pinned configuration / 获取固定配置

**English:** Save as `fetch_config.py`. The size bound catches an unexpected response before it is treated as configuration, and the checksum identifies exact bytes rather than only parsed values. If the file already exists, inspect its checksum or choose a fresh directory. Reusing an unknown file merely because its name matches would defeat the provenance boundary established at the start of the course. Refusing overwrite makes input changes explicit; a more elaborate cache would still need source and content checks rather than trusting any existing file.

**中文：** 保存为 `fetch_config.py`。大小边界在响应被当成配置之前捕获异常内容，校验值识别精确字节，而不只是解析后的值。如果文件已经存在，应检查它的校验，或选择新目录。不能仅因文件名相同就复用未知文件，否则课程开头建立的来源边界将失效。这里采用拒绝覆盖，是为了让输入变更保持显式；实际工具也可以设计缓存策略，但必须核对来源和内容，而不是默认任何现成文件都可靠。

```python
import hashlib
import urllib.request
from pathlib import Path

MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
REVISION = "ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562"
SHA256 = "37bd455e9679d2959536270fed49d25cc7c290a64f6e52abb97c71345a9cee41"
url = f"https://huggingface.co/{MODEL}/resolve/{REVISION}/config.json"
with urllib.request.urlopen(url, timeout=30) as response:
    content = response.read(1024 * 1024 + 1)
if len(content) > 1024 * 1024:
    raise ValueError("unexpectedly large configuration")
if hashlib.sha256(content).hexdigest() != SHA256:
    raise ValueError("configuration checksum differs from the teaching snapshot")
with Path("config.json").open("xb") as stream:
    stream.write(content)
print(f"downloaded config only: bytes={len(content)}, sha256={SHA256}")
```

### Implement the estimator / 实现估算器

**English:** Save as `estimate.py`. The implementation accepts only the stated dense Qwen2 layout, validates positive integer dimensions, and rejects unsupported sliding-window cache semantics. It reports a scenario margin rather than a boolean “fits” promise. Packed low-bit weights use an idealized global grouping calculation; real per-tensor grouping can need additional scales and padding. The reserve is added after the modeled subtotal so readers can separate derived quantities from assumptions. Output is written to a new JSON file with the exact configuration checksum. Every reported quantity should remain traceable to its formula, assumptions, and input instead of becoming an unexplained total.

**中文：** 保存为 `estimate.py`。实现只接受明确指定的稠密结构，校验正整数维度，并拒绝未支持的滑动窗口缓存语义。它报告场景余量，而不是能否装下的布尔承诺。低位权重采用理想全局分组计算，实际逐张量分组可能需要更多比例因子与补齐。假设余量在建模小计之后单独加入，使读者能够区分推导量与人为输入。结果写入新的 JSON 文件，并附带精确配置校验；这样每个数字都能追溯到公式、假设和输入，而不会混成一个来源不明的总量。

```python
import argparse
import hashlib
import json
import math
from pathlib import Path


def positive_int(value, label):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def dimensions(config):
    if (config.get("architectures") != ["Qwen2ForCausalLM"]
            or config.get("model_type") != "qwen2"):
        raise ValueError("this estimator supports only the stated dense Qwen2 layout")
    if config.get("use_sliding_window", False) is not False:
        raise ValueError("sliding-window cache requires a separate storage model")
    if type(config.get("tie_word_embeddings")) is not bool:
        raise ValueError("tie_word_embeddings must be explicit bool")
    keys = ["hidden_size", "num_attention_heads", "num_key_value_heads",
            "num_hidden_layers", "intermediate_size", "vocab_size",
            "max_position_embeddings"]
    d = {key: positive_int(config.get(key), key) for key in keys}
    if d["hidden_size"] % d["num_attention_heads"]:
        raise ValueError("hidden_size must divide into query heads")
    if d["num_attention_heads"] % d["num_key_value_heads"]:
        raise ValueError("query heads must divide into KV groups")
    d["head_dim"] = d["hidden_size"] // d["num_attention_heads"]
    return d


def parameter_count(config):
    d = dimensions(config)
    h, i, v = d["hidden_size"], d["intermediate_size"], d["vocab_size"]
    kv_width = d["num_key_value_heads"] * d["head_dim"]
    embedding = v * h
    output_head = 0 if config["tie_word_embeddings"] else v * h
    attention = 2 * h * h + 2 * h * kv_width
    qkv_bias = h + 2 * kv_width
    mlp = 3 * h * i
    layer_norms = 2 * h
    return (embedding + output_head
            + d["num_hidden_layers"] * (attention + qkv_bias + mlp + layer_norms)
            + h)


def estimate(config, *, batch, context, weight_bits, kv_bytes,
             budget_gib, reserve_gib, group_size=128, scale_bytes=2):
    d = dimensions(config)
    batch = positive_int(batch, "batch")
    context = positive_int(context, "context")
    if context > d["max_position_embeddings"]:
        raise ValueError("context exceeds this configuration's declared limit")
    if type(weight_bits) is not int or weight_bits not in (4, 8, 16, 32):
        raise ValueError("weight_bits must be 4, 8, 16, or 32")
    if type(kv_bytes) is not int or kv_bytes not in (1, 2, 4):
        raise ValueError("kv_bytes must be 1, 2, or 4")
    group_size = positive_int(group_size, "group_size")
    scale_bytes = positive_int(scale_bytes, "scale_bytes")
    if (not math.isfinite(budget_gib) or budget_gib <= 0
            or not math.isfinite(reserve_gib) or reserve_gib < 0):
        raise ValueError("budget must be positive; reserve must be nonnegative")
    params = parameter_count(config)
    weight_payload = (params * weight_bits + 7) // 8
    scales = ((params + group_size - 1) // group_size) * scale_bytes if weight_bits < 16 else 0
    kv = (2 * d["num_hidden_layers"] * batch * context
          * d["num_key_value_heads"] * d["head_dim"] * kv_bytes)
    reserve = round(reserve_gib * 1024 ** 3)
    budget = round(budget_gib * 1024 ** 3)
    subtotal = weight_payload + scales + kv
    return {"kind": "analytical_estimate_not_measurement", "parameter_count": params,
            "batch": batch, "stored_tokens_per_sequence": context,
            "weight_bits": weight_bits, "kv_bytes_per_value": kv_bytes,
            "weight_payload_bytes": weight_payload, "idealized_scale_bytes": scales,
            "kv_payload_bytes": kv, "modeled_subtotal_bytes": subtotal,
            "assumed_other_bytes": reserve, "assumed_budget_bytes": budget,
            "scenario_margin_bytes": budget - subtotal - reserve,
            "modelled_plus_reserve_gib": (subtotal + reserve) / 1024 ** 3}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--context", type=int, default=2048)
    parser.add_argument("--weight-bits", type=int, default=16)
    parser.add_argument("--kv-bytes", type=int, default=2)
    parser.add_argument("--budget-gib", type=float, default=8)
    parser.add_argument("--reserve-gib", type=float, default=1)
    args = parser.parse_args()
    content = args.config.read_bytes()
    config = json.loads(content)
    report = estimate(config, batch=args.batch, context=args.context,
        weight_bits=args.weight_bits, kv_bytes=args.kv_bytes,
        budget_gib=args.budget_gib, reserve_gib=args.reserve_gib)
    report["config_sha256"] = hashlib.sha256(content).hexdigest()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

### Test the assumptions / 测试假设

**English:** Save as `test_estimate.py`. Tests cover the pinned parameter inventory, linear KV scaling with batch and context, the independence of weight and KV precision, invalid dimensions, unsupported architectures, sliding-window rejection, tied-embedding accounting, and the distinction between a negative margin and a measured deployment failure. The tests use configuration arithmetic only. They are intentionally about invariants and counterexamples, rather than merely asserting that the script printed a JSON object without raising an exception. Resource tools can silently miscount, especially by omitting an independent output head or using query-head counts; verification must target such defects, beyond apparent execution success.

**中文：** 保存为 `test_estimate.py`。测试覆盖固定参数清单、缓存随批次和上下文的线性缩放、权重与键值精度独立、非法维度、未支持架构、滑动窗口拒绝、嵌入绑定核算，以及负余量与真实部署失败之间的区别。所有测试只使用配置算术，重点是约束与反例，而不是仅断言脚本能够打印一个对象且没有异常。资源估算程序同样可能发生静默算错，尤其是漏掉独立输出头或错误使用查询头数，因此需要能针对这些缺陷的验证，而非表面运行成功。

```python
import copy
import json
import unittest
from pathlib import Path

from estimate import estimate, parameter_count


class EstimateTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path("config.json").read_text())

    def calculate(self, **changes):
        args = dict(batch=1, context=2048, weight_bits=16, kv_bytes=2,
                    budget_gib=8, reserve_gib=1)
        args.update(changes)
        return estimate(self.config, **args)

    def test_pinned_layout_parameter_count(self):
        self.assertEqual(parameter_count(self.config), 1_777_088_000)

    def test_kv_reference_and_scaling(self):
        base = self.calculate()["kv_payload_bytes"]
        self.assertEqual(base, 56 * 1024 ** 2)
        self.assertEqual(self.calculate(batch=4)["kv_payload_bytes"], base * 4)
        self.assertEqual(self.calculate(context=4096)["kv_payload_bytes"], base * 2)
        self.assertEqual(self.calculate(kv_bytes=1)["kv_payload_bytes"], base // 2)

    def test_weight_and_kv_precision_are_independent(self):
        a, b = self.calculate(), self.calculate(weight_bits=4)
        self.assertEqual(a["kv_payload_bytes"], b["kv_payload_bytes"])
        self.assertEqual(b["weight_payload_bytes"] * 4, a["weight_payload_bytes"])
        self.assertGreater(b["idealized_scale_bytes"], 0)

    def test_invalid_dimensions(self):
        for key, value in [("batch", True), ("context", 0), ("context", 131073),
                           ("kv_bytes", 3), ("weight_bits", 3),
                           ("budget_gib", float("nan"))]:
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    self.calculate(**{key: value})

    def test_other_architecture_rejected(self):
        self.config["model_type"] = "deepseek_v4"
        with self.assertRaisesRegex(ValueError, "dense Qwen2"):
            self.calculate()

    def test_sliding_window_rejected(self):
        self.config["use_sliding_window"] = True
        with self.assertRaisesRegex(ValueError, "separate storage"):
            self.calculate()

    def test_tied_embedding_accounting(self):
        original = parameter_count(self.config)
        tied = copy.deepcopy(self.config)
        tied["tie_word_embeddings"] = True
        self.assertEqual(original - parameter_count(tied),
                         self.config["vocab_size"] * self.config["hidden_size"])

    def test_budget_is_scenario_not_fit_claim(self):
        report = self.calculate(budget_gib=1)
        self.assertLess(report["scenario_margin_bytes"], 0)
        self.assertEqual(report["kind"], "analytical_estimate_not_measurement")
        self.assertNotIn("fits", report)


if __name__ == "__main__":
    unittest.main()
```

```bash
python3 fetch_config.py
python3 -m unittest -v test_estimate.py
python3 estimate.py config.json fp16-b1-c2048.json --batch 1 --context 2048 --weight-bits 16 --kv-bytes 2
python3 estimate.py config.json int4-b1-c2048.json --batch 1 --context 2048 --weight-bits 4 --kv-bytes 2
python3 estimate.py config.json fp16-b4-c8192.json --batch 4 --context 8192 --weight-bits 16 --kv-bytes 2
python3 estimate.py config.json fp16-kv1-b4-c8192.json --batch 4 --context 8192 --weight-bits 16 --kv-bytes 1
```

**English:** The recorded CPU run used CPython 3.14.4 on 2026-09-18. All eight tests passed. The baseline calculated 3,554,176,000 bytes of sixteen-bit weight payload and 58,720,256 bytes of KV payload, for a modeled subtotal of 3,612,896,256 bytes. Adding the assumed one-GiB reserve gives approximately 4.365 GiB. Every number in this paragraph is derived arithmetic, not device allocation. The exact script output labels that distinction so copying the JSON into a later report does not silently convert an estimate into a measurement.

**中文：** 记录的处理器运行使用 CPython 三点十四点四，日期为二〇二六年九月十八日，八个测试全部通过。基线计算得到十六位权重负载三十五亿五千四百一十七万六千字节，键值负载五千八百七十二万零二百五十六字节，建模小计三十六亿一千二百八十九万六千二百五十六字节。加入假设的一吉二进制字节余量后约为四点三六五吉二进制字节。本段全部数字都是推导算术，不是设备分配；脚本输出明确标记这一点，防止后来复制报告时悄悄改变证据性质。

## 8. Read the sensitivity results / 阅读敏感性结果

**English:** Run the following two commands as deliberate failures after the successful baseline. Zero batch size violates the positive-dimension contract, and context 131073 exceeds this pinned configuration's declared limit. Each command must return a nonzero status before creating its named report. These are input-validation failures, not GPU out-of-memory results. If a stale file with either output name already exists, use a fresh directory so its presence cannot be mistaken for a newly written failure artifact. The unit tests additionally exercise a different architecture and sliding-window mode, both of which require a different formula rather than a larger budget. The error category determines the next action, so understand the rejection before changing input.

**中文：** 成功基线之后，可把下列两条命令作为有意失败场景执行。批次零违反正维度契约，上下文十三万一千零七十三超过固定配置声明的上限；两条命令都应在创建指定报告之前返回非零状态。这些是输入校验失败，不是显卡内存不足结果。如果同名旧文件已经存在，应换新目录，避免把它误认为本次新产生的失败产物。单元测试还覆盖不同架构与滑动窗口模式，它们需要不同公式，不能只靠增加预算修复。错误类型决定下一步动作，应先理解拒绝原因，再调整输入。

```bash
python3 estimate.py config.json invalid-batch.json --batch 0
python3 estimate.py config.json invalid-context.json --context 131073
```

**English:** Compare one factor at a time. Moving from batch one at context 2048 to batch four at context 8192 multiplies independent full-history KV payload by sixteen. It does not multiply shared model weights by sixteen in this single-model scenario. Halving KV bytes halves that modeled component, while changing sixteen-bit weights to four-bit weights quarters only the ideal weight payload before metadata. These proportional relationships are more informative than one total number because they identify which workload dimension can consume the remaining budget fastest. They also help decide whether to first limit context, concurrency, or weight representation.

**中文：** 每次只比较一个因素。从批次一、上下文两千零四十八，变成批次四、上下文八千一百九十二，独立完整历史缓存负载会扩大十六倍；在这个单模型场景里，共享权重不会同时扩大十六倍。键值字节减半，会让该建模组件减半；十六位权重改为四位，则只让元数据之前的理想权重负载变成四分之一。这些比例关系比一个总量更有信息，因为它们指出哪种负载维度最容易消耗剩余预算，也能帮助判断应该优先限制上下文、并发还是权重表示。

**English:** A negative scenario margin means the modeled terms plus chosen reserve exceed the supplied budget. A positive margin means only that this particular arithmetic scenario leaves room. Neither outcome is a direct runtime measurement. Unmodeled workspaces, loading peaks, memory fragmentation, graph capture, and backend expansion can invalidate a positive result. Conversely, a more sophisticated representation or verified offloading plan can change a negative result's assumptions. The estimator narrows the questions for deployment; it does not replace deployment validation. Use the output to guide the next validation steps rather than letting one number authorize procurement, deployment, or performance commitments.

**中文：** 场景余量为负，表示建模项加所选预留超过给定预算；余量为正，只表示这组算术假设留下空间，两者都不是运行时测量。未建模工作空间、加载峰值、碎片、计算图捕获和后端展开，都可能让正值不能兑现；反过来，更复杂表示或已验证卸载方案，也可以改变负值所依赖的假设。估算器缩小部署需要回答的问题，不能替代部署验证。正确使用方式是把输出当作下一轮验证清单的依据，而不是让一个数字自动决定采购、上线或性能承诺。

**English:** Loading and steady-state serving can have different peaks. Converting a checkpoint may temporarily retain both original and converted weights; initializing workspaces or capturing graphs can reserve additional memory before normal requests begin. A steady-state budget that appears comfortable may therefore still fail during startup. Keep startup logs and measure the complete lifecycle on a working device. If a proposed optimization only lowers steady-state KV storage, it may not solve a loading peak caused by conversion buffers, so the timing of the failure matters as much as the final total. Attributing every memory error to excessive context length misses remedies specific to other lifecycle stages.

**中文：** 加载和稳态服务可能有不同峰值。检查点转换可能暂时同时保留原始权重与转换权重，初始化工作空间或捕获计算图也可能在普通请求开始前预留内存。因此看似宽裕的稳态预算，仍可能在启动时失败。健康设备上应保存启动日志，并测量完整生命周期。如果优化只降低稳态键值存储，就未必能解决转换缓冲导致的加载峰值，所以失败发生时间与最终总量一样重要。把所有内存错误都归因于上下文太长，会漏掉不同阶段真正需要的修复。

**English:** Prefix sharing changes the independent-sequence assumption. If several requests reference the same cached prefix, multiplying every full sequence by batch size overcounts that shared portion. The amount saved depends on exact token identity, cache policy, eviction, and active references. The simple calculator intentionally excludes sharing so its baseline remains inspectable. To extend it, split each sequence into shared and unique portions and count each physical stored segment once. Do not apply an arbitrary cache-hit percentage to the whole memory budget, because weights and many temporary buffers are unaffected. Shared-state savings come from deduplicating specific objects, not proportionally shrinking all resources.

**中文：** 前缀共享会改变序列相互独立的假设。多个请求引用同一个缓存前缀时，把每条完整序列都乘批次，会重复计算共享部分；节省多少又取决于准确词元身份、缓存政策、淘汰和活跃引用。简单计算器有意不计共享，以保持基线清楚。扩展时应把序列拆成共享与独有部分，每段物理存储只计算一次，不能把任意命中百分比乘到整个内存预算上，因为权重和许多临时缓冲不受影响。共享节省来自具体对象去重，不是所有资源自动同比缩减。

## 9. Model selection as a constrained decision / 把模型选择视为约束决策

**English:** Start with the task and an acceptance set: representative inputs, required output behavior, latency budget, concurrency, context distribution, failure policy, and data-handling requirements. Then choose candidate models and deployment modes that can plausibly meet those constraints. Ranking models only by total parameters or a public benchmark ignores what the service actually needs. A smaller model with a reliable serving path can be more useful for a constrained application, while a harder reasoning task may justify a larger model and a different hardware or hosted-service plan. Match capability, resources, and service objectives with testable criteria, and retain alternatives if a candidate fails.

**中文：** 首先定义任务与验收集合，包括代表性输入、输出行为、延迟预算、并发、上下文分布、失败政策和数据处理要求，再选择可能满足约束的模型与部署方式。只按总参数或公开评测排名，忽略了服务真正需要什么。较小模型配合可靠执行路径，可能更适合约束明确的应用；更难推理任务也可能值得采用更大模型以及不同硬件或托管计划。选择不是简单寻找最大的名字，而是让能力、资源和服务目标之间形成可以验证的匹配，并保留不满足要求时的替代方案。

**English:** Separate capability evaluation from serving measurement. Capability tests ask whether the output solves the task under a stated generation policy. Serving tests ask how reliably and efficiently that policy runs under a workload. More reasoning tokens can improve some answers while increasing latency and retained state; restricting output can improve measured throughput while degrading completion quality. Report both sides together. A deployment that achieves a latency target by truncating most useful answers has changed the task rather than necessarily solving the original performance problem. For reasoning-model comparisons in particular, generation budget affects both quality and system resources and must be recorded as a controlled condition.

**中文：** 能力评价与服务测量应分开。前者判断在规定生成政策下输出能否解决任务，后者判断该政策在给定负载下是否可靠高效。更多推理词元可能改善部分答案，同时增加延迟和保留状态；限制输出可能改善测得吞吐，却降低完成质量，因此两边应一起报告。如果部署通过截断多数有用回答来达到延迟目标，它改变了任务，不一定解决原性能问题。尤其比较推理模型时，生成预算既是质量因素也是系统资源因素，需要作为受控条件明确记录。

**English:** Small dense models, full MoE models, and hosted APIs answer different operational needs. The student checkpoint is appropriate for understanding config inspection, cache arithmetic, request flow, and reproducible client behavior. Full MoE research adds routing, parallelism, topology, and much larger storage. Hosted APIs can provide capabilities without local weight management, but expose a different level of control and observability. Learning one path provides useful concepts for the others, while practical claims must stay attached to the path actually exercised. Successfully calling a hosted model does not establish experience deploying its local inference infrastructure.

**中文：** 小型稠密模型、完整混合专家模型与托管接口满足不同运维需求。学生检查点适合理解配置检查、缓存算术、请求流程和可复现客户端行为；完整混合专家研究增加路由、并行、拓扑和更大存储；托管接口可以免去本地权重管理，却提供不同程度的控制与可观测性。学习一种路径可以为另外两种提供概念基础，但实际能力与性能结论必须附着在真正操作过的路径上。不能把成功调用托管模型，等同于已经具备该模型本地推理基础设施部署经验。

**English:** Maintain a short decision record for each candidate: exact artifact and revision, architecture family, weight format, intended context and concurrency, analytically known terms, unresolved runtime terms, backend evidence, and functional acceptance results. Reject a candidate when a mandatory requirement fails, rather than hiding the mismatch behind a better headline score. If the evidence is incomplete, state the next experiment that would resolve it. This turns model selection into a repeatable engineering process instead of a series of untraceable preferences. When requirements or hardware change, the record also shows which conclusions remain valid and which need new validation.

**中文：** 每个候选应保留简短决策记录，包括精确产物与修订、架构家族、权重格式、目标上下文与并发、算术已知项、尚未确认的运行项、后端证据和功能验收结果。强制要求不满足时应排除候选，不能用更好看的总分掩盖不匹配。证据不足时，明确指出哪项下一步实验可以解决疑问。这样的记录让模型选择成为可重复工程流程，而不是一串无法追溯的偏好；之后需求或硬件改变，也能看清哪些结论仍有效，哪些必须重新验证。

## 10. Ten exercises with reference answers / 十道习题与参考答案

### Exercise 1: Teacher and student / 习题一：教师与学生

**English:** Exercise: A model name begins with DeepSeek-R1 but its configuration says `Qwen2ForCausalLM`. Which architecture should determine its KV estimate? Reference answer: the actual student architecture and serving representation. Distillation lineage does not copy the teacher's MoE or latent-attention storage rules. Inspect the pinned config and relevant implementation before choosing a formula. The teacher's capabilities can explain the training story, while the student's tensors determine local parameter and cache accounting. Conflating these two questions leads to incorrect hardware conclusions. Training lineage alone does not establish identical memory layout or parallel execution.

**中文：** 练习：模型名以某推理家族开头，配置却声明稠密学生架构，键值估算应依据哪一个？参考答案：实际学生架构与服务表示。蒸馏来源不会复制教师的混合专家或潜在注意力存储规则，选择公式之前应检查固定配置及相关实现。教师能力可以解释训练故事，学生张量才决定本地参数和缓存核算。混淆这两个问题会得出错误硬件结论。正确答案需要明确区分训练来源与推理结构，不能仅凭名字属于同一家族，就假定内存布局和并行方式也相同。

### Exercise 2: Total and activated parameters / 习题二：总参数与激活参数

**English:** Exercise: An MoE activates a small subset of its parameters per token. Can resident weight storage be estimated from only that subset? Reference answer: generally no. Other tokens can select different experts, and the deployment must retain or retrieve the larger weight inventory. Shared layers, routing, and communication add further costs. Activated parameters inform part of the per-token compute path, while storage planning requires the actual placement and offload policy. State those policies before estimating per-device requirements. Neither total parameters as all per-token computation nor activated parameters as all system storage is appropriate; the counts answer different questions.

**中文：** 练习：混合专家每词元只激活少量参数，能否只按该部分估算驻留权重？参考答案：通常不能，其他词元可能选择不同专家，部署必须保留或取得更大权重集合，共享层、路由和通信还会增加成本。激活参数反映单词元部分计算路径，存储规划则需要真实放置与卸载政策。估算每设备需求之前，应先说明这些政策。既不能把全部参数当成每词元全部计算，也不能把每词元激活量当成整系统全部存储，两种数字分别回答不同问题。

### Exercise 3: A hidden dtype coupling / 习题三：隐藏的精度耦合

**English:** Exercise: A calculator quarters both weights and KV bytes when weight precision changes from sixteen to four bits. What is wrong? Reference answer: it assumes a coupling that was never specified. Weight quantization and KV representation are independent, so only the weight term should change unless a separate cache change is declared. Add a test that compares KV output before and after changing weight bits. Also retain quantization metadata, because the resulting total is not exactly one quarter of the original model budget. Trace which tensor category each precision parameter controls instead of tuning one global multiplier until example numbers look reasonable.

**中文：** 练习：计算器把权重从十六位改成四位时，同时把权重和键值字节都除以四，错在哪里？参考答案：它假定了未经说明的耦合。权重量化与缓存表示独立，除非另外声明缓存变化，否则只能改变权重项。应增加测试，比较修改权重位数前后缓存输出相同；量化元数据也必须保留，因为最终总预算并不恰好变成原来的四分之一。修复公式时需要追踪每个精度参数作用于哪类张量，不能只调整一个全局乘数让示例数字看起来合理。

### Exercise 4: Batch and context / 习题四：批次与上下文

**English:** Exercise: In the independent full-history model, batch doubles and stored context triples. Which term grows sixfold? Reference answer: KV payload grows sixfold when layers, KV heads, head dimension, and bytes per value stay fixed. Shared model weights do not grow with this request batch in the same way. Temporary workspaces may follow different relationships and remain outside the simple formula. Explain the assumption of independent state; prefix sharing or sliding windows can change the relation and require a new model. Proportional reasoning requires explicit fixed terms and assumptions; a local linear relationship does not automatically describe the whole system.

**中文：** 练习：在独立完整历史模型中，批次翻倍、已存上下文变成三倍，哪项扩大六倍？参考答案：当层数、键值头、头维度和每值字节不变时，键值负载扩大六倍；同一模型共享权重不会按这种方式随请求批次增长。临时工作空间可能遵循其他关系，仍在简单公式之外。回答还应说明状态相互独立这一假设，因为前缀共享或滑动窗口会改变关系，需要新的模型。比例推理只有在固定项和假设明确时成立，否则容易把局部线性关系误推广到整个系统。

### Exercise 5: Positive margin / 习题五：正余量

**English:** Exercise: The estimator reports several GiB of positive margin. Has deployment feasibility been proved? Reference answer: no. The result depends on the assumed reserve and omits backend-specific allocations and startup peaks. It establishes only that the modeled scenario fits its supplied arithmetic budget. The next evidence should include actual loading, generation, and workload-dependent memory observation on the intended device. Do not replace those checks with a larger arbitrary reserve and call the result a measured guarantee. Conservative assumptions can screen candidates, but validation requires observing the declared environment and workload.

**中文：** 练习：估算器报告剩余几个二进制吉字节，是否已经证明部署可行？参考答案：没有，结果依赖假设预留，也遗漏后端特定分配和启动峰值，只能证明这组建模场景没有超过输入算术预算。下一步证据应包括目标设备真实加载、生成和负载相关内存观测。不能把预留随意加大，再把结果称为经过测量的保证。保守假设可以帮助筛选，但仍然是假设；它与验证的区别在于是否实际观察过所声明环境和工作负载下的行为。

### Exercise 6: Mixed precision / 习题六：混合精度

**English:** Exercise: A checkpoint uses low-bit experts but higher-precision attention and shared components. Why is total parameters times half a byte insufficient? Reference answer: it assigns the expert representation to every tensor and omits scale metadata and padding. Partition the inventory by storage format, compute each payload, then add metadata and runtime terms. The precision of a dominant component can describe the artifact informally without specifying every byte. A deployment estimator needs the component breakdown, not just the label on the model page. This also explains why two checkpoints both labeled four-bit can have different file sizes and runtime requirements.

**中文：** 练习：检查点专家采用低位，注意力和共享组件采用更高精度，为什么总参数乘半字节不够？参考答案：它把专家表示应用到所有张量，并遗漏比例元数据和补齐。应按存储格式划分清单，分别计算负载，再加元数据和运行项。占主导组件的精度可以用于非正式描述产物，却没有规定每个字节。部署估算需要组件拆分，而不是模型页面上的单一标签。理解这种差异，也能解释为什么两个都标四位的检查点，实际文件大小和运行资源仍可能不同。

### Exercise 7: Architecture rejection / 习题七：拒绝错误架构

**English:** Exercise: Why does the script raise an error when `model_type` changes to a V4 identifier instead of attempting a best-effort estimate? Reference answer: the formula's storage assumptions no longer match the model. Returning a precise-looking number would conceal an unsupported inference. The correct extension starts by identifying V4's actual persistent states and backend layout, then adding a separate estimator with tests. Explicit refusal is useful behavior when the alternative is silently applying the wrong architectural model. A reliable tool must recognize and communicate unsupported inputs, not merely answer as many inputs as possible.

**中文：** 练习：模型类型改成第四代标识时，脚本为什么报错，而不是尽量给一个估算？参考答案：公式存储假设已经不再匹配模型，返回看似精确数字会隐藏未经支持的推断。正确扩展应先识别第四代实际持久状态与后端布局，再建立独立估算器和测试。如果另一种选择是静默套用错误架构，那么明确拒绝就是有价值的行为。工具可靠性不只体现在能回答多少输入，也体现在知道哪些输入超出能力，并把该边界清楚地传达给调用方。

### Exercise 8: Configuration gates / 习题八：配置开关

**English:** Exercise: A config contains a window size of 4096 but disables sliding-window attention. Should cache size be capped at 4096 tokens? Reference answer: not on that evidence. The field is inactive under the stated configuration, so the full-history assumption remains relevant. Interpret the enable flag and implementation together. If the feature is later enabled, the current calculator intentionally refuses it; adding a cap without checking which layers use which attention pattern would be an unverified shortcut. Configuration fields jointly select an execution path; estimates must follow enabled behavior rather than isolated numeric values.

**中文：** 练习：配置含四千零九十六窗口大小，却关闭滑动窗口注意力，是否应该把缓存上限设为这个数？参考答案：不能据此决定，该字段在当前配置中未启用，完整历史假设仍然相关。应同时解释开关与实现。如果以后启用该功能，当前计算器有意拒绝；不检查哪些层采用哪种注意力就直接加上截断，是未经验证的捷径。配置不是孤立数字的集合，而是共同选择执行路径的约束，估算必须忠实于真正启用的行为。

### Exercise 9: Latest versus suitable / 习题九：最新与适合

**English:** Exercise: Does verifying a newer official DeepSeek model mean the teaching experiment should immediately replace its small student checkpoint? Reference answer: no. Currency matters for describing the ecosystem, while experiment choice depends on the learning objective and available evidence. The small dense checkpoint supports transparent arithmetic and a manageable serving study. A newer multimodal MoE requires different state accounting and backend validation. Keep the ecosystem description current without pretending the small-model results characterize the newer system. Choosing an older teaching model is reasonable when the rationale is explicit and it is not presented as the current full architecture.

**中文：** 练习：确认官方存在更新模型，是否意味着教学实验必须立即替换小型学生检查点？参考答案：不是，描述生态需要保持时效，选择实验则取决于学习目标和现有证据。小型稠密检查点支持透明算术和可管理的服务研究；更新的多模态混合专家需要不同状态核算与后端验证。应让生态介绍保持最新，同时不假装小模型结果能够刻画新系统。主动选择旧教学模型并没有问题，问题在于不说明选择理由，或者让读者误以为它代表当前完整架构。

### Exercise 10: A deployment decision / 习题十：部署决策

**English:** Exercise: A candidate fits the estimated memory budget but fails the task-quality threshold at the required output limit. What should the decision record say? Reference answer: it fails the current acceptance criteria despite promising capacity. Explore a changed output budget, another model, or another deployment mode, then re-evaluate quality and serving behavior together. Do not declare success by removing the difficult test cases. Resource feasibility is one constraint among several; a useful model service must satisfy the actual task as well as its operational limits. Recording the failure guides subsequent selection and prevents a capacity table from being mistaken for completed acceptance.

**中文：** 练习：候选模型符合估算内存预算，却在规定输出限制下达不到任务质量门槛，决策记录应怎么写？参考答案：即使容量看起来可行，它仍未满足当前验收条件。可以探索不同输出预算、另一个模型或另一种部署方式，再把质量与服务行为一起评价，不能删掉困难测试后宣称成功。资源可行只是多个约束之一，有用模型服务必须同时满足真实任务和运维限制。记录失败原因能够指导下一步选择，也防止之后只看到容量表便误认为该候选已经完成验收。

## Acceptance and next steps / 验收与下一步

**English:** Accept the CPU exercise when you can fetch the pinned config, reproduce its checksum, pass eight tests, derive the parameter and KV counts independently, and explain every assumption in the scenario margin. You should also be able to predict the direction and factor of changes when batch, context, weight bits, and KV bytes vary independently. The formulas must reject architectures outside their declared scope. Keep the config, script version, interpreter version, commands, and JSON reports together; those are the complete artifacts of this resource-analysis experiment. Acceptance means deriving a quantity again from its inputs and explaining what cannot be inferred from it, rather than memorizing a memory number.

**中文：** 处理器实验验收要求包括获取固定配置、复现校验值、通过八个测试、独立推导参数与键值计数，并解释场景余量中的全部假设。还应能够预测批次、上下文、权重位数和键值字节独立变化时，结果的方向与比例。公式必须拒绝超出声明范围的架构。把配置、脚本版本、解释器版本、命令和报告一起保留，它们共同构成这次资源分析实验的完整产物。验收不是背出一个显存数字，而是可以从输入重新推导它，并明确哪些结论不能从该数字推出。

**English:** The next GPU step is to compare the estimate with a real lifecycle trace on a healthy device: loading, idle readiness, short generation, longer context, and controlled concurrency. Attribute discrepancies to concrete categories rather than tuning the reserve until the prediction happens to match. For full DeepSeek architectures, begin a separate implementation-aware study of persistent state, mixed precision, expert placement, and supported kernels. The enduring skill is constructing an auditable model of resource use and revising it when evidence reveals a missing mechanism. That model guides both deployment and the choice of layer for the next performance investigation.

**中文：** 下一步显卡实验，是在健康设备上把估算与真实生命周期记录比较，包括加载、空闲就绪、短生成、更长上下文和受控并发。差异应归入具体资源类别，而不是不断调节预留，直到预测碰巧吻合。完整 DeepSeek 架构则需要另开理解实现的研究，分析持久状态、混合精度、专家放置和受支持核函数。长期有用的能力，是建立能够审计的资源使用模型，并在证据揭示遗漏机制时修正它。这样的模型既帮助部署，也帮助判断下一项性能调查应该从哪一层开始。

## Official references / 官方参考资料

**English:** These primary sources were checked on 2026-09-18. Newer model cards establish current architecture claims; the fixed student configuration and versioned Qwen implementation establish the assumptions used by the CPU experiment. None of these references substitutes for a local GPU measurement.

**中文：** 以下一手来源于二〇二六年九月十八日核验。新模型说明用于确认当前架构陈述，固定学生配置与版本化参考实现用于建立处理器实验假设，任何引用都不能代替本地显卡测量。

- [DeepSeek-V4.1-Flash official card / 最新核验模型官方说明](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
- [DeepSeek-V4.1-Flash repository metadata / 官方仓库元数据](https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4.1-Flash)
- [DeepSeek-V4-Flash official card / 第四代快速版官方说明](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)
- [DeepSeek-V4-Pro-0813 official card / 第四代专业版更新说明](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813)
- [DeepSeek-R1 report / 第一代推理模型研究报告](https://arxiv.org/abs/2501.12948)
- [DeepSeek-V3 technical report / 第三代技术报告](https://arxiv.org/abs/2412.19437)
- [Pinned student configuration / 固定学生模型配置](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B/blob/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562/config.json)
- [Student tensor metadata / 学生模型张量元数据](https://huggingface.co/api/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B)
- [Versioned Qwen2 implementation / 版本化参考实现](https://github.com/huggingface/transformers/blob/v4.48.2/src/transformers/models/qwen2/modeling_qwen2.py)
- [SGLang V4 deployment cookbook / 第四代部署指南](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4)
