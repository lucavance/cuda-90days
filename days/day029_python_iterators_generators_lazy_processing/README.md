# Day 029: Python Iterators, Generators, and Lazy Data Processing / Python 迭代器、生成器与惰性数据处理

Date / 日期: 2026-08-01

## Topic / 主题

**English:** A concept-first introduction to Python iterables, iterators,
`iter()`, `next()`, `StopIteration`, generator functions, `yield`, generator
expressions, short-circuit consumers, `yield from`, and lazy data-processing
pipelines.

**中文：** 从概念出发学习 Python 的 iterable、iterator、`iter()`、
`next()`、`StopIteration`、生成器函数、`yield`、生成器表达式、短路消费函数、
`yield from` 与惰性数据处理流水线。

## Goal / 目标

**English:** Build a reliable mental model for how Python obtains and consumes
iterators, understand when generator code runs and where it pauses, and use
lazy iteration to process benchmark records without loading every result into
memory at once.

**中文：** 建立可靠的迭代思维模型：理解 Python 如何获取并消费迭代器，掌握
生成器代码何时开始执行以及在何处暂停，并能使用惰性迭代处理 benchmark 记录，
避免一次性把所有结果载入内存。

## Core Mental Model / 核心思维模型

**English:** An iterable can create an iterator. An iterator remembers its
current position and returns one item per `next()` call. It signals exhaustion
by raising `StopIteration`. A generator is a convenient way to implement such
a stateful iterator: execution begins on demand, pauses at each `yield`, and
resumes from that point on the next request.

**中文：** iterable 可以创建 iterator；iterator 会记住当前位置，并在每次
`next()` 调用时返回一个元素。元素耗尽后，它通过抛出 `StopIteration` 表示结束。
生成器是实现这种有状态迭代器的一种便捷方式：代码按需开始执行，在每个 `yield`
处暂停，并在下一次请求元素时从暂停位置继续。

## 10 Concept Questions / 10 道概念题

### 1. Iterable versus iterator / 可迭代对象与迭代器

**Question (English):** What do the two lines print? Do `values` and `it` play
the same role, and what does `iter()` do?

```python
values = [10, 20, 30]
it = iter(values)

print(next(it))
print(next(it))
```

**问题（中文）：** 两行分别输出什么？`values` 和 `it` 是否扮演相同角色？
`iter()` 做了什么？

```python
values = [10, 20, 30]
it = iter(values)

print(next(it))
print(next(it))
```

**Explanation (English):** A list is an iterable: it can provide an iterator.
The iterator is a separate stateful object that tracks which element should be
returned next and implements the iterator protocol, including `__next__()`.

**解说（中文）：** list 是 iterable，能够提供 iterator。iterator 是一个独立的
有状态对象，会记录下一次应返回哪个元素，并实现包括 `__next__()` 在内的迭代器
协议。

**Correct Answer (English):** The output is:

```text
10
20
```

`values` stores the data and is iterable. `it` is a `list_iterator` that
refers to the list and maintains a current position. Each `next(it)` call
returns the current item and advances that position. Calling `iter()` on a
list creates a new iterator; calling `iter()` on an iterator normally returns
that same iterator.

**正确答案（中文）：** 输出为：

```text
10
20
```

`values` 保存数据并且是 iterable；`it` 是引用该列表并维护当前位置的
`list_iterator`。每次调用 `next(it)` 都会返回当前位置的元素，并把位置向前
推进。对列表调用 `iter()` 会创建新的 iterator；对 iterator 自身调用 `iter()`
通常会返回该 iterator 自己。

### 2. Iterator exhaustion and `StopIteration` / 迭代器耗尽与 `StopIteration`

**Question (English):** Continuing with the iterator after `10` and `20` have
already been consumed, what happens on each line? Why does the iterator not
keep returning its final element or return a null value?

```python
print(next(it))
print(next(it))
```

**问题（中文）：** 接着使用已经消费过 `10` 和 `20` 的 iterator，下面两行分别
会发生什么？为什么 iterator 不会一直返回最后一个元素，也不会返回空值？

```python
print(next(it))
print(next(it))
```

**Explanation (English):** Python's iterator protocol uses the
`StopIteration` exception as an unambiguous end signal. Returning `None` would
not work as a general end marker because `None` may itself be a valid element
in the data.

