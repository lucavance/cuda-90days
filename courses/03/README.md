# Course 03: C++ for CUDA Systems / 第三课：面向 CUDA 系统开发的 C++

## Goals, prerequisites, and evidence / 目标、前置知识与验证边界

**English:** This course connects ordinary C++ programs to reliable CUDA host code. The goal is to explain who owns every allocation, which objects borrow it, when ownership moves, and what must finish before release. By the end, you should be able to build a movable resource owner, explain its exception paths, organize a small CMake project, and design a C interface that Rust could call. Reading syntax alone is insufficient: predict state transitions, compile the examples, and compare the observations with those predictions.

**中文：** 本课把普通 C++ 程序连接到可靠的 CUDA 主机端代码。目标是说明每块内存由谁拥有、哪些对象只是借用、何时转移所有权，以及释放前哪些工作必须完成。学完后，你应能实现可移动的资源所有者，解释异常路径，组织小型 CMake 工程，并设计可由 Rust 调用的 C 接口。只读懂语法还不够：需要先预测状态变化，再编译示例，最后把实际观察与预测逐项比较。

**English:** The prerequisites are functions, loops, basic classes, arrays, and terminal commands. Rust ownership knowledge is useful but not required. This course primarily consolidates [Day 032](../../days/day032_cpp_raii_resource_lifetimes/README.md); the historical record remains intact. Unlike that conceptual session, this chapter develops the missing engineering connections: allocation failure, move assignment, build stages, and foreign-language boundaries. It is reasonable to study the chapter in three sittings: lifetimes, executable experiments, then CUDA and FFI design.

**中文：** 前置知识是函数、循环、基础类、数组与终端命令；理解 Rust 所有权有帮助，但不是要求。本课是 [Day 032](../../days/day032_cpp_raii_resource_lifetimes/README.md) 的主要系统化归属，原始学习记录继续保留。与当时的概念问答相比，本章补足分配失败、移动赋值、构建阶段和跨语言边界之间的工程联系。建议分三次学习：先掌握生命周期，再完成可执行实验，最后分析 CUDA 与外部接口设计。

**English:** Version verification date: 2026-09-18. The local environment is Ubuntu 26.04.1 LTS, GCC 15.2.0, CMake 4.2.3, and CUDA Toolkit 13.3.73. CPU examples use C++20; the CUDA wrapper requires only C++17. The RTX 4060 currently has a driver/NVML mismatch, so this course neither changes drivers nor claims GPU execution results. Successful host compilation proves syntax and linkage for the tested configuration; it does not prove device allocation, kernel correctness, or performance. NVIDIA's archived [CUDA 13.3 installation guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html) is the version reference.

**中文：** 版本核验日期为 2026 年 9 月 18 日。本地环境为 Ubuntu 26.04.1 LTS、GCC 15.2.0、CMake 4.2.3 和 CUDA Toolkit 13.3.73。CPU 实验采用 C++20，CUDA 包装器只需要 C++17。当前 RTX 4060 存在驱动与 NVML 不匹配，因此本课不修改驱动，也不声称完成 GPU 实测。主机编译成功只证明已测试配置下的语法与链接，不能证明设备分配、内核正确性或性能。版本依据采用 NVIDIA 的 [CUDA 13.3 安装归档](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html)。

## 1. Values, storage, and ownership / 值、存储与所有权

**English:** Separate three questions whenever you encounter a variable. Its value answers what it contains; its storage answers where those bytes reside; ownership answers who must eventually release a resource. A pointer variable contains an address, but its own storage is separate from the pointed-to allocation. Copying that address creates another way to access the same object. It neither copies the object nor tells either pointer to delete it. A diagram containing two arrows must therefore also name the owner; otherwise the most consequential part of the design is missing.

**中文：** 遇到变量时，先拆开三个问题：值说明它包含什么，存储说明这些字节放在哪里，所有权说明最终由谁释放资源。指针变量保存地址，但指针自身的存储与它指向的分配是两回事。复制地址只是增加一个访问同一对象的入口，既没有复制对象，也没有告诉任何指针应该负责删除。画出两条箭头之后，还必须标明所有者；否则图中恰好缺少最重要的资源管理约定。

**English:** Automatic storage duration usually makes a local object's destruction follow scope exit. Dynamic storage continues until explicitly released by its owner. A local vector combines these categories: the vector object is local, while its elements normally occupy a dynamic allocation managed by that object. Returning a vector by value therefore does not inherently return a dangling reference; the language and the vector's value operations transfer or construct the result appropriately. Returning a pointer into a destroyed local vector is a different operation and leaves no owner keeping its elements alive.

**中文：** 自动存储期通常让局部对象在离开作用域时析构；动态存储则持续到所有者主动释放。局部向量同时涉及这两类存储：向量对象本身是局部对象，元素通常位于由它管理的动态分配中。因此，按值返回向量并不天然产生悬垂引用，语言规则与向量的值操作会构造或转移结果。返回一个指向即将销毁的局部向量元素的指针则完全不同，因为已经没有所有者保证这些元素继续存在。

**English:** For an input-only sequence, a useful interface is `std::span<const float>`; for writable elements it is `std::span<float>`. A span carries a pointer and a count without owning the elements. It can prevent an API from losing the length, but it does not perform lifetime checking and C++20 subscript access is not a bounds-checking promise. Treat a span as a temporary permission to inspect a region. If the callee stores it for later, the interface must specify how the owner remains alive until that later use finishes.

**中文：** 对只读序列，可以使用 `std::span<const float>`；对可写元素，可以使用 `std::span<float>`。切片视图携带指针和数量，却不拥有元素。它能避免接口丢失长度信息，但不会执行生命周期检查，C++20 的下标访问也不承诺检查越界。应把切片视图理解为临时访问某片区域的许可。如果被调用者把它保存起来稍后使用，接口就必须规定所有者如何存活到最后一次访问完成。

**English:** Start API design with a small ownership vocabulary. A plain value usually means an independent value; `const T&` means borrowing for observation; `T&` allows modification of the existing object; `unique_ptr<T>` by value expresses transfer of unique ownership. None of these conventions alone proves that a raw pointer is valid, nor does `const` make all reachable data immutable. In CUDA host code, additionally name the address space and completion condition. A `float*` cannot tell the reader whether CPU dereference is legal or whether a stream still uses it.

**中文：** 设计接口时先建立一套小型所有权词汇：普通值通常表达独立的值，`const T&` 表达只读借用，`T&` 允许修改已有对象，按值传递 `unique_ptr<T>` 表达独占所有权移交。这些约定本身不能证明裸指针有效，`const` 也不会让所有间接可达的数据自动不可变。在 CUDA 主机代码中，还要说明地址空间和完成条件，因为一个 `float*` 无法告诉读者 CPU 能否解引用，或者某条流是否仍在使用它。

## 2. Pointers, references, and invalidation / 指针、引用与失效

**English:** A pointer may be reassigned and may represent a null value. A reference must be initialized to refer to an object, and assignment through it changes that object rather than reseating the reference. References are not a runtime validity mechanism: a reference can dangle after its referent dies. Prefer a reference for a required borrowed object and a pointer when absence is meaningful, but document both. Replacing every pointer with a reference would hide optionality without solving use-after-free.

**中文：** 指针可以重新赋值，也可以表示空值。引用必须在初始化时绑定对象，之后通过引用赋值会修改被引用对象，而不是让引用改绑。引用不是运行时有效性检查机制：被引用对象死亡之后，引用同样可能悬垂。必须存在的借用对象适合引用，允许缺失的对象适合指针，但两者都需要明确约定。把所有指针替换成引用，只会隐藏可选性，并不能解决释放后继续使用的问题。

**English:** Read `const` from the object it qualifies. `const float* p` permits changing `p` while prohibiting modification of the float through that pointer. `float* const p` fixes the pointer value but still permits element mutation. Passing either pointer by value copies an address; it does not transfer an allocation. A separate mutable alias may exist even when one view is const. For concurrent access, constness therefore cannot replace a rule preventing conflicting accesses or a synchronization operation that orders them.

**中文：** 阅读 `const` 时要看它限定的对象。`const float* p` 允许修改指针本身，但禁止通过该指针修改浮点数；`float* const p` 固定指针值，却仍允许修改元素。按值传递任何一种指针都只是复制地址，不会移交分配的所有权。即使某个视图只读，也可能同时存在其他可写别名。因此，并发访问中不能用常量限定替代禁止冲突访问的规则，也不能替代建立先后关系的同步操作。

**English:** Pointer arithmetic describes positions within an array, including its one-past-the-end position. The one-past position can be a loop boundary but cannot be dereferenced. A byte count and an element count are different dimensions: `n * sizeof(float)` describes storage bytes, whereas advancing a `float*` by `n` already advances by `n` elements. Before allocation, reject a count larger than `SIZE_MAX / sizeof(float)` to avoid wrapped size computation. A later bounds check cannot repair an allocation that was too small from the beginning.

**中文：** 指针算术描述数组内部的位置，也允许表示末尾之后的那个位置。末后指针可以作为循环边界，但不能解引用。字节数量和元素数量具有不同单位：`n * sizeof(float)` 表达存储字节，而浮点指针增加 `n` 已经表示前进 `n` 个元素。分配之前应拒绝大于 `SIZE_MAX / sizeof(float)` 的数量，避免尺寸计算发生回绕。如果一开始分配就偏小，后面仅仅检查元素下标无法补救。

**English:** An object's continued existence does not guarantee the continued validity of every pointer obtained from it. Growing a vector beyond capacity relocates its element storage, invalidating pointers, references, and iterators into the old allocation. `reserve` can reduce future reallocations within the reserved capacity; it cannot promise that a sequence will never move. The practical rule is to obtain views after storage organization is settled, use them within a clearly bounded interval, and reacquire them after operations that might invalidate them.

