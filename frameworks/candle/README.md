# Candle

**English:** Candle is the repository's primary Rust-native inference-framework
track.

**中文：** Candle 是本仓库 Rust-native 推理框架学习主线。

## Learning Goals / 学习目标

- Understand Candle tensors, devices, dtypes, and its CUDA backend / 理解 Candle tensor、device、dtype 与 CUDA backend
- Complete model loading and a basic inference flow / 完成模型加载与基础推理流程
- Understand custom-op and custom-kernel integration / 理解 custom op 与 custom kernel 接入方式
- Compare with `cuda-oxide` kernels, PyTorch baselines, and LLM runtimes / 与 `cuda-oxide` kernel、PyTorch baseline 和 LLM runtime 对照

## Suggested Documents / 建议文档

- `tensor_basics.md`: Tensors, devices, and dtypes / tensor、device 与 dtype
- `model_loading.md`: Model loading and weight formats / 模型加载与权重格式
- `cuda_backend.md`: CUDA backend usage and limitations / CUDA backend 使用与限制
- `custom_op.md`: Custom-op and custom-kernel integration / custom op 与 custom kernel 接入
- `inference_pipeline.md`: Rust-native inference flow / Rust-native 推理流程
