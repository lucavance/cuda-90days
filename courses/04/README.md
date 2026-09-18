# Rust Systems and Concurrent Programming / Rust 系统与并发编程

## 1. Outcomes and Evidence / 学习目标与证据

**English:** This course develops a way to reason about resource ownership while requests move through a concurrent inference service. You will distinguish ownership from access permission, choose between borrowed work and independently owned tasks, and explain what a timeout actually cancels. The goal is to justify a design with lifetimes, state transitions, and observable behavior. Recognizing the names of smart pointers is insufficient: you should be able to explain which component can still access a buffer at every transition. Explain both who can access the buffer and why that access remains valid during reception, queueing, execution, return, and failure.

**中文：** 本课建立一种分析方法：当请求在并发推理服务中流动时，如何持续判断资源属于谁。你将区分所有权与访问权限，选择借用执行还是独立持有数据的任务，并解释超时究竟取消了什么。学习目标是通过生命周期、状态转换和可观察行为说明设计依据。仅仅认识智能指针名称并不够；面对接收、排队、执行、返回和失败，你应能逐步指出哪个组件仍然可以访问缓冲区，以及该访问为什么有效。

**English:** The prerequisite is ordinary systems programming, not prior GPU expertise. Courses 01 and 03 provide useful comparisons with processes and C++ resource ownership. This lesson owns the material from Days 017, 033, 037, 041, and 042. Course 07 develops the CUDA-specific foreign-function and device-lifetime implications; here, an in-flight operation is primarily a CPU service operation. A CPU concurrency exercise must never be presented as a GPU throughput measurement. These exercises can validate tasks, queues, and resource states; simulated waiting time is not model inference time.

**中文：** 本课要求具备一般系统编程经验，不要求已经熟悉 GPU。课程 01 和 03 可作为进程与 C++ 资源所有权的对照。本课主讲 Day017、Day033、Day037、Day041 和 Day042 的知识；CUDA 专属的外部函数与设备生命周期问题在课程 07 深入。这里处于执行中的操作主要指 CPU 服务操作。CPU 并发实验可以验证任务、队列和资源状态，却不能据此声称获得了 GPU 吞吐量，也不能将模拟等待时间当作模型推理时间。

**English:** Sources were checked on 2026-09-18. The locally available compiler reports `rustc 1.100.0-nightly (330d31712 2026-09-17)`. Examples use edition 2024 and stable language constructs; this observation does not imply that nightly is required for ordinary service code. The standard-library program is dependency-free. The optional Tokio program uses an exact dependency in its manifest, so its API assumptions are reviewable instead of silently following every future release. Version selection supports reproduction; a newer version number is not itself evidence of correctness or performance.

**中文：** 资料核验日期为 2026-09-18。本机编译器报告为 `rustc 1.100.0-nightly (330d31712 2026-09-17)`。示例使用 2024 edition 和稳定语言功能，这一环境记录不代表普通服务代码必须使用 nightly。标准库实验没有外部依赖；可选 Tokio 实验通过清单中的精确依赖版本表明接口假设，避免教学代码悄然跟随未来所有发布版本。选择版本的目的在于复现，不能把较新的版本号本身当成正确性或性能证据。

## 2. Ownership Describes Responsibility / 所有权描述责任

**English:** Consider a request containing a `Vec<u8>`. The vector owns its allocation, while the request owns the vector. Moving the request into a queue transfers the ability and responsibility to destroy that allocation through the new owner. A move is a semantic transfer; it does not promise either a heap copy or zero machine instructions. In particular, moving a vector normally transfers its small descriptor without duplicating its elements. Do not infer a network send, device copy, or allocation merely from the word move.

**中文：** 设想一个请求包含 `Vec<u8>`：向量拥有其分配的存储，请求又拥有这个向量。将请求移动到队列，转交的是经由新所有者访问和最终销毁该存储的能力与责任。移动是一种语义转移，它既不承诺复制堆内存，也不承诺完全没有机器指令。移动向量通常传递较小的描述信息，而不会逐个复制元素。因此，不能只看到 move 就推断发生了网络发送、设备拷贝或新分配；这些是需要单独考察的操作。

**English:** Assignment behaves differently for `Copy` types. Copying a `usize` leaves both bindings usable because the type permits an implicit duplicate. A `Vec<T>` is not `Copy`, even when `T` is. Its explicit `clone` usually allocates storage and clones elements. An `Arc<T>` clone instead creates another owner of one allocation. These three operations can look similarly compact in source while having very different cost and lifetime effects. Explain the concrete type before discussing the performance of copying. Keep shallow copies, deep copies, and shared ownership distinct.

**中文：** 对于实现 `Copy` 的类型，赋值表现不同。复制一个 `usize` 后，两个绑定仍然可以使用，因为类型允许隐式产生副本。即使元素类型实现了 `Copy`，`Vec<T>` 本身也不是 `Copy`，其显式 `clone` 通常会分配存储并克隆元素。`Arc<T>` 的克隆则为同一份分配增加一个所有者。这三类操作在源代码中都可能只有一行，但成本与生命周期影响完全不同。讨论复制性能以前，必须先说明具体类型，不能把浅复制、深复制和共享所有权混为一谈。

**English:** A function taking `Request` consumes its argument unless the type is copied. A function taking `&Request` receives temporary read access without becoming responsible for destruction. Taking `&mut Request` provides exclusive access for a borrow, not permanent ownership. Design these signatures around the workflow: a validator usually borrows, an enqueue operation usually consumes, and a transformation may consume one request and return a new value. A signature that expresses the transition is easier to review than a comment saying that callers must stop using a value. Such a signature also lets the compiler identify calls that violate the transition.

**中文：** 接收 `Request` 的函数通常消费实参，除非该类型允许复制；接收 `&Request` 的函数得到临时读取权限，不承担销毁责任；接收 `&mut Request` 则在借用期间拥有排他访问权限，而非永久所有权。接口应围绕工作流设计：校验器通常借用，入队操作通常消费，转换操作可以消费旧值并返回新值。能够在签名中表达的状态变化，比注释要求调用方“之后别再用这个对象”更容易审查，也更能让编译器帮助发现违反约定的调用。

**English:** Returning an owned value is often the simplest way to return responsibility. A worker can consume a vector, update it, and return it through a join handle or reply channel. Waiting for the worker does not undo the move. The original binding remains moved; the returned value must be bound again. This is especially useful for reusable buffers: the protocol can explicitly return a buffer to its pool after processing, instead of sharing mutation of every buffer with every component. When reusing storage, distinguish retained capacity from logical contents; whether old contents must be cleared depends on the application.

**中文：** 返回一个拥有所有权的值，往往是交还责任最直接的方法。工作线程可以消费向量、修改它，再经由线程句柄或回复通道返回。等待线程完成并不会撤销此前的移动，原绑定仍然已经被移走，返回值必须重新绑定。这种方式适合可复用缓冲区：协议可以在处理完毕后明确将缓冲区交回池中，而不必让每个组件都共享所有缓冲区的修改权限。讨论复用时还应区分容量保留与逻辑内容，旧内容是否需要清零取决于实际业务约束。

**English:** `Drop` connects scope exit with cleanup, but cleanup is not a universal completion signal. A dropped file owner can close a file descriptor; dropping a request may release memory. Neither action proves that another process committed a transaction or that an asynchronous device operation finished. Likewise, a process abort may skip destructors. Use `Drop` for local resource ownership and an explicit protocol for operations whose completion must be acknowledged. If errors during cleanup matter, offer an explicit fallible `close` or `finish` operation before best-effort destruction.

**中文：** `Drop` 将离开作用域与清理联系起来，但清理并不是通用的完成信号。文件所有者被销毁可以关闭文件描述符，请求被销毁可以释放内存；这些动作都不能证明另一进程已经提交事务，也不能证明异步设备操作已经结束。另外，进程直接终止可能跳过析构。应当用 `Drop` 管理本地资源，用明确的协议确认需要对方承认的操作完成。如果清理阶段的错误会影响业务，就提供可返回错误的 `close` 或 `finish`，然后让析构只负责尽力收尾。

## 3. Borrowing Defines Access Windows / 借用定义访问窗口

**English:** A borrow is a relationship between a referent and an interval during which access is permitted. Shared borrows allow observations compatible with the type's rules. An exclusive borrow prevents conflicting access through ordinary safe references during its active use. The rules concern aliasing and access, not simply whether a variable was declared `mut`. Interior-mutability types provide specific checked or synchronized exceptions to the default access pattern; they do not make all simultaneous mutation valid. For a compiler error, first map the overlapping references and their last uses, then decide whether to shorten a borrow, split the data, or change the interface instead of bypassing checks.

