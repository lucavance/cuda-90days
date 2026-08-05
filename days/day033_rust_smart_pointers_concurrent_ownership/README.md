# Day 033: Rust Smart Pointers and Concurrent Ownership / Rust 智能指针与并发所有权

Date / 日期: 2026-08-05

## Topic / 主题

**English:** Rust smart pointers and concurrent ownership: `Box<T>`, the
`Drop` trait, `Rc<T>`, `Arc<T>`, `RefCell<T>`, `Mutex<T>`, RAII lock guards,
`Arc<Mutex<T>>`, move closures, and the `Send` and `Sync` auto traits.

**中文：** Rust 智能指针与并发所有权：`Box<T>`、`Drop` trait、`Rc<T>`、
`Arc<T>`、`RefCell<T>`、`Mutex<T>`、RAII lock guard、`Arc<Mutex<T>>`、
move 闭包，以及 `Send` 与 `Sync` 自动 trait。

## Goal / 目标

**English:** Build a precise model for choosing ownership and mutation
primitives in single-threaded and multi-threaded Rust. Understand which type
manages ownership, which type controls mutation, when cleanup occurs, and how
the compiler uses `Send` and `Sync` to prevent unsafe cross-thread sharing.

**中文：** 建立在单线程与多线程 Rust 中选择所有权和可变性工具的准确模型。
理解哪种类型管理所有权、哪种类型控制修改、何时发生清理，以及编译器如何利用
`Send` 与 `Sync` 阻止不安全的跨线程共享。

## Core Mental Model / 核心思维模型

**English:** Ownership and mutation are separate design dimensions. `Box`,
`Rc`, and `Arc` describe who owns a value; `RefCell`, `Mutex`, and `RwLock`
describe how mutation is coordinated. `Rc<RefCell<T>>` is a common
single-threaded shared-mutation composition, while `Arc<Mutex<T>>` is a common
multi-threaded composition. Guard objects enforce borrowing or locking rules
through their lifetimes and `Drop` implementations.

**中文：** 所有权与可变性是两个独立的设计维度。`Box`、`Rc` 和 `Arc` 描述谁
拥有值；`RefCell`、`Mutex` 和 `RwLock` 描述如何协调修改。
`Rc<RefCell<T>>` 是常见的单线程共享可变组合，`Arc<Mutex<T>>` 是常见的多线程
组合。guard 对象通过自身生命周期与 `Drop` 实现来执行借用或加锁规则。

## 10 Concept Questions / 10 个概念问题

### 1. Moving ownership of a `Box<T>` / 移动 `Box<T>` 的所有权

**Question (English):** What does the program print? Would the commented line
compile? Does assigning `first` to `second` copy the heap-allocated `String` or
move ownership of the `Box`?

**问题（中文）：** 程序输出什么？取消注释的最后一行能否编译？把 `first`
赋给 `second` 会复制堆上的 `String`，还是移动 `Box` 的所有权？

~~~rust
fn main() {
    let first = Box::new(String::from("GPU"));
    let second = first;

    println!("{}", second);

    // println!("{}", first);
}
~~~

**Explanation (English):** `Box<String>` is not `Copy`. Assignment therefore
moves the box value and its ownership of the existing heap allocation. It does
not clone the `String` contents. The old binding is considered moved and cannot
be used unless ownership is returned to it later.

**解说（中文）：** `Box<String>` 没有实现 `Copy`，因此赋值会移动 box 值以及
它对既有堆分配的所有权，而不会 clone `String` 内容。旧绑定被视为已经移动，
除非之后重新获得所有权，否则不能继续使用。

**Correct Answer (English):** The program prints `GPU`. Uncommenting the final
line causes a compile-time use-after-move error. After the move, `second` is the
sole owner of the same heap allocation and `first` is unavailable.

**正确答案（中文）：** 程序输出 `GPU`。取消最后一行的注释会产生编译期的移动后
使用错误。移动完成后，`second` 独占同一块堆分配，`first` 不再可用。

### 2. Reverse destruction order with `Drop` / 使用 `Drop` 按反序析构

**Question (English):** What is the complete output? In what order are values
in the inner scope dropped, and when is `outer` dropped?

