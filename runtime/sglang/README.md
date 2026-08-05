# SGLang

**English:** SGLang is the repository's primary LLM-serving runtime study
target.

**中文：** SGLang 是本仓库重点学习的 LLM serving runtime。

## Learning Goals / 学习目标

- Independently install and launch a model service, then call its OpenAI-compatible API / 能独立安装并启动模型服务，调用 OpenAI-compatible API
- Benchmark throughput, latency, and VRAM usage / 完成吞吐、延迟与显存占用 benchmark
- Understand the runtime, scheduler, KV cache, and RadixAttention / 理解 runtime、scheduler、KV cache 与 RadixAttention
- Understand structured generation and complex inference-flow expression / 理解 structured generation 与复杂推理流程表达
- Compare against PyTorch baselines, Candle, and custom kernels / 与 PyTorch baseline、Candle 和自研 kernel 实验对照

## Suggested Documents / 建议文档

- `install.md`: Installation and CUDA/PyTorch compatibility / 安装与 CUDA/PyTorch 版本兼容
- `serving.md`: Server startup, API calls, and common parameters / server 启动、API 调用与常用参数
- `benchmark.md`: QPS, latency, tokens/s, and VRAM usage / qps、latency、tokens/s 与显存占用
- `internals.md`: Scheduler, KV cache, RadixAttention, and attention backends / scheduler、KV cache、RadixAttention 与 attention backend
- `notes.md`: Issue tracking and troubleshooting / 问题记录与排查
