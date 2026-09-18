# Day 042: Rust Thread Ownership and Lifetimes / Rust 线程所有权与生命周期

Date / 日期: 2026-09-18

**English:** This session began on September 17 and finished on September 18, 2026, in the Asia/Shanghai time zone.

**中文：** 本次学习于北京时间 2026 年 9 月 17 日开始，9 月 18 日完成。

## Topic / 主题

**English:** Closure captures, ownership transfer through threads, the 'static bound, scoped threads, Send and Sync, Rc and Arc, shared mutation with Mutex, and parallel processing of disjoint slices.

**中文：** 闭包捕获、通过线程转移所有权、'static 约束、作用域线程、Send 与 Sync、Rc 与 Arc、使用 Mutex 共享修改，以及不重叠切片的并行处理。

## Goal / 目标

**English:** Explain which values and references may enter a thread, who owns the data during execution, and when the caller can safely use it again. Apply these ideas to the ownership choices behind inference workers and batch processing.

**中文：** 解释哪些值和引用可以进入线程、执行期间由谁拥有数据，以及调用方何时可以再次安全使用数据。把这些概念用于理解推理 worker 与批处理中的所有权设计。

## 10 Concept Questions / 10 个概念问题

### 1. Borrowing local data with spawn / 使用 spawn 借用局部数据

**Question (English):** Does this code compile? Is immediately calling join enough to let the thread borrow data safely?

**问题（中文）：** 这段代码能否编译？立即调用 join 是否足以让线程安全地借用 data？

```rust
use std::thread;

fn main() {
    let data = vec![10, 20, 30];

    let handle = thread::spawn(|| {
        println!("{data:?}");
    });

    handle.join().unwrap();
}
```

**Explanation (English):** The closure borrows the local vector. thread::spawn requires its closure to satisfy Send + 'static because the API allows the new thread to outlive the caller. Calling join afterward does not change those requirements at the spawn call.

**解说（中文）：** 闭包借用了局部 vector。thread::spawn 要求闭包满足 Send + 'static，因为该接口允许新线程比调用方存活更久。之后调用 join 不会改变 spawn 调用处的这些要求。

**Correct Answer (English):** It does not compile. Adding move to this closure transfers ownership of the Vec into the thread and fixes this example. A move capture is not mandatory for every spawn call; the captured values must satisfy the actual type and lifetime bounds.

**正确答案（中文）：** 不能编译。给这里的闭包加上 move，会把 Vec 的所有权转移进线程，从而修复本例。并不是每次调用 spawn 都必须写 move；实际要求是捕获的值满足相应类型与生命周期约束。

### 2. Using a vector after moving it / 移动 vector 后再次使用

**Question (English):** Does this code compile? Can the caller use data again after join returns?

**问题（中文）：** 这段代码能否编译？join 返回后，调用方能否再次使用 data？

```rust
use std::thread;

fn main() {
    let data = vec![10, 20, 30];

    let handle = thread::spawn(move || {
        println!("{data:?}");
    });

    handle.join().unwrap();

    println!("{data:?}");
}
```

**Explanation (English):** The move closure owns the vector. Vec is not Copy, so the original binding cannot be used after this transfer. Waiting for the thread does not restore ownership to that binding.

**解说（中文）：** move 闭包拥有了 vector。Vec 没有实现 Copy，因此转移后不能再使用原绑定。等待线程结束不会把所有权恢复给该绑定。

**Correct Answer (English):** It does not compile because the final print uses a moved value. This closure returns (), so join returns Ok(()) on success and join().unwrap() yields (). Returning the vector explicitly is one way to transfer it back.

**正确答案（中文）：** 不能编译，因为最后的打印使用了已被移动的值。这个闭包返回 ()，因此 join 成功时返回 Ok(())，join().unwrap() 得到 ()。显式返回 vector 是把所有权交回调用方的一种方式。

### 3. Returning ownership through join / 通过 join 返回所有权

**Question (English):** Does this code compile? Does returned receive a deep copy or ownership of the original Vec?

**问题（中文）：** 这段代码能否编译？returned 得到的是深拷贝，还是原来那个 Vec 的所有权？

```rust
use std::thread;

fn main() {
    let data = vec![10, 20, 30];

    let handle = thread::spawn(move || {
        println!("{data:?}");
        data
    });

    let returned = handle.join().unwrap();

    println!("{returned:?}");
}
```

