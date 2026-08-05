# PyTorch

**English:** PyTorch serves as the baseline, correctness oracle, and entry
point for learning CUDA extensions in this repository.

**中文：** PyTorch 在本仓库中承担 baseline、correctness oracle 和 CUDA
extension 学习入口的角色。

## Learning Goals / 学习目标

- Understand CUDA tensors, memory layouts, strides, and dtypes / 理解 CUDA tensor、memory layout、stride 与 dtype
- Build correctness baselines with PyTorch / 使用 PyTorch 构造 correctness baseline
- Benchmark custom CUDA/Rust kernels against PyTorch / 使用 PyTorch benchmark 对照自研 CUDA/Rust kernel
- Learn custom CUDA extensions and custom ops / 学习 custom CUDA extension 与 custom op
- Build a basic understanding of `torch.compile`, Inductor, and Triton / 建立对 `torch.compile`、Inductor、Triton 的基本认知

## Suggested Documents / 建议文档

- `tensor_basics.md`: Tensors, layouts, strides, and dtypes / tensor、layout、stride 与 dtype
- `cuda_extension.md`: Custom CUDA extensions / custom CUDA extension
- `custom_op.md`: Custom-op registration and invocation / custom op 注册与调用
- `torch_compile.md`: Basic mechanisms of `torch.compile`, Inductor, and Triton / `torch.compile`、Inductor、Triton 基本机制
- `benchmark_baseline.md`: Baseline and benchmark methods / baseline 与 benchmark 方法
