# Day 038: Python Closures and Decorators / Python 闭包与装饰器

Date / 日期: 2026-08-10

## Topic / 主题

**English:** Python first-class functions, closures, `nonlocal`, late binding,
lambda syntax, basic and parameterized decorators, argument forwarding,
`functools.wraps`, decorator stacking, and stateful decorators.

**中文：** Python 一等函数、闭包、`nonlocal`、延迟绑定、lambda 语法、基础装饰器
与带参数装饰器、参数转发、`functools.wraps`、装饰器叠加以及有状态装饰器。

## Goal / 目标

**English:** Build a precise mental model of functions as objects, understand
how closures preserve lexical state, and learn to write transparent decorators
that accept arbitrary arguments, preserve metadata, compose predictably, and
return the original function's result.

**中文：** 建立“函数也是对象”的准确思维模型，理解闭包如何保留词法状态，并学会
编写透明的装饰器，使其能够接收任意参数、保留元数据、按可预测方式组合，并返回
原函数的结果。

## Core Mental Model / 核心思维模型

**English:** A Python name refers to an object, and a function is one kind of
object. A closure combines a function with references to the lexical state it
needs. A decorator receives a callable and returns the callable that should be
bound to the decorated name; well-behaved wrappers forward calls, results, and
metadata deliberately.

**中文：** Python 名称引用对象，而函数也是对象的一种。闭包把函数与它所需词法
状态的引用组合起来。装饰器接收一个可调用对象，并返回应当绑定到被装饰名称上的
可调用对象；行为良好的包装器会有意识地转发调用参数、返回值与元数据。

## 10 Concept Questions / 10 个概念问题

### 1. Functions as first-class objects / 函数作为一等对象

**Question (English):** What does the following code print, and which Python
function property does it demonstrate?

**问题（中文）：** 下面的代码输出什么？它体现了 Python 函数的什么特性？

```python
def greet(name):
    return f"Hello, {name}"


another_name = greet

print(another_name("Luca"))
print(another_name is greet)
```

**Explanation (English):** Functions are first-class objects. A name can refer
to a function object just as it can refer to a string, list, or class, and the
object can be passed, returned, or stored without calling it.

**解说（中文）：** 函数是一等对象。名称可以像引用字符串、列表或类一样引用函数
对象；函数对象可以在不被调用的情况下传递、返回或保存。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
Hello, Luca
True
```

**English:** `another_name = greet` binds a second name to the same function
object; it neither calls nor copies the function. The `is` operator is
therefore true because both names have identical object identity.

**中文：** `another_name = greet` 把第二个名称绑定到同一个函数对象；它既没有
调用函数，也没有复制函数。由于两个名称引用同一对象，`is` 身份判断为真。

### 2. Capturing lexical state in a closure / 在闭包中捕获词法状态

**Question (English):** What does the code print? Why can the inner function
still access `factor` after `make_multiplier` has returned?

**问题（中文）：** 代码输出什么？为什么 `make_multiplier` 返回后，内部函数仍能
访问 `factor`？

```python
def make_multiplier(factor):
    def multiply(value):
        return value * factor

    return multiply


double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))
print(triple(5))
```

**Explanation (English):** A closure is a function together with access to the
lexical variables it references. Each invocation of the outer function creates
its own captured environment.

**解说（中文）：** 闭包由函数及其所引用词法变量的访问环境组成。外层函数每次
调用都会创建各自独立的捕获环境。

**Correct Answer (English):** The output is `10` followed by `15`. `double`
retains the `factor` cell created by `make_multiplier(2)`, while `triple`
retains the separate cell created by `make_multiplier(3)`. Returning the inner
function keeps the referenced state reachable even though the outer call has
finished.

**正确答案（中文）：** 输出依次为 `10` 和 `15`。`double` 保留
`make_multiplier(2)` 创建的 `factor` cell，而 `triple` 保留
`make_multiplier(3)` 创建的另一个 cell。返回内部函数后，即使外层调用已经
结束，被引用的状态仍然可达。

### 3. Rebinding captured state with `nonlocal` / 使用 `nonlocal` 重新绑定捕获状态

**Question (English):** Does the following code run normally? If not, what
happens, and what is the minimal correction?

**问题（中文）：** 下面的代码能否正常运行？如果不能，会发生什么？最小修改是
什么？

```python
def make_counter():
    count = 0

    def increment():
        count += 1
        return count

    return increment


