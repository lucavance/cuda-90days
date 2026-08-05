# Day 026: Python Exception Handling and Data Validation / Python 异常处理与数据校验

Date / 日期: 2026-07-28

## Topic / 主题

**English:** Practical Python exception handling and benchmark-data validation:
unhandled exceptions, precise `try`/`except` branches, `else`, `finally`,
explicit `raise`, exception objects, numeric type checks, batch recovery, and
robust JSON loading.

**中文：** 面向 benchmark 数据的实用 Python 异常处理与校验：未处理异常、
精确的 `try`/`except` 分支、`else`、`finally`、主动 `raise`、异常对象、
数值类型检查、批处理恢复以及可靠的 JSON 加载。

## Goal / 目标

**English:** Build a reliable control-flow model for failures and learn to
write small Python tools that reject invalid benchmark records without allowing
one missing, malformed, or semantically invalid input to terminate an entire
batch.

**中文：** 建立一套可靠的异常控制流模型，能够编写小型 Python 工具来拒绝无效
benchmark 记录，同时避免单个缺失、格式损坏或语义错误的输入终止整个批处理。

## 10 Concept Questions / 10 个概念问题

### 1. Unhandled exceptions / 未处理的异常

**Question (English):** Assume `missing.json` does not exist. Which exception
does the read operation raise? Is `"done"` printed? What happens if there is no
`try`/`except`?

```python
from pathlib import Path

text = Path("missing.json").read_text(encoding="utf-8")
print("done")
```

**问题（中文）：** 假设 `missing.json` 不存在，读取操作会抛出什么异常？
`"done"` 会不会打印？如果没有 `try`/`except`，程序接下来会怎样？

```python
from pathlib import Path

text = Path("missing.json").read_text(encoding="utf-8")
print("done")
```

**Explanation (English):** An exception interrupts the current execution path
at the failing expression. Assignment happens only after the right-hand side
finishes successfully.

**解说（中文）：** 异常会在失败的表达式处中断当前执行路径。只有右侧表达式成功
执行完毕后，赋值操作才会完成。

**Correct Answer (English):** The read raises `FileNotFoundError`. Because the
exception occurs before the next statement, `"done"` is not printed. If the
exception reaches the top level of the script without being handled, Python
prints a traceback and terminates the script. If `text` was not previously
defined, the failed assignment does not create it.

**正确答案（中文）：** 读取操作抛出 `FileNotFoundError`。异常发生在下一条语句
之前，因此不会打印 `"done"`。如果异常一直传播到脚本顶层而没有被处理，Python
会输出 traceback 并终止脚本。如果 `text` 原来没有定义，失败的赋值也不会创建
它。

### 2. Continuing after a handled exception / 处理异常后继续执行

**Question (English):** Assume `missing.json` does not exist. What does the
program print, and why can the final statement run?

```python
from pathlib import Path

try:
    text = Path("missing.json").read_text(encoding="utf-8")
except FileNotFoundError:
    print("file missing")

print("done")
```

**问题（中文）：** 假设 `missing.json` 不存在，程序会输出什么？为什么最后一条
语句仍然能够执行？

```python
from pathlib import Path

try:
    text = Path("missing.json").read_text(encoding="utf-8")
except FileNotFoundError:
    print("file missing")

print("done")
```

**Explanation (English):** A matching `except` handles the exception. After the
handler finishes, control continues after the complete `try`/`except` statement,
not from the failed line inside `try`.

**解说（中文）：** 匹配的 `except` 会处理异常。处理分支结束后，控制流从整个
`try`/`except` 结构之后继续，而不是回到 `try` 中失败的语句。

**Correct Answer (English):** The output is:

```text
file missing
done
```

`FileNotFoundError` matches the declared handler, so it no longer propagates.
The assignment to `text` still did not complete unless the handler explicitly
provides a fallback value.

**正确答案（中文）：** 输出为：

```text
file missing
done
```

`FileNotFoundError` 与声明的处理分支匹配，因此不会继续向外传播。除非处理分支
显式提供备用值，否则对 `text` 的赋值仍然没有完成。

### 3. Exception types must match / 异常类型必须匹配

**Question (English):** What exception does `json.loads()` raise here? Can the
`FileNotFoundError` handler catch it, and is `"done"` printed?

```python
import json

try:
    data = json.loads('{"kernel": }')
except FileNotFoundError:
    print("file missing")

print("done")
```

**问题（中文）：** 这里的 `json.loads()` 会抛出什么异常？
`FileNotFoundError` 分支能否捕获它？`"done"` 会不会打印？

