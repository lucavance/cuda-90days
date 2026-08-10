# Day 037: Rust Core Concepts Review / Rust 核心概念复习

Date / 日期: 2026-08-10

## Topic / 主题

**English:** Rust core concepts: ownership moves, shared and mutable borrowing,
non-lexical lifetimes, the `Copy` trait, exhaustive matching with `Option`,
error propagation with `Result` and `?`, trait bounds, borrowing iterators, and
explicit lifetime relationships.

**中文：** Rust 核心概念：所有权移动、共享借用与可变借用、非词法生命周期、
`Copy` trait、使用 `Option` 进行穷尽匹配、使用 `Result` 与 `?` 传播错误、trait
约束、借用式迭代器以及显式生命周期关系。

## Goal / 目标

**English:** Reinforce a practical mental model for how Rust tracks ownership,
temporary access, recoverable errors, generic behavior, and reference validity
at compile time.

**中文：** 巩固一套实用思维模型，理解 Rust 如何在编译期跟踪所有权、临时访问、
可恢复错误、泛型行为以及引用有效性。

## Core Mental Model / 核心思维模型

**English:** Every value has an owner, references grant temporary access
without transferring ownership, and lifetimes describe how references relate
to the data they borrow. Rust makes optional values, recoverable errors, and
shared behavior explicit through types so the compiler can reject invalid
states before execution.

**中文：** 每个值都有所有者，引用在不转移所有权的前提下提供临时访问，生命周期
则描述引用与其借用数据之间的关系。Rust 通过类型显式表示可选值、可恢复错误与
共享行为，使编译器能够在执行前拒绝无效状态。

## 10 Concept Questions / 10 个概念问题

### 1. Moving ownership of a `String` / 移动 `String` 的所有权

**Question (English):** Does the following code compile? What happens to the
ownership of the string?

**问题（中文）：** 下面的代码能否通过编译？字符串的所有权发生了什么变化？

```rust
fn main() {
    let s1 = String::from("hello");
    let s2 = s1;

    println!("{}", s1);
}
```

**Explanation (English):** `String` owns heap-allocated data and does not
implement `Copy`. Assignment transfers responsibility for that allocation
instead of silently duplicating it.

**解说（中文）：** `String` 拥有堆上分配的数据，并且没有实现 `Copy`。赋值操作
会转移管理该内存的责任，而不会静默复制它。

**Correct Answer (English):** The code does not compile. `let s2 = s1` moves
the `String` from `s1` to `s2`, so using `s1` afterward is a use-after-move
error. This rule prevents both bindings from freeing the same allocation. Use
`s1.clone()` before the move when an independent deep copy is required.

**正确答案（中文）：** 代码不能通过编译。`let s2 = s1` 将 `String` 从 `s1`
移动给 `s2`，因此后续使用 `s1` 会产生移动后使用错误。该规则防止两个绑定重复
释放同一块内存。如果需要独立的深拷贝，应在移动前使用 `s1.clone()`。

### 2. Shared borrowing without an ownership move / 不移动所有权的共享借用

**Question (English):** Does the following code compile? Is `s1` still valid
after the function call, and why?

**问题（中文）：** 下面的代码能否通过编译？函数调用后 `s1` 是否仍然有效？
为什么？

```rust
fn length(value: &String) -> usize {
    value.len()
}

fn main() {
    let s1 = String::from("hello");
    let size = length(&s1);

    println!("{s1}: {size}");
}
```

**Explanation (English):** A shared reference grants read-only access to a
value without taking ownership. The original binding remains the owner during
and after the borrow.

**解说（中文）：** 共享引用在不取得所有权的情况下提供只读访问。借用期间及借用
结束后，原绑定始终是该值的所有者。

**Correct Answer (English):** The code compiles. `&s1` creates a shared
reference, so `length` borrows the `String` and does not own it. `s1` therefore
remains valid after the call. A general-purpose API would normally accept
`&str` instead of `&String`, because `&str` also accepts string slices and
string literals.