**Explanation (English):** The final data expression is the closure's return value. The successful join result carries that value back to the caller; unwrap extracts it from the Result. The vector's ownership crosses the thread boundary in both directions without cloning its elements.

**解说（中文）：** 末尾的 data 表达式是闭包的返回值。成功的 join 结果把这个值带回调用方，unwrap 再从 Result 中取出它。vector 的所有权先后两次跨越线程边界，没有 clone 其中的元素。

**Correct Answer (English):** It compiles. returned owns the original Vec, and the program prints [10, 20, 30] twice. Moving the vector transfers ownership of its allocation without deep-copying the stored elements.

**正确答案（中文）：** 可以编译。returned 拥有原来的 Vec，程序两次输出 [10, 20, 30]。移动 vector 会转移其分配的所有权，不会深拷贝存储的元素。

### 4. Capturing a reference with move / 使用 move 捕获引用

**Question (English):** Does this code compile? Does move capture the Vec itself or the borrowed reference?

**问题（中文）：** 这段代码能否编译？move 捕获的是 Vec 本身，还是 borrowed 这个引用？

```rust
use std::thread;

fn main() {
    let data = vec![10, 20, 30];
    let borrowed = &data;

    let handle = thread::spawn(move || {
        println!("{borrowed:?}");
    });

    handle.join().unwrap();
}
```

**Explanation (English):** A move closure captures the value of borrowed, whose type is `&Vec<i32>`. Shared references implement Copy, so this capture copies the reference; it does not move ownership of the Vec. Capturing a reference by value does not extend the referent's lifetime.

**解说（中文）：** move 闭包按值捕获 borrowed，其类型是 `&Vec<i32>`。共享引用实现了 Copy，因此这里复制的是引用，不会移动 Vec 的所有权。按值捕获引用不会延长被引用数据的生命周期。

**Correct Answer (English):** It does not compile. The closure still depends on a reference to the local data, which cannot satisfy spawn's 'static bound. Ownership of the vector remains with the caller.

**正确答案（中文）：** 不能编译。闭包仍依赖指向局部 data 的引用，无法满足 spawn 的 'static 约束。vector 的所有权仍属于调用方。

### 5. Borrowing through scoped threads / 通过作用域线程借用

**Question (English):** Does this code compile? What guarantee from scope allows its thread to borrow local data?

**问题（中文）：** 这段代码能否编译？scope 提供了什么保证，使其中的线程可以借用局部数据？

```rust
use std::thread;

fn main() {
    let data = vec![10, 20, 30];
    let borrowed = &data;

    thread::scope(|s| {
        s.spawn(move || {
            println!("{borrowed:?}");
        });
    });

    println!("{data:?}");
}
```

**Explanation (English):** scope ensures that all threads spawned through its Scope are joined before it returns. A child may finish earlier; scope waits for any children that have not been manually joined. Local data that outlives the scope can therefore be borrowed by those threads.

**解说（中文）：** scope 保证通过其 Scope 创建的所有线程都被 join 后才返回。子线程可以提前结束；scope 会等待所有尚未手动 join 的子线程。因此，这些线程可以借用存活时间覆盖整个 scope 的局部数据。

**Correct Answer (English):** It compiles and prints [10, 20, 30] twice. The worker only receives a reference, so data remains owned by the caller. The worker finishes before scope returns, while data is still alive; the caller then prints data safely.

**正确答案（中文）：** 可以编译，两次输出 [10, 20, 30]。worker 只接收引用，因此 data 的所有权仍属于调用方。worker 在 scope 返回前结束，此时 data 仍然存活；随后调用方可以安全地打印 data。

### 6. Moving Rc across a thread boundary / 跨线程移动 Rc

**Question (English):** Does this code compile? Is owning an Rc through a move capture sufficient to send it to another thread?

**问题（中文）：** 这段代码能否编译？通过 move 捕获并拥有一个 Rc，是否就足以把它交给另一个线程？

```rust
use std::rc::Rc;
use std::thread;

fn main() {
    let data = Rc::new(vec![10, 20, 30]);

    let handle = thread::spawn(move || {
        println!("{data:?}");
    });

    handle.join().unwrap();
}
```

**Explanation (English):** spawn also requires the closure to implement Send. Rc uses a non-atomic reference count and does not implement Send. Moving a value into a closure does not change its thread-safety traits, and the compiler checks those traits even when this example has only one Rc owner.

