# Day 016: Python Basics

Date: 2026-07-08

## Topic

Python fundamentals: basic data types, type conversion, conditionals, loops, `range`, functions, `return`, `None`, lists, and dictionaries.

## Goal

Build a beginner-friendly foundation for reading and writing Python scripts, especially for later AI, CUDA, benchmarking, automation, and experiment-management workflows.

## 10 Concept Questions

### 1. Basic data types

**Question:** What are the types of the following variables?

```python
name = "CUDA"
days = 90
price = 200.0
enabled = True
items = ["Python", "CUDA", "AI"]
```

**Explanation:** Python values have runtime types. Common beginner types include strings, integers, floats, booleans, and lists.

**Correct Answer:** `name` is `str`, `days` is `int`, `price` is `float`, `enabled` is `bool`, and `items` is `list`. The list contains string elements. In Python, `["Python", "CUDA", "AI"]` is normally called a list, not a string array.

### 2. Numbers and strings

**Question:** What does the following code output?

```python
x = 10
y = "10"

print(x + 5)
print(y + "5")
```

**Explanation:** `+` means numeric addition for numbers and concatenation for strings.

**Correct Answer:**

```text
15
105
```

`x + 5` is integer addition. `y + "5"` joins two strings.

### 3. String concatenation and type conversion

**Question:** Does the following code raise an error? If yes, why?

```python
age = 18
message = "年龄是：" + age
print(message)
```

**Explanation:** Python does not automatically convert an integer into a string when using `+` for string concatenation.

**Correct Answer:** It raises a `TypeError` because `"年龄是："` is `str`, while `age` is `int`. Correct approaches include `str(age)` or an f-string:

```python
message = "年龄是：" + str(age)
message = f"年龄是：{age}"
```

### 4. `if` and `else`

**Question:** What does the following code output?

```python
age = 18

if age >= 18:
    print("adult")
else:
    print("child")
```

**Explanation:** Python uses boolean expressions to choose branches, and indentation defines the code block.

**Correct Answer:**

```text
adult
```

`age >= 18` evaluates to `True`, so the `if` branch runs.

### 5. `if`, `elif`, and branch order

**Question:** What does the following code output, and why is it not `C`?

```python
score = 85

if score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 60:
    print("C")
else:
    print("D")
```

**Explanation:** `if / elif / else` checks conditions from top to bottom and stops at the first matching branch.

**Correct Answer:**

```text
B
```

`score >= 90` is false, but `score >= 80` is true. After the `B` branch runs, the remaining branches are skipped, even though `85 >= 60` is also true.

### 6. `for` loops over a list

**Question:** What does the following code output? What does `for item in items` mean?

```python
items = ["Python", "CUDA", "AI"]

for item in items:
    print(item)
```

**Explanation:** A `for` loop takes one element at a time from an iterable object. `print()` adds a newline by default.

**Correct Answer:**

```text
Python
CUDA
AI
```

`for item in items` means each element in `items` is assigned to the loop variable `item` one by one, then the loop body runs. The loop variable name is reused and rebound each iteration; it is not a new block-scoped variable each time.

### 7. `range`

**Question:** What does the following code output? What numbers does `range(3)` produce?

```python
for i in range(3):
    print(i)
```

**Explanation:** `range(stop)` starts from `0` and stops before `stop`.

**Correct Answer:**

```text
0
1
2
```

`range(3)` represents `0, 1, 2`. It is a `range` object, not directly a list. `list(range(3))` produces `[0, 1, 2]`. To get `[1, 2, 3]`, use `list(range(1, 4))`.

### 8. Functions and `return`

**Question:** What does the following code output? What does `return` do?

```python
def add(a, b):
    return a + b

result = add(3, 5)
print(result)
```

**Explanation:** A function can receive arguments, compute a result, and return that result to the caller.

**Correct Answer:**

```text
8
```

`return a + b` sends the computed value back to the call site and ends the current function execution.

### 9. `print` versus `return`

**Question:** What does the following code output? Why is the second line that result?

```python
def greet(name):
    print("Hello", name)

result = greet("Luca")
print(result)
```

**Explanation:** Printing inside a function is not the same as returning a value from that function.

**Correct Answer:**

```text
Hello Luca
None
```

`print("Hello", name)` prints two arguments separated by a space. Because `greet()` has no explicit `return`, Python returns `None` by default. Therefore `print(result)` prints `None`.

### 10. Dictionaries and nested indexing

**Question:** What does the following code output? What type is `person`?

```python
person = {
    "name": "Luca",
    "age": 18,
    "skills": ["Python", "CUDA"]
}

print(person["name"])
print(person["skills"][1])
```

**Explanation:** A dictionary stores key-value pairs. A value inside a dictionary can itself be a list, dictionary, number, string, or another object.

**Correct Answer:**

```text
Luca
CUDA
```

`person` is a `dict`. `person["name"]` gets the value for key `"name"`. `person["skills"]` gets the list `["Python", "CUDA"]`, and index `[1]` selects `"CUDA"` because Python indexes start at `0`.

## Summary

Today covered:

- Python basic types: `str`, `int`, `float`, `bool`, `list`, and `dict`
- the difference between numeric addition and string concatenation
- converting values with `str()` and formatting with f-strings
- conditional control flow with `if`, `elif`, and `else`
- loop basics with `for`
- `range(stop)` and zero-based counting
- function definition, arguments, and `return`
- the difference between printed output and returned values
- default `None` return values
- dictionary lookup and nested list indexing

## Common Mistakes

- Calling a Python list a string array; `list` is the normal Python term.
- Thinking `range(3)` means `[1, 2, 3]`; it represents `0, 1, 2`.
- Treating `range(3)` as a list directly; use `list(range(3))` when an actual list is needed.
- Expecting Python to concatenate strings and integers automatically.
- Confusing `print()` with `return`.
- Expecting `print("Hello", name)` to insert a comma; it inserts a space by default.
- Assuming a `for` loop variable is newly created in a block scope on every iteration.

## Next Step

Study list and dictionary operations in more detail: adding, removing, updating, searching, iterating, nested structures, and common patterns for small automation scripts.