**解说（中文）：** Python 的迭代器协议使用 `StopIteration` 异常作为明确的结束
信号。不能通用地使用 `None` 表示结束，因为 `None` 本身也可能是数据中的合法
元素。

**Correct Answer (English):** The first call returns and prints `30`. The
second call raises `StopIteration`, so its surrounding `print()` receives no
value. Python has `None`, not `null`, but exhaustion does not return `None` by
default. A caller that wants a fallback can provide one explicitly:

```python
next(it, None)
```

**正确答案（中文）：** 第一次调用返回并打印 `30`。第二次调用抛出
`StopIteration`，因此外层 `print()` 无法获得返回值。Python 使用 `None` 而
不是 `null`，但迭代耗尽时默认不会返回 `None`。如果调用方需要默认值，可以
显式提供：

```python
next(it, None)
```

### 3. How a `for` loop consumes an iterator / `for` 循环如何消费迭代器

**Question (English):** A `for` loop repeatedly obtains values from an
iterator. Why does the code finish normally instead of displaying a
`StopIteration` exception, and what work does `for` perform for the caller?

```python
for value in [10, 20, 30]:
    print(value)
```

**问题（中文）：** `for` 循环会不断从 iterator 获取值。为什么下面的代码能够
正常结束，而不会向用户显示 `StopIteration`？`for` 替调用方完成了哪些工作？

```python
for value in [10, 20, 30]:
    print(value)
```

**Explanation (English):** A general iterable may have no known length, so a
`for` loop does not need a separate boundary check. It obtains an iterator
once, repeatedly calls `next()`, and treats `StopIteration` as the normal loop
termination signal.

**解说（中文）：** 通用 iterable 可能没有已知长度，因此 `for` 循环不需要单独
进行边界检查。它先获取一次 iterator，然后反复调用 `next()`，并把
`StopIteration` 当作正常的循环结束信号。

**Correct Answer (English):** The behavior is conceptually similar to:

```python
iterator = iter([10, 20, 30])

while True:
    try:
        value = next(iterator)
    except StopIteration:
        break

    print(value)
```

The loop catches the exhaustion signal internally and exits without exposing
it as an error to the user.

**正确答案（中文）：** 其行为在概念上类似于：

```python
iterator = iter([10, 20, 30])

while True:
    try:
        value = next(iterator)
    except StopIteration:
        break

    print(value)
```

循环会在内部捕获耗尽信号并退出，而不会把它作为错误暴露给用户。

### 4. When a generator function starts running / 生成器函数何时开始运行

**Question (English):** What is the exact output order? Does calling
`numbers()` immediately execute the function body and print `start`?

```python
def numbers():
    print("start")
    yield 10
    yield 20

g = numbers()

print("created")
print(next(g))
```

**问题（中文）：** 完整输出顺序是什么？调用 `numbers()` 时是否会立即执行函数
体并打印 `start`？

```python
def numbers():
    print("start")
    yield 10
    yield 20

g = numbers()

print("created")
print(next(g))
```

**Explanation (English):** Calling a generator function creates a generator
object but does not begin executing its body. The first request for a value,
such as `next(g)`, starts execution and runs until the first `yield`.

**解说（中文）：** 调用生成器函数只会创建 generator 对象，并不会立即执行函数
体。第一次请求元素（例如调用 `next(g)`）时才会开始执行，并一直运行到第一个
`yield`。

**Correct Answer (English):** The output is:

```text
created
start
10
```

Creating `g` performs no body-side effects. `next(g)` then prints `start`,
pauses at `yield 10`, and returns `10`; the outer `print()` displays that
returned value.

**正确答案（中文）：** 输出为：

```text
created
start
10
```

创建 `g` 时不会产生函数体中的副作用。随后，`next(g)` 打印 `start`，在
`yield 10` 处暂停并返回 `10`，外层 `print()` 再显示该返回值。

### 5. Pausing and resuming at `yield` / 在 `yield` 处暂停与恢复

**Question (English):** What is the complete output? Is `C` printed by these
two `next()` calls, and what would happen on a third call?

```python
def counter():
    print("A")
    yield 1
    print("B")
    yield 2
    print("C")

g = counter()

print(next(g))
print(next(g))
```

