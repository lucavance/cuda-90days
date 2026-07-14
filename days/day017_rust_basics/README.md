# Day 017: Rust Basics / Rust 基础

Date / 日期: 2026-07-14

## Topic / 主题

**English:** Rust fundamentals: immutable and mutable bindings, ownership,
borrowing, non-lexical lifetimes, `Copy`, string slices, `Option`, `Result`,
error propagation, and thread ownership.

**中文：** Rust 基础：不可变与可变绑定、所有权、借用、非词法生命周期、
`Copy`、字符串切片、`Option`、`Result`、错误传播以及线程所有权。

## Goal / 目标

**English:** Build a practical mental model of Rust's ownership and type
systems, with enough foundation to understand safe memory access, error
handling, and moving data into a new thread.

**中文：** 建立一套实用的 Rust 所有权与类型系统思维模型，为理解安全内存
访问、错误处理以及在线程间移动数据打下基础。

## 10 Concept Questions / 10 道概念题

### 1. Immutable and mutable bindings / 不可变与可变绑定

**Question (English):** Why are Rust variables immutable by default? How should
a variable be declared when it needs to be reassigned?

**问题（中文）：** Rust 中的变量为什么默认不可变？如果需要重新赋值，应当怎样
声明变量？

**Explanation (English):** Immutable bindings make state changes explicit,
reduce accidental mutation, and make code easier to reason about. Mutability is
an opt-in property of a binding.

**解说（中文）：** 不可变绑定可以让状态变化更加明确，减少意外修改，并使代码
更容易推理。绑定是否可变需要显式选择。

**Correct Answer (English):** Variables declared with `let` are immutable by
default. Use `let mut` when the binding needs to be changed:

**正确答案（中文）：** 使用 `let` 声明的变量默认不可变。绑定需要发生改变时，
使用 `let mut`：

```rust
let mut count = 1;
count = 2;
```

**English:** The main motivation is safety and clarity. Immutability can also
make concurrent code easier to reason about, but compiler optimization is not
its primary purpose.

**中文：** 主要目的是提高安全性和明确性。不可变性也能让并发代码更容易推理，
但编译器优化并不是默认不可变的首要原因。

### 2. Moving a `String` / 移动 `String`

**Question (English):** Does the following code compile? Why?

**问题（中文）：** 下面的代码能否通过编译？为什么？

```rust
let s1 = String::from("hello");
let s2 = s1;
println!("{s1}");
```

**Explanation (English):** `String` owns heap-allocated data and does not
implement `Copy`. Assigning it to another binding moves ownership instead of
implicitly duplicating the allocation.

**解说（中文）：** `String` 拥有堆上分配的数据，并且没有实现 `Copy`。将它赋值
给另一个绑定时会移动所有权，而不会隐式复制堆内存。

**Correct Answer (English):** The code does not compile. Ownership of the
`String` moves from `s1` to `s2`, so `s1` becomes invalid. This prevents both
bindings from trying to free the same allocation. Use `s1.clone()` when an
independent deep copy is required.

**正确答案（中文）：** 代码不能通过编译。`String` 的所有权从 `s1` 移动到了
`s2`，因此 `s1` 随后失效。这样可以防止两个绑定重复释放同一块内存。需要一份
独立的深拷贝时，应使用 `s1.clone()`。

### 3. Shared borrowing / 共享借用

**Question (English):** Why can `s1` still be used after this function call?
What does `&String` mean?

**问题（中文）：** 为什么函数调用结束后仍然可以使用 `s1`？`&String` 表示什么？

```rust
fn length(value: &String) -> usize {
    value.len()
}

let s1 = String::from("hello");
let len = length(&s1);
println!("{s1}: {len}");
```

**Explanation (English):** A reference grants temporary access to a value
without taking ownership. The owner remains responsible for the value
throughout the borrow.

**解说（中文）：** 引用可以在不取得所有权的情况下临时访问一个值。在整个借用
期间，原所有者仍然拥有并负责管理这个值。

**Correct Answer (English):** `&String` is a shared reference to a `String`.
The function can read the string but does not own it, so `s1` remains valid
after the call. Ownership never leaves `s1` and does not need to be returned.
APIs commonly use `&str` instead of `&String` because `&str` accepts both
borrowed `String` data and other string slices.

