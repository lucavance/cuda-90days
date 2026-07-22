# Day 022: Python Comprehensions, Tuples, and Sets / Python 推导式、元组与集合

Date / 日期: 2026-07-22

## Topic / 主题

**English:** Python list and dictionary comprehensions, tuples, sequence
unpacking, sets, set operations, and set comprehensions for filtering,
deduplication, and aggregation in small benchmark and experiment-management
scripts.

**中文：** Python 列表与字典推导式、元组、序列解包、集合、集合运算以及集合
推导式，用于小型 benchmark 与实验管理脚本中的筛选、去重和聚合。

## Goal / 目标

**English:** Build a practical mental model for writing concise Python data
transforms over experiment records, using comprehensions, immutable tuples, and
sets without confusing their types or set-operation meanings.

**中文：** 建立一套实用思维模型，能够用推导式、不可变元组和集合简洁处理实验
记录，并分清各自类型与集合运算的含义。

## 10 Concept Questions / 10 道概念题

### 1. List comprehension versus explicit loop / 列表推导式与显式循环

**Question (English):** Do the following two snippets produce the same result?
Which style is usually preferred for a small experiment script, and why?

**问题（中文）：** 下面两段代码结果是否相同？更推荐哪一种写小型实验脚本？
为什么？

```python
names = []
for r in records:
    if r["status"] == "ok":
        names.append(r["name"])

names = [r["name"] for r in records if r["status"] == "ok"]
```

**Explanation (English):** Both forms filter and project fields. Prefer the
clearer form for the complexity of the logic.

**解说（中文）：** 两种写法都在做筛选和字段投影。应根据逻辑复杂度选择更清晰
的形式。

**Correct Answer (English):** Yes, they produce the same result. For simple
filter-and-map logic, the list comprehension is usually preferred because the
intent is visible in one expression. An explicit `for` loop is better when the
body needs multiple statements or step-through debugging.

**正确答案（中文）：** 结果相同。对简单的「筛选 + 取字段」，通常更推荐列表
推导式，意图一眼可见。当循环体需要多步逻辑或逐步调试时，再用显式 `for`。

### 2. Filtering with a list comprehension / 用列表推导式筛选

**Question (English):** What does the following code print, and what is the
type of `passed`?

**问题（中文）：** 下面代码输出什么？`passed` 的类型是什么？

```python
results = [
    {"kernel": "vec_add", "ok": True, "ms": 1.2},
    {"kernel": "transpose", "ok": False, "ms": 3.4},
    {"kernel": "softmax", "ok": True, "ms": 2.1},
]

passed = [r["kernel"] for r in results if r["ok"]]
print(passed)
print(type(passed))
```

**Explanation (English):** The `if` clause keeps only truthy `ok` rows, and the
expression selects the kernel name.

**解说（中文）：** `if` 子句只保留 `ok` 为真的记录，表达式取出 kernel 名。

**Correct Answer (English):** It prints `['vec_add', 'softmax']` and
`<class 'list'>`. `passed` is a list of kernel names that succeeded.

**正确答案（中文）：** 输出 `['vec_add', 'softmax']` 以及 `<class 'list'>`。
`passed` 是成功记录对应的 kernel 名列表。

### 3. Dictionary comprehension and key overwrite / 字典推导式与键覆盖

**Question (English):** What does the following code print? If two rows share
the same `"name"`, what happens to the later value?

**问题（中文）：** 下面代码输出什么？若两个元素的 `"name"` 相同，后写入的会
怎样？

```python
rows = [
    {"name": "vec_add", "ms": 1.2},
    {"name": "transpose", "ms": 3.4},
]

timing = {r["name"]: r["ms"] for r in rows}
print(timing)
print(timing["vec_add"])
```

**Explanation (English):** Dictionary keys are unique. Building a mapping from
records therefore has overwrite semantics on collision.

**解说（中文）：** 字典键唯一；从记录构建映射时，冲突键遵循后写覆盖语义。

**Correct Answer (English):** It prints `{'vec_add': 1.2, 'transpose': 3.4}` and
`1.2`. If two rows share the same name, the later row overwrites the earlier
value for that key.