**问题（中文）：** 完整输出是什么？这两次 `next()` 调用是否会打印 `C`？如果
再调用第三次，会发生什么？

```python
def counter():
    print("A")
    yield 1
    print("B")
    yield 2
    print("C")

g = counter()

print(next(g))
print(next(g))
```

**Explanation (English):** A generator preserves its local execution state at
each `yield`. The next request resumes immediately after the previous `yield`
and continues until another value is yielded or the function ends.

**解说（中文）：** generator 会在每个 `yield` 处保留局部执行状态。下一次请求
元素时，它会从上一个 `yield` 之后立即恢复，并继续运行，直到产生下一个值或
函数结束。

**Correct Answer (English):** The two calls produce:

```text
A
1
B
2
```

`C` is not printed yet because the generator is paused at `yield 2`. A third
`next(g)` resumes after that point, prints `C`, reaches the end of the
function, and raises `StopIteration` during that same call. The surrounding
`print(next(g))` therefore receives no normal return value.

**正确答案（中文）：** 两次调用产生：

```text
A
1
B
2
```

此时不会打印 `C`，因为 generator 暂停在 `yield 2`。第三次调用 `next(g)`
会从该位置之后恢复，打印 `C`，随后到达函数末尾，并在同一次调用中抛出
`StopIteration`。因此，外层 `print(next(g))` 不会获得正常返回值。

### 6. A generator is exhausted after one complete pass / 生成器完整消费后即耗尽

**Question (English):** What do the two lines print? Does the second
`list(g)` automatically restart the generator?

```python
def numbers():
    yield 1
    yield 2

g = numbers()

print(list(g))
print(list(g))
```

**问题（中文）：** 两行分别输出什么？第二次调用 `list(g)` 时，generator 是否
会自动从头开始？

```python
def numbers():
    yield 1
    yield 2

g = numbers()

print(list(g))
print(list(g))
```

**Explanation (English):** `list(g)` consumes values until the iterator raises
`StopIteration`. A generator object preserves its exhausted state and is not
automatically recreated or rewound.

**解说（中文）：** `list(g)` 会持续消费元素，直到 iterator 抛出
`StopIteration`。generator 对象会保留已经耗尽的状态，不会被自动重新创建或
倒回起点。

**Correct Answer (English):** The output is:

```text
[1, 2]
[]
```

The first conversion consumes both values. The second conversion uses the
same exhausted generator, so it receives no values. To iterate again, create
a new generator with `g = numbers()`.

**正确答案（中文）：** 输出为：

```text
[1, 2]
[]
```

第一次转换会消费两个值；第二次转换使用同一个已经耗尽的 generator，因此收集
不到任何值。若要重新迭代，需要通过 `g = numbers()` 创建新的 generator。

### 7. List comprehension versus generator expression / 列表推导式与生成器表达式

**Question (English):** What are the types of `a` and `b`? Which expression
immediately computes and stores all results, and which normally uses less
memory?

```python
a = [x * x for x in range(1_000_000)]
b = (x * x for x in range(1_000_000))
```

**问题（中文）：** `a` 和 `b` 分别是什么类型？哪一个表达式会立即计算并保存
全部结果？哪一个通常使用更少的内存？

```python
a = [x * x for x in range(1_000_000)]
b = (x * x for x in range(1_000_000))
```

**Explanation (English):** Square brackets create a list comprehension, which
materializes its results. Parentheses around a comprehension-like expression
create a generator expression, which computes items on demand. Python has no
direct tuple-comprehension syntax.

**解说（中文）：** 方括号会创建列表推导式并实际保存结果；圆括号包围的类似推导
表达式会创建生成器表达式，按需计算元素。Python 没有直接的元组推导式语法。

**Correct Answer (English):** `a` is a `list`; it eagerly computes and stores
one million results. `b` is a `generator`; it produces values lazily and
normally requires much less memory when consumed incrementally. To materialize
a tuple explicitly, write:

```python
tuple(x * x for x in range(10))
```

**正确答案（中文）：** `a` 是 `list`，会立即计算并保存一百万个结果；`b` 是
`generator`，按需产生值，在逐步消费时通常占用少得多的内存。如果需要实际生成
元组，应显式写成：