```python
import json

try:
    data = json.loads('{"kernel": }')
except FileNotFoundError:
    print("file missing")

print("done")
```

**Explanation (English):** An `except` branch catches only compatible
exception types. A handler for an unrelated failure does not act as a general
fallback.

**解说（中文）：** `except` 分支只捕获类型兼容的异常。用于处理某一种错误的分支
不会自动成为所有错误的通用兜底。

**Correct Answer (English):** Invalid JSON raises
`json.JSONDecodeError`, which is a subclass of `ValueError`. It is not a
`FileNotFoundError`, so the shown handler does not catch it. The uncaught
exception prevents `"done"` from being printed and propagates toward the
caller or top level.

**正确答案（中文）：** 无效 JSON 会抛出 `json.JSONDecodeError`，它是
`ValueError` 的子类。它不是 `FileNotFoundError`，因此这里的处理分支无法捕获
它。未捕获的异常使 `"done"` 无法打印，并继续向调用方或脚本顶层传播。

### 4. Multiple handlers and exception objects / 多个处理分支与异常对象

**Question (English):** Assume `result.json` exists but contains the invalid
JSON `{"kernel": }`. Which handler runs? What does `exc` represent, and what is
printed?

```python
import json
from pathlib import Path

try:
    with Path("result.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("file missing")
except json.JSONDecodeError as exc:
    print("invalid JSON")
    print(type(exc).__name__)

print("finished")
```

**问题（中文）：** 假设 `result.json` 存在，但内容是无效 JSON
`{"kernel": }`。哪个异常分支会执行？`exc` 表示什么？程序会输出什么？

```python
import json
from pathlib import Path

try:
    with Path("result.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("file missing")
except json.JSONDecodeError as exc:
    print("invalid JSON")
    print(type(exc).__name__)

print("finished")
```

**Explanation (English):** `as exc` binds the raised exception instance, not
the exception class. The instance carries details such as the message and, for
`JSONDecodeError`, line and column information.

**解说（中文）：** `as exc` 绑定的是被抛出的异常实例，而不是异常类。异常实例
保存了错误消息；对于 `JSONDecodeError`，其中还包括行号和列号等信息。

**Correct Answer (English):** The `json.JSONDecodeError` handler runs. `exc`
is the caught exception object, and the output is:

```text
invalid JSON
JSONDecodeError
finished
```

Because the matching branch handles the exception, execution continues after
the complete exception-handling structure.

**正确答案（中文）：** `json.JSONDecodeError` 分支会执行。`exc` 是捕获到的异常
对象，输出为：

```text
invalid JSON
JSONDecodeError
finished
```

由于匹配的分支已经处理异常，程序会在整个异常处理结构之后继续执行。

### 5. The `else` branch / `else` 分支

**Question (English):** When does `else` run, what does this program print, and
would `else` run if the JSON were invalid?

```python
import json

try:
    data = json.loads('{"ms": 1.2}')
except json.JSONDecodeError:
    print("invalid JSON")
else:
    print("loaded", data["ms"])

print("finished")
```

**问题（中文）：** `else` 在什么条件下执行？这段程序会输出什么？如果 JSON
无效，`else` 是否还会执行？

```python
import json

try:
    data = json.loads('{"ms": 1.2}')
except json.JSONDecodeError:
    print("invalid JSON")
else:
    print("loaded", data["ms"])

print("finished")
```

**Explanation (English):** The `else` suite runs only when the `try` suite
finishes without raising an exception. It is useful for success-only work and
keeps the protected `try` region narrow.

**解说（中文）：** 只有 `try` 代码块没有抛出异常时，`else` 才会执行。它适合
放置仅在成功时执行的逻辑，并让 `try` 所保护的范围保持精确。

**Correct Answer (English):** The JSON is valid, so `else` runs and the output
is:

```text
loaded 1.2
finished
```

`print` inserts a space between its two arguments. If parsing raised
`JSONDecodeError`, the `except` branch would print `invalid JSON`, `else` would
be skipped, and the final `finished` would still be printed.

**正确答案（中文）：** JSON 合法，因此 `else` 会执行，输出为：

```text
loaded 1.2
finished
```

`print` 会在两个参数之间加入空格。如果解析抛出 `JSONDecodeError`，则
`except` 分支打印 `invalid JSON`，`else` 被跳过，而最后的 `finished` 仍会
打印。

### 6. The `finally` branch / `finally` 分支

**Question (English):** What is the output order? When does `finally` run, and
what kind of work belongs there?

