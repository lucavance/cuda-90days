# Day 041: Rust Borrowing, Slices, and Safe Parallelism / Rust 借用、切片与安全并行

Date / 日期: 2026-09-17

**English:** This session began on September 16 and finished on September 17, 2026, in the Asia/Shanghai time zone. The CUDA–Rust overview records the research snapshot from September 16.

**中文：** 本次学习于北京时间 2026 年 9 月 16 日开始，9 月 17 日完成。CUDA–Rust 概览记录的是 9 月 16 日调研时的情况。

## Topic / 主题

**English:** Mutable bindings and references, reference patterns, IndexMut, non-lexical lifetimes, disjoint slices, mutable iterators, vector reallocation, and scoped threads.

**中文：** 可变绑定与可变引用、引用模式、IndexMut、非词法生命周期、互不重叠的切片、可变迭代器、vector 重新分配与作用域线程。

## Goal / 目标

**English:** Distinguish changing a binding from changing its referent, track borrows through the last use of references, and explain when mutable references can coexist. Connect these rules to ownership in parallel systems and Rust GPU programming.

**中文：** 区分修改绑定与修改引用指向的数据，依据引用的最后一次使用追踪借用，并解释多个可变引用何时能够共存。把这些规则与并行系统和 Rust GPU 编程中的所有权联系起来。

## CUDA–Rust Research Snapshot / CUDA–Rust 调研快照

**English:** On September 8, 2026, NVIDIA introduced two native Rust kernel tracks: SIMT through cuda-oxide and tile programming through cutile-rs. The announcement described both as early-stage and not yet production-ready. See the [NVIDIA announcement](https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/).

**中文：** 2026 年 9 月 8 日，NVIDIA 介绍了两条原生 Rust kernel 路线：通过 cuda-oxide 进行 SIMT 编程，以及通过 cutile-rs 进行 tile 编程。公告指出两者仍处于早期阶段，尚未达到生产就绪状态。参见 [NVIDIA 公告](https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/)。

