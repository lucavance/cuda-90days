# Day 017: Rust Basics

Date: 2026-07-14

## Topic

Rust fundamentals: immutable and mutable bindings, ownership, borrowing,
non-lexical lifetimes, `Copy`, string slices, `Option`, `Result`, error
propagation, and thread ownership.

## Goal

Build a practical mental model of Rust's ownership and type systems, with
enough foundation to understand safe memory access, error handling, and moving
data into a new thread.

## 10 Concept Questions

### 1. Immutable and mutable bindings

**Question:** Why are Rust variables immutable by default? How should a variable
be declared when it needs to be reassigned?

**Explanation:** Immutable bindings make state changes explicit, reduce
accidental mutation, and make code easier to reason about. Mutability is an
opt-in property of a binding.

**Correct Answer:** Variables declared with `let` are immutable by default. Use
`let mut` when the binding needs to be changed:

```rust
let mut count = 1;
count = 2;
```

The main motivation is safety and clarity. Immutability can also make concurrent
code easier to reason about, but compiler optimization is not its primary
purpose.

### 2. Moving a `String`

**Question:** Does the following code compile? Why?

```rust
let s1 = String::from("hello");
let s2 = s1;
println!("{s1}");
```

**Explanation:** `String` owns heap-allocated data and does not implement
`Copy`. Assigning it to another binding moves ownership instead of implicitly
duplicating the allocation.

**Correct Answer:** The code does not compile. Ownership of the `String` moves
from `s1` to `s2`, so `s1` becomes invalid. This prevents both bindings from
trying to free the same allocation. Use `s1.clone()` when an independent deep
copy is required.

### 3. Shared borrowing

**Question:** Why can `s1` still be used after this function call? What does
`&String` mean?

```rust
fn length(value: &String) -> usize {
    value.len()
}

let s1 = String::from("hello");
let len = length(&s1);
println!("{s1}: {len}");
```

**Explanation:** A reference grants temporary access to a value without taking
ownership. The owner remains responsible for the value throughout the borrow.

**Correct Answer:** `&String` is a shared reference to a `String`. The function
can read the string but does not own it, so `s1` remains valid after the call.
Ownership never leaves `s1` and does not need to be returned. APIs commonly use
`&str` instead of `&String` because `&str` accepts both borrowed `String` data
and other string slices.

### 4. Overlapping mutable borrows

**Question:** Does the following code compile? Explain using Rust's mutable
borrowing rules.

```rust
let mut text = String::from("hello");

let r1 = &mut text;
let r2 = &mut text;

r1.push('!');
r2.push('?');
```

**Explanation:** A mutable reference represents exclusive access for the
duration of its borrow. Overlapping mutable references could allow unsynchronized
access to the same value.

**Correct Answer:** The code does not compile. `r1` is used after `r2` is
created, so their mutable borrows overlap. Rust permits either any number of
shared references or one mutable reference at a time, but not overlapping access
that includes a mutable reference.

### 5. Non-lexical lifetimes

**Question:** Does this code compile? Why can `r3` be created after `r1` and
`r2`?

```rust
let mut text = String::from("hello");

let r1 = &text;
let r2 = &text;
println!("{r1} {r2}");

let r3 = &mut text;
r3.push('!');
```

**Explanation:** With non-lexical lifetimes, the borrow checker can end a borrow
after its last use instead of always extending it to the end of the surrounding
block.

**Correct Answer:** The code compiles. The last uses of `r1` and `r2` occur in
`println!`, so their shared borrows end before `r3` is created. The bindings may
still be within the lexical block, but their borrows no longer need to remain
active.

### 6. The `Copy` trait

**Question:** Why does this code compile when assigning a `String` would move
the original value?

```rust
let x = 42;
let y = x;

println!("{x}, {y}");
```

**Explanation:** Types implementing `Copy` use implicit copy semantics for
assignment and function arguments.

**Correct Answer:** The inferred type of `x` is `i32`, which implements `Copy`.
The assignment duplicates the value, so both `x` and `y` remain usable.
`String` does not implement `Copy`; duplicating its owned data requires an
explicit `clone()`.

### 7. String slices and mutation

**Question:** Does the following code compile? What type is `word`, and why does
it affect mutation of `text`?

