# Course 02: Building Python Experiment Tools / 第二课：Python 实验工具开发

## Objectives and prerequisites / 目标与前置知识

**English:** This course turns the Python topics from Days 016, 018, 022, 024, 026, 027, 029, 030, 031, 035, 038, and 039 into one working experiment tool. The deliverable reads a configuration, validates result records, groups compatible observations, writes a traceable report, and verifies the important failure paths. The goal is to make trustworthy decisions from files produced by other programs. Completing the course should let you explain why a number entered a report, which records were excluded, and what additional evidence would be required before calling a result a GPU performance measurement.

**中文：** 本课把第十六、十八、二十二、二十四、二十六、二十七、二十九、三十、三十一、三十五、三十八和三十九天的 Python 知识组织成一个可运行的实验工具。最终交付物读取配置，校验结果记录，按可比较条件分组，写出能够追溯的报告，并验证重要失败路径。学习目标是依据其他程序产生的文件作出可信判断。完成后，你应能解释一个数值为什么进入报告、哪些记录被排除，以及把结果称为 GPU 性能测量之前还缺少什么证据。

**English:** You should already be comfortable with variables, conditions, loops, function calls, and a terminal. No GPU, third-party package, cloud account, or model download is required. The main exercise uses only the standard library and deliberately supplied fixture values. It does not launch a kernel. Work through the principles first, then create the package in a fresh temporary directory, execute its tests, and change one assumption at a time. Treat the ten exercises as checks of reasoning rather than an invitation to memorize the reference implementation. Passing these checks establishes the tested tool behavior, not mastery of the entire performance-optimization process.

**中文：** 前置要求是理解变量、条件、循环和函数调用，并能使用终端。本课不要求显卡、第三方依赖、云账号或模型下载。主实验只使用标准库和人为提供的测试数据，不会启动任何计算核函数。建议先阅读原理，再在新的临时目录中创建包、执行测试，每次只改变一项假设。最后的十道习题用来检查推理过程，而不是要求记住参考实现。即使所有测试通过，也只说明工具的这些已验证行为成立，不能据此宣称掌握了完整的性能优化方法。

