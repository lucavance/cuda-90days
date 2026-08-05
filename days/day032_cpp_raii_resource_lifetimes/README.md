# Day 032: C++ RAII and Resource Lifetimes / C++ RAII 与资源生命周期

Date / 日期: 2026-08-05

## Topic / 主题

**English:** C++ Resource Acquisition Is Initialization (RAII), automatic
object destruction, exception-safe cleanup, copy and move ownership semantics,
`std::unique_ptr`, `std::shared_ptr`, `std::lock_guard`, the Rule of Zero, and
RAII wrappers for CUDA device memory.

**中文：** C++ 资源获取即初始化（RAII）、对象自动析构、异常安全清理、复制与
移动所有权语义、`std::unique_ptr`、`std::shared_ptr`、`std::lock_guard`、
Rule of Zero，以及 CUDA device memory 的 RAII 包装。

## Goal / 目标

**English:** Build a reliable ownership model for C++ resources: understand
when destructors run, prevent double-free errors caused by shallow copies,
transfer unique ownership safely, compose existing RAII types, and apply the
same design to CUDA allocations and synchronization primitives.

**中文：** 建立可靠的 C++ 资源所有权模型：理解析构函数何时执行，避免浅拷贝
导致的 double free，安全转移独占所有权，组合已有 RAII 类型，并把同样的设计
应用到 CUDA 内存分配和同步原语。

## Core Mental Model / 核心思维模型

**English:** RAII binds resource acquisition to successful object construction
and resource release to object destruction. An automatic object is destroyed
when its scope ends, including during exception stack unwinding. A resource-owning
class must also define whether ownership can be copied, moved, or shared.
Whenever possible, compose standard RAII members so the containing class needs
no custom special-member functions.

**中文：** RAII 把资源获取绑定到对象的成功构造，把资源释放绑定到对象析构。
自动对象在离开作用域时会被析构，异常导致的栈展开也不例外。拥有资源的类还必须
明确所有权能否复制、移动或共享。应尽量组合标准 RAII 成员，使外层类不需要自行
实现特殊成员函数。

## 10 Concept Questions / 10 个概念问题

### 1. Automatic destruction at scope exit / 离开作用域时自动析构

**Question (English):** What is the complete output? Why is the resource
released even though the program never calls a `release` function explicitly?

**问题（中文）：** 完整输出是什么？程序没有显式调用 `release` 函数，为什么
资源仍然会被释放？

~~~cpp
#include <iostream>

struct Resource {
    Resource() {
        std::cout << "acquire\n";
    }

    ~Resource() {
        std::cout << "release\n";
    }
};

void run() {
    Resource resource;
    std::cout << "work\n";
}

int main() {
    run();
}
~~~

**Explanation (English):** `resource` has automatic storage duration. Its
construction occurs when execution reaches its declaration, and its destructor
runs automatically when `run()` leaves the scope. RAII uses this language rule
by acquiring a resource during construction and releasing it during
destruction.

**解说（中文）：** `resource` 具有自动存储期。执行到声明时完成构造，`run()`
离开作用域时自动执行析构函数。RAII 利用这一语言规则，在构造期间获取资源，在
析构期间释放资源。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
acquire
work
release
~~~

**English:** The C++ scope and destruction mechanism calls `~Resource()`;
RAII is the design pattern that attaches cleanup to that mechanism. A raw
pointer created with `new` would not automatically delete its allocation merely
because the pointer variable left scope.

**中文：** C++ 的作用域与析构机制负责调用 `~Resource()`；RAII 则是把清理逻辑
绑定到该机制的设计方式。使用 `new` 创建的裸指针不会仅因为指针变量离开作用域
就自动释放其内存。

### 2. Cleanup during exception unwinding / 异常栈展开期间的清理

**Question (English):** What is the complete output? Does the destructor run
before or after control enters the `catch` block?

**问题（中文）：** 完整输出是什么？析构函数是在进入 `catch` 之前还是之后
执行？

~~~cpp
#include <iostream>
#include <stdexcept>

