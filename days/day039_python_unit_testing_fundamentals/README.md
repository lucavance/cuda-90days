# Day 039: Python Unit Testing Fundamentals / Python 单元测试基础

Date / 日期: 2026-08-11

## Topic / 主题

**English:** Python unit testing with pytest: Arrange–Act–Assert, assertion
failures, test discovery, boundary analysis, expected exceptions,
parametrization, fixtures, temporary paths, monkeypatching, mock call behavior,
and balanced test-case design.

**中文：** 使用 pytest 进行 Python 单元测试：Arrange–Act–Assert、断言失败、测试
发现、边界分析、预期异常、参数化、fixture、临时路径、monkeypatch、mock 调用
行为以及均衡的测试用例设计。

## Goal / 目标

**English:** Learn to turn a function contract into isolated, repeatable tests
that cover successful behavior, boundaries, invalid inputs, and controlled
external dependencies, while producing useful failure diagnostics.

**中文：** 学会把函数契约转化为隔离且可重复的测试，覆盖正常行为、边界、非法
输入和受控外部依赖，并产生有用的失败诊断信息。

## Core Mental Model / 核心思维模型

**English:** A unit test prepares a known situation, performs one focused
action, and checks an observable result. Good tests control external state,
remain independent of execution order, and fail for one clear reason. Pytest
adds discovery, rich assertion reports, parametrization, fixtures, temporary
resources, and test doubles around ordinary Python functions and `assert`
statements.

**中文：** 单元测试先准备已知情境，再执行一个聚焦动作，并检查可观察结果。良好
测试会控制外部状态、不依赖执行顺序，并只因一个明确原因失败。Pytest 在普通
Python 函数与 `assert` 语句之上提供测试发现、丰富断言报告、参数化、fixture、
临时资源和测试替身等能力。

## 10 Concept Questions / 10 个概念问题

### 1. Arrange–Act–Assert structure / Arrange–Act–Assert 结构

**Question (English):** Does the following test pass? Which lines belong to
Arrange, Act, and Assert?

**问题（中文）：** 下面的测试能否通过？哪些代码分别属于 Arrange、Act 和
Assert？

```python
def add(left, right):
    return left + right


def test_add():
    left = 2
    right = 3

    result = add(left, right)

    assert result == 5
```

**Explanation (English):** Arrange–Act–Assert is an organizational pattern,
not special Python syntax. It separates setup, the behavior under test, and
verification so a reader can quickly identify the purpose of each line.

**解说（中文）：** Arrange–Act–Assert 是一种组织模式，而不是特殊 Python 语法。
它把准备、被测试行为和验证分开，使读者能够快速识别每行代码的目的。

**Correct Answer (English):** The test passes. Assigning `left` and `right` is
Arrange, calling `add` is Act, and `assert result == 5` is Assert. Small tests
may combine phases on fewer lines, but the conceptual separation remains
useful.

**正确答案（中文）：** 测试可以通过。给 `left` 和 `right` 赋值属于 Arrange，
调用 `add` 属于 Act，`assert result == 5` 属于 Assert。小型测试可以减少各阶段
所占行数，但这种概念分离仍然有用。

### 2. Assertion failure and test execution / 断言失败与测试执行

**Question (English):** What happens when the following test runs? Does the
final `print` execute, and how can the test be run with pytest?

**问题（中文）：** 下面的测试运行时会发生什么？最后的 `print` 是否执行？如何用
pytest 运行该测试？

```python
def add(left, right):
    return left + right


def test_add():
    result = add(2, 3)

    assert result == 6, f"expected 6, got {result}"

    print("finished")
```

**Explanation (English):** A false `assert` raises `AssertionError`
immediately, so later statements in the test do not run. Pytest discovers
appropriately named test files and functions, invokes them, and reports the
values involved in failed assertions.

**解说（中文）：** 条件为假的 `assert` 会立即抛出 `AssertionError`，因此测试中
后续语句不会执行。Pytest 会发现名称符合规则的测试文件和函数，调用它们，并报告
失败断言涉及的值。

**Correct Answer (English):** `add(2, 3)` returns `5`, so the assertion fails
with a message equivalent to `expected 6, got 5`; `print("finished")` is never
reached. A test file named `test_add.py` can be run with:

**正确答案（中文）：** `add(2, 3)` 返回 `5`，所以断言失败，并产生等价于
`expected 6, got 5` 的消息；`print("finished")` 不会执行。名为 `test_add.py`
的测试文件可以这样运行：