- [cuda-oxide](https://github.com/NVlabs/cuda-oxide): compiles Rust kernels to PTX with a custom backend; alpha software using a pinned nightly toolchain. / 使用自定义后端把 Rust kernel 编译为 PTX；处于 Alpha 阶段，使用固定版本的 nightly 工具链。
- [cutile-rs](https://github.com/NVlabs/cutile-rs): a tile-oriented Rust kernel DSL using stable Rust, with ownership-based tensor partitioning. / 使用 stable Rust 的 tile kernel DSL，以所有权和张量分区约束访问。
- [cudarc 0.19.9](https://docs.rs/crate/cudarc/0.19.9): the latest release found in this research, dated August 11, 2026; host-side CUDA bindings for buffers, launches, and libraries, rather than a Rust-to-PTX compiler. / 本次调研查到的最新版本，发布于 2026 年 8 月 11 日；提供 buffer、kernel 启动与 CUDA 库调用的主机端绑定，不是 Rust 到 PTX 的编译器。
- [Rust-GPU/rust-cuda](https://github.com/Rust-GPU/Rust-CUDA): the community project states that development has restarted and remains at an early stage. / 社区项目明确表示已重启开发，目前仍处于早期阶段。

**English:** The lesson uses ordinary CPU Rust examples to build an ownership model. These examples do not validate GPU kernels or an arbitrary CUDA API's safety.

**中文：** 本课程使用普通 CPU Rust 示例建立所有权模型。这些示例并未验证 GPU kernel，也不能证明任意 CUDA API 的安全性。

## Core Mental Model / 核心思维模型

**English:** Mutable access must be exclusive for the data being accessed. Disjoint regions can have separate mutable references simultaneously. Reading through a reference still uses its borrow; in these straight-line examples, a borrow can end after the reference's last use. A copied integer does not retain a borrow of its source.

**中文：** 可变访问要求对所访问的数据拥有独占权限。互不重叠的区域可以同时拥有各自的可变引用。通过引用读取仍属于使用借用；在这些直线执行示例中，借用可以在引用最后一次使用后结束。复制出来的整数不会继续借用其来源。

## 10 Concept Questions / 10 个概念问题

### 1. Two mutable vector indexes / 两次可变 vector 索引

**Question (English):** Does this code compile? Is selecting different elements enough for the borrow checker to accept these two mutable references?

**问题（中文）：** 这段代码能否编译？选择不同元素是否足以让借用检查器接受这两个可变引用？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let left = &mut data[0];
    let right = &mut data[1];

    *left += 1;
    *right += 1;

    println!("{data:?}");
}
```

**Explanation (English):** Mutable vector indexing uses IndexMut, which borrows the container through `&mut self` and returns a reference tied to that borrow. Independent indexing calls do not establish disjointness for the borrow checker.

**解说（中文）：** 对 vector 进行可变索引会使用 IndexMut，通过 `&mut self` 借用容器，并返回与该借用关联的引用。独立的索引调用不会为借用检查器建立不重叠证明。

**Correct Answer (English):** It does not compile (E0499). The later use of left keeps the first borrow active when right requests another mutable borrow of data. For this `Vec<i32>`, indexes 0 and 1 really do select different elements; the error concerns the borrowing interface, not the vector returning the same element.

**正确答案（中文）：** 不能编译（E0499）。后面仍要使用 left，所以 right 请求再次可变借用 data 时，第一次借用必须继续有效。对于这个 `Vec<i32>`，索引 0 和 1 确实对应不同元素；错误来自借用接口，而不是 vector 返回了同一个元素。

### 2. Last use before the next borrow / 下一次借用前的最后一次使用

**Question (English):** Does the reordered code compile? Must left's borrow remain active when right is created?

**问题（中文）：** 调整顺序后的代码能否编译？创建 right 时，left 的借用是否仍然必须保持有效？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let left = &mut data[0];
    *left += 1;

    let right = &mut data[1];
    *right += 1;

    println!("{data:?}");
}
```

**Explanation (English):** Non-lexical lifetimes allow a borrow to end after the reference's last use. The binding's name can remain in lexical scope without requiring its borrow to stay active.

**解说（中文）：** 非词法生命周期允许借用在引用最后一次使用后结束。绑定的变量名仍在词法作用域中，并不要求其借用继续有效。

**Correct Answer (English):** It compiles and prints [11, 21, 30, 40]. The last use of left occurs before right is created, so their borrows do not overlap. The last use of right also precedes the final shared access to data.

**正确答案（中文）：** 可以编译，输出 [11, 21, 30, 40]。left 的最后一次使用早于 right 的创建，所以两个借用不重叠。right 的最后一次使用也早于最后对 data 的共享访问。

### 3. A later read still extends the borrow / 后续读取仍会延续借用

**Question (English):** Does this code compile after adding a final read through left? Does reading instead of writing remove the conflict?

**问题（中文）：** 增加末尾通过 left 的读取后，代码还能编译吗？只读而不写能否消除冲突？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let left = &mut data[0];
    *left += 1;

    let right = &mut data[1];
    *right += 1;

    println!("left = {left}");
}
```

**Explanation (English):** Reading through a reference still requires that reference to be valid. A later read keeps the associated borrow needed across intervening statements.

**解说（中文）：** 通过引用读取仍要求引用有效。后续读取会让对应借用必须跨越中间语句继续存在。

**Correct Answer (English):** It does not compile (E0499). The final println! is now left's last use, so its borrow overlaps the creation of right. A read through left does not retroactively remove the original mutable borrow.

**正确答案（中文）：** 不能编译（E0499）。最后的 println! 变成了 left 的最后一次使用，所以其借用与创建 right 发生重叠。通过 left 读取不会追溯地消除原来的可变借用。

### 4. Copying a value out of a reference / 从引用中复制值

**Question (English):** Does this code compile? How does printing saved differ from printing left?

**问题（中文）：** 这段代码能否编译？打印 saved 与打印 left 有什么区别？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let left = &mut data[0];
    *left += 1;
    let saved = *left;

    let right = &mut data[1];
    *right += 1;

    println!("saved = {saved}");
}
```

**Explanation (English):** i32 implements Copy. Copying *left into a new integer binding does not give that binding a reference or lifetime relationship to data.

**解说（中文）：** i32 实现了 Copy。把 *left 复制进新的整数绑定，不会使新绑定携带对 data 的引用或生命周期关系。

**Correct Answer (English):** It compiles and prints saved = 11. saved has type i32 and holds an independent copy. The copy is left's last use, so the borrow can end before right is created. Keeping another reference instead of an integer copy would preserve a borrowing relationship.

**正确答案（中文）：** 可以编译，输出 saved = 11。saved 的类型是 i32，持有独立副本。复制是 left 的最后一次使用，其借用可以在创建 right 前结束。如果保留的是另一个引用而非整数副本，借用关系就仍然存在。

### 5. Disjoint slices with split_at_mut / 使用 split_at_mut 获得不重叠切片

**Question (English):** What does this code print? Why can left and right exist as mutable slices at the same time?

**问题（中文）：** 这段代码输出什么？为什么 left 和 right 两个可变切片可以同时存在？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let (left, right) = data.split_at_mut(2);

    left[0] += 1;
    right[0] += 1;

    println!("{data:?}");
}
```

**Explanation (English):** split_at_mut(mid) borrows a slice once and returns two non-overlapping mutable slices: the elements before mid, and the elements starting at mid. Its implementation guarantees that the regions are disjoint.

**解说（中文）：** split_at_mut(mid) 对切片进行一次借用，返回两个不重叠的可变切片：mid 之前的元素，以及从 mid 开始的元素。其实现保证两个区域互不重叠。

**Correct Answer (English):** It compiles and prints [11, 20, 31, 40]. left initially covers [10, 20], and right covers [30, 40]. Both have type `&mut [i32]`; no elements are copied. Exclusivity applies to each region, so these disjoint mutable references may coexist.

**正确答案（中文）：** 可以编译，输出 [11, 20, 31, 40]。left 最初覆盖 [10, 20]，right 覆盖 [30, 40]。两者的类型都是 `&mut [i32]`，没有复制元素。独占要求针对各自的区域，因此这些不重叠的可变引用可以共存。

### 6. Reading the vector during a slice borrow / 切片借用期间读取 vector

**Question (English):** Does this code compile when data is printed before the final use of right?

**问题（中文）：** 在 right 的最后一次使用之前打印 data，这段代码能否编译？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let (left, right) = data.split_at_mut(2);

    left[0] += 1;
    println!("{data:?}");
    right[0] += 1;
}
```

**Explanation (English):** Formatting the whole vector requires shared access to data, including the region accessed through right. The later write through right keeps its mutable borrow active across the print.

**解说（中文）：** 格式化整个 vector 需要共享访问 data，其中包括通过 right 访问的区域。后面对 right 的写入会使其可变借用跨越打印操作继续有效。

**Correct Answer (English):** It does not compile (E0502). Reading the original vector conflicts with the outstanding mutable borrow. Moving the print after right[0] += 1, with no later slice uses, lets both slice borrows end first.

**正确答案（中文）：** 不能编译（E0502）。读取原 vector 与尚未结束的可变借用冲突。把打印移到 right[0] += 1 后面，并确保之后不再使用切片，就能先结束两个切片的借用。

### 7. Reading one region and mutating another / 读取一个区域并修改另一个区域

**Question (English):** Does this code compile? Why does printing left differ from printing the entire data vector?

**问题（中文）：** 这段代码能否编译？为什么打印 left 与打印整个 data vector 不同？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    let (left, right) = data.split_at_mut(2);

    left[0] += 1;
    println!("{left:?}");
    right[0] += 1;
}
```

**Explanation (English):** Reading through the left slice only accesses its own region. Disjointness allows the right region to remain mutably borrowed while the left region is read.

**解说（中文）：** 通过左侧切片读取只会访问它自己的区域。不重叠保证允许读取左侧区域时，右侧区域仍被可变借用。

**Correct Answer (English):** It compiles and prints [11, 20]. The reason is not that only one mutable borrow exists: separate regions support simultaneous mutable borrows. This print does not access right's region, unlike a print of the entire vector.

**正确答案（中文）：** 可以编译，输出 [11, 20]。原因不是同一时刻只有一个可变借用：不同区域支持同时存在可变借用。此次打印不会像打印整个 vector 那样访问 right 对应的区域。

### 8. Mutable iterators yield distinct elements / 可变迭代器返回不同元素

**Question (English):** Does this code compile? Why can it retain two mutable references when question 1's separate vector indexes failed?

**问题（中文）：** 这段代码能否编译？为什么这里可以保留两个可变引用，而第 1 题的两次独立 vector 索引会失败？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];
    let mut iter = data.iter_mut();

    let first = iter.next().unwrap();
    let second = iter.next().unwrap();

    *first += 1;
    *second += 1;

    println!("{data:?}");
}
```

