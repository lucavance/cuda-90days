# Day 031: Python Modules, Imports, Packages, and Entry Points / Python 模块、导入、包与程序入口

Date / 日期: 2026-08-05

## Topic / 主题

**English:** Python modules, import execution, module caching, name binding,
regular packages, <code>__init__.py</code>, relative imports, module search
paths, circular imports, <code>__name__</code>, entry-point guards, and
executable packages using <code>python -m</code>.

**中文：** Python 模块、导入执行、模块缓存、名字绑定、常规包、
<code>__init__.py</code>、相对导入、模块搜索路径、循环导入、
<code>__name__</code>、程序入口保护，以及通过 <code>python -m</code> 执行包。

## Goal / 目标

**English:** Build a reliable mental model for how Python locates, initializes,
caches, and names modules; organize benchmark tooling into package boundaries;
and separate reusable library code from code that should run only at a program
entry point.

**中文：** 建立可靠的导入思维模型，理解 Python 如何查找、初始化、缓存和命名
模块；能够把 benchmark 工具组织到清晰的包边界中，并把可复用库代码与只应在
程序入口执行的代码分离。

## Core Mental Model / 核心思维模型

**English:** Importing is executable behavior, not textual file inclusion.
Python first checks its module cache, then asks the import system to locate a
module. On the first load, it creates a module object, registers it, executes
the module's top-level code, and binds a name in the importing scope. Packages
provide qualified module names and context for relative imports. The
<code>-m</code> option executes a module through that import system, preserving
its package identity.

**中文：** 导入是一种可执行行为，不是把文件文本粘贴进来。Python 会先检查模块
缓存，再让导入系统查找模块。首次加载时，它创建并注册模块对象，执行模块顶层
代码，然后在导入方作用域中绑定名字。包提供限定模块名和相对导入所需的上下文；
<code>-m</code> 选项通过导入系统执行模块，从而保留其包身份。

## 10 Concept Questions / 10 道概念题

### 1. What a first import does / 首次导入会做什么

**Question (English):** What is the complete output? Besides making the name
<code>helper</code> available, what work does <code>import helper</code>
perform?

**问题（中文）：** 完整输出是什么？除了获得名字 <code>helper</code>，
<code>import helper</code> 还会完成哪些工作？

<code>helper.py</code>:

~~~python
print("loading helper")
value = 42
~~~

<code>main.py</code>:

~~~python
print("before")
import helper
print("after", helper.value)
~~~

**Explanation (English):** On the first import, Python locates the module,
creates a module object and namespace, and executes its top-level statements.
The importing module receives the name <code>helper</code>, which refers to
that module object. Attributes remain in the module namespace and are accessed
with qualified names such as <code>helper.value</code>.

**解说（中文）：** 首次导入时，Python 会查找模块，创建模块对象及其命名空间，
并执行模块的顶层语句。导入方得到名字 <code>helper</code>，它指向该模块对象。
模块属性保留在模块命名空间中，需要通过 <code>helper.value</code> 这样的限定
名字访问。

**Correct Answer (English):** The output is:

~~~text
before
loading helper
after 42
~~~

The import executes <code>helper.py</code> and binds the resulting module
object to <code>helper</code>. It does not directly copy every module
attribute into <code>main.py</code>.

**正确答案（中文）：** 输出为：

~~~text
before
loading helper
after 42
~~~

导入会执行 <code>helper.py</code>，并把产生的模块对象绑定到
<code>helper</code>。它不会把模块中的每个属性直接复制到
<code>main.py</code>。

### 2. The module cache / 模块缓存

**Question (English):** What is the complete output? Does the second
<code>import helper</code> execute the module's top-level code again, and why?

**问题（中文）：** 完整输出是什么？第二次 <code>import helper</code> 是否会
再次执行模块的顶层代码？为什么？

<code>helper.py</code>:

~~~python
print("loading helper")
value = 42
~~~

