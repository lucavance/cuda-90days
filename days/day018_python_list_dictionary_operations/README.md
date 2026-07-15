# Day 018: Python List and Dictionary Operations / Python 列表与字典操作

Date / 日期: 2026-07-15

## Topic / 主题

**English:** Python list and dictionary operations: object binding, shallow and
deep copies, `append`, `extend`, dictionary updates, safe lookup, iteration,
counting, and processing nested data.

**中文：** Python 列表与字典操作：对象绑定、浅拷贝与深拷贝、`append`、
`extend`、字典更新、安全查询、遍历、计数以及嵌套数据处理。

## Goal / 目标

**English:** Build a practical mental model for mutable Python collections and
learn common patterns for processing structured experiment data in automation
scripts.

**中文：** 建立对 Python 可变集合的实用思维模型，并掌握在自动化脚本中处理
结构化实验数据的常见模式。

## 10 Concept Questions / 10 道概念题

### 1. Shared list object / 共享列表对象

**Question (English):** What does the following code print? What does `b = a`
mean?

**问题（中文）：** 下面的代码输出什么？`b = a` 表示什么？

```python
a = [1, 2, 3]
b = a
b.append(4)

print(a)
print(b)
```

**Explanation (English):** Assignment binds a name to an existing object. It
does not copy a mutable list automatically.

**解说（中文）：** 赋值操作会让名字绑定到已有对象，而不会自动复制可变列表。

**Correct Answer (English):** Both lines print `[1, 2, 3, 4]`. The names `a`
and `b` refer to the same list object, so mutating it through `b` is visible
through `a`.

**正确答案（中文）：** 两行都输出 `[1, 2, 3, 4]`。名字 `a` 和 `b` 指向同一个
列表对象，因此通过 `b` 修改对象后，通过 `a` 也能看到变化。

### 2. Copying the outer list / 复制外层列表

**Question (English):** What does this code print? How does `a.copy()` differ
from `b = a`?

**问题（中文）：** 这段代码输出什么？`a.copy()` 与 `b = a` 有什么区别？

```python
a = [1, 2, 3]
b = a.copy()
b.append(4)

print(a)
print(b)
```

**Explanation (English):** `list.copy()` creates a new outer list. Mutating
that outer list does not change the original outer list.

**解说（中文）：** `list.copy()` 会创建新的外层列表。修改这个外层列表不会改变
原来的外层列表。

**Correct Answer (English):** The output is `[1, 2, 3]` followed by
`[1, 2, 3, 4]`. `b` is bound to a new list object, while `b = a` would bind both
names to the same object.

**正确答案（中文）：** 先输出 `[1, 2, 3]`，再输出 `[1, 2, 3, 4]`。`b` 绑定到
一个新的列表对象；而 `b = a` 会让两个名字绑定到同一个对象。

### 3. Shallow copies and nested lists / 浅拷贝与嵌套列表

**Question (English):** Why does changing `b[0]` also affect `a`, even though
the outer list was copied?

**问题（中文）：** 虽然复制了外层列表，为什么修改 `b[0]` 仍会影响 `a`？

```python
a = [[1, 2], [3, 4]]
b = a.copy()
b[0].append(5)

print(a)
print(b)
```

**Explanation (English):** `list.copy()` is a shallow copy. It creates a new
outer list but reuses references to the nested objects.

**解说（中文）：** `list.copy()` 是浅拷贝。它会创建新的外层列表，但仍复用内部
嵌套对象的引用。

**Correct Answer (English):** Both lines print `[[1, 2, 5], [3, 4]]` because
`a[0]` and `b[0]` refer to the same inner list.

**正确答案（中文）：** 两行都输出 `[[1, 2, 5], [3, 4]]`，因为 `a[0]` 和
`b[0]` 指向同一个内部列表。

### 4. Deep copying nested data / 深拷贝嵌套数据

**Question (English):** What does the code print? How does `deepcopy` differ
from a shallow list copy?

**问题（中文）：** 代码输出什么？`deepcopy` 与列表浅拷贝有什么区别？

```python
import copy

a = [[1, 2], [3, 4]]
b = copy.deepcopy(a)
b[0].append(5)

print(a)
print(b)
```

**Explanation (English):** A deep copy recursively copies nested mutable
objects instead of only creating a new outer container.

**解说（中文）：** 深拷贝会递归复制内部的可变对象，而不是只创建一个新的外层
容器。

**Correct Answer (English):** The output is `[[1, 2], [3, 4]]` followed by
`[[1, 2, 5], [3, 4]]`. The inner lists are independent after `deepcopy`.