**中文：** 借用描述被引用对象与允许访问的时间区间之间的关系。共享借用允许符合类型规则的观察；排他借用则在有效使用期间阻止普通安全引用发生冲突访问。规则关心的是别名与访问行为，而不只是变量声明时有没有写 `mut`。内部可变性类型通过动态检查或同步提供特定机制，并不意味着所有并发修改都变得合法。面对编译错误，应先画出同时存在的引用和最后使用位置，再决定是缩短借用、拆分数据还是调整接口，而不是首先寻找绕开检查的方法。

**English:** Non-lexical lifetimes often allow a borrow to end at its last use instead of the end of the surrounding block. A resource-owning guard is a different matter: its destructor may still run at the lexical drop point. Therefore a mutex guard that is no longer read can still hold the mutex. A small block or explicit `drop(guard)` documents the unlock point. This distinction explains why a program can satisfy borrow checking while still holding a lock across far too much work. The compiler checks whether access is legal; it does not choose an appropriate critical-section size.

**中文：** 非词法生命周期经常允许借用在最后一次使用后结束，而不必延续到外围代码块末尾。但拥有资源的 guard 是另一回事，其析构仍可能发生在词法上的销毁位置。因此，一个不再被读取的互斥锁 guard 仍可能持有锁。使用较小代码块或显式 `drop(guard)`，可以清楚地表达解锁位置。这个区别解释了为什么程序虽然通过借用检查，仍然可能把锁持有得过久：编译器确认访问是否合法，并没有替你决定合理的临界区大小。

**English:** Lifetimes in signatures describe relationships; they do not extend storage duration. A function cannot return a reference to a local vector by adding a lifetime parameter. If the result must outlive the call, return an owned value, borrow from an input whose lifetime supports the result, or store the value in an owner that actually survives. Treat a lifetime annotation as a statement to prove about existing storage rather than a request to keep dead storage alive. The same reasoning applies to foreign-library callbacks: how long a callback is retained determines which data it can safely borrow.

**中文：** 签名中的生命周期描述关系，不会延长存储本身的寿命。给函数增加生命周期参数，不能让它返回对局部向量的有效引用。如果结果必须在调用结束后继续存在，就返回拥有所有权的值，从寿命足够长的输入借用，或者把值存入确实存活的所有者。应当把生命周期标注看成对现有存储关系提出的证明要求，而不是要求已经销毁的存储继续存在。这个判断也适用于外部库回调：回调被保存多久，决定了它能安全借用哪些数据。

