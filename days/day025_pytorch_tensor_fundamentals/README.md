# Day 025: PyTorch Tensor Fundamentals / PyTorch Tensor 基础

Date / 日期: 2026-07-27 to 2026-07-28 / 2026-07-27 至 2026-07-28

## Topic / 主题

**English:** A concept-first introduction to PyTorch tensors: tensor type,
dimensions, shape, element count, data type, indexing, CPU and CUDA devices,
cross-device operations, broadcasting, reshape, and transpose.

**中文：** 以概念为主的 PyTorch Tensor 入门：Tensor 类型、维度、形状、元素
数量、数据类型、索引、CPU 与 CUDA 设备、跨设备运算、broadcasting、reshape
以及 transpose。

## Goal / 目标

**English:** Build a lightweight mental model for reading basic PyTorch tensor
code and predicting the type, shape, device, and values produced by common
operations, without introducing neural-network training.

**中文：** 在不引入神经网络训练的前提下，建立一套轻量的 Tensor 思维模型，
能够阅读基础 PyTorch 代码，并判断常见操作产生的数据类型、形状、设备与结果值。

## 10 Concept Questions / 10 道概念题

### 1. Tensor type, dimension, and shape / Tensor 类型、维度与形状

**Question (English):** What kind of object is `x` below? Is it
zero-dimensional, one-dimensional, or two-dimensional, and what is
`x.shape`?

```python
import torch

x = torch.tensor([1.0, 2.0, 3.0])
```

**问题（中文）：** 下面的 `x` 是什么类型的对象？它是零维、一维还是
二维 Tensor？`x.shape` 是什么？

```python
import torch

x = torch.tensor([1.0, 2.0, 3.0])
```

**Explanation (English):** `ndim` counts the number of axes, while
`shape` records the length of each axis. A Tensor remains a PyTorch object
even when its input was written as a Python list.

**解说（中文）：** `ndim` 表示轴的数量，`shape` 记录每个轴的
长度。即使输入使用 Python 列表书写，构造后的对象仍然是 PyTorch Tensor。

**Correct Answer (English):** `x` is a PyTorch Tensor. It has one axis,
so `x.ndim` is `1`, and that axis contains three elements, so
`x.shape` is `torch.Size([3])`.

**正确答案（中文）：** `x` 是 PyTorch Tensor。它只有一个轴，因此
`x.ndim` 为 `1`；该轴有三个元素，因此 `x.shape` 为
`torch.Size([3])`。

### 2. Inferred tensor data types / Tensor 数据类型推导

**Question (English):** Under PyTorch's default settings, what are
`a.dtype` and `b.dtype` below, and why do they differ?

```python
a = torch.tensor([1, 2, 3])
b = torch.tensor([1.0, 2.0, 3.0])
```

**问题（中文）：** 在 PyTorch 默认设置下，下面的 `a.dtype` 和
`b.dtype` 分别是什么？为什么不同？

```python
a = torch.tensor([1, 2, 3])
b = torch.tensor([1.0, 2.0, 3.0])
```

**Explanation (English):** A Tensor has one element data type. When
`dtype` is not supplied explicitly, PyTorch infers it from the input values
and the configured default floating-point type.

**解说（中文）：** 一个 Tensor 具有统一的元素数据类型。没有显式传入
`dtype` 时，PyTorch 会根据输入值以及当前默认浮点类型进行推导。

**Correct Answer (English):** With normal defaults, `a.dtype` is
`torch.int64` and `b.dtype` is `torch.float32`. The first
input contains integer literals, while the second contains floating-point
literals. Exact floating-point inference can change if the global default
dtype has been changed.

**正确答案（中文）：** 在通常的默认设置下，`a.dtype` 是
`torch.int64`，`b.dtype` 是 `torch.float32`。第一组输入由
整数构成，第二组输入由浮点数构成。如果全局默认浮点类型被修改，浮点推导结果
也可能随之变化。

### 3. Two-dimensional shape and element count / 二维形状与元素数量

**Question (English):** For the Tensor below, what are `m.ndim`,
`m.shape`, and `m.numel()`?

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

**问题（中文）：** 对于下面的 Tensor，`m.ndim`、`m.shape` 和
`m.numel()` 分别是什么？

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

**Explanation (English):** A rectangular nested list gives a matrix-like
Tensor. Its shape stores row count followed by column count, while
`numel()` returns the total number of elements.