**正确答案（中文）：** 代码可以通过编译。`&s1` 创建共享引用，因此 `length`
只是借用 `String`，并不拥有它；调用后 `s1` 仍然有效。通用 API 通常会接收
`&str` 而不是 `&String`，因为 `&str` 还能接收字符串切片和字符串字面量。

### 3. Overlapping shared and mutable borrows / 重叠的共享借用与可变借用

**Question (English):** Does the following code compile? If not, which
borrowing rule does it violate?

**问题（中文）：** 下面的代码能否通过编译？如果不能，它违反了哪条借用规则？

```rust
fn main() {
    let mut text = String::from("hello");

    let shared = &text;
    let exclusive = &mut text;

    exclusive.push_str(" world");
    println!("{shared}");
}
```

**Explanation (English):** A mutable reference represents exclusive access.
Allowing a live shared reference at the same time could let one location read
while another changes the same value.

**解说（中文）：** 可变引用代表独占访问。如果同时允许有效的共享引用，一个位置
就可能在另一个位置修改同一值时读取它。

**Correct Answer (English):** The code does not compile. `shared` remains live
until its use in `println!`, so its shared borrow overlaps the mutable borrow
held by `exclusive`. Rust permits either multiple shared references or one
mutable reference at a time, but not overlapping access that includes a
mutable reference.

**正确答案（中文）：** 代码不能通过编译。`shared` 会一直有效到 `println!` 中的
最后一次使用，因此它的共享借用与 `exclusive` 持有的可变借用发生重叠。Rust
同一时刻允许多个共享引用，或者一个可变引用，但不允许包含可变引用的访问发生
重叠。

### 4. Non-lexical lifetimes and last use / 非词法生命周期与最后一次使用

**Question (English):** Does the reordered code compile? Why can the mutable
borrow begin while the `shared` binding is still in the surrounding block?

**问题（中文）：** 调整使用顺序后的代码能否通过编译？为什么 `shared` 绑定仍在
外层代码块中时就可以开始可变借用？

```rust
fn main() {
    let mut text = String::from("hello");

    let shared = &text;
    println!("{shared}");

    let exclusive = &mut text;
    exclusive.push_str(" world");

    println!("{text}");
}
```

**Explanation (English):** Non-lexical lifetimes allow the borrow checker to
end a borrow after a reference's last use rather than always keeping it active
until the end of the lexical block.

**解说（中文）：** 非词法生命周期允许借用检查器在引用最后一次使用后结束借用，
而不必始终让借用持续到词法代码块末尾。

**Correct Answer (English):** The code compiles. The shared borrow is no
longer needed after the first `println!`, so it ends before `exclusive` is
created. The `shared` binding is still lexically in scope, but its borrow is no
longer active and therefore does not overlap the mutable borrow.

**正确答案（中文）：** 代码可以通过编译。第一次 `println!` 后不再需要共享借用，
所以它会在创建 `exclusive` 前结束。`shared` 绑定在词法上仍处于作用域内，但其
借用已经不再有效，因此不会与可变借用重叠。

### 5. Implicit copying with `Copy` / 使用 `Copy` 隐式复制

**Question (English):** Does the following code compile? Why does this
assignment behave differently from assigning a `String`?

**问题（中文）：** 下面的代码能否通过编译？为什么该赋值与赋值一个 `String`
的行为不同？

```rust
fn main() {
    let number1 = 42;
    let number2 = number1;

    println!("{number1}, {number2}");
}
```

**Explanation (English):** Types implementing `Copy` duplicate their value
implicitly during ordinary assignment. Simple fixed-size values such as many
numeric types can support this behavior safely and cheaply.

**解说（中文）：** 实现 `Copy` 的类型会在普通赋值时隐式复制其值。许多数值类型
等简单的固定大小值能够安全且低成本地支持这种行为。

