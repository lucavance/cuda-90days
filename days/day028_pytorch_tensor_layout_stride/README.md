# Day 028: PyTorch Tensor Layout, Strides, and Contiguity / PyTorch Tensor 内存布局、步幅与连续性

Date / 日期: 2026-07-31

## Topic / 主题

**English:** A concept-first study of how PyTorch describes tensor memory
layout with shape, strides, storage offsets, views, contiguity, transposition,
strided slicing, expansion, and permutation, followed by the implications for
custom CUDA kernels.

**中文：** 从概念出发学习 PyTorch 如何使用 shape、stride、storage offset、
view、连续性、转置、步进切片、扩展与维度重排来描述 Tensor 内存布局，并理解
这些概念对自定义 CUDA kernel 的影响。

## Goal / 目标

**English:** Build a reliable model for translating a logical tensor index
into a storage offset, predicting whether common PyTorch operations return
contiguous tensors or metadata-only views, and choosing a correct input-layout
strategy for a CUDA kernel.

**中文：** 建立可靠的 Tensor 内存模型：能够把逻辑索引转换为底层存储偏移，
判断常见 PyTorch 操作会得到连续 Tensor 还是仅修改元数据的 view，并为 CUDA
kernel 选择正确的输入布局处理策略。

## Core Formula / 核心公式

**English:** For an n-dimensional tensor, the storage position associated
with a logical index is described by:

```text
storage position = storage_offset + Σ(index[i] * stride[i])
```

Stride values are measured in elements, not bytes.

**中文：** 对于 n 维 Tensor，一个逻辑索引所对应的底层存储位置可表示为：

```text
存储位置 = storage_offset + Σ(index[i] * stride[i])
```

stride 的单位是元素数量，而不是字节数量。

## 10 Concept Questions / 10 个概念问题

### 1. Shape and strides of a contiguous matrix / 连续矩阵的形状与步幅

**Question (English):** What are `x.shape` and `x.stride()` below? What does
each stride value mean?

```python
import torch

x = torch.arange(12).reshape(3, 4)
```

**问题（中文）：** 下面的 `x.shape` 和 `x.stride()` 分别是什么？stride 中
的每个数字表示什么？

```python
import torch

x = torch.arange(12).reshape(3, 4)
```

**Explanation (English):** Shape records the length of each logical axis.
Stride records how many storage elements must be crossed when the index on
that axis increases by one. The tensor here uses the ordinary contiguous
row-major layout.

**解说（中文）：** shape 记录每个逻辑轴的长度；stride 记录某一轴的索引增加
1 时，需要在底层存储中跨过多少个元素。这里的 Tensor 使用普通的行优先连续
布局。

**Correct Answer (English):** `x.shape` is `torch.Size([3, 4])`, often written
as `(3, 4)`, and `x.stride()` is `(4, 1)`. Moving down one row crosses four
elements, while moving right one column crosses one element. For example,
`x[1, 2]` has offset `1 * 4 + 2 * 1 = 6` and value `6`.

**正确答案（中文）：** `x.shape` 是 `torch.Size([3, 4])`，也常简写为
`(3, 4)`；`x.stride()` 是 `(4, 1)`。向下一行需要跨过 4 个元素，向右一列
需要跨过 1 个元素。例如，`x[1, 2]` 的偏移量是
`1 * 4 + 2 * 1 = 6`，对应的值为 `6`。

### 2. Shape and strides after transposition / 转置后的形状与步幅

**Question (English):** What are `y.shape` and `y.stride()`? Does
`transpose()` rearrange the stored values?

```python
y = x.transpose(0, 1)
```

**问题（中文）：** `y.shape` 和 `y.stride()` 分别是什么？`transpose()`
是否会重新排列底层存储中的值？

```python
y = x.transpose(0, 1)
```

**Explanation (English):** Transposition normally returns a view. It swaps
the selected axes in the tensor metadata, so their shape and stride entries
are swapped together while the underlying storage stays in place.