```python
try:
    print("start")
    raise ValueError("bad value")
except ValueError:
    print("handled")
finally:
    print("cleanup")

print("end")
```

**问题（中文）：** 输出顺序是什么？`finally` 在什么时候执行？其中通常适合
完成什么工作？

```python
try:
    print("start")
    raise ValueError("bad value")
except ValueError:
    print("handled")
finally:
    print("cleanup")

print("end")
```

**Explanation (English):** Under normal Python control flow, `finally` runs
when execution leaves the associated `try` statement, whether the protected
code succeeds, a matching handler runs, or an exception continues outward.

**解说（中文）：** 在正常的 Python 控制流中，当程序准备离开相关的 `try` 结构
时，`finally` 会执行；无论受保护代码成功、匹配的处理分支执行，还是异常继续
向外传播，都是如此。

**Correct Answer (English):** The output is:

```text
start
handled
cleanup
end
```

`finally` runs after the handler and before execution proceeds to `"end"`.
It is intended for required cleanup such as releasing a lock or closing a
manually managed connection. Files are usually better managed with `with`,
which provides deterministic cleanup automatically.

**正确答案（中文）：** 输出为：

```text
start
handled
cleanup
end
```

`finally` 在异常处理分支之后、执行 `"end"` 之前运行。它适合完成必须执行的
清理工作，例如释放锁或关闭手动管理的连接。文件通常更适合通过 `with` 管理，
由上下文管理器自动进行确定性的清理。

### 7. Validating data with `raise` / 使用 `raise` 校验数据

**Question (English):** For each independent call, what value is returned or
which exception is raised?

```python
def get_ms(result):
    if "ms" not in result:
        raise KeyError("missing ms")

    value = result["ms"]

    if not isinstance(value, (int, float)):
        raise TypeError("ms must be a number")

    if value < 0:
        raise ValueError("ms must be non-negative")

    return value


get_ms({})
get_ms({"ms": "1.2"})
get_ms({"ms": -0.5})
get_ms({"ms": 1.2})
```

**问题（中文）：** 下面每次调用相互独立。它们分别返回什么值，或者抛出什么
异常？

```python
def get_ms(result):
    if "ms" not in result:
        raise KeyError("missing ms")

    value = result["ms"]

    if not isinstance(value, (int, float)):
        raise TypeError("ms must be a number")

    if value < 0:
        raise ValueError("ms must be non-negative")

    return value


get_ms({})
get_ms({"ms": "1.2"})
get_ms({"ms": -0.5})
get_ms({"ms": 1.2})
```

**Explanation (English):** Validation should distinguish a missing field, an
incorrect value type, and an unacceptable value. `raise` rejects the record at
the point where its violated rule is known.

**解说（中文）：** 数据校验应区分字段缺失、值类型错误和取值不合法。`raise`
可以在明确知道记录违反哪条规则的位置直接拒绝该记录。

**Correct Answer (English):** The calls produce, in order:

1. `KeyError("missing ms")` because the key is absent.
2. `TypeError("ms must be a number")` because `"1.2"` is a string; the
   function performs no implicit conversion.
3. `ValueError("ms must be non-negative")` because the numeric value is
   negative.
4. The float `1.2`, because it passes every check.

**正确答案（中文）：** 四次调用依次得到：

1. `KeyError("missing ms")`，因为缺少该键。
2. `TypeError("ms must be a number")`，因为 `"1.2"` 是字符串；函数不会
   隐式转换它。
3. `ValueError("ms must be non-negative")`，因为数值小于零。
4. 返回浮点数 `1.2`，因为它通过了所有检查。

### 8. Booleans in numeric validation / 数值校验中的布尔值

**Question (English):** Using the original `get_ms()`, what do these lines
print? Should `True` be a valid benchmark duration, and how can the type check
accept `int` and `float` while rejecting `bool`?

```python
print(isinstance(True, (int, float)))
print(get_ms({"ms": True}))
```

**问题（中文）：** 使用原始的 `get_ms()`，下面两行分别输出什么？`True` 是否
应该成为合法的 benchmark 耗时？怎样让类型检查接受 `int` 和 `float`，同时
拒绝 `bool`？

```python
print(isinstance(True, (int, float)))
print(get_ms({"ms": True}))
```

**Explanation (English):** In Python, `bool` is a subclass of `int`. A broad
numeric `isinstance` check therefore accepts booleans even when the application
domain should reject them.

**解说（中文）：** 在 Python 中，`bool` 是 `int` 的子类。因此宽泛的数值
`isinstance` 检查会接受布尔值，即使业务语义要求拒绝它们。