counter = make_counter()

print(counter())
print(counter())
```

**Explanation (English):** Assignment to a name anywhere in a function body
normally makes that name local to the function. Augmented assignment reads the
current value before writing the new value, so scope classification matters
before the first statement in the wrapper executes.

**解说（中文）：** 通常只要函数体中存在对某个名称的赋值，Python 就会把该名称
判断为此函数的局部名称。增强赋值会先读取当前值再写入新值，因此在包装函数第一
条语句执行前，作用域分类就已经非常重要。

**Correct Answer (English):** The first call raises `UnboundLocalError`.
The closure can retain the outer `count`, but `count += 1` makes `count` local
to `increment`; its implicit read therefore occurs before that local name has
a value. Declare `nonlocal count` before the assignment:

**正确答案（中文）：** 第一次调用会抛出 `UnboundLocalError`。闭包能够保留外层
`count`，但 `count += 1` 使 Python 把 `count` 判断为 `increment` 的局部名称；
于是其中隐含的读取发生在该局部名称获得值之前。应在赋值前声明
`nonlocal count`：

```python
def increment():
    nonlocal count
    count += 1
    return count
```

**English:** The corrected counter prints `1` and then `2`. `nonlocal` selects
the nearest enclosing function scope containing that name; it does not select
the module-global scope.

**中文：** 修正后的计数器依次输出 `1` 和 `2`。`nonlocal` 选择包含该名称的最近
外层函数作用域，而不是模块全局作用域。

### 4. Lambda syntax and late name binding / Lambda 语法与名称延迟绑定

**Question (English):** What does the following code print? Why do the three
functions not preserve `0`, `1`, and `2` separately, and how can the code be
corrected?

**问题（中文）：** 下面的代码输出什么？为什么三个函数没有分别保留 `0`、`1`
和 `2`？如何修正？

```python
functions = []

for number in range(3):
    functions.append(lambda: number)

print([function() for function in functions])
```

**Explanation (English):** The lambda grammar is
`lambda parameters: expression`; an empty parameter list has no parentheses
and is written `lambda: expression`. Creating a lambda does not evaluate its
body. Names in the body are resolved when the function is called unless a
value is bound through another mechanism.

**解说（中文）：** lambda 语法是 `lambda 参数: 表达式`；无参数时不写圆括号，
应写成 `lambda: 表达式`。创建 lambda 不会执行其函数体；除非通过其他机制绑定
值，否则函数体中的名称会在函数调用时解析。

**Correct Answer (English):** The output is `[2, 2, 2]`. The loop creates
three different function objects, but every function later resolves the same
name `number`. A `for` statement does not create block scope, so after this
module-level loop the global `number` remains bound to `2`. Inside an enclosing
function, the analogous lambdas would share one closure cell and produce the
same result. Bind the current value as a default argument:

**正确答案（中文）：** 输出为 `[2, 2, 2]`。循环创建了三个不同的函数对象，但每个
函数之后都会解析同一个名称 `number`。`for` 语句不会创建块级作用域，因此这个
模块级循环结束后，全局 `number` 仍绑定到 `2`。若把类似代码放进外层函数，多个
lambda 会共享同一个闭包 cell，结果仍然相同。可以把当前值绑定为默认参数：

```python
functions.append(lambda saved=number: saved)
```

**English:** Default expressions are evaluated when each function is created,
so the corrected list is `[0, 1, 2]`. The default stores an object reference;
it is not a general-purpose deep copy.

**中文：** 默认值表达式在每个函数创建时求值，因此修正后的列表是 `[0, 1, 2]`。
默认值保存的是对象引用，并不是通用的深拷贝机制。

### 5. Basic decorator expansion / 基础装饰器展开

**Question (English):** What does the following code print, and which ordinary
assignment is `@uppercase` equivalent to?

**问题（中文）：** 下面的代码输出什么？`@uppercase` 等价于哪条普通赋值语句？

```python
def uppercase(function):
    def wrapper():
        result = function()
        return result.upper()

    return wrapper


@uppercase
def message():
    return "hello"


