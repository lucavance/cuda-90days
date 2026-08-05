# Day 027: Python Functions, Parameters, Scope, and Type Hints / Python 函数、参数、作用域与类型注解

Date / 日期: 2026-07-29

## Topic / 主题

**English:** Practical Python function design for experiment tooling: local
scope, positional and keyword arguments, default values, mutable-default
pitfalls, variable-length arguments, keyword-only parameters, tuple returns,
type hints, function objects, callbacks, and reusable batch-processing
functions.

**中文：** 面向实验工具的实用 Python 函数设计：局部作用域、位置参数与关键字
参数、默认值、可变默认参数陷阱、可变数量参数、仅限关键字参数、元组返回值、
类型注解、函数对象、回调函数以及可复用的批处理函数。

## Goal / 目标

**English:** Build an accurate model of how Python creates local bindings and
binds call arguments, then use that model to write reusable functions with safe
defaults and clear type contracts for benchmark-data processing.

**中文：** 建立一套准确的思维模型，理解 Python 如何创建局部绑定并完成调用参数
绑定，进而为 benchmark 数据处理编写具有安全默认值和清晰类型契约的可复用
函数。

## 10 Concept Questions / 10 个概念问题

### 1. Local scope and name shadowing / 局部作用域与名字遮蔽

**Question (English):** What do the two lines print? Do the two occurrences of
`x` represent the same binding, and why does calling `change()` not modify the
outer `x`?

```python
x = 10

def change():
    x = 20
    return x

result = change()

print(x)
print(result)
```

**问题（中文）：** 两行分别输出什么？函数内部和外部的 `x` 是同一个绑定吗？
为什么调用 `change()` 没有修改外部的 `x`？

```python
x = 10

def change():
    x = 20
    return x

result = change()

print(x)
print(result)
```

**Explanation (English):** Assignment to a name inside a function normally
creates a local binding. The local name can shadow an outer name without
rebinding or mutating the outer one.

**解说（中文）：** 在函数内部对名字赋值，通常会创建局部绑定。局部名字可以遮蔽
外部同名对象，而不会重新绑定或修改外部名字。

**Correct Answer (English):** The output is:

```text
10
20
```

The two `x` names are different bindings. `x = 20` makes `x` local to
`change`, so it shadows the outer `x`. Explicit declarations such as
`global` or `nonlocal` are required when a function truly needs to rebind a
name from another scope.

**正确答案（中文）：** 输出为：

```text
10
20
```

两个 `x` 是不同的绑定。`x = 20` 使 `x` 成为 `change` 的局部变量，因此它
只是遮蔽了外部 `x`。如果函数确实需要重新绑定其他作用域中的名字，就需要使用
`global` 或 `nonlocal` 等显式声明。

### 2. Positional, keyword, and default arguments / 位置参数、关键字参数与默认值

**Question (English):** What do the two calls print? Where does `ok` get its
value in the first call, and why may the keyword arguments in the second call
appear in a different order?

```python
def describe(kernel, ms, ok=True):
    return f"{kernel}: {ms} ms, ok={ok}"

print(describe("vec_add", 1.2))
print(describe(ms=2.5, kernel="transpose", ok=False))
```

**问题（中文）：** 两次调用分别输出什么？第一次调用中的 `ok` 从哪里获得值？
为什么第二次调用中的关键字参数可以改变书写顺序？

```python
def describe(kernel, ms, ok=True):
    return f"{kernel}: {ms} ms, ok={ok}"

print(describe("vec_add", 1.2))
print(describe(ms=2.5, kernel="transpose", ok=False))
```

**Explanation (English):** Positional arguments bind by position, keyword
arguments bind by parameter name, and a default value is used only when the
caller omits that parameter.

**解说（中文）：** 位置参数按照位置绑定，关键字参数按照形参名字绑定；只有调用方
省略某个参数时，该参数才使用默认值。

**Correct Answer (English):** The output is:

```text
vec_add: 1.2 ms, ok=True
transpose: 2.5 ms, ok=False
```

The first call binds `"vec_add"` and `1.2` positionally and uses the default
`ok=True`. The second call names every target parameter explicitly, so the
written order does not determine the binding.

**正确答案（中文）：** 输出为：

```text
vec_add: 1.2 ms, ok=True
transpose: 2.5 ms, ok=False
```

第一次调用按位置绑定 `"vec_add"` 和 `1.2`，并使用默认值 `ok=True`。第二次
调用显式写出了每个目标形参的名字，因此书写顺序不决定绑定关系。

### 3. Mutable default arguments / 可变默认参数

**Question (English):** What do the two calls print? Why does the second call
retain data from the first one, and how should the function be rewritten
safely?

```python
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags

print(add_tag("cuda"))
print(add_tag("python"))
```

**问题（中文）：** 两次调用分别输出什么？为什么第二次调用会保留第一次加入的
内容？应该怎样安全地改写这个函数？

```python
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags

print(add_tag("cuda"))
print(add_tag("python"))
```

**Explanation (English):** Default expressions are evaluated when the `def`
statement creates the function, not once per call. A mutable default object is
therefore reused whenever the caller omits that argument.

**解说（中文）：** 默认值表达式在 `def` 语句创建函数时求值，而不是每次调用时
重新求值。因此，只要调用方省略该参数，同一个可变默认对象就会被重复使用。

**Correct Answer (English):** The output is:

```text
['cuda']
['cuda', 'python']
```

Both calls mutate the same default list. Use an immutable sentinel and create
a fresh list inside the function:

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []

    tags.append(tag)
    return tags
```

Independent calls that omit `tags` now return `['cuda']` and `['python']`.

**正确答案（中文）：** 输出为：

```text
['cuda']
['cuda', 'python']
```

两次调用修改了同一个默认列表。应使用不可变的哨兵值，并在函数内部创建新列表：

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []

    tags.append(tag)
    return tags
```

现在，省略 `tags` 的两次独立调用分别返回 `['cuda']` 和 `['python']`。

### 4. Variable-length positional arguments / 可变数量的位置参数

**Question (English):** What does `*values` do? What are the type and contents
of `values` inside the function, and what does the program print?

```python
def total_ms(*values):
    print(type(values).__name__)
    return sum(values)

result = total_ms(1.0, 2.0, 3.5)
print(result)
```

**问题（中文）：** `*values` 起什么作用？函数内部 `values` 的类型和内容分别
是什么？程序会输出什么？

```python
def total_ms(*values):
    print(type(values).__name__)
    return sum(values)

result = total_ms(1.0, 2.0, 3.5)
print(result)
```

**Explanation (English):** A named `*parameter` gathers any remaining
positional arguments into a tuple. It does not create a list.

**解说（中文）：** 带名字的 `*parameter` 会把剩余位置参数收集到一个元组中，
而不是创建列表。

**Correct Answer (English):** Inside the function,
`values == (1.0, 2.0, 3.5)` and its type is `tuple`. The output is:

```text
tuple
6.5
```

**正确答案（中文）：** 在函数内部，`values == (1.0, 2.0, 3.5)`，其类型是
`tuple`。输出为：

```text
tuple
6.5
```

### 5. Variable-length keyword arguments / 可变数量的关键字参数

**Question (English):** What does `**options` do? What are the type and
contents of `options`, and would `configure("cuda", 10)` be a valid call?

```python
def configure(**options):
    print(type(options).__name__)
    print(options)

configure(device="cuda", repeats=10)
```

**问题（中文）：** `**options` 起什么作用？`options` 的类型和内容分别是什么？
`configure("cuda", 10)` 是否是合法调用？

```python
def configure(**options):
    print(type(options).__name__)
    print(options)

configure(device="cuda", repeats=10)
```

**Explanation (English):** A named `**parameter` gathers extra keyword
arguments into a dictionary. Argument binding is validated before Python enters
the function body.