**正确答案（中文）：** `&String` 是指向 `String` 的共享引用。函数可以读取该
字符串，但不拥有它，因此调用结束后 `s1` 仍然有效。所有权从未离开 `s1`，也
不需要归还。实际 API 通常优先接收 `&str`，因为它既能接收借用的 `String`
数据，也能接收其他字符串切片。

### 4. Overlapping mutable borrows / 重叠的可变借用

**Question (English):** Does the following code compile? Explain using Rust's
mutable borrowing rules.

**问题（中文）：** 下面的代码能否通过编译？请使用 Rust 的可变借用规则解释。

```rust
let mut text = String::from("hello");

let r1 = &mut text;
let r2 = &mut text;

r1.push('!');
r2.push('?');
```

**Explanation (English):** A mutable reference represents exclusive access for
the duration of its borrow. Overlapping mutable references could allow
unsynchronized access to the same value.

**解说（中文）：** 可变引用在借用有效期间代表独占访问。重叠的可变引用可能让
多个位置在没有同步的情况下修改同一个值。

**Correct Answer (English):** The code does not compile. `r1` is used after
`r2` is created, so their mutable borrows overlap. Rust permits either any
number of shared references or one mutable reference at a time, but not
overlapping access that includes a mutable reference.

**正确答案（中文）：** 代码不能通过编译。创建 `r2` 后仍然使用了 `r1`，所以
两个可变借用发生重叠。Rust 在同一时刻允许任意数量的共享引用，或者一个可变
引用，但不允许包含可变引用的访问发生重叠。

### 5. Non-lexical lifetimes / 非词法生命周期

**Question (English):** Does this code compile? Why can `r3` be created after
`r1` and `r2`?

**问题（中文）：** 这段代码能否通过编译？为什么可以在 `r1` 和 `r2` 之后创建
`r3`？

```rust
let mut text = String::from("hello");

let r1 = &text;
let r2 = &text;
println!("{r1} {r2}");

let r3 = &mut text;
r3.push('!');
```

**Explanation (English):** With non-lexical lifetimes, the borrow checker can
end a borrow after its last use instead of always extending it to the end of
the surrounding block.

**解说（中文）：** 借助非词法生命周期，借用检查器可以在引用最后一次使用后
结束借用，而不必始终将借用延长到所在代码块的末尾。

**Correct Answer (English):** The code compiles. The last uses of `r1` and `r2`
occur in `println!`, so their shared borrows end before `r3` is created. The
bindings may still be within the lexical block, but their borrows no longer
need to remain active.

**正确答案（中文）：** 代码可以通过编译。`r1` 和 `r2` 的最后一次使用发生在
`println!` 中，因此对应的共享借用会在创建 `r3` 前结束。虽然这些绑定仍处于
词法代码块中，但它们的借用不再需要保持有效。

### 6. The `Copy` trait / `Copy` trait

**Question (English):** Why does this code compile when assigning a `String`
would move the original value?

**问题（中文）：** 为什么这段代码可以通过编译，而赋值一个 `String` 时会移动
原值？

```rust
let x = 42;
let y = x;

println!("{x}, {y}");
```

**Explanation (English):** Types implementing `Copy` use implicit copy
semantics for assignment and function arguments.

**解说（中文）：** 实现 `Copy` 的类型在赋值和传递函数参数时使用隐式复制语义。

**Correct Answer (English):** The inferred type of `x` is `i32`, which
implements `Copy`. The assignment duplicates the value, so both `x` and `y`
remain usable. `String` does not implement `Copy`; duplicating its owned data
requires an explicit `clone()`.

**正确答案（中文）：** `x` 推导出的类型是实现了 `Copy` 的 `i32`。赋值操作会
复制该值，因此 `x` 和 `y` 都能继续使用。`String` 没有实现 `Copy`；复制它所
拥有的数据需要显式调用 `clone()`。

### 7. String slices and mutation / 字符串切片与修改

**Question (English):** Does the following code compile? What type is `word`,
and why does it affect mutation of `text`?

**问题（中文）：** 下面的代码能否通过编译？`word` 是什么类型？为什么它会影响
对 `text` 的修改？

```rust
let mut text = String::from("hello world");
let word = &text[0..5];

text.clear();

println!("{word}");
```

**Explanation (English):** A string slice borrows a range of UTF-8 bytes from
existing string data without allocating a new string. The underlying data must
remain valid and unchanged while the slice is used.

