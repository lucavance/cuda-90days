# 🚀 cuda-90days

> **90-day AI infrastructure engineering journey: write native GPU kernels in
> Rust (`cuda-oxide`) and CUDA C++, then build memory-safe, highly concurrent
> systems for production-grade LLM inference.**
>
> **90 天 AI 基础设施工程实践：使用 Rust（`cuda-oxide`）与 CUDA C++ 编写原生
> GPU kernel，并构建面向生产级 LLM 推理的内存安全、高并发系统。**

**English:** This repository records the low-level experiments behind a
transition from systems development to **AI infrastructure and high-performance
inference engines**.

**中文：** 本仓库记录从系统级开发向 **AI 基础设施（AI Infrastructure）与
高性能推理引擎** 转型过程中的底层实验。

**English:** The core mission is to learn CUDA C++ for tactical depth and
architectural understanding, while focusing on native GPU kernels written in
Rust with the `cuda-oxide` ecosystem. The long-term goal is an end-to-end path
from highly concurrent network scheduling to bare-metal operator acceleration
for industrial LLM inference systems.

**中文：** 核心任务是学习 CUDA C++ 开发，以获得战术深度与体系结构理解；同时
重点攻坚基于 `cuda-oxide` 体系、使用纯 Rust 编写原生 GPU kernel，打通从网络
高并发调度到 bare-metal 算子加速的完整链路，面向工业级大模型推理系统设计
高性能实现。

---

## 🎯 Goal / 目标

**English:** I use this repository to turn my interest in CUDA and AI
infrastructure into visible engineering evidence.

**中文：** 我用这个仓库把对 CUDA 和 AI Infra 的兴趣，逐步变成看得见的工程
证据。

**English:** The job goal is present, but the working rule is simpler: write
fewer abstract notes and leave behind more runnable experiments, benchmarks,
and profiling traces.

**中文：** 求职目标当然存在，但这里的规则更简单：少写空泛笔记，多留下能运行
的实验、benchmark 和 profiling 记录。

---

## 💻 Infrastructure Setup / 实验环境

- **OS / 操作系统:** Ubuntu 26.04 LTS
- **CUDA Toolkit:** 13.3
- **Rustc:** 1.98+
- **Core Crates / 核心 Crate:** `cuda-oxide`, `tokio`, `candle-core`
- **Profiling Tools / 性能分析工具:** NVIDIA Nsight Systems / Nsight Compute

---

## 🗓️ 90-Day Roadmap / 90 天硬核攻坚路线图

**English:** The repository follows this main path:

**中文：** 本仓库遵循以下主线：

```text
CUDA kernel development -> Rust GPU programming -> LLM inference infrastructure
```

**English:** Linux, C++, Rust, and Python are supporting capability layers for
CUDA kernel development and AI inference infrastructure, rather than separate
general-purpose learning tracks.

**中文：** Linux、C++、Rust 与 Python 在本仓库中是 CUDA kernel 开发与 AI
推理基础设施的支撑能力层，而不是独立的通用学习路线。

---

## 📁 Repository Layout / 仓库结构

```text
cuda-90days/
├── README.md
├── days/                  # Daily records for 90 days / 90 天每日实验记录
├── kernels/
│   ├── cuda_cpp/          # CUDA C++ kernel experiments / CUDA C++ kernel 实验
│   └── cuda_oxide/        # Rust cuda-oxide experiments / Rust cuda-oxide 实验
├── frameworks/
│   ├── pytorch/           # Baselines, oracles, extensions / 基线、正确性验证、扩展
│   └── candle/            # Rust-native framework track / Rust 原生推理框架主线
├── runtime/
│   └── sglang/            # Primary LLM serving runtime / 重点 LLM serving runtime
├── infra/
│   ├── linux/             # Ubuntu and GPU tooling / Ubuntu 与 GPU 工具
│   ├── cpp/               # C++ skills for CUDA / CUDA 所需 C++ 能力
│   ├── rust/              # Rust for cuda-oxide and AI Infra / Rust 支撑能力
│   └── python/            # Benchmarks and correctness tools / benchmark 与校验工具
├── benchmarks/
│   ├── configs/           # Benchmark configurations / benchmark 配置
│   ├── scripts/           # Benchmark scripts / benchmark 脚本
│   └── results/           # Results and analysis / 性能结果与分析
├── models/                # Model notes, no weights / 模型记录，不存权重
├── reports/               # Progress and final reports / 阶段复盘与最终报告
├── scripts/               # Repository-wide scripts / 仓库级通用脚本
├── configs/               # Shared configurations / 通用配置
└── docs/                  # Roadmaps, profiling, glossary / 路线图、profiling、术语
```