<code>main.py</code>:

~~~python
import helper
import helper
print(helper.value)
~~~

**Explanation (English):** Successfully loaded modules are cached by name in
<code>sys.modules</code>. A later import of that same name in the same process
normally reuses the existing module object instead of executing the file
again.

**解说（中文）：** 成功加载的模块会按名字缓存在 <code>sys.modules</code> 中。
同一进程之后再次导入相同名字时，通常会复用已有模块对象，而不会重新执行文件。

**Correct Answer (English):** The output is:

~~~text
loading helper
42
~~~

The loading message appears once. Starting a new Python process or explicitly
using <code>importlib.reload()</code> can cause module code to execute again.

**正确答案（中文）：** 输出为：

~~~text
loading helper
42
~~~

加载消息只出现一次。启动新的 Python 进程，或显式使用
<code>importlib.reload()</code>，可以让模块代码再次执行。

### 3. Imported names and rebinding / 导入名字与重新绑定

**Question (English):** What is the complete output? Does assigning
<code>value = 100</code> in <code>main.py</code> also change
<code>helper.value</code>?

**问题（中文）：** 完整输出是什么？在 <code>main.py</code> 中执行
<code>value = 100</code>，是否也会修改 <code>helper.value</code>？

<code>helper.py</code>:

~~~python
print("loading helper")
value = 42
~~~

<code>main.py</code>:

~~~python
from helper import value

value = 100
print(value)

import helper
print(helper.value)
~~~

**Explanation (English):** <code>from helper import value</code> binds the
name <code>value</code> in the importing scope to the object currently stored
in <code>helper.value</code>. A later assignment rebinds only the local name;
it does not perform <code>helper.value = 100</code>.

**解说（中文）：** <code>from helper import value</code> 会在导入方作用域中绑定
名字 <code>value</code>，使其指向当时存储在 <code>helper.value</code> 中的
对象。之后的赋值只重新绑定本地名字，并不等同于执行
<code>helper.value = 100</code>。

**Correct Answer (English):** The output is:

~~~text
loading helper
100
42
~~~

The two names were initially bound to the same integer object, but rebinding
the local name does not mutate the module attribute. If the imported value
were mutable, an in-place mutation could still be observed through both
bindings.

**正确答案（中文）：** 输出为：

~~~text
loading helper
100
42
~~~

两个名字最初绑定到同一个整数对象，但重新绑定本地名字不会修改模块属性。如果
导入值是可变对象，那么对该对象进行原地修改时，两个绑定仍可能观察到同一次
修改。

### 4. __name__ when executed and imported / 直接执行与导入时的 __name__

**Question (English):** What does <code>tool.py</code> print when it is
executed directly, and what does it print when another module imports it? Why
does <code>__name__</code> differ?

**问题（中文）：** 直接执行 <code>tool.py</code> 时会打印什么？被另一个模块
导入时又会打印什么？为什么两种情况下 <code>__name__</code> 不同？

<code>tool.py</code>:

~~~python
print(__name__)

if __name__ == "__main__":
    print("run directly")
~~~

Direct execution / 直接执行:

~~~bash
python tool.py
~~~

Imported by <code>main.py</code> / 由 <code>main.py</code> 导入:

~~~python
import tool
~~~

**Explanation (English):** Python assigns the special name
<code>"__main__"</code> to the top-level entry module. A normally imported
module receives its import name, here <code>"tool"</code>. The same file can
therefore detect whether it is the program entry point or reusable imported
code.

**解说（中文）：** Python 会把特殊名字 <code>"__main__"</code> 赋给最顶层的
入口模块；普通导入的模块则获得其导入名字，这里是 <code>"tool"</code>。因此
同一个文件可以判断自己是程序入口，还是被复用的导入代码。

**Correct Answer (English):** Direct execution prints:

~~~text
__main__
run directly
~~~

Importing <code>tool</code> prints:

~~~text
tool
~~~

