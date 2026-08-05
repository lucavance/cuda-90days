# Rust Supporting Skills / Rust 支撑能力

**English:** Rust is one of the repository's core supporting languages. Its
purpose is to support `cuda-oxide`, GPU kernel development, and AI inference
infrastructure.

**中文：** Rust 是本仓库的核心支撑语言之一，目标是服务于 `cuda-oxide`、GPU
kernel 编写和 AI 推理基础设施。

## Scope / 关注范围

- Ownership, borrowing, and GPU resource-lifetime modeling / ownership、borrowing 与 GPU 资源生命周期建模
- Designing `unsafe` boundaries / `unsafe` 边界设计
- FFI with the CUDA Runtime and Driver APIs / FFI 与 CUDA runtime、driver API 交互
- `cuda-oxide` experiment records / `cuda-oxide` 实验记录
- Async scheduling and inference runtimes with `tokio` / `tokio` 异步调度与推理服务 runtime
- Error handling, cleanup, and memory-safety constraints / 错误处理、资源释放与内存安全约束

## Non-Goal / 非目标

**English:** This is not a general Rust introduction. Notes should connect
directly to GPU programming, system scheduling, or inference-engine
implementation whenever possible.

**中文：** 本目录不作为通用 Rust 入门教程。所有笔记应尽量落到 GPU 编程、系统
调度或推理引擎实现上。