struct Resource {
    Resource() {
        std::cout << "acquire\n";
    }

    ~Resource() {
        std::cout << "release\n";
    }
};

void run() {
    Resource resource;
    std::cout << "before throw\n";
    throw std::runtime_error("failed");
}

int main() {
    try {
        run();
    } catch (const std::exception&) {
        std::cout << "caught\n";
    }
}
~~~

**Explanation (English):** When an exception propagates out of a scope, C++
performs stack unwinding. Fully constructed automatic objects in the abandoned
scopes are destroyed in reverse construction order before execution reaches a
matching handler. This gives RAII cleanup the same behavior for normal returns,
early returns, and exceptions.

**解说（中文）：** 异常向作用域外传播时，C++ 会执行 stack unwinding（栈展开）。
在到达匹配的异常处理器之前，被离开作用域中已经完成构造的自动对象会按构造顺序
的反序析构。因此正常返回、提前返回和异常退出都能触发一致的 RAII 清理。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
acquire
before throw
release
caught
~~~

**English:** `resource` is destroyed before the `catch` block runs. Destructors
used for cleanup should normally not allow exceptions to escape, especially
during stack unwinding.

**中文：** `resource` 会在 `catch` 执行前完成析构。用于清理的析构函数通常不应
让异常向外传播，尤其是在栈展开期间。

### 3. Shallow copying an owning pointer / 浅拷贝资源所有权指针

**Question (English):** What ownership bug is introduced by
`Buffer second = first`? Why can the program fail when the objects are
destroyed?

**问题（中文）：** `Buffer second = first` 引入了什么所有权错误？为什么对象
析构时程序可能失败？

~~~cpp
#include <iostream>

class Buffer {
public:
    Buffer()
        : data_(new int[4]) {
        std::cout << "allocate\n";
    }

    ~Buffer() {
        delete[] data_;
        std::cout << "release\n";
    }

private:
    int* data_;
};

int main() {
    Buffer first;
    Buffer second = first;
}
~~~

**Explanation (English):** The compiler-generated copy constructor performs a
member-wise copy. Copying `data_` copies only the address, not the allocated
array. Both objects therefore claim ownership of the same allocation.

**解说（中文）：** 编译器生成的默认复制构造函数会逐成员复制。复制 `data_`
只会复制地址，而不会复制已分配的数组，因此两个对象都会声称拥有同一块内存。

**Correct Answer (English):** `first.data_` and `second.data_` point to the
same array. Destruction occurs in reverse order, so one object deletes the
array and the other later attempts to delete the same address. This is a
double-free error and undefined behavior; no exact failure or output after the
first invalid operation is guaranteed. The class must prohibit copying or
implement a correct deep copy.

**正确答案（中文）：** `first.data_` 与 `second.data_` 指向同一个数组。对象按
构造反序析构，其中一个先删除数组，另一个随后再次删除相同地址，形成 double
free 和未定义行为；第一次无效操作之后的输出或失败方式没有保证。该类必须禁止
复制，或实现正确的深拷贝。

### 4. Expressing unique ownership by deleting copy operations / 删除复制操作以表达独占所有权

**Question (English):** Can `Buffer second = first` compile after adding the
following declarations? What ownership rule do they express?

**问题（中文）：** 添加以下声明后，`Buffer second = first` 还能编译吗？这些
声明表达了什么所有权规则？

~~~cpp
Buffer(const Buffer&) = delete;
Buffer& operator=(const Buffer&) = delete;
~~~

**Explanation (English):** Constructing a new object from an lvalue requires a
copy constructor, while assigning one existing object from another requires a
copy-assignment operator. Marking both operations as deleted makes accidental
copying a compile-time error.

**解说（中文）：** 使用左值构造新对象需要复制构造函数，给已有对象复制赋值则
需要复制赋值运算符。把这两个操作标记为 deleted，会让意外复制在编译期报错。