**Correct Answer (English):** The code compiles. The integer literal is
inferred as `i32` by default, and `i32` implements `Copy`, so both bindings
remain valid. The Rust type name is `i32`, not `int32`. `String` does not
implement `Copy`; its assignment moves ownership unless an explicit `clone()`
is performed.

**正确答案（中文）：** 代码可以通过编译。整数字面量默认推导为实现了 `Copy` 的
`i32`，所以两个绑定都保持有效。Rust 类型名是 `i32`，不是 `int32`。`String`
没有实现 `Copy`；除非显式调用 `clone()`，否则赋值会移动其所有权。

### 6. Exhaustive matching with `Option<T>` / 对 `Option<T>` 进行穷尽匹配

**Question (English):** What does the following code print? Why must the
`match` expression handle both `Some` and `None`?

**问题（中文）：** 下面的代码输出什么？为什么 `match` 表达式必须同时处理
`Some` 和 `None`？

```rust
fn describe(value: Option<i32>) {
    match value {
        Some(number) => println!("value: {number}"),
        None => println!("missing"),
    }
}

fn main() {
    describe(Some(7));
    describe(None);
}
```

**Explanation (English):** `Option<T>` represents presence and absence as two
explicit enum variants. Exhaustive pattern matching makes the compiler verify
that every possible case is handled.

**解说（中文）：** `Option<T>` 使用两个显式枚举变体表示有值和无值。穷尽式模式
匹配让编译器验证每一种可能情况都得到了处理。

**Correct Answer (English):** The output is:

**正确答案（中文）：** 输出为：

```text
value: 7
missing
```

**English:** `Option<i32>` can be either `Some(i32)` or `None`, so both must be
covered explicitly or through a wildcard such as `_`. This type-level design
forces callers to account for a missing value instead of relying on an
unchecked null-like state.

**中文：** `Option<i32>` 只能是 `Some(i32)` 或 `None`，因此必须显式覆盖两者，
或者使用 `_` 等通配模式覆盖剩余情况。这种类型层面的设计强制调用者处理缺失值，
而不是依赖未经检查的类 null 状态。

### 7. Error propagation with `Result` and `?` / 使用 `Result` 与 `?` 传播错误

**Question (English):** What do the two calls return, and what does the `?`
operator do?

**问题（中文）：** 两次调用分别返回什么？`?` 运算符起什么作用？

```rust
fn parse_and_double(
    input: &str,
) -> Result<i32, std::num::ParseIntError> {
    let number = input.parse::<i32>()?;
    Ok(number * 2)
}

fn main() {
    println!("{:?}", parse_and_double("21"));
    println!("{:?}", parse_and_double("rust"));
}
```

**Explanation (English):** `Result<T, E>` carries either a successful value or
a recoverable error value. The `?` operator concisely unwraps success and
returns early on failure.

**解说（中文）：** `Result<T, E>` 携带成功值或可恢复的错误值。`?` 运算符能够
简洁地取出成功值，并在失败时提前返回。

**Correct Answer (English):** The first call returns `Ok(42)`. The second
returns `Err` containing a `ParseIntError` whose error kind is `InvalidDigit`;
it is an error value, not the string `"std::num::ParseIntError"`. Its debug
output is typically similar to:

**正确答案（中文）：** 第一次调用返回 `Ok(42)`。第二次返回包含
`ParseIntError` 的 `Err`，其错误种类为 `InvalidDigit`；它是错误值，而不是
字符串 `"std::num::ParseIntError"`。其调试输出通常类似：

```text
Ok(42)
Err(ParseIntError { kind: InvalidDigit })
```

**English:** If parsing returns `Ok(number)`, `?` extracts the number and
execution continues. If parsing returns `Err(error)`, the current function
returns early with a compatible error, using `From` conversion when needed.

**中文：** 如果解析返回 `Ok(number)`，`?` 会取出数字并继续执行。如果解析返回
`Err(error)`，当前函数会携带兼容的错误提前返回，并在需要时使用 `From` 进行
转换。

### 8. Trait bounds and borrowed trait implementations / Trait 约束与借用实现类型