```bash
python -m pytest -q test_add.py
```

**English:** With uv and no existing project configuration, an isolated
environment can be created and used without activation:

**中文：** 使用 uv 且尚无项目配置时，可以在不激活环境的情况下创建并使用隔离
环境：

```bash
uv venv .venv
uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest -q test_add.py
```

**English:** Fixing the assertion to expect `5` makes the test pass. Running a
plain Python file only defines a test function unless something explicitly
calls it; pytest supplies discovery and invocation.

**中文：** 把断言期望修正为 `5` 后，测试可以通过。直接运行普通 Python 文件时，
测试函数通常只会被定义，除非有代码显式调用它；pytest 提供发现与调用过程。

### 3. Boundary-value analysis / 边界值分析

**Question (English):** Which minimal inputs test both sides of the boundary
at age 18? What result should each input produce?

**问题（中文）：** 哪些最少输入可以测试年龄 18 这一边界的两侧？每个输入应产生
什么结果？

```python
def is_adult(age):
    return age >= 18
```

**Explanation (English):** Boundary bugs commonly occur where a comparison
changes state. Values immediately below, exactly at, and sometimes immediately
above the boundary reveal off-by-one errors more effectively than an arbitrary
interior value.

**解说（中文）：** 边界 bug 常出现在比较结果改变的位置。紧邻边界下方、正好位于
边界以及有时紧邻边界上方的值，比任意内部值更容易暴露差一错误。

**Correct Answer (English):** The strict minimum is `17 -> False` and
`18 -> True`: one value immediately below the boundary and one exactly on it.
Adding `19 -> True` is useful confirmation immediately above the boundary,
although it is not required for the smallest two-case set.

**正确答案（中文）：** 严格最小集合是 `17 -> False` 与 `18 -> True`：一个值紧邻
边界下方，另一个正好位于边界。再加入 `19 -> True` 可以确认紧邻边界上方的
行为，但不是最小两用例集合的必需项。

### 4. Testing expected exceptions / 测试预期异常

**Question (English):** Does the following test pass? What does
`pytest.raises(ValueError)` verify, and what happens if no exception is raised?

**问题（中文）：** 下面的测试能否通过？`pytest.raises(ValueError)` 验证什么？
如果没有抛出异常会怎样？

```python
import pytest


def divide(total, count):
    if count == 0:
        raise ValueError("count must not be zero")

    return total / count


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

**Explanation (English):** An expected exception is part of a function's
observable contract. The `pytest.raises` context manager passes only when the
enclosed operation raises the requested exception type.

**解说（中文）：** 预期异常是函数可观察契约的一部分。只有代码块内的操作抛出所
请求的异常类型时，`pytest.raises` 上下文管理器才会通过。

**Correct Answer (English):** The test passes because `divide(10, 0)` raises
`ValueError`. If it raises nothing, pytest fails the test with a
did-not-raise report. A different exception type is not accepted and continues
as a test failure. The message can also be checked:

**正确答案（中文）：** 测试可以通过，因为 `divide(10, 0)` 抛出 `ValueError`。
如果没有抛出异常，pytest 会以“未抛出预期异常”的报告让测试失败；其他异常类型
不会被接受，也会导致测试失败。还可以检查错误消息：

```python
with pytest.raises(ValueError, match="count must not be zero"):
    divide(10, 0)
```

### 5. Parametrizing input and expected output / 参数化输入与预期输出

**Question (English):** How many test cases does pytest collect below? Which
arguments are passed each time, and what advantage does parametrization offer?

**问题（中文）：** Pytest 会从下面代码中收集多少个测试用例？每次分别传入哪些
参数？参数化有什么优势？

```python
import pytest


def is_adult(age):
    return age >= 18


@pytest.mark.parametrize(
    "age, expected",
    [
        (17, False),
        (18, True),
        (19, True),
    ],
)
def test_is_adult(age, expected):
    assert is_adult(age) is expected