**解说（中文）：** 带名字的 `**parameter` 会把额外关键字参数收集到字典中。
Python 会在进入函数体之前检查参数绑定是否合法。

**Correct Answer (English):** The output is:

```text
dict
{'device': 'cuda', 'repeats': 10}
```

`options` is a dictionary whose keys are the argument names. The call
`configure("cuda", 10)` raises `TypeError` because the signature accepts no
positional arguments; this is an argument-binding error, not a tuple-versus-dict
type mismatch.

**正确答案（中文）：** 输出为：

```text
dict
{'device': 'cuda', 'repeats': 10}
```

`options` 是以参数名为键的字典。`configure("cuda", 10)` 会抛出
`TypeError`，因为函数签名没有接收位置参数；这是参数绑定错误，而不是元组与
字典之间的类型冲突。

### 6. Keyword-only parameters / 仅限关键字参数

**Question (English):** What does the bare `*` mean? What does the first call
print, and can the second call succeed?

```python
def describe_run(kernel, *, device="cuda", repeats=10):
    return f"{kernel} on {device}, repeats={repeats}"

print(describe_run("vec_add", repeats=5))
describe_run("vec_add", "cpu", 5)
```

**问题（中文）：** 参数列表中单独的 `*` 表示什么？第一次调用会输出什么？
第二次调用能否成功？

```python
def describe_run(kernel, *, device="cuda", repeats=10):
    return f"{kernel} on {device}, repeats={repeats}"

print(describe_run("vec_add", repeats=5))
describe_run("vec_add", "cpu", 5)
```

**Explanation (English):** Unlike a named `*args` parameter, a bare `*` does
not receive or store values. It marks every following parameter as
keyword-only.

**解说（中文）：** 与带名字的 `*args` 参数不同，单独的 `*` 不接收或保存任何
值；它把后面的所有参数标记为仅限关键字参数。

**Correct Answer (English):** The first call prints:

```text
vec_add on cuda, repeats=5
```

Only `kernel` may be positional. The second call raises `TypeError` because
`device` and `repeats` were supplied positionally. A valid call is:

```python
describe_run("vec_add", device="cpu", repeats=5)
```

**正确答案（中文）：** 第一次调用输出：

```text
vec_add on cuda, repeats=5
```

只有 `kernel` 可以按位置传递。第二次调用会抛出 `TypeError`，因为 `device`
和 `repeats` 被作为位置参数传入。合法调用方式是：

```python
describe_run("vec_add", device="cpu", repeats=5)
```

### 7. Multiple return values and unpacking / 多返回值与解包

**Question (English):** What are the value and type of `result`? What does the
unpacking assignment do, and what does the program print?

```python
def parse_result(record):
    return record["kernel"], record["ms"]

result = parse_result({
    "kernel": "vec_add",
    "ms": 1.2,
})

kernel, ms = result

print(type(result).__name__)
print(kernel)
print(ms)
```

**问题（中文）：** `result` 的值和类型是什么？解包赋值执行了什么操作？程序会
输出什么？

```python
def parse_result(record):
    return record["kernel"], record["ms"]

result = parse_result({
    "kernel": "vec_add",
    "ms": 1.2,
})

kernel, ms = result

print(type(result).__name__)
print(kernel)
print(ms)
```

**Explanation (English):** `return a, b` constructs a two-element tuple.
Sequence unpacking binds each tuple element to the corresponding target name,
and the number of targets must match the number of elements.

**解说（中文）：** `return a, b` 会构造一个二元组。序列解包把每个元组元素
绑定到对应的目标名字，左侧目标数量必须与元素数量匹配。

**Correct Answer (English):** `result` is
`("vec_add", 1.2)`, and its type is `tuple`. The unpacking binds
`kernel = "vec_add"` and `ms = 1.2`. The output is:

```text
tuple
vec_add
1.2
```

