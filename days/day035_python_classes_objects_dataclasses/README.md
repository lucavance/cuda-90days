# Day 035: Python Classes, Objects, and Dataclasses / Python 类、对象与数据类

Date / 日期: 2026-08-07

## Topic / 主题

**English:** Python's object model: class and instance attributes, mutable
state, bound methods, `classmethod`, `staticmethod`, properties, inheritance,
method resolution order, dataclasses, object protocols, equality, identity,
hashing, and frozen value objects.

**中文：** Python 对象模型：类属性与实例属性、可变状态、绑定方法、
`classmethod`、`staticmethod`、property、继承、方法解析顺序、dataclass、对象
协议、相等性、身份、哈希以及冻结值对象。

## Goal / 目标

**English:** Build a precise mental model of how Python stores and resolves
attributes, binds methods, shares or isolates mutable values, cooperates across
an inheritance hierarchy, and generates value-oriented classes with
`dataclass`.

**中文：** 建立准确的思维模型，理解 Python 如何存储和查找属性、绑定方法、
共享或隔离可变值、在继承层次中协作，以及如何使用 `dataclass` 生成面向值的类。

## Core Mental Model / 核心思维模型

**English:** A Python object combines identity, instance state, and behavior
found through its class. Reading an attribute searches the instance and then
the class hierarchy; assigning through an instance normally creates or updates
instance state. Special methods let ordinary classes participate in Python
protocols, while dataclasses generate common value-oriented methods from
declared fields.

**中文：** Python 对象结合了身份、实例状态以及通过类找到的行为。读取属性时会
先查实例，再查类层次；通过实例赋值通常会创建或更新实例状态。特殊方法让普通类
参与 Python 协议，而 dataclass 会根据声明的字段生成常见的面向值方法。

## 10 Concept Questions / 10 个概念问题

### 1. Class attributes and instance shadowing / 类属性与实例属性遮蔽

**Question (English):** What does the program print? Why does
`first.count += 1` not directly update `Counter.count`?

**问题（中文）：** 程序输出什么？为什么 `first.count += 1` 没有直接修改
`Counter.count`？

```python
class Counter:
    count = 0


first = Counter()
second = Counter()

first.count += 1

print(first.count)
print(second.count)
print(Counter.count)
```

**Explanation (English):** Attribute reading checks `first.__dict__` first
and then falls back to the class hierarchy. The read side of `+=` therefore
finds `Counter.count`, but the write side assigns the result through `first`
and creates an instance attribute that shadows the class attribute.

**解说（中文）：** 属性读取会先检查 `first.__dict__`，然后回退到类层次。因此
`+=` 的读取部分找到了 `Counter.count`，但写入部分通过 `first` 赋值，创建了一个
遮蔽类属性的实例属性。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
1
0
0
```

**English:** After the assignment, `first.__dict__` contains `{"count": 1}`.
`second` has no instance-level `count`, so it still reads the unchanged class
attribute whose value is zero.

**中文：** 赋值后，`first.__dict__` 包含 `{"count": 1}`。`second` 没有实例级
`count`，因此仍然读取值为 0、且未被修改的类属性。

### 2. Shared mutable class attributes / 共享的可变类属性

**Question (English):** What does the program print? Why does mutating
`first.tags` also affect what `second.tags` observes?

**问题（中文）：** 程序输出什么？为什么修改 `first.tags` 也会影响
`second.tags` 观察到的内容？

```python
class Job:
    tags = []


first = Job()
second = Job()

first.tags.append("gpu")

print(first.tags)
print(second.tags)
print(Job.tags)
```

**Explanation (English):** Neither instance has a `tags` attribute, so both
lookups reach the same list referenced by `Job.tags`. `append()` mutates that
list in place; it does not assign a new value to `first.tags` and therefore
does not create an instance shadow.

**解说（中文）：** 两个实例都没有自身的 `tags` 属性，因此两次查找都会到达
`Job.tags` 引用的同一个列表。`append()` 会原地修改该列表；它没有给
`first.tags` 赋予新值，所以不会创建实例级遮蔽属性。

**Correct Answer (English):** All three lookups observe the same mutated list:

**正确答案（中文）：** 三次查找都会观察到同一个已经修改的列表：

```text
['gpu']
['gpu']
['gpu']
```

**English:** Mutable class attributes are appropriate only for intentionally
shared state. Per-instance collections should normally be created during
instance initialization.

**中文：** 只有在有意共享状态时，才适合使用可变类属性。每个实例独有的集合
通常应在实例初始化时创建。

### 3. Mutable default arguments in constructors / 构造函数中的可变默认参数

**Question (English):** What does the program print? Even though `tags` is
assigned to an instance attribute, why do the two instances still interfere,
and how should the constructor be written?

**问题（中文）：** 程序输出什么？虽然 `tags` 被赋给了实例属性，为什么两个
实例仍然相互影响？构造函数应该怎样编写？

```python
class Job:
    def __init__(self, tags=[]):
        self.tags = tags