**Explanation (English):** The standard mutable slice iterator yields each element at most once and allows previously yielded references to remain valid across later next calls. Its implementation keeps yielded elements disjoint from those still available.

**解说（中文）：** 标准可变切片迭代器最多返回每个元素一次，并允许之前返回的引用在后续 next 调用期间继续有效。其实现确保已返回元素与仍可迭代元素互不重叠。

**Correct Answer (English):** It compiles and prints [11, 21, 30, 40]. Both unwrap calls succeed because the vector has four elements. first and second have type `&mut i32` and refer to different elements. The iterator API permits keeping both, rather than requiring an independent borrow of the original vector at each call site. All iterator and element-reference uses end before the final print.

**正确答案（中文）：** 可以编译，输出 [11, 21, 30, 40]。vector 有四个元素，因此两次 unwrap 都会成功。first 和 second 的类型是 `&mut i32`，分别指向不同元素。迭代器接口允许同时保留两者，不需要在每个调用位置独立借用原 vector。迭代器与元素引用的所有使用都在最后打印前结束。

### 9. Pushing during mutable iteration / 可变迭代期间添加元素

**Question (English):** Does this code compile? If push reallocates the vector, what could happen to an existing element reference?

**问题（中文）：** 这段代码能否编译？如果 push 导致 vector 重新分配，已有的元素引用可能发生什么问题？

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];

    for value in data.iter_mut() {
        data.push(50);
        *value += 1;
    }
}
```

**Explanation (English):** Iteration keeps the collection's storage mutably borrowed. push needs another mutable borrow of the vector and may move its elements to a new allocation when capacity is exhausted. References into the old allocation could become dangling.

**解说（中文）：** 迭代会持续可变借用集合的存储区域。push 需要再次可变借用 vector，并且在容量不足时可能把元素移到新的分配中。指向旧分配的引用可能成为悬空引用。

**Correct Answer (English):** It does not compile (E0499). Borrow checking rejects the conflict before any reallocation can occur. Pre-reserving capacity does not make this borrowing pattern legal. A possible redesign is to finish updating existing elements, then append the intended new elements after the iteration borrow ends.

**正确答案（中文）：** 不能编译（E0499）。借用检查会在可能发生重新分配之前拒绝冲突。提前预留容量也不会使这种借用方式合法。一种改写方式是先完成对已有元素的更新，等迭代借用结束后，再追加预期的新元素。

### 10. Scoped threads over disjoint slices / 在不重叠切片上运行作用域线程

**Question (English):** Do these threads need an additional Mutex to modify data safely, and why? thread::scope waits for its threads before returning; move transfers each slice reference into its thread closure.

**问题（中文）：** 这两个线程是否需要额外的 Mutex 才能安全修改 data，为什么？thread::scope 会等待内部线程结束后再返回；move 则把各自的切片引用转移进线程闭包。

```rust
use std::thread;

