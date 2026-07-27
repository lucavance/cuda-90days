# Day 024: Python Pathlib, Files, and JSON / Python Pathlib、文件与 JSON

Date / 日期: 2026-07-24 to 2026-07-27 / 2026-07-24 至 2026-07-27

## Topic / 主题

**English:** Practical Python file handling for benchmark records: constructing
paths with `pathlib`, inspecting filesystem objects, reading and writing text
files safely, creating directories, finding files, parsing JSON, and handling
common errors.

**中文：** 面向 benchmark 实验记录的实用 Python 文件处理：使用 `pathlib`
构造路径、检查文件系统对象、安全读写文本文件、创建目录、查找文件、解析 JSON，
以及处理常见错误。

## Goal / 目标

**English:** Build a reliable mental model that separates path construction
from filesystem operations and supports small scripts that can safely locate,
read, write, and parse benchmark result files.

**中文：** 建立一套可靠的思维模型，分清“构造路径”和“操作文件系统”，并能够
编写小型脚本，安全地定位、读取、写入和解析 benchmark 结果文件。

## 10 Concept Questions / 10 道概念题

### 1. Path objects and relative paths / Path 对象与相对路径

**Question (English):** Consider:

```python
from pathlib import Path

p = Path("benchmarks/results/run.json")
```

Is `p` a string or a `Path` object? Has Python already read or created the
file? Is this an absolute or relative path, and what is it relative to?

**问题（中文）：** 观察代码：

```python
from pathlib import Path

p = Path("benchmarks/results/run.json")
```

`p` 是字符串还是 `Path` 对象？执行代码时，Python 是否已经读取或创建
文件？这是绝对路径还是相对路径，相对于哪里？

**Explanation (English):** Creating a `Path` builds a path representation only.
Relative paths are resolved from the Python process's current working directory
(CWD), which does not have to be the directory containing the script.

**解说（中文）：** 创建 `Path` 只会构造路径表示，不会自动访问文件系统。相对
路径以 Python 进程的当前工作目录（CWD）为基准，而不一定以脚本所在目录为
基准。

**Correct Answer (English):** `p` is a `Path` object. No file has been read
or created. The path is relative and is resolved against `Path.cwd()` when a
filesystem operation uses it.

**正确答案（中文）：** `p` 是 `Path` 对象；此时没有读取或创建文件。它
是相对路径，在真正执行文件系统操作时，相对于 `Path.cwd()` 表示的当前工作
目录解析。

### 2. Composing paths / 组合路径

**Question (English):** What path does `result` represent below? Is `/`
division here, and does this code create any directory or file?

```python
base = Path("benchmarks")
result = base / "results" / "run.json"
```

**问题（中文）：** 下面的 `result` 表示什么路径？`/` 在这里是除法吗？
这段代码会自动创建目录或文件吗？

```python
base = Path("benchmarks")
result = base / "results" / "run.json"
```

**Explanation (English):** `Path` overloads `/` as a platform-aware path
join operator. Joining path components still constructs an object only.

**解说（中文）：** `Path` 将 `/` 重载为能适配操作系统的路径拼接运算。
拼接路径仍然只是在构造对象。

**Correct Answer (English):** `result` represents
`benchmarks/results/run.json`. The operator joins path components; it is not
numeric division. No directory or file is created.

**正确答案（中文）：** `result` 表示 `benchmarks/results/run.json`。
`/` 用于拼接路径，不是数值除法；代码不会创建任何目录或文件。

### 3. Inspecting filesystem object types / 检查文件系统对象类型

**Question (English):** What do `p.exists()`, `p.is_file()`, and
`p.is_dir()` test? Can `exists()` be true while `is_file()` is
false?

**问题（中文）：** `p.exists()`、`p.is_file()` 和 `p.is_dir()`
分别判断什么？是否可能出现 `exists()` 为真而 `is_file()` 为假？

**Explanation (English):** Existence and object type are different questions.
A path may exist while referring to a directory or another non-regular-file
object.

**解说（中文）：** “是否存在”和“对象类型是什么”是两个不同问题。路径可以存在，
但它可能指向目录或其他非普通文件对象。

**Correct Answer (English):** `exists()` tests whether the path resolves to an
existing filesystem object. `is_file()` tests whether it exists and is a
regular file; `is_dir()` tests whether it exists and is a directory. If `p`
points to a directory, the results can be `True`, `False`, and `True`
respectively.

**正确答案（中文）：** `exists()` 判断路径指向的文件系统对象是否存在；
`is_file()` 判断它是否存在且为普通文件；`is_dir()` 判断它是否存在且
为目录。当 `p` 指向目录时，三者可以依次得到 `True`、`False`、
`True`。

### 4. Reading a file safely / 安全读取文件