**Correct Answer (English):** The statement does not compile because it selects
the deleted copy constructor. The declarations express unique ownership: one
`Buffer` owns one allocation, and a second owner cannot be created by copying.
If ownership transfer is desired, the class must provide move operations.

**正确答案（中文）：** 该语句不能编译，因为它选择了已删除的复制构造函数。
这些声明表达独占所有权：一个 `Buffer` 拥有一块内存，不能通过复制创建第二个
所有者。如果需要转移所有权，类必须提供移动操作。

### 5. Copying and moving `std::unique_ptr` / 复制与移动 `std::unique_ptr`

**Question (English):** Which alternative compiles? After the move, what are
the states of `first` and `second`?

**问题（中文）：** 哪一种写法能够编译？移动完成后，`first` 与 `second` 分别
处于什么状态？

~~~cpp
#include <memory>
#include <utility>

auto first = std::make_unique<int>(42);

// Alternative A / 写法 A
auto second = first;

// Alternative B / 写法 B
auto second = std::move(first);
~~~

**Explanation (English):** `std::unique_ptr` represents unique ownership and
therefore deletes its copy operations. It provides move operations that
transfer the stored pointer to a new owner. `std::move` itself is a cast that
makes the move operation selectable; the `unique_ptr` move constructor performs
the actual transfer.

**解说（中文）：** `std::unique_ptr` 表示独占所有权，因此删除了复制操作。它
提供移动操作，把保存的指针转交给新所有者。`std::move` 本身是一种让移动操作
能够被选择的转换；真正完成转移的是 `unique_ptr` 的移动构造函数。

**Correct Answer (English):** Alternative A does not compile. Alternative B
compiles. Afterwards, `second` owns the integer whose value is `42`, while
`first` remains a valid `unique_ptr` object in an empty state, normally with
`first.get() == nullptr`. `first` can still be destroyed, reset, or assigned a
new resource.

**正确答案（中文）：** 写法 A 不能编译，写法 B 可以编译。完成后，`second`
拥有值为 `42` 的整数；`first` 仍是有效的 `unique_ptr` 对象，但处于空状态，
通常满足 `first.get() == nullptr`。`first` 仍可以安全析构、reset 或接收新资源。

### 6. Emptying the source in a move constructor / 在移动构造中清空来源对象

**Question (English):** Why must the move constructor set
`other.data_ = nullptr`? What could happen without that assignment?

**问题（中文）：** 为什么移动构造函数必须执行 `other.data_ = nullptr`？如果
没有这条语句，可能发生什么？

~~~cpp
class Buffer {
public:
    Buffer()
        : data_(new int[4]) {}

    Buffer(Buffer&& other) noexcept
        : data_(other.data_) {
        other.data_ = nullptr;
    }

    ~Buffer() {
        delete[] data_;
    }

private:
    int* data_;
};
~~~

**Explanation (English):** A move must transfer ownership rather than duplicate
it. Copying the pointer into the destination is only half of that operation;
the source must stop claiming the resource. Deleting a null pointer is safe, so
an empty moved-from source can still be destroyed normally.

**解说（中文）：** 移动操作必须转移所有权，而不是复制所有权。把指针写入目标
对象只完成了一半，来源对象还必须停止声称拥有该资源。删除空指针是安全的，因此
被移动后置空的来源对象仍能正常析构。

**Correct Answer (English):** Without setting the source pointer to null,
`first` and `second` would both store the same address and both destructors
would call `delete[]` on it, causing double free and undefined behavior. With
the assignment, the destination is the sole owner and the source destructor is
a no-op for that resource.

**正确答案（中文）：** 如果不把来源指针设为空，`first` 与 `second` 会保存同一
地址，两个析构函数都会对它调用 `delete[]`，导致 double free 和未定义行为。
置空后，目标对象是唯一所有者，来源对象的析构函数不会处理该资源。

### 7. Composing RAII with the Rule of Zero / 使用 Rule of Zero 组合 RAII

**Question (English):** Which construction compiles, and does `Buffer` need a
custom destructor when its resource is stored in `std::unique_ptr<int[]>`?