print(message())
```

**Explanation (English):** A decorator is applied after the decorated function
object is created. Its return value is rebound to the decorated function's
name, which is why the name normally refers to a wrapper afterward.

**解说（中文）：** 被装饰函数对象创建完成后，装饰器才会应用。装饰器返回值会
重新绑定到被装饰函数的名称上，因此之后该名称通常指向包装函数。

**Correct Answer (English):** The code prints `HELLO`. The decorator syntax is
equivalent to `message = uppercase(message)`. Calling the rebound `message`
invokes `wrapper`, which calls the original function, receives `"hello"`, and
returns its uppercase form.

**正确答案（中文）：** 代码输出 `HELLO`。装饰器语法等价于
`message = uppercase(message)`。调用重新绑定后的 `message` 会执行 `wrapper`；
它调用原函数得到 `"hello"`，然后返回其大写形式。

### 6. Forwarding arbitrary call arguments / 转发任意调用参数

**Question (English):** Does the following code run normally? If not, where
does it fail, and how should the wrapper support arbitrary positional and
keyword arguments?

**问题（中文）：** 下面的代码能否正常运行？如果不能，它在哪里失败？包装函数应
如何支持任意位置参数和关键字参数？

```python
def log_call(function):
    def wrapper():
        print(f"calling {function.__name__}")
        return function()

    return wrapper


@log_call
def add(left, right):
    return left + right


print(add(2, 3))
```

**Explanation (English):** After decoration, `add(2, 3)` calls `wrapper` with
two arguments. Python binds call arguments before entering a function body, so
an incompatible wrapper signature fails before any logging statement runs.

**解说（中文）：** 装饰完成后，`add(2, 3)` 实际使用两个参数调用 `wrapper`。
Python 会在进入函数体前绑定调用参数，因此不兼容的包装函数签名会在任何日志语句
执行前失败。

**Correct Answer (English):** The call raises `TypeError` because `wrapper`
accepts no positional arguments; it does not print `calling add` first. A
general wrapper collects and forwards both kinds of arguments and preserves
the original return value:

**正确答案（中文）：** 调用会抛出 `TypeError`，因为 `wrapper` 不接收位置参数；
它不会先输出 `calling add`。通用包装函数应收集并转发两类参数，同时保留原函数
返回值：

```python
def log_call(function):
    def wrapper(*args, **kwargs):
        print(f"calling {function.__name__}")
        return function(*args, **kwargs)

    return wrapper
```

**English:** Here `args` is a tuple of positional arguments and `kwargs` is a
dictionary of keyword arguments. The corrected program prints `calling add`
and then `5`.

**中文：** 这里 `args` 是位置参数组成的 tuple，`kwargs` 是关键字参数组成的
dictionary。修正后的程序先输出 `calling add`，再输出 `5`。

### 7. Preserving metadata with `functools.wraps` / 使用 `functools.wraps` 保留元数据

**Question (English):** What does the following code print? Why can the result
mislead debugging, introspection, and documentation tools?

**问题（中文）：** 下面的代码输出什么？为什么该结果可能误导调试、反射与文档
工具？

```python
def log_call(function):
    def wrapper(*args, **kwargs):
        print(f"calling {function.__name__}")
        return function(*args, **kwargs)

    return wrapper


@log_call
def add(left, right):
    """Add two numbers."""
    return left + right


print(add.__name__)
print(add.__doc__)
```

**Explanation (English):** The decorated name refers to the wrapper object,
whose metadata is separate from the original function's metadata. Argument
forwarding alone does not make the wrapper transparent to introspection.

**解说（中文）：** 被装饰名称引用的是包装函数对象，而它的元数据与原函数元数据
相互独立。仅仅转发参数并不能让包装函数对反射工具保持透明。

**Correct Answer (English):** The code prints `wrapper` and then `None`,
because the wrapper has that generated name and no docstring. Apply
`@functools.wraps(function)` to the wrapper:

**正确答案（中文）：** 代码先输出 `wrapper`，再输出 `None`，因为包装函数具有该
生成名称并且没有文档字符串。应对包装函数应用
`@functools.wraps(function)`：

```python
from functools import wraps