---

## 🧱 Supporting Layers / 支撑能力层

### Linux

**English:** The current environment is Ubuntu. This area records only Linux
skills related to GPU development: drivers, the CUDA Toolkit, Nsight, dynamic
library paths, permissions, performance-observation tools, and common
environment troubleshooting.

**中文：** 当前实验环境使用 Ubuntu。该目录只记录 GPU 开发相关的 Linux 能力，
包括驱动、CUDA Toolkit、Nsight、动态库路径、权限、性能观察工具与常见环境排查。

### C++

**English:** The C++ area supports CUDA C++ development, with emphasis on
CMake, compilation and linking, memory models, RAII, templates, host/device
code organization, and FFI boundaries with Rust.

**中文：** C++ 目录服务于 CUDA C++ 开发，重点关注 CMake、编译链接、内存模型、
RAII、模板、host/device 代码组织，以及与 Rust 的 FFI 边界。

### Rust

**English:** Rust is one of the repository's primary supporting languages. Its
track focuses on `cuda-oxide`, `unsafe`, FFI, ownership boundaries, async
runtimes, and inference-system scheduling.

**中文：** Rust 是本仓库的重点支撑语言之一，围绕 `cuda-oxide`、`unsafe`、
FFI、所有权边界、异步运行时与推理系统调度展开。

### Python

**English:** Python is the tooling layer for PyTorch baselines, input-data
generation, correctness checks, benchmark-result processing, and visualization.

**中文：** Python 定位为工具层，用于 PyTorch baseline、输入数据生成、
correctness check、benchmark 结果处理和可视化。

---

## 🧩 Inference Runtime / 推理运行时

**English:** Mature inference runtimes provide references for custom kernels
and system design; they do not replace the CUDA/Rust track. To keep the scope
focused, the repository currently retains only SGLang.

**中文：** 成熟推理运行时用于对照自研 kernel 与系统设计，不替代 CUDA/Rust
主线。为避免学习范围发散，本仓库当前只保留 SGLang。

### SGLang

**English:** SGLang is the primary runtime studied here for high-performance
LLM/VLM serving, structured generation, runtime scheduling, KV cache, and
RadixAttention.

**中文：** SGLang 是重点学习对象，用于理解高性能 LLM/VLM serving、structured
generation、runtime 调度、KV cache 与 RadixAttention 等机制。

---

## 🧠 Frameworks / 框架层

**English:** The framework layer connects low-level kernels to inference
services and helps explain model execution, tensor abstractions, backend design,
and custom-op integration.

**中文：** 框架层连接底层 kernel 与上层推理服务，用于理解模型执行、张量抽象、
backend 设计和 custom op 集成。

**English:** Learning priority:

**中文：** 学习优先级：

```text
PyTorch baseline -> Candle
```

### PyTorch

**English:** PyTorch serves as the baseline, correctness oracle, and entry
point for learning CUDA extensions. Focus areas include CUDA tensors, memory
layout, custom ops, the basic mechanisms of `torch.compile`, Inductor, and
Triton, plus performance comparisons with custom kernels.

**中文：** PyTorch 用作 baseline、correctness oracle 和 CUDA extension 学习
入口。重点关注 CUDA tensor、memory layout、custom op、`torch.compile`、
Inductor、Triton 的基本机制，以及与自研 kernel 的性能对照。

### Candle

**English:** Candle is the Rust-native inference-framework track, used first to
understand tensors, model loading, CUDA backends, custom ops, and lightweight
LLM inference pipelines in Rust.

**中文：** Candle 是 Rust-native 推理框架主线，优先用于理解 Rust 中的 tensor、
model loading、CUDA backend、custom op 和轻量 LLM inference pipeline。

---

## 🤖 Models / 模型层

**English:** The models area records architecture, deployment requirements,
VRAM usage, runtime support, and benchmark observations for the DeepSeek model
family. Model weights are not stored in this repository.

**中文：** 模型目录记录 DeepSeek 系列模型的结构、部署要求、显存占用、runtime
支持情况和 benchmark 观察。本仓库不存放模型权重。

---

## 📊 Reports and Benchmarks / 复盘与度量

**English:** Each experiment should retain correctness, benchmark, and
profiling conclusions whenever possible. A progress report is produced every
15 days, followed by a final 90-day report.

**中文：** 每个实验尽量保留 correctness、benchmark 与 profiling 结论。每 15
天输出一次阶段复盘，最终形成 90 天总结报告。
