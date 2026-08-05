# Inference Runtime / 推理运行时

**English:** This directory records the use, benchmarking, and internal
mechanisms of mature LLM inference runtimes.

**中文：** 本目录记录成熟 LLM inference runtime 的使用、benchmark 与内部机制
分析。

**English:** These tools are references for custom CUDA/Rust kernels and AI
infrastructure design, not the repository's primary implementation targets. To
keep the scope focused, only SGLang is currently retained.

**中文：** 这些工具不是本仓库的主线实现对象，而是用于对照自研 CUDA/Rust
kernel 与 AI Infra 系统设计。为避免学习范围发散，本仓库当前只保留 SGLang。

## Role / 定位

- `sglang/`: Primary study target for runtimes, schedulers, KV cache, RadixAttention, and complex inference flows / 重点学习 runtime、scheduler、KV cache、RadixAttention 与复杂推理流程表达

## Record Template / 记录模板

**English:** Each runtime record should include:

**中文：** 每个 runtime 建议记录：

- Installation and version compatibility / 安装与版本兼容
- Model launch commands / 模型启动命令
- API usage / API 调用方式
- Benchmark methods / benchmark 方法
- VRAM, throughput, and latency data / 显存、吞吐与延迟数据
- Internal mechanisms such as the scheduler, KV cache, and attention backend / scheduler、KV cache、attention backend 等内部机制
- Differences from custom kernels or other runtimes / 与自研 kernel 或其他 runtime 的差异