**正确答案（中文）：** 直接执行时输出：

~~~text
__main__
run directly
~~~

导入 <code>tool</code> 时输出：

~~~text
tool
~~~

### 5. Preventing import side effects / 避免导入副作用

**Question (English):** How should this module be changed so that importing it
only provides functions, while direct execution still runs the benchmark?

**问题（中文）：** 应该如何修改这个模块，才能让导入操作只提供函数，而直接执行
时仍然运行 benchmark？

Original <code>benchmark.py</code> / 原始 <code>benchmark.py</code>:

~~~python
def run_benchmark():
    print("benchmark running")

run_benchmark()
~~~

**Explanation (English):** Reusable definitions should be created during
import, but application startup belongs behind an entry-point guard. Putting
startup logic in a <code>main()</code> function also makes the control flow
easier to call and test.

**解说（中文）：** 导入时可以创建可复用定义，但应用启动逻辑应放在入口保护条件
之后。把启动逻辑放进 <code>main()</code> 函数，也便于调用、测试和理解控制流。

**Correct Answer (English):** One suitable implementation is:

~~~python
def run_benchmark():
    print("benchmark running")


def main():
    run_benchmark()


if __name__ == "__main__":
    main()
~~~

Importing the module defines its functions without starting the benchmark.
Executing <code>python benchmark.py</code> calls <code>main()</code>.

**正确答案（中文）：** 一种合适的实现是：

~~~python
def run_benchmark():
    print("benchmark running")


def main():
    run_benchmark()


if __name__ == "__main__":
    main()
~~~

导入模块时只定义函数，不启动 benchmark；执行
<code>python benchmark.py</code> 时则会调用 <code>main()</code>。

### 6. Packages, submodules, and __init__.py / 包、子模块与 __init__.py

**Question (English):** In this project, what are <code>tools</code>,
<code>parser</code>, and <code>parse</code>? What is printed, and what role
does <code>__init__.py</code> play?

**问题（中文）：** 在这个项目中，<code>tools</code>、<code>parser</code> 和
<code>parse</code> 分别是什么？代码输出什么？<code>__init__.py</code> 起什么
作用？

~~~text
project/
├── main.py
└── tools/
    ├── __init__.py
    └── parser.py
~~~

<code>tools/parser.py</code>:

~~~python
def parse():
    return "ok"
~~~

<code>main.py</code>:

~~~python
from tools.parser import parse
print(parse())
~~~

**Explanation (English):** A package groups modules under a qualified
namespace. Here, <code>tools</code> is a regular package,
<code>tools.parser</code> is a submodule, and <code>parse</code> is a
function. A package's <code>__init__.py</code> executes during package
initialization and may define or re-export its public interface.

**解说（中文）：** 包会把模块组织到一个限定命名空间下。这里
<code>tools</code> 是常规包，<code>tools.parser</code> 是子模块，
<code>parse</code> 是函数。包初始化时会执行 <code>__init__.py</code>，该文件
也可以定义或重新导出包的公共接口。

**Correct Answer (English):** The output is:

~~~text
ok
~~~

The presence of <code>__init__.py</code> makes <code>tools</code> a regular
package. Modern Python also supports namespace packages without that file,
but explicit regular packages remain common and predictable for ordinary
projects.

**正确答案（中文）：** 输出为：

~~~text
ok
~~~

<code>__init__.py</code> 使 <code>tools</code> 成为常规包。现代 Python 也
支持没有该文件的命名空间包，但普通项目中显式使用常规包依然常见且行为明确。

### 7. Relative imports and package execution / 相对导入与包方式执行

**Question (English):** What does the leading dot in
<code>from .parser import parse</code> mean? Why can direct file execution
fail, and which command should be used from the project root?

**问题（中文）：** <code>from .parser import parse</code> 中开头的点表示什么？
为什么直接执行文件可能失败？从项目根目录应该使用什么命令？

<code>tools/formatter.py</code>:

~~~python
from .parser import parse

print(parse())
~~~

Problematic direct execution / 可能失败的直接执行:

~~~bash
python tools/formatter.py
~~~

**Explanation (English):** The leading dot means the current package. Direct
file execution names the file <code>__main__</code> without necessarily
giving it a known parent package. A relative import then has no package anchor
from which to resolve <code>.parser</code>.

**解说（中文）：** 开头的点表示当前包。直接执行文件时，该文件会被命名为
<code>__main__</code>，但不一定拥有已知的父包；相对导入因此没有可用于解析
<code>.parser</code> 的包锚点。

**Correct Answer (English):** From the project root, run:

~~~bash
python -m tools.formatter
~~~

This preserves the module's identity as <code>tools.formatter</code>, so the
relative import resolves to <code>tools.parser</code> and the program prints
<code>ok</code>. Direct execution commonly raises:

~~~text
ImportError: attempted relative import with no known parent package
~~~

**正确答案（中文）：** 应从项目根目录执行：

~~~bash
python -m tools.formatter
~~~

这样可以保留模块的 <code>tools.formatter</code> 身份，所以相对导入会解析为
<code>tools.parser</code>，程序输出 <code>ok</code>。直接执行时通常会抛出：

~~~text
ImportError: attempted relative import with no known parent package
~~~

### 8. Module search paths and local shadowing / 模块搜索路径与本地遮蔽

**Question (English):** Why can a local <code>json.py</code> shadow the
standard-library <code>json</code> module? Which object controls ordinary
filesystem search locations, and what can <code>json.__file__</code> reveal?

**问题（中文）：** 为什么本地 <code>json.py</code> 可能遮蔽标准库的
<code>json</code> 模块？哪个对象控制普通文件模块的搜索位置？
<code>json.__file__</code> 可以揭示什么？

~~~text
project/
├── main.py
└── json.py
~~~

<code>json.py</code>:

~~~python
print("local json")
~~~

<code>main.py</code>:

~~~python
import json
print(json.__file__)
~~~

**Explanation (English):** Python normally checks <code>sys.modules</code>
for an existing module first. If the module is not cached, import finders
locate it; ordinary filesystem lookup follows entries in
<code>sys.path</code>. The script directory is commonly near the front, so a
same-named local file can be found before the standard-library package.

**解说（中文）：** Python 通常先检查 <code>sys.modules</code> 中是否已有模块。
如果缓存未命中，导入查找器会定位模块；普通文件系统查找会按照
<code>sys.path</code> 中的条目进行。脚本目录通常位于较前位置，因此同名本地
文件可能先于标准库包被找到。

**Correct Answer (English):** The local module prints
<code>local json</code>, and <code>json.__file__</code> shows the path of the
module that was actually loaded. <code>sys.path</code> describes ordinary
module search locations and order, while <code>sys.modules</code> is the
cache of module objects already loaded under particular names.

**正确答案（中文）：** 本地模块会打印 <code>local json</code>，
<code>json.__file__</code> 则显示实际加载模块的路径。
<code>sys.path</code> 描述普通模块的搜索位置和顺序，而
<code>sys.modules</code> 是已经按特定名字加载的模块对象缓存。

### 9. Circular imports and partial initialization / 循环导入与部分初始化

**Question (English):** Why does this import print both starting messages and
then fail to obtain <code>value_a</code>? What circular dependency is active?

**问题（中文）：** 为什么这个导入会先打印两条启动消息，随后却无法获得
<code>value_a</code>？这里存在怎样的循环依赖？

<code>a.py</code>:

~~~python
print("start a")
from b import value_b

value_a = "A"
~~~

<code>b.py</code>:

~~~python
print("start b")
from a import value_a

value_b = "B"
~~~

<code>main.py</code>:

~~~python
import a
~~~

