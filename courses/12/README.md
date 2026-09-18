# Reproducible Benchmarks and Integrated Engineering / 可复现基准与综合工程

## 1. Turn a Result into Evidence / 让结果成为证据

**English:** A benchmark is a controlled observation of a specified system under a specified workload. It is not merely a loop with a timer. This course integrates the repository's kernels, framework examples, model deployment, service measurements, configurations, and reports. The objective is to produce a claim that another engineer can check: what changed, what stayed comparable, how correctness was established, which observations support the explanation, and where the conclusion stops being applicable. An attractive number is a clue; documenting how it was produced turns it into evidence for a decision.

**中文：** 基准是在明确负载下，对明确系统进行的受控观察，并不只是一个带计时器的循环。本课串联仓库中的 kernel、框架示例、模型部署、服务度量、配置与报告，目标是产生其他工程师能够检查的结论：改变了什么，哪些条件保持可比，如何建立正确性，哪些观察支持解释，以及结论在哪些边界外不再适用。一个漂亮数字可以作为线索，但只有把产生数字的过程说明清楚，它才有机会成为支持工程决策的证据。

**English:** Courses 02, 06, 10, and 11 provide the practical prerequisites. Read the measurement principles here before running your first experiment, then complete the integrated exercise after the serving path is understood. The final artifact is a reproducible report with preserved inputs and raw observations. A report showing no improvement can satisfy the learning goal when it correctly rejects a hypothesis. Fabricated speedups, unexplained dropped requests, and a single best run cannot satisfy it. Record unsuccessful attempts and the reason for the next investigation as well as the favorable results retained in the final design.

**中文：** 课程 02、06、10 和 11 提供实践前置知识。第一次实验以前就可以阅读本课的度量原则，在理解推理服务路径以后再完成综合练习。最终成果是一份保留输入和原始观察的可复现报告。如果正确否定了一个假设，即使没有获得性能提升，也可以达到学习目标。虚构加速倍数、无法解释的丢失请求，或只挑最好一次运行，都不满足要求。复盘时应同时说明哪些尝试有效、哪些无效，以及下一步为什么值得做，而不是只记录最后保留下来的有利结果。

**English:** Source verification date is 2026-09-18. The integrated service path uses the pinned SGLang setup and client in Course 10. The current native benchmark implementation lives under `sglang.benchmark.serving`; the older `sglang.bench_serving` entry point is retained as a compatibility wrapper in the checked release. Verify commands against that release rather than assuming that every historical tutorial uses the current module layout. The analysis lab below uses only Python's standard library and runs without a GPU. This separation lets you validate statistics before collecting real service data, keeping environment failures distinct from analysis errors.

**中文：** 资料核验日期为 2026-09-18。综合服务路径采用课程 10 固定的 SGLang 设置与客户端。所核查版本的原生基准实现位于 `sglang.benchmark.serving`，旧的 `sglang.bench_serving` 入口保留为兼容包装。因此应针对所使用发布版本检查命令，不能假定所有历史教程都采用当前模块布局。下文分析实验只使用 Python 标准库，不依赖 GPU。这种分层允许先验证统计与数据处理，再在环境具备时采集真实服务数据，避免把环境失败与分析逻辑错误混在一起。

## 2. Define the Question and the Boundary / 定义问题与测量边界

**English:** Begin with a falsifiable question. For example: under one fixed prompt distribution and concurrency, does enabling prefix reuse reduce client-observed first-response latency without increasing the failure fraction? This is more precise than asking whether a runtime is fast. Specify the independent variable, dependent measurements, workload, and important fixed conditions. Also write down an observation that would disprove the proposed explanation, such as cache reuse counters staying zero despite a reported latency change. Defining counterevidence in advance reduces retrospective selection of explanations and encourages testing what could prove your hypothesis wrong.

**中文：** 从可被否定的问题开始。例如：在固定提示分布与并发度下，启用前缀复用是否能够降低客户端观察到的首次响应延迟，同时不增加失败比例？这比询问某个运行时“快不快”更精确。应明确自变量、观测量、负载和重要固定条件，还要写出什么观察会推翻当前解释，例如报告延迟变化时缓存复用计数却始终为零。提前定义反证可以减少事后选择解释的倾向，使你愿意检查真正可能证明自己判断错误的证据。

**English:** Distinguish kernel, operator, model step, and service boundaries. A kernel duration may exclude allocation, host submission, tokenization, network transfer, and queueing. A service request includes some or all of those stages depending on where the client starts its clock. Improvements at one boundary are not automatically additive at another. If the optimized component occupies a small fraction of total latency, a large local speedup can have only a modest end-to-end effect even before other bottlenecks shift. Report local and overall observations separately, then explain their relationship rather than labeling a kernel speedup as a service speedup.

**中文：** 应区分 kernel、算子、模型步骤和服务边界。kernel 时间可能排除分配、主机提交、分词、网络传输和排队；服务请求包含其中哪些阶段，则取决于客户端从哪里开始计时。一个边界上的改进不能自动累加到另一个边界。如果被优化组件只占总延迟很小比例，那么即使局部加速很大，端到端效果也可能有限，更不用说优化后其他瓶颈还会改变。报告中应把局部观察与整体观察分开列出，再说明它们之间的关系，而不是直接把 kernel 加速倍数写成服务加速倍数。

**English:** A comparison needs equivalent work, not just equivalent command names. Changing output-token count, early-stop behavior, dtype, quantization, batch size, or cache state can change the problem being measured. Sometimes those changes are the intended optimization, but then the quality and resource tradeoffs must be part of the evaluation. If one implementation emits fewer tokens because it stops early, its shorter duration is not evidence of higher decoding throughput for the original fixed-length workload. Identify the fields that define work and verify actual outputs against them instead of trusting request parameters alone.

**中文：** 比较需要等价工作，而不只是命令名称相同。输出 token 数、提前停止行为、类型、量化方式、批次大小或缓存状态变化，都可能改变被测问题。有时这些变化本来就是优化目标，但必须将质量和资源取舍纳入评估。如果某个实现因为提前停止而少生成 token，那么更短时间不能证明它在原来固定长度负载下具有更高解码吞吐。设计实验时，应列出工作量由哪些字段决定，并检查实际输出是否满足这些字段，而不是只相信发给服务端的请求参数。

**English:** Correctness is a gate before performance interpretation. A kernel must satisfy its numerical and boundary contract; a model service must complete the intended protocol and output requirements. A response with status 200 can still be truncated, malformed, or based on an unexpected model. Preserve finish reasons, token counts, and raw responses when relevant. A fast run with more errors should be evaluated as a different reliability outcome, not silently filtered into an attractive latency table. Preserved failures can reveal behavior near capacity more clearly than additional successful samples.

**中文：** 正确性是解释性能之前的门槛。kernel 必须满足数值与边界契约，模型服务必须完成预期协议和输出要求。HTTP 状态为 200 的响应，仍可能被截断、格式错误，或者来自意外的模型。应在适用时保留结束原因、token 数和原始响应。一次更快但错误更多的运行，应作为不同可靠性结果评估，不能悄悄过滤成好看的延迟表。把失败记录保留下来，往往比继续增加成功样本更能揭示系统在容量边缘的真实行为。

**English:** Choose the unit of work before choosing throughput. Requests per second is meaningful only alongside a request distribution. Output tokens per second needs a definition of which tokens count and which time interval is used. Bytes per second for a transpose needs a stated read/write traffic model, and it may represent effective bandwidth rather than measured physical DRAM traffic. A metric name without numerator and denominator definitions is incomplete, even if the reported number has many decimal places. Precision comes from definitions and suitable instruments, not display formatting; readers should be able to recompute the result.

**中文：** 先选择工作单位，再选择吞吐指标。每秒请求数只有结合请求分布才有意义；每秒输出 token 数需要说明计算哪些 token，以及采用什么时间区间；转置的每秒字节数需要给出读写流量模型，而且可能只是有效带宽，不是真实测得的物理 DRAM 流量。即使数字保留了很多小数位，缺少分子与分母定义的指标仍然不完整。度量精度来自清楚的定义和适当的仪器，不来自显示格式；报告应优先让读者能够重算结果。

## 3. Preserve the Experimental Identity / 保留实验身份