```

**Explanation (English):** `pytest.mark.parametrize` creates a separate test
instance for each parameter set. The shared body expresses one rule while the
data table lists examples of that rule.

**解说（中文）：** `pytest.mark.parametrize` 会为每组参数创建独立测试实例。共享
测试体表达一条规则，数据表则列出该规则的多个例子。

**Correct Answer (English):** Pytest collects three cases with
`(age, expected)` equal to `(17, False)`, `(18, True)`, and `(19, True)`.
Parametrization avoids duplicating test logic, reports each dataset separately,
and makes new boundary cases easy to add. Parameter objects are passed as-is,
so mutable values are not automatically copied between cases.

**正确答案（中文）：** Pytest 收集三个用例，`(age, expected)` 分别为
`(17, False)`、`(18, True)` 和 `(19, True)`。参数化避免重复测试逻辑，同时让
每组数据独立报告，并便于添加新的边界用例。参数对象会原样传入，因此可变值不会
在用例之间自动复制。

### 6. Function-scoped fixture isolation / 函数级 fixture 隔离

**Question (English):** Do both tests pass? How many times does the fixture
run, and does mutation in the first test affect the second test?

**问题（中文）：** 两个测试能否都通过？Fixture 总共运行几次？第一个测试中的
修改是否会影响第二个测试？

```python
import pytest


@pytest.fixture
def sample_numbers():
    return [2, 3, 5]


def test_total(sample_numbers):
    sample_numbers.append(10)
    assert sum(sample_numbers) == 20


def test_original(sample_numbers):
    assert sample_numbers == [2, 3, 5]
```

**Explanation (English):** A test requests a fixture by declaring a parameter
with the fixture's name. The default fixture scope is `function`, so pytest
invokes the fixture separately for every requesting test.

**解说（中文）：** 测试通过声明与 fixture 同名的参数来请求该 fixture。Fixture
默认作用域是 `function`，因此 pytest 会为每个请求它的测试分别调用 fixture。

**Correct Answer (English):** Both tests pass and the fixture runs twice.
Each call returns a fresh list, so appending `10` in `test_total` does not
affect `test_original`. This isolation prevents order-dependent behavior.
A broader fixture scope would share one returned object for longer and would
require more care with mutation.

**正确答案（中文）：** 两个测试都能通过，fixture 共运行两次。每次调用都返回新
列表，因此 `test_total` 中追加 `10` 不会影响 `test_original`。这种隔离避免了
依赖执行顺序的行为。更宽的 fixture 作用域会在更长时间内共享同一个返回对象，
处理修改时需要更加谨慎。

### 7. Isolated filesystem testing with `tmp_path` / 使用 `tmp_path` 隔离文件系统测试

**Question (English):** Does the test pass? What type is `tmp_path`, what does
its concrete path look like, and why is it safer than a fixed shared filename?

**问题（中文）：** 测试能否通过？`tmp_path` 是什么类型？它的具体路径形式是什么？
为什么它比固定共享文件名更安全？

```python
def save_message(path, message):
    path.write_text(message, encoding="utf-8")


def test_save_message(tmp_path):
    target = tmp_path / "message.txt"

    save_message(target, "hello")

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello"
```

**Explanation (English):** Pytest's `tmp_path` fixture provides a unique
`pathlib.Path` directory for each test invocation. It avoids collisions with
parallel tests, stale files, and unrelated data in a shared location.

**解说（中文）：** Pytest 的 `tmp_path` fixture 为每次测试调用提供唯一的
`pathlib.Path` 目录。它可以避免并行测试、残留文件和共享位置中无关数据造成的
冲突。

**Correct Answer (English):** The test passes. On a typical Linux system, the
directory follows this shape:

**正确答案（中文）：** 测试可以通过。在典型 Linux 系统上，该目录采用以下形式：

```text
{temporary-root}/pytest-of-{user}/pytest-{run-number}/{test-name}/
```

**English:** The exact value changes between runs and must not be hard-coded.
To display it, print `tmp_path` and run pytest with `-s` to disable standard
output capture:

**中文：** 具体值会随运行变化，不应硬编码。要显示它，可以打印 `tmp_path`，并
使用 `-s` 运行 pytest 以关闭标准输出捕获：

```bash
python -m pytest -q -s test_file.py::test_save_message
```

**English:** Pytest normally retains temporary directories from a configurable
number of recent runs, but tests should depend only on the fixture value
provided for their own invocation.

**中文：** Pytest 通常会保留可配置数量的最近运行临时目录，但测试只能依赖为本次
调用提供的 fixture 值。

### 8. Controlling environment state with `monkeypatch` / 使用 `monkeypatch` 控制环境状态

**Question (English):** Does the test pass? Does `APP_MODE` remain changed
afterward, and what value does monkeypatching provide?

**问题（中文）：** 测试能否通过？之后 `APP_MODE` 是否会一直保持修改？
Monkeypatching 提供了什么价值？

```python
import os