**English:** `T: 'static` means the value contains no borrowed references that require a shorter lifetime, subject to the type system's treatment of the type. It does not mean the value must live forever. An owned string can meet a `'static` bound and be destroyed milliseconds later. By contrast, `&'static str` is a reference whose referent is valid for that lifetime. Mixing up these meanings often causes needless leaks or global variables when a moved, owned request would satisfy a task API. When a task API requires `'static`, first inspect the borrows contained in its captured values.

**中文：** `T: 'static` 表示该值不包含必须依赖更短生命周期的借用引用，具体约束由类型系统检查；它并不是说这个值必须永远活着。拥有数据的字符串可以满足 `'static` 约束，又在几毫秒后被正常销毁。与之不同，`&'static str` 本身是一个指向具有相应有效期对象的引用。混淆这两种含义，容易让人在本来只需要移动一个请求时，引入不必要的内存泄漏或全局变量。看到任务接口要求 `'static`，应先检查捕获值里究竟包含哪些借用。

**English:** Slices let an algorithm operate on a view instead of owning a particular container. A `&[T]` describes a contiguous sequence without promising that the source is a vector. A `&mut [T]` adds exclusive access to the represented region. Safe APIs such as `split_at_mut` or `chunks_mut` can establish that mutable regions do not overlap. Parallel processing can then use the disjointness proof instead of protecting the entire array with a mutex. The proof is about element regions; output ordering and error aggregation still require design. Task count and load balancing also need independent design; absence of data races does not establish correctness of the whole algorithm.

**中文：** 切片让算法操作一个视图，而不必拥有特定容器。`&[T]` 表示连续元素序列，不要求来源一定是向量；`&mut [T]` 进一步提供对所表示区域的排他访问。`split_at_mut`、`chunks_mut` 等安全接口可以建立可变区域互不重叠的关系。并行处理于是能够依赖这种不重叠保证，而不需要用一把互斥锁保护整个数组。但证明仅涉及元素区域，输出顺序、失败汇总、任务数量和负载均衡仍然需要独立设计，不能因为没有数据竞争就认为完整算法已经正确。

**English:** Choose an owned or borrowed interface according to retention. A synchronous checksum function can accept a slice because it finishes before returning. A queue that retains work after the caller returns usually needs owned bytes or another durable owner. Converting every slice to a vector is simple but can add unnecessary allocation; retaining a borrowed slice without a lifetime guarantee is invalid. The useful design question is who keeps the bytes alive while the consumer is entitled to use them. Also specify how that responsibility transfers during failure and cancellation.

**中文：** 接口应根据是否保留数据来选择所有权或借用。同步校验和函数在返回前完成计算，因此可以接收切片；在调用者返回后仍然保留任务的队列，通常需要拥有字节数据或另一个持久所有者。把所有切片都转换为向量虽然简单，却可能增加不必要的分配；在没有生命周期保证时保存借用切片则不合法。真正有用的设计问题是：消费者仍有权使用这些字节的整个时间里，由谁负责保持它们存活，以及该责任在失败和取消时如何转移。

## 4. Choose the Smallest Ownership Mechanism / 选择足够且最小的所有权机制

**English:** `Box<T>` provides an owning indirection. It is useful when a recursive representation needs a fixed-size link, when a trait object provides dynamic dispatch, or when an allocation must have one clearly identified owner. It does not intrinsically create shared ownership or thread synchronization. Moving a box transfers its ownership; it does not change the fact that the allocation needs a valid owner until the last authorized access. Start with a plain value, then introduce a box only when the representation or API requires it. Large data alone is not a reason to add indirection at every layer, and indirection does not establish sharing.

**中文：** `Box<T>` 提供拥有所有权的间接访问。当递归结构需要固定大小的链接、trait 对象需要动态分发，或者某个分配应有一个明确所有者时，它很有用。但它本身不会产生共享所有权，也不会提供线程同步。移动 box 只是转移所有权，最后一次合法访问以前仍须有有效所有者维持分配。设计时可以先使用普通值，再根据表示方式或接口需要引入 box；不要因为数据可能较大就默认所有层都加一层指针，也不要把地址间接性误认为共享机制。

**English:** `Rc<T>` shares ownership within a single-threaded setting using a non-atomic reference count. `Arc<T>` uses an atomic reference count and can support cross-thread sharing when its inner type meets the necessary trait bounds. Neither pointer automatically grants mutable access to `T`. A read-only configuration can often be an `Arc<Config>`, while mutable state needs a separate access mechanism. Reference counting answers when allocation ownership ends; it does not answer whether a particular operation is synchronized. Review liveness and permitted access separately; neither conclusion substitutes for the other.

**中文：** `Rc<T>` 通过非原子的引用计数支持单线程环境中的共享所有权。`Arc<T>` 使用原子引用计数，在内部类型满足必要 trait 约束时可以支持跨线程共享。两者都不会自动赋予修改 `T` 的权限。只读配置通常可以使用 `Arc<Config>`，可变状态则需要另外选择访问机制。引用计数回答的是分配何时不再被拥有，不能回答某个业务操作是否已经同步。代码评审应分别检查“是否存活”和“是否允许这样读写”，不能用其中一个结论替代另一个。

**English:** Reference cycles deserve explicit ownership design. Two objects that own strong references to one another may remain allocated after external owners disappear. A non-owning `Weak<T>` back-reference can represent an observer or parent link without extending strong ownership; upgrading it may fail and must be handled. This is relevant to request registries, callbacks, and session graphs. A memory-safe cycle can still become a production memory leak, so the absence of dangling pointers is not a complete resource-usage guarantee. Check that strong reference counts can actually reach zero when the object graph is torn down.

**中文：** 引用环需要明确设计。两个对象互相持有强引用时，即使外部所有者都消失，也可能继续占用内存。不增加强所有权的 `Weak<T>` 回指可以表达观察者或父节点关系，但升级为强引用可能失败，调用方必须处理对象已经不存在的情况。请求注册表、回调和会话图都容易涉及这种结构。安全的引用环仍然可能造成生产环境中的内存泄漏，因此“没有悬空指针”不是完整的资源使用保证；还应确认对象图退出后的强引用数量确实能够归零。

**English:** `RefCell<T>` permits interior mutation by checking borrow rules at runtime. A conflicting borrow can panic even on one thread. Its borrow state is not a synchronization mechanism for concurrent threads, so `Arc<RefCell<T>>` is not a general replacement for `Arc<Mutex<T>>`. Choose `RefCell` when single-threaded ownership organization needs dynamic access checking, and choose a suitable synchronization or message-passing design when multiple execution contexts may access shared state. Adding an atomic reference count around the wrong container does not repair its access rules; the outer layer only protects its own count.

**中文：** `RefCell<T>` 通过运行时借用检查允许内部可变性，即使只有一个线程，冲突借用也可能引发 panic。它的借用状态并不是用于并发线程的同步机制，因此 `Arc<RefCell<T>>` 不能普遍替代 `Arc<Mutex<T>>`。当单线程中的对象组织确实需要动态访问检查时，可以选择 `RefCell`；当多个执行上下文可能访问共享状态时，应选择合适的同步或消息传递设计。错误选择容器不能靠再包一层原子引用计数修正，外层只解决自己的计数问题。

**English:** A mutex provides synchronized exclusive access. Its guard releases that access through destruction. Keep the guarded work small and avoid calling unknown code while locked, because callbacks can block or acquire other locks. Standard-library mutex poisoning reports that a panic may have interrupted an invariant; recovering the inner value does not prove the invariant is repaired. Decide which state can be reconstructed and which operation should fail. Poisoning is advisory and is not a substitute for the safety invariants of unsafe code. Successfully acquiring the mutex does not prove that application data is complete and consistent.

**中文：** 互斥锁提供同步的排他访问，guard 在销毁时释放这项访问权。应尽量缩小受保护工作，避免持锁调用行为未知的代码，因为回调可能阻塞或继续申请其他锁。标准库互斥锁的中毒状态提示 panic 可能打断了业务不变量；取回内部值并不意味着不变量已经修复。你需要决定哪些状态能够重建，哪些操作应该失败。中毒属于提示机制，不能作为 unsafe 代码安全性的依赖，更不能把“能够取得锁”当作内部数据在业务上完整一致的证明。

**English:** An atomic counter can be appropriate for independent metrics, but separate atomic variables do not automatically form one transaction. If a request count and its total bytes must describe exactly the same snapshot, independent loads can observe different moments. A mutex, an explicit snapshot protocol, or a design that tolerates approximate metrics may be appropriate. Memory ordering should follow a stated synchronization requirement. Do not introduce `unsafe impl Send` or stronger atomic ordering merely to silence a misunderstanding of the state model. State which values must change together before choosing a concurrent container.

**中文：** 独立指标有时适合使用原子计数器，但多个独立原子变量不会自动组成事务。如果请求数与累计字节数必须表示完全相同的一次快照，分别读取可能观察到不同时间点。此时可以使用互斥锁、明确的快照协议，或者明确接受近似指标的设计。内存顺序应由实际同步要求决定，不能因为不理解状态模型就随意增加更强顺序，也不能手工实现 `Send` 来压制编译错误。首先写清哪些数据必须共同变化，往往比立即选用某种并发容器更重要。

## 5. Threads, Scopes, and Transfer Contracts / 线程、作用域与转移契约

**English:** `Send` describes whether ownership of a type may safely cross thread boundaries. `Sync` means shared references to the type can safely be sent between threads; equivalently, `&T` is `Send` when `T` is `Sync`. These are type-level safety properties, not promises of speed, fairness, or absence of deadlocks. Many types derive the properties from their fields. When a compiler rejects a transfer, examine the captured type and its fields before adding wrappers. A wrapper cannot manufacture an absent synchronization invariant. Whether a foreign handle can cross threads must follow the foreign library's actual contract.

**中文：** `Send` 描述类型的所有权能否安全跨越线程边界；`Sync` 描述该类型的共享引用能否安全在线程间传递，即 `T` 为 `Sync` 时 `&T` 可为 `Send`。这些是类型层面的安全属性，不保证运行速度、公平性或不会死锁。很多类型的属性由字段自动决定。编译器拒绝转移时，应先检查实际捕获类型及其字段，而不是不断增加包装。包装本身不能凭空创造缺失的同步不变量；一个外部句柄是否可跨线程，必须由外部库的真实契约支持。

**English:** An ordinary `thread::spawn` starts a thread whose lifetime is not constrained to the caller's stack frame. Its closure and return value therefore have bounds that exclude temporary borrowed state. Adding `move` changes how captures enter the closure: it does not turn a borrowed reference into owned referent data. Moving `&data` still moves or copies a reference to `data`. If `data` can disappear while the thread still needs it, moving the reference does not solve the problem. List the actual captured values rather than judging a closure only by whether it contains `move`.

**中文：** 普通 `thread::spawn` 创建的线程，其生命周期不受调用方栈帧约束，因此闭包和返回值的约束排除了短期借用状态。增加 `move` 会改变捕获值进入闭包的方式，却不会把借用引用变成对被引用数据的所有权。移动 `&data`，转移或复制的仍然是指向 `data` 的引用。如果线程还需要访问时 `data` 可能已经消失，移动引用并不能解决问题。判断一段闭包代码时，应列出捕获的实际值，而不是只根据有没有 `move` 作出结论。

**English:** Immediately joining a spawned thread does not relax its function signature. The compiler checks the API's declared contract, including the possibility that callers discard the handle. Join is an operation that observes completion and retrieves a result; it is not a retroactive proof that arbitrary local borrows were permitted in the spawn call. Use a scoped thread when the desired API is specifically allowed to borrow surrounding local data and wait before leaving the scope. This choice expresses different lifetime guarantees, even if two short execution paths happen to look equivalent.

**中文：** 创建普通线程后立即调用 join，也不会放宽创建函数的签名。编译器检查的是接口声明的契约，其中包含调用方可能丢弃句柄的情形。join 用来观察完成并取得结果，不是对先前创建线程时任意局部借用进行追认的证明。如果需要的是允许借用外围局部数据、并在离开范围之前等待完成的接口，就应使用作用域线程。这个选择表达的是不同生命周期保证，不是两种写法在当前一小段执行路径上看起来碰巧等价。

**English:** `thread::scope` guarantees that its scoped threads are joined before it returns. The surrounding data can therefore outlive all scoped uses. The callback finishing its own statements is not necessarily the point when every child has already finished; the scope machinery performs the necessary joining before returning to its caller. With `chunks_mut`, each child can own an exclusive borrowed slice, and the caller can inspect the whole vector after the scope returns. No mutex is needed for those non-overlapping elements. [Scoped-thread contract](https://doc.rust-lang.org/std/thread/fn.scope.html).

**中文：** `thread::scope` 保证在自身返回前，作用域内线程已经完成 join，因此外围数据可以覆盖所有受限线程中的使用。回调函数执行完自己的语句，不一定就是所有子线程已经结束的时刻；作用域机制会在向调用方返回之前执行必要等待。结合 `chunks_mut`，每个子线程可以持有一个独占的借用切片，调用方在 scope 返回后再检查整个向量。对这些互不重叠的元素不需要互斥锁。[作用域线程契约](https://doc.rust-lang.org/std/thread/fn.scope.html)。

**English:** Join handles also carry failure information. A panic in a normal worker is different from an application error returned by that worker. If the worker returns `Result<T, E>`, joining produces two layers to interpret: did the thread panic, and did the operation succeed? Flattening everything into `unwrap` is acceptable in a deliberately small demonstration but loses useful operational classification in a service. A worker failure should have a defined effect on pending requests, reply channels, and reusable resources. Otherwise, the main thread may detect a failure while other queued callers wait forever.

**中文：** 线程句柄还携带失败信息。普通工作线程发生 panic，与它正常返回一个业务错误并不是同一件事。如果线程返回 `Result<T, E>`，join 后就有两个层次需要解释：线程是否 panic，以及操作是否成功。在刻意简化的演示中统一使用 `unwrap` 可以帮助突出机制，但服务中这样处理会丢失有用的故障分类。还应定义工作线程失败对待处理请求、回复通道和可复用资源的影响，避免主线程虽然检测到失败，队列中的其他调用方却永远等待。

**English:** Message passing can make ownership transitions explicit. A producer moves a request into a channel; a consumer receives it and eventually sends a result. A bounded channel adds a capacity policy, but capacity counts messages rather than bytes unless the design says otherwise. Ten requests can still contain ten enormous buffers. Bound queue length, payload size, concurrent execution, and retained responses as separate resources. Otherwise replacing a shared vector with a channel may simply move the memory-growth problem. The sustainable memory peak may therefore remain uncontrolled.

**中文：** 消息传递可以让所有权转换变得明确：生产者把请求移入通道，消费者接收后最终发送结果。有界通道增加了容量策略，但容量通常计算消息条数，不会自动计算字节数，除非设计另外约定。十条请求仍然可能各自带有巨大的缓冲区。应把队列长度、负载大小、并行执行数量和保留回复分别视为资源。否则，把共享向量改成通道，可能只是把内存持续增长的问题换了一个位置，实际可承受的峰值并没有得到控制。

## 6. Async Tasks and Backpressure / 异步任务与背压

**English:** A future represents an operation that can make progress when polled. An async function call constructs such an operation; work runs as it is polled by an executor or another future. An await point permits suspension when the awaited operation is not ready. It is not a request to create a fresh operating-system thread. Code between suspension points can still occupy a worker for a long time. A CPU-intensive tokenization loop or blocking foreign call does not become cooperative simply because it appears inside an async function. Distinguish waiting for external events from occupying the CPU when choosing a scheduling strategy.

**中文：** future 表示一种在被轮询时可以推进的操作。调用异步函数会构造这样的操作，由执行器或其他 future 对它进行轮询时再执行工作。被等待操作尚未就绪时，await 点允许挂起，它不是要求创建一个新的操作系统线程。两个挂起点之间的代码仍然可能长时间占用执行线程。密集的分词循环或阻塞式外部调用，不会因为写进异步函数就自动具备协作性。分析延迟时必须区分等待外部事件和真正占用 CPU 的计算，才能选择正确的调度方式。

**English:** Tokio can schedule many tasks on a bounded set of worker threads. For a task to move between workers while suspended, the values retained across awaits must satisfy the relevant `Send` requirement. It is possible for a non-Send value to be used entirely before an await and not be retained in the future's suspended state. Nevertheless, scope the value explicitly rather than relying on obscure lifetime behavior. A local executor can host some non-Send tasks, but it does not remove the need to avoid blocking its thread. That thread remains a finite resource that must be allocated sensibly.

**中文：** Tokio 能在有限工作线程上调度大量任务。任务挂起后若可能转移到其他工作线程，跨 await 保留的值就需要满足相应的 `Send` 要求。有些不支持跨线程的值如果完全在 await 以前使用，没有保留进挂起状态，仍然可能出现在任务代码里。不过，建议通过明确的代码块表达其作用范围，不要依赖难以理解的生命周期细节。局部执行器可以承载某些非 `Send` 任务，但这也不会消除避免阻塞执行线程的要求，线程仍是需要合理分配的有限资源。

**English:** A short standard mutex critical section can be appropriate in asynchronous code when no guard crosses an await and contention is limited. An asynchronous mutex allows waiting without blocking the runtime thread and may support a guard across awaits, but a large critical section can still serialize all callers. The important choice is not a blanket rule that every async function needs an async mutex. First ask whether state can be immutable, transferred through a channel, or updated in a short synchronous section. [Tokio shared-state guidance](https://tokio.rs/tokio/tutorial/shared-state).

**中文：** 当 guard 不跨 await、竞争也较小时，异步代码中短暂使用标准互斥锁可以是合理选择。异步互斥锁允许等待者挂起而不阻塞运行时线程，也可能支持跨 await 保留 guard，但较大的临界区仍会让所有调用者串行。重要的不是制定“异步函数一律使用异步锁”的规则，而是先判断状态能否不可变、能否经通道转移，或者能否在短暂的同步区间内完成更新。[Tokio 共享状态说明](https://tokio.rs/tokio/tutorial/shared-state)。

**English:** Backpressure means an upstream component responds to a downstream capacity limit. Awaiting a bounded channel send is one possible policy. Rejecting immediately, applying a deadline, or selecting a different destination are others. Merely waiting on the send can leave many callers alive with large payloads outside the queue. A service therefore needs an admission policy before expensive allocation or task spawning. Record admission wait separately from execution time so that a slower response is not automatically blamed on GPU computation. Channel capacity is a local mechanism; effective backpressure must propagate along the request path to a component that can reduce incoming work.

**中文：** 背压表示上游对下游容量限制作出反应。等待有界通道发送完成是一种策略，立即拒绝、设置截止时间或选择其他目标也是策略。但只在发送处等待，仍可能让大量调用方带着大负载存活在队列外。因此，服务需要在昂贵分配或创建大量任务之前就定义准入策略。还应把准入等待与实际执行时间分别记录，避免响应变慢时自动归咎于 GPU 计算。通道容量是局部机制，完整的背压需要沿请求路径传递到真正能够减少输入的一层。

**English:** A semaphore limits concurrent ownership of permits, not every resource associated with a request. Acquire the permit before starting the work whose concurrency is being limited, and keep it until that work actually ends. If a timeout drops the permit while a detached backend operation continues, the number of backend operations may exceed the supposed limit. The permit lifetime and operation lifetime must agree. This pattern matters equally for database connections, subprocesses, and device submissions. Limiting a few admission futures alone does not prove that external concurrency is bounded.

**中文：** 信号量限制的是同时持有许可的数量，而不是请求关联的所有资源。应在启动需要限流的工作之前取得许可，并保留到该工作确实结束。如果超时让许可先被释放，而分离出去的后端操作仍继续执行，后端实际操作数量就可能超过声称的上限。许可生命周期必须与受约束操作的生命周期一致。这个问题既存在于数据库连接和子进程，也存在于设备任务提交；单看入口处限制了几个 future，无法证明外部世界中的并发数量也被正确限制。

**English:** Use blocking-task facilities for suitable blocking work, but bound their workload explicitly. Offloading each incoming request can otherwise create a large backlog or excessive CPU competition. A started blocking operation usually cannot be stopped simply by aborting the async handle that represents it. When possible, partition long CPU work and check a cancellation flag between bounded units. When interruption is unsafe or unsupported, maintain ownership until completion and stop admitting unnecessary additional work. A caller no longer waiting is not a reason to destroy resources that remain in use.

**中文：** 对合适的阻塞工作可以使用阻塞任务设施，但仍要明确限制其负载。若每个新请求都立即卸载过去，可能产生巨大积压或过度的 CPU 竞争。已经开始的阻塞操作，通常不能仅通过取消代表它的异步句柄就停止。条件允许时，可以把长计算拆成有限单元，在单元之间检查取消标志。如果中断不安全或不受支持，就应维持资源所有权直到完成，并停止接纳不必要的新工作，而不是以“调用方不等了”为理由提前销毁仍被使用的资源。

## 7. Cancellation Is a Protocol / 取消是一项协议

**English:** Distinguish four events: the client stops waiting, a queued request is removed or skipped, a running operation notices cancellation, and backend resources become reclaimable. These events may occur at different times. A timeout on a reply future directly establishes only that the caller did not obtain a reply within that waiting policy. A service that wants stronger cancellation must propagate an identifier or token, define where it is checked, and acknowledge which effects can no longer occur. Without that protocol, adding a timeout to every request does not prove that computation, network communication, or external tasks have stopped.

**中文：** 必须区分四件事：客户端停止等待、队列中的请求被移除或跳过、运行中的操作发现取消，以及后端资源真正可以回收。它们可能发生在不同时间。对回复 future 设置超时，直接说明的只是调用方没有按该等待策略及时获得回复。如果服务需要更强的取消语义，就必须传播标识符或令牌，规定检查位置，并确认哪些后续效果不再可能发生。没有这个协议，仅给每个请求套一个 timeout，不能证明计算、网络通信或外部任务已经全部停止。

**English:** Dropping an unspawned future can release its owned local state. Dropping a Tokio task's join handle normally detaches the task rather than aborting it. Requesting task abortion has its own completion semantics and cannot arbitrarily interrupt an ongoing synchronous foreign call. Moreover, external side effects may already have occurred before any local cancellation. A correct design therefore distinguishes cancellation requested, cancellation observed, and operation completed, rather than representing all three with one ambiguous boolean in a dashboard. Conflating these states also makes memory reclamation and concurrency capacity difficult to interpret.

**中文：** 销毁尚未独立创建为任务的 future，可以释放它拥有的本地状态。销毁 Tokio 任务的 join handle 通常只是放弃跟踪该任务，并不自动中止它。请求中止任务也有自己的完成语义，不能任意打断正在执行的同步外部调用。而且在本地取消发生前，外部副作用可能已经产生。因此，正确设计应区分“已请求取消”“已观察取消”和“操作已完成”，不能在监控面板上用一个含糊的布尔值代表三个状态，否则内存回收和并发容量都会难以解释。

**English:** In a `select!` expression, losing branches may have their futures dropped. Whether retrying a selected operation loses progress depends on that operation's cancellation safety. A high-level read that accumulated bytes internally is not interchangeable with an operation whose state remains in a caller-owned buffer. Review the exact method contract and choose where partial progress lives. The fact that all branches are memory-safe does not guarantee preservation of a business message or an external transaction. [Tokio select tutorial](https://tokio.rs/tokio/tutorial/select).

**中文：** 在 `select!` 表达式中，没有被选中的分支对应的 future 可能被销毁。之后重试是否丢失进度，取决于该操作自身的取消安全性。在内部累计字节的高层读取，与把状态保存在调用方缓冲区里的操作，并不可以随意互换。应查看具体方法的契约，决定部分进度由谁保存。所有分支在内存层面安全，并不保证业务消息不会丢失，也不保证外部事务保持完整。[Tokio select 教程](https://tokio.rs/tokio/tutorial/select)。

**English:** A deadline should usually describe the end-to-end budget, not restart a full budget at every stage. If admission takes most of the allowed time, execution should not automatically receive another full interval. Carry a deadline with the request and compute remaining time at transitions. Use monotonic time for elapsed budgets. Record where the deadline was exceeded, because an admission timeout and a late backend completion have different operational causes and may need different recovery actions. One aggregate request-timeout counter is insufficient for effective capacity and performance diagnosis.

**中文：** 截止时间通常应描述端到端预算，而不是让每个阶段重新获得完整预算。如果准入等待已经花掉大部分时间，执行阶段不应自动再得到同样长的一整段时间。可以让请求携带截止点，在状态转换时计算剩余时间，并使用适合衡量经过时间的单调时钟。还应记录在哪个阶段超过预算：准入超时和后端迟到完成具有不同原因，可能需要不同恢复措施。单一“请求超时”计数虽然便于汇总，却不足以支持有效的容量和性能诊断。

**English:** Graceful shutdown is another ownership protocol. Stop admission, close or drain queues according to policy, notify running operations, await the tasks that still own resources, and only then tear down shared services. Dropping one sender may not close a channel when hidden clones remain. Waiting forever for all tasks is also not a complete policy: define a shutdown deadline and what must be reported if work cannot finish. Treat forced termination as a distinct outcome rather than calling it successful draining. This protocol matters for service upgrades, test cleanup, and preventing background work from contaminating the next benchmark.

**中文：** 优雅退出也是所有权协议：先停止接纳请求，再按策略关闭或排空队列，通知正在运行的操作，等待仍持有资源的任务，最后拆除共享服务。如果还有隐藏的发送端克隆，仅销毁一个 sender 不一定会关闭通道。反过来，永远等待所有任务也不是完整策略；需要定义退出期限，并说明无法结束时应该报告哪些信息。强制终止应当成为单独结果，不能标记为成功排空。这个流程对服务升级、测试清理以及避免后台任务污染下一次基准都十分重要。

## 8. Unsafe and FFI Proof Boundaries / unsafe 与 FFI 的证明边界

**English:** An unsafe block permits certain operations that the compiler cannot fully validate. It does not disable ordinary type checking, and it does not make a false precondition true. A small unsafe block should identify what is being assumed about pointer validity, alignment, initialized contents, aliasing, bounds, and duration. Its safe wrapper must establish those facts for every safe caller. A wrapper whose safety depends on callers following an undocumented convention is not a sound safe interface. Passing tests is not that proof: finite test inputs cannot cover every permitted call.

**中文：** unsafe 块允许执行某些编译器无法完全验证的操作，但不会关闭普通类型检查，也不会让不成立的前提突然成立。一个小型 unsafe 块应说明它对指针有效性、对齐、已初始化内容、别名、边界和持续时间作出了哪些假设。安全包装必须为每个安全调用方建立这些条件。如果所谓安全接口仍然依赖调用方遵守没有表达出来的约定，这个接口就不能被认为健全。说明“这里经过测试”也不是证明，因为有限输入无法覆盖所有允许的调用方式。

**English:** Crossing a C ABI boundary requires compatible representations and explicit ownership. `repr(C)` can support a C-compatible structure layout, but it does not make Rust-specific containers such as `Vec` or `String` appropriate C interface fields. Prefer an opaque handle or clearly documented pointer-and-length representation. Specify who allocates, who frees, whether null is allowed, whether the callee stores the pointer, and whether callbacks occur on other threads. Each answer changes the wrapper's lifetime and thread-transfer requirements. Matching structure sizes alone does not establish interface correctness.

**中文：** 跨越 C ABI 边界需要兼容的表示和明确的所有权。`repr(C)` 可以支持与 C 兼容的结构体布局，但不会让 `Vec`、`String` 等 Rust 专属容器自动适合作为 C 接口字段。通常应使用不透明句柄，或者明确约定的指针加长度表示。需要说明谁分配、谁释放、是否接受空指针、被调用方是否保存指针，以及回调是否在其他线程发生。每个答案都会改变包装层的生命周期和线程转移要求，不能只对齐结构体大小就认为接口已经正确。

**English:** A pointer received from a foreign library is evidence of an address, not a complete reference contract. Before creating a Rust reference or slice, the wrapper must establish all corresponding Rust requirements. Creating a mutable slice is particularly strong because it expresses exclusive access for its lifetime. If the foreign library may still access that memory asynchronously, a simple lexical borrow around the submission call is insufficient. An in-flight owner, a completion event, or an equivalent protocol must connect buffer validity to actual completion. Course 07 applies this issue to CUDA; here, first identify the time interval missing from the proof.

**中文：** 从外部库得到的指针首先只是一个地址，不是完整的引用契约。构造 Rust 引用或切片前，包装层必须建立相应的全部要求。创建可变切片尤其强，因为它表达在有效期内的排他访问。如果外部库仍可能异步访问这块内存，那么只在提交调用附近建立词法借用并不足够。必须用执行中所有者、完成事件或等价协议，把缓冲区有效性与真实完成联系起来。课程 07 会将这个问题应用到 CUDA；本课首先要求你能够识别证明中缺失的时间范围。

**English:** Error and panic boundaries also need an ABI policy. Convert ordinary recoverable failures into documented return values or error objects. Do not let an unexpected Rust panic cross a foreign boundary whose ABI does not permit unwinding. Catching a panic, when appropriate, does not necessarily repair interrupted shared invariants. Likewise, matching an error code is only the first step: determine whether the foreign call started work, retained memory, or partially initialized an object before returning the error. [Rustonomicon FFI](https://doc.rust-lang.org/nomicon/ffi.html). Those facts determine which party still owns cleanup responsibility.

**中文：** 错误和 panic 边界也需要 ABI 策略。一般可恢复失败应转换为约定好的返回值或错误对象，不能让意外的 Rust panic 穿过不允许栈展开的外部调用边界。在适当场景捕获 panic，也不意味着被打断的共享不变量已经修复。同样，匹配错误码只是第一步，还必须判断外部调用返回错误以前是否已经启动工作、保存内存或部分初始化对象。只有知道这些事实，才能决定哪一方仍有清理责任。[Rustonomicon FFI](https://doc.rust-lang.org/nomicon/ffi.html)。

## 9. Lab A: Bounded Ownership Transfer / 实验 A：有界所有权转移

**English:** Save the following complete program as `bounded.rs` in a temporary working directory. It first fills a two-message queue before a consumer exists, so the full-queue observation is deterministic. The rejected third job is returned by `try_send` and remains owned by the caller. Starting the worker allows that same job to be submitted without cloning its payload. One request is canceled before submission, and each payload increments a destruction counter exactly once. This independently checks ownership retention under a full queue, cleanup of canceled work, and returned results for normal work without depending on a lucky scheduling order.

**中文：** 在临时工作目录中将以下完整程序保存为 `bounded.rs`。程序先在消费者出现之前填满容量为二的队列，因此满载观察具有确定性。第三个被拒绝的任务通过 `try_send` 返回，所有权仍属于调用方。启动工作线程后，再提交同一个任务，不需要克隆负载。一个请求在提交以前被标记取消，每份负载销毁时将计数器增加一次。这样可以分别验证满载时没有丢失所有权、取消任务仍被正确清理，以及正常任务确实返回计算结果，而不依赖线程刚好按某种顺序抢到时间片。

```rust
use std::sync::{Arc, atomic::{AtomicBool, AtomicUsize, Ordering}, mpsc};
use std::thread;