**解说（中文）：** 字符串切片从已有字符串数据中借用一段 UTF-8 字节范围，不会
创建新的字符串。切片仍在使用时，底层数据必须保持有效且不能被修改。

**Correct Answer (English):** `word` has type `&str`, and the code does not
compile. Its shared borrow remains active until `println!`, while
`text.clear()` requires a mutable borrow of `text`. Rejecting the mutation
prevents `word` from referring to cleared or changed data. String slice ranges
must also fall on valid UTF-8 character boundaries.

**正确答案（中文）：** `word` 的类型是 `&str`，代码不能通过编译。它的共享
借用会持续到 `println!`，而 `text.clear()` 需要可变借用 `text`。拒绝这次修改
可以防止 `word` 指向已被清空或改变的数据。字符串切片的范围还必须位于有效的
UTF-8 字符边界上。

### 8. `Option<T>` / 可选值 `Option<T>`

**Question (English):** What are the two possible variants of `Option<T>`?
What advantage does it have over using a null pointer to mean "no value"?

**问题（中文）：** `Option<T>` 有哪两种可能的变体？与使用空指针表示“没有值”
相比，它有什么优势？

**Explanation (English):** `Option<T>` represents optional data directly in
the type system. Callers can see that a value may be absent and handle that case
explicitly.

**解说（中文）：** `Option<T>` 直接在类型系统中表示可选数据。调用者能够看出
值可能不存在，并显式处理这种情况。

**Correct Answer (English):** The variants are `Some(T)`, which contains a
value, and `None`, which represents absence. Pattern matching and methods such
as `map`, `unwrap_or`, and `ok_or` make both cases explicit. This avoids
ordinary null dereferences and lets the compiler check that optionality is
respected.

**正确答案（中文）：** 两个变体分别是包含值的 `Some(T)` 和表示不存在的
`None`。模式匹配以及 `map`、`unwrap_or`、`ok_or` 等方法能够显式处理两种
情况。这可以避免普通的空指针解引用，并让编译器检查代码是否正确处理了可选性。

### 9. Error propagation with `?` / 使用 `?` 传播错误

**Question (English):** What does `?` do in the following function? Why must
the function return `Result` or another compatible type?

**问题（中文）：** 下面函数中的 `?` 做了什么？为什么函数必须返回 `Result`
或其他兼容类型？

```rust
fn read_number(text: &str) -> Result<i32, std::num::ParseIntError> {
    let number = text.parse::<i32>()?;
    Ok(number)
}
```

**Explanation (English):** The `?` operator provides concise early error
propagation while allowing successful execution to continue with the inner
value.

**解说（中文）：** `?` 运算符能够简洁地提前传播错误，同时在操作成功时取出
内部值并继续执行。

**Correct Answer (English):** If `parse()` returns `Ok(number)`, `?` extracts
the number and execution continues. If it returns `Err(error)`, the current
function returns early with that error, converting it through `From` when
necessary. The return type must be compatible with this early-return behavior.

**正确答案（中文）：** 如果 `parse()` 返回 `Ok(number)`，`?` 会取出数字并继续
执行。如果返回 `Err(error)`，当前函数会携带该错误提前返回，并在需要时通过
`From` 转换错误类型。函数返回类型必须与这种提前返回行为兼容。

### 10. Moving data into a thread / 将数据移动到线程中

**Question (English):** Does the following code compile? What does `move` do,
and what does `handle.join().unwrap()` mean?

**问题（中文）：** 下面的代码能否通过编译？`move` 有什么作用？
`handle.join().unwrap()` 表示什么？

```rust
use std::thread;

let message = String::from("hello");

let handle = thread::spawn(move || {
    println!("{message}");
});

handle.join().unwrap();

println!("{message}");
```

**Explanation (English):** A `move` closure captures used values by value. This
allows a spawned thread to own its captured data independently of the stack
frame that created it.

**解说（中文）：** `move` 闭包按值捕获它所使用的变量。这样，新线程可以独立
拥有捕获的数据，而不依赖创建它的原始栈帧。

**Correct Answer (English):** The complete code does not compile because
`message` moves into the closure and cannot be used by the final `println!` in
the original thread. `thread::spawn` returns a `JoinHandle<T>`. Calling `join()`
consumes the handle, blocks the current thread until the spawned thread
finishes, and returns `Ok(T)` when it finishes normally or `Err(panic_payload)`
when it panics. Calling `unwrap()` extracts the successful value or panics in
the waiting thread if the spawned thread panicked. In this example the closure
returns `()`, so a successful `handle.join().unwrap()` also evaluates to `()`.
Joining the thread does not move captured values back to the original thread.