**正确答案（中文）：** 输出 `{'vec_add': 1.2, 'transpose': 3.4}` 和 `1.2`。若
两个元素同名，后出现的值会覆盖先前的值。

### 4. Tuple immutability / 元组不可变

**Question (English):** What is an important difference between tuples and
lists? Which line below raises an error, and why? When are tuples a better fit
than lists in experiment records?

**问题（中文）：** 元组和列表有什么重要区别？下面代码哪一行会报错？为什么？
在实验记录里，什么时候更适合用元组而不是列表？

```python
point = (1.0, 2.0, 3.0)
print(point[0])
point[0] = 9.0
```

**Explanation (English):** Tuples support indexing for reads, but do not allow
item assignment.

**解说（中文）：** 元组支持按索引读取，但不允许对元素赋值。

**Correct Answer (English):** Lists are mutable; tuples are immutable. Only
`point[0] = 9.0` raises `TypeError`. `print(point[0])` is valid and prints
`1.0`. Prefer tuples for fixed records such as coordinates, shapes, multi-value
returns, or hashable composite dict keys.

**正确答案（中文）：** 列表可变，元组不可变。只有 `point[0] = 9.0` 会抛出
`TypeError`。`print(point[0])` 合法，输出 `1.0`。坐标、形状、多返回值，或需要
作为可哈希复合 dict 键的固定组合，更适合用元组。

### 5. Sequence unpacking / 序列解包

**Question (English):** What does the following code print? What is this pattern
called? What happens with `name, ms = row`?

**问题（中文）：** 下面代码输出什么？这种写法叫什么？若写成
`name, ms = row` 会怎样？

```python
row = ("vec_add", 1.2, True)
name, ms, ok = row
print(name)
print(ms)
print(ok)
```

**Explanation (English):** Unpack targets must match the number of values in the
iterable.

**解说（中文）：** 解包左侧名字数量必须与可迭代对象中的值数量一致。

**Correct Answer (English):** It prints:

```text
vec_add
1.2
True
```

This is sequence unpacking (often called tuple unpacking). `name, ms = row`
raises `ValueError` because there are too many values to unpack.

**正确答案（中文）：** 输出：

```text
vec_add
1.2
True
```

这种写法叫序列解包（常称元组解包）。`name, ms = row` 会抛出 `ValueError`，
因为值太多，无法解包到两个名字。

### 6. Sets for deduplication / 用集合去重

**Question (English):** Which experiment-data problem are sets best for? What
does the following code print? Name two important differences between sets and
lists.

**问题（中文）：** 集合最适合解决实验数据里的哪类问题？下面代码输出什么？
集合和列表相比，有哪两个重要差别？

```python
kernels = ["vec_add", "transpose", "vec_add", "softmax", "transpose"]
unique = set(kernels)
print(unique)
print(len(unique))
```

**Explanation (English):** Sets store unique elements and are unordered
collections.

**解说（中文）：** 集合保存不重复元素，并且是无序集合。

**Correct Answer (English):** Sets are best for deduplication and membership
tests. The printout contains the three names `vec_add`, `transpose`, and
`softmax` (order not guaranteed), and `len(unique)` is `3`. Compared with
lists: sets remove duplicates, and they are unordered (no reliable positional
indexing like `unique[0]`).

**正确答案（中文）：** 集合最适合去重和成员判断。打印结果包含 `vec_add`、
`transpose`、`softmax` 这三个名字（顺序不保证），`len(unique)` 为 `3`。与列表
相比：集合不重复，且无序（不能可靠地用 `unique[0]` 这类下标）。

### 7. Set operations for result comparison / 用集合运算对比结果

**Question (English):** What does the following code print? In one sentence each,
what do intersection, difference, and union mean for comparing CPU and GPU
kernel sets?

**问题（中文）：** 下面输出什么？用一句话说明交集、差集、并集分别表示什么
业务含义（都跑过的 / 只在 CPU 有的 / 全部出现过的）。