**正确答案（中文）：** `result` 是 `("vec_add", 1.2)`，类型为 `tuple`。
解包后得到 `kernel = "vec_add"` 和 `ms = 1.2`。输出为：

```text
tuple
vec_add
1.2
```

### 8. Type hints and runtime behavior / 类型注解与运行时行为

**Question (English):** What do `ms: float` and `-> float` mean? What does the
program actually print, and does Python automatically enforce or convert values
based on these annotations?

```python
def double_ms(ms: float) -> float:
    return ms * 2

print(double_ms(1.5))
print(double_ms("1.5"))
```

**问题（中文）：** `ms: float` 和 `-> float` 分别表示什么？程序实际输出什么？
Python 是否会根据这些注解自动检查或转换值？

```python
def double_ms(ms: float) -> float:
    return ms * 2

print(double_ms(1.5))
print(double_ms("1.5"))
```

**Explanation (English):** Type hints describe an intended contract for
readers, IDEs, and static checkers. Standard Python execution does not use them
to cast arguments or enforce return types automatically.

**解说（中文）：** 类型注解为阅读者、IDE 和静态检查工具描述预期契约。标准
Python 运行时不会依据注解自动转换参数或强制检查返回类型。

**Correct Answer (English):** `ms: float` says that callers are expected to
provide a float, and `-> float` says that the function is expected to return a
float. The actual output is:

```text
3.0
1.51.5
```

The second argument remains a string. Multiplying a string by `2` repeats it,
so the function returns a `str` despite its annotation. Runtime validation or
explicit conversion must be written separately when required.

**正确答案（中文）：** `ms: float` 表示调用方预期传入浮点数，`-> float` 表示
函数预期返回浮点数。实际输出为：

```text
3.0
1.51.5
```

第二次调用中的参数仍然是字符串。字符串乘以 `2` 会重复两次，因此函数虽然带有
浮点返回注解，实际仍返回 `str`。需要运行时校验或显式转换时，必须另外编写相应
代码。

### 9. Function objects and callables / 函数对象与可调用对象

**Question (English):** Why is `seconds_to_ms` passed without parentheses?
What does `Callable[[float], float]` mean, and what does the program print?

```python
from collections.abc import Callable

def seconds_to_ms(value: float) -> float:
    return value * 1000

def transform(
    values: list[float],
    operation: Callable[[float], float],
) -> list[float]:
    return [operation(value) for value in values]

result = transform([0.001, 0.002], seconds_to_ms)
print(result)
```

**问题（中文）：** 为什么传入的是不带括号的 `seconds_to_ms`？
`Callable[[float], float]` 表示什么？程序会输出什么？

```python
from collections.abc import Callable

def seconds_to_ms(value: float) -> float:
    return value * 1000

def transform(
    values: list[float],
    operation: Callable[[float], float],
) -> list[float]:
    return [operation(value) for value in values]

result = transform([0.001, 0.002], seconds_to_ms)
print(result)
```

**Explanation (English):** Functions are objects and can be passed as values.
A function name without parentheses refers to the object; parentheses invoke
it. A callable is any object that can be called and is not necessarily a
closure.

**解说（中文）：** 函数也是对象，可以作为值传递。不带括号的函数名引用函数
对象，带括号则执行调用。可调用对象泛指任何能够被调用的对象，并不一定是闭包。

**Correct Answer (English):** `seconds_to_ms` passes the function object so
that `transform` can call it later for each value. Writing
`seconds_to_ms()` would invoke it immediately and, here, raise `TypeError`
because `value` is missing. `Callable[[float], float]` describes a callable
that accepts one float and returns one float. The output is:

```text
[1.0, 2.0]
```

`seconds_to_ms` is an ordinary top-level function, not a closure. A closure is
typically a nested function that retains bindings from an enclosing scope.

**正确答案（中文）：** `seconds_to_ms` 传递函数对象，使 `transform` 可以稍后
针对每个值调用它。如果写成 `seconds_to_ms()`，就会立即执行；在这里还会因为
缺少 `value` 而抛出 `TypeError`。`Callable[[float], float]` 表示接收一个
浮点数并返回一个浮点数的可调用对象。输出为：