**正确答案（中文）：** 先输出 `[[1, 2], [3, 4]]`，再输出
`[[1, 2, 5], [3, 4]]`。经过 `deepcopy` 后，内部列表也彼此独立。

### 5. `append` versus `extend` / `append` 与 `extend`

**Question (English):** What do these two list operations produce? Explain the
difference between `append` and `extend`.

**问题（中文）：** 这两个列表操作分别产生什么结果？请解释 `append` 与
`extend` 的区别。

```python
a = [1, 2]
a.append([3, 4])

b = [1, 2]
b.extend([3, 4])

print(a)
print(b)
```

**Explanation (English):** `append(x)` adds `x` as one element. `extend(xs)`
iterates over `xs` and adds each element separately.

**解说（中文）：** `append(x)` 会把 `x` 作为一个元素加入列表；`extend(xs)` 会
遍历 `xs`，将其中的元素逐个加入列表。

**Correct Answer (English):** `a` is `[1, 2, [3, 4]]`, while `b` is
`[1, 2, 3, 4]`. Their lengths are three and four respectively.

**正确答案（中文）：** `a` 是 `[1, 2, [3, 4]]`，`b` 是 `[1, 2, 3, 4]`；它们
的长度分别为 3 和 4。

### 6. Updating and adding dictionary keys / 更新与添加字典键

**Question (English):** What does this code print? What does each assignment
do to the dictionary?

**问题（中文）：** 这段代码输出什么？两次赋值分别对字典执行了什么操作？

```python
person = {"name": "Luca", "age": 18}

person["age"] = 19
person["city"] = "Shanghai"

print(person)
```

**Explanation (English):** Assigning through an existing key updates its value.
Assigning through a missing key creates a new key-value pair.

**解说（中文）：** 通过已有键赋值会更新对应的值；通过不存在的键赋值会创建
新的键值对。

**Correct Answer (English):** The result is
`{"name": "Luca", "age": 19, "city": "Shanghai"}`. The first assignment
updates `age`, and the second adds `city`.

**正确答案（中文）：** 结果是
`{"name": "Luca", "age": 19, "city": "Shanghai"}`。第一次赋值更新
`age`，第二次赋值添加 `city`。

### 7. Safe dictionary lookup / 安全查询字典

**Question (English):** What happens on each line when the `age` key is
missing?

**问题（中文）：** 当字典缺少 `age` 键时，下面每一行分别会发生什么？

```python
person = {"name": "Luca"}

print(person.get("age"))
print(person.get("age", 0))
print(person["age"])
```

**Explanation (English):** `dict.get` can return a default for a missing key,
while bracket lookup requires the key to exist.

**解说（中文）：** `dict.get` 可以在键不存在时返回默认值，而方括号查询要求该键
必须存在。

**Correct Answer (English):** The first line prints `None`, the second prints
`0`, and the third raises `KeyError: 'age'`. Execution stops at the exception
unless it is handled.

**正确答案（中文）：** 第一行输出 `None`，第二行输出 `0`，第三行抛出
`KeyError: 'age'`。如果没有处理异常，程序会在这里停止。

### 8. Iterating over dictionary items / 遍历字典键值对

**Question (English):** What does `scores.items()` provide on each iteration,
and what do `name` and `score` represent?

**问题（中文）：** `scores.items()` 每次迭代提供什么？`name` 和 `score` 分别
表示什么？

```python
scores = {
    "Alice": 90,
    "Bob": 80,
}

for name, score in scores.items():
    print(name, score)
```

**Explanation (English):** `dict.items()` provides key-value pairs. Sequence
unpacking binds each key to `name` and its value to `score`.

**解说（中文）：** `dict.items()` 提供键值对。序列解包会把每个键绑定到
`name`，把对应的值绑定到 `score`。

**Correct Answer (English):** The output is `Alice 90` and then `Bob 80`, each
on its own line. Python dictionaries preserve insertion order, and `print`
does not add quotation marks around string contents.

**正确答案（中文）：** 依次输出 `Alice 90` 和 `Bob 80`，每项各占一行。Python
字典保持插入顺序，并且 `print` 不会在字符串内容周围自动添加引号。

### 9. Counting with a dictionary / 使用字典计数

**Question (English):** What dictionary does this loop build? What happens on
the first and second occurrences of `cuda`?

**问题（中文）：** 这个循环会构建出什么字典？第一次和第二次遇到 `cuda` 时分别
会发生什么？

```python
words = ["cuda", "python", "cuda", "rust", "cuda"]
counts = {}

for word in words:
    counts[word] = counts.get(word, 0) + 1

print(counts)
```

