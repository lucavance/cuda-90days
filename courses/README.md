# AI Infrastructure Courses / AI 基础设施课程

**English:** Twelve bilingual courses turn the repository's learning topics into a connected engineering curriculum. Each course targets 8,000–12,000 Chinese instructional characters and a complete English counterpart. Read an English paragraph and its Chinese counterpart together; executable examples appear only once. These are complete lessons, not a claim that reading alone provides production experience.

**中文：** 十二门双语课程将仓库的学习主题组织为相互衔接的工程课程。每门目标为 8,000–12,000 个中文教学汉字，并提供完整英文对照。英文段落与对应中文就近配对，可执行示例只保留一份。课程提供完整讲解，但阅读本身不等于生产实践经验。

## Course Map / 课程目录

| ID / 编号 | Course / 课程 | Prerequisites / 前置课程 |
| --- | --- | --- |
| 01 | [Linux and the GPU Development Environment / Linux 与 GPU 开发环境](01/README.md) | General software development / 通用软件开发 |
| 02 | [Python for Experimental Tools / Python 实验工具开发](02/README.md) | General programming / 通用编程 |
| 03 | [C++ for CUDA / 面向 CUDA 的 C++](03/README.md) | 01 |
| 04 | [Rust Systems and Concurrent Programming / Rust 系统与并发编程](04/README.md) | General programming / 通用编程 |
| 05 | [CUDA Programming Foundations / CUDA 编程基础](05/README.md) | 01, 03 |
| 06 | [CUDA Optimization and Profiling / CUDA 优化与性能分析](06/README.md) | 05 |
| 07 | [Rust GPU and CUDA Interoperability / Rust GPU 与 CUDA 互操作](07/README.md) | 03, 04, 05 |
| 08 | [PyTorch and Custom Operators / PyTorch 与自定义算子](08/README.md) | 02, 03, 05; 06 for performance / 性能部分需 06 |
| 09 | [Candle and Rust Inference Frameworks / Candle 与 Rust 推理框架](09/README.md) | 04, 08; 07 for GPU integration / GPU 集成需 07 |
| 10 | [SGLang Inference Systems / SGLang 推理系统](10/README.md) | 01, 02, 08; model foundations in 11 / 11 的模型基础 |
| 11 | [DeepSeek Models and Deployment Analysis / DeepSeek 模型与部署分析](11/README.md) | 05, 08 |
| 12 | [Reproducible Benchmarks and Integrated Engineering / 可复现基准与综合工程](12/README.md) | 02, 06, 10, 11 |

**English:** For a serving-oriented path, read 01 → 02 → 03 → 05 → 06 → 08 → 11 → 10 → 12. Add the Rust branch 04 → 07 → 09 when studying resource-safe systems and native GPU programming. Read the measurement principles in 12 before your first benchmark; its integrated exercise comes last. Course numbers organize the library rather than prescribe twelve calendar weeks.

**中文：** 推理服务方向建议按 01 → 02 → 03 → 05 → 06 → 08 → 11 → 10 → 12 阅读。研究资源安全的系统实现与原生 GPU 编程时，再加入 04 → 07 → 09 的 Rust 分支。第一次做性能实验前就应阅读 12 的度量原则，其综合实验放到最后。编号用于组织课程库，不代表十二个日历周。

## Existing Learning Record Coverage / 已有学习记录覆盖

**English:** Each existing daily record has exactly one primary course below. Secondary references are encouraged, but they do not replace the primary explanation. Newly planned material includes native Rust kernels, Candle, framework integration, model analysis, and reproducible engineering.

**中文：** 下表为每篇已有每日记录指定唯一主讲课程。课程之间可以交叉引用，但不能代替主讲内容。原规划中尚未形成每日记录的内容也纳入课程，包括原生 Rust kernel、Candle、框架集成、模型分析和可复现工程。

| Course / 课程 | Primary daily records / 主归属每日记录 |
| --- | --- |
| 01 | Day015, Day019, Day036 |
| 02 | Day016, Day018, Day022, Day024, Day026, Day027, Day029, Day030, Day031, Day035, Day038, Day039 |
| 03 | Day032 |
| 04 | Day017, Day033, Day037, Day041, Day042 |
| 05 | Day001, Day002, Day003, Day010, Day011, Day012 |
| 06 | Day005, Day006, Day008, Day009, Day013, Day014 |
| 07 | Day020, Day021 |
| 08 | Day025, Day028 |
| 09 | Planned Candle topics / 规划中的 Candle 主题 |
| 10 | Day004, Day007, Day023, Day034, Day040 |
| 11 | Planned DeepSeek topics / 规划中的 DeepSeek 主题 |
| 12 | Planned benchmark, configuration, reporting, and integrated engineering topics / 规划中的基准、配置、报告和综合工程主题 |