```python
tuple(x * x for x in range(10))
```

### 8. Lazy evaluation and short-circuiting with `any()` / `any()` 的惰性求值与短路

**Question (English):** What is the exact output? Is `4` passed to `check()`,
and does `any()` return the successful input value or a Boolean?

```python
def check(x):
    print(x)
    return x > 2

result = any(check(x) for x in [1, 2, 3, 4])
print(result)
```

**问题（中文）：** 完整输出是什么？`4` 是否会传入 `check()`？`any()` 返回的
是触发成功的输入值，还是布尔值？

```python
def check(x):
    print(x)
    return x > 2

result = any(check(x) for x in [1, 2, 3, 4])
print(result)
```

**Explanation (English):** `any()` consumes its iterable only until it finds a
truthy item. A generator expression supports that short-circuit behavior by
producing one result at a time instead of evaluating every input first.

**解说（中文）：** `any()` 只会消费 iterable，直到遇到第一个真值。生成器表达式
每次只产生一个结果，因此能够配合这种短路行为，而不必先计算所有输入。

**Correct Answer (English):** The output is:

```text
1
2
3
True
```

The generated Boolean values are `False`, `False`, and `True`. Once `True` is
found, `any()` stops, so `check(4)` is never called. `any()` always returns the
Boolean `True` or `False`, not the original truthy element.

**正确答案（中文）：** 输出为：

```text
1
2
3
True
```

依次产生的布尔值是 `False`、`False`、`True`。找到 `True` 后，`any()` 立即
停止，因此不会调用 `check(4)`。`any()` 始终返回布尔值 `True` 或 `False`，
而不是原始的真值元素。

### 9. Delegating iteration with `yield from` / 使用 `yield from` 委托迭代

**Question (English):** What does the program print, and what role does
`yield from first()` play?

```python
def first():
    yield 1
    yield 2

def combined():
    yield 0
    yield from first()
    yield 3

print(list(combined()))
```

**问题（中文）：** 程序输出什么？`yield from first()` 起什么作用？

```python
def first():
    yield 1
    yield 2

def combined():
    yield 0
    yield from first()
    yield 3

print(list(combined()))
```

**Explanation (English):** `yield from iterable` delegates iteration to
another iterable and forwards each of its yielded values. It avoids writing an
explicit forwarding loop and does not merge the generator objects themselves.

**解说（中文）：** `yield from iterable` 会把迭代工作委托给另一个 iterable，
并逐个转交它产生的值。这样可以避免显式编写转发循环；它并不是把 generator
对象本身合并起来。

**Correct Answer (English):** The output is one printed list:

```text
[0, 1, 2, 3]
```

`combined()` first yields `0`, delegates values `1` and `2` to `first()`, and
then resumes to yield `3`.

**正确答案（中文）：** 输出是一行列表：

```text
[0, 1, 2, 3]
```

`combined()` 先产生 `0`，再委托 `first()` 产生 `1` 和 `2`，之后恢复自身并
产生 `3`。

### 10. A lazy filtering pipeline / 惰性过滤流水线

**Question (English):** What is the exact output order? When is `start`
printed, and why do the two `list(g)` calls return different results?

```python
def positive_timings(lines):
    print("start")

    for line in lines:
        value = float(line)
        if value > 0:
            yield value

g = positive_timings(["1.2", "-1", "2.5"])

print("created")
print(list(g))
print(list(g))
```

**问题（中文）：** 完整输出顺序是什么？`start` 何时打印？为什么两次
`list(g)` 会得到不同的结果？

```python
def positive_timings(lines):
    print("start")

    for line in lines:
        value = float(line)
        if value > 0:
            yield value

g = positive_timings(["1.2", "-1", "2.5"])

print("created")
print(list(g))
print(list(g))
```

**Explanation (English):** Creating the generator does not parse any lines.
The first consumer starts the function and pulls input values one at a time.
Filtering can therefore be performed without building an intermediate list,
but the generator remains exhausted after that complete pass.

**解说（中文）：** 创建 generator 时不会解析任何输入行。第一个消费者会启动
函数，并逐个拉取输入值。因此，过滤过程不需要建立中间列表，但完整消费一次后，
该 generator 会保持耗尽状态。

**Correct Answer (English):** The output is:

```text
created
start
[1.2, 2.5]
[]
```

`start` is printed only when the first `list(g)` begins iteration. That call
parses all three strings, yields only the positive values, and exhausts `g`.
The second call uses the same exhausted generator and therefore produces an
empty list.

**正确答案（中文）：** 输出为：

```text
created
start
[1.2, 2.5]
[]
```

只有第一次 `list(g)` 开始迭代时，才会打印 `start`。该调用会解析三个字符串，
只产生其中的正数，并耗尽 `g`。第二次调用使用同一个已经耗尽的 generator，
因此得到空列表。

## Summary / 总结

**English:** An iterable supplies an iterator, while an iterator owns mutable
iteration state and produces one value per request. `StopIteration` is the
normal protocol-level end signal, and a `for` loop handles it automatically.
Generator functions make stateful iterators concise: their bodies run lazily,
pause at `yield`, and resume on demand. Generator expressions avoid eager
intermediate collections and work especially well with short-circuit
consumers such as `any()`. Generator objects are single-pass; creating a new
pass requires creating a new generator.

**中文：** iterable 能够提供 iterator，而 iterator 拥有可变的迭代状态，并在
每次请求时产生一个值。`StopIteration` 是协议层面的正常结束信号，`for` 循环会
自动处理它。生成器函数可以简洁地实现有状态 iterator：函数体惰性执行，在
`yield` 处暂停，并按需恢复。生成器表达式可以避免急切创建中间集合，并且特别
适合与 `any()` 等短路消费者结合使用。generator 对象只能单遍消费；若要重新
迭代，需要创建新的 generator。

## Common Mistakes / 常见错误

**English:**

- Expecting an exhausted iterator to return `None` or keep returning its last
  element instead of raising `StopIteration`.
- Assuming a `for` loop performs a length-based boundary check for every
  iterable.
- Expecting a generator function body to run when the generator object is
  created.
- Forgetting that a generator remains paused immediately after its last
  `yield` until another request resumes it and reaches the function end.
- Attempting to reuse an exhausted generator object.
- Mistaking a generator expression in parentheses for a tuple.
- Assuming `any()` returns the original truthy value instead of a Boolean.
- Confusing individually yielded values with the formatting produced by
  `print(list(generator))`.

**中文：**

- 误以为 iterator 耗尽后会返回 `None` 或持续返回最后一个元素，而不是抛出
  `StopIteration`。
- 误以为 `for` 会对每一种 iterable 都执行基于长度的越界检查。
- 误以为创建 generator 对象时就会执行生成器函数体。
- 忘记 generator 在最后一个 `yield` 之后仍处于暂停状态，需要再次请求元素才
  会恢复并到达函数末尾。
- 尝试重复使用已经耗尽的 generator 对象。
- 把圆括号中的生成器表达式误认为 tuple。
- 误以为 `any()` 会返回原始真值，而不是布尔值。
- 混淆逐个产生的值与 `print(list(generator))` 展示出的列表格式。

## Next Steps / 下一步建议

**English:**

1. Implement a small iterator class with `__iter__()` and `__next__()` to make
   the iterator protocol explicit.
2. Practice `enumerate()`, `zip()`, and selected `itertools` tools such as
   `islice()`, `chain()`, and `takewhile()`.
3. Build a generator pipeline that reads a benchmark log line by line, parses
   valid timings, filters failed runs, and computes an aggregate.
4. Compare a list-based pipeline with a generator-based pipeline using a large
   synthetic input and observe peak memory use.
5. Study generator cleanup and context-manager lifetimes before combining
   generators with open files or other external resources.

**中文：**

1. 使用 `__iter__()` 和 `__next__()` 实现一个小型 iterator 类，显式理解
   迭代器协议。
2. 练习 `enumerate()`、`zip()`，以及 `itertools` 中的 `islice()`、
   `chain()`、`takewhile()` 等工具。
3. 构建生成器流水线：逐行读取 benchmark 日志、解析有效 timing、过滤失败运行，
   并计算汇总结果。
4. 使用大型合成输入比较 list 流水线与 generator 流水线，并观察峰值内存占用。
5. 在把 generator 与打开的文件或其他外部资源结合之前，学习生成器清理与上下文
   管理器的生命周期。