**English:** A run identity should connect source revision, dependency versions, model revision, hardware, launch command, and workload to the resulting observations. A model name alone is insufficient when its repository can change. Record immutable revisions when available and preserve tokenizer and configuration identities as well as weight identity. A configuration file is useful only when the program actually consumed it; keep the effective command and relevant resolved settings, not just a planned configuration that may have been overridden. That record lets others distinguish changes in code, dependencies, models, and runtime settings.

**中文：** 一次运行的身份应把源代码修订、依赖版本、模型修订、硬件、启动命令和负载与产生的观察连接起来。当模型仓库可能变化时，只记录模型名称不够。条件允许时应记录不可变修订，并同时保留分词器、配置和权重身份。配置文件只有在程序真实使用它时才有意义；需要保留实际生效命令和解析后关键设置，而不是仅保存可能已经被其他参数覆盖的计划配置。这样，其他人才能判断差异来自代码、依赖、模型还是运行参数。

**English:** Store raw observations before derived summaries. A per-request record can preserve success, timing, token counts, condition labels, and errors; a run-level record can preserve wall-clock duration and environment. Derived percentiles can then be recomputed with a different clearly stated convention. If only the final average remains, investigating truncation, mixed workloads, or failed requests becomes impossible. Data reduction should be a reproducible transformation, not an irreversible manual copy into a spreadsheet. For overlapping requests, retaining both levels avoids later attempts to infer unrecorded facts from an incomplete summary.

**中文：** 应先保存原始观察，再生成汇总。逐请求记录可以保存成功状态、计时、token 数、条件标签和错误；运行级记录保存墙钟区间与环境。之后可以根据另一种清楚定义的分位数规则重新计算。如果只留下最终平均值，就无法调查截断、混合负载或失败请求。数据缩减应是一项可复现转换，而不是不可逆的人工复制到表格。特别是并发请求存在重叠时，保留运行区间和逐请求数据，可以避免后来被迫从不完整摘要反推出本来没有记录的事实。

**English:** Hashes help detect accidental input changes but do not establish semantic equivalence or measurement truth. Two files with different formatting may describe equivalent prompts, while two identical prompt strings can tokenize differently under different tokenizer versions. Define what is hashed: raw bytes, normalized request objects, or token sequences. Preserve the transformation that produced the hashed representation. A hash of a fabricated report faithfully identifies that fabricated report; it does not certify the existence of the claimed GPU run. File integrity, reproducibility, and truthful measurement are therefore related but distinct evidence properties.

**中文：** 哈希有助于发现输入意外变化，却不能建立语义等价或测量真实性。格式不同的文件可能描述相同提示，而相同提示字符串在不同分词器版本下也可能产生不同 token。必须定义哈希对象是原始字节、规范化请求对象还是 token 序列，并保留生成被哈希表示的转换过程。对虚构报告计算出的哈希，只是忠实标识了这份虚构报告，不能证明声称的 GPU 运行真实发生。因此，文件完整性、实验可复现性和结果真实性属于相关但不同的证据层次。

**English:** Keep measured, derived, synthetic, and unverified data distinguishable. A protocol fixture is valuable for testing a client parser; it is not a model-serving measurement. A memory formula estimates a budget; it is not an observed peak allocation. A result from an HTTP endpoint may remain unverified with respect to backend model and hardware until correlated with server evidence. Analysis software should preserve these labels rather than automatically upgrading evidence because the input has valid JSON and plausible numbers. The analyzer below preserves those categories even when the arithmetic is fully valid.

**中文：** 必须区分实测、推导、合成和未核实数据。协议夹具可以有效测试客户端解析器，但不是模型服务测量；内存公式估算预算，却不是观察到的峰值分配；HTTP 端点返回的数据，在与服务器证据关联以前，其后端模型和硬件仍可能未核实。分析软件应保留这些标签，而不是因为输入 JSON 合法、数字看起来合理就自动提升证据等级。本课分析器将原样保留证据类别，这样即使统计计算完全正确，也不会把 CPU 合成测试包装成 GPU 性能成果。

**English:** Organize results so that rerunning does not destroy the evidence being compared. Use a unique run directory or fail if an output already exists. Store a small manifest, raw data, analysis command, and report together; large profiler traces can live outside Git with a recorded location and digest. Keep model weights out of the repository as required by its existing model policy. Reproducibility depends on finding the artifacts and understanding their origin, not on committing every large binary. Clear directories and run identities also reduce accidental mixing of different conditions in one chart.

**中文：** 结果组织应避免重新运行时破坏正在比较的证据。可以为每次运行使用唯一目录，或者在输出已经存在时拒绝覆盖。把小型清单、原始数据、分析命令和报告放在一起；较大的性能轨迹可以保存在 Git 外，并记录位置与摘要。按照仓库既有模型策略，模型权重不放进仓库。可复现性依赖能够找到产物并理解来源，而不是把每个大型二进制都提交进去。清晰的目录和不可混淆的运行身份，也能减少人工把不同条件下的数据误拼在同一张图里的机会。

## 4. Latency, Throughput, and Successful Work / 延迟、吞吐与有效工作

**English:** End-to-end latency needs an explicit start point. The clock may start before admission, after acquiring a client concurrency slot, or after preparing input tokens. Each choice answers a different question. Course 10's token-ID workload deliberately bypasses server-side text tokenization, so it cannot diagnose that stage's throughput. Record that boundary in the report. If the production path accepts text, add a separate text-input experiment rather than silently treating token-ID and text requests as interchangeable observations. The stated start point tells readers whether preparation, client waiting, and server preprocessing are included.

**中文：** 端到端延迟必须有明确起点。计时可以从准入以前、取得客户端并发槽之后，或准备完输入 token 之后开始，每种选择回答不同问题。课程 10 的 token ID 负载有意绕过服务端文本分词，因此不能用来诊断该阶段吞吐，报告中应记录这项边界。如果生产路径接收文本，就另做文本输入实验，而不是悄悄把 token ID 请求与文本请求当作可互换观察。只有把开始位置讲清楚，读者才知道一条延迟数字是否包含输入准备、客户端等待和服务端预处理。

**English:** Client-observed time to first token is affected by transport and streaming behavior as well as model computation. A server can buffer multiple tokens before emitting one event, or emit an event containing metadata without new text. Count the first qualifying output event using an explicit rule. When the available data only establishes time to first received output chunk, call it an observed proxy rather than claiming a device-level first-token timestamp. The difference matters when comparing different servers or transport settings. Buffering changes can alter the client observation while model execution stays unchanged.

**中文：** 客户端观察到的首 token 时间不仅受模型计算影响，也受传输和流式输出行为影响。服务器可能积攒多个 token 才发出一个事件，也可能先发出只有元数据、没有新增文本的事件。应明确什么样的输出事件满足首次响应条件。如果现有数据只能建立首次收到输出块的时间，就把它称为观察代理量，而不是声称得到设备层面的首 token 时间。比较不同服务器或传输设置时，这个区别尤其重要，因为缓冲策略变化本身就能改变客户端观察，而模型执行未必改变。

**English:** Average time per output token after the first is often computed from a suitable decoding interval divided by the number of subsequent tokens. It is undefined for a request with fewer than two relevant tokens. If events coalesce several tokens, event-to-event time is not automatically token-to-token time. Preserve null for unobservable values and report the eligible sample count. Replacing missing values with zero artificially improves the average and makes a less observable system appear faster. Missing data needs an explanation, not an invented value that makes a table look complete.

**中文：** 首 token 之后的平均每输出 token 时间，通常以合适的解码时间区间除以后续 token 数计算。对于不足两个相关 token 的请求，这个量没有定义。如果一个事件合并了多个 token，事件间时间也不会自动等于 token 间时间。应对无法观察的值保留空值，并报告符合统计条件的样本数量。把缺失值替换成零，会人为改善平均值，让观测能力较弱的系统看起来更快。缺失数据是一种需要解释的事实，不能为了让表格完整就给它编造一个数值。

