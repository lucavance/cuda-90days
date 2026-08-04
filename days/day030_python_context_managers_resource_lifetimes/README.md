# Day 030: Python Context Managers and Resource Lifetimes / Python 上下文管理器与资源生命周期

Date / 日期: 2026-08-04

## Topic / 主题

**English:** Python context managers and deterministic resource cleanup:
the <code>with</code> statement, file lifetimes, <code>__enter__()</code>,
<code>__exit__()</code>, exception propagation and suppression, nested
contexts, <code>contextlib.contextmanager</code>, and the interaction between
lazy generators and open files.

**中文：** Python 上下文管理器与确定性资源清理：<code>with</code> 语句、
文件生命周期、<code>__enter__()</code>、<code>__exit__()</code>、异常传播与
抑制、嵌套上下文、<code>contextlib.contextmanager</code>，以及惰性生成器与
打开文件之间的生命周期关系。

## Goal / 目标

**English:** Build a reliable model for when resources are acquired and
released, understand how context managers behave during normal and exceptional
control flow, and avoid returning lazy iterators that depend on resources which
have already been closed.

**中文：** 建立可靠的资源生命周期模型，理解资源何时获取、何时释放，掌握上下文
管理器在正常流程和异常流程中的行为，并避免返回依赖已关闭资源的惰性迭代器。

## Core Mental Model / 核心思维模型

**English:** A <code>with</code> statement enters a context by calling
<code>__enter__()</code>, binds its return value after <code>as</code>, and
always attempts to leave the context through <code>__exit__()</code>.
The context manager—not the <code>with</code> keyword itself—defines the actual
cleanup behavior. Exceptions are passed to <code>__exit__()</code>; a truthy
return value suppresses an exception, while a false value lets it propagate.

**中文：** <code>with</code> 语句通过调用 <code>__enter__()</code> 进入上下文，
把它的返回值绑定到 <code>as</code> 后面的变量，并总是尝试通过
<code>__exit__()</code> 离开上下文。真正的清理行为由上下文管理器定义，而不是
由 <code>with</code> 关键字统一规定。异常会传给 <code>__exit__()</code>；
返回真值会抑制异常，返回假值则让异常继续传播。

## 10 Concept Questions / 10 道概念题

### 1. File state after leaving a context / 离开上下文后的文件状态

**Question (English):** What does the final line print? After the
<code>with</code> block, has the name <code>f</code> disappeared, or has the
file resource been closed?

**问题（中文）：** 最后一行打印什么？退出 <code>with</code> 后，名字
<code>f</code> 是消失了，还是文件资源被关闭了？

~~~python
with open("results.txt", "w") as f:
    f.write("ok\n")

print(f.closed)
~~~

**Explanation (English):** A <code>with</code> statement does not create a
separate variable scope in Python. The file object remains bound to
<code>f</code>, but the file context manager closes its operating-system
resource while leaving the block.

**解说（中文）：** Python 的 <code>with</code> 不会创建独立的变量作用域。文件
对象仍然绑定在 <code>f</code> 上，但文件上下文管理器会在离开代码块时关闭其
操作系统资源。

**Correct Answer (English):** It prints:

~~~text
True
~~~

The name <code>f</code> still exists, and <code>f.closed</code> is
<code>True</code>. A later write through that closed object raises
<code>ValueError</code>.

**正确答案（中文）：** 输出为：

~~~text
True
~~~

名字 <code>f</code> 仍然存在，且 <code>f.closed</code> 为
<code>True</code>。之后再通过这个已关闭的对象写入会抛出
<code>ValueError</code>。

### 2. Cleanup when an exception occurs / 发生异常时的资源清理

**Question (English):** What is printed to the terminal? Does the file close
even though division raises an exception, and does the file context manager
silently consume that exception?

**问题（中文）：** 终端会打印什么？即使除法触发异常，文件是否仍会关闭？文件
上下文管理器会不会静默吞掉这个异常？

~~~python
try:
    with open("results.txt", "w") as f:
        f.write("start\n")
        1 / 0