## Evidence and Versions / 证据与版本

**English:** Every course states its source-check date and the scope of its validation. Official rolling documentation describes current capabilities; runnable instructions must also identify compatible versions. A compiled example, a CPU test, a GPU run, and a performance result are different levels of evidence. Treat illustrative output as illustrative unless it is explicitly marked as measured.

**中文：** 每门课程注明资料核验日期和验证范围。官方滚动文档用于确认当前能力，可运行说明还必须标出兼容版本。编译通过、CPU 测试、GPU 运行和性能结果属于不同层次的证据。除非明确标为实测，否则示意输出只能作为示意理解。

**English:** Keep course environments separate. For example, Course 08 validates
PyTorch 2.14.0 on CPU, while Course 10 pins SGLang 0.5.19 with its own PyTorch
dependency. A package version used in one experiment is not an instruction to
replace dependencies in another. Record the actual resolved versions whenever
you build an environment from the inline instructions.

**中文：** 各课程使用独立环境。例如课程 08 在 CPU 上验证 PyTorch 2.14.0，
课程 10 则固定 SGLang 0.5.19 及其自身的 PyTorch 依赖。某个实验采用的版本
不表示应替换另一实验的依赖。按照内嵌说明建立环境时，都应记录实际解析版本。

**English:** The authoring environment was inspected on 2026-09-18: Ubuntu 26.04.1, CUDA Toolkit 13.3, and an RTX 4060. At inspection time, the loaded NVIDIA driver reported 610.43.02 while NVML reported 610.57, and `nvidia-smi` failed with a version mismatch. GPU-dependent validation must therefore be reported separately from CPU and compilation checks. The curriculum does not modify the system driver.

**中文：** 编写环境于 2026-09-18 核查：Ubuntu 26.04.1、CUDA Toolkit 13.3 和 RTX 4060。核查时已加载的 NVIDIA 驱动为 610.43.02，NVML 为 610.57，`nvidia-smi` 因版本不匹配失败。因此，依赖 GPU 的验证必须与 CPU 和编译检查分别记录。本课程库不修改系统驱动。

**English:** Validation includes CPU execution, selected CUDA and Rust host
builds, and CPU framework integration, as detailed in each course. The native
cuda-oxide backend build in Course 07 also stopped at a disk-quota limit, so its
native kernel compilation remains unverified. No GPU performance numbers are
claimed from synthetic fixtures, resource estimates, or successful host builds.

**中文：** 验证包括 CPU 执行、部分 CUDA 与 Rust 宿主构建，以及 CPU 框架集成，
具体范围见每门课程记录。课程 07 的原生 cuda-oxide 后端构建还受到磁盘配额
限制而中止，因此原生内核编译仍未验证。合成测试、资源估算和宿主构建成功均未
被用于宣称 GPU 性能结果。

## Completion Criteria / 完成标准

**English:** Work through a course in four passes: explain its main contracts in
your own words, reproduce the inline experiment in a separate working directory,
predict and inspect the deliberate failures, then answer the ten exercises before
reading their solutions. Keep your commands and observations with the learning
record. GPU-dependent steps remain pending until they run on a healthy device;
CPU tests and successful builds provide useful, narrower evidence.

**中文：** 每门课可以分四轮学习：用自己的话解释主要契约，在独立工作目录中
复现内嵌实验，先预测再检查有意设计的失败，最后先回答十道习题再阅读答案。
把命令与观察结果保存在学习记录中。依赖 GPU 的步骤须在健康设备上执行后才能
验收；CPU 测试和构建成功提供有用但范围更窄的证据。

**English:** A course is complete when its full bilingual explanation, runnable examples or clearly classified excerpts, ten exercises with answers, failure analysis, source references, and validation status are present. Chinese length counts instructional prose and exercise explanations outside code fences, excluding navigation and references. English is judged by equivalent coverage and meaning, not by matching the Chinese character count.

**中文：** 每门课程须具备完整双语讲解、可运行示例或明确分类的片段、十道附答案习题、失败分析、来源和验证状态。中文篇幅统计代码围栏外的教学正文及习题解说，排除导航与参考文献。英文按覆盖范围和语义等价验收，不要求与中文汉字数相同。