**Question (English):** Why can `print_summary` accept an `Article`? Is
`article` still valid after the call?

**问题（中文）：** 为什么 `print_summary` 可以接收 `Article`？调用结束后
`article` 是否仍然有效？

```rust
trait Summary {
    fn summary(&self) -> String;
}

struct Article {
    title: String,
}

impl Summary for Article {
    fn summary(&self) -> String {
        format!("Article: {}", self.title)
    }
}

fn print_summary(item: &impl Summary) {
    println!("{}", item.summary());
}

fn main() {
    let article = Article {
        title: String::from("Learning Rust"),
    };

    print_summary(&article);
    println!("{}", article.title);
}
```

**Explanation (English):** A trait describes behavior that types can
implement. An `impl Trait` parameter constrains accepted values to types that
provide that behavior, while `&` controls whether the function owns or merely
borrows the accepted value.

**解说（中文）：** trait 描述类型可以实现的行为。`impl Trait` 参数把可接收的值
约束为提供该行为的类型，而 `&` 决定函数是拥有该值还是仅仅借用它。

**Correct Answer (English):** `Article` implements the `Summary` trait, so
`&Article` satisfies the `&impl Summary` parameter. This form is similar to
`fn print_summary<T: Summary>(item: &T)` and normally uses static dispatch.
The function receives a shared reference, so ownership is not transferred and
`article` remains valid after the call.

**正确答案（中文）：** `Article` 实现了 `Summary` trait，因此 `&Article` 满足
`&impl Summary` 参数。该写法类似于
`fn print_summary<T: Summary>(item: &T)`，通常使用静态分派。函数接收共享
引用，不会转移所有权，所以调用后 `article` 仍然有效。

### 9. Borrowing iteration with `.iter()` / 使用 `.iter()` 进行借用式迭代

**Question (English):** Does the following code compile? What does `lengths`
contain, and why can `words` still be used afterward?

**问题（中文）：** 下面的代码能否通过编译？`lengths` 包含什么？为什么之后仍能
使用 `words`？

```rust
fn main() {
    let words = vec![
        String::from("rust"),
        String::from("cuda"),
    ];

    let lengths: Vec<usize> = words
        .iter()
        .map(|word| word.len())
        .collect();

    println!("{lengths:?}");
    println!("{words:?}");
}
```

**Explanation (English):** `.iter()` borrows a collection and yields shared
references to its elements. Iterator adapters such as `map` are lazy until a
consumer such as `collect` requests their results.

**解说（中文）：** `.iter()` 借用集合并产生指向元素的共享引用。`map` 等迭代器
适配器保持惰性，直到 `collect` 等消费者请求结果时才执行。

**Correct Answer (English):** The code compiles. The closure receives each
element as `&String`, reads its length, and `collect` builds
`vec![4_usize, 4_usize]`. Because `.iter()` only borrows the vector, `words`
still owns both strings and remains usable. By contrast, `.into_iter()` would
consume this vector and yield owned `String` values.

**正确答案（中文）：** 代码可以通过编译。闭包以 `&String` 接收每个元素并读取
其长度，`collect` 构建出 `vec![4_usize, 4_usize]`。由于 `.iter()` 只借用
vector，`words` 仍然拥有两个字符串并可继续使用。相比之下，`.into_iter()`
会消费该 vector，并产生拥有所有权的 `String` 值。

### 10. Explicit lifetime relationships / 显式生命周期关系

**Question (English):** Does the following code compile? What relationship
does the lifetime parameter `'a` express?

**问题（中文）：** 下面的代码能否通过编译？生命周期参数 `'a` 表达了什么关系？

```rust
fn longest<'a>(left: &'a str, right: &'a str) -> &'a str {
    if left.len() >= right.len() {
        left
    } else {
        right
    }
}

fn main() {
    let outer = String::from("a long string");
    let result;

    {
        let inner = String::from("short");
        result = longest(&outer, &inner);
    }

    println!("{result}");
}
```