except ZeroDivisionError:
    print("caught")

print(f.closed)
~~~

**Explanation (English):** Writing to a file is not terminal output. When the
exception leaves the block, the file's <code>__exit__()</code> closes the file.
The standard file context manager does not suppress this exception, so it
continues to the surrounding <code>except</code>.

**解说（中文）：** 写入文件不等于向终端打印。当异常离开代码块时，文件的
<code>__exit__()</code> 会关闭文件。标准文件上下文管理器不会抑制这个异常，
因此异常继续传播到外层的 <code>except</code>。

**Correct Answer (English):** The terminal output is:

~~~text
caught
True
~~~

The text <code>start</code> is written into the file rather than printed.
Cleanup occurs before the outer handler catches <code>ZeroDivisionError</code>.

**正确答案（中文）：** 终端输出为：

~~~text
caught
True
~~~

文本 <code>start</code> 被写进文件，而不是打印到终端。外层处理器捕获
<code>ZeroDivisionError</code> 之前，文件清理已经完成。

### 3. The value bound by as / as 所绑定的值

**Question (English):** What is the complete output? Does <code>value</code>
refer to the original <code>Demo</code> instance or to the value returned by
<code>__enter__()</code>?

**问题（中文）：** 完整输出是什么？<code>value</code> 指向原始的
<code>Demo</code> 实例，还是 <code>__enter__()</code> 的返回值？

~~~python
class Demo:
    def __enter__(self):
        print("enter")
        return "resource"

    def __exit__(self, exc_type, exc_value, traceback):
        print("exit", exc_type is None)

with Demo() as value:
    print(value)
~~~

**Explanation (English):** Entering the block first calls
<code>__enter__()</code>. Its return value—not necessarily the context-manager
object—is assigned to the name after <code>as</code>. With no exception, all
three exception arguments passed to <code>__exit__()</code> are
<code>None</code>.

**解说（中文）：** 进入代码块时首先调用 <code>__enter__()</code>。赋给
<code>as</code> 后变量的是它的返回值，不一定是上下文管理器对象自身。没有异常
时，传给 <code>__exit__()</code> 的三个异常参数都是 <code>None</code>。

**Correct Answer (English):** The output is:

~~~text
enter
resource
exit True
~~~

The name <code>value</code> is bound to the string
<code>"resource"</code>.

**正确答案（中文）：** 输出为：

~~~text
enter
resource
exit True
~~~

名字 <code>value</code> 绑定到字符串 <code>"resource"</code>。

### 4. Suppressing an exception with __exit__ / 使用 __exit__ 抑制异常

**Question (English):** What is the complete output, and what effect does
returning <code>True</code> from <code>__exit__()</code> have?

**问题（中文）：** 完整输出是什么？<code>__exit__()</code> 返回
<code>True</code> 会产生什么效果？

~~~python
class Guard:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(exc_type.__name__)
        return True

with Guard():
    print("before")
    raise ValueError("bad")

print("after")
~~~

**Explanation (English):** The exception details are delivered to
<code>__exit__()</code>. A truthy return value means that the context manager
has handled the exception, so execution continues after the
<code>with</code> statement.

**解说（中文）：** 异常信息会被传给 <code>__exit__()</code>。返回真值表示上下文
管理器已经处理该异常，因此程序会从 <code>with</code> 语句之后继续执行。

**Correct Answer (English):** The output is:

~~~text
before
ValueError
after
~~~

Returning <code>False</code> or <code>None</code> instead would allow the
exception to continue propagating.

**正确答案（中文）：** 输出为：

~~~text
before
ValueError
after
~~~

如果改为返回 <code>False</code> 或 <code>None</code>，异常就会继续向外传播。

### 5. Nested context order / 嵌套上下文的顺序

**Question (English):** What is the complete output order, and why is the exit
order the reverse of the entry order?

**问题（中文）：** 完整输出顺序是什么？为什么退出顺序与进入顺序相反？