```python
cpu = {"vec_add", "transpose", "softmax"}
gpu = {"vec_add", "gemm", "softmax"}

print(cpu & gpu)
print(cpu - gpu)
print(cpu | gpu)
```

**Explanation (English):** `&` keeps items in both sets, `-` keeps items only in
the left set, and `|` keeps items from either set.

**解说（中文）：** `&` 保留两边都有的元素，`-` 保留只在左边的元素，`|` 保留
任意一边出现过的元素。

**Correct Answer (English):** Ignoring print order:

- `cpu & gpu` -> `{"vec_add", "softmax"}`: kernels run on both sides
- `cpu - gpu` -> `{"transpose"}`: kernels present only on CPU
- `cpu | gpu` -> `{"vec_add", "transpose", "softmax", "gemm"}`: all kernels that
  appeared on either side

**正确答案（中文）：** 忽略打印顺序：

- `cpu & gpu` -> `{"vec_add", "softmax"}`：两边都跑过的
- `cpu - gpu` -> `{"transpose"}`：只在 CPU 有的
- `cpu | gpu` -> `{"vec_add", "transpose", "softmax", "gemm"}`：全部出现过的

### 8. Set comprehension versus dict comprehension / 集合推导式与字典推导式

**Question (English):** What does the following code print? How do you distinguish
this `{... for ...}` form from a dictionary comprehension?

**问题（中文）：** 下面这段输出是什么？这里的 `{... for ...}` 和字典推导式怎么
区分？

```python
rows = [
    {"name": "vec_add", "backend": "cuda", "ms": 1.2},
    {"name": "vec_add", "backend": "cpu", "ms": 8.0},
    {"name": "transpose", "backend": "cuda", "ms": 3.4},
]

cuda_names = {r["name"] for r in rows if r["backend"] == "cuda"}
print(cuda_names)
print(type(cuda_names))
```

**Explanation (English):** Curly braces create a set when the comprehension has
only a value expression, and a dict when it has `key: value`.

**解说（中文）：** 花括号在只有值表达式时生成集合，在有 `键: 值` 时生成字典。

**Correct Answer (English):** It prints a set containing `vec_add` and
`transpose` (order not guaranteed) and `<class 'set'>`. A set comprehension looks
like `{x for ...}`; a dict comprehension looks like `{k: v for ...}`. Square
brackets `[]` make a list comprehension.

**正确答案（中文）：** 输出包含 `vec_add` 与 `transpose` 的集合（顺序不保证）
以及 `<class 'set'>`。集合推导式形如 `{x for ...}`；字典推导式形如
`{k: v for ...}`。方括号 `[]` 才是列表推导式。

### 9. Multiple filters in a comprehension / 推导式中的多重过滤

**Question (English):** Which of the following correctly keeps CUDA rows with
`ms < 2.0`? Why are the other forms wrong or less clear?

**问题（中文）：** 想筛出「cuda 且耗时 < 2.0 ms」的名字，下面哪种写法正确？
为什么另外两种不对或不清晰？

```python
# A
fast = [r["name"] for r in rows if r["backend"] == "cuda" and r["ms"] < 2.0]

# B
fast = [r["name"] for r in rows if r["backend"] == "cuda" if r["ms"] < 2.0]

# C
fast = [r["name"] if r["ms"] < 2.0 for r in rows if r["backend"] == "cuda"]
```

**Explanation (English):** Prefer combining predicates with `and`. Chained `if`
filters are legal but less readable. A bare ternary-style `x if cond` inside a
comprehension requires `else`.

**解说（中文）：** 更推荐用 `and` 组合条件。连续多个 `if` 过滤合法但更绕。
推导式里单独的 `x if cond` 三元写法必须带 `else`。

**Correct Answer (English):** A is the preferred correct form and yields
`["vec_add"]` for the example rows. B is also legal and produces the same result
via chained filters, but is usually less readable. C is a `SyntaxError` because
`name if cond` is a conditional expression and requires an `else`.

**正确答案（中文）：** A 是更推荐的正确写法，对本例结果为 `["vec_add"]`。B
也合法，通过连续 `if` 过滤得到相同结果，但通常更不清晰。C 是 `SyntaxError`，
因为 `name if cond` 是条件表达式，必须带 `else`。