**解说（中文）：** 转置通常返回一个 view。它会在 Tensor 元数据中交换指定的
轴，因此对应的 shape 与 stride 项会一起交换，而底层存储保持不动。

**Correct Answer (English):** `y.shape` is `(4, 3)` and `y.stride()` is
`(1, 4)`. The operation does not rearrange or copy the stored values in this
case. It changes how logical indices map to the same storage.

**正确答案（中文）：** `y.shape` 是 `(4, 3)`，`y.stride()` 是 `(1, 4)`。
在这个例子中，转置不会重新排列或复制底层数据，而是改变逻辑索引映射到同一
底层存储的方式。

### 3. Testing contiguity after transposition / 判断转置后的连续性

**Question (English):** What do the two calls return, and why?

```python
print(x.is_contiguous())
print(y.is_contiguous())
```

**问题（中文）：** 下面两个调用分别返回什么？为什么？

```python
print(x.is_contiguous())
print(y.is_contiguous())
```

**Explanation (English):** In the default row-major memory format, adjacent
logical elements along the final non-singleton dimension must be adjacent in
storage, and preceding strides must match the accumulated sizes of the later
dimensions. A valid tensor view does not have to be contiguous.

**解说（中文）：** 在默认的行优先内存格式中，最后一个非单例维度上的相邻逻辑
元素应在存储中相邻，更前面的 stride 则要与后续维度大小的累积结果匹配。一个
有效的 Tensor view 并不一定连续。

**Correct Answer (English):** `x.is_contiguous()` returns `True`, while
`y.is_contiguous()` returns `False`. A default contiguous tensor of shape
`(4, 3)` would normally have stride `(3, 1)`, but `y` has stride `(1, 4)`.

**正确答案（中文）：** `x.is_contiguous()` 返回 `True`，而
`y.is_contiguous()` 返回 `False`。形状为 `(4, 3)` 的默认连续 Tensor 通常
应具有 `(3, 1)` 的 stride，但 `y` 的 stride 是 `(1, 4)`。

### 4. Materializing a contiguous copy / 生成连续副本

**Question (English):** What are the shape and strides of `z`? Does it share
the same underlying storage with the non-contiguous `y`?

```python
z = y.contiguous()
```

**问题（中文）：** `z` 的 shape 和 stride 分别是什么？它是否与非连续的 `y`
共享同一底层存储？

```python
z = y.contiguous()
```

**Explanation (English):** `contiguous()` preserves the logical shape and
values. When the requested memory format is not already satisfied, it
allocates storage and copies the values into the required order. Calling it
on an already contiguous tensor normally requires no copy.

**解说（中文）：** `contiguous()` 会保留逻辑形状和值。如果当前布局不符合所需
内存格式，它就会分配新存储，并按所需顺序复制数据；如果输入已经连续，通常不
需要复制。

**Correct Answer (English):** `z.shape` is `(4, 3)` and `z.stride()` is
`(3, 1)`. Because `y` is non-contiguous here, `y.contiguous()` creates a new
contiguous storage allocation, so `z` and `y` do not share the same storage.

**正确答案（中文）：** `z.shape` 是 `(4, 3)`，`z.stride()` 是 `(3, 1)`。
因为这里的 `y` 不连续，所以 `y.contiguous()` 会创建新的连续存储，`z` 与
`y` 不共享同一底层存储。

### 5. `view()` versus `reshape()` on a non-contiguous tensor / 非连续 Tensor 上的 `view()` 与 `reshape()`

**Question (English):** Can both lines succeed? Which operation may copy
data?

```python
a = y.view(12)
b = y.reshape(12)
```

**问题（中文）：** 下面两行是否都能成功？哪一个操作可能复制数据？

```python
a = y.view(12)
b = y.reshape(12)
```

**Explanation (English):** `view()` requires the requested shape to be
compatible with the existing shape and strides and does not silently create a
contiguous copy. `reshape()` returns a view when possible and otherwise may
materialize a copy.

**解说（中文）：** `view()` 要求目标形状与现有 shape 和 stride 兼容，并且不会
静默创建连续副本。`reshape()` 会在可行时返回 view，否则可能实际生成一份
副本。