def get_mode():
    return os.getenv("APP_MODE", "development")


def test_get_mode(monkeypatch):
    monkeypatch.setenv("APP_MODE", "testing")

    assert get_mode() == "testing"
```

**Explanation (English):** Tests often need deterministic control over global
or external state. Pytest's monkeypatch fixture can temporarily set or delete
environment variables, attributes, mapping entries, working directories, and
import paths.

**解说（中文）：** 测试经常需要确定性地控制全局或外部状态。Pytest 的
monkeypatch fixture 可以临时设置或删除环境变量、对象属性、mapping 条目、工作
目录与导入路径。

**Correct Answer (English):** The test passes, and pytest restores the prior
environment after the requesting test finishes. The value of monkeypatching is
controlled isolation: code can be exercised under a known condition without
permanently changing the real process environment or contacting an external
dependency. Simulating randomness is one possible use, not its definition.

**正确答案（中文）：** 测试可以通过；请求该 fixture 的测试结束后，pytest 会恢复
之前的环境。Monkeypatching 的价值在于受控隔离：代码可以在已知条件下执行，而
不会永久修改真实进程环境或联系外部依赖。模拟随机行为只是可能用途之一，并不是
它的定义。

### 9. Mock side effects and call verification / Mock 副作用与调用验证

**Question (English):** Does the test pass? What do the two `side_effect`
elements do, and what does `call_count` verify?

**问题（中文）：** 测试能否通过？`side_effect` 中两个元素分别起什么作用？
`call_count` 验证什么？

```python
from unittest.mock import Mock


def retry_once(function):
    def wrapper():
        try:
            return function()
        except ValueError:
            return function()

    return wrapper


def test_retry_once():
    worker = Mock(
        side_effect=[
            ValueError("temporary failure"),
            "ok",
        ]
    )

    wrapped = retry_once(worker)

    assert wrapped() == "ok"
    assert worker.call_count == 2
```

**Explanation (English):** A mock replaces a dependency with a controllable
callable and records how it is used. When `side_effect` is an iterable, each
call consumes the next element; exception elements are raised and ordinary
values are returned.

**解说（中文）：** Mock 使用可控制的 callable 替换依赖，并记录它的使用方式。
当 `side_effect` 是 iterable 时，每次调用消费下一个元素；异常元素会被抛出，
普通值会被返回。

**Correct Answer (English):** The test passes. The first call to `worker`
raises `ValueError`, which `wrapper` catches. The retry makes a second call,
which returns `"ok"`; this becomes the result of `wrapped()`. Both calls are
recorded, including the one that raised, so `worker.call_count` is `2`.

**正确答案（中文）：** 测试可以通过。第一次调用 `worker` 抛出 `ValueError`，
`wrapper` 将其捕获；重试产生第二次调用并返回 `"ok"`，它成为 `wrapped()` 的
结果。两次调用都会被记录，包括抛出异常的那次，因此 `worker.call_count` 为
`2`。

### 10. Designing a balanced test matrix / 设计均衡测试矩阵

**Question (English):** Choose one ordinary valid input, both valid boundary
inputs, one wrong-type input, and two out-of-range inputs for the following
function. State the expected result or exception for each.

**问题（中文）：** 为下面的函数选择一个普通有效输入、两个有效边界输入、一个错误
类型输入和两个越界输入，并说明每个输入的预期结果或异常。

```python
def normalize_score(score):
    if not isinstance(score, int):
        raise TypeError("score must be an integer")

    if score < 0 or score > 100:
        raise ValueError("score must be between 0 and 100")

    return score / 100