**Question (English):** In the code below, what is the type of `data`, what
does mode `"r"` mean, why is `with` recommended, and is the file still
open after leaving the block?

```python
path = Path("results.txt")

with path.open("r", encoding="utf-8") as f:
    data = f.read()
```

**问题（中文）：** 在下面的代码中，`data` 是什么类型？`"r"` 表示什么
模式？为什么推荐使用 `with`？离开代码块后文件是否仍保持打开？

```python
path = Path("results.txt")

with path.open("r", encoding="utf-8") as f:
    data = f.read()
```

**Explanation (English):** A `with` statement manages a resource through a
context manager. It is not a separate lexical variable scope; its important
job here is deterministic cleanup even when an exception occurs.

**解说（中文）：** `with` 通过上下文管理器管理资源，它不是独立的临时变量
作用域。这里最重要的作用是保证文件被确定地清理，即使代码发生异常也会关闭
文件。

**Correct Answer (English):** `data` is a `str`, and `"r"` means
read-only text mode. The context manager closes the file on normal exit or
exception. The name `f` may remain bound after the block, but `f.closed` is
true and the file can no longer be read.

**正确答案（中文）：** `data` 是 `str`，`"r"` 表示只读文本
模式。上下文管理器会在正常退出或发生异常时关闭文件。离开代码块后，名字
`f` 可能仍然存在，但 `f.closed` 为真，不能再从中读取数据。

### 5. Overwrite and append modes / 覆盖与追加模式

**Question (English):** When opening `results.txt` with mode `"w"`, what
happens if the file exists or does not exist? How is mode `"a"` different?

```python
with Path("results.txt").open("w", encoding="utf-8") as f:
    f.write("new result\n")
```

**问题（中文）：** 使用 `"w"` 模式打开 `results.txt` 时，文件已存在或
不存在分别会怎样？`"a"` 模式与它有什么区别？

```python
with Path("results.txt").open("w", encoding="utf-8") as f:
    f.write("new result\n")
```

**Explanation (English):** The base mode determines both creation behavior and
the write position. The optional `+` means reading and writing; it is not part
of the meaning of plain append mode.

**解说（中文）：** 基本模式同时决定文件创建行为和写入位置。可选的 `+` 表示
同时读写，它不是普通追加模式含义的一部分。

**Correct Answer (English):** `"w"` creates a missing file but truncates an
existing file before writing. `"a"` also creates a missing file, but writes at
the end without removing existing content. Plain `"w"` and `"a"` are
write-only; examples of read/write modes are `"r+"`, `"w+"`, and
`"a+"`.

**正确答案（中文）：** `"w"` 会创建不存在的文件，但会先清空已存在文件再
写入。`"a"` 也会创建不存在的文件，但会在末尾追加而不删除原内容。普通
`"w"` 和 `"a"` 都是只写；`"r+"`、`"w+"`、`"a+"`
才是相应的读写模式。

### 6. Creating parent directories / 创建父目录

**Question (English):** What does `output.parent` represent, and what do
`parents=True` and `exist_ok=True` do?

```python
output = Path("benchmarks/results/run1.txt")
output.parent.mkdir(parents=True, exist_ok=True)
```

**问题（中文）：** `output.parent` 表示什么路径？`parents=True` 和
`exist_ok=True` 分别有什么作用？

```python
output = Path("benchmarks/results/run1.txt")
output.parent.mkdir(parents=True, exist_ok=True)
```

**Explanation (English):** `parent` computes the containing path, while
`mkdir()` performs the filesystem change. Recursive creation and tolerance
for an existing target are separate options.

**解说（中文）：** `parent` 计算包含该文件的目录路径，而 `mkdir()` 才
执行文件系统修改。递归创建上级目录和允许目标已存在是两个独立选项。

**Correct Answer (English):** `output.parent` is
`benchmarks/results`. `parents=True` recursively creates missing
ancestors such as `benchmarks`; `exist_ok=True` avoids an error if the
target directory already exists. It still fails if that target path is an
incompatible object such as a regular file.

**正确答案（中文）：** `output.parent` 是 `benchmarks/results`。
`parents=True` 会递归创建缺少的上级目录，例如 `benchmarks`；
`exist_ok=True` 会在目标目录已经存在时避免报错。如果该路径已存在但其实是
普通文件等不兼容对象，操作仍然会失败。

### 7. Finding files with glob patterns / 使用 glob 模式查找文件

**Question (English):** What does `files` contain below? Does `glob("*.json")`
search subdirectories, and how can all nested directories be searched?

```python
results_dir = Path("benchmarks/results")
files = list(results_dir.glob("*.json"))
```

