# Day 009: Matrix Transpose with Shared Memory / 使用 Shared Memory 的矩阵转置

Date / 日期: 2026-06-15

## Topic / 主题

**English:** A runnable matrix-transpose experiment comparing a naive kernel,
an unpadded `32x32` shared-memory tile, and a padded `32x33` tile.

**中文：** 可运行的 matrix transpose 实验，对比 naive kernel、无 padding 的
`32x32` shared-memory tile，以及带 padding 的 `32x33` tile。

## Goal / 目标

**English:** Apply the shared-memory and bank-conflict concepts from Days 006
and 008 to real kernels, with correctness checking and benchmark scaffolding.

**中文：** 把 Day 006 的 shared memory 与 Day 008 的 bank conflict 概念落到
真实 kernel 中，并加入 correctness check 与 benchmark 框架。

## Experiment Location / 实验位置

~~~text
kernels/cuda_cpp/matrix_transpose/
├── CMakeLists.txt
├── .gitignore
├── .vscode/
└── transpose_bench.cu
~~~

## Kernel Variants / Kernel 版本

### 1. transpose_naive / transpose_naive

**English:** The naive kernel reads directly from global memory:

**中文：** naive kernel 直接从 global memory 读取：

~~~cpp
out[x * height + y] = in[y * width + x];
~~~

**English:** It is simple, but swapping read/write orientation makes one side
of the transpose non-contiguous and normally reduces performance.

**中文：** 逻辑最简单，但 transpose 交换读写方向后，其中一侧 global memory
访问会不连续，通常性能较差。

### 2. transpose_shared_32x32 / transpose_shared_32x32

**English:** This version stages a tile in shared memory:

**中文：** 这个版本把一个 tile 暂存到 shared memory：

~~~cpp
__shared__ float tile[32][32];
~~~

**English:** It reads a contiguous tile, swaps block coordinates, and writes
the transposed tile back, improving the global-memory access pattern. However,
`tile[threadIdx.x][threadIdx.y + j]` becomes a stride-32 shared-memory
access in row-major layout and can create bank conflicts.

**中文：** 它连续读入 tile，交换 block 坐标后写回，从而改善 global memory
访问模式。但在 row-major 布局中，
`tile[threadIdx.x][threadIdx.y + j]` 会形成 stride-32 shared-memory 访问，
容易产生 bank conflict。

### 3. transpose_shared_32x33 / transpose_shared_32x33

**English:** The padded version declares:

**中文：** padding 版本声明：

~~~cpp
__shared__ float tile[32][33];
~~~

**English:** One extra element per row changes the column stride from 32 to
33. Under the simplified mapping below, a stride of 33 distributes a warp's
accesses across banks:

**中文：** 每行多一个 padding 元素，把按列访问的 stride 从 32 改为 33。按下面
的简化映射，stride 33 会把一个 warp 的访问分散到不同 bank：

~~~text
bank_id = index % 32
~~~

## Build / 构建

~~~bash
cd kernels/cuda_cpp/matrix_transpose
cmake -S . -B build -G Ninja
cmake --build build
~~~

**English:** The current environment produced:

**中文：** 当前环境的构建输出为：

~~~text
cmake --build build
# nvcc -O3 -std=c++23 -arch=native ...
# nvcc warning : Cannot find valid GPU for '-arch=native', default arch is used
~~~

**English:** The source compiles successfully with `nvcc`.

**中文：** 源码可以通过 `nvcc` 编译。

## Run / 运行

~~~bash
cd kernels/cuda_cpp/matrix_transpose
cmake --build build --target run
# 或
./build/matrix_transpose 50
~~~

**English:** The current environment reported:

**中文：** 当前环境的运行结果为：

~~~text
CUDA error transpose_bench.cu:210: no CUDA-capable device is detected
~~~

**English:** No CUDA-capable GPU was visible from this shell, so the session
did not produce real performance measurements.

**中文：** 当前 shell 未检测到可用 CUDA GPU，因此本次没有产生真实性能数据。

## Benchmark Design / Benchmark 设计