```

**Explanation (English):** A useful test matrix derives cases from the
contract rather than choosing many arbitrary values. It covers the normal
partition, each inclusive boundary, each invalid range, and each distinct
failure category.

**解说（中文）：** 有用的测试矩阵应从契约推导用例，而不是选择大量任意值。它会
覆盖普通有效分区、每个包含式边界、每个非法范围以及每种不同失败类别。

**Correct Answer (English):** One balanced set is:

**正确答案（中文）：** 一组均衡用例是：

- `33 -> 0.33`
- `0 -> 0.0`
- `100 -> 1.0`
- `"33" -> TypeError`
- `-1 -> ValueError`
- `101 -> ValueError`

**English:** There is an additional Python-specific edge: `bool` is a subclass
of `int`, so the implementation accepts `True` and returns `0.01`. If the
business contract excludes Boolean values, reject them explicitly and add a
test for `True` or `False`.

**中文：** 还有一个 Python 特有边界：`bool` 是 `int` 的子类，因此当前实现会
接受 `True` 并返回 `0.01`。如果业务契约排除布尔值，应显式拒绝它们，并为
`True` 或 `False` 添加测试。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** Arrange–Act–Assert separates setup, behavior, and verification.
  **中文：** Arrange–Act–Assert 分离准备、行为与验证。
- **English:** Failed assertions stop the current test and provide actionable
  diagnostics. **中文：** 失败断言会停止当前测试并提供可操作的诊断。
- **English:** Boundary cases are derived from comparison transitions rather
  than arbitrary inputs. **中文：** 边界用例来自比较结果转换点，而不是任意输入。
- **English:** `pytest.raises` verifies exception contracts, while
  parametrization expresses multiple examples of one rule. **中文：**
  `pytest.raises` 验证异常契约，参数化则表达同一规则的多个例子。
- **English:** Function-scoped fixtures provide fresh per-test setup.
  **中文：** 函数级 fixture 为每个测试提供新的准备状态。
- **English:** `tmp_path` isolates filesystem changes and provides a standard
  `pathlib.Path`. **中文：** `tmp_path` 隔离文件系统修改，并提供标准
  `pathlib.Path`。
- **English:** `monkeypatch` temporarily controls external state and restores
  it automatically. **中文：** `monkeypatch` 临时控制外部状态并自动恢复。
- **English:** `Mock` can simulate sequential behavior and record calls.
  **中文：** `Mock` 可以模拟连续行为并记录调用。
- **English:** A balanced suite covers normal values, boundaries, invalid
  ranges, and wrong types. **中文：** 均衡测试套件覆盖普通值、边界、非法范围与
  错误类型。

## Common Mistakes / 常见错误

- **English:** Defining implementation and tests in separate modules without
  importing the object under test. **中文：** 把实现与测试放在不同模块中，却没有
  导入被测试对象。
- **English:** Updating an expected value while leaving a stale custom failure
  message. **中文：** 修改了预期值，却留下过时的自定义失败消息。
- **English:** Expecting code after a failed assertion to continue running.
  **中文：** 误以为失败断言之后的代码仍会继续运行。
- **English:** Treating three nearby boundary values as the strict minimum
  when the value below and the value at an inclusive boundary already cover
  both outcomes. **中文：** 把三个相邻边界值当作严格最小集合，而边界下方值和
  包含式边界值已经覆盖两种结果。
- **English:** Assuming fixture return values are shared between tests under
  the default function scope. **中文：** 误以为默认函数级作用域下的 fixture
  返回值会在测试之间共享。
- **English:** Hard-coding the runtime directory produced by `tmp_path`.
  **中文：** 硬编码 `tmp_path` 产生的运行时目录。
- **English:** Describing monkeypatching only as random-value simulation
  instead of general temporary dependency control. **中文：** 只把
  monkeypatching 描述成随机值模拟，而没有理解其通用的临时依赖控制作用。
- **English:** Losing track of the two mock calls when the first call raises
  and the wrapper retries. **中文：** 第一次 mock 调用抛出异常并触发重试时，遗漏
  对两次调用的追踪。
- **English:** Forgetting that `bool` satisfies `isinstance(value, int)`.
  **中文：** 忘记 `bool` 满足 `isinstance(value, int)`。

## Next Steps / 下一步建议

**English:** Write the `normalize_score` suite with parametrized success and
failure cases, then study shared fixtures in `conftest.py`, fixture setup and
teardown with `yield`, broader fixture scopes, where to patch a dependency,
mock specifications and call assertions, test coverage, and a small integrated
test suite for a command-line benchmark tool.

**中文：** 使用参数化的成功与失败用例编写 `normalize_score` 测试套件，然后学习
`conftest.py` 中的共享 fixture、使用 `yield` 进行 fixture 准备与清理、更宽的
fixture 作用域、依赖的正确 patch 位置、mock 规格与调用断言、测试覆盖率，以及
面向命令行 benchmark 工具的小型集成测试套件。