first = Job()
second = Job()

first.tags.append("gpu")

print(first.tags)
print(second.tags)
print(first.tags is second.tags)
```

**Explanation (English):** Default argument expressions are evaluated once
when the function is defined, not once per call. Both no-argument constructor
calls therefore receive the same default list and store references to that
same object in separate instance attributes.

**解说（中文）：** 默认参数表达式在函数定义时求值一次，而不是每次调用时求值。
因此两次无参数构造都会获得同一个默认列表，并在各自实例属性中保存对同一对象的
引用。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
['gpu']
['gpu']
True
```

**English:** Use an immutable sentinel and create a fresh list inside the
call. Copying a provided iterable also prevents accidental aliasing with the
caller's list:

**中文：** 应使用不可变哨兵，并在每次调用内部创建新列表。复制调用方提供的
iterable 还可以避免意外共享调用方的列表：

```python
class Job:
    def __init__(self, tags=None):
        self.tags = [] if tags is None else list(tags)
```

**English:** Python lists have `copy()` but no standard `clone()` method. The
`None` pattern is preferred because it avoids the mutable-default trap at the
function boundary.

**中文：** Python 列表具有 `copy()`，但没有标准 `clone()` 方法。推荐使用
`None` 模式，因为它从函数边界上消除了可变默认参数陷阱。

### 4. Bound instance methods and `self` / 绑定实例方法与 `self`

**Question (English):** What do the first two calls print, why are they
equivalent, and what happens if the final call is executed?

**问题（中文）：** 前两次调用分别输出什么？为什么它们等价？如果执行最后一次
调用，会发生什么？

```python
class Multiplier:
    def apply(self, value):
        return value * 2


worker = Multiplier()

print(worker.apply(3))
print(Multiplier.apply(worker, 3))

# print(Multiplier.apply(3))
```

**Explanation (English):** Accessing a normal method through an instance
creates a bound method. Python supplies that instance as the first positional
argument. Accessing the function through the class does not bind an instance,
so the caller must supply it explicitly.

**解说（中文）：** 通过实例访问普通方法时会创建绑定方法，Python 自动把该实例
作为第一个位置参数传入。通过类访问函数时不会绑定实例，因此调用方必须显式
提供它。

**Correct Answer (English):** The first two calls both print `6`.
`worker.apply(3)` is effectively `Multiplier.apply(worker, 3)`. In the final
call, `3` occupies the `self` position and `value` is missing, so Python raises
a `TypeError` at runtime.

**正确答案（中文）：** 前两次调用都输出 `6`。`worker.apply(3)` 实际等价于
`Multiplier.apply(worker, 3)`。在最后一次调用中，`3` 占据了 `self` 参数位置，
而 `value` 缺失，因此 Python 在运行时抛出 `TypeError`。

### 5. Class methods and static methods / 类方法与静态方法

**Question (English):** What does the program print? Why does `describe()`
produce a result based on the calling class, while `count_tokens()` needs
neither `self` nor `cls`?

**问题（中文）：** 程序输出什么？为什么 `describe()` 会根据调用它的类产生
不同结果，而 `count_tokens()` 不需要 `self` 或 `cls`？

```python
class Model:
    name = "base"

    @classmethod
    def describe(cls):
        return cls.name

    @staticmethod
    def count_tokens(text):
        return len(text.split())


class ChatModel(Model):
    name = "chat"


print(Model.describe())
print(ChatModel.describe())
print(ChatModel.count_tokens("hello gpu world"))
```

**Explanation (English):** A class method binds the class used for access as
`cls`, including a subclass that inherited the method. A static method performs
no automatic binding and behaves like a regular function organized inside the
class namespace.