def log_call(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        print(f"calling {function.__name__}")
        return function(*args, **kwargs)

    return wrapper
```

**English:** The decorated function then reports `add` and
`Add two numbers.`. `wraps` copies important metadata and sets `__wrapped__`,
which lets many tools reach the original callable and signature.

**中文：** 此时被装饰函数会报告 `add` 和 `Add two numbers.`。`wraps` 会复制
重要元数据并设置 `__wrapped__`，使许多工具能够找到原始可调用对象及其签名。

### 8. Parameterized decorator factories / 带参数的装饰器工厂

**Question (English):** What does the following code print? Which ordinary
assignment process is `@repeat(3)` equivalent to?

**问题（中文）：** 下面的代码输出什么？`@repeat(3)` 等价于怎样的普通赋值过程？

```python
from functools import wraps


def repeat(times):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                function(*args, **kwargs)

        return wrapper

    return decorator


@repeat(3)
def greet(name):
    print(f"Hello, {name}")


greet("Luca")
```

**Explanation (English):** A decorator that accepts configuration needs an
outer factory call. The factory captures configuration, returns the actual
decorator, and that decorator receives the original function and returns a
wrapper.

**解说（中文）：** 接收配置的装饰器需要最外层工厂调用。工厂捕获配置并返回真正
的装饰器；该装饰器再接收原函数并返回包装函数。

**Correct Answer (English):** The program prints `Hello, Luca` three times.
The syntax expands to `greet = repeat(3)(greet)`, which can be viewed as:

**正确答案（中文）：** 程序连续三次输出 `Hello, Luca`。该语法展开为
`greet = repeat(3)(greet)`，也可以理解成：

```python
decorator = repeat(3)
greet = decorator(greet)
```

**English:** `repeat(3)` captures `times`, `decorator(greet)` captures the
original function, and later calls enter `wrapper`. The underscore loop name
conventionally signals that the loop value itself is unused.

**中文：** `repeat(3)` 捕获 `times`，`decorator(greet)` 捕获原函数，之后的调用
进入 `wrapper`。下划线循环名称按惯例表示循环值本身未被使用。

### 9. Stacking and executing multiple decorators / 叠加并执行多个装饰器

**Question (English):** In which order are the decorators applied and
executed, and what is the complete output?

**问题（中文）：** 多个装饰器按什么顺序应用和执行？完整输出是什么？

```python
from functools import wraps


def first(function):
    @wraps(function)
    def wrapper():
        print("first: before")
        function()
        print("first: after")

    return wrapper


def second(function):
    @wraps(function)
    def wrapper():
        print("second: before")
        function()
        print("second: after")

    return wrapper


@first
@second
def work():
    print("work")


work()
```

**Explanation (English):** Decorator expressions wrap from the function
outward, so the closest decorator is applied first. At call time, execution
enters the outermost wrapper and unwinds from the innermost wrapper after the
original call returns.

**解说（中文）：** 装饰器表达式从函数向外包装，因此最靠近函数的装饰器最先应用。
调用时先进入最外层包装函数；原函数返回后，再从最内层包装函数向外退出。

**Correct Answer (English):** Decoration is equivalent to
`work = first(second(work))`. The complete output is:

**正确答案（中文）：** 装饰过程等价于 `work = first(second(work))`。完整输出为：

```text
first: before
second: before
work
second: after
first: after
```

**English:** Application order and runtime entry order are related but not
identical descriptions: `second` is created first, while the resulting
`first` wrapper is entered first when `work()` is called.

**中文：** 应用顺序与运行时进入顺序相关，但不是同一种描述：`second` 最先创建，
而调用 `work()` 时最先进入最终得到的 `first` 包装函数。

### 10. Stateful decorators with closure cells / 使用闭包 cell 的有状态装饰器

**Question (English):** What is the complete output? Why does `count` persist
between calls, and what role does `nonlocal` play?

**问题（中文）：** 完整输出是什么？为什么两次调用之间的 `count` 不会丢失？
`nonlocal` 起什么作用？

```python
from functools import wraps


def count_calls(function):
    count = 0

    @wraps(function)
    def wrapper(*args, **kwargs):
        nonlocal count
        count += 1
        print(f"call {count}")
        return function(*args, **kwargs)

    return wrapper


@count_calls
def square(value):
    return value * value


print(square(3))
print(square(4))
```

**Explanation (English):** Decoration happens once, so the decorated name
continues to refer to the same wrapper closure. That wrapper keeps the same
captured `count` cell reachable across calls.

**解说（中文）：** 装饰过程只发生一次，因此被装饰名称持续引用同一个包装闭包。
该包装函数让同一个被捕获的 `count` cell 在多次调用之间保持可达。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
call 1
9
call 2
16
```

**English:** `nonlocal count` makes the augmented assignment update the
nearest enclosing function's binding rather than create an uninitialized
wrapper-local binding. The wrapper also returns the original function's
result, so each outer `print` displays the computed square. This simple counter
is stateful but does not by itself provide synchronization for concurrent
calls.

**中文：** `nonlocal count` 使增强赋值更新最近外层函数的绑定，而不是创建一个
尚未初始化的包装函数局部绑定。包装函数还返回原函数结果，所以外层每个 `print`
都会显示计算出的平方。这个简单计数器具有状态，但它本身没有为并发调用提供同步。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** Functions are objects, and assignment can bind multiple names
  to the same callable. **中文：** 函数是对象，赋值可以让多个名称绑定到同一个
  可调用对象。
- **English:** Closures preserve access to lexical variables after an outer
  call returns. **中文：** 外层调用返回后，闭包仍会保留对词法变量的访问。
- **English:** `nonlocal` permits deliberate rebinding of captured state.
  **中文：** `nonlocal` 允许有意识地重新绑定捕获状态。
- **English:** Lambda bodies use late name resolution, while default arguments
  can bind per-creation values. **中文：** Lambda 函数体使用延迟名称解析，而默认
  参数可以绑定每次创建时的值。
- **English:** Decorator syntax rebinds a function name to the decorator's
  return value. **中文：** 装饰器语法把函数名称重新绑定到装饰器返回值。
- **English:** Transparent wrappers forward `*args`, `**kwargs`, return values,
  and metadata with `functools.wraps`. **中文：** 透明包装函数使用 `*args`、
  `**kwargs`、返回值与 `functools.wraps` 转发调用和元数据。
- **English:** Parameterized decorators add a configuration-capturing factory
  layer. **中文：** 带参数装饰器增加一层用于捕获配置的工厂函数。
- **English:** Stacked decorators apply bottom-up and execute through nested
  wrappers. **中文：** 叠加装饰器自下而上应用，并通过嵌套包装函数执行。
- **English:** A closure cell can implement persistent decorator state.
  **中文：** 闭包 cell 可以实现持久的装饰器状态。

## Common Mistakes / 常见错误

- **English:** Saying a function belongs to a variable instead of saying a
  name is bound to a function object. **中文：** 把函数描述为属于某个变量，而不是
  说明名称绑定到函数对象。
- **English:** Assuming a closure cannot retain an outer local variable; the
  counter failure instead comes from assignment making the name wrapper-local.
  **中文：** 误以为闭包不能保留外层局部变量；计数器失败实际是因为赋值使名称被
  判断为包装函数局部名称。
- **English:** Writing zero-argument lambda parameters as `lambda ():` instead
  of `lambda:`. **中文：** 把无参数 lambda 写成 `lambda ():`，而不是
  `lambda:`。
- **English:** Expecting lambdas created in a loop to snapshot the loop value
  automatically. **中文：** 误以为循环中创建的 lambda 会自动保存循环值快照。
- **English:** Expecting a wrapper with no parameters to enter its body before
  rejecting supplied arguments. **中文：** 误以为无参数包装函数会先进入函数体，
  然后才拒绝传入的参数。
- **English:** Forgetting that decoration replaces visible function metadata
  unless `functools.wraps` preserves it. **中文：** 忘记装饰过程会替换可见函数
  元数据，除非使用 `functools.wraps` 保留它。
- **English:** Omitting the original function's output or return value when
  predicting a wrapper's complete output. **中文：** 预测包装函数完整输出时，遗漏
  原函数的输出或返回值。
- **English:** Confusing bottom-up decorator application with outer-to-inner
  wrapper entry at call time. **中文：** 混淆自下而上的装饰器应用顺序与调用时从
  外向内的包装函数进入顺序。

## Next Steps / 下一步建议

**English:** Implement logging, timing, retry, and validation decorators with
unit tests. Then study class-based decorators, descriptors, generic callable
typing with `ParamSpec` and `TypeVar`, standard decorators such as
`functools.lru_cache`, and wrappers that correctly handle methods, exceptions,
and asynchronous functions.

**中文：** 实现日志、计时、重试与校验装饰器，并为它们编写单元测试。随后学习
基于类的装饰器、描述符、使用 `ParamSpec` 与 `TypeVar` 进行泛型 callable 类型
标注、`functools.lru_cache` 等标准装饰器，以及能够正确处理方法、异常和异步函数
的包装器。