**问题（中文）：** 下面的 `files` 包含什么？`glob("*.json")` 是否查找
子目录？怎样递归查找所有嵌套目录？

```python
results_dir = Path("benchmarks/results")
files = list(results_dir.glob("*.json"))
```

**Explanation (English):** A simple glob pattern matches immediate children.
Recursive matching must be requested explicitly, and matches are returned as
`Path` objects.

**解说（中文）：** 普通 glob 模式只匹配当前目录的直接子项。递归匹配必须显式
指定，返回的匹配项是 `Path` 对象。

**Correct Answer (English):** `files` is a list of matching `Path`
objects directly under `results_dir`. It does not recurse. Use
`results_dir.rglob("*.json")` or
`results_dir.glob("**/*.json")` for recursive matching. If only regular
files are acceptable, filter matches with `is_file()`.

**正确答案（中文）：** `files` 是 `results_dir` 直接子项中匹配模式的
`Path` 对象列表，不会递归。递归匹配可使用
`results_dir.rglob("*.json")` 或
`results_dir.glob("**/*.json")`。如果必须保证结果都是普通文件，还应使用
`is_file()` 过滤。

### 8. Parsing JSON from a file or string / 从文件或字符串解析 JSON

**Question (English):** Given this JSON file and code, what are the Python
types of `result` and `result["ms"]`? What does JSON `true` become?
How do `json.load()` and `json.loads()` differ?

```json
{
  "kernel": "vec_add",
  "ms": 1.2,
  "ok": true
}
```

```python
import json

with Path("run.json").open("r", encoding="utf-8") as f:
    result = json.load(f)
```

**问题（中文）：** 对于上面的 JSON 文件和代码，`result` 与
`result["ms"]` 分别是什么 Python 类型？JSON 的 `true` 会变成什么？
`json.load()` 与 `json.loads()` 有什么区别？

**Explanation (English):** JSON syntax maps into Python values during parsing.
The trailing `s` in `loads` indicates input already held as a string-like
value rather than an open file object.

**解说（中文）：** 解析时，JSON 语法会映射为相应的 Python 值。`loads`
末尾的 `s` 可帮助记忆：输入已经是字符串类数据，而不是打开的文件对象。

**Correct Answer (English):** `result` is a `dict`,
`result["ms"]` is a `float`, and JSON `true` becomes Python
`True`. `json.load(f)` reads and parses JSON from a file-like object;
`json.loads(text)` parses JSON already held in a string, bytes, or bytearray.

**正确答案（中文）：** `result` 是 `dict`，`result["ms"]` 是
`float`，JSON 的 `true` 会变成 Python 的 `True`。
`json.load(f)` 从文件类对象读取并解析 JSON；`json.loads(text)`
解析已经位于字符串、字节或字节数组中的 JSON。

### 9. Handling file and JSON errors / 处理文件与 JSON 错误

**Question (English):** In the code below, when is `FileNotFoundError`
raised, when is `json.JSONDecodeError` raised, and why should they be
handled separately?

```python
try:
    with Path("run.json").open("r", encoding="utf-8") as f:
        result = json.load(f)
except FileNotFoundError:
    print("file not found")
except json.JSONDecodeError:
    print("invalid JSON")
```

**问题（中文）：** 在下面的代码中，什么时候会抛出
`FileNotFoundError`，什么时候会抛出 `json.JSONDecodeError`？为什么
应该分别处理？

```python
try:
    with Path("run.json").open("r", encoding="utf-8") as f:
        result = json.load(f)
except FileNotFoundError:
    print("文件不存在")
except json.JSONDecodeError:
    print("JSON 格式错误")
```

**Explanation (English):** Opening and parsing are separate failure stages.
Specific exception handlers preserve the cause and allow different recovery
actions or messages.

**解说（中文）：** 打开文件和解析内容是两个独立的失败阶段。捕获具体异常可以
保留问题原因，并采用不同的恢复措施或提示信息。

**Correct Answer (English):** Opening the path raises `FileNotFoundError` if
the target file or required path does not exist. After a successful open,
`json.load()` raises `JSONDecodeError` when the content is not valid JSON,
such as an empty or malformed document. Handling them separately distinguishes
a missing input from corrupt input instead of hiding both behind one generic
error.

**正确答案（中文）：** 如果目标文件或所需路径不存在，打开路径时会抛出
`FileNotFoundError`。成功打开后，如果内容为空或格式不合法，
`json.load()` 会抛出 `JSONDecodeError`。分别处理可以区分“输入缺失”
和“输入损坏”，而不是用一个笼统错误隐藏两种原因。

### 10. Saving a benchmark result / 保存 benchmark 结果

**Question (English):** Explain what each filesystem and JSON operation below
does. What happens when it is run again, and how does `json.dumps()` differ
from `json.dump()`?