**问题（中文）：** 完整输出是什么？内部作用域中的值按什么顺序 drop？`outer`
在什么时候 drop？

~~~rust
struct Resource(&'static str);

impl Drop for Resource {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let _outer = Resource("outer");

    {
        let _first = Resource("first");
        let _second = Resource("second");
        println!("inside");
    }

    println!("outside");
}
~~~

**Explanation (English):** Local values are dropped when their drop scope
ends. Values in the same scope are normally dropped in reverse declaration
order. The inner values are therefore gone before execution reaches the
`outside` print, while `outer` lives until the end of `main`.

**解说（中文）：** 局部值在其 drop scope 结束时被释放。同一作用域中的值通常
按照声明顺序的反序 drop。因此内部值会在打印 `outside` 之前释放，而 `outer`
存活到 `main` 结束。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
inside
drop second
drop first
outside
drop outer
~~~

**English:** `_second` is dropped before `_first`, and `_outer` is dropped last
when the outer function scope ends.

**中文：** `_second` 先于 `_first` drop；最外层函数作用域结束时，`_outer`
最后 drop。

### 3. `Rc<T>` shared ownership and strong counts / `Rc<T>` 共享所有权与强引用计数

**Question (English):** What is the complete output? Does `Rc::clone()` deeply
copy the `String`, and what happens when `second` leaves its scope?

**问题（中文）：** 完整输出是什么？`Rc::clone()` 是否会深拷贝 `String`？
`second` 离开作用域时会发生什么？

~~~rust
use std::rc::Rc;

fn main() {
    let first = Rc::new(String::from("GPU"));
    println!("{}", Rc::strong_count(&first));

    {
        let second = Rc::clone(&first);
        println!("{}", Rc::strong_count(&first));
        println!("{}", second);
    }

    println!("{}", Rc::strong_count(&first));
}
~~~

**Explanation (English):** `Rc<T>` provides non-atomic reference-counted
shared ownership within one thread. Cloning an `Rc` creates another handle to
the same allocation and increments the strong count. Dropping a handle
decrements the count; the stored value is dropped when the final strong owner
disappears.

**解说（中文）：** `Rc<T>` 在单线程内提供基于非原子引用计数的共享所有权。
clone 一个 `Rc` 会创建指向同一分配的新 handle，并增加强引用计数。handle drop
时计数减少；最后一个强所有者消失时，内部值才会 drop。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
1
2
GPU
1
~~~

**English:** `Rc::clone()` does not clone the `String`. When `second` is
dropped, the strong count falls from two to one. The allocation remains alive
because `first` is still an owner.

**中文：** `Rc::clone()` 不会 clone `String`。`second` drop 时，强引用计数从
2 降为 1。由于 `first` 仍是所有者，分配继续存活。

### 4. Why `Rc<T>` cannot cross thread boundaries / 为什么 `Rc<T>` 不能跨线程

**Question (English):** Does the program compile? If not, is the problem a
missing `move` keyword or the thread-safety properties of `Rc<T>`? Which type
should replace it?

**问题（中文）：** 程序能否编译？如果不能，问题是缺少 `move` 关键字，还是
`Rc<T>` 的线程安全属性？应该替换成什么类型？

~~~rust
use std::rc::Rc;
use std::thread;

fn main() {
    let value = Rc::new(String::from("GPU"));

    let handle = thread::spawn(move || {
        println!("{}", value);
    });

    handle.join().unwrap();
}
~~~

**Explanation (English):** The closure already uses `move`, so it attempts to
transfer ownership of the captured `Rc` into the new thread. `Rc` updates its
reference count non-atomically and therefore does not implement the required
cross-thread traits. Moving a value does not override its `Send` or `Sync`
properties.

**解说（中文）：** 闭包已经使用 `move`，因此它会尝试把捕获的 `Rc` 所有权转移
到新线程。`Rc` 使用非原子方式更新引用计数，所以没有实现所需的跨线程 trait。
移动一个值不会改变它是否实现 `Send` 或 `Sync`。

**Correct Answer (English):** The program does not compile because `Rc<String>`
is not safe to send between threads. The appropriate shared-ownership type is
`std::sync::Arc<String>`, whose reference-count updates are atomic.

**正确答案（中文）：** 程序不能编译，因为 `Rc<String>` 不能安全地在线程之间
传递。应使用 `std::sync::Arc<String>` 表示共享所有权；它以原子方式更新引用
计数。

### 5. `Arc<T>` ownership does not imply mutable access / `Arc<T>` 共享所有权不代表可变访问

**Question (English):** What is the complete output, including the two strong
counts? Can multiple threads directly mutate the same `String` through
`Arc<String>`? If not, what is normally added?

**问题（中文）：** 包括两个强引用计数在内，完整输出是什么？多个线程能否直接
通过 `Arc<String>` 修改同一个 `String`？如果不能，通常还要组合什么类型？

~~~rust
use std::sync::Arc;
use std::thread;

fn main() {
    let value = Arc::new(String::from("GPU"));
    let worker_value = Arc::clone(&value);

    let handle = thread::spawn(move || {
        println!("{}", worker_value);
        println!("{}", Arc::strong_count(&worker_value));
    });

    handle.join().unwrap();

    println!("{}", Arc::strong_count(&value));
}
~~~

**Explanation (English):** The main thread retains `value` while the worker
owns `worker_value`, so the worker observes two strong owners. Joining the
worker waits until its handle has been dropped, leaving only the main handle.
`Arc` solves thread-safe ownership, not mutation; its normal shared dereference
does not provide `&mut T`.

**解说（中文）：** 主线程保留 `value`，worker 拥有 `worker_value`，因此 worker
观察到两个强所有者。join 等待 worker 结束并 drop 它的 handle，之后只剩主线程
handle。`Arc` 解决线程安全的所有权问题，而不是可变性问题；普通共享解引用不会
提供 `&mut T`。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
GPU
2
1
~~~

**English:** Multiple threads cannot directly mutate the `String` through
ordinary shared `Arc` handles. Shared mutation is commonly expressed with
`Arc<Mutex<T>>`, or `Arc<RwLock<T>>` for workloads that benefit from multiple
concurrent readers.

**中文：** 多个线程不能通过普通的共享 `Arc` handle 直接修改 `String`。共享
可变状态通常使用 `Arc<Mutex<T>>`；需要多个并发 reader 的场景可以使用
`Arc<RwLock<T>>`。

### 6. Runtime borrow checking with `RefCell<T>` / 使用 `RefCell<T>` 进行运行时借用检查

**Question (English):** Does the program compile? If so, does it run normally
or fail at runtime? How does `RefCell<T>` differ from ordinary `&mut T` borrow
checking?

**问题（中文）：** 程序能否编译？如果能够，它会正常运行还是在运行时失败？
`RefCell<T>` 与普通 `&mut T` 的借用检查有何不同？

~~~rust
use std::cell::RefCell;

fn main() {
    let value = RefCell::new(42);

    let first = value.borrow_mut();
    let second = value.borrow_mut();

    println!("{} {}", first, second);
}
~~~

**Explanation (English):** `RefCell<T>` implements interior mutability by
tracking shared and mutable borrows at runtime. `borrow_mut()` returns a
`RefMut<T>` guard. While the first guard remains alive, a second mutable borrow
violates the same exclusivity rule that ordinary references enforce at compile
time.

**解说（中文）：** `RefCell<T>` 通过在运行时记录共享借用与可变借用，实现内部
可变性。`borrow_mut()` 返回 `RefMut<T>` guard。第一个 guard 仍然存活时，第二个
可变借用会违反普通引用在编译期执行的同一独占规则。

**Correct Answer (English):** The program compiles, but the second
`borrow_mut()` panics at runtime because the first mutable borrow is still
active. Ordinary `&mut T` conflicts are rejected by the compiler; `RefCell<T>`
defers those checks to runtime and is intended for single-threaded interior
mutability.

**正确答案（中文）：** 程序能够编译，但第二次 `borrow_mut()` 会在运行时 panic，
因为第一个可变借用仍然有效。普通 `&mut T` 冲突由编译器拒绝；`RefCell<T>` 把
检查推迟到运行时，适用于单线程内部可变性。

### 7. Single-threaded shared mutation with `Rc<RefCell<T>>` / 使用 `Rc<RefCell<T>>` 实现单线程共享可变性

**Question (English):** What does the program print? Is `Rc<RefCell<T>>`
suitable for mutable state shared among threads? What is the common
multi-threaded counterpart?

**问题（中文）：** 程序输出什么？`Rc<RefCell<T>>` 是否适合在线程之间共享可变
状态？常见的多线程对应组合是什么？

~~~rust
use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    let value = Rc::new(RefCell::new(1));

    let first = Rc::clone(&value);
    let second = Rc::clone(&value);

    *first.borrow_mut() += 1;
    *second.borrow_mut() += 2;

    println!("{}", value.borrow());
}
~~~