**English:** Documentation was checked on 2026-09-18. The official Python documentation currently identifies itself as version 3.14.7; the complete exercise was executed locally with CPython 3.14.4. The code uses syntax and standard-library features available in Python 3.11 and later, but the recorded run covers only the stated interpreter. Pin the documentation branch and record your actual interpreter when reproducing results. A documentation version and a tested runtime are different pieces of evidence; neither silently stands in for the other. See the [official Python documentation](https://docs.python.org/3/) for the version selector.

**中文：** 文档核验日期为二〇二六年九月十八日。Python 官方文档当前标示版本为三点十四点七；完整实验在本地 CPython 三点十四点四上执行。代码使用 Python 三点十一及之后版本已有的语法和标准库功能，但本次运行证据只覆盖明确写出的解释器。复现时应固定查阅的文档分支，并记录自己实际使用的版本。文档版本与经过测试的运行环境是两种证据，不能默默互相替代；版本选择入口见上述官方文档。

## 1. Start from the data contract / 从数据契约出发

**English:** An experiment pipeline has at least three boundaries: bytes become Python values, values become validated domain records, and records become a report. Successful JSON parsing crosses only the first boundary. The object `{ "ms": true }` is valid JSON, but a boolean is not a latency measurement. Conversely, an empty input file can be readable and well encoded while containing no evidence. Keeping these boundaries separate produces useful errors and prevents a permissive parser from accidentally becoming your business specification. Trustworthy data requires validating meaning beyond syntax.

**中文：** 实验流水线至少有三个边界：字节变成 Python 值，普通值变成经过验证的领域记录，记录再变成报告。JSON 解析成功只跨过第一个边界。对象 `{ "ms": true }` 在语法上合法，但布尔值不是延迟测量。反过来，空文件可以读取正常、编码正确，却没有任何实验依据。把这些边界分开，可以生成有用的错误信息，也能避免把解析器允许的所有输入误当成业务规则。检查数据是否可信，必须从语法进一步走到含义。

**English:** Our record identifies a run, a kernel, a two-dimensional shape, a dtype, a device, a timing scope, a source kind, a duration, and a correctness result. Grouping uses all the experimental conditions rather than only the kernel name. A device-kernel duration and an end-to-end service duration answer different questions, so their medians must never be merged. Fixture and measurement records also stay separate. This is an intentionally small teaching schema: production comparisons usually need compiler flags, revision, runtime, warmup policy, power state, and more provenance.

**中文：** 本课记录包含运行编号、核函数、二维形状、数据类型、设备、计时范围、数据来源、耗时以及正确性结果。分组依据全部实验条件，而不是只看核函数名称。设备核函数耗时与服务端到端耗时回答的是不同问题，不能合并求中位数；人为测试数据与真实测量也必须分开。本课刻意使用较小的教学模式。实际性能比较通常还需要编译选项、代码版本、运行时、预热策略和功耗状态等来源信息，不能把这里列出的字段误认为完整标准。

**English:** Define failure policy before writing the loop. In `fail` mode, one invalid record aborts aggregation and no new report is written. In `skip` mode, the tool records rejected line numbers and reasons, retains valid records, and marks the report incomplete. A correctly parsed record whose correctness flag is false is different from an invalid record: it remains visible in the group, but contributes no duration to the successful-sample statistics. Neither mode quietly converts missing evidence into a successful experiment. Defining these outcomes first lets you judge whether exception handling fulfills the requirements or merely silences errors.

**中文：** 写循环之前先定义失败策略。严格模式遇到一条非法记录就终止聚合，不写出新报告；跳过模式保存被拒绝的行号和原因，保留合法记录，同时把报告标记为不完整。正确性标志为假的合法记录，又不同于字段非法的记录：前者仍出现在分组中，但耗时不参与成功样本统计。两种策略都不能把缺失证据悄悄变成成功实验。先约定这些行为，才能判断后续异常处理是在落实要求，还是仅仅让程序不再报错。

## 2. Names, objects, and container design / 名字、对象与容器设计

**English:** Assignment connects a name to an object; it is not an instruction to clone that object's contents. Imagine two report-building functions receive the same dictionary and one inserts a temporary field. The other function sees that mutation because they share the dictionary. Rebinding the local parameter to a new dictionary behaves differently: it changes the local name, not the caller's binding. Draw names as arrows and containers as boxes when debugging this distinction. The picture explains more reliably than saying that Python passes everything “by reference.”

**中文：** 赋值让名字绑定到对象，并不指示解释器克隆对象内容。假设两个报告函数收到同一个字典，其中一个加入临时字段，另一个也会看到修改，因为它们共享这个字典。把函数内部参数重新绑定到新字典则不同：变化的是局部名字，不是调用方的绑定。调试这类问题时，可以把名字画成箭头，把容器画成盒子，再观察操作改变了箭头还是盒子内容。这样的分析比笼统地说所有参数都是引用传递更准确，也更容易定位跨函数的数据污染。

**English:** A shallow copy creates a new outer container while preserving references to nested objects. It is sufficient when you add a top-level scalar field without changing shared children. It is insufficient when you change a nested shape list. A deep copy recursively reconstructs supported object graphs and tracks already copied objects, so shared relationships within the copied graph may remain shared. It is not a universal duplication mechanism for open files, sockets, or external resources. Decide which data must be independent, then choose copying or normalization to establish that boundary. See [copy semantics](https://docs.python.org/3/library/copy.html).

**中文：** 浅拷贝创建新的外层容器，却保留对子对象的引用。如果只是加入顶层标量字段，不修改共享子对象，它可能已经足够；如果要修改内部的形状列表，它就不够。深拷贝递归重建支持复制的对象图，并记录已经复制的对象，所以副本内部原有的共享关系仍可能保留。它不是复制打开文件、套接字或外部资源的通用机制。正确做法是先确定哪些数据需要独立，再选择复制或规范化方法建立边界，具体语义见上述官方说明。

```python
import copy

original = {"shape": [32, 32], "tag": "baseline"}
shallow = original.copy()
deep = copy.deepcopy(original)
shallow["shape"][0] = 64
assert original["shape"] == [64, 32]
assert deep["shape"] == [32, 32]
normalized_shape = tuple(original["shape"])
original["shape"][1] = 128
assert normalized_shape == (64, 32)
```

**English:** Choose a list when order and repeated observations matter, a dictionary when a key identifies one value, and a set when membership or uniqueness is the question. Converting durations to a set would erase repeated measurements and distort their distribution. Building `{row["kernel"]: row for row in rows}` would overwrite earlier runs of the same kernel. Our implementation therefore keeps samples in lists, uses a dictionary for condition-based groups, and uses a set only to detect duplicate run identifiers. Each container corresponds to a specific invariant.

**中文：** 当顺序和重复观测有意义时使用列表，当一个键对应一个值时使用字典，当问题是成员关系或唯一性时使用集合。把耗时转换成集合，会删除数值相同但分别发生的测量，破坏分布；用核函数名称构建单值字典，则会覆盖同名核函数之前的运行。本课因此用列表保存样本，用字典按条件分组，只用集合检测重复运行编号。容器选择不是语法偏好，而是在声明要保留什么信息、允许什么重复，以及什么情况必须拒绝。

**English:** Comprehensions are useful for a short projection or filter, such as extracting successful durations. They become harder to audit when they combine parsing, exception recovery, logging, and mutation. Prefer a normal loop at an error boundary so that the line number, rejected record, and continuation policy are obvious. Also distinguish `append(record)` from `extend(records)`: the first preserves one record as an element; the second iterates its argument. Accidentally extending a list with a dictionary inserts its keys instead of inserting the dictionary. Compact syntax is useful only while the information structure stays clear.

**中文：** 推导式适合简短的字段提取或筛选，例如抽取正确性通过的耗时。如果同时承担解析、异常恢复、日志记录和修改状态，代码就很难检查。在错误边界使用普通循环，更容易看清行号、被拒绝的记录和继续执行策略。还应区分把一条记录作为元素加入列表，与遍历一个集合逐个加入元素。如果误把字典传给 `extend`，列表得到的是字典键，而不是那条完整记录。紧凑写法只有在信息结构仍然清晰时才有价值。

## 3. Functions, scope, and callable contracts / 函数、作用域与可调用契约

**English:** A useful function makes one transformation explicit. `validate_sample` turns an unknown value into a `Sample` or raises a domain error; `aggregate` turns validated samples into statistics; `write_report` performs file output. Printing inside all three would couple computation to presentation and make tests harder to control. Return data from the computational layer and let the command-line entry point choose what to print. Keyword-only parameters such as `min_samples` and `on_error` also make policy visible at the call site instead of hiding it in positional arguments. This also reduces argument-order mistakes during later maintenance.

**中文：** 有用的函数会明确表达一次转换。校验函数把未知值变成样本对象，失败时抛出领域错误；聚合函数把合法样本变成统计结果；写入函数执行文件输出。如果三个函数都随意打印，就会把计算与展示耦合起来，增加测试控制难度。计算层应返回数据，由命令行入口决定如何展示。最小样本数和错误策略采用仅限关键字参数，也是在调用位置直接表达政策，避免读者猜测几个位置参数分别代表什么，尤其能减少后续维护中的参数错位。

**English:** Default argument values are evaluated when the function is defined. A default list can therefore accumulate state across calls that were intended to be independent. Use `None` as a sentinel and construct a new list inside the call, or require the caller to supply the collection when shared mutation is intentional. In the main exercise, rejected records are accumulated into an explicitly provided list. That choice makes the side effect visible. The list belongs to one report run, so separate invocations cannot inherit one another's rejection history. Understanding when the object is created helps recognize related bugs better than memorizing a ban on default lists.

**中文：** 默认参数值在函数定义时求值，因此默认列表可能在本应独立的多次调用之间积累状态。通常应以 `None` 作为哨兵，在每次调用内部建立新列表；如果确实希望共享修改，则要求调用方显式传入容器。主实验的拒绝记录累积到调用方明确提供的列表中，这让副作用能够在接口上看见。该列表只属于一次报告运行，不会把上一轮拒绝历史带进下一轮。理解创建时机，比机械记住不要写默认列表更能帮助你识别同类错误。

```python
def collect(label: str, bucket: list[str] | None = None) -> list[str]:
    if bucket is None:
        bucket = []
    bucket.append(label)
    return bucket

assert collect("first") == ["first"]
assert collect("second") == ["second"]
```

**English:** Type hints describe an intended interface for readers and type-checking tools; they do not validate JSON values during execution. Annotating a parameter as `float` does not stop a caller from passing `True`. At an external-data boundary, receive `object`, inspect structure and values, and then build the domain representation. Internal code can operate on stronger assumptions once that boundary succeeds. The exercise's annotations document interfaces, but this course does not claim a clean run from a particular static type checker; runtime tests and static analysis establish different facts. See [typing](https://docs.python.org/3/library/typing.html).

**中文：** 类型注解为读者和类型检查工具描述预期接口，不会在运行时自动校验 JSON 值。即使参数注明浮点数，调用方仍然可以传入布尔值。在外部数据边界，先接收未知对象，检查结构和取值，再构造领域表示；通过边界之后，内部代码才能依赖更强的假设。本课注解用于说明接口，没有声称通过某个静态类型检查器的完整检查。运行测试和静态分析证明的是不同事情，不能把一方的结果扩大成另一方的保证，相关机制见上述官方文档。

**English:** A closure keeps access to bindings in an enclosing function. If an inner function assigns to an enclosing local name, `nonlocal` selects that binding; mutating an object already reached through the binding does not require rebinding the name. Late binding matters when callbacks are created in a loop: each callback can observe the loop variable's later value. A small factory creates a distinct binding for each callback. Use this deliberately when constructing per-kernel filters, otherwise all filters can silently end up selecting the final kernel.

**中文：** 闭包保留访问外层函数绑定的能力。内部函数如果要给外层局部名字重新赋值，需要使用 `nonlocal`；如果只是修改通过该名字访问到的对象，则不属于重新绑定。循环里创建回调时还要警惕延迟绑定：每个回调可能读到循环变量后来的值。小型工厂函数可以为每个回调建立独立绑定。按核函数生成筛选器时尤其需要理解这一点，否则多个看似不同的筛选器可能最终都选择最后一个核函数，结果仍然合法却已经失去原意。

```python
def make_filter(expected: str):
    def matches(record: dict) -> bool:
        return record["kernel"] == expected
    return matches

filters = [make_filter(name) for name in ("transpose", "reduce")]
assert filters[0]({"kernel": "transpose"})
assert not filters[1]({"kernel": "transpose"})
```

## 4. Decorators without hidden measurement claims / 不混淆测量含义的装饰器

**English:** A decorator receives a callable and returns the callable that replaces its name. The wrapper should usually forward arguments, return the original result, and preserve exception behavior. `functools.wraps` copies useful metadata and exposes the wrapped callable, making introspection less misleading. It does not automatically preserve the function's runtime behavior; the wrapper's body remains responsible for that. A logging wrapper that catches every exception and returns `None` has changed the contract even if its name and documentation were preserved perfectly. See [functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps). Review return values, errors, and side effects before checking whether the wrapper looks like the original function.

**中文：** 装饰器接收可调用对象，再返回一个替代原名字的可调用对象。包装函数通常应转发参数、返回原结果，并保留异常行为。`functools.wraps` 复制有用的元信息，并暴露被包装对象，使自省结果更准确，但它不会自动保留运行行为，真正的契约仍取决于包装函数体。如果日志包装器吞掉全部异常并返回空值，即使名字和文档字符串都保留得很好，也已经改变了接口。检查装饰器时，应优先观察返回值、错误和副作用，再观察外观是否一致。

**English:** The following decorator measures the duration of a Python call with a monotonic performance counter. The event is explicitly named `host_call_elapsed_ms`, not `gpu_ms`. File parsing, scheduling, synchronization, or logging can contribute to the interval depending on what is wrapped. An asynchronous GPU launch may return before device work completes, while wrapping the full reporting command includes unrelated work. Thus this wrapper can diagnose tool overhead but cannot certify device-kernel performance. Its counter uses closure state and is intended here for sequential calls, not concurrent accounting.

**中文：** 下例装饰器通过单调性能计数器测量一次 Python 调用的时间，事件明确命名为主机调用耗时，而不是显卡耗时。被包装内容不同，区间中可能包括文件解析、调度、同步或日志写入。异步启动 GPU 任务可能在设备工作完成之前返回；包装整个报告命令又会混入无关操作。因此它可以帮助分析工具自身开销，却不能证明设备核函数性能。计数器使用闭包状态，这里只面向顺序调用，不承担多线程或异步并发条件下的精确计数责任。

```python
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def observe(sink: list[dict]):
    calls = 0

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal calls
            calls += 1
            call_id = calls
            start = perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                sink.append({"call_id": call_id, "name": function.__name__,
                             "host_call_elapsed_ms":
                                 (perf_counter() - start) * 1000})
        return wrapper
    return decorate

events = []

@observe(events)
def reciprocal(value: float) -> float:
    return 1 / value

assert reciprocal(2) == 0.5
try:
    reciprocal(0)
except ZeroDivisionError:
    pass
assert len(events) == 2
assert reciprocal.__name__ == "reciprocal"
```

**English:** Decorator order is part of behavior. In `outer(inner(work))`, execution enters `outer`, then `inner`, then the original function, and unwinds in reverse. Placing timing outside a retry wrapper includes repeated attempts and retry delays; placing it inside measures individual attempts. Both are meaningful if named accurately. Before adding retries, ask whether the operation is safe to repeat. Repeating pure validation is harmless but unnecessary; repeating a report write may encounter an existing file. Instrumentation and retries need explicit semantics rather than decorative syntax added by habit.

**中文：** 装饰器顺序也是行为的一部分。外层包装内层时，调用依次进入外层、内层和原函数，退出则反向进行。计时放在重试包装器外面，会包括多次尝试和重试等待；放在里面，则记录各次尝试。只要名称准确，两种范围都可以有意义。增加重试之前还要判断操作能否安全重复：纯校验可以重复但通常没有必要，报告写入则可能碰到已存在文件。观测与重试需要明确语义，不能仅因为装饰器写法方便，就不加分析地套在函数上。

## 5. Iteration and resource lifetime / 迭代与资源生命周期

**English:** An iterable can provide an iterator; an iterator stores progress and supplies successive values. A list can produce a fresh iterator for each pass, while a generator object is normally a single consumable stream. Calling a generator function creates that object without executing its body. The first `next` starts the body, and each `yield` suspends it with local state preserved. Consequently, a parsing error may appear during aggregation rather than when the reader function is called. Exception handling must surround consumption, not only construction.

**中文：** 可迭代对象能够提供迭代器；迭代器保存进度并连续提供值。列表每次遍历可以生成新迭代器，而一个生成器对象通常是一条只能消费一次的流。调用生成器函数时只是创建对象，并不执行函数体；首次请求值才开始运行，每次产出又会暂停并保留局部状态。因此解析错误可能出现在聚合过程中，而不是调用读取函数时。异常处理必须覆盖实际消费阶段，只包住生成器创建语句，会漏掉真正执行读取和解析时发生的错误。

**English:** Laziness reduces unnecessary work only when downstream code also cooperates. A line-by-line reader avoids first building a list of every raw line, but our exact-median aggregator intentionally retains samples for each group. Its memory therefore grows with the number of accepted records. A generator at the front does not make the entire pipeline constant-memory. If only counts and sums were needed, an online accumulator could use memory proportional to the number of groups. Exact medians or retained run identifiers require additional storage or a different external-memory design. Assess memory complexity along the complete data path.

**中文：** 惰性求值只有在下游也配合时才减少不必要工作。逐行读取避免预先建立全部原始行的列表，但本课为了计算精确中位数并保留运行编号，仍然保存各组样本，所以内存会随合法记录数量增长。入口使用生成器，并不意味着整条流水线都是常量内存。如果只需要计数和总和，在线累加器可以把空间控制在分组数量附近；精确中位数与完整编号则需要额外存储，或改用外部存储算法。评估空间复杂度必须追踪整个数据路径。

**English:** Resource lifetime is independent of a variable's lexical visibility. After `with path.open() as stream` finishes, the name can still exist while the file is already closed. A generator expression returned from inside that block does not keep the file usable. Put the `with` inside a generator function when reading must continue across yields, and arrange deterministic closure when consumption stops early. The main tool closes the reader in `finally`, so an exception inside aggregation does not leave its open file waiting for garbage collection. See [contextlib](https://docs.python.org/3/library/contextlib.html). Express release timing through program structure instead of relying on prompt garbage collection.

**中文：** 资源生命周期独立于变量名字的可见范围。文件上下文结束之后，名字可能还存在，但文件已经关闭；从上下文内部返回生成器表达式，也不会让文件继续可用。如果读取需要跨越多次产出，应把文件上下文放进生成器函数内部，并在提前停止消费时安排确定性的关闭。主工具在 `finally` 中关闭读取生成器，因此聚合逻辑即使抛出异常，也不会让打开的文件等待垃圾回收。资源何时释放应由结构表达，而不是依赖解释器碰巧很快回收对象。

```python
from contextlib import closing
from pathlib import Path

def lines(path: Path):
    with path.open(encoding="utf-8") as stream:
        yield from stream

# Supply a real file before executing this fragment. / 执行前提供真实文件。
# with closing(lines(Path("runs.jsonl"))) as source:
#     first = next(source)
```

**English:** A context manager's cleanup is not automatically exception suppression. Ordinary file contexts close the handle and let the error propagate. A custom `__exit__` suppresses a pending exception when it returns a truthy value, so returning `True` merely to indicate successful cleanup is a serious mistake. Generator-based context managers likewise must re-raise errors they are not intentionally handling. Cleanup can be reliable while the operation still fails; that is often exactly the desired outcome for a corrupted experiment file. The file closes, the error survives, and the caller can tell that reporting did not complete.

**中文：** 上下文管理器执行清理，并不等于自动吞掉异常。普通文件上下文关闭句柄之后，错误仍会向外传播。自定义退出方法返回真值时才会抑制待处理异常，因此仅为了表示清理成功而返回真值，是危险的误解。基于生成器实现的上下文管理器，也应重新抛出自己无意处理的错误。可靠清理与操作失败完全可以同时成立；对损坏的实验文件而言，这通常正是期望结果：文件被关闭，错误被保留，调用方可以明确知道报告没有完成。

## 6. JSON, paths, and publication boundaries / JSON、路径与输出边界

**English:** JSON objects become dictionaries, but syntax acceptance does not enforce unique keys or valid business values. Python's default decoder accepts repeated object names and retains the last value; this course installs `object_pairs_hook` to reject duplicates. Numeric validation separately rejects booleans, negative durations, nonfinite floats, and numbers too large for the chosen float representation. Blank lines are invalid records rather than silent separators. These are deliberate schema choices, not universal JSON rules; document them so that producers can meet the contract. See [the JSON decoder](https://docs.python.org/3/library/json.html).

**中文：** JSON 对象会转换成字典，但语法解析不会自动保证键唯一，也不会验证业务取值。Python 默认解码器接受重复字段并保留后值，本课通过对象键值对钩子拒绝重复键。数值校验还会排除布尔值、负耗时、非有限浮点数，以及大到无法转换为所选浮点表示的数。空白行被视为非法记录，而不是悄悄跳过的分隔符。这些都是明确选择的数据模式规则，不是所有 JSON 文件必须遵循的普遍约定，应写清楚让数据生产者能够配合。

**English:** A `Path` object represents a location; constructing or joining one does not read or create files. Relative paths normally depend on the process's working directory. Our configuration loader instead anchors its `input` and `output` paths to the configuration file's parent directory, making a saved configuration portable across launch locations. Resolving a path normalizes that interpretation but does not prove the file exists or is readable. The actual open remains the operation that can fail, so preliminary existence checks are not substitutes for exception handling. See [pathlib](https://docs.python.org/3/library/pathlib.html). Path interpretation, the object currently at that path, and the eventual operation result are separate questions.

**中文：** 路径对象表示位置，构造或拼接路径不会读取文件，也不会创建目录。相对路径通常依赖进程当前工作目录；本课配置加载器则把输入和输出路径锚定到配置文件所在目录，让保存的配置不受启动位置影响。解析路径能够规范化这种解释，却不证明文件存在或可读。真正打开文件时仍然可能失败，所以提前检查存在性不能替代异常处理。必须区分路径如何解释、目标当时是什么对象，以及最终文件操作是否成功这三个独立问题。

**English:** Publishing a report is another contract. This exercise serializes the complete report before opening its destination, rejects nonstandard nonfinite JSON output, creates missing parent directories, and uses exclusive creation mode `x`. Running again against the same output therefore fails instead of replacing existing evidence. This is intentionally simpler than atomic replacement. A crash during the final write can still leave a partial newly created file; the example makes no transactional or crash-durability promise. Such guarantees require an explicitly designed temporary-file and replacement protocol. A stronger publication protocol also needs any required synchronization and verification of the target filesystem behavior.

**中文：** 写出报告同样需要契约。本实验先把完整报告序列化，再打开目标文件；输出拒绝非有限 JSON 数值，自动建立缺失的父目录，并使用独占创建模式。因此再次运行到同一输出位置会失败，不会替换既有证据。这比原子替换更简单，但如果最终写入途中进程崩溃，仍然可能留下一个不完整的新文件。本例没有承诺事务性或断电持久性；需要这些保证时，应另外设计临时文件、替换和必要同步组成的发布协议，并验证目标文件系统的行为。

**English:** Do not catch every exception in a record loop. Parsing and schema errors can follow the configured skip policy, but failure to open the source or decode its bytes is a file-level failure here. Bugs such as calling a nonexistent method should remain visible as programming errors. The command-line boundary converts expected input/output failures into exit code 2, and a written but incomplete report returns 3. Successful completion returns 0. This lets a shell or continuous-integration system distinguish success, unusable input, and partial evidence without interpreting human-readable prose. A process merely avoiding a crash is not sufficient evidence of a successful experiment.

**中文：** 不要在记录循环里捕获所有异常。解析与模式错误可以遵循跳过策略，但本课把源文件打不开或字节编码损坏视为文件级失败；调用不存在方法之类的程序错误也应该直接暴露。命令行边界把预期的输入输出失败转成退出码二，把已经写出但证据不完整的报告转成退出码三，完整成功返回零。这样脚本或持续集成系统可以区分成功、不可用输入与部分证据，不必分析面向人的提示文字，也不会把只要进程没崩溃当作实验通过。

## 7. Modules, packages, and domain objects / 模块、包与领域对象

**English:** Importing a module normally executes its top-level statements the first time that module is loaded in a process, after which the module cache is normally reused. Therefore top-level file writes, command-line parsing, or benchmark launches become surprising import side effects. Keep reusable definitions in `core.py`, the command-line policy in `__main__.py`, and package initialization quiet. Run the package with `python -m experiment_tool`; this establishes package context for the relative import. Directly executing the internal file is a different launch mode and is not the supported interface. See [modules and packages](https://docs.python.org/3/tutorial/modules.html). Resolve import context through package structure rather than temporary changes to the global search path.

**中文：** 模块首次在进程中导入时，通常会执行顶层语句，之后一般复用模块缓存。因此顶层文件写入、命令行解析或基准启动都会变成令人意外的导入副作用。应把可复用定义放在核心模块，把命令行策略放在入口模块，并让包初始化保持安静。使用模块方式运行包，可以为相对导入建立正确上下文；直接执行内部文件则是另一种启动方式，不属于本课支持的接口。导入路径和启动方式应该由结构解决，不应靠临时修改全局搜索路径掩盖问题。

**English:** A dataclass removes repetitive initialization and representation code, but it does not automatically validate external values. `frozen=True` blocks ordinary attribute reassignment; it does not recursively freeze objects stored in fields. A frozen record containing a mutable list would still allow that list to change. Our `Sample` stores its shape as a tuple of validated integers and its other fields as immutable scalar values. This establishes a useful stable snapshot after parsing, while `Config` stores path descriptions rather than open file handles. See [dataclasses](https://docs.python.org/3/library/dataclasses.html). Separating data representation from resource ownership makes objects easier to compare, pass, and test while reducing hidden lifetime responsibilities.

**中文：** 数据类减少重复的初始化和对象展示代码，却不会自动校验外部数据。冻结选项阻止普通属性重新赋值，并不会递归冻结字段内部对象；冻结记录如果包含可变列表，那个列表仍然可能被修改。本课样本把形状转换为经过验证的整数元组，其他字段也使用不可变标量，从而在解析之后建立稳定快照。配置对象保存路径描述，而不是打开的文件句柄。数据表示与资源持有分离以后，对象更容易比较、传递和测试，也减少隐藏的生命周期责任。

**English:** Avoid placing a mutable list on a class as if it were per-instance state. With dataclasses, `field(default_factory=list)` creates a fresh list when an instance needs a default, while a class attribute represents shared class state. In this tool, rejected rows are deliberately ordinary local lists, and validated samples are immutable snapshots. No class hierarchy is necessary. Introduce classes because they clarify data invariants and behavior, not merely because the tool now has several functions; an unnecessary abstraction can conceal the same sharing problem under more code.

**中文：** 不要把可变列表放在类上，却误以为每个实例都会独立持有它。数据类的默认工厂会在实例需要默认值时创建新列表，而普通类属性表示类级共享状态。本工具有意让拒绝记录成为局部列表，让合法样本成为不可变快照，不需要额外的继承体系。引入类的理由应该是更清晰地表达数据约束和行为，而不是函数数量变多就必须面向对象。没有必要的抽象，往往只是在更多代码下面隐藏同一个共享状态问题。

## 8. Complete experiment / 完整实验

**English:** Create a fresh directory, then save each following block under the indicated relative filename. The fixture contains three successful observations with durations 1, 3, and 2; its expected median is therefore 2. These numbers are intentionally chosen for hand calculation, not collected from hardware. Preserve the `source_kind` value `fixture`. No change to a label can transform artificial data into a measurement. The package layout is deliberately small enough to inspect completely before execution, and every production code path can be understood from the preceding contracts. If a branch is unclear, trace the input condition that reaches it before copying and running it.

**中文：** 新建一个目录，再把后续代码块保存到标注的相对文件路径。测试数据包含三个成功观测，耗时分别为一、三、二，所以预期中位数为二。这些数值为方便手算而刻意选择，并非来自硬件采集，来源字段必须保留为测试数据。修改标签不能把人为数值变成真实测量。包布局保持足够小，使你能在运行之前完整阅读；前面定义的契约应当能够解释每条主要路径。如果看到无法解释的分支，先停下来追踪其输入条件，再继续复制执行。

```bash
mkdir -p experiment_tool tests demo
python3 --version
```

### Package initialization / 包初始化

**English:** Save the following as `experiment_tool/__init__.py`; importing the package should not start a report run.

**中文：** 将下列内容保存为 `experiment_tool/__init__.py`；导入包不应启动报告生成。

```python
"""Validated experiment aggregation."""
```

### Core implementation / 核心实现

**English:** Save as `experiment_tool/core.py`. The strict object hook checks duplicate JSON keys before dictionary construction can hide them. The reader attaches physical line numbers to rejected records, and aggregation preserves run identifiers. Configuration validation refuses direct path aliases to its input or configuration, while exclusive output creation also prevents overwriting any existing destination. This is an offline tool for trusted local workflows, not a sandbox for arbitrary hostile filesystem mutation. Do not turn a few useful path checks into a claim of a complete security boundary.

**中文：** 保存为 `experiment_tool/core.py`。严格对象钩子在字典构造隐藏重复字段之前检查它们；读取器为拒绝记录附上物理行号，聚合器保留运行编号。配置校验拒绝输出直接指向输入或配置文件的情况，而独占创建又防止覆盖任何既有目标。本工具服务于可信本地工作流中的离线处理，不是用来隔离任意恶意文件系统变更的沙箱。路径校验有明确用途和适用条件，不应把少数检查扩大解释为完整安全边界。

```python
from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from statistics import median


class DataError(ValueError):
    pass


def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DataError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=strict_object)


def fields(value: object, expected: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DataError("expected a JSON object")
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise DataError(f"fields: missing={missing}, extra={extra}")
    return value


def text_field(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{label} must be a nonempty string")
    return value


@dataclass(frozen=True)
class Config:
    input: Path
    output: Path
    on_error: str
    min_samples: int


@dataclass(frozen=True)
class Sample:
    run_id: str
    kernel: str
    shape: tuple[int, int]
    dtype: str
    device: str
    timing_scope: str
    source_kind: str
    ms: float
    passed: bool

    @property
    def group_key(self) -> tuple[str, tuple[int, int], str, str, str, str]:
        return (self.kernel, self.shape, self.dtype, self.device,
                self.timing_scope, self.source_kind)


def load_config(path: Path) -> Config:
    path = path.resolve()
    obj = fields(parse_json(path.read_text(encoding="utf-8")),
                 {"schema_version", "input", "output", "on_error", "min_samples"})
    if type(obj["schema_version"]) is not int or obj["schema_version"] != 1:
        raise DataError("schema_version must be integer 1")
    policy = obj["on_error"]
    if policy not in ("fail", "skip"):
        raise DataError("on_error must be fail or skip")
    count = obj["min_samples"]
    if type(count) is not int or count < 1:
        raise DataError("min_samples must be a positive integer")
    source = (path.parent / text_field(obj["input"], "input")).resolve()
    target = (path.parent / text_field(obj["output"], "output")).resolve()
    if target in (source, path):
        raise DataError("output must not overwrite input or config")
    if target.exists() and any(target.samefile(p) for p in (source, path)
                               if p.exists()):
        raise DataError("output aliases input or config")
    return Config(source, target, policy, count)


def validate_sample(value: object) -> Sample:
    obj = fields(value, {"run_id", "kernel", "shape", "dtype", "device",
                         "timing_scope", "source_kind", "ms", "passed"})
    shape = obj["shape"]
    if (not isinstance(shape, list) or len(shape) != 2
            or any(type(n) is not int or n <= 0 for n in shape)):
        raise DataError("shape must contain two positive integers")
    ms = obj["ms"]
    if type(ms) not in (int, float):
        raise DataError("ms must be a number, not bool or string")
    try:
        numeric_ms = float(ms)
    except OverflowError as exc:
        raise DataError("ms is outside the supported float range") from exc
    if not math.isfinite(numeric_ms) or numeric_ms < 0:
        raise DataError("ms must be finite and nonnegative")
    if type(obj["passed"]) is not bool:
        raise DataError("passed must be bool")
    if obj["timing_scope"] not in ("device_kernel", "service_e2e"):
        raise DataError("unsupported timing_scope")
    if obj["source_kind"] not in ("fixture", "measurement"):
        raise DataError("source_kind must be fixture or measurement")
    if obj["dtype"] not in ("float16", "float32"):
        raise DataError("unsupported dtype")
    return Sample(text_field(obj["run_id"], "run_id"),
                  text_field(obj["kernel"], "kernel"), (shape[0], shape[1]),
                  obj["dtype"], text_field(obj["device"], "device"),
                  obj["timing_scope"], obj["source_kind"], numeric_ms,
                  obj["passed"])


def read_samples(path: Path, *, on_error: str,
                 rejected: list[dict[str, object]]) -> Iterator[Sample]:
    if on_error not in ("fail", "skip"):
        raise DataError("on_error must be fail or skip")
    seen: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                sample = validate_sample(parse_json(line))
                if sample.run_id in seen:
                    raise DataError(f"duplicate run_id: {sample.run_id}")
            except (json.JSONDecodeError, DataError) as exc:
                detail = {"line": line_number, "reason": str(exc)}
                if on_error == "fail":
                    raise DataError(f"{path}:{line_number}: {exc}") from exc
                rejected.append(detail)
                continue
            seen.add(sample.run_id)
            yield sample


def aggregate(samples: Iterator[Sample], *, min_samples: int) -> list[dict]:
    groups: dict[tuple, list[Sample]] = defaultdict(list)
    for sample in samples:
        groups[sample.group_key].append(sample)
    result = []
    for key, rows in sorted(groups.items()):
        kernel, shape, dtype, device, scope, source_kind = key
        times = [row.ms for row in rows if row.passed]
        result.append({"kernel": kernel, "shape": list(shape), "dtype": dtype,
                       "device": device, "timing_scope": scope,
                       "source_kind": source_kind, "accepted_count": len(rows),
                       "passed_count": len(times),
                       "failed_count": len(rows) - len(times),
                       "median_ms": median(times) if times else None,
                       "min_ms": min(times) if times else None,
                       "max_ms": max(times) if times else None,
                       "meets_min_samples": len(times) >= min_samples,
                       "run_ids": [row.run_id for row in rows]})
    return result


def run(config: Config) -> dict:
    rejected: list[dict[str, object]] = []
    rows = read_samples(config.input, on_error=config.on_error, rejected=rejected)
    try:
        groups = aggregate(rows, min_samples=config.min_samples)
    finally:
        rows.close()
    complete = (bool(groups) and not rejected
                and all(g["meets_min_samples"] and g["failed_count"] == 0
                        for g in groups))
    return {"schema_version": 1, "input": str(config.input),
            "on_error": config.on_error, "min_samples": config.min_samples,
            "complete": complete, "rejected_count": len(rejected),
            "rejected": rejected, "groups": groups}


def write_report(path: Path, report: dict) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(payload + "\n")
```

### Command-line entry point / 命令行入口

**English:** Save as `experiment_tool/__main__.py`. `main` accepts optional argument values so it can be called under controlled conditions, and returns an integer status instead of directly terminating from inside reusable functions. The final guard translates that value into process termination only when the module is used as an entry point. Expected operational errors go to standard error; the normal report location goes to standard output. That separation lets another program capture successful output without mixing it with diagnostics. Keep this command-line policy in one layer rather than spreading it across validation, aggregation, and file handling.

**中文：** 保存为 `experiment_tool/__main__.py`。入口函数接收可选参数列表，便于在可控条件下调用，并返回整数状态，而不是从可复用函数深处直接终止进程。末尾入口判断只在模块作为程序入口时，才把返回值转换为进程退出状态。预期操作错误写到标准错误，正常报告位置写到标准输出。这样其他程序可以独立捕获成功输出与诊断信息，也让命令行策略保持在清晰的一层，而不散落到校验、聚合和文件处理内部。

```python
import argparse
import json
import sys
from pathlib import Path

from .core import DataError, load_config, run, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        report = run(config)
        write_report(config.output, report)
    except (OSError, UnicodeError, json.JSONDecodeError, DataError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"report={config.output} complete={report['complete']}")
    return 0 if report["complete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
```

### Configuration and fixture / 配置与测试数据

**English:** Save the first block as `demo/config.json` and the second as `demo/runs.jsonl`. JSONL means one complete JSON value per physical line; the main reader does not accept a pretty-printed multi-line object as one record. All three identifiers must be distinct. Using a tiny fixture makes it possible to establish the expected answer independently of the implementation, which is more informative than generating expected results by calling the same aggregation function again. An independent oracle prevents the implementation and test from sharing the same error and passing together.

**中文：** 第一块保存为 `demo/config.json`，第二块保存为 `demo/runs.jsonl`。这里的逐行 JSON 表示每个物理行对应一个完整 JSON 值；主读取器不会把跨越多行的美化对象当作一条记录。三个运行编号必须不同。小型数据集的价值是可以独立于实现推导正确结果，而不是再次调用同一个聚合函数来生成所谓预期值。只有预期值来自独立依据，测试才能揭示实现错误，避免程序与测试复制了同一种错误却共同通过。

```json
{"schema_version": 1, "input": "runs.jsonl", "output": "report.json", "on_error": "fail", "min_samples": 3}
```

```jsonl
{"run_id":"r1","kernel":"transpose","shape":[32,32],"dtype":"float32","device":"illustrative-device","timing_scope":"device_kernel","source_kind":"fixture","ms":1.0,"passed":true}
{"run_id":"r2","kernel":"transpose","shape":[32,32],"dtype":"float32","device":"illustrative-device","timing_scope":"device_kernel","source_kind":"fixture","ms":3.0,"passed":true}
{"run_id":"r3","kernel":"transpose","shape":[32,32],"dtype":"float32","device":"illustrative-device","timing_scope":"device_kernel","source_kind":"fixture","ms":2.0,"passed":true}
```

### Tests / 测试

**English:** Save as `tests/test_core.py`. The suite focuses on observable contracts: grouping, sample exclusion, invalid numeric values, alias independence, lazy failure timing, provenance, empty input, refusal to overwrite, and import behavior. `TemporaryDirectory` creates independent workspaces, and `addCleanup` ensures cleanup is registered immediately. `subTest` names each invalid numeric partition without duplicating the entire test body. These are standard-library equivalents of the isolation and parameterized reasoning introduced in Day 039; installing pytest is unnecessary for this exercise. See [unittest](https://docs.python.org/3/library/unittest.html). Tools may change, but verification should still follow from the contract.

**中文：** 保存为 `tests/test_core.py`。测试聚焦可观察契约，包括分组、排除失败样本、非法数值、别名隔离、惰性失败时机、来源信息、空输入、拒绝覆盖和导入行为。临时目录提供独立工作空间，清理回调在创建后立即注册；子测试为每类非法数值提供独立上下文，避免重复整段测试代码。这些方法把第三十九天的隔离与参数化思路落实到标准库中，因此不必安装额外测试框架。工具选择可以改变，但从契约推导验证内容的原则保持不变。

```python
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiment_tool.core import (
    Config, DataError, aggregate, load_config, parse_json,
    read_samples, run, validate_sample, write_report,
)


def raw(run_id="r1", ms=2.0):
    return {"run_id": run_id, "kernel": "transpose", "shape": [32, 32],
            "dtype": "float32", "device": "illustrative-device",
            "timing_scope": "device_kernel", "source_kind": "fixture",
            "ms": ms, "passed": True}


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)

    def input_file(self, rows):
        path = self.root / "runs.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                        encoding="utf-8")
        return path

    def test_median_and_failure_exclusion(self):
        bad = raw("r4", 0.01)
        bad["passed"] = False
        rows = [validate_sample(r) for r in
                [raw("r1", 1), raw("r2", 3), raw("r3", 2), bad]]
        group, = aggregate(iter(rows), min_samples=3)
        self.assertEqual(group["median_ms"], 2)
        self.assertEqual(group["failed_count"], 1)
        self.assertEqual(group["passed_count"], 3)

    def test_numeric_boundaries(self):
        for value in [True, "2", -1, float("nan"), float("inf"), 10 ** 400]:
            with self.subTest(value=repr(value)):
                with self.assertRaises(DataError):
                    validate_sample(raw(ms=value))
        self.assertEqual(validate_sample(raw(ms=0)).ms, 0)

    def test_different_conditions_stay_separate(self):
        base = raw()
        changed = copy.deepcopy(base)
        changed.update(run_id="r2", shape=[64, 64])
        groups = aggregate(iter(map(validate_sample, [base, changed])),
                           min_samples=1)
        self.assertEqual(len(groups), 2)
        self.assertEqual(base["shape"], [32, 32])

    def test_input_mutation_cannot_change_sample_shape(self):
        value = raw()
        sample = validate_sample(value)
        value["shape"][0] = 99
        self.assertEqual(sample.shape, (32, 32))

    def test_skip_keeps_line_and_marks_report_incomplete(self):
        path = self.input_file([raw(), raw("r2", True), raw("r3", 4)])
        report = run(Config(path, self.root / "report.json", "skip", 1))
        self.assertEqual(report["rejected_count"], 1)
        self.assertEqual(report["rejected"][0]["line"], 2)
        self.assertFalse(report["complete"])
        self.assertEqual(report["groups"][0]["median_ms"], 3)

    def test_fail_is_observed_on_consumption(self):
        path = self.input_file([raw(), raw("r2", True)])
        rows = read_samples(path, on_error="fail", rejected=[])
        try:
            self.assertEqual(next(rows).run_id, "r1")
            with self.assertRaisesRegex(DataError, r":2:"):
                next(rows)
        finally:
            rows.close()

    def test_duplicate_keys_and_ids(self):
        with self.assertRaisesRegex(DataError, "duplicate JSON key"):
            parse_json('{"ms": 1, "ms": 2}')
        path = self.input_file([raw(), raw()])
        with self.assertRaisesRegex(DataError, "duplicate run_id"):
            run(Config(path, self.root / "out.json", "fail", 1))

    def test_config_anchors_relative_paths(self):
        config_path = self.root / "config.json"
        config_path.write_text(json.dumps({"schema_version": 1,
            "input": "runs.jsonl", "output": "result.json", "on_error": "fail",
            "min_samples": 2}), encoding="utf-8")
        config = load_config(config_path)
        self.assertEqual(config.input, self.root / "runs.jsonl")
        self.assertEqual(config.output, self.root / "result.json")

    def test_incomplete_without_successful_samples(self):
        failed = raw()
        failed["passed"] = False
        report = run(Config(self.input_file([failed]), self.root / "out.json",
                            "fail", 1))
        self.assertIsNone(report["groups"][0]["median_ms"])
        self.assertFalse(report["complete"])

    def test_empty_input_is_not_complete(self):
        path = self.root / "empty.jsonl"
        path.write_text("", encoding="utf-8")
        report = run(Config(path, self.root / "out.json", "fail", 1))
        self.assertEqual(report["groups"], [])
        self.assertFalse(report["complete"])

    def test_writer_refuses_overwrite(self):
        target = self.root / "out.json"
        write_report(target, {"value": 1})
        with self.assertRaises(FileExistsError):
            write_report(target, {"value": 2})
        self.assertEqual(json.loads(target.read_text()), {"value": 1})

    def test_import_has_no_output(self):
        process = subprocess.run([sys.executable, "-c",
            "import experiment_tool.core; import experiment_tool.__main__"],
            text=True, capture_output=True, check=False)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "")
        self.assertEqual(process.stderr, "")


if __name__ == "__main__":
    unittest.main()
```

**English:** Run the commands below from the directory containing `experiment_tool`, `tests`, and `demo`. The successful report has one group, three accepted and passed samples, no rejected records, and minimum, median, and maximum durations of 1, 2, and 3. A second invocation targeting the same report should fail because the destination already exists. Preserve that report as an artifact or choose a new output path in a copied configuration before another successful run; silently deleting previous evidence is not part of the tool's behavior. The operator must explicitly choose the rerun policy as part of the reproducible workflow.

**中文：** 在包含工具包、测试目录和示例目录的位置执行下列命令。成功报告应只有一个分组，接收并通过三个样本，没有拒绝记录，最小值、中位数和最大值依次为一、二、三。第二次向同一报告位置执行应失败，因为目标已经存在。下一次成功运行前，可以保留旧报告作为产物，再在复制的配置中选择新输出路径。工具不会悄悄删除上一次证据；重复执行的处理方式也是可复现工作流的一部分，必须由操作者明确决定。

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m experiment_tool demo/config.json
python3 -m json.tool demo/report.json
```

## 9. Controlled failures and interpretation / 可控失败与结果解释

**English:** Create each failure case in its own directory using the following script. It copies the teaching fixture, modifies one condition, and writes a fresh configuration and input. The process runner records exit status and captures both output channels. There is no GPU activity anywhere in this failure experiment. Keeping cases independent is essential: otherwise a report left by an earlier run can cause an output-exists error that hides the malformed-input behavior you actually intended to test. Confirm that the intended condition caused the failure, rather than stale environment state merely producing the expected nonzero status.

**中文：** 使用下列脚本在不同目录中建立每个失败场景。脚本复制教学测试数据，每次修改一个条件，并写入新的配置与输入；进程运行器记录退出状态，同时捕获两个输出通道。整个失败实验都没有 GPU 活动。场景隔离非常重要，否则上次留下的报告可能触发目标已存在错误，掩盖你原本想检查的非法输入行为。排查失败时，应先确认是预期条件触发了错误，而不是环境残留替你制造了一个看似符合预期的非零退出码。

```python
import json
import subprocess
import sys
import tempfile
from pathlib import Path

source = [json.loads(line) for line in
          Path("demo/runs.jsonl").read_text(encoding="utf-8").splitlines()]
root = Path(tempfile.mkdtemp(prefix="course02-failures-"))

for name, policy, expected in [("strict", "fail", 2), ("skip", "skip", 3),
                                ("duplicate", "fail", 2), ("empty", "fail", 3)]:
    folder = root / name
    folder.mkdir()
    rows = [dict(row) for row in source]
    if name in ("strict", "skip"):
        rows[1]["ms"] = True
    elif name == "duplicate":
        rows[1]["run_id"] = rows[0]["run_id"]
    else:
        rows = []
    (folder / "runs.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    config = {"schema_version": 1, "input": "runs.jsonl",
              "output": "report.json", "on_error": policy, "min_samples": 3}
    path = folder / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "experiment_tool", str(path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode == expected, (name, result.stdout, result.stderr)
    exists = (folder / "report.json").exists()
    assert exists == (name in ("skip", "empty"))
    print(name, result.returncode, f"report_exists={exists}")
print(f"artifacts={root}")
```

**English:** The expected exit codes are 2 for strict invalid input, 3 for skipped invalid input, 2 for duplicate identifiers, and 3 for empty input. The skip case writes a report containing two valid samples and the rejected second line, but it remains incomplete. The empty case writes an explicitly incomplete report with no groups. The strict and duplicate cases create no report. These distinctions protect downstream consumers from treating every existing JSON report as successful evidence or treating every nonzero status as the same failure. Interpret report existence, completeness, and process status together.

**中文：** 预期退出码依次为：严格模式非法输入返回二，跳过模式非法输入返回三，重复编号返回二，空输入返回三。跳过场景写出报告，保留两个合法样本并记录第二行被拒绝，但报告仍不完整；空输入写出没有分组的明确不完整报告。严格模式与重复编号场景则不产生报告。这些差异防止下游把任何存在的 JSON 报告都当成成功证据，也避免把所有非零状态视为同一种失败。报告存在性、内容完整性和进程状态需要配合解读。

**English:** Inspect `complete` separately from individual group statistics. A group can meet the minimum number of successful samples and still contain a failed correctness observation; the overall report must then remain incomplete. Similarly, a rejected record can make the report incomplete even when every surviving group has enough samples. Completeness here means compliance with the teaching contract, not proof of measurement quality. A dataset that lies about its provenance can pass structural validation, so raw logs and the producer's procedure remain necessary for scientific or engineering claims. A validator checks consistency of the representation; it cannot prove that the represented event actually occurred.

**中文：** 应把报告完整性与单组统计分开检查。某组可能已经满足成功样本数要求，却仍包含一次正确性失败，此时整体报告仍然不完整；被拒绝的记录也可能让报告不完整，即使保留下来的每组都有足够样本。这里的完整只表示满足教学契约，不代表测量质量已经得到证明。数据集如果虚假标注来源，结构校验仍可能通过，因此任何科学或工程结论都还需要原始日志与数据生产过程。校验工具能检查表达是否一致，不能凭空证明表达的事情真实发生过。

## 10. Test reasoning and maintenance / 测试推理与维护

**English:** Derive tests from partitions, not from a desire for a large test count. For a nonnegative finite duration, useful cases include zero, an ordinary positive value, a negative value, a string, a boolean, infinity, NaN, and conversion overflow. Each challenges a different rule. Ten arbitrary positive floats mostly repeat the same rule. For aggregation, use an unsorted odd-sized sample with a hand-computable median, then add a failed observation whose tiny duration would visibly corrupt the answer if it were mistakenly included.

**中文：** 测试应从输入分区推导，而不是为了数量好看。对于有限且非负的耗时，有用场景包括零、普通正数、负数、字符串、布尔值、无穷、非数值和转换溢出，它们分别挑战不同规则；十个随意选择的正浮点数，多半只重复同一规则。聚合测试应使用未排序且可手算中位数的奇数个样本，再加入耗时极小的正确性失败记录。如果错误地把失败记录算进去，答案会明显改变，这样测试才对真实错误具有敏感性。

**English:** A test should fail for a recognizable broken implementation. If a median test uses identical durations, replacing the median with the first sample would still pass. If a copy test checks only equality before mutation, shallow and deep copies appear equivalent. If a resource test merely observes a generator eventually finish, it says nothing about early termination. State the defect each test is intended to detect, and choose observations that distinguish the correct behavior from that defect. This produces a smaller but more informative suite than duplicating implementation details line by line.

**中文：** 测试应该能够使一种可识别的错误实现失败。如果中位数测试使用完全相同的耗时，误写成取第一个样本也能通过；如果复制测试只检查修改之前是否相等，浅拷贝和深拷贝看起来没有差别；如果资源测试只观察生成器最终耗尽，就无法说明提前终止时的行为。应先说明每个测试想识别哪种缺陷，再选择能区分正确行为和该缺陷的观测。这样通常能得到更小却更有信息量的测试集，避免逐行复述实现而没有独立判断。

**English:** Distinguish a teaching implementation's limitations from bugs. Retaining all samples is a documented memory tradeoff, exclusive output creation is a documented publication policy, and refusing unknown fields is a documented schema rule. They become change requests when requirements evolve. By contrast, including failed durations or accepting a boolean as a duration violates an existing contract and is a bug. Write a regression test around the violated behavior, change the narrowest relevant layer, and rerun the suite; avoid rebuilding the architecture merely because a small validation branch was wrong.

**中文：** 要区分教学实现的限制与程序错误。保留全部样本是明确的内存取舍，独占创建输出是明确的发布策略，拒绝未知字段是明确的模式规则；需求改变时，它们成为可以讨论的变更。相反，把失败耗时计入统计，或把布尔值接受为耗时，违反现有契约，属于错误。修复时应围绕违反的行为增加回归测试，修改最直接相关的层，再运行测试。不能因为一个小校验分支错误，就在没有需求依据的情况下重新设计整个系统。

## 11. Ten exercises with reference answers / 十道习题与参考答案

### Exercise 1: Copy boundaries / 习题一：复制边界

**English:** Exercise: Two experiment variants are made with `baseline.copy()`, and each contains the same nested `shape` list. One variant changes its first dimension. Predict which values change and choose a repair when only the shape must be independent. Reference answer: every dictionary still sharing that list observes the mutation; the dictionaries themselves are distinct. Copy or normalize the shape explicitly, for example with `tuple(baseline["shape"])`, and create a replacement tuple when changing a dimension. A deep copy also works for this simple data, but copies more structure than the stated requirement needs. Identify the exact shared layer, rather than naming a copy function without explaining it.

**中文：** 练习：两个实验变体都由基线字典浅拷贝得到，内部形状仍是同一个列表，其中一个变体修改第一维。预测哪些值改变，并在只要求形状独立时选择修复方法。参考答案：所有仍共享该列表的字典都会看到修改，尽管外层字典不同。可以显式复制或把形状规范化为元组，需要修改维度时再创建替代元组。对这种简单数据，深拷贝也能解决问题，但它复制的结构超过题目要求。回答的重点是指出共享发生在哪一层，而不只是写出某个复制函数名称。

### Exercise 2: Numeric meaning / 习题二：数值含义

**English:** Exercise: Why do `isinstance(value, (int, float))` and `value >= 0` fail to establish a valid duration? Reference answer: booleans satisfy the type test because `bool` subclasses `int`, and infinity satisfies the range check. NaN requires explicit handling because ordinary comparisons have unusual results. The course uses exact built-in numeric types, controlled float conversion, `isfinite`, and a nonnegative check. Accepting zero is a schema decision, not evidence that a real operation consumed no time. A measurement producer should separately describe timer resolution and how zeros are interpreted. A complete answer distinguishes representation type, mathematical range, and business meaning rather than merely adding another comparison.

**中文：** 练习：为什么宽泛数值类型检查加非负比较，仍不能证明耗时有效？参考答案：布尔类型继承整数，因此会通过类型检查；正无穷也会通过非负比较，非数值的比较行为则需要特别处理。本课采用精确内置类型检查、受控浮点转换、有限性检查和非负范围检查。允许零是数据模式决定，不表示真实操作完全不消耗时间。测量生产者仍应解释计时器分辨率以及零值含义。完整答案需要分别讨论表示类型、数学取值和业务语义，而不是只增加一个比较符号。

### Exercise 3: Callable behavior / 习题三：可调用行为

**English:** Exercise: A logging decorator calls its wrapped function but omits `return`, and catches `Exception` to print a warning. What contracts changed? Reference answer: successful return values become `None`, and many failures stop propagating. Add result forwarding and allow unexpected errors to escape; use `finally` only for the observation that must happen on both success and failure. Test with a known return value and a known exception. Preserving `__name__` through `wraps` is useful but cannot repair either behavioral defect. Evaluate transparency through call outcomes, not attractive logging output.

**中文：** 练习：日志装饰器调用原函数却省略返回语句，同时捕获全部普通异常并打印警告，改变了什么契约？参考答案：成功返回值变成空值，许多失败也不再向外传播。应转发原结果，让不该处理的错误继续抛出；需要成功失败都执行的观测逻辑放进最终清理分支。测试至少使用一个已知返回值和一种已知异常。保留函数名称的工具虽然有用，却不能修复这两个行为问题。评价包装器是否透明，需要观察调用结果，而不是仅观察输出日志是否漂亮。

### Exercise 4: Exhaustion and two passes / 习题四：耗尽与两次遍历

**English:** Exercise: A report first executes `sum(1 for _ in samples)` and then computes statistics from the same generator. Why is the second result empty? Reference answer: the first pass consumed the iterator. Decide whether the source should be reopened, materialized once, or processed in one pass. Reopening a changing file may observe a different dataset, while materialization uses memory; neither is automatically correct. For this tool, aggregation already observes each sample once and can update counts while grouping, so a separate preliminary counting pass is unnecessary. Explain where iteration progress lives and how the chosen repair affects consistency and resources.

**中文：** 练习：报告先遍历生成器计数，再用同一个生成器计算统计，为什么第二次结果为空？参考答案：第一次已经消费迭代器。应根据要求选择重新打开源文件、一次性实体化数据，或者在同一次遍历中完成工作。重新打开可能遇到已变化的数据集，实体化则占用内存，两者都不是无条件正确。本工具聚合时已经逐条观察样本，可以同时更新计数，没有必要预先单独遍历。回答应解释进度保存在哪里，以及所选修复对一致性和资源的影响，而不仅是建议再调用一次读取函数。

### Exercise 5: Early resource release / 习题五：提前释放资源

**English:** Exercise: A caller reads one value from a generator whose file context spans `yield`, then retains the generator without consuming it. Is the file necessarily closed? Reference answer: no; suspension can leave the context active. Use `contextlib.closing` around consumption or call `close` in a `finally` block. Closing a started generator runs its pending cleanup in normal Python control flow. This is different from relying on object destruction, and does not promise cleanup after abrupt process termination. Explain both the ordinary guarantee and its boundary.

**中文：** 练习：调用方从跨越产出点持有文件上下文的生成器读取一个值，然后保留生成器却不继续消费，文件是否必然关闭？参考答案：不会，暂停可能让上下文保持活动。消费时可以使用关闭上下文包装，或在最终清理分支显式调用关闭方法。关闭已启动生成器会在正常 Python 控制流中执行待完成清理，这不同于依赖对象析构，也不保证进程被强制终止后仍能清理。需要同时说明正常保证及其边界，避免把确定性释放误说成任何故障条件下都能执行。

### Exercise 6: Paths and launch location / 习题六：路径与启动位置

**English:** Exercise: A configuration at `/tmp/demo/config.json` contains `input: "runs.jsonl"`. The command is launched from `/tmp/work`. Which path should this tool read, and why can another script behave differently? Reference answer: the tool resolves the input under the configuration directory, yielding `/tmp/demo/runs.jsonl`. A script that directly opens the string would normally use the process working directory and read `/tmp/work/runs.jsonl`. Neither convention is imposed by JSON; the application must define it. Reproduce this distinction with an absolute configuration path and a subprocess using a different working directory. Control the launch directory in the test; one run from a coincidentally matching directory does not establish portability.

**中文：** 练习：配置位于 `/tmp/demo/config.json`，输入填写相对文件名，但命令从另一个目录启动，本工具读取哪里，为什么别的脚本可能不同？参考答案：本工具以配置目录为基准，读取该目录下的输入；直接打开字符串的脚本通常以进程当前工作目录为基准。两种约定都不是 JSON 强制规定的，必须由应用明确选择。可用配置绝对路径配合不同工作目录的子进程复现区别。测试路径行为时，需要控制启动位置，不能只在碰巧相同的目录里运行一次就断言配置可移植。

### Exercise 7: Duplicate observations / 习题七：重复观测

**English:** Exercise: Two lines have different run identifiers but equal durations; two other lines have the same identifier. Which duplication is legitimate? Reference answer: equal durations can be independent observations and must remain in the distribution. Repeated identifiers violate this tool's uniqueness contract and are rejected rather than overwritten. If a producer legitimately uses identifiers local to separate files, extend the identity to include a source identifier before merging files. Removing duplicates by duration or kernel name destroys information and cannot substitute for designing the correct identity. First decide whether a record represents a run, a request, or an aggregate; that determines which duplicates violate identity.

**中文：** 练习：两行运行编号不同但耗时相同，另外两行编号相同，哪一种重复可以接受？参考答案：相同耗时可以来自独立观测，必须保留在分布中；重复编号违反本工具唯一性契约，应拒绝而不是覆盖。如果生产者的编号只在各文件内部唯一，那么合并多文件之前，应把来源编号加入身份定义。按耗时或核函数名去重会破坏信息，不能代替设计正确身份。需要先确定记录代表一次运行、一次请求还是一组汇总，再决定何种重复说明数据有问题。

### Exercise 8: Frozen records / 习题八：冻结记录

**English:** Exercise: A frozen dataclass has `shape: list[int]`. Does `record.shape.append(64)` necessarily fail? Reference answer: no; frozen attributes do not recursively freeze their contents. A tuple of validated integers is suitable for the shape snapshot used here. If arbitrary nested metadata is introduced later, either normalize it into immutable representations, copy it at the boundary, or explicitly document ownership and permitted mutation. A type annotation alone does not choose that policy, and returning a reference to mutable internals can reopen the same sharing problem. Trace the entire access path even when construction already makes a copy.

**中文：** 练习：冻结数据类把形状存成整数列表，对该列表追加元素是否必然失败？参考答案：不会，冻结属性不等于递归冻结内容。本课的形状快照适合用经过校验的整数元组。如果之后引入任意嵌套元数据，需要把它规范化为不可变表示、在边界复制，或者明确说明谁拥有数据以及允许谁修改。类型注解本身不会替你选择策略。即使构造时复制过，后来把内部可变容器直接返回，也可能重新打开共享修改问题，所以应追踪完整访问路径。

### Exercise 9: Meaningful tests / 习题九：有意义的测试

**English:** Exercise: Design a test that distinguishes a correct median from “take the first duration,” and another that detects accidental inclusion of failed observations. Reference answer: use successful values 9, 1, and 3 with expected median 3; then add a failed value 0 and require the same successful median and a failed count of one. Use fresh objects so the added failure cannot mutate the original scenario. Check the visible result and counts, not the private grouping container type, so a future implementation can change its internal algorithm while preserving the contract.

**中文：** 练习：设计一个能区分正确中位数与取第一个耗时的测试，再设计一个能识别失败样本被误算的测试。参考答案：成功数值使用九、一、三，预期中位数为三；再加入耗时为零的失败记录，要求成功中位数不变且失败计数为一。每个场景使用新对象，避免新增失败记录意外修改原场景。验证应围绕可见结果和计数，而不是私有分组容器类型，这样未来实现可以改变算法，只要契约相同就继续通过测试，减少测试与实现的不必要耦合。

### Exercise 10: Evidence and performance / 习题十：证据与性能

**English:** Exercise: The reporting command now runs twice as fast after a Python refactor. Can the course claim a GPU speedup? Reference answer: no; the measured work is report processing, and the fixture contains no device measurements. A GPU comparison requires an actual workload, a defined timing boundary, compatible conditions, correctness checks, repeated observations, and preserved measurement provenance. A faster tool can improve engineering productivity without changing the kernel. Report those benefits separately and describe exactly which timer and workload support each numerical claim. Ask what was measured before asking how much it improved; the project name does not determine the metric.

**中文：** 练习：Python 重构后报告命令运行速度变成原来的两倍，能否宣称 GPU 加速？参考答案：不能，被测工作是报告处理，测试数据也不含设备测量。GPU 比较需要真实工作负载、明确计时边界、兼容条件、正确性检查、重复观测和保留的测量来源。更快的工具可以提升工程效率，而核函数本身完全不变。应分别描述这些收益，并为每个数值结论说明计时器与工作负载。判断性能结论时，首先问测了什么，再问数值提高多少，而不是由项目名称决定解释。

## 12. Acceptance and next steps / 验收与下一步

**English:** Verification on 2026-09-18 used the exact source blocks printed above under CPython 3.14.4. All twelve unit tests passed; the successful invocation produced `complete=True` and the expected median of 2. The four failure cases returned the specified statuses and created reports only in the skip and empty cases. These results verify the documented examples on one local environment. They do not establish compatibility with every Python implementation, resistance to concurrent file replacement, or correctness for an unlimited input size. When adapting the example, retain these checks and add evidence for any newly claimed guarantee.

**中文：** 二〇二六年九月十八日的核验使用上方展示的完整源代码，在 CPython 三点十四点四下执行。十二个单元测试全部通过，成功调用生成完整报告，中位数符合预期值二。四种失败场景返回指定状态，并且只有跳过与空输入场景产生报告。这些结果验证了一个本地环境中的文档示例，不代表兼容所有 Python 实现，也没有证明能抵抗并发文件替换或处理无限大的输入。改造示例时应保留这些检查，并为任何新增保证补充对应证据。

**English:** Accept the exercise only when you can recreate the package from this document, pass its twelve tests, explain the successful report by hand, and reproduce all four failure statuses. Also explain why repeated execution refuses to overwrite, why empty input is incomplete, why grouping includes timing scope and source kind, and why the generator does not make the complete pipeline constant-memory. Keep your interpreter version, command output, fixture, and generated report together. Those artifacts document a reproducible Python-tool experiment, with no implication that GPU benchmarking has occurred. Acceptance requires explanation and reproducible behavior, not merely a passing terminal message.

**中文：** 验收要求是能够仅凭本文重建工具包，通过十二个测试，手算解释成功报告，并复现四种失败状态。还应说明重复运行为什么拒绝覆盖，空输入为什么不完整，分组为什么包含计时范围与数据来源，以及生成器为什么没有让整个流水线变成常量内存。把解释器版本、命令输出、测试数据和生成报告保存在一起。这些产物记录的是可复现的 Python 工具实验，不隐含任何已经进行 GPU 基准测量的意思。验收关注解释能力与可重复行为，而不只是终端出现通过字样。

**English:** For the next iteration, connect the tool to one real producer rather than adding many abstractions at once. Start by agreeing on units, run identity, correctness policy, and provenance fields; preserve its raw output before normalization. Add only the schema fields that distinguish genuinely different experiment conditions. If the dataset becomes large, profile memory and decide whether to retain exact medians, use external storage, or adopt a documented approximation. Each extension should have a concrete reason and a test that demonstrates the new contract, so the tool grows with the experiments it actually serves. This path turns syntax knowledge into engineering practice while retaining the source of each conclusion.

**中文：** 下一轮应连接一个真实数据生产者，而不是一次增加很多抽象。先约定单位、运行身份、正确性策略和来源字段，规范化之前保留原始输出；只加入能够区分实际实验条件的模式字段。如果数据规模扩大，再测量内存，并决定保留精确中位数、采用外部存储，还是使用明确说明的近似方法。每项扩展都应有具体理由，以及能够展示新契约的测试，使工具随着它真正服务的实验成长。这样的路线能把语法知识逐步转化为可靠工程能力，同时保留每个结论的来源。

## Official references / 官方参考资料

**English:** The linked documentation below was checked on 2026-09-18. It defines the language and library behavior used by the original exercises; it is not a source of GPU measurements. Prefer the version matching your interpreter when an API detail differs. The local run and failure artifacts described above are the verification evidence for this particular implementation.

**中文：** 下列文档于二〇二六年九月十八日核验，用于确认原创练习采用的语言和标准库行为，不是 GPU 测量来源。接口细节出现版本差异时，应优先使用与解释器对应的文档。上述本地运行结果和失败场景产物，才是这份具体实现的验证证据。

- [Data structures / 数据结构](https://docs.python.org/3/tutorial/datastructures.html)
- [Function definitions and arguments / 函数定义与参数](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [Classes, scope, and generators / 类、作用域与生成器](https://docs.python.org/3/tutorial/classes.html)
- [Shallow and deep copying / 浅拷贝与深拷贝](https://docs.python.org/3/library/copy.html)
- [Type hints / 类型注解](https://docs.python.org/3/library/typing.html)
- [Callable utilities / 可调用对象工具](https://docs.python.org/3/library/functools.html)
- [Context managers / 上下文管理器](https://docs.python.org/3/library/contextlib.html)
- [JSON encoding and decoding / JSON 编解码](https://docs.python.org/3/library/json.html)
- [Filesystem paths / 文件系统路径](https://docs.python.org/3/library/pathlib.html)
- [Modules and packages / 模块与包](https://docs.python.org/3/tutorial/modules.html)
- [Data classes / 数据类](https://docs.python.org/3/library/dataclasses.html)
- [Unit testing / 单元测试](https://docs.python.org/3/library/unittest.html)