**解说（中文）：** 规则嵌套列表会得到类似矩阵的 Tensor。形状依次记录行数和
列数，`numel()` 返回所有元素的总数。

**Correct Answer (English):** `m.ndim` is `2`,
`m.shape` is `torch.Size([2, 3])`, and `m.numel()` is
`6` because `2 * 3 = 6`.

**正确答案（中文）：** `m.ndim` 为 `2`，`m.shape` 为
`torch.Size([2, 3])`，`m.numel()` 为 `6`，因为
`2 * 3 = 6`。

### 4. Indexing rows and scalar elements / 索引行与标量元素

**Question (English):** What do `m[0]` and `m[1, 2]` return
below, and does PyTorch indexing start at zero or one?

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

**问题（中文）：** 下面的 `m[0]` 和 `m[1, 2]` 分别返回
什么？PyTorch 索引从零还是从一开始？

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

**Explanation (English):** A single index selects along the first axis.
Providing both a row and column index selects one element. Tensor indexing is
zero-based, like Python sequence indexing.

**解说（中文）：** 单个索引沿第一个轴进行选择；同时给出行索引和列索引时会
选择一个元素。Tensor 与 Python 序列一样使用从零开始的索引。

**Correct Answer (English):** `m[0]` returns the one-dimensional
Tensor `tensor([1, 2, 3])`. `m[1, 2]` selects the second row and
third column, returning the scalar Tensor `tensor(6)`. Indexing starts at
`0`.

**正确答案（中文）：** `m[0]` 返回一维 Tensor
`tensor([1, 2, 3])`。`m[1, 2]` 选择第二行第三列，返回标量
Tensor `tensor(6)`。索引从 `0` 开始。

### 5. Moving a Tensor to CUDA / 将 Tensor 移至 CUDA

**Question (English):** Assuming a CUDA GPU is available, what are the devices
of `x` and `y` below? Does calling `x.to("cuda")` also move
the original `x`?

```python
x = torch.tensor([1.0, 2.0, 3.0])
y = x.to("cuda")
```

**问题（中文）：** 假设 CUDA GPU 可用，下面的 `x` 和 `y` 分别
位于什么设备？调用 `x.to("cuda")` 后，原来的 `x` 是否也会移动？

```python
x = torch.tensor([1.0, 2.0, 3.0])
y = x.to("cuda")
```

**Explanation (English):** Tensors created without a device argument normally
start on the CPU. Moving between CPU and CUDA memory returns a Tensor on the
requested device; the original binding is not reassigned automatically.

**解说（中文）：** 没有指定设备时，Tensor 通常创建在 CPU。CPU 与 CUDA 内存
之间的移动会返回位于目标设备的 Tensor，不会自动重新绑定原来的变量。

**Correct Answer (English):** `x.device` is `cpu` and
`y.device` is normally `cuda:0`. The original `x` remains on
the CPU. To make the same name refer to the CUDA Tensor, write
`x = x.to("cuda")`.

**正确答案（中文）：** `x.device` 是 `cpu`，
`y.device` 通常是 `cuda:0`。原来的 `x` 仍位于 CPU。如果
希望同一个名字指向 CUDA Tensor，应写成 `x = x.to("cuda")`。

### 6. Operations across different devices / 跨设备运算

**Question (English):** Can the addition below succeed directly? If not, why,
and how should it be corrected?

```python
x = torch.tensor([1.0, 2.0])
y = torch.tensor([3.0, 4.0]).cuda()

z = x + y
```

**问题（中文）：** 下面的加法能否直接成功？如果不能，原因是什么？应该怎样
修改？

```python
x = torch.tensor([1.0, 2.0])
y = torch.tensor([3.0, 4.0]).cuda()

z = x + y
```

**Explanation (English):** An ordinary tensor operation expects its operands
to be on the same device. PyTorch does not silently choose a transfer
direction because CPU-GPU copies have a cost and the intended destination can
be ambiguous.

**解说（中文）：** 普通 Tensor 运算要求操作数位于同一设备。PyTorch 不会静默
选择传输方向，因为 CPU-GPU 拷贝存在成本，而且目标设备可能存在歧义。

**Correct Answer (English):** The addition fails because `x` is on the CPU
and `y` is on CUDA. Move one operand explicitly, for example:

```python
z = x.to(y.device) + y
```

**正确答案（中文）：** 该加法会失败，因为 `x` 位于 CPU，而 `y`
位于 CUDA。应显式移动一个操作数，例如：