**解说（中文）：** spawn 还要求闭包实现 Send。Rc 使用非原子引用计数，没有实现 Send。把值移动进闭包不会改变其线程安全 trait，即使本例只有一个 Rc 所有者，编译器仍会检查这些 trait。

**Correct Answer (English):** It does not compile. The captured `Rc<Vec<i32>>` prevents the closure from satisfying Send. Non-atomic updates could race if multiple Rc owners of the same allocation were allowed to operate across threads.

**正确答案（中文）：** 不能编译。捕获的 `Rc<Vec<i32>>` 使闭包无法满足 Send。如果允许同一分配的多个 Rc 所有者跨线程操作，非原子的引用计数更新就可能发生竞争。

### 7. Sharing a vector with Arc / 使用 Arc 共享 vector

**Question (English):** Does this code compile? Does Arc::clone deeply copy the Vec or let both threads share the same data?

**问题（中文）：** 这段代码能否编译？Arc::clone 会深拷贝 Vec，还是让两个线程共享同一份数据？

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(vec![10, 20, 30]);
    let worker_data = Arc::clone(&data);

    let handle = thread::spawn(move || {
        println!("{worker_data:?}");
    });

    println!("{data:?}");
    handle.join().unwrap();
}
```

**Explanation (English):** Arc::clone creates another shared owner by increasing the atomic strong reference count. It does not clone the stored vector. `Vec<i32>` satisfies Send and Sync, so this Arc may cross the thread boundary and both threads may read the same vector.

**解说（中文）：** Arc::clone 通过增加原子的强引用计数，创建另一个共享所有者，不会 clone 内部 vector。`Vec<i32>` 满足 Send 与 Sync，因此这个 Arc 可以跨越线程边界，两个线程也可以读取同一个 vector。

**Correct Answer (English):** It compiles and prints [10, 20, 30] twice. Both Arc values own the same allocation. The two print calls have no guaranteed relative order, but their contents are identical.

**正确答案（中文）：** 可以编译，两次输出 [10, 20, 30]。两个 Arc 值共同拥有同一份分配。两次打印没有保证的先后顺序，但内容相同。

### 8. Combining Arc with RefCell / 组合 Arc 与 RefCell

**Question (English):** Does this code compile? Are Arc's atomic reference count and RefCell's runtime borrow checks sufficient for cross-thread shared mutation?

**问题（中文）：** 这段代码能否编译？Arc 的原子引用计数与 RefCell 的运行时借用检查，是否足以支持跨线程共享修改？

```rust
use std::cell::RefCell;
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(RefCell::new(vec![10, 20, 30]));
    let worker_data = Arc::clone(&data);

    let handle = thread::spawn(move || {
        worker_data.borrow_mut().push(40);
    });

    handle.join().unwrap();
    println!("{:?}", data.borrow());
}
```

**Explanation (English):** Send permits transferring a value to another thread. Sync means a shared reference &T can be sent to another thread. RefCell's borrow state has no cross-thread synchronization, so `RefCell<T>` is not Sync. Arc protects its reference count, not RefCell's internal borrow state.

**解说（中文）：** Send 允许把值转移到另一个线程。Sync 表示共享引用 &T 可以发送到另一个线程。RefCell 的借用状态没有跨线程同步，因此 `RefCell<T>` 不满足 Sync。Arc 保护的是自己的引用计数，不是 RefCell 内部的借用状态。

**Correct Answer (English):** It does not compile. Although `RefCell<Vec<i32>>` is Send, it is not Sync; `Arc<RefCell<Vec<i32>>>` therefore does not satisfy Send. Waiting before the caller's read does not remove spawn's type bounds. A Mutex can provide synchronized access for this shared vector.

**正确答案（中文）：** 不能编译。虽然 `RefCell<Vec<i32>>` 满足 Send，但它不满足 Sync，因此 `Arc<RefCell<Vec<i32>>>` 不满足 Send。调用方先等待再读取，也不会取消 spawn 的类型约束。Mutex 可以为这个共享 vector 提供同步访问。

### 9. Shared mutation with Mutex / 使用 Mutex 共享修改

**Question (English):** Does this code compile? When is the lock acquired by the worker released?

**问题（中文）：** 这段代码能否编译？worker 取得的锁会在什么时候释放？

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let data = Arc::new(Mutex::new(vec![10, 20, 30]));
    let worker_data = Arc::clone(&data);

    let handle = thread::spawn(move || {
        let mut guard = worker_data.lock().unwrap();
        guard.push(40);
    });

    handle.join().unwrap();
    println!("{:?}", data.lock().unwrap());
}
```