**解说（中文）：** 类方法会把访问该方法时使用的类绑定为 `cls`，其中也包括继承
该方法的子类。静态方法不会执行自动绑定，其行为类似组织在类命名空间中的普通
函数。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
base
chat
3
```

**English:** `classmethod` is useful for class-level behavior and inheritable
alternative constructors. `staticmethod` is useful for related utility logic
that does not depend on instance or class state.

**中文：** `classmethod` 适合类级行为与可被继承的替代构造函数；
`staticmethod` 适合逻辑上属于该类、但不依赖实例或类状态的工具逻辑。

### 6. Properties, validation, and exception flow / Property、校验与异常流程

**Question (English):** What is printed before the invalid assignment, what
happens at that assignment, and is `done` printed? What benefit does the
property provide over directly exposing `_celsius`?

**问题（中文）：** 无效赋值前会打印什么？无效赋值时发生什么？`done` 是否会被
打印？相比直接公开 `_celsius`，property 提供了什么作用？

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value


temperature = Temperature(20)
temperature.celsius = 30
print(temperature.celsius)

temperature.celsius = -300
print("done")
```

**Explanation (English):** A property preserves attribute syntax while routing
reads and writes through methods. It can validate, compute, normalize, or log
access without forcing callers to change from `obj.attribute` to explicit
getter and setter calls.

**解说（中文）：** Property 在保留属性语法的同时，让读取与写入经过方法。它可以
执行校验、计算、规范化或日志记录，而无需迫使调用方把 `obj.attribute` 改成显式
getter 与 setter 调用。

**Correct Answer (English):** The program prints `30`, then raises
`ValueError: below absolute zero`. The exception interrupts normal control
flow, so `done` is not printed. The current constructor writes `_celsius`
directly and bypasses validation; it can delegate to the property instead:

**正确答案（中文）：** 程序先输出 `30`，随后抛出
`ValueError: below absolute zero`。异常中断正常控制流，因此不会打印 `done`。
当前构造函数直接写入 `_celsius`，绕过了校验；可以改为委托给 property：

```python
def __init__(self, celsius):
    self.celsius = celsius
```

### 7. Inheritance, MRO, and cooperative `super()` / 继承、MRO 与协作式 `super()`

**Question (English):** What is the complete output? Does `super()` simply
mean the direct parent class in this multiple-inheritance hierarchy?

**问题（中文）：** 完整输出是什么？在这个多继承层次中，`super()` 是否只是
表示直接父类？

```python
class A:
    def run(self):
        print("A")


class B(A):
    def run(self):
        print("B")
        super().run()


class C(A):
    def run(self):
        print("C")
        super().run()


class D(B, C):
    def run(self):
        print("D")
        super().run()


D().run()
```

**Explanation (English):** Python computes a method resolution order for the
actual class. Zero-argument `super()` continues lookup after the current class
in that MRO; it does not hard-code one named parent. This enables cooperative
multiple inheritance when each implementation calls `super()` consistently.

**解说（中文）：** Python 会为实际类型计算方法解析顺序。零参数 `super()` 会从
当前类之后的 MRO 位置继续查找，而不是硬编码某个具名父类。当各实现一致调用
`super()` 时，这种机制可以支持协作式多继承。

**Correct Answer (English):** The MRO is `D, B, C, A, object`, so the output
is:

**正确答案（中文）：** MRO 为 `D, B, C, A, object`，因此输出为：

```text
D
B
C
A
```

**English:** In particular, `super()` inside `B.run()` reaches `C.run()` for a
`D` instance because `C` follows `B` in `D`'s MRO.

**中文：** 特别是对于 `D` 实例，`B.run()` 内部的 `super()` 会进入 `C.run()`，
因为在 `D` 的 MRO 中，`C` 位于 `B` 之后。

### 8. Dataclasses and per-instance factories / Dataclass 与逐实例工厂

**Question (English):** What does the program print? Which common methods does
`@dataclass` generate, and why is `default_factory=list` required here?

**问题（中文）：** 程序输出什么？`@dataclass` 会生成哪些常用方法？为什么这里
需要使用 `default_factory=list`？

```python
from dataclasses import dataclass, field


@dataclass
class Job:
    name: str
    tags: list[str] = field(default_factory=list)


first = Job("train")
second = Job("train")

first.tags.append("gpu")

print(first)
print(second)
print(first == second)
print(first.tags is second.tags)
```

**Explanation (English):** A dataclass treats annotated attributes as fields
and normally generates `__init__`, `__repr__`, and field-wise `__eq__` methods.
A factory is called separately for every new instance, avoiding one shared
mutable default object.