**问题（中文）：** 当资源保存在 `std::unique_ptr<int[]>` 中时，哪一种构造能够
编译？`Buffer` 是否还需要自定义析构函数？

~~~cpp
#include <memory>
#include <utility>

class Buffer {
public:
    Buffer()
        : data_(std::make_unique<int[]>(4)) {}

private:
    std::unique_ptr<int[]> data_;
};

Buffer first;

Buffer second = first;             // A
Buffer third = std::move(first);   // B
~~~

**Explanation (English):** Special-member behavior composes from member
behavior. Because `unique_ptr` is non-copyable, the containing class cannot be
copied implicitly. Because `unique_ptr` is movable, the compiler-generated move
constructor can move the member. The compiler-generated destructor invokes the
member destructor automatically.

**解说（中文）：** 特殊成员函数的行为会由成员行为组合而来。由于 `unique_ptr`
不可复制，外层类也不能被隐式复制；由于 `unique_ptr` 可以移动，编译器生成的
移动构造函数能够移动该成员；编译器生成的析构函数会自动调用成员析构函数。

**Correct Answer (English):** A does not compile, while B compiles. `Buffer`
does not need to write `delete[]` or define a custom destructor. This is the
Rule of Zero: prefer RAII members whose ownership behavior allows the containing
class to use compiler-generated destruction, copying, and moving behavior.

**正确答案（中文）：** A 不能编译，B 可以编译。`Buffer` 不需要自行编写
`delete[]`，也不需要自定义析构函数。这就是 Rule of Zero：优先使用已经正确
管理所有权的 RAII 成员，让外层类使用编译器生成的析构、复制和移动行为。

### 8. Shared ownership and reference counts / 共享所有权与引用计数

**Question (English):** What is the complete output? Why is the resource not
released when `second` leaves its inner scope?

**问题（中文）：** 完整输出是什么？为什么 `second` 离开内部作用域时资源没有
立即释放？

~~~cpp
#include <iostream>
#include <memory>

struct Resource {
    ~Resource() {
        std::cout << "release\n";
    }
};

int main() {
    auto first = std::make_shared<Resource>();

    {
        auto second = first;
        std::cout << first.use_count() << '\n';
    }

    std::cout << first.use_count() << '\n';
}
~~~

**Explanation (English):** `std::shared_ptr` represents shared ownership using
a control block and a strong reference count. Copying a `shared_ptr` creates
another owner. Destroying one owner decrements the count, and the managed
resource is destroyed only when the last strong owner disappears.

**解说（中文）：** `std::shared_ptr` 通过控制块和强引用计数表示共享所有权。
复制 `shared_ptr` 会创建另一个所有者；销毁其中一个所有者只会减少计数，只有
最后一个强所有者消失时，被管理资源才会析构。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
2
1
release
~~~

**English:** Inside the nested scope, `first` and `second` are both owners.
After `second` is destroyed, `first` remains, so the count becomes one. The
resource is released when `first` is destroyed at the end of `main`. Cyclic
`shared_ptr` ownership can prevent the count from reaching zero; non-owning
`std::weak_ptr` references are commonly used to break such cycles.

**中文：** 在内部作用域中，`first` 与 `second` 都是所有者。`second` 析构后，
`first` 仍然存在，因此计数降为 1。`main` 结束、`first` 析构时才释放资源。
循环的 `shared_ptr` 所有权可能让计数永远无法归零，通常使用不拥有资源的
`std::weak_ptr` 打破这种循环。

### 9. Exception-safe locking with `std::lock_guard` / 使用 `std::lock_guard` 实现异常安全加锁

**Question (English):** What is the complete output? Does the mutex remain
locked after `work()` throws?

**问题（中文）：** 完整输出是什么？`work()` 抛出异常后，mutex 是否仍然处于
锁定状态？

~~~cpp
#include <iostream>
#include <mutex>
#include <stdexcept>

std::mutex mutex;

void work() {
    std::lock_guard<std::mutex> guard(mutex);

    std::cout << "locked\n";
    throw std::runtime_error("failed");
}