```rust
let mut text = String::from("hello world");
let word = &text[0..5];

text.clear();

println!("{word}");
```

**Explanation:** A string slice borrows a range of UTF-8 bytes from existing
string data without allocating a new string. The underlying data must remain
valid and unchanged while the slice is used.

**Correct Answer:** `word` has type `&str`, and the code does not compile. Its
shared borrow remains active until `println!`, while `text.clear()` requires a
mutable borrow of `text`. Rejecting the mutation prevents `word` from referring
to cleared or changed data. String slice ranges must also fall on valid UTF-8
character boundaries.

### 8. `Option<T>`

**Question:** What are the two possible variants of `Option<T>`? What advantage
does it have over using a null pointer to mean "no value"?

**Explanation:** `Option<T>` represents optional data directly in the type
system. Callers can see that a value may be absent and handle that case
explicitly.

**Correct Answer:** The variants are `Some(T)`, which contains a value, and
`None`, which represents absence. Pattern matching and methods such as `map`,
`unwrap_or`, and `ok_or` make both cases explicit. This avoids ordinary null
dereferences and lets the compiler check that optionality is respected.

### 9. Error propagation with `?`

**Question:** What does `?` do in the following function? Why must the function
return `Result` or another compatible type?

```rust
fn read_number(text: &str) -> Result<i32, std::num::ParseIntError> {
    let number = text.parse::<i32>()?;
    Ok(number)
}
```

**Explanation:** The `?` operator provides concise early error propagation while
allowing successful execution to continue with the inner value.

**Correct Answer:** If `parse()` returns `Ok(number)`, `?` extracts the number
and execution continues. If it returns `Err(error)`, the current function returns
early with that error, converting it through `From` when necessary. The return
type must be compatible with this early-return behavior.

### 10. Moving data into a thread

**Question:** Does the following code compile? What does `move` do, and what does
`handle.join().unwrap()` mean?

```rust
use std::thread;

let message = String::from("hello");

let handle = thread::spawn(move || {
    println!("{message}");
});

handle.join().unwrap();

println!("{message}");
```

**Explanation:** A `move` closure captures used values by value. This allows a
spawned thread to own its captured data independently of the stack frame that
created it.

**Correct Answer:** The complete code does not compile because `message` moves
into the closure and cannot be used by the final `println!` in the original
thread. `thread::spawn` returns a `JoinHandle<T>`. Calling `join()` consumes the
handle, blocks the current thread until the spawned thread finishes, and returns
`Ok(T)` when it finishes normally or `Err(panic_payload)` when it panics.
Calling `unwrap()` extracts the successful value or panics in the waiting thread
if the spawned thread panicked. In this example the closure returns `()`, so a
successful `handle.join().unwrap()` also evaluates to `()`. Joining the thread
does not move captured values back to the original thread.

## Summary

Today covered:

- immutable bindings by default and explicit mutation with `mut`
- ownership moves for non-`Copy` values such as `String`
- shared and mutable references
- exclusive mutable access and overlapping-borrow prevention
- non-lexical lifetimes and last-use borrow analysis
- implicit copies through the `Copy` trait
- borrowed string slices with `&str`
- optional values with `Option<T>`
- recoverable errors with `Result` and the `?` operator
- moving captured values into spawned threads
- waiting for thread completion with `JoinHandle::join`
- handling a spawned thread's panic result with `unwrap`

## Common Mistakes

- Treating a borrow as ownership temporarily leaving and later returning to the
  original binding. The owner retains ownership throughout a borrow.
- Saying a borrow ends only when its variable leaves the lexical scope. With
  non-lexical lifetimes, it can end after the reference's last use.
- Forgetting that a live `&str` slice prevents mutation of its source `String`.
- Writing `Some<T>` as a value variant; the value constructor is `Some(T)`.
- Treating `move` as a thread operation. It changes how a closure captures
  values; `thread::spawn` then moves that closure into the new thread.
- Assuming `join()` restores values moved into a thread. It only waits and
  returns the closure's return value or panic payload.

## Next Step

Study structs, enums, and exhaustive `match` expressions, followed by traits,
generics, explicit lifetime annotations, iterators, and the `Send` and `Sync`
traits used in concurrent Rust.