**Explanation (English):** `Rc` gives multiple single-threaded owners, while
`RefCell` gives runtime-checked mutation. Each temporary `RefMut` in this
example is dropped at the end of its statement, so the two mutable borrows do
not overlap. Neither the composition nor its borrow state is suitable for
cross-thread sharing.

**解说（中文）：** `Rc` 提供多个单线程所有者，`RefCell` 提供运行时检查的修改。
本例中每个临时 `RefMut` 都在所在语句结束时 drop，因此两次可变借用没有重叠。
这种组合及其借用状态都不适合跨线程共享。

**Correct Answer (English):** The program prints `4`. `Rc<RefCell<T>>` is a
single-threaded shared-mutation pattern. The common multi-threaded counterpart
is `Arc<Mutex<T>>`, or `Arc<RwLock<T>>` when read/write locking is appropriate.

**正确答案（中文）：** 程序输出 `4`。`Rc<RefCell<T>>` 是单线程共享可变模式。
常见的多线程对应组合是 `Arc<Mutex<T>>`；适合读写锁的场景可使用
`Arc<RwLock<T>>`。

### 8. RAII unlocking with `MutexGuard` / 使用 `MutexGuard` 进行 RAII 解锁

**Question (English):** What is the complete output? When is the mutex
unlocked, and is an explicit `unlock()` call required?