**正确答案（中文）：** 完整代码不能通过编译，因为 `message` 被移动到了闭包
中，原线程最后的 `println!` 无法再使用它。`thread::spawn` 返回一个
`JoinHandle<T>`。调用 `join()` 会消费该句柄，阻塞当前线程直到新线程结束；
新线程正常结束时返回 `Ok(T)`，发生 panic 时返回 `Err(panic_payload)`。随后
调用 `unwrap()` 会取出成功值；如果新线程发生了 panic，则等待它的线程也会
panic。本例闭包返回 `()`，因此成功的 `handle.join().unwrap()` 结果同样是
`()`。等待线程结束并不会把闭包捕获的值移回原线程。

## Summary / 总结

### Concepts Covered / 已学习概念

- **English:** Immutable bindings by default and explicit mutation with `mut`.
  **中文：** 默认不可变绑定以及使用 `mut` 显式开启可变性。
- **English:** Ownership moves for non-`Copy` values such as `String`.
  **中文：** `String` 等非 `Copy` 值的所有权移动。
- **English:** Shared references, mutable references, and exclusive mutable
  access. **中文：** 共享引用、可变引用以及独占的可变访问。
- **English:** Non-lexical lifetimes and last-use borrow analysis.
  **中文：** 非词法生命周期和基于最后一次使用的借用分析。
- **English:** Implicit copies through the `Copy` trait.
  **中文：** 通过 `Copy` trait 进行隐式复制。
- **English:** Borrowed string slices with `&str`.
  **中文：** 使用 `&str` 表示借用的字符串切片。
- **English:** Optional values with `Option<T>`.
  **中文：** 使用 `Option<T>` 表示可选值。
- **English:** Recoverable errors with `Result` and the `?` operator.
  **中文：** 使用 `Result` 和 `?` 处理并传播可恢复错误。
- **English:** Moving captured values into spawned threads.
  **中文：** 将闭包捕获的值移动到新线程。
- **English:** Waiting with `JoinHandle::join` and handling the thread result
  with `unwrap`. **中文：** 使用 `JoinHandle::join` 等待线程，并通过 `unwrap`
  处理线程结果。

## Common Mistakes / 常见错误

- **English:** Treating a borrow as ownership temporarily leaving and later
  returning to the original binding. The owner retains ownership throughout a
  borrow. **中文：** 把借用理解成所有权暂时离开后再归还。借用期间，原所有者
  始终保留所有权。
- **English:** Saying a borrow ends only when its variable leaves the lexical
  scope. With non-lexical lifetimes, it can end after the reference's last use.
  **中文：** 认为借用只能在变量离开词法作用域后结束。借助非词法生命周期，
  借用可以在引用最后一次使用后结束。
- **English:** Forgetting that a live `&str` slice prevents mutation of its
  source `String`. **中文：** 忘记有效的 `&str` 切片会阻止对来源 `String` 的
  可变操作。
- **English:** Writing `Some<T>` as a value variant; the value constructor is
  `Some(T)`. **中文：** 把值变体写成 `Some<T>`；正确的值构造形式是 `Some(T)`。
- **English:** Treating `move` as a thread operation. It changes how a closure
  captures values; `thread::spawn` then moves that closure into the new thread.
  **中文：** 把 `move` 当作线程操作。它实际改变的是闭包捕获值的方式，随后
  `thread::spawn` 再把闭包移动到新线程。
- **English:** Assuming `join()` restores values moved into a thread. It only
  waits and returns the closure's return value or panic payload.
  **中文：** 认为 `join()` 会归还移动到线程中的值。它只负责等待，并返回闭包
  的返回值或 panic 载荷。

## Next Step / 下一步

**English:** Study structs, enums, and exhaustive `match` expressions, followed
by traits, generics, explicit lifetime annotations, iterators, and the `Send`
and `Sync` traits used in concurrent Rust.

**中文：** 接下来学习结构体、枚举和穷尽式 `match`，然后继续学习 trait、泛型、
显式生命周期标注、迭代器，以及并发 Rust 中使用的 `Send` 和 `Sync` trait。