**Explanation (English):** Arc supplies shared ownership, while Mutex serializes access to the protected vector. A successful lock call returns a MutexGuard, and dropping that guard releases the lock. The guard remains alive until its drop point, even after its last use; drop(guard) can release it explicitly before the end of its scope.

**解说（中文）：** Arc 提供共享所有权，Mutex 则串行化对受保护 vector 的访问。成功调用 lock 会返回 MutexGuard，销毁这个 guard 就会释放锁。即使已完成最后一次使用，guard 仍会存活到其销毁位置；使用 drop(guard) 可以在作用域结束前显式释放锁。

**Correct Answer (English):** It compiles and prints [10, 20, 30, 40]. In this program the worker's guard is dropped when its closure body ends, releasing the lock. After join succeeds, the caller acquires the lock and reads the updated vector.

**正确答案（中文）：** 可以编译，输出 [10, 20, 30, 40]。本例中，worker 的 guard 在闭包体结束时被销毁，从而释放锁。join 成功后，调用方取得锁并读取更新后的 vector。

### 10. Parallel updates to disjoint chunks / 并行更新不重叠的数据块

**Question (English):** Does this program need an additional Mutex? Why can the caller read the whole vector after scope returns? chunks_mut(2) yields non-overlapping mutable slices with at most two elements each.

**问题（中文）：** 这段程序是否需要额外的 Mutex？为什么 scope 返回后，调用方可以读取整个 vector？chunks_mut(2) 会返回互不重叠的可变切片，每片最多两个元素。

```rust
use std::thread;

fn main() {
    let mut data = vec![10, 20, 30, 40];

    thread::scope(|s| {
        for chunk in data.chunks_mut(2) {
            s.spawn(move || {
                for value in chunk {
                    *value *= 2;
                }
            });
        }
    });

    println!("{data:?}");
}
```

**Explanation (English):** Each thread receives exclusive access to a different region through its mutable slice. The elements are not copied, and the caller retains ownership of the vector. Region separation prevents conflicting accesses between workers; scoped completion ensures their accesses finish before the caller reads the whole vector.

**解说（中文）：** 每个线程通过自己的可变切片，独占访问不同的数据区域。元素没有被复制，vector 的所有权仍由调用方持有。区域分离防止 worker 之间发生访问冲突；作用域线程完成机制则保证它们的访问结束后，调用方才读取整个 vector。

**Correct Answer (English):** No mutex is needed. It compiles and prints [20, 40, 60, 80]. Disjoint slices make the parallel writes safe, and scope waits for all its workers before returning. Completion alone would not make overlapping unsynchronized writes safe; exclusive regions and the completion guarantee serve different purposes.

**正确答案（中文）：** 不需要互斥锁。可以编译，输出 [20, 40, 60, 80]。不重叠切片保证并行写入安全，scope 则在返回前等待所有 worker。单纯等待完成并不能让重叠区域上的无同步写入变得安全；区域独占与完成保证分别承担不同职责。

## Additional Clarifications / 补充讲解

### The meaning of the 'static bound / 'static 约束的含义

**English:** A T: 'static bound does not require a value to remain alive until the program exits. It means the type does not carry a borrow restricted to a shorter lifetime. An owned `Vec<i32>` can satisfy this bound and still be dropped when its owner finishes using it. In contrast, a reference to a local vector cannot become 'static merely by being captured with move.

**中文：** T: 'static 约束不要求某个值一直存活到程序退出。它表示该类型不携带受较短生命周期限制的借用。拥有所有权的 `Vec<i32>` 可以满足这个约束，并且仍可在所有者使用完毕后被销毁。相反，指向局部 vector 的引用不会仅因被 move 捕获就变成 'static。

## Summary / 总结

**English:** The session connected ownership moves, reference captures, thread completion, and shared-state access. Returning a Vec through join transfers ownership back; Arc::clone instead creates another owner of the same data. Rc and `Arc<RefCell<_>>` fail different thread-safety requirements, while `Arc<Mutex<_>>` supports synchronized shared mutation in the example.