```python
import json
from pathlib import Path

output = Path("benchmarks/results/run.json")
output.parent.mkdir(parents=True, exist_ok=True)

result = {
    "kernel": "vec_add",
    "ms": 1.2,
    "ok": True,
}

with output.open("w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
```

**问题（中文）：** 说明下面每个文件系统和 JSON 操作的作用。再次运行时会发生
什么？`json.dumps()` 与 `json.dump()` 有什么区别？

```python
import json
from pathlib import Path

output = Path("benchmarks/results/run.json")
output.parent.mkdir(parents=True, exist_ok=True)

result = {
    "kernel": "vec_add",
    "ms": 1.2,
    "ok": True,
}

with output.open("w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
```

**Explanation (English):** Directory creation, file creation, serialization,
and overwrite behavior come from different calls. Keeping these responsibilities
separate prevents assumptions such as believing `mkdir()` creates the JSON file
or that mode `"w"` appends.

**解说（中文）：** 目录创建、文件创建、序列化和覆盖行为分别来自不同调用。分清
这些职责，可以避免误以为 `mkdir()` 会创建 JSON 文件，或者误以为
`"w"` 会追加内容。

**Correct Answer (English):** `output.parent` is
`benchmarks/results`, and `mkdir()` creates that directory chain but not
`run.json`. `open("w")` creates or truncates the file. `json.dump()`
serializes the dictionary as JSON and writes it to `f`. Running the code
again replaces the old JSON rather than appending another copy.
`json.dumps(result)` returns the serialized JSON string instead of writing to
a file object.

**正确答案（中文）：** `output.parent` 是 `benchmarks/results`，
`mkdir()` 会创建这条目录链，但不会创建 `run.json`。
`open("w")` 会创建或清空文件；`json.dump()` 将字典序列化为 JSON
并写入 `f`。再次运行会替换旧 JSON，而不是追加一份。
`json.dumps(result)` 返回序列化后的 JSON 字符串，不会直接写入文件对象。

## Summary / 总结

**English:** The session connected path construction to real filesystem
operations and then to structured benchmark data. The key workflow is:

```text
construct Path
  -> inspect or create directories
  -> open files with an explicit mode and encoding
  -> manage the file with a context manager
  -> parse or serialize JSON
  -> handle specific failure modes
```

The learner can now explain path composition, CWD-relative resolution, file
type checks, safe text I/O, overwrite versus append behavior, recursive
directory creation, glob matching, JSON type conversion, and targeted
exceptions.

**中文：** 本次学习把路径构造、真实文件系统操作和结构化 benchmark 数据处理连接
起来。核心流程是：

```text
构造 Path
  -> 检查或创建目录
  -> 使用明确的模式与编码打开文件
  -> 用上下文管理器管理文件
  -> 解析或序列化 JSON
  -> 针对性处理失败情况
```

现在已经能够解释路径拼接、基于 CWD 的相对路径解析、文件类型检查、安全文本
读写、覆盖与追加的区别、递归创建目录、glob 匹配、JSON 类型转换和具体异常处理。

## Common Mistakes / 常见错误

**English:**

- Treating `with` as a temporary variable scope instead of a resource manager.
- Confusing append mode `"a"` with the read/write `+` modifier.
- Reversing the roles of `parents=True` and `exist_ok=True`.
- Assuming `mkdir()` creates the final file as well as its directories.
- Expecting mode `"w"` to append instead of truncating existing content.
- Mixing up file-object APIs (`load` and `dump`) with string APIs
  (`loads` and `dumps`).

**中文：**

- 把 `with` 当作临时变量作用域，而不是资源管理器。
- 混淆追加模式 `"a"` 与表示读写的 `+` 修饰符。
- 颠倒 `parents=True` 和 `exist_ok=True` 的职责。
- 误以为 `mkdir()` 在创建目录的同时也会创建最终文件。
- 误以为 `"w"` 会追加内容，而不是清空已有内容。
- 混淆操作文件对象的 `load`、`dump` 与操作字符串的
  `loads`、`dumps`。

## Next Steps / 下一步

**English:**

1. Learn line-by-line processing for files too large to read all at once.
2. Read and write CSV benchmark tables with the `csv` module.
3. Wrap path and JSON operations in small, testable functions.
4. Validate required JSON fields and value types before aggregation.
5. Learn atomic writes when a partially written result file would be unsafe.

**中文：**

1. 学习逐行处理无法一次性全部读入的大文件。
2. 使用 `csv` 模块读写 benchmark 表格。
3. 把路径和 JSON 操作封装为小型、可测试的函数。
4. 在聚合前验证 JSON 必需字段和值类型。
5. 在结果文件不能接受部分写入时，学习原子写入。