**Explanation (English):** A lifetime parameter is not a duration chosen by
the programmer and does not keep data alive. It relates input and output
references so the borrow checker can ensure that a returned reference never
outlives borrowed data from which it might originate.

**解说（中文）：** 生命周期参数不是由程序员选择的一段持续时间，也不会让数据
延长存活。它关联输入引用与输出引用，使借用检查器能够保证返回引用不会比其可能
来源的借用数据存活更久。

**Correct Answer (English):** The code does not compile. The signature says
the returned reference may come from either input and is valid only for a
lifetime common to both. At this call site, that usable lifetime cannot extend
beyond `inner`, which is dropped at the end of the inner block. The compiler
therefore rejects using `result` afterward, even though these particular
runtime string lengths would select `outer`. The annotation describes a
relationship; it does not extend either value's lifetime.

**正确答案（中文）：** 代码不能通过编译。函数签名表明返回引用可能来自任一输入，
并且只在两个输入共同有效的生命周期内有效。在该调用处，这段可用生命周期不能
超过 `inner`；而 `inner` 会在内部代码块末尾释放。因此，即使这些具体字符串在
运行时会选择 `outer`，编译器仍会拒绝随后使用 `result`。生命周期标注描述的是
关系，不会延长任一值的实际生命周期。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** Ownership moves for non-`Copy` values and explicit cloning when
  independent data is needed. **中文：** 非 `Copy` 值的所有权移动，以及需要独立
  数据时进行显式 clone。
- **English:** Shared borrowing preserves ownership, while mutable borrowing
  requires exclusive access. **中文：** 共享借用保留所有权，而可变借用要求独占
  访问。
- **English:** Non-lexical lifetimes can end a borrow after its last use.
  **中文：** 非词法生命周期可以在引用最后一次使用后结束借用。
- **English:** `i32` and other `Copy` types remain usable after assignment.
  **中文：** `i32` 等 `Copy` 类型在赋值后仍然可用。
- **English:** `Option`, exhaustive `match`, `Result`, and `?` make absence and
  recoverable failure explicit. **中文：** `Option`、穷尽式 `match`、`Result`
  与 `?` 显式表达缺失值和可恢复失败。
- **English:** Trait bounds describe accepted behavior, and `.iter()` borrows
  rather than consumes a collection. **中文：** Trait 约束描述可接收的行为，而
  `.iter()` 借用集合而不是消费集合。

## Common Mistakes / 常见错误

- **English:** Assuming a mutable reference may coexist with a shared
  reference that will be used later. **中文：** 误以为可变引用可以与之后仍会使用的
  共享引用同时存在。
- **English:** Calling Rust's default integer type `int32` instead of `i32`.
  **中文：** 把 Rust 的默认整数类型 `i32` 写成 `int32`。
- **English:** Describing `ParseIntError` as a string instead of an error value
  stored inside `Err`. **中文：** 把 `ParseIntError` 描述成字符串，而不是存放在
  `Err` 中的错误值。
- **English:** Treating a trait as a data shape rather than a contract for
  behavior implemented by a type. **中文：** 把 trait 当作数据形状，而不是类型
  所实现的行为契约。
- **English:** Treating `'a` as a concrete lifetime length or assuming an
  annotation extends how long data lives. **中文：** 把 `'a` 当作具体的生命周期
  长度，或误以为标注会延长数据的实际存活时间。

## Next Steps / 下一步

**English:** Practice more nested-scope lifetime examples, then study structs,
enums, richer pattern matching, iterator ownership choices, Cargo modules, and
unit tests. A focused follow-up session on explicit lifetimes and borrow-checker
diagnostics would reinforce the weakest point from this review.

**中文：** 继续练习更多嵌套作用域的生命周期示例，然后学习结构体、枚举、更丰富
的模式匹配、迭代器所有权选择、Cargo 模块和单元测试。下一次可集中练习显式生命
周期与借用检查器诊断，以巩固本次复习中最薄弱的部分。