int main() {
    try {
        work();
    } catch (const std::exception&) {
        std::cout << "caught\n";
    }

    if (mutex.try_lock()) {
        std::cout << "unlocked\n";
        mutex.unlock();
    }
}
~~~

**Explanation (English):** `std::lock_guard` locks its mutex during
construction and unlocks it during destruction. When the exception leaves
`work()`, stack unwinding destroys `guard` before the handler runs, so the
mutex cannot be accidentally left locked by this control path.

**解说（中文）：** `std::lock_guard` 在构造时锁定 mutex，在析构时解锁。异常
离开 `work()` 时，栈展开会在执行异常处理器之前析构 `guard`，因此这条控制流
不会意外遗留一个被锁定的 mutex。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
locked
caught
unlocked
~~~

**English:** The `try_lock()` succeeds because `guard` has already unlocked
the mutex. Manual `lock()` and `unlock()` calls are easier to get wrong when an
early return or exception bypasses the explicit unlock operation.

**中文：** `try_lock()` 能够成功，是因为 `guard` 已经解锁 mutex。手动调用
`lock()` 与 `unlock()` 时，提前返回或异常更容易绕过显式解锁操作。

### 10. Moving a CUDA device-memory RAII wrapper / 移动 CUDA device memory RAII 包装器

**Question (English):** After the exception, how many times is `cudaFree`
called, which object releases the allocation, and why does the moved-from
object not release it again?

**问题（中文）：** 异常发生后，`cudaFree` 会调用几次？哪个对象负责释放分配？
为什么被移动的来源对象不会再次释放？

~~~cpp
#include <cuda_runtime.h>
#include <cstddef>
#include <stdexcept>
#include <utility>

class DeviceBuffer {
public:
    explicit DeviceBuffer(std::size_t bytes) {
        cudaMalloc(&pointer_, bytes);
    }

    ~DeviceBuffer() {
        if (pointer_ != nullptr) {
            cudaFree(pointer_);
        }
    }

    DeviceBuffer(const DeviceBuffer&) = delete;
    DeviceBuffer& operator=(const DeviceBuffer&) = delete;

    DeviceBuffer(DeviceBuffer&& other) noexcept
        : pointer_(std::exchange(other.pointer_, nullptr)) {}

private:
    void* pointer_ = nullptr;
};

void run() {
    DeviceBuffer first(1024);
    DeviceBuffer second = std::move(first);

    throw std::runtime_error("failed");
}
~~~

**Explanation (English):** `std::exchange` returns the old source pointer for
the destination initializer while replacing the source pointer with `nullptr`.
The move therefore leaves one owner. During stack unwinding, local objects are
destroyed in reverse construction order.

**解说（中文）：** `std::exchange` 返回来源指针的旧值，用于初始化目标对象，
同时把来源指针替换为 `nullptr`，因此移动后只剩一个所有者。栈展开期间，局部
对象按照构造顺序的反序析构。

**Correct Answer (English):** `cudaFree` is called exactly once. `second` is
destroyed first and releases the device allocation. `first` is destroyed next,
but its pointer is null, so its destructor performs no CUDA release. A
production implementation must also check the result of `cudaMalloc`, define
the required move-assignment behavior, and avoid throwing from its destructor.

**正确答案（中文）：** `cudaFree` 恰好调用一次。`second` 先析构并释放 device
allocation；随后 `first` 析构，但它的指针已经为空，因此不会执行 CUDA 释放。
生产实现还必须检查 `cudaMalloc` 的返回值，按需要定义移动赋值行为，并避免从
析构函数抛出异常。

## Summary / 总结

- **English:** Automatic objects are destroyed when their scopes end, during
  both normal control flow and exception stack unwinding.
  **中文：** 自动对象在离开作用域时析构，正常控制流和异常栈展开都会触发这一
  行为。