**English:** Aggregate throughput divides completed work by one shared wall-clock interval. Summing each request's tokens-per-second rate double-counts overlapping time in a concurrent workload. Keep failures and client overhead within the chosen run interval even when the token numerator counts only successful completions. If tokens emitted by failed requests are counted for a separate hardware-work metric, label that different numerator. User-visible successful output and all backend computation are related, but they are not the same measure. Do not switch the metric definition simply because one result looks more favorable.

**中文：** 聚合吞吐应将完成工作量除以一个共享墙钟区间。把每条请求自己的每秒 token 率相加，会在并发负载中重复计算重叠时间。即使 token 分子只包含成功完成的请求，所选运行区间也应按定义保留失败和客户端开销。如果要把失败请求已产生的 token 计入另一项硬件工作指标，就明确标出这个不同分子。用户实际收到的成功输出与后端全部计算彼此相关，却不是同一个度量，不能根据哪一种数字更好看就临时替换口径。

**English:** A service-level objective can combine correctness and latency. For a teaching example, count a request as good only if it succeeds and meets both a first-response limit and an end-to-end limit. Divide good requests by all recorded attempts for an attainment fraction, or by the run duration for a good-request rate. The example thresholds are not production recommendations. A fast successful subset should not hide a large timeout fraction, and rejected requests must be accounted for at a stated admission boundary. If rejected attempts were never recorded, declare that gap instead of calling admitted requests all arrivals.

**中文：** 服务目标可以同时约束正确性和延迟。教学示例中，只有请求成功且同时满足首次响应和端到端时间限制，才算达标请求；用达标数除以所有记录尝试得到达标比例，除以运行时间则得到达标请求率。示例阈值不是生产建议。成功子集速度很快，不能掩盖大量超时；拒绝请求也必须在明确准入边界统计。如果客户端根本没有记录被拒绝的尝试，就应说明数据缺口，不能把仅包含成功进入服务的记录称为所有到达请求。

**English:** Use monotonic clocks for elapsed intervals and avoid subtracting timestamps from unrelated clock domains. Client and server wall clocks may differ, and a CUDA event duration is not directly a client timestamp. Correlate stages through identifiers and an appropriate tracing tool, acknowledging synchronization accuracy where needed. A negative inferred queue delay is often evidence of incompatible clocks or boundaries, not a remarkable scheduling optimization. Preserve local durations when cross-machine alignment is uncertain. Local durations also make later calibration easier than an unjustified complete-looking decomposition.

**中文：** 经过时间应使用单调时钟，并避免直接相减不同时间域的时间戳。客户端与服务器墙钟可能不同，CUDA 事件时长也不是可以直接与客户端相减的时间戳。应通过标识符和适当追踪工具关联阶段，必要时说明时钟同步精度。推导出的负排队时间往往说明时钟或边界不兼容，而不是调度优化创造了奇迹。跨机器对齐存在不确定性时，保留各自本地时长，比强行拼成看似完整的端到端分解更可靠，也更方便以后补充校准证据。

## 5. Statistics without False Precision / 避免虚假精度的统计

**English:** Mean and median answer different questions. The mean reflects the total sum spread across observations and is sensitive to long delays; the median describes the midpoint of the empirical sample. Neither summarizes the whole distribution. Report sample count, failure count, and selected tail information alongside a central statistic. If two workloads have different lengths, stratify them or preserve a fixed mixture rather than averaging away a shift in which requests were served. A better aggregate mean may only reflect more easy, short requests, with no improvement for any fixed request class.

**中文：** 均值和中位数回答不同问题。均值将总和分摊到观察值，对较长延迟敏感；中位数描述经验样本的中间位置。两者都不能概括完整分布。报告中心统计量时，还应提供样本数量、失败数量和选定尾部信息。如果两组负载长度不同，就分层比较或保持固定混合比例，而不是用平均操作掩盖服务请求构成的变化。一个总体平均值改善，可能只是较容易的短请求比例上升，并不表示任一固定类型的请求真正更快。

**English:** Quantiles have multiple finite-sample conventions. This course uses nearest rank: sort `n` values and take the value at one-based position `ceil(q*n)`. The choice is explicit so results can be recomputed. With two values, the 95th percentile under this convention is the maximum; this does not establish a stable population tail estimate. State the algorithm and sample count, and avoid comparing a nearest-rank number with an interpolated number as if only the system had changed. The statistical method is part of the experiment configuration; recompute old data when changing it.

**中文：** 有限样本分位数存在多种约定。本课采用最近秩方法：把 n 个值排序，取从一开始计数的 `ceil(q*n)` 位置。明确方法是为了让结果可以重算。只有两个样本时，这种规则下的第九十五百分位就是最大值，并不能建立稳定的总体尾部估计。应说明算法和样本数，不要把最近秩结果与插值结果直接比较，再假装唯一变化来自被测系统。统计实现属于实验配置的一部分，变更统计方法时应同时重算旧数据。

**English:** Percentiles generally cannot be averaged across runs or hosts to recover the percentile of their combined requests. Preserve raw samples or use a suitable mergeable distribution representation with known approximation behavior. Averages of per-run medians can still be reported as that specific statistic, but must not be relabeled as the median of all requests. The aggregation level matters because a run with few observations and a run with many observations should not acquire accidental equal weight in a request-level claim. Readers need to know whether a plotted point represents a request, a run, or a machine.

**中文：** 通常不能把不同运行或不同主机的分位数取平均，就恢复合并请求的分位数。应保留原始样本，或者使用具有已知近似性质、可以合并的分布表示。可以报告各运行中位数的平均，但必须如实命名，不能改称全部请求的中位数。汇总层级很重要，因为观察很少的一次运行与观察很多的一次运行，不应该在关于逐请求总体的结论里意外获得相同权重。读者需要知道每个点代表请求、一次运行还是一台机器。

**English:** Repeat whole runs, not just inner-loop iterations. Repetition within one warm process may hide startup variability, allocator history, or a persistent cache state. Independent runs can reveal those effects, although they are not perfectly independent when they share hardware and background load. Alternate or randomize A/B order when feasible, and retain every planned run. Removing an outlier requires an explained measurement defect or a predefined rule, not discomfort with the resulting speedup. Let readers see variability rather than a selected impression of stability.

**中文：** 应重复整次运行，而不只是重复内层循环。在同一个热态进程里反复执行，可能隐藏启动差异、分配器历史或持续缓存状态。独立运行有助于观察这些影响，但共享硬件和后台负载意味着它们也不一定完全独立。条件允许时，交替或随机安排 A/B 顺序，并保留所有计划运行。删除离群值必须有可解释的测量缺陷或预先定义的规则，不能因为某个数值让加速比例难看就删掉。报告应允许读者看到波动，而不是只看到经过选择的稳定印象。

**English:** Confidence intervals require assumptions and a clearly defined target statistic. They are not made valid merely by calling a bootstrap function. Correlated requests within a run can make request-level resampling overconfident; resampling run-level summaries answers a different question. For this introductory course, show repeated-run values and variability before adding inferential claims. When uncertainty is large relative to the proposed improvement, report that the evidence is inconclusive rather than forcing a winner. Recognizing an inconclusive comparison can avoid maintenance costs for unstable or nonexistent gains.

**中文：** 置信区间需要假设和明确目标统计量，并不会因为调用一个 bootstrap 函数就自动有效。同次运行内的相关请求，可能让逐请求重采样过于自信；对运行级汇总重采样则回答另一个问题。本入门课程要求先展示重复运行值与波动，再增加推断性结论。当不确定性相对于拟议改善很大时，应报告证据不足，而不是勉强选出赢家。能够承认当前实验无法区分两个方案，也是重要工程能力，因为它可以避免为不稳定甚至不存在的收益承担维护成本。

## 6. Workload, Load Generation, and Controls / 负载、压测与控制变量

**English:** A closed-loop client starts new work as earlier requests finish, often maintaining a fixed concurrency. When the server slows, the offered arrival rate can fall. An open-loop experiment schedules arrivals independently and can reveal queue growth under a fixed arrival process. Neither mode is universally superior; choose the one matching the question. Record scheduled and actual dispatch times if client saturation can delay arrivals, otherwise the load generator may hide the overload it was supposed to test. Fixed concurrency and fixed request rate are different conditions even when both tools report requests per second.