### 10. End-to-end filter, unpack, and dedupe / 端到端筛选、解包与去重

**Question (English):** Using comprehensions, tuples, and sets, complete this
small task: from the records below, list all successful names (duplicates
allowed), then the unique successful kernel names. Which names belong in the
final set?

**问题（中文）：** 用推导式、元组、集合完成小任务：取出所有
`status == "ok"` 的 `name`（可重复），再得到成功跑通过的不重复 kernel 名。
最终集合里应有哪些名字？

```python
records = [
    ("vec_add", "ok", 1.2),
    ("transpose", "fail", 3.4),
    ("vec_add", "ok", 1.1),
    ("softmax", "ok", 2.0),
    ("transpose", "ok", 3.1),
]
```

**Explanation (English):** List comprehensions preserve duplicates; set
comprehensions collapse them. Unpacking can make the filters clearer.

**解说（中文）：** 列表推导式保留重复；集合推导式去重。解包可以让过滤条件更
易读。

**Correct Answer (English):** One clear solution is:

```python
ok_names = [name for name, status, _ in records if status == "ok"]
unique_ok = {name for name, status, _ in records if status == "ok"}
```

`ok_names` is `['vec_add', 'vec_add', 'softmax', 'transpose']`. The final set
contains `vec_add`, `softmax`, and `transpose` (print order not guaranteed).
Indexing with `r[0]` / `r[1]` also works, but unpacking is usually clearer.

**正确答案（中文）：** 一种清晰写法是：

```python
ok_names = [name for name, status, _ in records if status == "ok"]
unique_ok = {name for name, status, _ in records if status == "ok"}
```

`ok_names` 为 `['vec_add', 'vec_add', 'softmax', 'transpose']`。最终集合包含
`vec_add`、`softmax`、`transpose`（打印顺序不保证）。使用 `r[0]` / `r[1]`
也可以，但解包通常更清晰。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** List comprehensions concisely filter and project experiment
  records. **中文：** 列表推导式可简洁筛选并投影实验记录字段。
- **English:** Dictionary comprehensions build name-to-metric maps, with later
  keys overwriting earlier ones. **中文：** 字典推导式构建名字到指标的映射，
  后写键覆盖先写键。
- **English:** Tuples are immutable and support sequence unpacking.
  **中文：** 元组不可变，并支持序列解包。
- **English:** Sets deduplicate and support `&`, `-`, and `|` comparisons.
  **中文：** 集合可去重，并用 `&`、`-`、`|` 做对比。
- **English:** `{x for ...}` is a set comprehension; `{k: v for ...}` is a dict
  comprehension. **中文：** `{x for ...}` 是集合推导式；`{k: v for ...}` 是
  字典推导式。

### Common Mistakes / 常见错误

- **English:** Preferring an explicit loop for simple filter-and-map cases where
  a comprehension is clearer. **中文：** 在简单筛选投影场景仍偏好显式循环，
  而推导式更清晰。
- **English:** Thinking tuple indexing reads are illegal; only item assignment
  is. **中文：** 误以为元组按索引读取也非法；非法的是元素赋值。
- **English:** Swapping the business meanings of intersection and union.
  **中文：** 把交集与并集的业务含义对调。
- **English:** Confusing set comprehensions with lists or dicts.
  **中文：** 把集合推导式与列表或字典混淆。
- **English:** Assuming only `and` filters are legal; chained `if` filters also
  work but are usually less readable. **中文：** 误以为只有 `and` 过滤合法；
  连续 `if` 也可以，但通常更不清晰。

### Next Step / 下一步

**English:** Write a small script that reads JSON experiment records with
`pathlib` and `json`, filters and aggregates them with comprehensions and sets,
then writes a short summary for correctness or benchmark reporting.

**中文：** 编写一个小脚本：用 `pathlib` 与 `json` 读取实验记录，用推导式和
集合做筛选与聚合，再写出用于 correctness 或 benchmark 汇报的简短汇总。