```python
z = x.to(y.device) + y
```

### 7. Broadcasting a row-shaped value / 对行形值进行 Broadcasting

**Question (English):** Can `a + b` succeed below? What are
`c.shape` and the contents of `c`?

```python
a = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
b = torch.tensor([10, 20, 30])

c = a + b
```

**问题（中文）：** 下面的 `a + b` 能否成功？`c.shape` 和
`c` 的内容分别是什么？

```python
a = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
b = torch.tensor([10, 20, 30])

c = a + b
```

**Explanation (English):** Broadcasting aligns dimensions from the right.
Here `b` has length three, matching the last dimension of `a`, so
the same three values are added to every row.

**解说（中文）：** Broadcasting 从右侧对齐维度。这里 `b` 的长度为三，
与 `a` 的最后一维相同，因此同一组三个值会应用到每一行。

**Correct Answer (English):** The addition succeeds.
`c.shape` is `torch.Size([2, 3])`, and:

```python
c = torch.tensor([
    [11, 22, 33],
    [14, 25, 36],
])
```

**正确答案（中文）：** 加法可以成功。`c.shape` 是
`torch.Size([2, 3])`，结果为：

```python
c = torch.tensor([
    [11, 22, 33],
    [14, 25, 36],
])
```

### 8. Reshaping without changing element count / 在元素数量不变时 Reshape

**Question (English):** What are `x.shape`, `m.shape`, and the
contents of `m` below?

```python
x = torch.tensor([1, 2, 3, 4, 5, 6])
m = x.reshape(2, 3)
```

**问题（中文）：** 下面的 `x.shape`、`m.shape` 和 `m`
的内容分别是什么？

```python
x = torch.tensor([1, 2, 3, 4, 5, 6])
m = x.reshape(2, 3)
```

**Explanation (English):** `reshape(2, 3)` requests two rows and three
columns. Reshape changes the logical shape while preserving the six elements
and their linear order.

**解说（中文）：** `reshape(2, 3)` 表示两行三列。reshape 改变逻辑形状，
但保持六个元素以及它们的线性顺序。

**Correct Answer (English):** `x.shape` is `torch.Size([6])`,
`m.shape` is `torch.Size([2, 3])`, and:

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

**正确答案（中文）：** `x.shape` 是 `torch.Size([6])`，
`m.shape` 是 `torch.Size([2, 3])`，结果为：

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
```

### 9. Transposing two dimensions / 交换两个维度

**Question (English):** Given a `m` of shape `[2, 3]` below, what
are `t.shape` and the contents of `t`? What does
`transpose(0, 1)` mean?

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
t = m.transpose(0, 1)
```

**问题（中文）：** 对于下面形状为 `[2, 3]` 的 `m`，
`t.shape` 和 `t` 的内容分别是什么？`transpose(0, 1)`
表示什么？

```python
m = torch.tensor([
    [1, 2, 3],
    [4, 5, 6],
])
t = m.transpose(0, 1)
```

**Explanation (English):** The arguments are dimension indices, not data
values. Swapping dimension zero and dimension one exchanges the row and column
axes.

**解说（中文）：** 参数表示维度编号，不是 Tensor 中的数据。交换第零维与第一维
就是交换行轴和列轴。

**Correct Answer (English):** `t.shape` is
`torch.Size([3, 2])`, and:

```python
t = torch.tensor([
    [1, 4],
    [2, 5],
    [3, 6],
])
```

`transpose(0, 1)` swaps the first and second axes.

**正确答案（中文）：** `t.shape` 是 `torch.Size([3, 2])`，结果为：

```python
t = torch.tensor([
    [1, 4],
    [2, 5],
    [3, 6],
])
```

`transpose(0, 1)` 会交换第一个轴与第二个轴。

### 10. Combining dtype, shape, and device / 综合判断 dtype、shape 与 device

**Question (English):** Assuming CUDA is available, determine the shape,
dtype, and device properties produced by this code:

```python
x = torch.tensor(
    [[1, 2], [3, 4]],
    dtype=torch.float32,
)

y = x.to("cuda")
z = y.reshape(4)
```

What are `x.shape`, `x.dtype`, and `x.device`? What is
`y.device`, and does `x` remain on the CPU? Finally, what are
`z.shape` and `z.numel()`?

**问题（中文）：** 假设 CUDA 可用，请判断下面代码产生的 shape、dtype 与
device：