**English:** The program tests these matrix sizes by default:

**中文：** 程序默认测试以下矩阵尺寸：

~~~text
1024 x 1024
2048 x 2048
4096 x 4096
~~~

**English:** Each kernel reports:

**中文：** 每个 kernel 输出：

~~~text
kernel
avg_ms
GB/s
correct
~~~

**English:** Effective bandwidth assumes one read and one write per element:

**中文：** 有效带宽按每个元素至少读一次、写一次计算：

~~~text
effective_bandwidth = 2 * matrix_bytes / elapsed_time
~~~

## Correctness Design / Correctness 设计

**English:** A CPU reference computes:

**中文：** CPU reference 计算：

~~~cpp
out[x * height + y] = in[y * width + x];
~~~

**English:** Every CUDA result is copied back and compared element by element.
A mismatch prints its location and values and terminates the program.

**中文：** 每个 CUDA 结果都会拷回 Host 并逐元素比较。任何 mismatch 都会打印
位置和数值并让程序失败退出。

## Understanding / 今日理解

- **English:** Matrix transpose is a classic experiment for global-memory
  coalescing, shared-memory tiling, and bank conflicts.
  **中文：** matrix transpose 是观察 global-memory coalescing、shared-memory
  tile 和 bank conflict 的经典实验。
- **English:** A direct transpose normally makes either its reads or writes
  non-contiguous.
  **中文：** 直接 transpose 通常会让读写中的一侧不连续。
- **English:** A shared tile reorganizes global reads and writes into more
  contiguous patterns.
  **中文：** shared tile 能把 global 读写组织得更连续。
- **English:** `tile[32][32]` can conflict during column access; padding to
  `tile[32][33]` changes the stride and reduces that conflict.
  **中文：** `tile[32][32]` 按列访问时可能冲突；padding 到
  `tile[32][33]` 会改变 stride 并减少冲突。
- **English:** Correctness and timing belong in the same minimal runnable
  experiment.
  **中文：** correctness check 与 benchmark 应放进同一个最小可运行实验。

## Pending Benchmark / 待补 benchmark

**English:** On a machine with a visible CUDA GPU, run:

**中文：** 在可见 CUDA GPU 的环境中运行：

~~~bash
cd kernels/cuda_cpp/matrix_transpose
rm -rf build
cmake -S . -B build -G Ninja
cmake --build build
./build/matrix_transpose 100
~~~

**English:** Then fill in the real measurements without replacing the current
`TBD` values with estimates:

**中文：** 随后填写真实性能数据，不使用估算值替换当前 `TBD`：

| Matrix / 矩阵 | Kernel | avg_ms | GB/s | Correct / 正确 |
| --- | --- | ---: | ---: | --- |
| 1024 x 1024 | naive | TBD | TBD | TBD |
| 1024 x 1024 | shared_32x32 | TBD | TBD | TBD |
| 1024 x 1024 | shared_32x33 | TBD | TBD | TBD |
| 2048 x 2048 | naive | TBD | TBD | TBD |
| 2048 x 2048 | shared_32x32 | TBD | TBD | TBD |
| 2048 x 2048 | shared_32x33 | TBD | TBD | TBD |
| 4096 x 4096 | naive | TBD | TBD | TBD |
| 4096 x 4096 | shared_32x32 | TBD | TBD | TBD |
| 4096 x 4096 | shared_32x33 | TBD | TBD | TBD |

## Next Steps / 下一步

- **English:** Run the benchmark on a CUDA GPU and complete the table.
  **中文：** 在 CUDA GPU 上运行 benchmark 并补全表格。
- **English:** Use Nsight Compute to inspect bank-conflict metrics.
  **中文：** 使用 Nsight Compute 观察 bank-conflict 指标。
- **English:** Add a copy kernel to establish a bandwidth ceiling.
  **中文：** 增加 copy kernel，对比 transpose 与纯 copy 的带宽上限。
- **English:** Port the experiment to Rust/cuda-oxide later.
  **中文：** 后续把实验迁移到 Rust/cuda-oxide。