**问题（中文）：** 完整输出是什么？mutex 在什么时候解锁？是否需要显式调用
`unlock()`？

~~~rust
use std::sync::Mutex;

fn main() {
    let value = Mutex::new(1);

    {
        let mut guard = value.lock().unwrap();
        *guard += 1;
        println!("inside {}", *guard);
    }

    println!("outside {}", *value.lock().unwrap());
}
~~~

**Explanation (English):** `Mutex::lock()` returns a `MutexGuard`. The guard
provides access to the protected value and releases the lock through its `Drop`
implementation. Ending the inner scope drops `guard` before the second lock
attempt.

**解说（中文）：** `Mutex::lock()` 返回 `MutexGuard`。guard 提供对受保护值的
访问，并通过自身的 `Drop` 实现释放锁。内部作用域结束会在第二次加锁前 drop
`guard`。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

~~~text
inside 2
outside 2
~~~

**English:** No explicit unlock is needed. Leaving the scope drops the guard
and unlocks the mutex deterministically. The temporary guard created for the
outside print is likewise dropped at the end of that statement.

**中文：** 不需要显式 unlock。离开作用域会确定性地 drop guard 并解锁 mutex。
外部打印语句创建的临时 guard 同样会在该语句结束时 drop。

### 9. A shared counter with `Arc<Mutex<T>>` / 使用 `Arc<Mutex<T>>` 实现共享计数器

**Question (English):** What does the program print after joining all workers?
What roles do `Arc`, `Mutex`, and the `move` closure each play?

**问题（中文）：** join 全部 worker 后，程序输出什么？`Arc`、`Mutex` 与 `move`
闭包分别承担什么作用？