**Correct Answer (English):** Both lines print `True`. The type check succeeds,
`True < 0` is false, and the function returns the original boolean. A boolean
should not represent elapsed milliseconds. One explicit fix is:

```python
if isinstance(value, bool) or not isinstance(value, (int, float)):
    raise TypeError("ms must be a number")
```

For an exact built-in-type policy, another option is
`type(value) not in (int, float)`, which also rejects subclasses.

**正确答案（中文）：** 两行都输出 `True`。类型检查成功，`True < 0` 为假，函数
最终返回原始布尔值。布尔值不应表示毫秒耗时。一种明确的修复方式是：

```python
if isinstance(value, bool) or not isinstance(value, (int, float)):
    raise TypeError("ms must be a number")
```

如果策略要求只接受精确的内置类型，也可以使用
`type(value) not in (int, float)`；这种写法也会拒绝子类。

### 9. Recovering during batch processing / 批处理中的异常恢复

**Question (English):** Using the corrected `get_ms()`, what does this program
print? Why does one invalid record not terminate the loop, and what does the
tuple after `except` mean?

```python
records = [
    {"ms": 1.2},
    {"ms": -0.5},
    {"ms": "2.0"},
]

valid = []

for record in records:
    try:
        valid.append(get_ms(record))
    except (KeyError, TypeError, ValueError) as exc:
        print(type(exc).__name__)

print(valid)
```

**问题（中文）：** 使用修正后的 `get_ms()`，这段程序会输出什么？为什么单个
无效记录不会终止循环？`except` 后面的异常类型元组表示什么？

```python
records = [
    {"ms": 1.2},
    {"ms": -0.5},
    {"ms": "2.0"},
]

valid = []

for record in records:
    try:
        valid.append(get_ms(record))
    except (KeyError, TypeError, ValueError) as exc:
        print(type(exc).__name__)

print(valid)
```

**Explanation (English):** Placing exception handling inside the loop isolates
each record. The tuple means that one handler accepts any one of the listed
exception types.

**解说（中文）：** 把异常处理放在循环内部，可以隔离每一条记录。异常类型元组
表示同一个处理分支可以接受其中任意一种异常。

**Correct Answer (English):** The output is:

```text
ValueError
TypeError
[1.2]
```

The first record contributes the return value `1.2`. Each later error is
handled during its own iteration, after which the loop proceeds to the next
record. `valid.append(get_ms(record))` stores the function's returned number,
not the original dictionary.

**正确答案（中文）：** 输出为：

```text
ValueError
TypeError
[1.2]
```

第一条记录把返回值 `1.2` 加入列表。后面每个错误都在各自的迭代中被处理，随后
循环进入下一条记录。`valid.append(get_ms(record))` 保存的是函数返回的数值，
不是原始字典。

### 10. A complete loading and validation flow / 完整的加载与校验流程

**Question (English):** What tuple does the function return when the file is
missing, contains `{"ms": }`, contains `{"ms": -1.0}`, or contains
`{"ms": 2.5}`? Why must the `JSONDecodeError` handler appear before the tuple
that includes `ValueError`?

```python
import json
from pathlib import Path

def load_benchmark_result(path):
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            result = json.load(f)

        ms = get_ms(result)

    except FileNotFoundError:
        return None, "file missing"
    except json.JSONDecodeError:
        return None, "invalid JSON"
    except (KeyError, TypeError, ValueError) as exc:
        return None, f"invalid data: {exc}"
    else:
        return ms, None
```

**问题（中文）：** 当文件不存在、内容为 `{"ms": }`、内容为
`{"ms": -1.0}` 或内容为 `{"ms": 2.5}` 时，函数分别返回什么元组？为什么
`JSONDecodeError` 分支必须放在包含 `ValueError` 的异常元组之前？

```python
import json
from pathlib import Path

def load_benchmark_result(path):
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            result = json.load(f)

        ms = get_ms(result)

    except FileNotFoundError:
        return None, "file missing"
    except json.JSONDecodeError:
        return None, "invalid JSON"
    except (KeyError, TypeError, ValueError) as exc:
        return None, f"invalid data: {exc}"
    else:
        return ms, None
```

**Explanation (English):** A robust loader separates filesystem errors, syntax
errors, semantic validation errors, and success. Exception handlers are tested
from top to bottom, so subclass-specific handlers must precede handlers for
their parent classes.

