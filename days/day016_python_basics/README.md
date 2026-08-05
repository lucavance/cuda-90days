# Day 016: Python Basics / Python 基础

Date / 日期: 2026-07-08

## Topic / 主题

**English:** Python data types, conversion, conditionals, loops, `range`,
functions, `return`, `None`, lists, and dictionaries.

**中文：** Python 数据类型、类型转换、条件分支、循环、`range`、函数、
`return`、`None`、列表与字典。

## Goal / 目标

**English:** Build a beginner-friendly foundation for reading and writing
Python scripts used later in AI, CUDA, benchmarking, automation, and
experiment management.

**中文：** 建立适合初学者的 Python 基础，为后续 AI、CUDA、benchmark、自动化
与实验管理脚本做准备。

## 10 Concept Questions / 10 个概念问题

### 1. Basic data types / 基础数据类型

**Question (English):** What are the types of these variables?

**问题（中文）：** 下面变量分别是什么类型？

~~~python
name = "CUDA"
days = 90
price = 200.0
enabled = True
items = ["Python", "CUDA", "AI"]
~~~

**Explanation (English):** Python values have runtime types, including
strings, integers, floats, booleans, and lists.

**解说（中文）：** Python 值在运行时具有类型，常见基础类型包括字符串、整数、
浮点数、布尔值与列表。

**Correct Answer (English):** `name` is `str`, `days` is `int`, `price`
is `float`, `enabled` is `bool`, and `items` is a `list` containing strings.
Python normally calls it a list, not a string array.

**正确答案（中文）：** `name` 是 `str`，`days` 是 `int`，`price` 是
`float`，`enabled` 是 `bool`，`items` 是包含字符串的 `list`。Python 中
通常称它为列表，而不是字符串数组。

### 2. Numbers and strings / 数字与字符串

**Question (English):** What does this code print?

**问题（中文）：** 下面代码输出什么？

~~~python
x = 10
y = "10"

print(x + 5)
print(y + "5")
~~~

**Explanation (English):** `+` performs addition for numbers and
concatenation for strings.

**解说（中文）：** `+` 对数字表示加法，对字符串表示拼接。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
15
105
~~~

**English:** `x + 5` adds integers; `y + "5"` joins strings.

**中文：** `x + 5` 是整数加法；`y + "5"` 是字符串拼接。

### 3. String conversion / 字符串转换

**Question (English):** Does this code fail, and why?

**问题（中文）：** 下面代码会报错吗？为什么？

~~~python
age = 18
message = "年龄是：" + age
print(message)
~~~

**Explanation (English):** Python does not implicitly convert an integer to a
string for `+` concatenation.

**解说（中文）：** Python 使用 `+` 拼接字符串时，不会自动把整数转换为字符串。

**Correct Answer (English):** It raises `TypeError` because one operand is
`str` and the other is `int`. Convert explicitly or use an f-string:

**正确答案（中文）：** 会抛出 `TypeError`，因为一边是 `str`，另一边是
`int`。应显式转换或使用 f-string：

~~~python
message = "年龄是：" + str(age)
message = f"年龄是：{age}"
~~~

### 4. if and else / if 与 else

**Question (English):** What does this code print?

**问题（中文）：** 下面代码输出什么？

~~~python
age = 18

if age >= 18:
    print("adult")
else:
    print("child")
~~~

**Explanation (English):** Python evaluates a Boolean condition and uses
indentation to define each branch.

**解说（中文）：** Python 根据布尔条件选择分支，并用缩进定义代码块。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
adult
~~~

**English:** `age >= 18` is `True`, so the `if` branch runs.

**中文：** `age >= 18` 为 `True`，因此执行 `if` 分支。

### 5. if, elif, and branch order / if、elif 与分支顺序

**Question (English):** What is printed, and why is it not `C`?

**问题（中文）：** 输出是什么？为什么不是 `C`？

~~~python
score = 85

if score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 60:
    print("C")
else:
    print("D")
~~~

**Explanation (English):** Python tests branches from top to bottom and stops
at the first match.

**解说（中文）：** `if/elif/else` 从上到下检查，并在第一个匹配分支停止。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
B
~~~

**English:** The first condition is false and the second is true. Remaining
branches are skipped even though `85 >= 60` is also true.

**中文：** 第一个条件为假，第二个为真；执行 `B` 后剩余分支跳过，即使
`85 >= 60` 也为真。

### 6. for over a list / 遍历列表

**Question (English):** What is printed, and what does
`for item in items` mean?

**问题（中文）：** 输出什么？`for item in items` 表示什么？

~~~python
items = ["Python", "CUDA", "AI"]

for item in items:
    print(item)
~~~

**Explanation (English):** A `for` loop obtains one value at a time from an
iterable. `print()` adds a newline by default.

**解说（中文）：** `for` 循环每次从 iterable 取得一个值；`print()` 默认换行。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
Python
CUDA
AI
~~~

**English:** Each element is assigned to `item` in turn and the body runs.
The same loop-variable name is rebound each iteration; Python does not create
a new block-scoped variable.

**中文：** 每个元素依次绑定到 `item` 并执行循环体。同一个变量名会在每次迭代
重新绑定，Python 不会创建新的 block-scoped 变量。