**Correct Answer (English):** `y.view(12)` raises an error because this
flattening is incompatible with `y`'s non-contiguous strides.
`y.reshape(12)` succeeds and copies in this case. Its values in logical order
are `[0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11]`.

**正确答案（中文）：** `y.view(12)` 会报错，因为这种展平方式与 `y` 的非连续
stride 不兼容。`y.reshape(12)` 可以成功，并且在这里会发生复制。按照逻辑顺序，
结果中的值为 `[0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11]`。

### 6. Strides produced by stepped slicing / 步进切片产生的 stride

**Question (English):** What are the shape, strides, and contiguity of `s`?

```python
x = torch.arange(12).reshape(3, 4)
s = x[:, ::2]
```

**问题（中文）：** `s` 的 shape、stride 和连续性分别是什么？

```python
x = torch.arange(12).reshape(3, 4)
s = x[:, ::2]
```

**Explanation (English):** A basic stepped slice is a view. Selecting every
second column changes the logical column count and multiplies the column
stride by two, but it does not close the gaps in storage or change the
original row stride.

**解说（中文）：** 基础步进切片会返回 view。每隔一列取一次会改变逻辑列数，并
把列 stride 乘以 2，但不会填补底层存储中的间隔，也不会改变原来的行 stride。

**Correct Answer (English):** `s.shape` is `(3, 2)`, `s.stride()` is `(4, 2)`,
and `s.is_contiguous()` is `False`. Its values are:

```text
[[ 0,  2],
 [ 4,  6],
 [ 8, 10]]
```

**正确答案（中文）：** `s.shape` 是 `(3, 2)`，`s.stride()` 是 `(4, 2)`，
`s.is_contiguous()` 是 `False`。它的值为：

```text
[[ 0,  2],
 [ 4,  6],
 [ 8, 10]]
```

### 7. Mapping a sliced index to storage / 将切片索引映射到底层存储

**Question (English):** For the tensor `s` with shape `(3, 2)` and stride
`(4, 2)`, what is the storage offset of `s[2, 1]`, which element of `x` does it
refer to, and what value does it return?

**问题（中文）：** 对于 shape 为 `(3, 2)`、stride 为 `(4, 2)` 的 Tensor
`s`，`s[2, 1]` 的底层存储偏移是多少？它对应 `x` 中的哪个元素？返回值是
多少？

**Explanation (English):** Each sliced-tensor index must be multiplied by
that tensor's own stride. The second logical index in `s` selects the second
retained column, which is original column `2`, not original column `1`.

**解说（中文）：** 切片 Tensor 的每个索引都应乘以该 Tensor 自己的 stride。
`s` 的第二个逻辑列索引选择的是保留下来的第二列，也就是原 Tensor 的第 `2`
列，而不是第 `1` 列。

**Correct Answer (English):** The offset is
`2 * 4 + 1 * 2 = 10`, assuming the zero storage offset used here. Therefore,
`s[2, 1]` maps to `x[2, 2]` and returns `10`.

**正确答案（中文）：** 在本例 storage offset 为 0 的前提下，底层偏移为
`2 * 4 + 1 * 2 = 10`。因此，`s[2, 1]` 对应 `x[2, 2]`，返回值为 `10`。

### 8. Zero strides created by expansion / 扩展操作产生的零 stride

**Question (English):** What are `b.shape` and `b.stride()`? What does a zero
stride mean?

```python
a = torch.tensor([10, 20, 30])
b = a.expand(4, 3)
```

**问题（中文）：** `b.shape` 和 `b.stride()` 分别是什么？stride 为 0 表示
什么？

```python
a = torch.tensor([10, 20, 30])
b = a.expand(4, 3)
```

**Explanation (English):** `expand()` represents broadcasting as a view
without allocating repeated copies. A zero stride means that changing the
logical index on that axis does not move to a different storage element.

**解说（中文）：** `expand()` 使用 view 表示 broadcasting，而不会真正分配
多份重复数据。零 stride 表示该轴的逻辑索引发生变化时，底层存储位置并不会
移动。