```python
x = torch.tensor(
    [[1, 2], [3, 4]],
    dtype=torch.float32,
)

y = x.to("cuda")
z = y.reshape(4)
```

`x.shape`、`x.dtype` 和 `x.device` 分别是什么？
`y.device` 是什么，`x` 是否仍在 CPU？最后，`z.shape`
和 `z.numel()` 分别是什么？

**Explanation (English):** Dtype, logical shape, and storage device are
independent properties. Moving a Tensor does not change its shape or dtype,
and reshaping does not change its device or element count.

**解说（中文）：** dtype、逻辑形状和存储设备是相互独立的属性。移动 Tensor
不会改变其形状或 dtype；reshape 不会改变其设备或元素总数。

**Correct Answer (English):**

```python
x.shape   # torch.Size([2, 2])
x.dtype   # torch.float32
x.device  # cpu

y.device  # cuda:0

z.shape   # torch.Size([4])
z.numel() # 4
```

The original `x` remains on the CPU. `z` remains on CUDA and
contains the same four values in one dimension.

**正确答案（中文）：**

```python
x.shape   # torch.Size([2, 2])
x.dtype   # torch.float32
x.device  # cpu

y.device  # cuda:0

z.shape   # torch.Size([4])
z.numel() # 4
```

原来的 `x` 仍在 CPU。`z` 仍在 CUDA，并以一维形式保存相同的四个
值。

## Summary / 总结

**English:** This session established the first PyTorch Tensor mental model:

```text
Tensor
  = values
  + dtype
  + shape
  + device
```

The learner can recognize a Tensor, distinguish CPU from CUDA storage, explain
why cross-device arithmetic needs an explicit transfer, and identify basic
one-dimensional and two-dimensional structures. Exact multi-dimensional shape
reasoning, broadcasting, reshape ordering, and transpose still need repeated
practice before moving to stride and contiguous storage.

**中文：** 本次学习建立了第一层 PyTorch Tensor 思维模型：

```text
Tensor
  = 数值
  + dtype
  + shape
  + device
```

目前能够识别 Tensor、区分 CPU 与 CUDA 存储、解释跨设备运算为何需要显式传输，
并判断基础的一维与二维结构。多维 shape 的精确推理、broadcasting、reshape
参数顺序和 transpose 仍需要重复练习，然后再进入 stride 与连续存储。

## Common Mistakes / 常见错误

**English:**

- Giving generic names such as integer or float instead of exact PyTorch dtype
  names such as `torch.int64` and `torch.float32`.
- Treating `shape` as a function instead of the `tensor.shape`
  attribute.
- Reversing the row and column sizes in `reshape(rows, columns)`.
- Assuming different shapes cannot operate together without first checking
  broadcasting compatibility.
- Treating `transpose(0, 1)` arguments as values rather than dimension
  indices.
- Forgetting that `to("cuda")` returns a Tensor on the requested device
  without automatically rebinding the original variable.

**中文：**

- 只使用整数或浮点数等泛称，而没有给出 `torch.int64`、
  `torch.float32` 等准确 PyTorch dtype 名称。
- 把 `shape` 当作函数，而不是 `tensor.shape` 属性。
- 颠倒 `reshape(行数, 列数)` 中的行列大小。
- 看到形状不同就认为无法运算，而没有先检查 broadcasting 兼容性。
- 把 `transpose(0, 1)` 的参数当成数据，而不是维度编号。
- 忘记 `to("cuda")` 会返回目标设备上的 Tensor，但不会自动重新绑定原
  变量。

## Next Steps / 下一步

**English:**

1. Repeat short drills that predict `ndim`, `shape`, and
   `numel()` from nested values.
2. Practice compatible and incompatible broadcasting examples.
3. Compare `reshape`, `transpose`, and element indexing with small
   tensors.
4. Learn elementwise reductions such as `sum` and `mean` with a
   selected dimension.
5. After shape reasoning becomes stable, study `stride`,
   `contiguous()`, and CUDA asynchronous timing.

**中文：**

1. 通过短题反复练习从嵌套数据判断 `ndim`、`shape` 和
   `numel()`。
2. 分别练习能够和不能够 broadcasting 的形状组合。
3. 使用小型 Tensor 对比 `reshape`、`transpose` 和元素索引。
4. 学习在指定维度上执行 `sum`、`mean` 等归约运算。
5. shape 推理稳定后，再学习 `stride`、`contiguous()` 与 CUDA
   异步计时。