**解说（中文）：** 可靠的加载函数会区分文件系统错误、语法错误、语义校验错误和
成功结果。异常分支从上到下匹配，因此针对子类的具体处理分支必须位于父类处理
分支之前。

**Correct Answer (English):** The four results are:

```python
(None, "file missing")
(None, "invalid JSON")
(None, "invalid data: ms must be non-negative")
(2.5, None)
```

`return a, b` constructs a two-element tuple. The f-string inserts the caught
exception object's message, not the `ValueError` class. Because
`json.JSONDecodeError` is a subclass of `ValueError`, placing the broad tuple
first would catch malformed JSON there and prevent the more precise
`"invalid JSON"` response.

**正确答案（中文）：** 四种结果分别为：

```python
(None, "file missing")
(None, "invalid JSON")
(None, "invalid data: ms must be non-negative")
(2.5, None)
```

`return a, b` 会构造一个二元组。f-string 插入的是捕获到的异常对象的消息，而
不是 `ValueError` 类。由于 `json.JSONDecodeError` 是 `ValueError` 的子类，
如果宽泛的异常元组在前，它就会提前捕获格式损坏的 JSON，使函数无法返回更精确
的 `"invalid JSON"`。

## Summary / 总结

**English:** This session established a practical failure-handling workflow:

```text
perform a narrow operation
  -> catch the most specific expected exception
  -> validate structure, type, and value
  -> raise a meaningful error at the violated rule
  -> isolate bad records inside a batch
  -> return either a valid result or an actionable failure reason
```

The learner can now predict handled and unhandled exception flow, use
`try`/`except`/`else`/`finally`, inspect an exception instance, raise targeted
validation errors, and keep batch processing alive when an individual JSON
record fails.

**中文：** 本次学习建立了一套实用的失败处理流程：

```text
执行范围明确的操作
  -> 捕获最具体的预期异常
  -> 校验结构、类型和取值
  -> 在违反规则的位置抛出有意义的错误
  -> 在批处理中隔离坏记录
  -> 返回有效结果或可操作的失败原因
```

现在已经能够判断已处理和未处理异常的控制流，使用
`try`/`except`/`else`/`finally`，查看异常实例，主动抛出有针对性的校验错误，
并在单条 JSON 记录失败时让批处理继续运行。

## Common Mistakes / 常见错误

**English:**

- Describing invalid JSON without naming the precise
  `json.JSONDecodeError` type.
- Confusing an exception instance such as `exc` with an exception class such
  as `ValueError`.
- Forgetting that Python class names are case-sensitive, for example writing
  `Typeerror` instead of `TypeError`.
- Assuming a numeric-looking string such as `"1.2"` is converted implicitly.
- Forgetting that `bool` is a subclass of `int`, which makes a broad numeric
  `isinstance` check accept `True` and `False`.
- Confusing the value returned by a validator with the original record passed
  into it.
- Putting a broad parent-class handler before a more specific subclass handler.

**中文：**

- 只描述 JSON 格式错误，却没有准确说出 `json.JSONDecodeError` 类型。
- 混淆 `exc` 这类异常实例和 `ValueError` 这类异常类。
- 忘记 Python 类名区分大小写，例如把 `TypeError` 写成 `Typeerror`。
- 误以为 `"1.2"` 这类看起来像数字的字符串会被隐式转换。
- 忘记 `bool` 是 `int` 的子类，导致宽泛的数值 `isinstance` 检查接受
  `True` 和 `False`。
- 混淆校验函数的返回值与传入函数的原始记录。
- 把宽泛的父类异常分支放在更具体的子类异常分支之前。

## Next Steps / 下一步

**English:**

1. Implement a command-line tool that scans a directory of benchmark JSON
   files and reports valid values and per-file errors.
2. Add type hints to the loader and validator so their input and return
   contracts are explicit.
3. Represent validated benchmark records with `dataclasses.dataclass`.
4. Write unit tests for missing files, malformed JSON, missing keys, booleans,
   negative values, and valid values.
5. Learn `argparse` and `logging` to turn the validator into a reusable
   experiment tool.

**中文：**

1. 实现一个命令行工具，扫描目录中的 benchmark JSON 文件，并报告有效数值和
   每个文件的错误。
2. 为加载器和校验函数添加类型注解，使输入与返回契约更加明确。
3. 使用 `dataclasses.dataclass` 表示通过校验的 benchmark 记录。
4. 为文件缺失、JSON 损坏、键缺失、布尔值、负数和合法值编写单元测试。
5. 学习 `argparse` 和 `logging`，把校验器发展为可复用的实验工具。