**中文：** 一个对象继续存在，并不保证从它取出的所有指针都继续有效。向量增长并超过容量时，会迁移元素存储，使指向旧分配的指针、引用和迭代器失效。预留容量可以减少容量范围内的后续重新分配，却不能承诺序列永远不移动。实际规则是：先完成存储组织，再获取视图，在明确限定的区间内使用；执行可能导致失效的操作之后，重新获取视图，而不是沿用之前缓存的地址。

## 3. Object lifetime is a contract / 对象生命周期是一份契约

**English:** For the ordinary class objects used here, suitable storage and completed initialization are prerequisites for normal use. Releasing or reusing the storage ends the old object's lifetime; an unchanged numerical address does not revive it. The [draft lifetime rules](https://eel.is/c++draft/basic.life) distinguish storage from live objects, with additional rules for construction, destruction, and implicit-lifetime types. This course does not require manual placement construction. Its working discipline is simpler: let containers and resource owners establish lifetime, and never access a view after the owner's relevant lifetime ends.

**中文：** 对本课使用的普通类对象，正常使用的前提是已有合适存储且初始化完成。释放或复用存储会终结原对象的生命周期，地址数值没有变化也不能让它重新有效。[标准草案的生命周期规则](https://eel.is/c++draft/basic.life) 区分存储与存活对象，并另外规定构造、析构和隐式生命周期类型。本课不要求手动定位构造，采用更简单的纪律：让容器和资源所有者建立生命周期，在相关所有者的生命周期结束后，不再访问其视图。

**English:** Lifetime diagrams should include the last use, not merely allocation and deallocation. In a synchronous CPU function, returning from the function often closes the borrow interval. In a submitted GPU operation, the submitting function can return while device work continues. Consequently, lexical scope and operational completion are two separate axes. A buffer's host wrapper may still exist while a raw view has become invalid through resize, or it may be destroyed while a queued operation still needs the allocation. Both errors become easier to see when the timeline includes all consumers.

**中文：** 生命周期图应该标出最后一次使用，而不只是分配和释放。同步 CPU 函数返回时，借用区间通常已经结束；但 GPU 操作提交之后，提交函数可能先返回，设备工作仍然继续。因此，词法作用域与操作完成是两条不同轴线。主机包装对象可能还活着，其裸视图却因调整大小而失效；包装器也可能先被析构，而排队操作仍然需要那块分配。把所有使用者放进时间线后，这两类错误都会更加明显。

**English:** Temporary lifetime extension is a specific language rule, not a general ownership feature of references. Certain direct bindings to a local const reference extend a temporary's life, but returning a reference to a local object does not. Nor should you infer that passing a temporary through another function gives a saved reference an arbitrary new lifetime. When an interface needs a result to survive the call independently, prefer returning an owning value. Doing so makes the required lifetime visible and allows normal value construction and move semantics to do their work.

**中文：** 临时对象生命周期延长是具体语言规则，不是引用普遍具有的所有权能力。某些直接绑定到局部常量引用的写法能够延长临时对象寿命，但返回局部对象的引用并不能。也不应推断把临时对象传过另一个函数，就能让保存的引用任意延寿。如果接口需要结果独立存活到调用结束之后，优先返回拥有资源的值。这样既让生命周期要求明确可见，也能交给正常的值构造与移动语义处理。

**English:** Treat undefined behavior as a violated reasoning boundary. Reading freed memory may appear to work because the bytes have not been overwritten, but that observation establishes no contract for the next run or optimization level. The experiments below deliberately avoid executing double deletion or dangling dereferences. Instead, they demonstrate rejected copies, counted release operations, and controlled exceptions. Sanitizers are useful additional evidence for executed paths, but their silence does not prove every possible path or every inter-thread ordering correct.

**中文：** 应把未定义行为理解为推理边界已经被破坏。读取已释放内存可能暂时成功，只是因为字节尚未被覆盖；这个观察不能建立下一次运行或另一优化级别下的保证。后面的实验不主动执行重复删除或悬垂解引用，而是通过复制被拒绝、释放次数统计和受控异常观察规则。检测器可以为实际执行路径补充证据，但没有报错不能证明所有可能路径或所有线程间顺序都正确。

## 4. RAII and construction order / RAII 与构造顺序

**English:** RAII places a cleanup obligation inside an object whose destruction is deterministic. Resource acquisition establishes the object's invariant; destruction discharges its obligation. The resource might be a heap allocation, file, mutex lock, CUDA stream, or device buffer. This is a design technique built on the language's destruction rules, not a separate garbage collector. Our buffer invariant will be either an empty state with null pointer and zero length, or one uniquely owned allocation paired with its correct element count.

**中文：** RAII 把清理责任放进一个具有确定性析构规则的对象中。获取资源建立对象不变量，析构则履行释放责任。资源可以是堆分配、文件、互斥锁、CUDA 流或设备缓冲区。这是一种建立在语言析构规则之上的设计技术，不是独立的垃圾回收器。后面的缓冲区不变量是两种状态之一：空指针加零长度的空状态，或者独占一块分配并保存正确元素数量的有效状态。

**English:** Fully constructed local objects are destroyed in reverse construction order when their scope exits normally. Destruction also occurs for the relevant completed objects during exception unwinding toward a matching handler. This allows one owner to cover normal return, early return, and exceptional exit. It does not promise cleanup after every form of process termination: forced termination and `abort` are outside this mechanism. A reliable explanation therefore identifies the control path instead of saying that destructors run under absolutely all circumstances.

**中文：** 正常离开作用域时，已经完成构造的局部对象按构造反序析构。异常向匹配处理器展开时，相关已构造对象也会被析构。因此，一个所有者就能覆盖正常返回、提前返回和异常退出。但这不承诺所有进程终止方式都会清理：强制终止与 `abort` 不属于这一机制。可靠的解释需要指出具体控制路径，而不能笼统地说析构函数在任何情况下都一定执行。

**English:** A class's members are initialized in declaration order, regardless of their order in the constructor's initializer list, and are destroyed in reverse order. If a member needs another member during destruction, declare the dependency first so it outlives the dependent member. For example, a session that owns both an execution context and buffers must make the context's required lifetime explicit. Rearranging initializer-list text cannot repair the wrong declaration order. Enable compiler warnings, but also explain this dependency in the type's structure.

**中文：** 类成员按照声明顺序初始化，不受构造函数初始化列表书写顺序影响，析构则采用相反顺序。如果一个成员在析构时需要另一个成员，应先声明被依赖的成员，让它活得更久。例如，一个会话同时拥有执行上下文和缓冲区，就必须明确上下文需要维持到何时。单纯调整初始化列表中的文本顺序不能修复错误的成员声明顺序。除了启用编译警告，也应该在类型结构中表达这种依赖。

**English:** When a constructor throws, the complete object's destructor is not called because that object never completed construction. Already completed base and member subobjects are cleaned up. This is why acquiring a resource into a raw pointer and then performing a throwing operation is dangerous: the raw pointer member has no cleanup behavior. Acquire into an existing owner immediately, or ensure that the owning constructor performs no throwing work after a successful raw acquisition. The controlled `FailingJob` experiment exercises member cleanup rather than assuming the incomplete outer object is destroyed. See [construction and exception rules](https://eel.is/c++draft/except.ctor).

**中文：** 构造函数抛出异常时，完整对象的析构函数不会执行，因为该对象从未完成构造；已经完成的基类和成员子对象会被清理。因此，先把资源放入裸指针，再执行可能抛出的操作很危险：裸指针成员自身没有清理行为。应立即交给已有资源所有者，或者保证原始资源获取成功后，拥有它的构造函数不再执行可能抛出的工作。后面的失败作业实验验证成员清理，不会误认为未完成的外层对象被析构。参见[构造与异常规则](https://eel.is/c++draft/except.ctor)。

## 5. Copying, moving, and special members / 复制、移动与特殊成员函数

**English:** Compiler-generated copying is memberwise. Copying an owning raw pointer copies its address, so two destructors may later release one allocation. A resource-owning type must deliberately choose among deep copying, forbidden copying, or shared ownership. Move semantics offer another operation: transferring an existing resource into a new owner without duplicating its contents. The [copy and move constructor rules](https://eel.is/c++draft/class.copy.ctor) describe generation and suppression; the practical lesson is to review all ownership operations when introducing a custom destructor.

**中文：** 编译器生成的复制按成员进行。复制拥有资源的裸指针会复制地址，因而两个析构函数可能在之后释放同一块分配。拥有资源的类型必须明确选择深拷贝、禁止复制或共享所有权。移动语义提供另一种操作：把既有资源转给新所有者，而不复制内部数据。[复制与移动构造规则](https://eel.is/c++draft/class.copy.ctor) 规定隐式生成和抑制条件；实际应记住的是，一旦引入自定义析构函数，就要重新检查全部所有权操作。

**English:** `std::move` is a cast that makes an expression eligible for overloads accepting an rvalue reference; it does not itself release, transfer, or copy a resource. The selected constructor or assignment operator determines what happens. A named rvalue-reference parameter is still an lvalue expression inside its function. Also, applying `std::move` to a const object preserves constness, so a usual `T(T&&)` cannot take that source. You must inspect overloads and type qualifiers rather than infer an ownership transfer from the word `move` alone.

**中文：** `std::move` 是一种类型转换，让表达式有机会匹配接受右值引用的重载；它本身不释放、不转移，也不复制资源。真正发生什么，由选中的构造或赋值函数决定。具名右值引用参数在函数内部仍然是左值表达式。另外，对常量对象使用 `std::move` 不会去掉常量性，因此通常的 `T(T&&)` 不能接收它。必须检查重载与类型限定，不能仅看到移动这个名字就断定所有权已经转移。

**English:** A move constructor initializes a new destination; move assignment replaces the state of an already existing destination. The second operation must account for the destination's previous resource, otherwise it leaks. Our owner checks self-assignment, releases its previous allocation, takes the source pointer and length, then empties the source. Its move operations are `noexcept` because these steps do not throw. This matters when generic containers choose how to relocate elements while preserving their documented exception guarantees.

**中文：** 移动构造初始化一个新的目标对象，移动赋值则替换已经存在的目标状态。后者必须处理目标先前拥有的资源，否则会泄漏。我们的所有者先检查自赋值，释放原来的分配，再接收来源指针和长度，并把来源置为空。由于这些步骤不抛异常，移动操作声明为 `noexcept`。这一承诺会影响通用容器在保持自身异常保证时，如何选择迁移元素的方式。

**English:** The moved-from state belongs to the type's contract. Our custom buffer explicitly becomes empty, and a moved-from `unique_ptr` relinquishes its pointer. Do not generalize this into a rule that every moved-from object is empty or unusable. Standard library types generally remain valid with an unspecified value unless a stronger requirement applies. A custom type must supply its own usable invariant. Test operations permitted by that invariant, such as destruction, assignment, or a size query, rather than relying on an accidental old value.

**中文：** 移动后的来源状态属于类型契约。我们的自定义缓冲区明确变为空，移走的 `unique_ptr` 也会放弃原指针。但不能推广成所有被移动对象都会变空或不可使用。标准库类型通常保持有效但值未指定，除非另有更强规定；自定义类型则必须自行定义可用的不变量。测试应针对不变量允许的操作，例如析构、再次赋值或查询长度，不应依赖偶然残留的旧数值。

**English:** The Rule of Five is a review checklist, not a requirement to write five complicated functions everywhere: destructor, copy constructor, copy assignment, move constructor, and move assignment. Prefer the Rule of Zero for application objects: compose owners such as vector and `unique_ptr`, then let member behavior define the containing type's operations. Write a custom owner only at the boundary of a resource API that lacks one. This keeps manual lifetime reasoning concentrated in a small, testable piece rather than spread across every algorithm.

**中文：** 五法则是一份检查清单，不是要求每个类都编写五个复杂函数：析构、复制构造、复制赋值、移动构造、移动赋值。应用层对象优先采用零法则，组合向量和 `unique_ptr` 等所有者，让成员行为决定外层类型操作。只有在尚无所有者的资源接口边界，才手写资源包装。这样能够把手工生命周期推理集中在一个小而可测试的地方，而不是散布到每个算法中。

## 6. Smart pointers and ownership graphs / 智能指针与所有权图

**English:** Use `unique_ptr<T>` when one object should hold deletion responsibility, and `unique_ptr<T[]>` for an owned array with the corresponding array deletion operation. A custom deleter can adapt a C resource API, but it must use the correct release function: memory obtained from `malloc` requires `free`, and device memory requires the matching CUDA operation. Returning `.get()` creates only a borrowed pointer; `.release()` abandons ownership and requires another owner to take responsibility. Confusing these operations can turn an apparently modern interface into a leak. See the [unique pointer specification](https://eel.is/c++draft/unique.ptr).

**中文：** 只有一个对象负责删除时使用 `unique_ptr<T>`，拥有数组并采用数组删除操作时使用 `unique_ptr<T[]>`。自定义删除器能够适配 C 资源接口，但释放函数必须匹配来源：`malloc` 获取的内存用 `free`，设备内存用对应的 CUDA 操作。调用 `.get()` 只产生借用指针；`.release()` 则放弃所有权，要求另一个所有者接管。混淆这些操作，会让看似现代的接口实际发生泄漏。参见[独占智能指针规范](https://eel.is/c++draft/unique.ptr)。

**English:** `shared_ptr` represents shared lifetime, with destruction when the final strong owner disappears. It does not automatically synchronize accesses to the pointed-to object's fields. Distinct shared-pointer objects can participate in the supported ownership operations across threads, while conflicting accesses to the same pointee still require a separate concurrency design. If two objects own each other through strong pointers, the strong counts never reach zero. Use a non-owning relationship, commonly `weak_ptr`, where one edge observes rather than extends lifetime. See the [shared pointer specification](https://eel.is/c++draft/util.smartptr.shared).

**中文：** `shared_ptr` 表达共享生命周期，最后一个强所有者消失时销毁资源。它不会自动同步被指向对象各字段的访问。不同的共享指针对象可以跨线程参与受支持的所有权操作，但对同一被指向对象的冲突访问，仍然需要单独设计并发规则。如果两个对象通过强指针互相拥有，强计数就不会降到零。应把其中的观察关系改为不延长生命周期的边，常见工具是 `weak_ptr`。参见[共享智能指针规范](https://eel.is/c++draft/util.smartptr.shared)。

**English:** Choose ownership by drawing a graph of responsibilities, not by choosing the most convenient pointer spelling. A request may own a batch; a batch may own tensor buffers; a profiler may merely observe that request. Making every arrow shared increases hidden lifetime coupling and makes release timing harder to predict. GPU memory is often large, so retaining one apparently small request object can retain a substantial device allocation. Explicit task completion and bounded ownership are as important as preventing premature destruction.

**中文：** 选择所有权时，应画出责任关系图，而不是选择最方便书写的指针。请求可以拥有批次，批次拥有张量缓冲区，而性能记录器可能只是观察请求。把每条箭头都改成共享所有权，会增加隐含的生命周期耦合，使释放时机更难预测。显存通常比较昂贵，保留一个看似很小的请求对象，就可能间接保留大量设备分配。因此，明确任务完成与限制所有权范围，和防止过早析构同样重要。

## 7. Exception guarantees and transactional changes / 异常保证与事务式修改

**English:** Exception safety asks what remains true after an operation fails. The basic guarantee preserves valid invariants and avoids leaks; the strong guarantee leaves the observable state unchanged on failure; a no-throw guarantee promises the operation will not propagate an exception. These are different commitments. RAII helps eliminate leaks but does not automatically restore overwritten elements or undo external side effects. For a resize operation, define whether losing old contents is allowed before selecting an implementation.

**中文：** 异常安全关注操作失败后还能保证什么。基本保证维持对象不变量并避免资源泄漏；强保证让失败前后的可观察状态保持不变；不抛异常保证承诺操作不向外传播异常。这是不同层次的承诺。RAII 有助于消除泄漏，却不会自动恢复被覆盖的元素，也不会撤销外部副作用。实现调整大小之前，应先规定是否允许丢失旧内容，再根据所需保证选择具体实现。

**English:** A practical strong-guarantee pattern is prepare, validate, then commit. Allocate a temporary buffer and populate it while leaving the original untouched. If preparation fails, the temporary cleans itself up and the original still represents the prior state. If preparation succeeds, exchange the two owners using a non-throwing swap. The temporary then owns the old allocation and releases it on scope exit. The boundary between preparation and commit should be short enough that a reviewer can identify every operation that might still fail.

**中文：** 一种实用的强保证写法是准备、验证、提交。先分配临时缓冲区并填充它，同时保持原对象不动。如果准备失败，临时对象自行清理，原对象仍表示旧状态；如果准备成功，就通过不抛异常的交换互换两个所有者。之后临时对象拥有旧分配，并在离开作用域时释放。准备与提交的边界应足够短，让审查者能够明确指出哪些操作仍可能失败。

**English:** Cleanup destructors should not propagate exceptions, especially while another exception is already unwinding. Yet some resource APIs can report release errors. Separate an explicit, checked completion or close operation from a non-throwing fallback destructor. The caller uses the explicit operation at a point where errors can be handled; the destructor provides last-resort cleanup. Logging a cleanup error is not equivalent to recovering the resource, and silently discarding it is not a strong success guarantee. Record this limitation in the wrapper's contract.

**中文：** 清理析构函数不应向外传播异常，尤其是在另一个异常已经展开时。但有些资源接口可能报告释放错误。可以把显式、可检查的完成或关闭操作，与不抛异常的兜底析构分开：调用者在能够处理错误的位置执行显式操作，析构提供最后的清理尝试。记录清理错误不等于成功回收资源，忽略错误也不能算强成功保证。这项限制必须写进包装器契约，而不能被自动清理的表象掩盖。

## 8. Templates and the host/device boundary / 模板与主机设备边界

**English:** A template describes a family of implementations selected by types or compile-time values. It is useful when element type or fixed block size changes code generation, while the algorithmic structure remains shared. It is not a promise of faster code: instantiating many variants can increase build time and binary size. Choose a few measurable variants, give them identical correctness checks, and compare their actual costs. A runtime input such as the current batch length usually remains a function argument unless there is a specific reason to specialize it.

**中文：** 模板描述由类型或编译期数值选择的一组实现。元素类型或固定线程块大小会改变生成代码，而算法结构基本相同时，模板很有用。但模板不保证更快：实例化过多变体会增加构建时间和二进制体积。应选择少量可以测量的变体，采用相同正确性检查，再比较实际成本。当前批次长度等运行时输入通常仍应作为函数参数，除非有明确理由为它生成专门版本。

**English:** A compiler normally needs a template's definition when instantiating it, which is why small generic implementations often live in headers. Hiding a definition in a source file is possible with a deliberate explicit-instantiation strategy for a known set of types. Otherwise, a declaration may let a caller compile while the required implementation is missing at link time. Do not repair that symptom by including arbitrary source files. Decide whether the library exposes a generic definition or a finite set of compiled specializations. See [template instantiation rules](https://eel.is/c++draft/temp.inst).

**中文：** 编译器实例化模板时通常需要看到定义，因此小型通用实现经常放在头文件中。对于已知的一组类型，可以通过明确的显式实例化策略，把定义留在源文件。否则，声明可能让调用者通过编译，但链接时缺少需要的实现。不要通过随意包含源文件来掩盖问题，应先决定库要公开通用定义，还是只提供有限的一组已编译特化。参见[模板实例化规则](https://eel.is/c++draft/temp.inst)。

**English:** CUDA adds execution-space constraints. A host-only function executes on the CPU; a device function executes on the GPU; a kernel entry point has its own launch mechanism. Marking a function for both host and device compilation does not make every called library operation available in both environments. A convenient host owner may contain exception handling, dynamic containers, or API calls unsuitable for a kernel. Keep resource management on the host and pass a small non-owning view, such as pointer and length, to device code after establishing its lifetime and address-space validity.

**中文：** CUDA 又增加了执行空间约束。主机函数在 CPU 执行，设备函数在 GPU 执行，内核入口有专门的启动机制。把函数标记为同时支持主机和设备编译，并不会让它调用的全部库操作都在两边可用。方便的主机所有者可能包含异常处理、动态容器或不适合内核的接口调用。应把资源管理留在主机，在先保证生命周期和地址空间有效的前提下，把指针加长度等小型非拥有视图传给设备代码。

**English:** Generic code still needs dimensional contracts. A buffer template parameter describes element type; its runtime length describes elements; an allocation API may accept bytes. Converting among those quantities belongs in one checked location, not scattered multiplications across callers. For scalar CUDA buffers, restricting the wrapper to an appropriate trivial element category avoids suggesting that raw device allocation constructs arbitrary C++ objects. Classes with nontrivial constructors require a separate construction strategy rather than a cast of the returned address.

**中文：** 通用代码仍然需要单位契约。缓冲区模板参数描述元素类型，运行时长度描述元素个数，而分配接口可能接收字节数。这些量之间的转换应该集中在一个带检查的位置，不能由各调用点随意相乘。对标量 CUDA 缓冲区，限定适当的平凡元素类别，可以避免让人误以为原始设备分配会构造任意 C++ 对象。具有非平凡构造函数的类需要另外的构造方案，不能靠把返回地址强制转换一下就完成。

## 9. Compilation, linking, and CMake / 编译、链接与 CMake

**English:** A header declaration teaches a translation unit which names and types exist; a definition supplies an implementation or object. Compiling each source produces an object file, and linking combines object files and libraries to resolve references. A missing header causes a compilation problem; a declared but absent function commonly causes an undefined-reference link failure; an unavailable shared library can fail when loading the executable. Identify the failed stage before changing flags, because these stages need different fixes.

**中文：** 头文件声明让翻译单元知道名字与类型，定义则提供实现或对象。各源文件编译后产生目标文件，链接再把目标文件和库组合起来解析引用。缺少头文件是编译问题；函数已声明但缺少实现，通常表现为未定义引用的链接错误；找不到共享库则可能在加载可执行文件时失败。调整选项之前先定位失败阶段，因为这几种阶段需要完全不同的修复办法。

**English:** Organize a CMake build around targets. Put the language requirement on the target, expose headers through target include directories, and express dependencies with `target_link_libraries`. `PRIVATE` affects the target itself; `PUBLIC` additionally communicates relevant usage requirements to consumers; `INTERFACE` describes requirements for consumers without applying them to that target's own compilation. This is easier to reason about than global include paths and library flags that silently affect unrelated components. See [CMake's target dependency documentation](https://cmake.org/cmake/help/v4.2/command/target_link_libraries.html).

**中文：** CMake 工程应围绕目标组织：把语言要求写在目标上，通过目标包含目录公开头文件，用 `target_link_libraries` 表达依赖。`PRIVATE` 影响目标自身，`PUBLIC` 还把相关使用要求传给使用者，`INTERFACE` 只描述使用者所需条件，不用于该目标自身编译。相比悄悄影响无关组件的全局包含路径和库选项，这种写法更容易推理。参见 [CMake 目标依赖文档](https://cmake.org/cmake/help/v4.2/command/target_link_libraries.html)。

**English:** Separate the compiler driver from the libraries being linked. A host-only source that calls CUDA Runtime functions can use the host C++ compiler with CUDA headers and `CUDA::cudart`. A source containing kernel launch syntax needs CUDA language processing, typically through `nvcc`. NVIDIA's [13.3 compiler-driver guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html) explains host/device compilation and separate compilation. Enabling device linking addresses cross-translation-unit device references; it does not repair an unrelated missing host function or an incompatible driver.

**中文：** 要区分编译器驱动程序与参与链接的库。只调用 CUDA Runtime 函数的主机源文件，可以使用主机 C++ 编译器，并配合 CUDA 头文件及 `CUDA::cudart`。包含内核启动语法的源文件则需要 CUDA 语言处理，通常由 `nvcc` 参与。NVIDIA 的 [13.3 编译驱动指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html) 解释主机设备编译与分离编译。设备链接解决跨翻译单元设备引用，不能修复无关的主机函数缺失或驱动不兼容。

**English:** Record configuration facts independently. The compiler version, C++ standard, target architecture, toolkit version, and driver state answer different questions. The CUDA version displayed by a driver utility is not a substitute for the `nvcc` version, and finding toolkit headers does not verify a usable GPU. For this course, the CPU build is unconditional and the CUDA check is optional at configuration time. Keeping them separate makes a host-language learning experiment reproducible even while device execution is unavailable.

**中文：** 配置事实应分别记录。编译器版本、C++ 标准、目标架构、工具包版本和驱动状态回答的是不同问题。驱动工具显示的 CUDA 版本不能替代 `nvcc` 版本，找到工具包头文件也不能证明 GPU 可用。本课 CPU 构建无条件启用，CUDA 检查则在配置时选择开启。把两者分开，能够在设备暂不可执行时，仍然复现主机语言与工程组织实验，而不让所有学习依赖驱动状态。

## 10. CPU experiment: observe the ownership transitions / CPU 实验：观察所有权转移

**English:** Run the following blocks in the same terminal. They create an isolated temporary directory and leave repository files untouched. The class deliberately implements a raw allocation owner to expose the mechanism; application code should normally prefer vector or an existing owner. Its counters describe this single-threaded experiment only, and are not a production telemetry design. Before running, predict how many allocations occur, which allocation move assignment releases, and whether failure during resize changes the original size and values.

**中文：** 请在同一个终端依次执行下列代码块。它们创建独立临时目录，不改动仓库文件。为了暴露底层机制，这个类故意手写原始分配的所有者；应用代码通常应优先采用向量或现成所有者。统计计数只服务本次单线程实验，并不是生产环境的监控设计。运行之前，先预测分配总次数、移动赋值释放的是哪块分配，以及调整大小失败后，原有长度与元素内容是否改变。

```bash
COURSE03_DIR=$(mktemp -d /tmp/course03.XXXXXX)
cd "$COURSE03_DIR"
cat > cpu_buffer.hpp <<'CPP'
#pragma once
#include <algorithm>
#include <cstddef>
#include <stdexcept>
#include <utility>

class CpuBuffer {
    int* data_ = nullptr;
    std::size_t size_ = 0;

    void release() noexcept {
        if (data_) {
            delete[] data_;
            ++releases;
            --live;
        }
        data_ = nullptr;
        size_ = 0;
    }

public:
    inline static int allocations = 0;
    inline static int releases = 0;
    inline static int live = 0;

    CpuBuffer() noexcept = default;

    explicit CpuBuffer(std::size_t n)
        : data_(n ? new int[n]{} : nullptr), size_(n) {
        if (data_) {
            ++allocations;
            ++live;
        }
    }

    ~CpuBuffer() noexcept { release(); }
    CpuBuffer(const CpuBuffer&) = delete;
    CpuBuffer& operator=(const CpuBuffer&) = delete;

    CpuBuffer(CpuBuffer&& other) noexcept
        : data_(std::exchange(other.data_, nullptr)),
          size_(std::exchange(other.size_, 0)) {}

    CpuBuffer& operator=(CpuBuffer&& other) noexcept {
        if (this != &other) {
            release();
            data_ = std::exchange(other.data_, nullptr);
            size_ = std::exchange(other.size_, 0);
        }
        return *this;
    }

    std::size_t size() const noexcept { return size_; }
    const int* data() const noexcept { return data_; }

    int& at(std::size_t i) {
        if (i >= size_) throw std::out_of_range("buffer index");
        return data_[i];
    }

    const int& at(std::size_t i) const {
        if (i >= size_) throw std::out_of_range("buffer index");
        return data_[i];
    }

    void swap(CpuBuffer& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

    void resize_preserving(std::size_t n, bool inject_failure = false) {
        CpuBuffer replacement(n);
        for (std::size_t i = 0; i < std::min(n, size_); ++i)
            replacement.data_[i] = data_[i];
        if (inject_failure) throw std::runtime_error("prepare failed");
        swap(replacement);
    }
};
CPP

cat > main.cpp <<'CPP'
#include "cpu_buffer.hpp"
#include <cassert>
#include <iostream>
#include <type_traits>

struct FailingJob {
    inline static int destructors = 0;
    CpuBuffer temporary{3};
    FailingJob() { throw std::runtime_error("job setup failed"); }
    ~FailingJob() { ++destructors; }
};

int main() {
    static_assert(!std::is_copy_constructible_v<CpuBuffer>);
    static_assert(!std::is_copy_assignable_v<CpuBuffer>);
    static_assert(std::is_nothrow_move_constructible_v<CpuBuffer>);
    static_assert(std::is_nothrow_move_assignable_v<CpuBuffer>);
    {
        CpuBuffer first(4);
        for (std::size_t i = 0; i < first.size(); ++i)
            first.at(i) = static_cast<int>(i + 1);
        const int* original = first.data();
        CpuBuffer second(std::move(first));
        assert(first.size() == 0 && first.data() == nullptr);
        assert(second.data() == original);
        CpuBuffer third(2);
        third = std::move(second);
        assert(second.size() == 0 && third.data() == original);
        std::cout << "move keeps address: yes\n";

        bool failed = false;
        try { third.resize_preserving(8, true); }
        catch (const std::runtime_error&) { failed = true; }
        assert(failed && third.size() == 4 && third.at(3) == 4);
        assert(third.data() == original);
        third.resize_preserving(8);
        assert(third.size() == 8 && third.at(3) == 4);
        assert(third.at(7) == 0);
        std::cout << "strong guarantee: yes\n";

        const int live_before = CpuBuffer::live;
        failed = false;
        try { FailingJob job; }
        catch (const std::runtime_error&) { failed = true; }
        assert(failed && CpuBuffer::live == live_before);
        assert(FailingJob::destructors == 0);
        std::cout << "constructor member cleanup: yes\n";

        failed = false;
        try { third.at(99) = 9; }
        catch (const std::out_of_range&) { failed = true; }
        assert(failed);
        std::cout << "bounds failure: yes\n";
    }
    assert(CpuBuffer::allocations == 5);
    assert(CpuBuffer::releases == 5 && CpuBuffer::live == 0);
    std::cout << "allocations=" << CpuBuffer::allocations
              << " releases=" << CpuBuffer::releases
              << " live=" << CpuBuffer::live << '\n';
}
CPP

cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.24)
project(course03 LANGUAGES C CXX)
enable_testing()
add_executable(ownership main.cpp)
target_compile_features(ownership PRIVATE cxx_std_20)
target_compile_options(ownership PRIVATE -Wall -Wextra -Wpedantic)
add_test(NAME ownership_transitions COMMAND ownership)
CMAKE

cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
./build/ownership
```

**English:** The expected output below records semantic properties, not pointer values that change between executions. Five allocations are paired with five releases: the initial buffer, the move-assignment destination, failed preparation, successful preparation, and the failing job's member. Moving does not allocate in this class. The failed resize discards its temporary while keeping the old address; the successful resize commits replacement storage. These are more informative assertions than merely checking that the process exited successfully.

**中文：** 下方预期输出记录语义性质，不打印每次运行可能变化的地址。五次分配对应五次释放，来源依次是初始缓冲区、移动赋值的目标、失败的准备、成功的准备，以及构造失败作业的成员。这个类的移动不会分配。失败调整大小时丢弃临时对象，保留旧地址；成功时才提交新存储。相比只检查程序正常退出，这些断言能够说明更多实际所有权性质。

```text
move keeps address: yes
strong guarantee: yes
constructor member cleanup: yes
bounds failure: yes
allocations=5 releases=5 live=0
```

**English:** The constructor-failure case distinguishes two destruction events. `FailingJob` never becomes a complete object, so its own destructor count remains zero. Its buffer member completed construction earlier and is therefore destroyed when setup throws. The live allocation count returns to its prior value. If the member had been a naked pointer with no owning subobject, there would be no matching automatic cleanup. This is the exact reason to acquire resources into owners before beginning additional fallible setup.

**中文：** 构造失败案例区分了两种析构事件。失败作业从未成为完整对象，因此它自己的析构计数保持零；其中的缓冲区成员此前已完成构造，所以设置过程抛出异常时会被销毁，存活分配数量恢复原值。如果成员只是没有所有者包装的裸指针，就不会有对应的自动清理。这正是为什么应该先把资源交给所有者，再开始其他可能失败的初始化步骤，而不是依赖外层析构来补救。

**English:** Now verify that an accidental copy is rejected at the type boundary. The shell block treats compilation failure as the expected result and reports unexpected success as an error. Diagnostic wording varies with compiler version, so the stable fact is the rejected use of a deleted copy constructor. This is safer and stronger than constructing two owners of one allocation and hoping a runtime checker reports the later double deletion. The program being rejected is itself the desired behavior.

**中文：** 接下来验证意外复制会在类型边界被拒绝。脚本把编译失败视为预期结果，把意外成功视为错误。诊断文字会随编译器版本变化，稳定事实是删除的复制构造函数不允许被调用。这比先制造同一分配的两个所有者，再指望运行时检测器发现重复释放，更安全也更有约束力。此处程序被拒绝就是我们要验证的正确行为，并不是实验没有完成。

```bash
cat > copy_must_fail.cpp <<'CPP'
#include "cpu_buffer.hpp"
int main() {
    CpuBuffer first(4);
    CpuBuffer second = first;
}
CPP
if g++ -std=c++20 -Wall -Wextra -c copy_must_fail.cpp -o copy_must_fail.o; then
    printf '%s\n' 'ERROR: copying unexpectedly compiled'
    exit 1
else
    printf '%s\n' 'Expected: unique ownership cannot be copied'
fi

g++ -std=c++20 -g -O1 -Wall -Wextra -Wpedantic \
    -fsanitize=address,undefined -fno-omit-frame-pointer \
    main.cpp -o ownership_sanitized
./ownership_sanitized
```

**English:** Debug configuration keeps the assertions enabled, and the sanitized build exercises the same controlled paths with additional memory and undefined-behavior checks. This does not measure performance. To extend the experiment meaningfully, add empty-buffer movement, self move assignment, shrinking, and repeated replacement, then predict the ownership graph before running. Avoid adding sleeps or relying on printed addresses. The important evidence is preserved invariants and matched resource obligations across each transition.

**中文：** 调试配置保留断言，检测器构建则在相同受控路径上增加内存与未定义行为检查，这不属于性能测量。若要有意义地扩展实验，可以加入空缓冲区移动、自移动赋值、缩小和反复替换，并在运行前预测所有权关系。不要通过等待时间或打印地址碰运气。真正需要的证据，是每次状态转换之后不变量仍成立，以及获取资源所产生的责任都被正确履行。

## 11. A CUDA allocation owner with explicit limitations / 具有明确限制的 CUDA 分配所有者

**English:** The next owner manages raw storage for float elements and does not launch a kernel. Its constructor checks byte-count overflow and the allocation result; copying is deleted; moving transfers the handle. `close()` consumes the local handle and returns the release status, while the destructor logs an error without throwing. If release reports failure, the empty wrapper does not prove that reclamation succeeded. This deliberate one-attempt policy avoids pretending that an ambiguous error can always be safely retried. Production software needs an explicit cleanup-error policy.

**中文：** 下面的所有者管理浮点元素的原始设备存储，不启动内核。构造函数检查字节计算溢出和分配结果，禁止复制，移动时移交句柄。显式关闭消耗本地句柄并返回释放状态，析构则记录错误而不抛出。如果释放报告失败，包装器变空不能证明资源已经成功回收。这里明确采用只尝试一次的策略，避免假装含义不明确的错误总能安全重试；生产系统必须另外规定清理错误处理方式。

**English:** Its precondition is that all GPU users have completed before explicit close, destruction, or replacing an owned allocation through move assignment. The caller must also use the correct device/context conditions for the allocation. These conditions are not encoded in `float*` or in ordinary C++ move semantics. Do not use a presumed synchronization side effect of `cudaFree` as your whole lifetime design. The [CUDA 13.3 memory API](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html) is the reference for allocation and release behavior.

**中文：** 使用前提是：显式关闭、析构或通过移动赋值替换已有分配之前，所有 GPU 使用者都已完成；调用者还必须满足该分配所需的正确设备与上下文条件。这些条件没有编码在浮点指针或普通 C++ 移动语义中。不能把想当然的释放同步副作用当作整个生命周期设计。分配和释放行为以 [CUDA 13.3 内存接口](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html) 为准。

```bash
cat > device_floats.hpp <<'CPP'
#pragma once
#include <cuda_runtime_api.h>
#include <cstddef>
#include <cstdio>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

class DeviceFloats {
    void* pointer_ = nullptr;
    std::size_t count_ = 0;

    void cleanup() noexcept {
        const cudaError_t status = close();
        if (status != cudaSuccess)
            std::fprintf(stderr, "cudaFree failed: %s\n",
                         cudaGetErrorString(status));
    }

public:
    DeviceFloats() noexcept = default;

    explicit DeviceFloats(std::size_t count) {
        if (count > std::numeric_limits<std::size_t>::max() / sizeof(float))
            throw std::length_error("device size overflow");
        if (count == 0) return;
        void* acquired = nullptr;
        const cudaError_t status = cudaMalloc(&acquired, count * sizeof(float));
        if (status != cudaSuccess)
            throw std::runtime_error(std::string("cudaMalloc: ") +
                                     cudaGetErrorString(status));
        pointer_ = acquired;
        count_ = count;
    }

    ~DeviceFloats() noexcept { cleanup(); }
    DeviceFloats(const DeviceFloats&) = delete;
    DeviceFloats& operator=(const DeviceFloats&) = delete;

    DeviceFloats(DeviceFloats&& other) noexcept
        : pointer_(std::exchange(other.pointer_, nullptr)),
          count_(std::exchange(other.count_, 0)) {}

    DeviceFloats& operator=(DeviceFloats&& other) noexcept {
        if (this != &other) {
            cleanup();
            pointer_ = std::exchange(other.pointer_, nullptr);
            count_ = std::exchange(other.count_, 0);
        }
        return *this;
    }

    float* data() noexcept { return static_cast<float*>(pointer_); }
    const float* data() const noexcept {
        return static_cast<const float*>(pointer_);
    }
    std::size_t size() const noexcept { return count_; }

    cudaError_t close() noexcept {
        void* released = std::exchange(pointer_, nullptr);
        count_ = 0;
        return released ? cudaFree(released) : cudaSuccess;
    }
};
CPP

cat > cuda_compile_check.cpp <<'CPP'
#include "device_floats.hpp"
#include <type_traits>
static_assert(!std::is_copy_constructible_v<DeviceFloats>);
static_assert(std::is_nothrow_move_constructible_v<DeviceFloats>);
static_assert(std::is_nothrow_move_assignable_v<DeviceFloats>);
int main() {
    DeviceFloats empty;
    DeviceFloats moved(std::move(empty));
    return moved.size() != 0;
}
CPP

cat >> CMakeLists.txt <<'CMAKE'

option(COURSE03_CHECK_CUDA "Compile the CUDA host wrapper" OFF)
if(COURSE03_CHECK_CUDA)
    find_package(CUDAToolkit 13.3 REQUIRED)
    add_executable(cuda_compile_check cuda_compile_check.cpp)
    target_compile_features(cuda_compile_check PRIVATE cxx_std_17)
    target_link_libraries(cuda_compile_check PRIVATE CUDA::cudart)
endif()
CMAKE

cmake -S . -B build-cuda -DCMAKE_BUILD_TYPE=Debug \
    -DCOURSE03_CHECK_CUDA=ON
cmake --build build-cuda --target cuda_compile_check
```

**English:** These commands compile and link a host wrapper using the [CMake CUDA Toolkit imported target](https://cmake.org/cmake/help/v4.2/module/FindCUDAToolkit.html); they intentionally do not run the resulting executable or allocate device memory. The requested package version is a minimum, so record the version CMake actually finds and confirm it matches the intended 13.3 installation. No architecture setting is needed for this host-only source. A future kernel target needs its own tested architecture choice and a working runtime before any device result can be claimed.

**中文：** 这些命令通过 [CMake CUDA 工具包导入目标](https://cmake.org/cmake/help/v4.2/module/FindCUDAToolkit.html) 编译并链接主机包装器，不运行生成的程序，也不分配设备内存。所请求的包版本是最低要求，因此需要记录 CMake 实际找到的版本，并确认符合预期的 13.3 安装。这个纯主机源文件不需要设备架构设置。未来添加内核目标时，应单独选择经过验证的架构，并具备可用运行环境，之后才能报告设备结果。

**English:** To make this owner asynchronous later, introduce an explicit completion token or an owner associated with stream-ordered work. Document whether finishing a request waits, transfers a pending allocation elsewhere, or defers reclamation until an event completes. Merely adding a stream parameter to the constructor does not establish these rules. A useful review question is: if the caller immediately leaves scope after submitting work, which object now keeps the allocation alive, and which event authorizes its final release?

**中文：** 以后若要让该所有者支持异步工作，应引入明确的完成凭证，或与流顺序任务关联的所有者。需要说明请求结束时究竟是等待、把仍被使用的分配转交他处，还是等事件完成再延后释放。仅给构造函数增加流参数不能建立这些规则。审查时可以问：如果调用者提交任务后立即离开作用域，现在由哪个对象维持分配存活，最终又由哪个完成事件授权释放？

## 12. ABI and a C boundary suitable for FFI / ABI 与适合跨语言调用的 C 边界

**English:** An API describes source-level use; an ABI describes binary agreements such as symbol names, calling convention, data layout, and runtime interoperability. Two files may agree on a C++ function's name while disagreeing on the binary representation of a standard-library object. `extern "C"` requests C language linkage for the declared functions; it does not turn arbitrary C++ classes into portable C data. Keep `std::string`, vector, exceptions, and owning C++ classes behind the boundary. See the [language-linkage rules](https://eel.is/c++draft/dcl.link).

**中文：** API 描述源代码层的使用方式，ABI 描述符号名称、调用约定、数据布局和运行时互操作等二进制约定。两个文件可能认同某个 C++ 函数名称，却不认同标准库对象的二进制表示。`extern "C"` 为声明的函数请求 C 语言链接，并不会把任意 C++ 类变成可移植的 C 数据。应把字符串、向量、异常和拥有资源的 C++ 类留在边界内部。参见[语言链接规则](https://eel.is/c++draft/dcl.link)。

**English:** An opaque handle makes the representation private while exposing a small lifetime protocol: create, use, destroy. Creation returns a status and writes the handle only on success. The creator supplies the matching destroy function so memory is released by the appropriate implementation and allocator. On failure, output values must have a documented state; this example initializes the returned handle to null and sum output to zero. A Rust wrapper could place destruction in `Drop`, but would still need to enforce pointer validity, aliasing, and the C API's thread rules.

**中文：** 不透明句柄隐藏内部表示，只公开创建、使用、销毁这一小套生命周期协议。创建函数返回状态，仅在成功时写入句柄。创建方提供配对销毁函数，让正确的实现和分配器负责回收。失败时输出值必须处于已说明的状态；本例把返回句柄预置为空，把求和输出预置为零。Rust 包装可以在 `Drop` 中销毁，但仍须保证指针有效性、别名条件及 C 接口的线程约定。

```bash
cat > buffer_api.h <<'C'
#ifndef COURSE03_BUFFER_API_H
#define COURSE03_BUFFER_API_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct buffer_handle buffer_handle;
enum { BUFFER_OK = 0, BUFFER_INVALID = 1, BUFFER_FAILURE = 2 };
int buffer_create(size_t count, buffer_handle** output);
int buffer_set(buffer_handle* handle, size_t index, int value);
int buffer_sum(const buffer_handle* handle, double* output);
void buffer_destroy(buffer_handle** handle);
#ifdef __cplusplus
}
#endif
#endif
C

cat > buffer_api.cpp <<'CPP'
#include "buffer_api.h"
#include "cpu_buffer.hpp"
#include <memory>

struct buffer_handle {
    CpuBuffer buffer;
    explicit buffer_handle(std::size_t n) : buffer(n) {}
};

extern "C" int buffer_create(size_t count, buffer_handle** output) {
    if (!output) return BUFFER_INVALID;
    *output = nullptr;
    try {
        auto owner = std::make_unique<buffer_handle>(count);
        *output = owner.release();
        return BUFFER_OK;
    } catch (...) {
        return BUFFER_FAILURE;
    }
}

extern "C" int buffer_set(buffer_handle* handle, size_t index, int value) {
    if (!handle) return BUFFER_INVALID;
    try {
        handle->buffer.at(index) = value;
        return BUFFER_OK;
    } catch (const std::out_of_range&) {
        return BUFFER_INVALID;
    } catch (...) {
        return BUFFER_FAILURE;
    }
}

extern "C" int buffer_sum(const buffer_handle* handle, double* output) {
    if (!output) return BUFFER_INVALID;
    *output = 0.0;
    if (!handle) return BUFFER_INVALID;
    try {
        double result = 0.0;
        for (std::size_t i = 0; i < handle->buffer.size(); ++i)
            result += handle->buffer.at(i);
        *output = result;
        return BUFFER_OK;
    } catch (...) {
        return BUFFER_FAILURE;
    }
}

extern "C" void buffer_destroy(buffer_handle** handle) {
    if (!handle) return;
    delete *handle;
    *handle = nullptr;
}
CPP

cat > ffi_client.c <<'C'
#include "buffer_api.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    buffer_handle* handle = NULL;
    assert(buffer_create(3, &handle) == BUFFER_OK);
    assert(buffer_set(handle, 0, 10) == BUFFER_OK);
    assert(buffer_set(handle, 1, 20) == BUFFER_OK);
    assert(buffer_set(handle, 2, 30) == BUFFER_OK);
    assert(buffer_set(handle, 99, 40) == BUFFER_INVALID);
    double result = 0;
    assert(buffer_sum(handle, &result) == BUFFER_OK);
    assert(result == 60);
    buffer_destroy(&handle);
    assert(handle == NULL);
    buffer_destroy(&handle);
    assert(buffer_sum(NULL, &result) == BUFFER_INVALID);
    assert(result == 0);
    puts("C ABI: sum=60, invalid index handled, handle cleared");
    return 0;
}
C

cat >> CMakeLists.txt <<'CMAKE'

add_library(buffer_api STATIC buffer_api.cpp)
target_compile_features(buffer_api PRIVATE cxx_std_20)
target_include_directories(buffer_api PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
add_executable(ffi_client ffi_client.c)
target_link_libraries(ffi_client PRIVATE buffer_api)
set_target_properties(ffi_client PROPERTIES LINKER_LANGUAGE CXX)
add_test(NAME c_abi_client COMMAND ffi_client)
CMAKE

cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
./build/ffi_client

gcc -std=c11 -Wall -Wextra -Wpedantic -c ffi_client.c -o ffi_client.o
if g++ ffi_client.o -o missing_library; then
    printf '%s\n' 'ERROR: missing implementation unexpectedly linked'
    exit 1
else
    printf '%s\n' 'Expected: link needs the implementation library'
fi
g++ ffi_client.o build/libbuffer_api.a -o ffi_manual
./ffi_manual
nm -g --defined-only build/libbuffer_api.a
```

**English:** The source ending in `.c` is compiled as C, which verifies that the header does not accidentally require C++ syntax. The final link uses the C++ driver because the implementation needs the C++ runtime. The intentional missing-library link demonstrates that a correct declaration is not an implementation. `nm` should show exported names such as `buffer_create` without C++ name mangling; other implementation symbols can still appear in the archive. This experiment tests one local compiler/runtime combination, not universal ABI compatibility.

**中文：** 以 `.c` 结尾的文件按照 C 编译，这能够验证头文件没有意外依赖 C++ 语法。最终链接使用 C++ 驱动，因为实现需要 C++ 运行库。故意缺少实现库的链接步骤说明，正确声明不等于已经提供实现。符号工具应显示没有 C++ 名字修饰的导出名称，例如 `buffer_create`，而静态库仍可能包含其他实现符号。本实验只验证本地这一组编译器与运行库，不代表所有平台的 ABI 都兼容。

**English:** The null checks do not validate arbitrary non-null addresses. Callers must pass live handles created by this library and valid writable output pointers; destruction invalidates all aliases, even if one variable is cleared. Concurrent mutation is unsupported in this teaching API. Exceptions are translated into statuses inside the implementation, and its destructor path is non-throwing. Extending the API requires stable status meanings and a versioning plan. Adding a field to a private handle is easier than changing an exposed structure consumed by separately compiled clients.

**中文：** 空值检查不能验证任意非空地址。调用者必须传入本库创建且仍然存活的句柄，以及有效可写的输出指针；销毁会使所有别名失效，即使只清空了其中一个变量。本教学接口不支持并发修改。实现内部把异常转成状态，析构路径也不抛异常。扩展接口时，需要保持状态含义稳定并制定版本策略。给私有句柄增加字段，比修改已被独立编译调用者使用的公开结构更容易维护。

**English:** For a future Rust binding, an opaque non-null handle can sit inside an owning wrapper, and borrowed methods can expose only operations justified by the C contract. Do not automatically mark the wrapper `Send` or `Sync`; device affinity, internal state, and synchronization requirements determine those traits. Likewise, a C++ `noexcept` annotation alone would not make a foreign call safe. The boundary needs a complete agreement about allocation, release, failure, thread use, and completion before either language can present a safe higher-level abstraction.

**中文：** 未来接入 Rust 时，可以把不透明非空句柄放进拥有资源的包装器，再通过借用方法只公开 C 契约允许的操作。不要自动给包装器实现 `Send` 或 `Sync`，设备亲和性、内部状态和同步条件共同决定这些性质。同样，单独添加 C++ 不抛异常标记也不能让外部调用自动安全。双方必须就分配、释放、失败、线程使用与操作完成形成完整约定，之后任何一方才能提供安全的高层抽象。

## 13. Ten exercises with reference solutions / 十道练习与参考解答

### Exercise 1: Separate the owner and the view / 练习一：区分所有者与视图

**English:** Exercise: A function receives `float* data` and an element count, reads every element synchronously, and retains nothing. Does receiving the pointer transfer ownership? Choose an alternative C++ interface and state the conditions that the caller still must satisfy.

**中文：** 练习：函数接收浮点指针和元素数量，同步读取全部元素且不保留任何信息。收到指针是否表示接收所有权？请选择一种替代 C++ 接口，并说明调用者仍需满足哪些条件。

**English:** Reference solution: No ownership transfer follows from copying a pointer. `std::span<const float>` expresses a read-only borrowed sequence and carries its length. The caller must provide live, accessible elements for the entire call, and prevent conflicting concurrent modification. If the pointer denotes ordinary device-only storage, replacing its type with a span does not make CPU reads legal. An interface contract must state address space as well as lifetime; the convenient container view addresses only part of the problem.

**中文：** 参考解答：复制指针不意味着移交所有权。`std::span<const float>` 能表达只读借用序列，并携带长度。调用者必须让元素在整个调用期间存活且可访问，同时避免冲突的并发修改。如果指针表示普通的设备专用存储，把类型换成切片视图也不会让 CPU 读取合法。接口契约必须同时说明地址空间与生命周期，方便的容器视图只解决其中一部分问题，不能替代这些前提。

### Exercise 2: Diagnose vector invalidation / 练习二：诊断向量地址失效

**English:** Exercise: A program saves `auto p = values.data()`, then appends enough elements to exceed the vector's capacity. The vector itself still exists. Can the old pointer be used, and would calling `reserve` once make this design permanently safe?

**中文：** 练习：程序保存向量的数据指针，随后追加足够多的元素使数量超过容量。向量对象本身仍然存在。旧指针还能使用吗？提前调用一次预留容量，是否让这个设计永久安全？

**English:** Reference solution: Reallocation invalidates the old element pointer even though the vector object survives. Reserving enough capacity protects against those reallocations only while future operations remain within the applicable conditions. It does not protect against destruction, replacement, or later growth beyond capacity. Obtain the pointer after the relevant structural changes and bound its use. If a worker retains the view, the owner must prohibit invalidating changes until that worker completes, rather than relying on a large guessed reserve value.

**中文：** 参考解答：重新分配会使旧元素指针失效，即使向量对象还存在。预留足够容量只能在后续操作继续满足相关条件时避免这类重新分配，不能防止析构、替换或再次超容量增长。应在相关结构修改完成之后获取指针，并限制使用区间。如果工作线程保留视图，所有者必须在线程完成之前禁止导致失效的修改，而不是靠猜测一个很大的容量，把正确性建立在暂时没有超过它之上。

### Exercise 3: Repair a shallow-copy owner / 练习三：修复浅拷贝所有者

**English:** Exercise: A class contains an owning raw array pointer and a destructor calling `delete[]`, but declares no copy operations. Explain what `Buffer b = a` can do and propose two legitimate ownership designs without running the broken program.

**中文：** 练习：类包含拥有数组的裸指针，析构函数负责数组删除，但没有声明复制操作。请解释复制初始化可能造成什么问题，并在不运行错误程序的前提下提出两种合理设计。

**English:** Reference solution: Memberwise copying duplicates the address, leaving two apparent owners and a later double deletion. One design deletes copy construction and assignment, then implements safe movement. Another implements independent deep copying, including allocation failure handling. Shared ownership is a separate explicit option, not a property of duplicated raw pointers. In application code, replacing the member with vector often supplies the desired deep-copy semantics with the Rule of Zero and reduces the amount of custom code requiring review.

**中文：** 参考解答：逐成员复制会复制地址，留下两个看似拥有资源的对象，之后可能重复删除。一种设计删除复制构造与复制赋值，再实现安全移动；另一种实现独立深拷贝，并处理分配失败。共享所有权也是单独的明确选项，不是复制裸指针自动带来的性质。在应用代码中，把成员改为向量，常能通过零法则直接得到需要的深拷贝语义，并减少必须审查的手写资源管理代码。

### Exercise 4: Explain what move actually selects / 练习四：解释移动究竟选择了什么

**English:** Exercise: Consider a const vector passed to `std::move` when constructing another vector. Why might copying occur? Does the presence of an rvalue-reference type prove that no allocation happens or that the source is empty afterward?

**中文：** 练习：把一个常量向量传给 `std::move`，再用于构造另一个向量，为什么可能发生复制？出现右值引用类型，能否证明没有分配，或者证明来源之后必定为空？

**English:** Reference solution: The cast preserves constness, while the usual move constructor needs a non-const rvalue reference so it can modify the source's ownership state. A compatible const-reference copy constructor may therefore be selected. More generally, a move operation's cost and postconditions depend on the type, allocator, and selected overload. Our buffer explicitly promises an empty source and pointer transfer; that promise comes from its implementation and contract, not from the spelling of `std::move` alone. Follow overload selection through to the actual operation when analyzing the result.

**中文：** 参考解答：转换保留常量性，而通常的移动构造需要非常量右值引用，才能修改来源的所有权状态。因此可能选择接受常量引用的复制构造。更一般地说，移动操作的成本与后置条件由类型、分配器以及选中的重载决定。本课缓冲区明确承诺来源变空并转移指针，这个承诺来自具体实现和契约，不是 `std::move` 的写法单独保证。分析时应沿重载选择继续追踪实际行为。

### Exercise 5: Account for move assignment / 练习五：计算移动赋值的资源责任

**English:** Exercise: Owner A holds allocation X, and owner B holds allocation Y. After `B = std::move(A)`, which allocation must be released immediately, who owns the survivor, and what should self move assignment do in the implementation supplied here?

**中文：** 练习：所有者甲持有分配甲，所有者乙持有分配乙。将甲移动赋值给乙之后，哪块分配应立即释放，谁拥有剩余分配？本课实现应怎样处理自移动赋值？

**English:** Reference solution: B must discharge its old obligation for Y before taking X, after which B owns X and A has the documented empty state. Forgetting Y leaks it; failing to empty A creates duplicate ownership. The explicit identity check makes self move assignment leave the object unchanged. Other designs can define other valid behavior, but this implementation's behavior is precise and testable. Count releases by allocations, not by the number of wrapper objects whose destructors execute.

**中文：** 参考解答：乙接收甲的分配之前，必须先履行释放自己旧分配的责任，之后乙拥有原来的甲分配，甲进入约定的空状态。忘记处理乙的旧资源会泄漏，没有清空甲则会制造重复所有权。显式身份检查让本课自移动赋值保持对象不变。其他设计可以规定别的有效行为，但本实现的行为明确且可测试。统计释放次数应针对分配，而不是只数执行过多少个包装对象析构函数。

### Exercise 6: Distinguish failed construction from destruction / 练习六：区分构造失败与完整对象析构

**English:** Exercise: A class finishes constructing its resource member, then throws from its constructor body. Which destructor runs? How does that answer change if the member is merely a raw pointer obtained before the throwing operation?

**中文：** 练习：类先完成资源成员构造，随后在构造函数体内抛出异常。哪个析构函数会执行？如果成员仅仅是抛出操作之前取得的裸指针，答案有什么变化？

**English:** Reference solution: The completed owning member is destroyed during unwinding, while the incomplete containing object's destructor does not run. A raw pointer member contributes no resource release by itself. Consequently, placing cleanup only in the outer destructor cannot protect acquisitions made before its construction succeeds. Store the resource in a fully constructed owner before additional work can fail, or use a local owner whose lifetime covers the vulnerable setup interval. The experiment's zero outer-destructor count and unchanged live-allocation count demonstrate both parts.

**中文：** 参考解答：已经完成的资源所有者成员在展开时析构，未完成的外层对象不会执行自己的析构。裸指针成员自身没有资源释放行为，因此仅把清理放在外层析构里，不能保护其成功构造之前获取的资源。应在其他工作可能失败前，把资源存进已经完成构造的所有者，或者用局部所有者覆盖这段脆弱的设置区间。实验中外层析构计数为零且存活分配数量不变，分别验证了这两个结论。

### Exercise 7: Establish a strong exception guarantee / 练习七：建立强异常保证

**English:** Exercise: Compare freeing the old allocation before acquiring a replacement with preparing a replacement and then swapping. Which can preserve the original value if allocation or preparation fails? Identify the commit operation and explain why its exception behavior matters.

**中文：** 练习：比较先释放旧分配再获取新分配，以及先准备新分配再交换这两种实现。哪一种能在分配或准备失败时保留原值？请指出提交操作，并解释它的异常行为为什么重要。

**English:** Reference solution: Preparing a replacement keeps the original untouched through all fallible work. A non-throwing swap commits the result; the temporary then releases the old allocation. Freeing first has already lost the old value before a replacement failure occurs and therefore cannot provide the same unchanged-state guarantee. This reasoning assumes all other observable preparation effects are also controlled. Writing to a file or modifying a shared external object during preparation would require its own rollback or a weaker documented guarantee.

**中文：** 参考解答：先准备替代资源，能让原对象在全部可能失败的工作期间保持不动，再由不抛异常的交换提交，临时对象负责释放旧分配。先释放旧资源的方案在替代失败之前已经丢失原值，因而无法提供相同的不变状态保证。这个推理还要求准备阶段其他可观察副作用同样受控。如果准备过程写入文件或修改外部共享对象，就需要单独回滚，或者明确承诺较弱的保证，不能把局部交换当作万能事务。

### Exercise 8: Separate shared lifetime from synchronization / 练习八：区分共享生命周期与同步

**English:** Exercise: Two threads hold separate `shared_ptr` objects referring to the same vector and both append elements. Does reference counting make those mutations safe? How would you decide between a lock, partitioned ownership, and immutable sharing?

**中文：** 练习：两个线程各持有共享指针，指向同一向量，并且都向其追加元素。引用计数能让修改安全吗？你会怎样在锁、分区所有权与只读共享之间选择？

**English:** Reference solution: Shared ownership keeps the pointee alive but does not serialize vector mutation. A lock can protect a genuinely shared mutable container; disjoint ownership is appropriate when work can use independently owned regions without structural changes; immutable sharing works when all consumers only read. Decide from access patterns rather than pointer convenience. In particular, separate logical indices do not automatically make concurrent `push_back` safe because each call also changes shared size, capacity, and potentially the storage itself.

**中文：** 参考解答：共享所有权保证被指向对象存活，不会把向量修改串行化。真正共享可变容器时可以加锁；任务能处理各自独占区域且不修改整体结构时可以分区；所有使用者只读时适合不可变共享。选择依据应是访问模式，而不是哪种指针方便。特别要注意，逻辑下标不同也不能自动让并发追加安全，因为每次追加还会修改共同的长度、容量，甚至替换整个底层存储。

### Exercise 9: Locate a build failure / 练习九：定位构建失败阶段

**English:** Exercise: A caller includes a correct declaration, compiles into an object file, but final linking reports an undefined reference. Name two plausible causes involving an ordinary function or a template. Would changing a GPU driver be a relevant repair?

**中文：** 练习：调用者包含正确声明并成功生成目标文件，但最后链接报告未定义引用。请分别给出普通函数与模板场景中的可能原因。修改 GPU 驱动是否是相关修复方式？

**English:** Reference solution: An ordinary function's implementation object or library may be absent from the link. A template definition may be hidden without supplying the required explicit instantiation. In either case, inspect target dependencies, compiled definitions, and symbol names; also consider a mismatched signature or language linkage. A GPU driver cannot provide a missing host implementation. The intentionally failed manual link becomes successful when the correct static library is added, illustrating a targeted stage-specific repair rather than a broad environment change.

**中文：** 参考解答：普通函数可能缺少参与链接的实现目标文件或库；模板可能把定义藏在源文件中，却没有提供所需显式实例化。两者都应检查目标依赖、已编译定义和符号名称，也要考虑签名或语言链接不一致。GPU 驱动不能补出缺失的主机实现。实验中手动链接故意失败，补上正确静态库后成功，展示的是针对失败阶段的修复，而不是大范围改动环境，希望问题偶然消失。

### Exercise 10: Review an asynchronous foreign call / 练习十：审查异步跨语言调用

**English:** Exercise: A Rust caller obtains a C handle, submits GPU work through it, and immediately drops the handle. The C++ wrapper has a destructor and all exposed functions use C linkage. Are those facts enough for safety? List the remaining obligations and the evidence missing from this course's CUDA check.

**中文：** 练习：Rust 调用者获得 C 句柄，通过它提交 GPU 工作，然后立即销毁句柄。C++ 包装器有析构函数，所有公开函数也采用 C 链接。这是否足够安全？请列出剩余责任，以及本课 CUDA 检查尚未提供的证据。

**English:** Reference solution: The design still needs a completion protocol so destruction cannot reclaim storage that queued work will use. It needs device/context rules, valid pointers, matched destruction, aliasing and thread restrictions, and error translation that prevents exceptions from crossing the boundary. C linkage addresses binary naming conventions, not these obligations. Our CUDA target was compiled and linked only; device allocation, actual completion, error behavior on a running GPU, and performance remain unverified. A safe binding cannot infer those properties from successful compilation.

**中文：** 参考解答：设计仍然需要完成协议，防止销毁回收排队任务还要使用的存储；还需要设备与上下文规则、有效指针、配对销毁、别名和线程限制，以及阻止异常穿越边界的错误转换。C 链接处理二进制链接约定，不负责这些资源责任。本课 CUDA 目标只完成编译与链接，设备分配、真实完成时机、运行中 GPU 的错误行为及性能仍未验证。安全绑定不能从编译成功推断这些性质。

## 14. Acceptance, conclusions, and next steps / 验收、总结与下一步

**English:** The local verification completed the CPU ownership experiment, its AddressSanitizer/UndefinedBehaviorSanitizer run, the expected rejected copy, both CTest cases, the C-compiled client, the expected missing-library link failure, and the corrected manual link. CUDA 13.3.73 headers and runtime supported compilation and linkage of the host allocation wrapper. No GPU program was executed, no device allocation was tested, and no driver was changed. The reproducible blocks provide evidence for these narrow claims without presenting compilation as a performance result.

**中文：** 本地验证完成 CPU 所有权实验、地址与未定义行为检测器运行、预期被拒绝的复制、两个 CTest 案例、按 C 编译的调用者、预期缺库链接失败，以及补库后的手动链接。CUDA 13.3.73 头文件和运行库支持主机分配包装器编译链接。没有执行 GPU 程序，没有测试设备分配，也没有修改驱动。可复制代码块为这些范围明确的结论提供证据，不会把编译成功描述成性能结果。

**English:** Completion means you can explain every ownership transition without relying on the printed output first. Identify the invariant before and after a move; state the last permitted use of a borrowed view; distinguish incomplete construction from complete-object destruction; and explain which failure leaves the old value unchanged. You should also be able to reproduce a link failure and repair its actual dependency, then describe the C boundary's lifetime protocol in ordinary language. Memorizing the five special-member signatures without these explanations does not meet the learning goal.

**中文：** 完成本课意味着不先依赖打印结果，也能解释每次所有权转换：指出移动前后的不变量，说明借用视图最后允许使用的时刻，区分构造未完成和完整对象析构，并解释哪种失败保持原值。还应能复现链接失败、修复真正缺失的依赖，再用普通语言描述 C 边界的生命周期协议。仅背下五个特殊成员函数的签名，却无法解释这些行为，仍不满足本课学习目标。

**English:** The next practical step is to reuse this reasoning in a small CUDA vector-add project once device execution is available: an owner for allocations, views for kernel arguments, explicit completion before host validation, and matched cleanup on every failure path. Measure correctness before speed, then examine transfer and launch overhead separately from kernel time. Rust can later wrap the same C interface or manage analogous ownership directly. The transferable skill is making resource and completion contracts precise enough that a compiler, a test, and another engineer can all check them.

**中文：** 下一步是在设备可执行之后，把这套推理用于小型向量加法工程：分配由所有者管理，内核参数使用视图，主机验证之前明确等待完成，各失败路径正确配对清理。先验证正确性，再测速度，并把传输、启动开销与内核耗时分别分析。之后可以让 Rust 包装同一个 C 接口，或直接管理类似所有权。真正可迁移的能力，是把资源与完成契约写得足够明确，让编译器、测试和其他工程师都能检查。

## Official and standards references / 官方与标准参考资料

**English:** Checked on 2026-09-18. The language sources are the public C++ working draft and the C++ Core Guidelines; the draft is a living specification, so these links support the foundational rules rather than asserting that every current draft feature belongs to C++20. Examples and experiments in this chapter are original. CUDA references are pinned to 13.3, and CMake references use the 4.2 documentation family; installed patch versions are recorded above.

**中文：** 核验日期为 2026 年 9 月 18 日。语言资料来自公开 C++ 工作草案与核心指南；草案持续更新，因此这些链接用于核实基础规则，不表示当前草案的每项新特性都属于 C++20。本章案例与实验为原创。CUDA 资料固定到 13.3，CMake 资料采用 4.2 文档系列，已安装的具体补丁版本在前文单独记录。

- [C++ lifetime rules / C++ 生命周期规则](https://eel.is/c++draft/basic.life)
- [Copy and move constructors / 复制与移动构造](https://eel.is/c++draft/class.copy.ctor)
- [Construction and exceptions / 构造与异常](https://eel.is/c++draft/except.ctor)
- [Unique ownership / 独占所有权](https://eel.is/c++draft/unique.ptr)
- [Shared ownership / 共享所有权](https://eel.is/c++draft/util.smartptr.shared)
- [Template instantiation / 模板实例化](https://eel.is/c++draft/temp.inst)
- [Language linkage / 语言链接](https://eel.is/c++draft/dcl.link)
- [C++ Core Guidelines: RAII / C++ 核心指南：RAII](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rr-raii)
- [CMake target dependencies / CMake 目标依赖](https://cmake.org/cmake/help/v4.2/command/target_link_libraries.html)
- [CMake CUDA Toolkit integration / CMake CUDA 工具包集成](https://cmake.org/cmake/help/v4.2/module/FindCUDAToolkit.html)
- [CUDA 13.3 compiler driver / CUDA 13.3 编译驱动](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-compiler-driver-nvcc/index.html)
- [CUDA 13.3 memory API / CUDA 13.3 内存接口](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-runtime-api/group__CUDART__MEMORY.html)
- [CUDA 13.3 Linux environment / CUDA 13.3 Linux 环境](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html)