**解说（中文）：** Dataclass 把带注解的属性视为字段，并通常生成 `__init__`、
`__repr__` 与逐字段比较的 `__eq__`。工厂会为每个新实例分别调用，从而避免共享
同一个可变默认对象。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
Job(name='train', tags=['gpu'])
Job(name='train', tags=[])
False
False
```

**English:** `name` and `tags` are separate fields. The instances compare
unequal because their `tags` values differ, and their lists have different
identities because `default_factory` created each list independently.

**中文：** `name` 与 `tags` 是两个独立字段。两个实例的 `tags` 值不同，因此
比较结果不相等；`default_factory` 分别创建了列表，所以两个列表的身份也不同。

### 9. Special methods and object protocols / 特殊方法与对象协议

**Question (English):** What does the program print? Why can `Batch` be used
with `len()`, `list()`, and `bool()` without inheriting from `list`?

**问题（中文）：** 程序输出什么？为什么 `Batch` 不需要继承 `list`，也能与
`len()`、`list()` 和 `bool()` 一起使用？

```python
class Batch:
    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


batch = Batch(["A", "B"])

print(len(batch))
print(list(batch))
print(bool(batch))
```

**Explanation (English):** Python operations are defined by protocols.
`len()` looks for `__len__`, iteration looks for `__iter__`, and truth testing
uses `__bool__` or falls back to `__len__`. A class can support an operation by
implementing its protocol instead of inheriting a particular concrete type.

**解说（中文）：** Python 操作由协议定义。`len()` 查找 `__len__`，迭代查找
`__iter__`，真值测试使用 `__bool__`，若不存在则回退到 `__len__`。类可以通过
实现协议来支持操作，而不必继承某个具体类型。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
2
['A', 'B']
True
```

**English:** The nonzero length makes the instance truthy. This protocol-
oriented behavior is a foundation of Python's duck typing.

**中文：** 非零长度使实例的真值为 `True`。这种面向协议的行为是 Python 鸭子
类型的基础。

### 10. Equality, identity, hashing, and frozen dataclasses / 相等性、身份、哈希与冻结数据类

**Question (English):** What does the program print? What happens if the final
assignment is executed? Why can two distinct objects compare equal, and what
does `frozen=True` provide?

**问题（中文）：** 程序输出什么？如果执行最后一次赋值会发生什么？为什么两个
不同对象可以比较相等？`frozen=True` 提供了什么？

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    name: str
    batch_size: int = 1


first = ModelConfig("demo", 4)
second = ModelConfig("demo", 4)

print(first == second)
print(first is second)
print(len({first, second}))

# first.batch_size = 8
```

**Explanation (English):** Equality asks whether values compare equivalent;
identity asks whether two references point to the exact same object. A frozen
dataclass blocks normal field reassignment and, when its fields are hashable,
can generate a field-based hash consistent with field-based equality.

**解说（中文）：** 相等性询问两个值是否等价；身份询问两个引用是否指向完全相同
的对象。冻结 dataclass 会阻止常规字段重新赋值；当字段可哈希时，它还能生成与
逐字段相等性一致的逐字段哈希。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
True
False
1
```

**English:** `first` and `second` are separately allocated objects, so `is` is
false, but the generated `__eq__` considers their equal fields. Equal hashes
and equal values make the set retain one member. Assigning `first.batch_size`
raises `dataclasses.FrozenInstanceError`. `frozen=True` does not intern or
reuse objects, and its immutability is shallow: a mutable object stored inside
a field may still be mutable.

**中文：** `first` 与 `second` 是分别分配的对象，因此 `is` 为 `False`；但生成的
`__eq__` 认为它们的字段相等。相等的哈希与值让集合只保留一个成员。给
`first.batch_size` 赋值会抛出 `dataclasses.FrozenInstanceError`。
`frozen=True` 不会驻留或复用对象，而且其不可变性是浅层的：字段内部保存的可变
对象仍可能被修改。

## Summary / 总结

- **English:** Instance assignment can shadow a class attribute, while
  in-place mutation of a mutable class attribute changes shared state.
  **中文：** 实例赋值可以遮蔽类属性，而原地修改可变类属性会改变共享状态。
- **English:** Mutable default arguments are created once; use an immutable
  sentinel or a dataclass factory to create per-instance collections.
  **中文：** 可变默认参数只创建一次；应使用不可变哨兵或 dataclass 工厂创建逐
  实例集合。