struct Payload {
    values: Vec<u64>,
    drops: Arc<AtomicUsize>,
}
impl Drop for Payload {
    fn drop(&mut self) {
        self.drops.fetch_add(1, Ordering::SeqCst);
    }
}
struct Job {
    id: usize,
    payload: Payload,
    cancelled: Arc<AtomicBool>,
    reply: mpsc::Sender<(usize, Result<u64, &'static str>)>,
}
fn main() {
    let drops = Arc::new(AtomicUsize::new(0));
    let (tx, rx) = mpsc::sync_channel::<Job>(2);
    let (reply_tx, reply_rx) = mpsc::channel();
    let make_job = |id, cancelled| Job {
        id,
        payload: Payload { values: vec![1, 2, 3, 4], drops: Arc::clone(&drops) },
        cancelled: Arc::new(AtomicBool::new(cancelled)),
        reply: reply_tx.clone(),
    };
    tx.send(make_job(0, false)).unwrap();
    tx.send(make_job(1, true)).unwrap();
    let pending = match tx.try_send(make_job(2, false)) {
        Err(mpsc::TrySendError::Full(job)) => job,
        _ => panic!("expected a full queue before starting the consumer"),
    };
    let worker = thread::spawn(move || {
        for job in rx {
            let result = if job.cancelled.load(Ordering::SeqCst) {
                Err("cancelled before execution")
            } else {
                Ok(job.payload.values.iter().sum())
            };
            let _ = job.reply.send((job.id, result));
        }
    });
    tx.send(pending).unwrap();
    drop(tx);
    drop(reply_tx);
    worker.join().unwrap();
    let mut results: Vec<_> = reply_rx.into_iter().collect();
    results.sort_by_key(|item| item.0);
    assert_eq!(results, vec![
        (0, Ok(10)), (1, Err("cancelled before execution")), (2, Ok(10))
    ]);
    assert_eq!(drops.load(Ordering::SeqCst), 3);

    let mut values = vec![1_u64, 2, 3, 4, 5, 6];
    thread::scope(|scope| {
        for chunk in values.chunks_mut(2) {
            scope.spawn(move || {
                for value in chunk { *value *= 2; }
            });
        }
    });
    assert_eq!(values, vec![2, 4, 6, 8, 10, 12]);
    println!("ownership, cancellation, cleanup, and scoped slicing: passed");
}
```

```bash
rustc --edition=2024 bounded.rs -o bounded
./bounded
```

**English:** The reply channel is unbounded only because the entire exercise has three bounded-size results and the main thread joins before collecting them. Replacing it with a capacity-one reply channel without changing the control flow can deadlock: the worker waits to send its second reply while the main thread waits for the worker to finish. A production implementation should continuously collect replies or give each request its own reply path. Bounded input does not by itself prove every other buffer is bounded. Review both data flow and wait dependencies to find where components can wait on one another.

**中文：** 回复通道使用无界形式，是因为整个实验只有三条大小受限的结果，而且主线程先 join 再收集结果。如果只把回复通道换成容量为一的有界通道，而不调整控制流程，就可能死锁：工作线程等待发送第二条回复，主线程却在等待工作线程结束。生产实现应该持续接收结果，或者让每条请求有独立回复路径。入口有界不能自动证明其他缓冲区也有界。评审一个并发流程时，应同时画出数据流和等待关系，找出双方可能相互等待的位置。

**English:** This program checks invariants, not scheduling performance. `SeqCst` makes the small atomic examples easy to inspect; it is not a recommendation to use that ordering for every metric. The canceled flag is initialized before queueing, so the test establishes skipping already-canceled work, not interruption of running work. Ignoring a reply-send error is intentional because it means the receiver is gone, and the job must still be cleaned up. A real service should account for that discarded reply in observability without retrying it forever. Each assertion should establish a specific fact; several passing assertions do not certify a production service.

**中文：** 本程序检查不变量，不测量调度性能。示例采用 `SeqCst` 是为了让小型原子操作容易审查，并不是建议所有指标都使用这种顺序。取消标志在入队前已经设置，所以实验验证的是跳过已经取消的任务，并不证明能够中断运行中的工作。忽略回复发送错误是有意的：接收者已经消失时，任务仍然必须得到清理。真实服务应在观测中记录被丢弃的回复，但不应因此无限重试。每项断言都应该对应一个明确事实，不能把多项通过直接概括成“生产级服务已经完成”。

### Expected Compilation Failure / 预期编译失败

**English:** Save this separately as `borrow_fail.rs` and compile it. It is intentionally invalid: the closure needs a longer-lived capture than a borrow of this local vector permits. Fix it first by moving the vector into the closure, then separately by using scoped borrowing. Explain why the move-based variant cannot also print the original vector after joining unless ownership is returned. The error category is the observation; diagnostic wording may change between compiler versions. Treat the failure as intentional, and explain the API meaning rather than merely copying a suggested keyword.

**中文：** 将下面程序单独保存为 `borrow_fail.rs` 并编译。它是故意无效的：闭包需要的捕获有效期，超出了对该局部向量的借用所能保证的范围。先通过移动向量到闭包中修复，再另写一个使用作用域借用的版本。解释为什么使用移动的版本，若没有把所有权返回，就不能在 join 后打印原向量。实验观察应是错误类别和产生原因，具体诊断文字可能随编译器版本变化。不要把预期失败当作教材缺陷，也不要仅把建议中的关键字抄上去而忽略接口含义。

```rust
fn main() {
    let data = vec![1, 2, 3];
    let worker = std::thread::spawn(|| println!("{data:?}"));
    worker.join().unwrap();
}
```

```bash
rustc --edition=2024 borrow_fail.rs
```

## 10. Lab B: Timeout Does Not Finish Backend Work / 实验 B：超时不等于后端完成

**English:** The second experiment uses Tokio's paused clock to make a timeout scenario reproducible without asserting real wall-clock timing. Create an isolated Cargo project and use the two files below. The dependency version is pinned to the version shown by the official API reference during source verification. `test-util` enables the virtual clock. This is a model of cancellation and ownership, not a model of GPU execution speed, kernel interruption, or the internal scheduler of a serving framework. Actual elapsed time depends on compilation, machine load, and the executor. Observe logical ordering and assertions rather than deriving inference throughput from it.

**中文：** 第二个实验使用 Tokio 的暂停时钟，让超时场景可复现，而不对真实墙钟时间作断言。在独立 Cargo 项目中使用下面两个文件。依赖版本固定为资料核验时官方 API 文档显示的版本，`test-util` 用于虚拟时钟。该程序模拟取消与所有权关系，不模拟 GPU 执行速度、kernel 中断或推理框架内部调度。真实运行时间受编译、机器负载与执行器影响，因此输出中的逻辑顺序和断言才是本实验的观察对象，不能据此计算推理吞吐量。

**English:** Manifest, `Cargo.toml`:

**中文：** 清单文件 `Cargo.toml`：

```toml
[package]
name = "course04-cancel"
version = "0.1.0"
edition = "2024"

[dependencies]
tokio = { version = "=1.53.1", features = ["rt", "macros", "sync", "time", "test-util"] }
```

**English:** Complete program, `src/main.rs`:

**中文：** 完整程序 `src/main.rs`：

```rust
use std::sync::{Arc, atomic::{AtomicBool, AtomicUsize, Ordering}};
use std::time::Duration;
use tokio::sync::{mpsc, oneshot};

struct Active(Arc<AtomicUsize>);
impl Drop for Active {
    fn drop(&mut self) { self.0.fetch_sub(1, Ordering::SeqCst); }
}
struct Job {
    cancelled: Arc<AtomicBool>,
    reply: oneshot::Sender<Result<usize, &'static str>>,
}

#[tokio::main(flavor = "current_thread")]
async fn main() {
    tokio::time::pause();
    let active = Arc::new(AtomicUsize::new(0));
    let cancelled = Arc::new(AtomicBool::new(false));
    let (tx, mut rx) = mpsc::channel::<Job>(1);
    let worker_active = Arc::clone(&active);
    let worker = tokio::spawn(async move {
        let mut observed_cancel = 0;
        while let Some(job) = rx.recv().await {
            worker_active.fetch_add(1, Ordering::SeqCst);
            let _guard = Active(Arc::clone(&worker_active));
            tokio::time::sleep(Duration::from_millis(20)).await;
            let result = if job.cancelled.load(Ordering::SeqCst) {
                observed_cancel += 1;
                Err("cancellation observed after the current step")
            } else {
                Ok(42)
            };
            let _ = job.reply.send(result);
        }
        observed_cancel
    });
    let (reply_tx, reply_rx) = oneshot::channel();
    tx.send(Job { cancelled: Arc::clone(&cancelled), reply: reply_tx })
        .await.unwrap();
    let result = tokio::time::timeout(Duration::from_millis(5), reply_rx).await;
    assert!(result.is_err());
    cancelled.store(true, Ordering::SeqCst);
    assert_eq!(active.load(Ordering::SeqCst), 1);
    drop(tx);
    assert_eq!(worker.await.unwrap(), 1);
    assert_eq!(active.load(Ordering::SeqCst), 0);
    println!("caller timeout precedes backend cleanup: passed");
}
```

```bash
cargo run
```

**English:** The main task times out while waiting for a reply. It then records cancellation, but the worker still owns its active-operation guard until its simulated step ends. The first active-count assertion proves that releasing the caller's reply receiver did not release backend ownership. Awaiting the worker after closing admission proves that cleanup eventually occurred. A cancellation token checked only between steps gives a cancellation latency bounded by the remaining step only when each step itself has a known bound; a blocking external operation may not provide one. Record this limitation in real service behavior; the virtual twenty-millisecond step does not generalize to arbitrary backends.

**中文：** 主任务等待回复时超时，随后记录取消，但工作任务在模拟步骤结束以前仍然拥有代表活动操作的 guard。第一次活动计数断言证明：释放调用方的回复接收端，没有同时释放后端所有权。关闭入口后等待工作任务结束，则验证清理最终发生。仅在步骤之间检查令牌时，只有每个步骤本身具有已知时间上界，才能据此约束取消延迟；阻塞式外部操作未必提供这样的上界。真实系统需要把这一限制写进服务行为，不能把虚拟时钟实验中的二十毫秒直接推广到任意后端。

**English:** For an additional failure analysis, remove `drop(tx)` and predict what happens before running under an external timeout. The receiver remains open because the sender still exists, so the worker waits for another job and the main task waits for the worker. This is a lifecycle deadlock, not a data race. Restore channel closure rather than increasing the timeout. A second variation removes the cancellation flag store: the late worker computes a reply that no caller receives, demonstrating why reply abandonment and work cancellation are separate policies. Define and observe those policies separately.

**中文：** 进一步分析失败时，可以先预测删除 `drop(tx)` 会发生什么，再在外部超时保护下运行。发送端仍然存在，接收通道就保持开放；工作任务等待下一条请求，主任务则等待工作任务结束。这属于生命周期死锁，而不是数据竞争。修复应是恢复正确关闭流程，而非不断延长超时时间。另一个变体是删除设置取消标志的语句：后端将产生已经无人接收的迟到回复。这说明放弃回复和取消计算属于两个策略，必须分别定义和观察。

## 11. Ten Exercises with Answers / 十道习题与参考答案

### 1. Queue Ownership / 队列所有权

**English:** Question: why can the third payload in Lab A be submitted after `try_send` reports a full queue without cloning it? Answer: the full-channel error contains the unsent job. The failed transfer returns ownership, and the caller binds that returned value before sending again. If the caller simply discards the error, the job is dropped rather than secretly retained in the queue. Review the concrete error type whenever designing retries, since not every API preserves its input in the same way. Decide whether retries have a deadline so persistent lack of capacity does not retain payloads indefinitely.

**中文：** 问题：实验 A 的第三份负载在 `try_send` 报告队列已满后，为什么还能不经过克隆就再次提交？答案：满载错误包含未发送的任务，失败的转移把所有权交回，调用方重新绑定后再次发送。如果调用方直接丢弃这个错误，任务会被销毁，而不是偷偷保留在队列中。设计重试时必须检查实际错误类型，因为并不是所有接口都以相同方式保存输入。还应决定重试是否具有截止时间，避免在容量长期不足时无限保留负载。

### 2. Move a Reference / 移动引用

**English:** Question: does `move || use_slice(borrowed)` make the closure own the vector behind `borrowed: &[u8]`? Answer: no; the captured value is the slice reference, including its lifetime relationship. Own the data, share a suitable owning allocation, or use a scoped interface that permits borrowing. The closure keyword alone cannot change the referent's lifetime. Identify the captured type before deciding whether ownership has crossed the intended boundary. A reference containing an address and length does not own destruction of that allocation.

**中文：** 问题：`move || use_slice(borrowed)` 会让闭包拥有 `borrowed: &[u8]` 背后的向量吗？答案：不会，捕获的是切片引用，其中仍保留与被引用对象的生命周期关系。可以转交数据所有权，共享合适的拥有者，或者使用允许借用的作用域接口。闭包关键字本身不能改变被引用对象的寿命。判断所有权是否穿过预期边界以前，必须先确认捕获类型；看到引用里有地址和长度，并不意味着它承担该分配的销毁责任。

### 3. Scope Completion / 作用域完成

**English:** Question: when may the caller safely inspect the whole vector mutated through scoped `chunks_mut` workers? Answer: after `thread::scope` returns, provided no other conflicting access exists. The API guarantees child completion before return, and the chunk API establishes non-overlap. Neither an arbitrary sleep nor observing one worker's log establishes that all workers are done. The proof combines a spatial property with a temporal property. Assuming work has probably finished cannot replace either property.

**中文：** 问题：通过作用域内的 `chunks_mut` 工作线程修改向量后，调用方何时可以安全检查整个向量？答案：在没有其他冲突访问的前提下，`thread::scope` 返回以后。线程接口保证子线程在返回前完成，切片接口保证区域不重叠。随意等待一段时间，或者看到某个工作线程打印日志，都不能证明所有线程结束。这里的证明同时包含空间属性与时间属性，缺少任何一项都不能用“应该已经执行完”来补足。

### 4. Shared Ownership / 共享所有权

**English:** Question: why is `Arc<RefCell<Vec<u8>>>` not the usual cross-thread mutable buffer? Answer: atomic reference counting protects the ownership count, while `RefCell` does not provide cross-thread synchronization for its borrow state. Use disjoint owned data, message passing, or a synchronization type satisfying the actual access requirements. Choosing a mutex still leaves critical-section length and lock ordering to the programmer; trait satisfaction is the start of the design review. Trait satisfaction does not prevent contention from reducing throughput or cyclic waits from stopping the service.

**中文：** 问题：为什么 `Arc<RefCell<Vec<u8>>>` 不是通常意义上的跨线程可变缓冲区？答案：原子引用计数保护的是所有权计数，`RefCell` 并没有为其借用状态提供跨线程同步。可以选择互不重叠的独立数据、消息传递，或者满足实际访问要求的同步类型。即使选择了互斥锁，临界区大小和加锁顺序仍需要程序员设计。满足 trait 约束只是设计审查的起点，并不保证服务不会因锁竞争而失去吞吐或因为循环等待而停住。

### 5. Timeout Meaning / 超时含义

**English:** Question: what does the first active-count assertion in Lab B establish? Answer: the caller has stopped waiting, but backend ownership is still alive. It does not establish that a GPU kernel is running or that cancellation will always complete within twenty milliseconds. Those would require different evidence. Monitoring should expose both abandoned requests and operations still consuming resources so that an apparent fall in waiting clients is not mistaken for a fall in backend load. Capacity protection should therefore follow the actual execution lifecycle rather than only the client connection lifecycle.

**中文：** 问题：实验 B 的第一次活动计数断言证明了什么？答案：调用方已经停止等待，但后端所有权仍然存活。它不能证明 GPU kernel 正在执行，也不能证明取消总会在二十毫秒内完成，这些结论需要另外的证据。监控应分别体现已经放弃的请求和仍然消耗资源的操作，避免等待客户端数量下降时，就错误推断后端负载同步下降。这也是为什么容量保护应围绕实际执行生命周期设计，而不能仅跟随客户端连接生命周期。

### 6. Static Bounds / 静态生命周期约束

**English:** Question: must an owned `String` passed to a `'static` task leak? Answer: no. The bound excludes incompatible short-lived borrowed contents; it does not require permanent allocation. The string can be dropped when task ownership ends. A leak is only one way to produce long-lived storage and is generally the wrong response to a task-capture problem. Prefer moving durable ownership and making cleanup observable through the normal task lifecycle. Do not make requests permanently live merely to remove a compiler error.

**中文：** 问题：把拥有数据的 `String` 传给要求 `'static` 的任务，是否必须泄漏这块内存？答案：不需要。约束排除不兼容的短期借用内容，并不要求永久分配。任务所有权结束时，字符串可以正常销毁。泄漏只是制造长期存储的一种方式，通常不是处理任务捕获问题的正确办法。应优先移动寿命由所有者管理的数据，并通过正常任务生命周期观察清理；不要为了让编译错误消失就把本来应及时释放的请求变成永久存活的数据。

### 7. Diagnose a Reply Deadlock / 排查回复死锁

**English:** Question: Lab A uses a capacity-one reply channel and joins before reading replies; the process hangs. Where is the cycle? Answer: the worker waits for space to send a later reply, while the only reader waits for the worker's completion. Collect replies concurrently or redesign the response path. Adding more input capacity does not break this cycle. A thread dump and a diagram of blocking operations are more informative than randomly changing buffer sizes. Use an external timeout for the failure experiment, record the expected hang, and restore the working design without leaving the failed process running in the background.

**中文：** 问题：把实验 A 的回复通道改为容量一，并保持先 join 后读取，进程挂住。循环等待在哪里？答案：工作线程等待空间以发送后续回复，唯一的读取方却等待工作线程结束。应并发接收回复，或者重新设计返回路径。增加入口队列容量不能打破这个环。线程状态和阻塞操作关系图，比随机修改缓冲区大小更有帮助。复现实验时应设置外部超时，记录预期挂起原因，然后恢复正常设计，避免将故意失败的程序遗留为后台进程。

### 8. Diagnose Lock Retention / 排查锁持有时间

**English:** Question: a guard's last read occurs before an expensive computation, yet other workers wait until the function returns. Why? Answer: last use of the borrowed access does not necessarily run the guard's destructor. Inspect its drop scope and introduce an explicit inner block or `drop` after the protected update. Verify that subsequent work uses owned or otherwise valid data. Moving code out of a lock without preserving the data invariant can exchange contention for incorrect results. Validate the relationship among snapshots, state versions, and concurrent updates before and after optimization rather than checking only reduced waiting time.

**中文：** 问题：guard 最后一次读取发生在昂贵计算以前，其他线程却一直等待函数返回，原因是什么？答案：借用访问的最后使用不一定触发 guard 析构。应检查销毁作用域，在受保护更新后加入明确内部代码块或 `drop`。还要确认后续工作使用拥有所有权或其他仍有效的数据。把代码移到锁外时必须维护数据不变量，否则可能只是用错误结果替换了锁竞争。优化前后都应验证快照、状态版本和并发更新之间的关系，而不是只看等待时间是否下降。

### 9. Design Admission Limits / 设计准入限制

**English:** Question: design limits for a service accepting large variable-size requests. Answer: cap payload size, bound admitted request count or total admitted bytes, bound the queue, and bound active backend work. Apply a deadline or rejection policy before retaining expensive state. Measure rejected, waiting, executing, and abandoned requests separately. A queue length of one hundred is insufficient without a payload-size policy, and a caller timeout cannot release execution capacity before actual backend completion. Acceptance should combine large payloads, sustained overload, and frequent client disconnections.

**中文：** 问题：为接收大体积、可变大小请求的服务设计限制。答案：限制单条负载大小，对已接纳请求数或累计字节数设界，限制队列和实际后端并发，并在保留昂贵状态前实施截止时间或拒绝策略。分别测量拒绝、等待、执行和已放弃请求。没有负载大小策略，一百条队列容量仍然可能耗尽内存；后端尚未完成时，也不能仅因调用方超时就提前释放执行容量。验收应包含大负载、持续过载及客户端频繁断连的组合场景。

### 10. Design an FFI Wrapper / 设计 FFI 包装

**English:** Question: a C function stores a byte pointer and calls back later. What must the safe Rust wrapper own? Answer: an owner keeping the buffer and callback state alive through the last possible foreign access, plus a completion or unregister protocol. Specify callback thread behavior, mutation rights, allocation/deallocation pairing, and error cases where registration partially succeeds. A temporary borrowed slice around the registration call proves too little. Tests exercise the protocol, but the soundness argument must cover every allowed safe call. In particular, consider early handle destruction, repeated unregistration, and races between cancellation and callbacks.

**中文：** 问题：一个 C 函数保存字节指针并稍后回调，安全 Rust 包装必须拥有什么？答案：需要一个所有者，在外部最后一次可能访问以前保持缓冲区和回调状态存活，同时需要完成确认或注销协议。必须说明回调线程、修改权限、分配释放配对，以及注册部分成功后又返回错误的情形。只在注册调用附近借用切片，证明范围太小。测试可以检查协议路径，但健全性论证必须覆盖所有允许的安全调用，尤其要考虑调用方提前丢弃句柄、重复注销及取消与回调竞争。

## 12. Review and Acceptance / 复盘与验收

**English:** You have completed the course when you can trace an owned request from admission to cleanup, explain which borrows may cross which boundaries, and distinguish data-race prevention from deadlock and cancellation correctness. Reproduce the bounded-channel assertions and the intended compilation failure without copying unexplained fixes. For the async exercise, describe the three distinct observations: caller timeout, cancellation detection, and final resource release. State what the experiment does not measure before using it in a portfolio. This prevents a resource-lifetime check from being mistaken for performance evidence for an entire inference platform.

**中文：** 完成本课的标准是：能够追踪一条拥有数据的请求从准入到清理的全过程，解释哪些借用可以跨越哪些边界，并区分数据竞争防护、死锁正确性和取消正确性。应能复现有界通道断言及预期编译失败，而不是复制自己无法解释的修复。异步实验中，需要分别说明调用方超时、后端发现取消和资源最终释放三个观察。将实验放进作品集以前，先明确它没有测量什么，才能让读者理解结论的适用范围，不把一个资源生命周期验证误读为完整推理平台的性能证明。

**English:** Read Course 07 next if the main question is foreign CUDA ownership. Read Course 10 for the model-serving execution path, and Course 12 for reproducible service measurements. Rust's type system can prevent many invalid memory-access patterns, but it does not choose a queue policy, infer an acceptable tail latency, or decide whether a request may be retried. Those are system contracts that must remain explicit. Good Rust infrastructure combines a small, well-justified ownership model with measurements and failure behavior that another engineer can reproduce. That combination turns language-level benefits into system maintainability.

**中文：** 如果主要问题是外部 CUDA 资源所有权，下一步阅读课程 07；如果关注模型服务执行路径，阅读课程 10；需要可复现服务度量时，参考课程 12。Rust 类型系统可以排除许多无效内存访问方式，却不会替你选择队列策略、推断可接受的尾延迟，或者决定请求是否允许重试。这些系统契约仍然必须明确。可靠的 Rust 基础设施需要把规模较小、依据充分的所有权模型，与其他工程师能够复现的测量和失败行为结合起来，才能将语言层面的优势转化为系统层面的可维护性。

## Validation Record / 验证记录

**English:** On 2026-09-18 the standard-library lab was extracted from this Markdown, compiled with the recorded compiler, and executed successfully. The separate borrowing example failed with E0373 as intended. The Tokio lab was extracted into a temporary Cargo project, resolved Tokio 1.53.1, compiled, and passed both active-resource assertions and the cancellation-observation assertion. No GPU is used by these experiments. The intentionally hanging variations are reasoning exercises, not claims of additional completed runs.

**中文：** 2026-09-18，标准库实验从本 Markdown 提取，使用所记录编译器完成编译并成功执行；独立借用反例按预期产生 E0373。Tokio 实验提取至临时 Cargo 项目，解析到 Tokio 1.53.1，编译后通过两项活动资源断言和取消观察断言。这些实验不使用 GPU。故意挂起的变体属于分析练习，并不表示已经另外完成相关运行。

## References / 参考资料

**English:** Primary references checked on 2026-09-18. The explanations, exercises, and lab programs above are original instructional material; references support API contracts rather than substitute for experiment evidence.

**中文：** 以下一手资料于 2026-09-18 核验。正文讲解、习题和实验程序为原创教学材料；引用用于支持接口契约，不能代替实验运行证据。

- [Rust Book: ownership / Rust Book：所有权](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
- [Rust Book: shared-state concurrency / Rust Book：共享状态并发](https://doc.rust-lang.org/book/ch16-03-shared-state.html)
- [Standard library: scoped threads / 标准库：作用域线程](https://doc.rust-lang.org/std/thread/fn.scope.html)
- [Standard library: bounded channels / 标准库：有界通道](https://doc.rust-lang.org/std/sync/mpsc/fn.sync_channel.html)
- [Standard library: mutex contracts / 标准库：互斥锁契约](https://doc.rust-lang.org/std/sync/struct.Mutex.html)
- [Tokio shared state / Tokio 共享状态](https://tokio.rs/tokio/tutorial/shared-state)
- [Tokio select and cancellation / Tokio select 与取消](https://tokio.rs/tokio/tutorial/select)
- [Tokio API documentation / Tokio API 文档](https://docs.rs/tokio/1.53.1/tokio/)
- [Rustonomicon FFI / Rustonomicon 外部函数接口](https://doc.rust-lang.org/nomicon/ffi.html)