**Explanation (English):** Python registers a module object before finishing
its execution so recursive imports can find it. Module <code>a</code> pauses
while importing <code>b</code>. Module <code>b</code> then finds the cached
but partially initialized <code>a</code>; however, execution has not yet
reached <code>value_a = "A"</code>.

**解说（中文）：** Python 会在模块执行完成之前先注册模块对象，以便递归导入能够
找到它。模块 <code>a</code> 在导入 <code>b</code> 时暂停；模块
<code>b</code> 随后找到已缓存但只完成部分初始化的 <code>a</code>，可是执行
流程尚未到达 <code>value_a = "A"</code>。

**Correct Answer (English):** The program prints:

~~~text
start a
start b
~~~

It then raises an import error referring to <code>value_a</code> in a
partially initialized module. The dependency cycle is
<code>a -> b -> a</code>. Common fixes include moving shared definitions into
a third module, changing module responsibilities, or carefully deferring an
import until a function is called.

**正确答案（中文）：** 程序先输出：

~~~text
start a
start b
~~~

随后抛出导入错误，指出无法从部分初始化的模块中获得
<code>value_a</code>。依赖环为 <code>a -> b -> a</code>。常见修复方法包括：
把共享定义移到第三个模块、重新划分模块职责，或谨慎地把某次导入延迟到函数调用
时。

### 10. An executable package with __main__.py / 使用 __main__.py 创建可执行包

**Question (English):** What does <code>python -m benchmark_tool</code> print?
Which file acts as the package entry point, and why does the relative import
work?

**问题（中文）：** <code>python -m benchmark_tool</code> 会打印什么？哪个文件
充当包入口？为什么相对导入能够工作？

~~~text
benchmark_tool/
├── __init__.py
├── __main__.py
└── parser.py
~~~

<code>parser.py</code>:

~~~python
def parse(text):
    return int(text)
~~~

<code>__main__.py</code>:

~~~python
from .parser import parse


def main():
    print(parse("42"))


if __name__ == "__main__":
    main()
~~~

Command run from the parent directory / 从父目录运行:

~~~bash
python -m benchmark_tool
~~~

**Explanation (English):** Running a package with <code>-m</code> asks the
import system to initialize the package and execute its
<code>__main__.py</code> as the top-level module. That module has
<code>__name__ == "__main__"</code> and retains
<code>__package__ == "benchmark_tool"</code>, which provides the anchor for
the relative import.

**解说（中文）：** 使用 <code>-m</code> 运行包时，导入系统会初始化该包，并把
它的 <code>__main__.py</code> 作为顶层模块执行。该模块具有
<code>__name__ == "__main__"</code>，同时保留
<code>__package__ == "benchmark_tool"</code>，从而为相对导入提供包锚点。

**Correct Answer (English):** The output is:

~~~text
42
~~~

The package entry file is <code>benchmark_tool/__main__.py</code>. Its
<code>.parser</code> import resolves to <code>benchmark_tool.parser</code>
because package execution preserves the package context. The parent directory
must be discoverable so Python can locate <code>benchmark_tool</code>.

**正确答案（中文）：** 输出为：

~~~text
42
~~~

包入口文件是 <code>benchmark_tool/__main__.py</code>。由于按包执行时保留了
包上下文，<code>.parser</code> 会解析为
<code>benchmark_tool.parser</code>。父目录需要处于可发现位置，以便 Python
找到 <code>benchmark_tool</code>。

## Summary / 总结

- **English:** A module is an executed namespace represented by a module
  object; importing is not textual inclusion.
  **中文：** 模块是由模块对象表示的、经过执行的命名空间；导入不是文本包含。
- **English:** The first import initializes a module, while later imports in
  the same process normally reuse the object stored in
  <code>sys.modules</code>.
  **中文：** 首次导入会初始化模块；同一进程后续导入通常复用
  <code>sys.modules</code> 中的对象。
- **English:** Import forms create name bindings. Rebinding a locally imported
  name does not assign to the source module's attribute.
  **中文：** 各种导入形式会建立名字绑定；重新绑定本地导入名字不会给来源模块的
  属性赋值。