fn main() {
    let mut data = vec![10, 20, 30, 40];

    thread::scope(|s| {
        let (left, right) = data.split_at_mut(2);

        s.spawn(move || {
            left[0] += 1;
        });

        s.spawn(move || {
            right[0] += 1;
        });
    });

    println!("{data:?}");
}
```

**Explanation (English):** Splitting establishes exclusive access to separate regions. Moving the slice references into the closures neither copies the elements nor moves the vector's ownership into a thread. Scoped thread completion orders the writes before the final read of data.

**解说（中文）：** 分割操作建立了对不同区域的独占访问。把切片引用移动进闭包，既不会复制元素，也不会把 vector 的所有权移动给线程。作用域线程的完成保证写入发生在最后读取 data 之前。

**Correct Answer (English):** It compiles without a mutex and prints [11, 20, 31, 40]. Each thread modifies only its own region, so these accesses do not race. `&mut [i32]` can be transferred to a thread because i32 is Send. The scope waits for both threads, after which the borrows are finished and the final print may read data.

**正确答案（中文）：** 无需互斥锁即可编译，输出 [11, 20, 31, 40]。每个线程只修改自己的区域，因此这些访问不会发生数据竞争。由于 i32 实现了 Send，`&mut [i32]` 可以转移给线程。作用域等待两个线程结束后，借用已结束，最后的打印即可读取 data。

## Additional Clarifications / 补充讲解

### Mutable bindings and reference patterns / 可变绑定与引用模式

**English:** With `let left = &mut data[0]`, left has type `&mut i32`. Assigning through *left changes the element without reassigning left, so the binding need not be mutable. `let mut left = &mut data[0]` additionally allows reassigning left to another compatible reference, subject to borrowing rules.

**中文：** 使用 `let left = &mut data[0]` 时，left 的类型为 `&mut i32`。通过 *left 赋值会修改元素而不重新赋值 left，所以绑定不需要可变。`let mut left = &mut data[0]` 额外允许在借用规则允许的前提下，把另一个兼容引用赋给 left。

**English:** For an independent, reassignable integer, copy the element into a mutable binding. The vector need not be mutable, and changing left does not change data[0].

**中文：** 如果需要独立且可以重新赋值的整数，就把元素复制进可变绑定。vector 本身不需要可变，修改 left 不会改变 data[0]。

```rust
fn main() {
    let data = vec![10, 20, 30, 40];
    let mut left = data[0];
    println!("before: {left}");

    left = 8i32;

    println!("left: {left}");
    println!("data: {data:?}");
}
```

**English:** A left-hand pattern has a different role: `let &mut left = &mut data[0]` destructures the reference and copies the i32 into an immutable binding. To keep this destructuring form but make the integer binding mutable, use `let &mut mut left`. The first &mut matches the reference; the second mut belongs to the binding. The simpler copy above is normally clearer.

**中文：** 左侧模式的作用不同：`let &mut left = &mut data[0]` 会解构引用，把 i32 复制进不可变绑定。如果保留解构形式，同时让整数绑定可变，可以使用 `let &mut mut left`。前面的 &mut 匹配引用，后面的 mut 修饰绑定。通常上面直接复制的形式更清楚。

```rust
fn main() {
    let mut data = vec![10, 20, 30, 40];
    let &mut mut left = &mut data[0];
    println!("before: {left}");

    left = 8i32;

    println!("left: {left}");
    println!("data: {data:?}");
}
```

**English:** Both supplemental programs produce the output below. Copying here depends on i32 implementing Copy; it does not permit moving arbitrary non-Copy owned values out of borrowed elements.

**中文：** 两个补充程序都产生以下输出。这里的复制依赖 i32 实现了 Copy，并不意味着可以从借用的元素中随意移出没有实现 Copy 的拥有所有权的值。

```text
before: 10
left: 8
data: [10, 20, 30, 40]
```

### IndexMut and lifetime contracts / IndexMut 与生命周期约定

**English:** Index defines the associated Output type and provides shared indexing. IndexMut requires Index and provides mutable indexing. For `Vec<i32>` indexed by usize, Output is i32 while index_mut returns `&mut i32`. See the [IndexMut definition](https://doc.rust-lang.org/std/ops/trait.IndexMut.html).

**中文：** Index 定义关联类型 Output 并提供共享索引。IndexMut 要求实现 Index，并提供可变索引。对 `Vec<i32>` 使用 usize 索引时，Output 是 i32，而 index_mut 返回 `&mut i32`。参见 [IndexMut 定义](https://doc.rust-lang.org/std/ops/trait.IndexMut.html)。

```rust
fn index_mut(&mut self, index: Idx) -> &mut Self::Output;
```

**English:** The elided lifetime relationship can be written explicitly below. The output remains tied to the input borrow even after the method returns. See the [lifetime elision rules](https://doc.rust-lang.org/reference/lifetime-elision.html#lifetime-elision-in-functions).

**中文：** 省略的生命周期关系可以显式写成下方形式。即使方法已经返回，输出仍与输入借用关联。参见 [生命周期省略规则](https://doc.rust-lang.org/reference/lifetime-elision.html#lifetime-elision-in-functions)。

```rust
fn index_mut<'a>(&'a mut self, index: Idx) -> &'a mut Self::Output;
```

**English:** For question 1's local vector, `&mut data[0]` can be understood as `&mut *IndexMut::index_mut(&mut data, 0usize)`. The method returns a reference, dereferencing selects the element's place, and the outer &mut borrows that place. This explains the example, rather than a universal text replacement covering temporary-lifetime rules. See the [index expression rules](https://doc.rust-lang.org/reference/expressions/array-expr.html#array-and-slice-indexing-expressions).

**中文：** 对第 1 题的局部 vector，`&mut data[0]` 可以理解成 `&mut *IndexMut::index_mut(&mut data, 0usize)`。方法返回引用，解引用选中元素所在的位置，外层 &mut 再借用这个位置。这是在解释当前示例，并不是涵盖临时值生命周期规则的通用文本替换。参见 [索引表达式规则](https://doc.rust-lang.org/reference/expressions/array-expr.html#array-and-slice-indexing-expressions)。

**English:** In `let value = (&mut data)[0]`, the final index operation is a read and copies an i32 into value. It is not equivalent to `let value = &mut data[0]`. The indexing context determines the requested access; merely starting from a mutable reference does not make the result another mutable reference.

**中文：** 在 `let value = (&mut data)[0]` 中，最终索引操作是读取，会把 i32 复制进 value。它不等价于 `let value = &mut data[0]`。索引所处的上下文决定请求的访问方式；仅仅从可变引用出发，并不会让结果变成另一个可变引用。

## Summary / 总结

**English:** The session established the distinction between mutable bindings and mutable referents, the independence of copied integers, and the ability to mutate disjoint regions concurrently without a mutex. Separate ownership of data regions can remove the need for shared-state locking.

**中文：** 本次学习建立了可变绑定与可变引用目标之间的区别、复制整数的独立性，以及无需互斥锁即可并发修改不重叠区域的理解。对数据区域分别拥有独占权限，可以消除共享状态加锁的需要。

**English:** Borrow-lifetime reasoning needs more practice: check every reference's last use, including reads, and distinguish access through a slice from a new borrow of the entire original vector. The compiler uses the interface's borrowing relationships, rather than an informal argument that two indexes differ.

**中文：** 借用生命周期推理还需要继续练习：检查每个引用的最后一次使用，包括读取；区分通过切片访问与重新借用整个原 vector。编译器依据接口表达的借用关系，而不是关于两个索引不同的非形式化判断。

## Common Mistakes / 常见错误

- Equating binding scope with borrow duration / 把绑定作用域等同于借用持续时间
- Assuming a final read does not keep a borrow needed / 认为末尾读取不会延续借用
- Applying exclusivity to all memory rather than the same region / 把独占规则理解成限制所有内存，而不是同一片区域
- Inferring that vector indexes 0 and 1 return the same element from a compiler rejection / 因为编译器拒绝代码就认为 vector 的索引 0 和 1 返回同一元素
- Confusing `let mut left`, a right-hand &mut, and a left-hand &mut pattern / 混淆 `let mut left`、右侧 &mut 与左侧 &mut 模式
- Expecting reserved capacity to remove the borrow conflict around push / 认为预留容量就能消除 push 处的借用冲突

## Next Steps / 下一步建议

1. Compare the lifetime requirements of thread::spawn and thread::scope, and distinguish moving a reference from moving its referent. / 比较 thread::spawn 与 thread::scope 的生命周期要求，区分移动引用与移动其指向的数据。
2. Practice Send and Sync, then compare partitioned slices with shared updates through `Arc<Mutex<T>>`. / 练习 Send 与 Sync，再比较分区切片与通过 `Arc<Mutex<T>>` 进行共享修改的场景。
3. Relate disjoint regions to Rust GPU output-buffer partitioning while checking device completion and each API's safety contract. / 把不重叠区域与 Rust GPU 输出 buffer 分区联系起来，同时检查设备执行完成时机与各个 API 的安全约定。

## Further Reading / 延伸阅读

- [Index trait / Index trait 文档](https://doc.rust-lang.org/std/ops/trait.Index.html)
- [Splitting borrows / 拆分借用](https://doc.rust-lang.org/nomicon/borrow-splitting.html)
- [Scoped threads / 作用域线程](https://doc.rust-lang.org/std/thread/fn.scope.html)

## Validation / 验证

**English:** All ten question programs and both supplemental runnable programs
were checked with Rust 2024 using
`rustc 1.100.0-nightly (215a8af4b 2026-09-15)`. Questions 1, 3, and 9 failed
with E0499, and question 6 failed with E0502, as expected. The other eight
programs compiled and their output matched the documented results. Compilation
and execution used temporary files outside the repository.

**中文：** 使用 Rust 2024 和
`rustc 1.100.0-nightly (215a8af4b 2026-09-15)` 验证了全部 10 道题的程序与
两个补充可运行程序。第 1、3、9 题按预期产生 E0499，第 6 题按预期产生 E0502。
其余 8 个程序均编译成功，输出与记录中的结果一致。编译与执行使用仓库外的临时文件。

**English:** The repository's bilingual documentation checker and all seven
checker unit tests passed. The required documentation checks are:

**中文：** 仓库双语文档检查器与全部 7 个检查器单元测试均通过。要求的文档检查为：

```bash
python3 scripts/check_bilingual_docs.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```