~~~rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = Vec::new();

    for _ in 0..4 {
        let worker_counter = Arc::clone(&counter);

        handles.push(thread::spawn(move || {
            let mut value = worker_counter.lock().unwrap();
            *value += 1;
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("{}", *counter.lock().unwrap());
}
~~~

**Explanation (English):** Each worker owns one cloned `Arc` handle. The
`move` closure transfers that handle into the new thread. `Mutex` serializes
mutable access to the shared integer, and joining all workers ensures every
increment has completed before the final read.

**解说（中文）：** 每个 worker 拥有一个 clone 得到的 `Arc` handle。`move` 闭包
把该 handle 转移进新线程；`Mutex` 串行化对共享整数的可变访问；join 全部 worker
保证最终读取前所有自增都已经完成。

**Correct Answer (English):** The program prints `4`. `Arc` supplies
thread-safe shared ownership, `Mutex` protects mutation, and `move` gives each
thread ownership of its own `Arc` handle. `Arc` makes its reference count
atomic; it does not make the protected integer itself an atomic integer.

**正确答案（中文）：** 程序输出 `4`。`Arc` 提供线程安全的共享所有权，`Mutex`
保护修改，`move` 让每个线程拥有自己的 `Arc` handle。`Arc` 使自身引用计数具备
原子性，并不会把受保护的整数本身变成原子整数。

### 10. Formal thread-safety boundaries with `Send` and `Sync` / 使用 `Send` 与 `Sync` 表达线程安全边界

**Question (English):** Which generic requirement compiles? What do `Send` and
`Sync` mean, and why do the two composed types differ?

**问题（中文）：** 哪一个泛型约束调用能够编译？`Send` 与 `Sync` 分别表示什么？
为什么两个组合类型不同？

~~~rust
use std::cell::RefCell;
use std::rc::Rc;
use std::sync::{Arc, Mutex};

fn require_send_and_sync<T: Send + Sync>() {}

fn main() {
    require_send_and_sync::<Arc<Mutex<i32>>>();
    require_send_and_sync::<Rc<RefCell<i32>>>();
}
~~~

**Explanation (English):** `Send` means ownership of a value can be transferred
safely to another thread. `Sync` means shared references to a value can be used
safely from multiple threads; equivalently, `&T` is `Send` when `T` is `Sync`.
These traits are normally derived automatically from the thread-safety
properties of a type's components.

**解说（中文）：** `Send` 表示一个值的所有权可以安全转移到另一个线程；`Sync`
表示多个线程可以安全使用同一个值的共享引用。等价地，当 `T` 是 `Sync` 时，
`&T` 是 `Send`。这些 trait 通常根据类型各组成部分的线程安全属性自动推导。

**Correct Answer (English):** `Arc<Mutex<i32>>` satisfies `Send + Sync` and
the first call compiles. The second call fails: `Rc` uses a non-atomic count and
is neither suitable for transfer nor shared cross-thread access, while
`RefCell`'s runtime borrow bookkeeping does not provide synchronized shared
access. Combining two single-threaded primitives does not create a
thread-safe type.

**正确答案（中文）：** `Arc<Mutex<i32>>` 满足 `Send + Sync`，第一个调用能够
编译。第二个调用失败：`Rc` 使用非原子计数，不适合在线程之间转移或共享；
`RefCell` 的运行时借用记录也没有提供同步的共享访问。组合两个单线程工具并不会
得到线程安全类型。

## Summary / 总结

- **English:** Moving a `Box<T>` transfers ownership without cloning the heap
  allocation, and the old binding cannot be reused.
  **中文：** 移动 `Box<T>` 会转移所有权而不 clone 堆分配，旧绑定不能继续使用。
- **English:** `Drop` provides deterministic cleanup at scope boundaries, with
  local values normally dropped in reverse declaration order.
  **中文：** `Drop` 在作用域边界提供确定性清理，局部值通常按照声明反序 drop。
- **English:** `Rc<T>` and `Arc<T>` both provide shared ownership, but only
  `Arc<T>` uses an atomic count suitable for cross-thread composition.
  **中文：** `Rc<T>` 与 `Arc<T>` 都提供共享所有权，但只有 `Arc<T>` 使用适合
  跨线程组合的原子计数。
- **English:** Shared ownership does not automatically grant mutable access;
  ownership and mutation must be designed separately.
  **中文：** 共享所有权不会自动赋予可变访问；所有权与修改方式必须分别设计。
- **English:** `RefCell<T>` enforces borrowing dynamically for single-threaded
  interior mutability, while `Mutex<T>` synchronizes mutation across threads.
  **中文：** `RefCell<T>` 为单线程内部可变性动态执行借用规则，`Mutex<T>` 则
  在线程之间同步修改。
- **English:** `RefMut` and `MutexGuard` encode access rights in guard
  lifetimes and release those rights through `Drop`.
  **中文：** `RefMut` 与 `MutexGuard` 把访问权限编码在 guard 生命周期中，并通过
  `Drop` 释放权限。
- **English:** `Arc<Mutex<T>>` combines thread-safe shared ownership with
  mutually exclusive mutation.
  **中文：** `Arc<Mutex<T>>` 组合了线程安全的共享所有权与互斥修改。
- **English:** `Send` and `Sync` formalize whether ownership or shared
  references may cross thread boundaries safely.
  **中文：** `Send` 与 `Sync` 形式化描述所有权或共享引用能否安全跨越线程边界。

## Common Mistakes / 常见错误

- **English:** Assuming a Rust move clones the heap allocation owned by a
  `Box<T>`.
  **中文：** 误以为 Rust move 会 clone `Box<T>` 拥有的堆分配。
- **English:** Omitting the `drop ` prefix when predicting output produced by
  a custom `Drop` implementation.
  **中文：** 推导自定义 `Drop` 输出时漏掉实现中打印的 `drop ` 前缀。
- **English:** Treating `Rc::clone()` as a deep clone rather than a new shared
  owner.
  **中文：** 把 `Rc::clone()` 当成深拷贝，而不是创建新的共享所有者。
- **English:** Assuming a `move` closure can make an `Rc<T>` safe to send to a
  thread.
  **中文：** 误以为 `move` 闭包能够让 `Rc<T>` 变得可以安全跨线程传递。
- **English:** Reversing `Arc` strong-count transitions around worker creation
  and completion.
  **中文：** 混淆 worker 创建与结束前后的 `Arc` 强引用计数变化。
- **English:** Assuming `Arc<T>` alone permits direct concurrent mutation of
  `T`.
  **中文：** 误以为仅使用 `Arc<T>` 就能直接并发修改 `T`。
- **English:** Expecting conflicting `RefCell<T>` borrows to be compile-time
  errors rather than runtime panics.
  **中文：** 误以为冲突的 `RefCell<T>` 借用会产生编译错误，而不是运行时 panic。
- **English:** Treating `Rc<RefCell<T>>` as a cross-thread shared-mutation
  pattern.
  **中文：** 把 `Rc<RefCell<T>>` 当成跨线程共享可变模式。
- **English:** Describing `Arc` as making the stored value atomic rather than
  making reference-count updates atomic.
  **中文：** 误以为 `Arc` 会让内部值具备原子性，而不是仅让引用计数更新具备
  原子性。
- **English:** Memorizing `Send` and `Sync` type lists without understanding
  their ownership-transfer and shared-reference meanings.
  **中文：** 只记忆哪些类型实现 `Send` 与 `Sync`，却不理解它们分别对应所有权
  转移和共享引用的含义。

## Next Steps / 下一步建议

1. **English:** Study how the compiler automatically derives or rejects
   `Send` and `Sync`, including examples with raw pointers and custom types.
   **中文：** 学习编译器如何自动推导或拒绝 `Send` 与 `Sync`，包括裸指针与自定义
   类型示例。
2. **English:** Compare `Cell<T>`, `RefCell<T>`, `Mutex<T>`, and `RwLock<T>`
   through small mutation experiments.
   **中文：** 通过小型修改实验对比 `Cell<T>`、`RefCell<T>`、`Mutex<T>` 与
   `RwLock<T>`。
3. **English:** Build an `Rc` ownership cycle, observe why it leaks, and break
   the cycle with `Weak<T>`.
   **中文：** 构造一个 `Rc` 所有权循环，观察它为什么泄漏，再使用 `Weak<T>`
   打破循环。
4. **English:** Compare shared-state concurrency with `std::sync::mpsc`
   channels and ownership transfer through messages.
   **中文：** 对比共享状态并发与 `std::sync::mpsc` channel，理解通过消息转移
   所有权。
5. **English:** Apply `Arc<Mutex<T>>` or channels to a small inference-worker
   queue, then inspect contention and shutdown behavior.
   **中文：** 在小型推理 worker queue 中应用 `Arc<Mutex<T>>` 或 channel，并观察
   锁竞争与关闭行为。
