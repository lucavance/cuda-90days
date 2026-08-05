# Frameworks / 框架

**English:** This directory records study notes and experiments for the model
execution layer that connects low-level CUDA/Rust kernels with high-level LLM
serving runtimes.

**中文：** 本目录记录模型执行框架层的学习与实验，连接底层 CUDA/Rust kernel
和上层 LLM serving runtime。

## Learning Priority / 学习优先级

```text
PyTorch baseline -> Candle
```

## Roles / 定位

- `pytorch/`: Baselines, correctness oracle, and CUDA extension entry point / baseline、correctness oracle 与 CUDA extension 学习入口
- `candle/`: Rust-native inference-framework track / Rust-native 推理框架主线

## Scope / 关注范围

- Tensor abstractions / tensor abstraction
- CUDA backends / CUDA backend
- Model loading / model loading
- Custom ops and custom kernels / custom op 与 custom kernel
- Inference pipelines / inference pipeline
- Comparisons with `kernels/`, `runtime/`, and `benchmarks/` / 与这些目录的对照关系
