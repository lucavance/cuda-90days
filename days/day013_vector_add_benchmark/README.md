# Day 013: Vector Add Benchmark / 向量加法性能测试

Date / 日期: 2026-06-27

## Topic / 主题

**English:** Vector-add benchmark: CPU versus CUDA, correctness checking, data
transfer timing, and kernel timing.

**中文：** Vector add benchmark：对比 CPU 与 CUDA，检查正确性，并测量数据传输
和 kernel 时间。

## Goal / 目标

**English:** Complete a minimal CUDA performance experiment with:

**中文：** 完成一个最小 CUDA 性能实验，包含：

- **English:** A CPU reference and CUDA kernel implementation.
  **中文：** CPU reference 与 CUDA kernel 实现。
- **English:** Host-to-device, kernel, and device-to-host timing.
  **中文：** Host-to-Device、kernel 与 Device-to-Host 计时。
- **English:** A correctness check against the CPU result.
  **中文：** 与 CPU 结果对比的 correctness check。

## Implementation / 实现

- **English:** Fixed the input size at `N = 1024`.
  **中文：** 输入规模固定为 `N = 1024`。
- **English:** Kept the CPU reference in `vector_add_cpu` and added
  `vector_add_kernel`.
  **中文：** CPU reference 保留在 `vector_add_cpu`，并新增
  `vector_add_kernel`。
- **English:** Used `CUDA_CHECK` for CUDA Runtime calls.
  **中文：** 使用 `CUDA_CHECK` 检查 CUDA Runtime API。
- **English:** Measured kernel time with `cudaEvent` and transfer time with
  `std::chrono`.
  **中文：** 用 `cudaEvent` 测 kernel，用 `std::chrono` 测数据传输。
- **English:** Printed one tabular summary row.
  **中文：** 以表格形式打印一行汇总结果。

## Run / 运行

**English:** Build:

**中文：** 构建：

~~~bash
make -C kernels/cuda_cpp/vector_add_benchmark
~~~

**English:** Run:

**中文：** 运行：

~~~bash
make -C kernels/cuda_cpp/vector_add_benchmark run
~~~

## Result / 结果

**English:** The code compiles successfully. Runtime execution depends on a
CUDA-capable GPU being available in the local environment.

**中文：** 代码可以成功编译。实际运行取决于本地环境是否提供可用 CUDA GPU。

## Summary / 总结

**English:** The experiment covers the complete basic loop:

**中文：** 本实验覆盖完整基础闭环：

1. **English:** Prepare host data.
   **中文：** 准备 Host 数据。
2. **English:** Allocate device memory.
   **中文：** 分配 Device memory。
3. **English:** Copy inputs to the GPU.
   **中文：** 把输入拷到 GPU。
4. **English:** Launch the kernel.
   **中文：** 启动 kernel。
5. **English:** Copy output back.
   **中文：** 把输出拷回 Host。
6. **English:** Compare CPU and GPU results.
   **中文：** 对比 CPU 与 GPU 结果。
7. **English:** Print timing data.
   **中文：** 打印计时数据。

## Next Step / 下一步

**English:** Extend the benchmark to multiple input sizes, then compare how
`CPU_ms`, `GPU_kernel_ms`, `H2D_ms`, and `D2H_ms` change with `N`.

**中文：** 把 benchmark 扩展到多个输入规模，再比较 `CPU_ms`、
`GPU_kernel_ms`、`H2D_ms` 与 `D2H_ms` 随 `N` 的变化。