**Explanation (English):** A missing word starts from the default count zero.
Each occurrence reads the current count, adds one, and stores the result.

**解说（中文）：** 单词不存在时从默认计数 0 开始；每次出现都会读取当前计数、
加 1，再把结果写回字典。

**Correct Answer (English):** The result is
`{"cuda": 3, "python": 1, "rust": 1}`. The first `cuda` changes the default
zero to one; the second reads one and updates it to two.

**正确答案（中文）：** 结果是 `{"cuda": 3, "python": 1, "rust": 1}`。
第一次遇到 `cuda` 时把默认值 0 更新为 1；第二次读取已有值 1，并更新为 2。

### 10. Processing nested experiment data / 处理嵌套实验数据

**Question (English):** What does the code print? Why is `reduce` not added to
`passed_names`?

**问题（中文）：** 代码输出什么？为什么 `reduce` 不会被加入 `passed_names`？

```python
runs = [
    {"name": "vector_add", "passed": True},
    {"name": "transpose", "passed": False},
    {"name": "reduce"},
]

passed_names = []

for run in runs:
    if run.get("passed", False):
        passed_names.append(run["name"])

result = {
    "count": len(passed_names),
    "names": passed_names,
}

print(result)
```

**Explanation (English):** The loop combines safe dictionary lookup, a
condition, list mutation, nested indexing, and result aggregation. A missing
`passed` key is treated as false.

**解说（中文）：** 这个循环组合了安全字典查询、条件判断、列表修改、嵌套索引和
结果汇总。缺少 `passed` 键时会按假值处理。

**Correct Answer (English):** The output is
`{"count": 1, "names": ["vector_add"]}`. `transpose` has an explicit false
value, while `reduce` has no `passed` key, so `get("passed", False)` returns
the default `False`.

**正确答案（中文）：** 输出为
`{"count": 1, "names": ["vector_add"]}`。`transpose` 的值明确为假；
`reduce` 没有 `passed` 键，所以 `get("passed", False)` 返回默认值 `False`。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** Assignment can bind multiple names to one mutable list object.
  **中文：** 赋值可以让多个名字绑定到同一个可变列表对象。
- **English:** A shallow copy creates a new outer container but shares nested
  objects; a deep copy recursively copies nested mutable data.
  **中文：** 浅拷贝创建新的外层容器但共享嵌套对象；深拷贝会递归复制内部可变
  数据。
- **English:** `append` adds one object, whereas `extend` adds elements from an
  iterable one by one. **中文：** `append` 添加一个完整对象，而 `extend` 会将
  可迭代对象中的元素逐个加入。
- **English:** Dictionary assignment can update existing keys or add new keys.
  **中文：** 字典赋值既可以更新已有键，也可以添加新键。
- **English:** `get`, `items`, sequence unpacking, and counting are practical
  dictionary-processing patterns. **中文：** `get`、`items`、序列解包和计数是
  实用的字典处理模式。
- **English:** Lists and dictionaries can be combined to filter and summarize
  structured experiment records. **中文：** 列表与字典可以组合使用，以筛选和
  汇总结构化实验记录。

## Common Mistakes / 常见错误

- **English:** Calling a Python `list` an array in ordinary Python code.
  **中文：** 在普通 Python 代码中把 `list` 称为数组，而不是列表。
- **English:** Assuming `b = a` copies a list instead of sharing the same
  object. **中文：** 误以为 `b = a` 会复制列表，而不是共享同一个对象。
- **English:** Assuming `list.copy()` recursively copies nested lists.
  **中文：** 误以为 `list.copy()` 会递归复制嵌套列表。
- **English:** Expecting `append([3, 4])` to add `3` and `4` separately.
  **中文：** 误以为 `append([3, 4])` 会分别添加 `3` 和 `4`。
- **English:** Writing `null` instead of Python's `None`.
  **中文：** 使用 `null`，而不是 Python 中的 `None`。
- **English:** Calling dictionary keys fields, or forgetting that bracket
  lookup raises `KeyError` for a missing key. **中文：** 把字典键称为字段，或者
  忘记使用方括号查询缺失键会抛出 `KeyError`。
- **English:** Expecting `print` to display quotation marks around strings.
  **中文：** 误以为 `print` 会显示字符串两侧的引号。

## Next Step / 下一步

**English:** Study list comprehensions, dictionary comprehensions, tuples, and
sets, then use them to simplify filtering, deduplication, and aggregation in
small benchmark and experiment-management scripts.

**中文：** 接下来学习列表推导式、字典推导式、元组和集合，并用它们简化小型
benchmark 与实验管理脚本中的筛选、去重和聚合逻辑。
