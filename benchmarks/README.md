# Benchmarks / 性能测试

**English:** This directory stores benchmark scripts, raw results, and
analyses.

**中文：** 本目录用于保存 benchmark 脚本、原始结果和分析结论。

- `configs/`: Benchmark configurations / benchmark 配置
- `scripts/`: Benchmark and data-processing scripts / benchmark 与数据处理脚本
- `results/`: Outputs, tables, and progress analyses / 输出、表格与阶段性分析

**English:** Each benchmark should record at least:

**中文：** 每次 benchmark 建议至少记录：

- GPU model / GPU 型号
- NVIDIA driver and CUDA versions / NVIDIA driver 与 CUDA 版本
- Runtime, framework, and kernel versions / runtime、framework 与 kernel 版本
- Model, batch size, input tokens, and output tokens / 模型、batch size、输入与输出 token 数
- Latency, throughput, and tokens per second / latency、throughput 与 tokens/s
- Peak VRAM usage / 显存峰值
- Reproduction commands / 复现实验命令
- Profiling tools and key observations / profiling 工具与关键观察