**中文：** 闭环客户端通常在旧请求完成后发起新工作，维持固定并发；服务器变慢时，提供的到达率可能随之下降。开环实验独立安排到达，可以观察固定到达过程下队列增长。两者没有普遍优劣，选择应与问题匹配。如果客户端饱和可能推迟发送，就记录计划和实际发送时间，否则负载生成器可能把原本要测试的过载隐藏起来。固定并发与固定请求率不是同一个条件，不能只因为二者都能产生每秒请求数，就把结果视为可直接替代。

**English:** Coordinated omission occurs when the measurement process omits delays that would have been observed under the intended arrival pattern, for example because a blocked generator stops issuing work during a stall. A concurrency-limited test can still be valid for a closed-loop user model, but it should not be presented as a fixed-rate capacity test. Check the generator's CPU, connection limits, parsing work, and scheduling delays. A quiet GPU may reflect a slow client rather than spare server capacity. [wrk2 measurement discussion](https://github.com/giltene/wrk2). Assess a tool through its arrival schedule and time recording, not merely its ability to send many requests.

**中文：** 协调遗漏指测量过程遗漏了目标到达模式下本应观察到的等待，例如生成器在一次停顿期间也停止产生新工作。限制并发的测试对于闭环用户模型仍然可以有效，但不能把它包装成固定到达率容量测试。应检查生成器 CPU、连接限制、解析工作与调度延迟。GPU 看起来空闲，可能反映客户端太慢，而不一定说明服务器仍有大量容量。[wrk2 的度量讨论](https://github.com/giltene/wrk2)。判断工具是否适用，应从它怎样安排请求和记录时间开始，而不是只看它能否发送很多请求。

**English:** Cache state is a treatment variable when the hypothesis concerns reuse. Separate cold start, intentionally warmed shared prefixes, and unique prompts. Reset or isolate state according to a documented procedure, and verify that the intended reuse actually occurred. Turning off cross-request prefix caching does not remove the within-request KV state needed for autoregressive decoding. A cache comparison that accidentally changes prompt lengths or token identities can no longer isolate reuse as the cause. An A/B design controls possible explanations; changing a switch and observing any changed number is insufficient.

**中文：** 假设涉及复用时，缓存状态本身就是处理变量。应区分冷启动、有意预热的共享前缀和独特提示；按记录的流程重置或隔离状态，并验证预期复用确实发生。关闭跨请求前缀缓存，不等于移除自回归解码所需的请求内部 KV 状态。如果缓存比较同时意外改变提示长度或 token 身份，就不能再把复用单独视为原因。A/B 设计的价值在于控制解释空间，而不是简单把一个开关改为开或关，然后观察任意一个数字有没有变化。

**English:** Hardware state and competing work can affect results. Record the GPU model, memory capacity, driver, power or clock constraints when relevant, and whether other processes share the device. Observe thermal or utilization changes rather than silently changing system-wide settings. The current authoring machine's driver/NVML mismatch is a preflight failure, so it cannot supply valid GPU benchmark results. Fixing that environment is a separate operational task; synthetic client tests remain useful but must keep their own evidence label. When the environment is unavailable, preserve the conclusion boundary instead of substituting output that merely resembles a measurement.

**中文：** 硬件状态与竞争工作会影响结果。应记录 GPU 型号、显存容量、驱动、适用时的功耗或时钟约束，以及是否有其他进程共享设备。观察温度或利用率变化，而不是悄悄修改系统全局设置。当前编写机器的驱动与 NVML 不匹配，属于预检查失败，无法提供有效 GPU 基准结果。修复环境是一项单独运维任务；合成客户端测试仍然有用，但必须保留自己的证据标签。环境不可用时最重要的是维护结论边界，而不是寻找看起来像实测数字的替代输出。

**English:** Profile selectively because instrumentation can perturb the workload. Use an unprofiled benchmark for the primary performance comparison and a representative profiled run to investigate the hypothesis. Nsight Systems is useful for CPU/GPU timeline relationships, while kernel-level metrics can require a different collection tool and may replay work. Keep trace settings with the evidence. A profiled run and an unprofiled run can support each other, but their durations should not be treated as interchangeable without checking overhead. Short kernels and frequent synchronization are particularly sensitive to collection overhead changing the details under investigation.

**中文：** 性能轨迹应有选择地采集，因为插桩可能扰动负载。主要性能比较使用不带分析器的基准，再用代表性的轨迹运行调查假设。Nsight Systems 适合观察 CPU 与 GPU 时间线关系，kernel 层指标可能需要另一种采集工具，也可能重放工作。应把轨迹设置与证据一起保存。带分析器与不带分析器的运行可以相互支持，但如果没有检查额外开销，就不能把它们的时间当成可互换数据。尤其在短 kernel 或高频同步场景，采集本身可能改变原先想观察的细节。

## 7. Lab: Audit a Serving Report / 实验：审计推理服务报告

**English:** Save the following program as `analyze_report.py` in a fresh working directory. It consumes the single JSON report produced by Course 10, not the workload JSONL file. It recomputes counts and derived metrics from request rows and the recorded run duration, retaining the original report's evidence labels and a SHA-256 digest of its bytes. The digest identifies input content; it does not establish who collected it or whether its measurements are truthful. Preserve the raw report alongside the derived file so a reviewer can inspect individual failures. The offline workflow lets you check the statistics on a CPU before processing real observations.

**中文：** 在新的工作目录中，将下列程序保存为 `analyze_report.py`。它读取课程 10 生成的单个 JSON 报告，而不是负载 JSONL 文件；根据逐请求记录与整轮时长重新计算计数及派生指标，同时保留原报告的证据标签，以及输入原始字节的 SHA-256 摘要。摘要用于识别输入内容，不能证明采集者身份或测量真实性。应同时保留原始报告与派生文件，让复核者能检查每个失败请求。整个流程不需要连接模型服务，因而可以先在 CPU 上验证统计实现，再处理真实采集数据。

**English:** The accepted contract requires nonempty rows, unique integer or string request IDs, one common workload condition, explicit Boolean success, nonnegative finite durations, and positive completion counts for successful requests. Course 10 uses a condition object; the analyzer also accepts a nonempty string for small fixtures. An integer ID and its string representation are distinct IDs. Successful zero-token responses are outside this teaching contract and cause rejection rather than being silently assigned a first-token latency. Extending the contract requires a deliberate definition of that population. Do not use default zeros to hide the semantic gap; extend both the implementation and its tests when changing the population.

**中文：** 接受的数据契约要求记录非空、整数或字符串请求 ID 唯一、同一负载条件、明确的布尔成功标记、有限非负时长，以及成功请求的正数输出 token 数。课程 10 使用条件对象；分析器也接受非空字符串，方便小型测试。整数 ID 与同样数字写成的字符串视为不同身份。成功却生成零 token 的响应超出本教学契约，程序会拒绝，而不会悄悄赋予它首 token 延迟。若业务需要支持这种情况，应先定义相应统计人群，再扩展实现和测试，不应依靠缺省零值掩盖语义缺口。

**English:** The program reports successful-request latency separately from the failure fraction. SLO attainment uses every attempted request in its denominator, including failures. Unknown TPOT remains `null` and contributes neither a zero nor a guessed value to its median. The example thresholds are explicit command-line parameters, so a report can be regenerated with a different policy without changing the raw observations. They are latency gates only; a production success definition would also need the relevant semantic correctness checks. A fast wrong answer is not useful service, but quality judgments must not become an undocumented filtering step either.

**中文：** 程序分别报告成功请求的延迟分布与失败比例；SLO 达标比例的分母包含全部尝试，包括失败。未知 TPOT 保持 `null`，既不会作为零进入中位数，也不会使用猜测值。阈值通过命令行明确提供，因此可以在不改动原始观察的情况下，按不同策略重新派生报告。这里的达标门槛仅包含延迟；生产业务还应加入适用的语义正确性检查。快速返回错误答案不能构成有效服务成果，但性能实验也不应把人工质量判断偷偷混入未记录的过滤步骤。

```python
import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path


def finite_nonnegative(value, name, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name}: expected a finite number")
    if value < 0 or (positive and value == 0):
        raise ValueError(f"{name}: invalid sign")
    return value


def p95(values):
    return sorted(values)[math.ceil(0.95 * len(values)) - 1] if values else None


def median(values):
    return statistics.median(values) if values else None


def analyze(report, ttft_limit, e2e_limit):
    finite_nonnegative(ttft_limit, "TTFT limit")
    finite_nonnegative(e2e_limit, "E2E limit")
    rows = report["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a nonempty list")
    wall = finite_nonnegative(report["summary"]["wall_seconds"],
                              "wall_seconds", positive=True)
    ids, conditions, evidence = set(), set(), set()
    ttfts, e2es, tpots = [], [], []
    tokens = good = 0
    for row in rows:
        request_id = row["id"]
        if type(request_id) not in (int, str):
            raise ValueError("id must be an integer or string")
        typed_id = (type(request_id), request_id)
        if typed_id in ids:
            raise ValueError("duplicate request id")
        ids.add(typed_id)
        condition = row["condition"]
        if not isinstance(condition, (dict, str)) or not condition:
            raise ValueError("condition must be a nonempty object or string")
        conditions.add(json.dumps(condition, sort_keys=True, allow_nan=False))
        tag = row["evidence"]
        if not isinstance(tag, str) or not tag:
            raise ValueError("missing evidence label")
        evidence.add(tag)
        success = row["success"]
        if type(success) is not bool:
            raise ValueError("success must be boolean")
        e2e = finite_nonnegative(row["e2e_ms"], "e2e_ms")
        if not success:
            if not isinstance(row.get("error"), str) or not row["error"]:
                raise ValueError("failed request must preserve its error")
            continue
        ttft = finite_nonnegative(row["observed_ttft_ms"], "observed_ttft_ms")
        if ttft > e2e:
            raise ValueError("TTFT exceeds E2E")
        count = row["completion_tokens"]
        if type(count) is not int or count < 1:
            raise ValueError("successful request needs positive token count")
        tpot = row.get("observed_tpot_ms")
        if tpot is not None:
            finite_nonnegative(tpot, "observed_tpot_ms")
            if count < 2:
                raise ValueError("TPOT requires at least two output tokens")
            tpots.append(tpot)
        ttfts.append(ttft)
        e2es.append(e2e)
        tokens += count
        good += int(ttft <= ttft_limit and e2e <= e2e_limit)
    if len(conditions) != 1:
        raise ValueError("mixed conditions: analyze each condition separately")
    total, succeeded = len(rows), len(ttfts)
    return {
        "label": report.get("label"), "concurrency": report.get("concurrency"),
        "condition": json.loads(next(iter(conditions))),
        "evidence_labels": sorted(evidence),
        "requests": total, "successful_requests": succeeded,
        "failed_requests": total - succeeded,
        "failure_fraction": (total - succeeded) / total,
        "wall_seconds": wall, "successful_output_tokens": tokens,
        "successful_output_tokens_per_second": tokens / wall,
        "latency_population": "successful_requests_only",
        "ttft_median_ms": median(ttfts), "ttft_p95_ms": p95(ttfts),
        "e2e_p95_ms": p95(e2es), "tpot_median_ms": median(tpots),
        "tpot_eligible_requests": len(tpots),
        "slo_ttft_limit_ms": ttft_limit, "slo_e2e_limit_ms": e2e_limit,
        "slo_good_requests": good, "slo_attainment": good / total,
        "slo_good_requests_per_second": good / wall,
    }


def reject_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def run_file(source, destination, ttft_limit, e2e_limit):
    raw = Path(source).read_bytes()
    report = json.loads(raw, parse_constant=reject_constant)
    result = analyze(report, ttft_limit, e2e_limit)
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)
    with Path(destination).open("x", encoding="utf-8") as stream:
        stream.write(encoded + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--ttft-limit-ms", required=True, type=float)
    parser.add_argument("--e2e-limit-ms", required=True, type=float)
    args = parser.parse_args()
    try:
        run_file(args.source, args.destination,
                 args.ttft_limit_ms, args.e2e_limit_ms)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**English:** Save the following as `test_analyze.py` beside the analyzer. All fixture numbers are invented arithmetic inputs, not measurements of SGLang or any GPU. Two successful requests produce six tokens over a two-second run, so successful output throughput is three tokens per second. Only one of three attempts meets both the 20 ms TTFT and 100 ms E2E gates: attainment is one third and good request rate is 0.5 per second. A failed request remains part of the denominator even though its timeout does not enter successful-request latency percentiles. Display both populations together.

**中文：** 将下列内容保存为分析器旁边的 `test_analyze.py`。所有测试数字都是人为构造的算术输入，不是 SGLang 或任何 GPU 的性能测量。两个成功请求在整轮两秒内产生六个 token，因此成功输出吞吐为每秒三个 token。三次尝试中只有一次同时满足 20 毫秒 TTFT 与 100 毫秒 E2E 门槛，所以达标比例为三分之一，达标请求速率为每秒零点五次。失败请求的超时不进入成功请求延迟分位数，但仍然属于总尝试分母，这两种统计口径必须同时展示。

```python
import json
import tempfile
import unittest
from pathlib import Path

from analyze_report import analyze, run_file


def fixture():
    common = {"condition": {"input_tokens": 4, "output_tokens": 3},
              "evidence": "synthetic_protocol_test"}
    return {"label": "invented-fixture", "concurrency": 2,
            "summary": {"wall_seconds": 2.0}, "rows": [
        dict(common, id=0, success=True, e2e_ms=30,
             observed_ttft_ms=10, observed_tpot_ms=10, completion_tokens=3),
        dict(common, id=1, success=True, e2e_ms=70,
             observed_ttft_ms=30, observed_tpot_ms=20, completion_tokens=3),
        dict(common, id=2, success=False, e2e_ms=1000, error="timeout"),
    ]}


class AnalysisTests(unittest.TestCase):
    def test_known_arithmetic(self):
        result = analyze(fixture(), 20, 100)
        self.assertEqual(result["successful_output_tokens_per_second"], 3)
        self.assertEqual(result["failed_requests"], 1)
        self.assertEqual(result["ttft_median_ms"], 20)
        self.assertEqual(result["ttft_p95_ms"], 30)
        self.assertEqual(result["e2e_p95_ms"], 70)
        self.assertEqual(result["slo_attainment"], 1 / 3)
        self.assertEqual(result["slo_good_requests_per_second"], 0.5)
        self.assertEqual(result["tpot_median_ms"], 15)
        self.assertEqual(result["evidence_labels"], ["synthetic_protocol_test"])

    def test_missing_tpot_is_not_zero(self):
        data = fixture()
        data["rows"][0]["observed_tpot_ms"] = None
        result = analyze(data, 20, 100)
        self.assertEqual(result["tpot_median_ms"], 20)
        self.assertEqual(result["tpot_eligible_requests"], 1)

    def test_duplicate_id(self):
        data = fixture()
        data["rows"][1]["id"] = 0
        with self.assertRaisesRegex(ValueError, "duplicate"):
            analyze(data, 20, 100)

    def test_nonfinite_and_boolean_number(self):
        for value in (float("nan"), float("inf"), True):
            data = fixture()
            data["rows"][0]["e2e_ms"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze(data, 20, 100)

    def test_mixed_conditions(self):
        data = fixture()
        data["rows"][1]["condition"] = {"input_tokens": 8, "output_tokens": 3}
        with self.assertRaisesRegex(ValueError, "mixed"):
            analyze(data, 20, 100)

    def test_all_failed(self):
        data = fixture()
        data["rows"] = [data["rows"][2]]
        result = analyze(data, 20, 100)
        self.assertIsNone(result["ttft_p95_ms"])
        self.assertEqual(result["failure_fraction"], 1)
        self.assertEqual(result["successful_output_tokens_per_second"], 0)

    def test_invalid_wall(self):
        data = fixture()
        data["summary"]["wall_seconds"] = 0
        with self.assertRaises(ValueError):
            analyze(data, 20, 100)

    def test_invalid_success_record(self):
        for field, value in (("success", "true"), ("observed_ttft_ms", 40),
                             ("completion_tokens", 1), ("evidence", "")):
            data = fixture()
            data["rows"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyze(data, 20, 100)

    def test_preserve_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "raw.json", Path(directory) / "out.json"
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            result = run_file(source, target, 20, 100)
            self.assertEqual(len(result["source_sha256"]), 64)
            original = target.read_bytes()
            with self.assertRaises(FileExistsError):
                run_file(source, target, 20, 100)
            self.assertEqual(target.read_bytes(), original)

    def test_invalid_input_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "raw.json", Path(directory) / "out.json"
            source.write_text('{"rows": NaN}', encoding="utf-8")
            with self.assertRaises(ValueError):
                run_file(source, target, 20, 100)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
```

**English:** Run the suite and create a fixture report with the commands below. The second command deliberately imports the fixture builder so the demonstrated input and tested input are identical. Use a new derived filename on each rerun; exclusive creation prevents replacing an earlier result. This protection is not a complete transactional storage design: a disk failure during writing can leave a partial newly created file. Such a file must be treated as failed output, never as a complete report simply because its path exists. Integrity checks, durability, and multi-file commit semantics require further design for the actual environment; a file-opening mode does not supply them.

**中文：** 用以下命令运行测试并创建示例报告。第二条命令直接导入测试数据构造函数，使演示输入与测试输入保持一致。重复运行时使用新的派生文件名；独占创建会阻止覆盖已有结果。这种保护并不是完整的事务存储设计：写入过程中发生磁盘故障，仍可能留下部分新文件。此类文件必须视为失败输出，不能只因路径存在就当作完整报告。完整性检查、持久化保证和多文件提交是更进一步的工程需求，应根据实际运行环境设计，而不是由一个写文件参数推导出来。

```bash
python3 -m unittest -v test_analyze.py
python3 -c 'import json; from test_analyze import fixture; print(json.dumps(fixture(), indent=2))' > fixture.json
python3 analyze_report.py fixture.json derived.json --ttft-limit-ms 20 --e2e-limit-ms 100
```

**English:** Read `derived.json` and explain its populations before looking at individual values. `latency_population` is successful requests only; `tpot_eligible_requests` can be smaller still. `evidence_labels` must remain `synthetic_protocol_test` for the fixture. The program uses the raw wall duration because per-request durations cannot reconstruct an overlapping run's interval. It also cannot prove that every offered request was logged. Compare request IDs and counts with the original workload manifest; collection omissions require collection evidence, not a more elaborate percentile formula.

**中文：** 阅读 `derived.json` 时，先解释统计人群，再看具体数值。`latency_population` 仅包含成功请求，`tpot_eligible_requests` 还可能更少；测试数据的 `evidence_labels` 必须保持 `synthetic_protocol_test`。程序使用原始整轮时长，因为互相重叠的逐请求耗时无法重建整轮区间。它也不能证明每个已提供请求都被记录，因此还应与原负载清单核对请求 ID 和数量。采集遗漏需要采集证据才能识别，换用更复杂的分位数公式无法补回消失的请求。

**English:** Deliberately rerun the analyzer with the same destination and observe its nonzero exit and preserved old content. Then alter one fixture condition, introduce a duplicate ID, and set one time to `NaN`; the corresponding tests show why each input must fail. Finally set TPOT to `null` and observe a smaller eligible count rather than an improved median caused by a zero placeholder. These failures exercise the trust boundary between raw observations and reported conclusions. They are more valuable than a test that merely checks whether some JSON file was produced. These tests protect statistical meaning rather than restating the implementation line by line.

**中文：** 有意使用同一个输出路径再次运行分析器，观察非零退出与旧文件保留。再改变一条测试记录的条件、制造重复 ID，以及把某个时间改成 `NaN`；对应测试说明这些输入为何必须失败。最后把 TPOT 设为 `null`，观察可用样本数减少，而不是因为补零而得到更漂亮的中位数。这些失败覆盖从原始观察到结论之间的信任边界，比只检查“生成了某个 JSON 文件”更有价值。测试目标是保护统计语义，而不是机械地逐行复述实现。

## 8. Integrated Project and Report / 综合项目与报告

**English:** Choose one serving question from Course 10, such as prefix reuse at fixed concurrency, and write the hypothesis before running it. Use Course 11 to justify the exact small model and capacity assumptions, Course 01 to record a healthy device environment, and Course 02 to preserve the workload and configuration. Copy the Course 10 client and this analyzer into your experiment workspace. Reuse their input and output contracts; do not insert an unrecorded conversion that drops failed rows or rewrites evidence labels. Integration means each stage can explicitly consume the previous stage, rather than merely listing many technologies in one report.

**中文：** 从课程 10 选择一个服务问题，例如固定并发下的前缀复用，并在运行前写明假设。使用课程 11 论证具体小模型与容量假设，使用课程 01 记录健康设备环境，再用课程 02 的方法保留负载与配置。把课程 10 的客户端和本课分析器复制到实验工作区，沿用其输入输出契约，不要插入会删除失败行或改写证据标签却未记录的转换步骤。综合项目的核心是让每一步成果能够被下一步明确消费，而不是简单把许多技术名称同时写进报告。

**English:** Establish a baseline first. Verify that the fixed model loads, a readiness request completes, the measured workload is retained, and the client reports the expected number of attempts. Check generated output and termination reasons before making performance comparisons. Then run one treatment condition, repeating complete runs and alternating their order when appropriate. Keep each raw report under a unique run ID. The example below assumes Course 10 has already produced the two raw reports and uses explicit teaching thresholds; it does not start a server or claim either run has been performed here. If device preflight fails, stop at validated CPU analysis and leave GPU collection as a pending step.

**中文：** 先建立基线：确认固定模型能够加载、就绪请求完成、测量负载已经保留，并且客户端报告的尝试次数与预期一致。进行性能比较前检查生成结果和结束原因，然后运行一个处理条件，重复完整运行，并在适用时交替顺序。每份原始报告使用唯一运行 ID。以下命令假设课程 10 已生成两份原始报告，并使用明确的教学阈值；命令本身不会启动服务，也不表示这里已完成真实采集。如果设备预检查失败，就应停在已验证的 CPU 分析阶段，把 GPU 采集列为待执行步骤。

```bash
python3 analyze_report.py cache-on-c1.json cache-on-c1-analysis.json --ttft-limit-ms 500 --e2e-limit-ms 5000
python3 analyze_report.py cache-off-c1.json cache-off-c1-analysis.json --ttft-limit-ms 500 --e2e-limit-ms 5000
```

**English:** Compare failure fraction, successful output throughput, latency distributions, eligible TPOT counts, and latency-gated good request rate together. Report the first prefix-building request separately from subsequent reuse when the hypothesis requires that distinction. The simple analyzer intentionally does not split that population automatically. Derive such a subgroup from preserved request IDs with an explicit rule, and give both its count and the complete-run result. A favorable subgroup must never replace the overall experience without being named. Preserve any grouping transformation and its input digest so another reader can reproduce the same selection.

**中文：** 比较时同时观察失败比例、成功输出吞吐、延迟分布、TPOT 有效样本数和满足延迟门槛的请求速率。如果假设需要区分首次建立前缀与后续复用，就单独报告这两类请求。本课简化分析器不会自动拆分该人群，应基于保留的请求 ID 和明确规则进行派生，并同时给出子群数量和完整运行结果。较有利的子群不能未经说明就替代整体体验。若新的分组脚本改变原始数据，还需保留转换代码与输入摘要，使另一个人能够重建同样的选择过程。

**English:** When a service bottleneck points to device work, collect a representative trace and connect the relevant operations to Course 06's profiling methods. A teaching transpose optimization is an independent kernel experiment unless that kernel is actually used by the measured serving path. Do not add its speedup to a service speedup or imply an end-to-end benefit from an isolated microbenchmark. If an operation occupies fraction p of the original total duration and improves by factor s under otherwise fixed conditions, the idealized total speedup is 1 / ((1 - p) + p / s); changed scheduling and overlap can invalidate those simplifying assumptions. Use this formula to constrain expectations, not to replace a new whole-system measurement.

**中文：** 服务瓶颈指向设备执行时，再采集代表性轨迹，并结合课程 06 的方法分析相关操作。教学转置优化属于独立 kernel 实验，除非测量中的服务路径确实使用了它。不能把其加速倍数与服务加速倍数相加，也不能从孤立微基准直接宣称端到端收益。如果某操作原先占总时长比例为 p，在其他条件固定时提升 s 倍，理想化总加速为 `1 / ((1 - p) + p / s)`；但调度、重叠和排队变化可能破坏这些简化假设。因此公式用于约束预期，而不能替代改动后的整体测量。

**English:** Write the final report as an argument with evidence: the question and practical motivation, fixed conditions and treatment, correctness checks, collection procedure, complete results, interpretation, counterevidence, and remaining limits. Include commands, versions, raw-file digests, and links to traces where they support the argument. Distinguish measured values, estimates, synthetic checks, and unfinished validation. A reader should be able to identify the result that would change your recommendation. This structure also produces a stronger interview discussion than a list of frameworks you have installed. It makes the formation of a judgment, encountered failures, and verified corrections available for discussion.

**中文：** 最终报告应构成有证据支撑的论证，依次说明问题与实际动机、固定条件和处理变量、正确性检查、采集过程、完整结果、解释、反证与剩余边界。在相关位置提供命令、版本、原始文件摘要与轨迹链接，并明确区分实测、估算、合成检查和未完成验证。读者应能辨认什么结果会让你改变当前建议。这样的结构也更适合求职展示：可以讲清楚一个工程判断怎样形成、哪里遇到失败、如何验证修正，比罗列安装过哪些框架更有说服力。

**English:** Keep a small reproduction package: a README explaining the run order, exact source revision, dependency lock or explicit resolved versions, configuration, workload identity, raw reports, derived reports, and a compact evidence manifest. Large weights and traces may live in separate storage, with locations and integrity hashes recorded. Review secrets and user data before sharing real production traces. The goal is a package another engineer can execute or audit, with resource needs and missing steps visible, rather than a folder whose author alone remembers how its files relate. The package may be compact, but its evidence chain should not depend on oral explanation.

**中文：** 保留一个小型复现包，包括解释运行顺序的 README、精确源码 revision、依赖锁文件或实际解析版本、配置、负载身份、原始与派生报告，以及简洁的证据清单。大权重与轨迹可以放在单独存储中，同时记录位置和完整性摘要。共享真实生产轨迹前应检查其中的凭据与用户数据。目标是让另一位工程师能够执行或审计，并看清资源需求和缺失步骤；不是留下一堆只有作者自己记得相互关系的文件。报告结构可以简洁，但证据链不能依靠口头补充才能成立。

## 9. Ten Exercises with Answers / 十道习题与答案

### 1. Submission Time / 提交时间

**English:** Exercise: A CPU timer around an asynchronous kernel launch reports a large improvement. What is established? Answer: only the measured host interval improved. Without a completion boundary, it does not establish device execution time or end-to-end latency. Measure the intended stream interval with appropriate events, or synchronize the relevant work for an end-to-end measurement, and state what the boundary includes. Preserve compilation and warmup policy so first-use initialization does not quietly become the explanation. A more precise timer cannot repair an incorrectly defined measurement target.

**中文：** 练习：CPU 计时器包住异步 kernel launch，显示大幅提升，能够说明什么？答案：只能说明所测主机区间变短，若没有完成边界，就不能证明设备执行时间或端到端延迟改善。应使用适当事件测量目标流区间，或为端到端测量等待相关工作完成，并说明边界包含哪些操作。同时固定编译与预热策略，防止首次使用的初始化被悄悄混入比较。计时工具的精度再高，也无法弥补测量对象定义错误。

### 2. Throughput Denominator / 吞吐分母

**English:** Exercise: Ten overlapping requests each take one second and generate ten tokens; the whole run lasts two seconds. What is successful output throughput if all succeed? Answer: one hundred tokens divided by two seconds, or fifty tokens per second. Summing their durations gives ten seconds and answers a different question. Conversely, adding each request's instantaneous rate is not generally a valid run throughput estimator. State the run start and end, including whether drain time is included. Matching units alone does not justify summing intervals whose overlap changes under concurrency.

**中文：** 练习：十个重叠请求分别耗时一秒、各产生十个 token，整轮运行持续两秒，且全部成功，成功输出吞吐是多少？答案：一百个 token 除以两秒，即每秒五十个。把逐请求耗时相加得到十秒，回答的是另一种问题；把逐请求速率相加，也通常不是有效的整轮吞吐估计。应明确整轮起止点，以及是否包含最后请求完成前的排空阶段。并发改变了时间区间的重叠关系，不能只凭单位看起来一致就直接相加。

### 3. Missing Token Timing / 缺失 token 时间

**English:** Exercise: An SSE event advances the cumulative output count by four. Can that event establish four individual token arrival times? Answer: no. Several tokens may be batched into one event or delayed by buffering. Keep the count and event timestamp, and mark the individual-token TPOT estimate unavailable under this course's contract. Do not invent evenly spaced token arrivals; that would make a smooth distribution by construction rather than by observation. Missing information motivates better collection; it does not authorize invented precision.

**中文：** 练习：一个 SSE 事件让累计输出数量增加四个，能否由此确定四个独立 token 到达时间？答案：不能。多个 token 可能合并在一个事件中，也可能被缓冲延迟。应保留计数和事件时间，并按本课程契约把逐 token 的 TPOT 估计标为不可用。不能人为把四个到达点均匀摊开，否则平滑分布来自构造而非观察。缺失信息可以成为改进采集的理由，但不应变成自动补出更精确数据的许可。

### 4. Tail and Failures / 尾延迟与失败

**English:** Exercise: Successful-request p95 improves while twenty percent of requests now time out. Is the variant better? Answer: that conclusion is unsupported. Removing slow failures from the successful population can improve its percentile while degrading overall service. Compare failure fraction and SLO attainment over all attempts alongside conditional latency, and inspect timeout handling. The desired tradeoff requires a declared objective, not a single favorable metric chosen after the experiment. Also check whether connection errors caused the client to omit requests and undercount failures.

**中文：** 练习：成功请求 p95 改善，但现在百分之二十的请求超时，是否说明变体更好？答案：证据不足。慢请求变成失败并退出成功人群后，该人群的分位数可能改善，整体服务却恶化。必须同时比较失败比例、以全部尝试为分母的 SLO 达标率，以及条件延迟，并检查超时处理。取舍需要预先声明目标，不能在实验后选择一个有利指标作为结论。尤其要核对客户端是否因连接错误漏记请求，避免失败数量本身也被低估。

### 5. Percentile Aggregation / 分位数聚合

**English:** Exercise: Two runs have p95 values of 10 ms and 100 ms. Is their combined p95 55 ms? Answer: not in general. The two scalar summaries discard sample counts and the underlying order statistics. Recompute from compatible raw samples when a pooled population is intended, and retain per-run results to expose run-to-run variation. If the runs use different conditions, pooling may be inappropriate even when every raw sample is available. State the quantile algorithm so interpolation differences are not mistaken for performance changes.

**中文：** 练习：两轮 p95 分别为 10 毫秒和 100 毫秒，合并后是否为 55 毫秒？答案：一般不是。两个标量摘要丢失了样本数量与底层排序信息。若目标确实是合并人群，应从可比较的原始样本重新计算，同时保留每轮结果以呈现轮间波动。如果两轮条件不同，即使原始样本完整，合并也可能没有合理含义。还应说明分位数算法，避免把不同插值规则产生的数值差异误判为服务性能变化。

### 6. Local and Global Speedup / 局部与整体加速

**English:** Exercise: A kernel consumes twenty percent of an otherwise sequential run and becomes twice as fast. What is the idealized total speedup? Answer: 1 / (0.8 + 0.2 / 2), approximately 1.11. The result assumes unchanged work elsewhere and a compatible time decomposition. It is not a prediction for a queued, overlapping service without further analysis. Verify whether the optimized kernel lies on the critical path and whether its input sizes match the service workload. Small-matrix gains do not automatically transfer to large matrices, and scheduling overhead can change the benefit of one invocation.

**中文：** 练习：一个 kernel 占原先顺序运行的百分之二十，现在快了两倍，理想化整体加速是多少？答案：`1 / (0.8 + 0.2 / 2)`，约为 1.11 倍。这个结论假设其他工作不变，而且时间划分适用；没有进一步分析时，它不是对排队与重叠服务的预测。还需核验优化操作是否位于关键路径，以及其输入规模是否与服务负载一致。小矩阵上取得的提升不能自动外推到大矩阵，单次调用优势也可能被调度开销改变。

### 7. Debug a Suspicious Median / 排查可疑中位数

**English:** Exercise: After adding support for a new server version, TPOT median falls nearly to zero. The new version omits a metadata field. How do you debug? Answer: inspect raw events and the parser's missing-value handling before touching the model. A default zero may have entered the sample population. Represent unavailable measurements as null, count eligible requests, and add a regression test using the actual changed event shape. Recompute prior derived reports from preserved raw data rather than editing summary numbers manually. This both repairs the current result and explains the effect on older reports.

**中文：** 练习：适配新服务版本后，TPOT 中位数几乎降为零，而新版本省略了一个元数据字段，如何排查？答案：先查看原始事件与解析器的缺失值处理，不急于修改模型。可能有默认零进入样本人群。应把不可用测量表示为 null，记录可用请求数量，并用真实变化后的事件形状补回归测试。然后从保留的原始数据重新生成派生报告，而不是手改摘要数字。这样既修复当前结果，也能解释旧报告为何受影响。

### 8. Debug an Idle GPU / 排查空闲 GPU

**English:** Exercise: GPU utilization stays low during a claimed saturation test, and increasing client threads raises throughput. What should be checked next? Answer: client CPU, connection pools, request scheduling, tokenization, response parsing, and server admission. The observation suggests a load-generation or host-side limit but does not identify it uniquely. Measure actual offered load and scheduling delay, then use a trace to connect host waits with device idle intervals. Avoid raising unrelated GPU settings before establishing where work is stalled.

**中文：** 练习：声称进行饱和测试时 GPU 利用率很低，而增加客户端线程会提高吞吐，下一步检查什么？答案：客户端 CPU、连接池、请求调度、分词、响应解析与服务准入。这说明负载生成或主机侧限制值得调查，但还不能唯一确定原因。应测量真实提供负载与调度延迟，再用轨迹把主机等待和设备空闲区间对应起来。先定位工作停在哪里，再决定优化层次；仅根据低利用率直接调整无关 GPU 参数，可能完全触及不到瓶颈。

### 9. Design a Cache Comparison / 设计缓存对比

**English:** Exercise: Design a defensible prefix-cache A/B experiment. Answer: pin model, tokenizer, runtime, prompts, output policy, and concurrency; change only the intended cache treatment. Declare warmup and reset procedures, separate the initial prefix-building request when relevant, alternate run order, preserve all outcomes, and inspect reuse counters. Compare multiple complete runs and state which request population the conclusion describes. A larger experiment is not automatically better if it loses control of these conditions. With uncontrolled conditions, more samples can describe a confounded problem more precisely without answering the original question.

**中文：** 练习：设计一个可辩护的前缀缓存 A/B 实验。答案：固定模型、tokenizer、运行时、提示、输出策略与并发，只改变目标缓存处理。声明预热和重置流程，在需要时分离首次建立前缀的请求，交替运行顺序，保留所有结果，并检查复用计数。比较多轮完整运行，说明结论针对哪种请求人群。实验规模越大并不自动越好；如果条件失控，大量样本只会更精确地描述一个混杂问题，而不是回答最初假设。

### 10. Review the Evidence Package / 审查证据包

**English:** Exercise: A candidate presents passing CPU tests, a compiled CUDA source file, and a synthetic client report while their GPU driver is broken. What has been completed, and what remains? Answer: the specified CPU behavior, compilation boundary, and synthetic protocol or arithmetic checks may be established. Model loading, actual device correctness, service capacity, and speedup remain unverified. Request the exact commands and logs, then define the missing healthy-GPU run. Do not discard valid partial evidence or promote it beyond what it measures. Credibility comes from stating known and unknown facts clearly and completing the missing validation.

**中文：** 练习：某份项目展示了通过的 CPU 测试、已编译 CUDA 源码和合成客户端报告，但 GPU 驱动损坏，哪些工作完成了，哪些仍缺失？答案：对应的 CPU 行为、编译边界、合成协议或算术检查可以成立；模型加载、真实设备正确性、服务容量与加速仍未验证。应检查精确命令与日志，再定义缺失的健康 GPU 运行。既不要丢弃有效的阶段成果，也不要提升其证据等级。工程可信度来自清楚说明已知与未知，并持续补齐必要验证。

## 10. Completion and Next Steps / 完成标准与下一步

**English:** Complete this course by reproducing the CPU analysis lab and explaining every denominator, then producing one controlled GPU-backed service report when a healthy environment is available. The report must retain failures, workload identity, raw observations, validation status, and at least one plausible alternative explanation. A useful next iteration follows the strongest evidence: improve client generation, tune serving policy, analyze memory capacity, or investigate a specific kernel. Choose the layer because observations point to it, not because its technology name is fashionable. The course supplies a runnable starting point; engineering skill grows through repeated hypotheses, checks, recorded failures, and revised judgments.

**中文：** 完成本课首先要复现 CPU 分析实验并解释每个分母，然后在具备健康环境时生成一份受控的真实 GPU 服务报告。报告须保留失败、负载身份、原始观察、验证状态，以及至少一种合理的替代解释。下一轮迭代应遵循最有力证据：改进客户端生成、调整服务策略、分析显存容量，或调查具体 kernel。选择某一层是因为观察指向它，而不是因为技术名称流行。课程提供可执行起点，真正的工程能力来自连续提出假设、验证、记录失败并修正判断。

## Validation Record / 验证记录

**English:** On 2026-09-18, the exact analyzer and test blocks above were executed with Python 3.14.4 in an isolated temporary directory. All ten tests passed, and the CLI produced the expected synthetic arithmetic: three attempts, two successes, one failure, three successful output tokens per second, and one-third latency-gate attainment. These values validate calculations only. GPU serving and profiling were not executed because the authoring host had a driver/NVML mismatch; no service latency, capacity, or speedup is claimed.

**中文：** 2026-09-18，在隔离临时目录中使用 Python 3.14.4 执行了上述完全相同的分析器与测试代码。十项测试全部通过，命令行产生预期的合成算术结果：三次尝试、两次成功、一次失败、成功输出每秒三个 token，以及三分之一的延迟门槛达标率。这些数值仅验证计算。由于编写主机存在驱动与 NVML 不匹配，未执行 GPU 服务或性能轨迹采集，未宣称任何服务延迟、容量或加速结果。

**English:** A cross-course integration check also connected Course 10's actual client to its local synthetic HTTP fixture, then passed the resulting report through this analyzer. One successful response and one HTTP rejection were both retained, the object-valued condition survived unchanged, and the evidence label remained synthetic. This checks the shared data contract, not model inference or serving performance.

**中文：** 跨课程集成检查还让课程 10 的实际客户端连接其本地合成 HTTP 服务，再把所得报告传入本课分析器。一次成功响应和一次 HTTP 拒绝均得到保留，对象形式的条件保持不变，证据标签仍为合成测试。这验证了两课共享的数据契约，不代表模型推理或服务性能验证。

## References / 参考资料

**English:** Checked on 2026-09-18. These primary sources support measurement semantics and current tool entry points; the experiments, thresholds, and fixtures are original teaching material.

**中文：** 以下一手资料于 2026-09-18 核查，用于支持度量语义与当前工具入口；实验、阈值和测试数据为本课原创教学内容。

- [SGLang v0.5.19 serving benchmark source / SGLang 固定版本服务基准源码](https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/benchmark/serving.py)
- [SGLang compatibility entry point / SGLang 兼容入口](https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/bench_serving.py)
- [Nsight Systems User Guide / Nsight Systems 用户指南](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)
- [Python statistics: median, quantiles, and nonfinite values / Python 统计函数与非有限值](https://docs.python.org/3/library/statistics.html)
- [NIST: skewness and distribution tails / NIST 偏度与分布尾部](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm)
- [wrk2: load generation and coordinated omission / wrk2 负载生成与协调遗漏](https://github.com/giltene/wrk2)
- [Course 10 client and experiments / 课程 10 客户端与实验](../10/README.md)
- [Course 06 kernel measurement / 课程 06 kernel 度量](../06/README.md)