- **English:** RAII turns this deterministic destruction into deterministic
  cleanup for memory, locks, files, CUDA allocations, and other resources.
  **中文：** RAII 利用确定性的析构，为内存、锁、文件、CUDA allocation 等资源
  提供确定性清理。
- **English:** A raw owning pointer cannot safely use the compiler-generated
  shallow copy behavior; ownership must be deleted, deeply copied, moved, or
  shared deliberately.
  **中文：** 拥有资源的裸指针不能安全使用编译器生成的浅拷贝；必须有意识地禁止
  复制、实现深拷贝、移动或共享所有权。
- **English:** `std::unique_ptr` represents movable unique ownership, whereas
  `std::shared_ptr` represents reference-counted shared ownership.
  **中文：** `std::unique_ptr` 表示可以移动的独占所有权，`std::shared_ptr`
  表示基于引用计数的共享所有权。
- **English:** A moved-from object remains valid but must no longer own the
  transferred resource.
  **中文：** 被移动后的对象仍然有效，但不得继续拥有已经转移的资源。
- **English:** The Rule of Zero favors composing existing RAII types instead
  of manually implementing destruction and ownership operations.
  **中文：** Rule of Zero 鼓励组合已有 RAII 类型，而不是手动实现析构与所有权
  操作。
- **English:** `std::lock_guard` and a movable `DeviceBuffer` apply the same
  lifetime model to concurrency and CUDA programming.
  **中文：** `std::lock_guard` 与可移动的 `DeviceBuffer` 把同一生命周期模型
  应用到并发和 CUDA 编程。

## Difficulty and Current Level / 难度与当前水平评估

**English:** This session was an intermediate C++ ownership session rather than
a single introductory RAII lesson. It began with deterministic destruction,
then combined compiler-generated special members, shallow copying, move
semantics, smart pointers, exception unwinding, lock ownership, and a CUDA
resource wrapper. The density of interacting rules made it substantially harder
than its title suggested.

**中文：** 本次学习更接近一节中级 C++ 所有权课程，而不只是单一的 RAII 入门。
它从确定性析构开始，随后组合了编译器生成的特殊成员函数、浅拷贝、移动语义、
智能指针、异常栈展开、锁所有权和 CUDA 资源包装。多组规则相互作用，使实际难度
明显高于主题名称呈现出的难度。

- **English:** C++ ownership behavior is partly implicit: the compiler may
  generate, delete, or suppress copy and move operations according to the
  class members and declared special-member functions.
  **中文：** C++ 所有权行为有一部分是隐式的：编译器会根据类成员与已经声明的
  特殊成员函数，生成、删除或抑制复制与移动操作。
- **English:** Raw-pointer mistakes often produce undefined behavior rather
  than a clear compile-time error, so the learner must predict lifetime and
  aliasing behavior manually.
  **中文：** 裸指针错误经常产生未定义行为，而不是清晰的编译期错误，因此学习者
  必须主动推演生命周期与别名关系。
- **English:** Rust ownership knowledge provides the correct high-level model,
  but C++ expresses that model through destructors, value categories,
  `std::move`, special-member rules, and library conventions instead of one
  unified borrow checker.
  **中文：** Rust 所有权知识能够提供正确的上层模型，但 C++ 通过析构函数、值
  类别、`std::move`、特殊成员规则和库约定表达该模型，而不是依靠统一的借用
  检查器。
- **English:** Applying the model immediately to mutexes and CUDA allocations
  added concurrency and GPU API concerns before the core copy/move rules had
  become automatic.
  **中文：** 在复制与移动规则尚未熟练时，立即把模型应用到 mutex 与 CUDA
  allocation，又额外引入了并发和 GPU API 层面的负担。

**English:** The current C++ level is best described as advanced beginner,
approaching the early-intermediate boundary. Basic class scope, construction,
destruction, normal cleanup, and exception cleanup are understood. The basic
idea of movable unique ownership is emerging. The main gap is not general
programming ability; it is fluency with C++-specific implicit ownership rules,
special-member generation, smart-pointer selection, and resource-wrapper
design.