- **English:** Instance methods bind `self`, class methods bind the accessing
  class as `cls`, and static methods perform no implicit binding.
  **中文：** 实例方法绑定 `self`，类方法把访问类绑定为 `cls`，静态方法不执行
  隐式绑定。
- **English:** Properties add controlled behavior behind normal attribute
  syntax, including validation and computed access.
  **中文：** Property 在普通属性语法背后加入受控行为，包括校验与计算式访问。
- **English:** `super()` follows the actual class's MRO, enabling cooperative
  multiple inheritance rather than naming one fixed parent.
  **中文：** `super()` 遵循实际类型的 MRO，支持协作式多继承，而不是指定一个
  固定父类。
- **English:** Dataclasses generate common methods from fields, and special
  methods let custom objects participate in Python protocols.
  **中文：** Dataclass 根据字段生成常用方法，特殊方法让自定义对象参与 Python
  协议。
- **English:** Equality, identity, and hashing answer different questions;
  frozen dataclasses support immutable value-object patterns but do not imply
  object reuse.
  **中文：** 相等性、身份与哈希回答不同问题；冻结 dataclass 支持不可变值对象
  模式，但不表示对象复用。

## Common Mistakes / 常见错误

- **English:** Treating every attribute reached through an instance as private
  instance state, even when lookup actually reaches the class.
  **中文：** 把所有通过实例访问的属性都视为实例私有状态，即使查找实际到达了类。
- **English:** Describing shared mutable attributes only as pointers without
  distinguishing in-place mutation from reassignment and shadowing.
  **中文：** 只用指针描述共享可变属性，却没有区分原地修改、重新赋值与遮蔽。
- **English:** Using `[]`, `{}`, or another mutable object as a function's
  default argument.
  **中文：** 使用 `[]`、`{}` 或其他可变对象作为函数默认参数。
- **English:** Expecting Python lists to provide a standard `clone()` method.
  **中文：** 误以为 Python 列表提供标准 `clone()` 方法。
- **English:** Saying a class-level method call leaves `self` empty when the
  first supplied positional argument actually occupies that slot.
  **中文：** 认为通过类调用方法时 `self` 为空，而实际上第一个位置参数已经占据
  该参数位置。
- **English:** Assuming code after an uncaught exception continues executing.
  **中文：** 误以为未捕获异常之后的代码仍会继续执行。
- **English:** Treating `super()` as an alias for one direct parent instead of
  the next lookup position in the MRO.
  **中文：** 把 `super()` 当成某个直接父类的别名，而不是 MRO 中的下一个查找
  位置。
- **English:** Reading a dataclass representation as one combined list instead
  of separate named fields.
  **中文：** 把 dataclass 的表示形式理解成一个组合列表，而不是多个具名字段。
- **English:** Confusing `==` with `is`, or believing `frozen=True` causes
  instance caching and reuse.
  **中文：** 混淆 `==` 与 `is`，或误以为 `frozen=True` 会缓存并复用实例。

## Next Steps / 下一步建议

1. **English:** Study generic typing with `TypeVar`, `Generic`, bounded type
   variables, and generic methods.
   **中文：** 学习使用 `TypeVar`、`Generic`、有界类型变量与泛型方法进行泛型
   类型标注。
2. **English:** Compare nominal inheritance with structural typing through
   `typing.Protocol` and small inference-backend interfaces.
   **中文：** 通过 `typing.Protocol` 与小型推理 backend 接口，对比名义继承与
   结构化类型。
3. **English:** Practice composition and dependency injection by separating a
   model runner, scheduler, tokenizer, and metrics collector into small
   objects.
   **中文：** 把 model runner、scheduler、tokenizer 与 metrics collector 分成
   小对象，练习组合与依赖注入。
4. **English:** Explore `__post_init__`, `ClassVar`, ordering, slots, and the
   shallow limits of frozen dataclasses.
   **中文：** 探索 `__post_init__`、`ClassVar`、排序、slots 与冻结 dataclass 的
   浅层限制。
5. **English:** Continue into Python threading, the GIL, locks,
   `ThreadPoolExecutor`, and the distinction between CPU-bound and I/O-bound
   work.
   **中文：** 继续学习 Python 线程、GIL、锁、`ThreadPoolExecutor`，以及 CPU
   密集型与 I/O 密集型工作的区别。