**中文：** 本次学习把所有权移动、引用捕获、线程完成与共享状态访问联系起来。通过 join 返回 Vec 会交回所有权；Arc::clone 则为同一份数据创建另一个所有者。Rc 与 `Arc<RefCell<_>>` 分别无法满足相应的线程安全要求，而示例中的 `Arc<Mutex<_>>` 支持带同步的共享修改。

**English:** The important timing rule is that scope returns only after its scoped threads are joined. Disjoint regions remove the need for a mutex in the final example; scoped completion makes the later whole-vector read safe. Further practice should explain Send, Sync, and 'static in words rather than relying only on compilation predictions.

**中文：** 关键的时间顺序是 scope 在其作用域线程全部被 join 后才返回。最后一个示例中，不重叠区域消除了对互斥锁的需求；作用域线程完成则保证后续读取整个 vector 的安全。后续应练习用语言解释 Send、Sync 与 'static，而不只是判断能否编译。

## Common Mistakes / 常见错误

- Assuming an immediate join relaxes spawn's bounds / 认为立即 join 就能放宽 spawn 的约束
- Expecting join to automatically restore the original binding's ownership / 认为 join 会自动恢复原绑定的所有权
- Treating a move capture of a reference as a move of its referent / 把 move 捕获引用当作移动被引用数据
- Interpreting 'static as requiring a value to live forever / 把 'static 理解为要求某个值永久存活
- Reversing the completion order: scoped threads finish before scope returns / 颠倒结束顺序；正确顺序是作用域线程先结束，scope 再返回
- Assuming Arc makes all operations on its inner value thread-safe / 认为 Arc 会让内部值的所有操作都具备线程安全性
- Equating a guard's last use with releasing its mutex / 把 guard 的最后一次使用等同于释放互斥锁
- Relying on completion alone while overlooking overlapping writes / 只关注等待完成，忽略写入区域是否重叠

## Next Steps / 下一步建议

1. Study std::sync::mpsc with a small worker that receives an input batch and sends back a result, tracking ownership at each send and receive. / 使用 std::sync::mpsc 实现接收输入 batch 并发回结果的小型 worker，追踪每次发送与接收时的所有权变化。
2. Compare transferring a whole batch, borrowing disjoint slices inside scope, and sharing mutable state through `Arc<Mutex<_>>`. Explain the lifetime and synchronization requirements for each choice. / 比较转移整个 batch、在 scope 中借用不重叠切片，以及通过 `Arc<Mutex<_>>` 共享可变状态，并解释各自的生命周期与同步要求。
3. Relate these CPU ownership patterns to GPU buffer management in a later lesson, separately checking device completion and the CUDA API's resource-lifetime contract. / 在后续课程中把这些 CPU 所有权模式与 GPU buffer 管理联系起来，另外检查设备执行完成时机及 CUDA API 的资源生命周期约定。

## Further Reading / 延伸阅读

- [Thread spawning and its bounds / 线程创建及其约束](https://doc.rust-lang.org/std/thread/fn.spawn.html)
- [Scoped threads / 作用域线程](https://doc.rust-lang.org/std/thread/fn.scope.html)
- [Arc and thread safety / Arc 与线程安全](https://doc.rust-lang.org/std/sync/struct.Arc.html)
- [RefCell / RefCell 文档](https://doc.rust-lang.org/std/cell/struct.RefCell.html)
- [MutexGuard and lock release / MutexGuard 与锁释放](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html)

## Validation / 验证

**English:** All ten programs were compiled with Rust 2024 using rustc 1.100.0-nightly (215a8af4b 2026-09-15). Questions 1, 2, and 4 failed with E0373, E0382, and E0597 respectively; questions 6 and 8 failed with E0277. Questions 3, 5, 7, 9, and 10 compiled and ran successfully, with output matching the answers above. Validation used temporary files outside the repository.

**中文：** 使用 rustc 1.100.0-nightly (215a8af4b 2026-09-15)，以 Rust 2024 编译了全部 10 段程序。第 1、2、4 题分别产生 E0373、E0382、E0597；第 6、8 题产生 E0277。第 3、5、7、9、10 题均编译并运行成功，输出与上述答案一致。验证使用仓库外的临时文件。

**English:** The repository's bilingual documentation checker passed for all 64 Markdown files, and all seven checker unit tests passed. The documentation validation commands are:

**中文：** 仓库双语文档检查器检查的全部 64 个 Markdown 文件通过，全部 7 个检查器单元测试通过。文档验证命令如下：

```bash
python3 scripts/check_bilingual_docs.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git diff --check
```