**中文：** 当前 C++ 水平更适合描述为“初级后段，正在接近中级入门”。已经理解
基本的类作用域、构造、析构、正常清理与异常清理，也开始建立可移动独占所有权的
概念。主要差距不是通用编程能力，而是对 C++ 特有的隐式所有权规则、特殊成员函数
生成规则、智能指针选择和资源包装设计还不够熟练。

**English:** The recommended adjustment is to split this material into three
reinforcement sessions: copy/move and special members; smart pointers and the
Rule of Zero/Five; then exception-safe CUDA RAII wrappers. Small compile-and-run
experiments should accompany the conceptual questions.

**中文：** 建议把本次内容拆成三个强化主题：复制/移动与特殊成员函数；智能指针
与 Rule of Zero/Five；异常安全的 CUDA RAII 包装。每个概念问答主题都配合小型
编译运行实验。

## Common Mistakes / 常见错误

- **English:** Treating RAII as a runtime component rather than a design
  pattern built on deterministic C++ object destruction.
  **中文：** 把 RAII 当成运行时组件，而不是建立在 C++ 确定性对象析构之上的
  设计方式。
- **English:** Assuming that an owning raw pointer is deeply copied by a
  compiler-generated copy constructor.
  **中文：** 误以为编译器生成的复制构造函数会深拷贝拥有资源的裸指针。
- **English:** Forgetting that both copy construction and copy assignment must
  be considered when expressing non-copyable ownership.
  **中文：** 表达不可复制所有权时，只考虑复制构造而忘记复制赋值。
- **English:** Describing a moved-from `unique_ptr` as a deleted object rather
  than a valid, normally empty object.
  **中文：** 把移动后的 `unique_ptr` 描述成已经删除的对象，而不是仍然有效、
  通常为空的对象。
- **English:** Assuming a class containing `unique_ptr` remains implicitly
  copyable.
  **中文：** 误以为包含 `unique_ptr` 的类仍然能够隐式复制。
- **English:** Using `shared_ptr` by default without a real shared-ownership
  requirement or without considering ownership cycles.
  **中文：** 在没有真实共享所有权需求时默认使用 `shared_ptr`，或忽略循环所有权。
- **English:** Manually locking a mutex without guaranteeing an unlock on all
  exit paths.
  **中文：** 手动锁定 mutex，却没有保证所有退出路径都会解锁。
- **English:** Ignoring CUDA API errors inside an RAII constructor or allowing
  a cleanup destructor to throw.
  **中文：** 在 RAII 构造函数中忽略 CUDA API 错误，或让负责清理的析构函数抛出
  异常。

## Next Steps / 下一步建议

1. **English:** Study the Rule of Five: destructor, copy constructor,
   copy-assignment operator, move constructor, and move-assignment operator.
   **中文：** 学习 Rule of Five：析构函数、复制构造、复制赋值、移动构造和移动
   赋值。
2. **English:** Implement and test a production-style `DeviceBuffer` that
   checks CUDA errors, exposes size and data accessors, and supports safe move
   assignment.
   **中文：** 实现并测试生产风格的 `DeviceBuffer`：检查 CUDA 错误，提供 size
   与 data accessor，并支持安全的移动赋值。
3. **English:** Compare `unique_ptr`, `shared_ptr`, and `weak_ptr` ownership
   graphs, including one cyclic-reference example.
   **中文：** 对比 `unique_ptr`、`shared_ptr` 与 `weak_ptr` 的所有权图，并练习
   一个循环引用示例。
4. **English:** Practice `std::scoped_lock`, `std::unique_lock`, and condition
   variables for more flexible synchronization lifetimes.
   **中文：** 练习 `std::scoped_lock`、`std::unique_lock` 与条件变量，理解更灵活
   的同步生命周期。
5. **English:** Extend the same RAII model to CUDA streams, events, cuBLAS
   handles, and other non-memory GPU resources.
   **中文：** 把同一 RAII 模型扩展到 CUDA stream、event、cuBLAS handle 等非
   内存 GPU 资源。