```text
[1.0, 2.0]
```

`seconds_to_ms` 是普通的顶层函数，不是闭包。闭包通常是一个嵌套函数，并保留了
外层作用域中的绑定。

### 10. A reusable batch-processing function / 可复用的批处理函数

**Question (English):** Why must `transform` be passed by keyword, and what is
its default value? What does the shown call print? If `transform` is omitted,
what valid values are returned?

```python
from collections.abc import Callable

def get_ms(result):
    if "ms" not in result:
        raise KeyError("missing ms")

    value = result["ms"]

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("ms must be a number")

    if value < 0:
        raise ValueError("ms must be non-negative")

    return value

def identity(value: float) -> float:
    return value

def seconds_to_ms(value: float) -> float:
    return value * 1000

def collect_ms(
    records: list[dict],
    *,
    transform: Callable[[float], float] = identity,
) -> tuple[list[float], list[str]]:
    values = []
    errors = []

    for record in records:
        try:
            ms = get_ms(record)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(str(exc))
        else:
            values.append(transform(ms))

    return values, errors

records = [
    {"ms": 0.001},
    {"ms": -1.0},
    {"ms": 0.002},
]

values, errors = collect_ms(records, transform=seconds_to_ms)

print(values)
print(errors)
```

**问题（中文）：** 为什么 `transform` 必须通过关键字传递？它的默认值是什么？
当前调用会输出什么？如果省略 `transform`，返回的有效值会变成什么？

```python
from collections.abc import Callable

def get_ms(result):
    if "ms" not in result:
        raise KeyError("missing ms")

    value = result["ms"]

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("ms must be a number")

    if value < 0:
        raise ValueError("ms must be non-negative")

    return value

def identity(value: float) -> float:
    return value

def seconds_to_ms(value: float) -> float:
    return value * 1000

def collect_ms(
    records: list[dict],
    *,
    transform: Callable[[float], float] = identity,
) -> tuple[list[float], list[str]]:
    values = []
    errors = []

    for record in records:
        try:
            ms = get_ms(record)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(str(exc))
        else:
            values.append(transform(ms))

    return values, errors

records = [
    {"ms": 0.001},
    {"ms": -1.0},
    {"ms": 0.002},
]

values, errors = collect_ms(records, transform=seconds_to_ms)

print(values)
print(errors)
```

**Explanation (English):** The signature combines a keyword-only callback,
a function object as an immutable default, type-hint metadata, per-record
exception isolation, and tuple unpacking. The value appended to each list is
determined by the expression passed to `append`.

**解说（中文）：** 这个函数签名组合了仅限关键字的回调、作为不可变默认值的
函数对象、类型注解元数据、逐记录异常隔离以及元组解包。每个列表最终保存的内容
由传给 `append` 的表达式决定。

**Correct Answer (English):** The bare `*` makes `transform` keyword-only; it
does not collect a tuple. Its default is the function object `identity`. The
shown call prints:

```text
[1.0, 2.0]
['ms must be non-negative']
```

The valid seconds are converted to milliseconds. The invalid negative record
contributes `str(exc)`, so `errors` stores an error-message string rather than
the `ValueError` class or exception object. If `transform` is omitted,
`identity` leaves the valid values unchanged and `values` becomes
`[0.001, 0.002]`.

**正确答案（中文）：** 单独的 `*` 使 `transform` 成为仅限关键字参数，它不会
收集元组。默认值是函数对象 `identity`。当前调用输出：

```text
[1.0, 2.0]
['ms must be non-negative']
```

合法的秒数被转换为毫秒。无效负数记录执行 `str(exc)`，因此 `errors` 保存的是
错误消息字符串，而不是 `ValueError` 类或异常对象。如果省略 `transform`，
`identity` 会保持有效值不变，`values` 变为 `[0.001, 0.002]`。