**Correct Answer (English):** `b.shape` is `(4, 3)` and `b.stride()` is
`(0, 1)`. All four logical rows alias the same three stored values. For
example, `b[0, 1]`, `b[1, 1]`, `b[2, 1]`, and `b[3, 1]` all refer to `a[1]`.
Because multiple logical elements can alias one location, in-place writes on
expanded views are unsafe or may be rejected by PyTorch.

**正确答案（中文）：** `b.shape` 是 `(4, 3)`，`b.stride()` 是 `(0, 1)`。
四个逻辑行都引用同样的三个底层值。例如，`b[0, 1]`、`b[1, 1]`、
`b[2, 1]` 和 `b[3, 1]` 都指向 `a[1]`。由于多个逻辑元素可能引用同一位置，
对 expanded view 进行原地写入是不安全的，也可能被 PyTorch 拒绝。

### 9. Reordering metadata with `permute()` / 使用 `permute()` 重排元数据

**Question (English):** What are `q.shape` and `q.stride()`?

```python
p = torch.zeros(2, 3, 4)
# p.shape    == (2, 3, 4)
# p.stride() == (12, 4, 1)

q = p.permute(2, 0, 1)
```

**问题（中文）：** `q.shape` 和 `q.stride()` 分别是什么？

```python
p = torch.zeros(2, 3, 4)
# p.shape    == (2, 3, 4)
# p.stride() == (12, 4, 1)

q = p.permute(2, 0, 1)
```

**Explanation (English):** `permute(2, 0, 1)` says that the new axes come
from old axes 2, 0, and 1, in that order. The shape and stride metadata must
both be reordered by exactly the same axis permutation.

**解说（中文）：** `permute(2, 0, 1)` 表示新 Tensor 的各轴依次来自原来的
第 2、0、1 轴。shape 和 stride 元数据都必须按照完全相同的轴顺序进行重排。

**Correct Answer (English):** `q.shape` is `(4, 2, 3)` and `q.stride()` is
`(1, 12, 4)`. `permute()` returns a metadata-only view here, so `q` shares
storage with `p` and is not contiguous in the default memory format.

**正确答案（中文）：** `q.shape` 是 `(4, 2, 3)`，`q.stride()` 是
`(1, 12, 4)`。这里的 `permute()` 返回一个只修改元数据的 view，所以 `q`
与 `p` 共享存储，并且在默认内存格式下不连续。

### 10. Layout assumptions in a custom CUDA kernel / 自定义 CUDA kernel 中的布局假设

**Question (English):** A two-dimensional CUDA kernel reads an input with the
formula below. Will it correctly read a non-contiguous tensor created by
`transpose(0, 1)`? If not, what are two valid solutions?

```cpp
offset = row * num_cols + col;
```

**问题（中文）：** 一个二维 CUDA kernel 使用下面的公式读取输入。当输入是由
`transpose(0, 1)` 得到的非连续 Tensor 时，它能否正确读取？如果不能，有哪两种
有效的解决办法？

```cpp
offset = row * num_cols + col;
```

**Explanation (English):** This formula hard-codes contiguous row-major
strides `(num_cols, 1)`. A transposed or sliced view can have different
strides even when its shape and values are logically valid.

**解说（中文）：** 这个公式把连续行优先布局的 stride `(num_cols, 1)` 写死了。
转置或切片 view 即使在逻辑上具有有效的形状和值，也可能使用完全不同的 stride。

**Correct Answer (English):** The kernel will not generally read the intended
elements. One solution is to require a contiguous input and call
`input.contiguous()` before launch, accepting a possible allocation and copy.
The other is to make the kernel stride-aware and calculate, for example,
`row * stride_row + col * stride_col`; if addressing starts from the storage
base rather than the tensor's first logical element, the storage offset must
also be included. A contiguous-only operator should validate its layout
contract explicitly.