- **English:** <code>__name__ == "__main__"</code> identifies the top-level
  entry module and protects startup code from import side effects.
  **中文：** <code>__name__ == "__main__"</code> 标识顶层入口模块，并保护启动
  代码不在导入时产生副作用。
- **English:** Packages create qualified names and relative-import context;
  <code>python -m</code> preserves that context while executing a module.
  **中文：** 包会创建限定名字和相对导入上下文；<code>python -m</code> 在执行
  模块时保留该上下文。
- **English:** <code>sys.path</code> participates in locating ordinary
  modules, whereas <code>sys.modules</code> stores already loaded module
  objects.
  **中文：** <code>sys.path</code> 参与查找普通模块，而
  <code>sys.modules</code> 保存已经加载的模块对象。
- **English:** Circular imports can expose partially initialized modules whose
  later definitions do not yet exist.
  **中文：** 循环导入可能暴露尚未完整初始化的模块，其中靠后的定义还不存在。

## Common Mistakes / 常见错误

- **English:** Saying that <code>import module</code> directly copies all
  exposed variables and functions into the importing namespace.
  **中文：** 误以为 <code>import module</code> 会把所有暴露变量和函数直接复制
  到导入方命名空间。
- **English:** Reversing the values of <code>__name__</code> for direct
  execution and normal import.
  **中文：** 混淆直接执行与普通导入时的 <code>__name__</code> 值。
- **English:** Leaving application startup calls at module top level and
  unintentionally running them during import.
  **中文：** 把应用启动调用留在模块顶层，导致导入时意外执行。
- **English:** Treating a package as an ordinary module without recognizing
  the role of <code>__init__.py</code> and qualified names.
  **中文：** 把包当作普通模块，而没有识别 <code>__init__.py</code> 和限定名字
  的作用。
- **English:** Directly executing a module that uses relative imports, thereby
  losing its parent-package context.
  **中文：** 直接执行使用相对导入的模块，从而丢失父包上下文。
- **English:** Confusing <code>sys.modules</code>, the module cache, with
  <code>sys.path</code>, the ordinary filesystem search path.
  **中文：** 混淆模块缓存 <code>sys.modules</code> 与普通文件系统搜索路径
  <code>sys.path</code>。
- **English:** Assuming that a cached module is necessarily fully initialized
  during a circular import.
  **中文：** 误以为循环导入期间已缓存的模块一定完成了全部初始化。
- **English:** Attributing successful relative imports only to local search
  priority instead of the module's <code>__package__</code> context.
  **中文：** 把相对导入成功仅归因于本地搜索优先级，而忽略模块的
  <code>__package__</code> 上下文。

## Next Steps / 下一步建议

1. **English:** Build a small <code>benchmark_tool</code> package with
   separate parsing, validation, reporting, and entry-point modules.
   **中文：** 构建一个小型 <code>benchmark_tool</code> 包，分别设置解析、
   校验、报告和程序入口模块。
2. **English:** Learn classes, object state, and
   <code>dataclasses.dataclass</code> for representing benchmark records.
   **中文：** 学习类、对象状态和 <code>dataclasses.dataclass</code>，用于表示
   benchmark 记录。
3. **English:** Refine type annotations with union, optional, and container
   types across module boundaries.
   **中文：** 使用联合类型、可选类型和容器类型，完善跨模块的类型注解。
4. **English:** Use <code>pytest</code> to test imports, parsers, validation
   failures, and command-line entry behavior.
   **中文：** 使用 <code>pytest</code> 测试导入、解析器、校验失败和命令行入口
   行为。
5. **English:** Add <code>argparse</code> and <code>logging</code> to turn
   the package into a reusable experiment tool.
   **中文：** 添加 <code>argparse</code> 和 <code>logging</code>，把该包发展为
   可复用的实验工具。