~~~python
class Trace:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print("enter", self.name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("exit", self.name)

with Trace("A"):
    with Trace("B"):
        print("work")
~~~

**Explanation (English):** Nested resources are released in last-in,
first-out order. Resource <code>B</code> is acquired after
<code>A</code>, so it must be released before <code>A</code>. This preserves
dependencies between nested resources.

**解说（中文）：** 嵌套资源按照“后进先出”的顺序释放。资源 <code>B</code> 在
<code>A</code> 之后获取，因此必须先于 <code>A</code> 释放，从而维持嵌套资源
之间的依赖关系。

**Correct Answer (English):** The output is:

~~~text
enter A
enter B
work
exit B
exit A
~~~

**正确答案（中文）：** 输出为：

~~~text
enter A
enter B
work
exit B
exit A
~~~

### 6. A generator-based context manager / 基于生成器的上下文管理器

**Question (English):** What is printed? Which context-manager phases
correspond to the code before and after <code>yield</code>?

**问题（中文）：** 代码会打印什么？<code>yield</code> 前后的代码分别对应上下文
管理器的哪个阶段？

~~~python
from contextlib import contextmanager

@contextmanager
def managed():
    print("acquire")
    try:
        yield "resource"
    finally:
        print("release")

with managed() as value:
    print(value)
~~~

**Explanation (English):** The code before <code>yield</code> performs entry
and acquisition. The yielded value is bound after <code>as</code>. When the
block exits, execution resumes after <code>yield</code> for cleanup. A
<code>finally</code> block ensures that cleanup also runs during exception
unwinding.

**解说（中文）：** <code>yield</code> 之前的代码负责进入和获取资源；
<code>yield</code> 产生的值绑定到 <code>as</code> 后的变量。代码块退出时，
执行会从 <code>yield</code> 之后恢复并完成清理。使用 <code>finally</code>
可以确保异常展开时也执行清理。

**Correct Answer (English):** The output is:

~~~text
acquire
resource
release
~~~

**正确答案（中文）：** 输出为：

~~~text
acquire
resource
release
~~~

### 7. Exception handling around yield / 在 yield 周围处理异常

**Question (English):** What is printed? Why does the
<code>ValueError</code> not continue propagating?

**问题（中文）：** 代码会打印什么？为什么 <code>ValueError</code> 没有继续
向外传播？

~~~python
from contextlib import contextmanager

@contextmanager
def guard():
    try:
        yield
    except ValueError:
        print("handled")

with guard():
    print("work")
    raise ValueError("bad")

print("after")
~~~

**Explanation (English):** The exception from the <code>with</code> body is
thrown back into the generator at its suspended <code>yield</code>. The
<code>except</code> clause catches it, and the generator then finishes
normally. Because it does not re-raise the exception, the context manager
suppresses it.

**解说（中文）：** <code>with</code> 主体中的异常会被抛回生成器暂停的
<code>yield</code> 位置。<code>except</code> 捕获异常后，生成器正常结束。由于
它没有重新抛出异常，上下文管理器会抑制该异常。

**Correct Answer (English):** The output is:

~~~text
work
handled
after
~~~

To let the exception continue, the handler must execute <code>raise</code>.

**正确答案（中文）：** 输出为：

~~~text
work
handled
after
~~~

如果要让异常继续传播，处理器必须执行 <code>raise</code>。

### 8. Returning a lazy expression backed by a closed file / 返回依赖已关闭文件的惰性表达式

**Question (English):** Assuming the file exists and is nonempty, does
<code>next(lines)</code> read the first line successfully? What resource
lifetime problem exists?

**问题（中文）：** 假设文件存在且非空，<code>next(lines)</code> 能否成功读取
第一行？这里存在什么资源生命周期问题？

~~~python
def read_lines(path):
    with open(path) as f:
        return (line.strip() for line in f)

lines = read_lines("results.txt")
print(next(lines))
~~~

**Explanation (English):** Creating and returning the generator expression
does not consume its lines. Returning from the function first leaves the
<code>with</code> block and closes the file. The later call to
<code>next()</code> then attempts lazy iteration over a closed file.

**解说（中文）：** 创建并返回生成器表达式并不会立即消费其中的行。函数返回时会
先离开 <code>with</code> 代码块并关闭文件；之后调用 <code>next()</code> 才尝试
惰性迭代，此时文件已经关闭。

**Correct Answer (English):** It does not read the first line. It raises an
error similar to:

~~~text
ValueError: I/O operation on closed file
~~~

The lifetime of the lazy consumer has escaped the lifetime of the resource it
needs.

**正确答案（中文）：** 它无法读取第一行，而会抛出类似错误：

~~~text
ValueError: I/O operation on closed file
~~~

惰性消费者的生命周期超过了它所依赖资源的生命周期。

### 9. Keeping a file open across generator yields / 在生成器 yield 之间保持文件打开

**Question (English):** When is the file opened in this version? Is it closed
immediately after the first <code>next()</code>, and when is it normally
closed?

**问题（中文）：** 在这个版本中，文件何时打开？第一次
<code>next()</code> 后是否立即关闭？它通常在什么时候关闭？

~~~python
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

lines = read_lines("results.txt")
first = next(lines)
~~~

**Explanation (English):** Because the function contains <code>yield</code>,
calling it only creates a generator. The first <code>next()</code> begins
execution, opens the file, and pauses at the first <code>yield</code>. While
paused there, the generator is still inside the <code>with</code> block, so
the file remains open.

**解说（中文）：** 由于函数中包含 <code>yield</code>，调用函数时只会创建生成器。
第一次 <code>next()</code> 才开始执行、打开文件，并暂停在第一个
<code>yield</code>。暂停期间生成器仍处于 <code>with</code> 代码块中，因此
文件保持打开。

**Correct Answer (English):** The file is not opened when
<code>read_lines()</code> is called. It opens on the first
<code>next()</code> and remains open after that yielded item. It closes when
the generator exhausts, is explicitly closed, or unwinds because of an
exception. Important resources should not depend on eventual garbage
collection for timely cleanup.

**正确答案（中文）：** 调用 <code>read_lines()</code> 时文件尚未打开。第一次
<code>next()</code> 时文件才打开，并在产生该元素后继续保持打开。生成器耗尽、
被显式关闭或因异常展开时，文件会关闭。重要资源不应依赖未来某次垃圾回收来及时
清理。

### 10. Explicitly closing a generator / 显式关闭生成器

**Question (English):** Assuming the file has at least two lines, what does
<code>lines.close()</code> do to the generator and its file? Does the final
<code>next(lines)</code> return the second line?

**问题（中文）：** 假设文件至少有两行，<code>lines.close()</code> 会如何影响
生成器及其文件？最后一次 <code>next(lines)</code> 会返回第二行吗？

~~~python
lines = read_lines("results.txt")

print(next(lines))
lines.close()
print(next(lines))
~~~

**Explanation (English):** Closing a suspended generator injects
<code>GeneratorExit</code> at its suspension point. Stack unwinding leaves
the <code>with</code> block, so the file context manager closes the file.
The generator is then permanently exhausted.

**解说（中文）：** 关闭一个暂停中的生成器，会在其暂停位置注入
<code>GeneratorExit</code>。调用栈展开并离开 <code>with</code> 代码块，文件
上下文管理器因此关闭文件。随后该生成器永久耗尽。

**Correct Answer (English):** The first line from the file is printed.
<code>close()</code> then terminates the generator and closes the file. The
final <code>next(lines)</code> raises <code>StopIteration</code> immediately;
it does not attempt another read from the closed file and does not print a
second line.

**正确答案（中文）：** 首先打印文件中的第一行。随后
<code>close()</code> 终止生成器并关闭文件。最后一次
<code>next(lines)</code> 会立即抛出 <code>StopIteration</code>；它不会再次
尝试读取已关闭的文件，也不会打印第二行。

## Summary / 总结

- **English:** A context manager separates resource acquisition from reliable
  release and works across both normal and exceptional control flow.
  **中文：** 上下文管理器把资源获取与可靠释放组织在一起，并同时适用于正常流程
  和异常流程。
- **English:** The name after <code>as</code> receives the value returned by
  <code>__enter__()</code>; leaving a <code>with</code> block does not erase
  that name.
  **中文：** <code>as</code> 后的名字接收 <code>__enter__()</code> 的返回值；
  离开 <code>with</code> 代码块不会删除这个名字。
- **English:** Exceptions are provided to <code>__exit__()</code>. A truthy
  result suppresses them, whereas a false result lets them propagate.
  **中文：** 异常会传给 <code>__exit__()</code>。返回真值会抑制异常，返回假值
  则让异常继续传播。
- **English:** Nested contexts exit in last-in, first-out order.
  **中文：** 嵌套上下文按“后进先出”的顺序退出。
- **English:** <code>@contextmanager</code> maps code before
  <code>yield</code> to acquisition and code after it to release.
  **中文：** <code>@contextmanager</code> 将 <code>yield</code> 前的代码映射为
  资源获取，将其后的代码映射为资源释放。
- **English:** Lazy iteration must not outlive the open resource it needs.
  A generator that owns a file should be exhausted or explicitly closed.
  **中文：** 惰性迭代不能超过其所需打开资源的生命周期。拥有文件的生成器应被
  完整消费或显式关闭。

## Common Mistakes / 常见错误

- **English:** Assuming that <code>f.write()</code> prints text to the
  terminal instead of writing it into the file.
  **中文：** 误以为 <code>f.write()</code> 会向终端打印，而不是写入文件。
- **English:** Assuming that the variable after <code>as</code> must refer to
  the original context-manager object.
  **中文：** 误以为 <code>as</code> 后的变量一定指向原始上下文管理器对象。
- **English:** Forgetting that returning <code>True</code> from
  <code>__exit__()</code> suppresses the active exception.
  **中文：** 忘记从 <code>__exit__()</code> 返回 <code>True</code> 会抑制当前
  异常。
- **English:** Returning a generator expression that depends on a file which
  is closed as the function returns.
  **中文：** 返回依赖某个文件的生成器表达式，却在函数返回时同时关闭该文件。
- **English:** Assuming that <code>generator.close()</code> merely closes the
  file while leaving the generator reusable.
  **中文：** 误以为 <code>generator.close()</code> 只关闭文件，而生成器仍可
  继续使用。
- **English:** Relying on garbage collection instead of deterministic cleanup
  for important resources.
  **中文：** 对重要资源依赖垃圾回收，而不是使用确定性的清理方式。

## Next Steps / 下一步建议

1. **English:** Implement a small timing context-manager class with
   <code>__enter__()</code> and <code>__exit__()</code> for benchmark code.
   **中文：** 使用 <code>__enter__()</code> 和 <code>__exit__()</code> 实现一个
   用于 benchmark 代码的小型计时上下文管理器。
2. **English:** Practice <code>contextlib.closing</code>,
   <code>nullcontext</code>, and <code>ExitStack</code> for dynamic groups
   of resources.
   **中文：** 练习使用 <code>contextlib.closing</code>、
   <code>nullcontext</code> 和 <code>ExitStack</code> 管理动态资源组。
3. **English:** Learn modules, imports, package boundaries, and
   <code>if __name__ == "__main__"</code>.
   **中文：** 学习模块、导入、包边界和
   <code>if __name__ == "__main__"</code>。
4. **English:** Use <code>dataclasses.dataclass</code> to model validated
   benchmark records.
   **中文：** 使用 <code>dataclasses.dataclass</code> 为经过校验的 benchmark
   记录建模。
5. **English:** Write unit tests that verify normal cleanup, exceptional
   cleanup, exception suppression, and early generator closure.
   **中文：** 编写单元测试，验证正常清理、异常清理、异常抑制和生成器提前关闭。