## Summary / 总结

**English:** This session connected function definition, argument binding,
scope, callback execution, and return values into one practical model:

```text
define a function and its defaults
  -> bind positional and keyword arguments
  -> create local names
  -> validate or transform values
  -> call injected behavior when needed
  -> return a value or tuple with a documented type contract
```

The learner can now distinguish local shadowing from outer mutation, use
positional and keyword arguments, avoid mutable defaults, recognize the tuple
and dictionary produced by `*args` and `**kwargs`, declare keyword-only
configuration, unpack tuple returns, and pass functions as callbacks. Type
hints are understood as static metadata rather than automatic runtime
conversion.

Within the repository-specific Python tool-layer roadmap, completing this
topic raises estimated content coverage from about 41 percent to about
48 percent. This is curriculum exposure, not yet a measure of independent
implementation fluency.

**中文：** 本次学习把函数定义、参数绑定、作用域、回调执行和返回值连接成一套
实用模型：

```text
定义函数及其默认值
  -> 绑定位置参数和关键字参数
  -> 创建局部名字
  -> 校验或转换数据
  -> 在需要时调用注入的行为
  -> 返回具有明确类型契约的值或元组
```

现在已经能够区分局部遮蔽和外部修改，使用位置参数与关键字参数，避免可变默认值，
识别 `*args` 和 `**kwargs` 分别产生的元组与字典，声明仅限关键字的配置参数，
解包元组返回值，并把函数作为回调传递。也已经理解类型注解属于静态元数据，不会
在运行时自动转换数据。

按照本仓库的 Python 工具层学习路线，完成本主题后，估算的内容覆盖率从约 41%
提升到约 48%。这个数字表示课程内容接触程度，还不是独立实现熟练度。

## Common Mistakes / 常见错误

**English:**

- Saying a local variable overwrites an outer variable instead of recognizing
  name shadowing.
- Expecting a mutable default list to be created separately for every call.
- Treating the tuple produced by `*args` as a list.
- Assuming `**kwargs` can receive ordinary positional arguments.
- Confusing a bare `*` keyword-only separator with a named `*args` collector.
- Expecting type hints to enforce types or convert strings at runtime.
- Calling every passed function a closure instead of using the broader term
  callable.
- Confusing an error-message string stored by `str(exc)` with an exception
  class or exception object.

**中文：**

- 把局部变量描述为覆盖外部变量，而没有识别出名字遮蔽。
- 误以为可变默认列表会在每次调用时分别创建。
- 把 `*args` 生成的元组当作列表。
- 误以为 `**kwargs` 可以接收普通位置参数。
- 混淆仅限关键字的单独 `*` 分隔符与带名字的 `*args` 收集参数。
- 误以为类型注解会在运行时强制检查类型或转换字符串。
- 把所有被传递的函数都称为闭包，而没有使用更宽泛的可调用对象概念。
- 混淆 `str(exc)` 保存的错误消息字符串与异常类或异常对象。

## Next Steps / 下一步

**English:**

1. Learn modules, `import`, package boundaries, and
   `if __name__ == "__main__"`.
2. Use `dataclasses.dataclass` to represent validated benchmark records.
3. Refine container annotations such as `dict[str, object]` and learn optional
   and union types.
4. Run a static checker such as `mypy` or `pyright` on deliberately incorrect
   calls.
5. Write unit tests for mutable defaults, argument binding, callbacks, and the
   batch collector.

**中文：**

1. 学习模块、`import`、包边界以及 `if __name__ == "__main__"`。
2. 使用 `dataclasses.dataclass` 表示经过校验的 benchmark 记录。
3. 完善 `dict[str, object]` 等容器注解，并学习可选类型与联合类型。
4. 使用 `mypy` 或 `pyright` 等静态检查器检查故意写错的调用。
5. 为可变默认值、参数绑定、回调函数和批处理收集器编写单元测试。