### 7. range / range

**Question (English):** What does `range(3)` produce and what is printed?

**问题（中文）：** `range(3)` 表示哪些数？下面代码输出什么？

~~~python
for i in range(3):
    print(i)
~~~

**Explanation (English):** `range(stop)` starts at zero and excludes
`stop`.

**解说（中文）：** `range(stop)` 从 0 开始，不包含 `stop`。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
0
1
2
~~~

**English:** `range(3)` is a range object representing 0, 1, 2, not directly
a list. `list(range(3))` creates `[0, 1, 2]`; use `range(1, 4)` for 1, 2, 3.

**中文：** `range(3)` 是表示 0、1、2 的 range 对象，不直接是 list。
`list(range(3))` 得到 `[0, 1, 2]`；1、2、3 应使用 `range(1, 4)`。

### 8. Functions and return / 函数与 return

**Question (English):** What is printed, and what does `return` do?

**问题（中文）：** 输出什么？`return` 做什么？

~~~python
def add(a, b):
    return a + b

result = add(3, 5)
print(result)
~~~

**Explanation (English):** A function receives arguments, computes, and can
send a value back to its caller.

**解说（中文）：** 函数接收参数、执行计算，并可把值返回给调用方。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
8
~~~

**English:** `return a + b` returns the computed value and ends the current
function invocation.

**中文：** `return a + b` 把结果交回调用处，并结束当前函数执行。

### 9. print versus return / print 与 return

**Question (English):** What is printed, and why is the second line
`None`?

**问题（中文）：** 输出什么？为什么第二行是 `None`？

~~~python
def greet(name):
    print("Hello", name)

result = greet("Luca")
print(result)
~~~

**Explanation (English):** Printing within a function is not returning a value
from it.

**解说（中文）：** 函数内部打印不等于从函数返回值。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
Hello Luca
None
~~~

**English:** `print("Hello", name)` separates its arguments with a space.
Because `greet()` has no explicit `return`, it returns `None`.

**中文：** `print("Hello", name)` 用空格分隔参数。`greet()` 没有显式
`return`，因此默认返回 `None`。

### 10. Dictionaries and nested indexing / 字典与嵌套索引

**Question (English):** What is printed, and what type is `person`?

**问题（中文）：** 输出什么？`person` 是什么类型？

~~~python
person = {
    "name": "Luca",
    "age": 18,
    "skills": ["Python", "CUDA"]
}

print(person["name"])
print(person["skills"][1])
~~~

**Explanation (English):** A dictionary stores key-value pairs, and values can
be arbitrary Python objects including lists.

**解说（中文）：** dictionary 保存键值对，value 可以是 list 等任意 Python
对象。

**Correct Answer (English):**

**正确答案（中文）：**

~~~text
Luca
CUDA
~~~

**English:** `person` is a `dict`. The first lookup returns the name; the
second gets the skills list and selects index 1, with indexing starting at
zero.

**中文：** `person` 是 `dict`。第一次查找返回 name；第二次先取得 skills
列表，再选择索引 1。Python 索引从 0 开始。

## Summary / 总结

- **English:** Basic types include `str`, `int`, `float`, `bool`, `list`,
  and `dict`.
  **中文：** 基础类型包括 `str`、`int`、`float`、`bool`、`list` 与 `dict`。
- **English:** Numeric addition differs from string concatenation; conversion
  is explicit.
  **中文：** 数字加法不同于字符串拼接，类型转换需要显式完成。
- **English:** `if/elif/else` selects the first matching branch.
  **中文：** `if/elif/else` 执行第一个匹配分支。
- **English:** `for` consumes iterables and `range(stop)` starts at zero.
  **中文：** `for` 消费 iterable；`range(stop)` 从 0 开始。
- **English:** Functions distinguish returned values from printed output and
  default to `None`.
  **中文：** 函数需要区分返回值与打印输出，未显式返回时得到 `None`。
- **English:** Dictionaries support key lookup and nested objects.
  **中文：** dictionary 支持 key 查询与嵌套对象。

## Common Mistakes / 常见错误

- **English:** Calling a list a string array.
  **中文：** 把 list 称作字符串数组。
- **English:** Treating `range(3)` as `[1, 2, 3]` or as a list object.
  **中文：** 把 `range(3)` 当作 `[1, 2, 3]` 或直接当作 list。
- **English:** Expecting implicit string/integer concatenation.
  **中文：** 期待字符串与整数自动拼接。
- **English:** Confusing `print()` with `return`.
  **中文：** 混淆 `print()` 与 `return`。
- **English:** Expecting a comma in `print("Hello", name)` output instead of
  a space.
  **中文：** 误以为 `print("Hello", name)` 会输出逗号，而不是默认空格。
- **English:** Assuming loop variables have block scope.
  **中文：** 误以为循环变量具有 block scope。

## Next Step / 下一步

**English:** Study list and dictionary operations: adding, removing, updating,
searching, iteration, nested structures, and automation patterns.

**中文：** 深入学习列表与字典的添加、删除、更新、查找、遍历、嵌套结构与自动化
脚本常见模式。