**正确答案（中文）：** 该 kernel 通常无法读取到预期元素。一种方法是要求输入
连续，并在 launch 前调用 `input.contiguous()`，同时接受可能发生的内存分配与
复制。另一种方法是让 kernel 支持 stride，例如使用
`row * stride_row + col * stride_col` 计算位置；如果地址计算从 storage 的
起始位置而不是 Tensor 的第一个逻辑元素开始，还必须加入 storage offset。只
支持连续输入的算子应显式检查其布局约束。

## Summary / 总结

**English:** Shape describes the logical lengths of tensor axes; it does not
fully describe memory layout. Strides and the storage offset define how
indices map to storage. Operations such as `transpose()`, `permute()`, basic
slicing, and `expand()` can create inexpensive views with unusual or zero
strides. Such views remain logically valid but may be non-contiguous.
`contiguous()` materializes the requested layout when necessary, `view()`
requires stride compatibility, and `reshape()` may copy. Custom CUDA code
must either enforce a contiguous-input contract or honor the supplied strides.

**中文：** shape 描述 Tensor 各逻辑轴的长度，但不能完整描述内存布局。stride
与 storage offset 共同决定索引如何映射到底层存储。`transpose()`、
`permute()`、基础切片和 `expand()` 等操作可以低成本创建具有特殊 stride 或零
stride 的 view；这些 view 在逻辑上仍然有效，但可能不连续。必要时，
`contiguous()` 会实际生成所需布局；`view()` 要求 stride 兼容；`reshape()`
则可能复制数据。自定义 CUDA 代码必须在“强制连续输入”和“正确处理输入
stride”之间选择一种明确策略。

## Common Mistakes / 常见错误

**English:**

- Deriving strides only from the current shape after a view operation.
- Assuming that a transposed tensor is automatically copied into contiguous
  order.
- Treating a sliced logical column index as the same column index in the
  original tensor.
- Assuming `expand()` allocates repeated data instead of creating zero-stride
  aliases.
- Treating `view()` and `reshape()` as identical operations.
- Using a row-major indexing formula in a CUDA kernel without checking the
  input layout.

**中文：**

- 在 view 操作后只根据当前 shape 推导 stride。
- 误以为转置会自动把数据复制为连续布局。
- 把切片后的逻辑列索引直接当作原 Tensor 中相同的列索引。
- 误以为 `expand()` 会分配重复数据，而不是创建零 stride 的别名。
- 把 `view()` 与 `reshape()` 当成完全相同的操作。
- CUDA kernel 未检查输入布局，就直接使用行优先索引公式。

## Next Steps / 下一步建议

**English:**

1. Run a small inspection program that prints `shape`, `stride()`,
   `storage_offset()`, and `is_contiguous()` after slicing, transposition,
   permutation, expansion, and `contiguous()`.
2. Verify aliasing by changing safe individual elements in views and observing
   which base-tensor elements change; avoid ambiguous overlapping in-place
   operations.
3. Benchmark a representative CUDA operation on contiguous and transposed
   inputs, measuring the cost of an explicit `contiguous()` copy separately.
4. Implement a small correctness exercise that compares a contiguous-only
   kernel with a stride-aware kernel against a PyTorch reference.
5. Continue with PyTorch CUDA execution and autograd fundamentals before
   starting a custom CUDA extension.

**中文：**

1. 编写一个小型观察程序，在切片、转置、维度重排、扩展和 `contiguous()` 后
   分别打印 `shape`、`stride()`、`storage_offset()` 与
   `is_contiguous()`。
2. 通过安全地修改 view 中的单个元素来验证别名关系，并观察基础 Tensor 中哪些
   元素发生变化；避免含义不明确的重叠原地操作。
3. 对连续输入和转置输入运行一个有代表性的 CUDA 运算，并单独测量显式
   `contiguous()` 复制的成本。
4. 完成一个小型 correctness 实验：分别实现仅支持连续布局和支持任意 stride
   的 kernel，并与 PyTorch 参考结果进行比较。
5. 在开始 custom CUDA extension 之前，继续学习 PyTorch CUDA 执行与 autograd
   基础。
