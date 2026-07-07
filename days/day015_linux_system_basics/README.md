# Day 015: Linux System Basics

Date: 2026-07-07

## Topic

Linux system fundamentals: user space, kernel space, system calls, processes, virtual memory, file descriptors, pipes, fork/exec, and signals.

## Goal

Build a coherent mental model of how Linux separates user programs from kernel-managed resources, and how processes use system calls and file descriptors to interact with files, pipes, sockets, memory, and other programs.

## 10 Concept Questions

### 1. Kernel space and user space

**Question:** In Linux, what are kernel space and user space? Why are they separated?

**Explanation:** Kernel space is the privileged address space where the kernel runs and manages CPU, memory, disks, network devices, and other hardware resources. User space is where normal applications run without direct hardware access.

**Correct Answer:** User programs run in user space and must use system calls to request privileged operations from the kernel. This separation improves safety and stability because ordinary programs cannot freely read kernel memory, control hardware directly, or crash the whole system as easily.

### 2. System calls

**Question:** What is a system call? If a user program wants to read a file, why can it not directly read from disk?

**Explanation:** A system call is a controlled entry point from user space into kernel space.

**Correct Answer:** A program uses system calls such as `read()`, `write()`, `open()`, `fork()`, and `mmap()` to ask the kernel to perform privileged operations. For file reading, the kernel checks the file descriptor, permissions, page cache, and disk I/O state, then safely copies data back to user space.

### 3. Process and thread

**Question:** What is the difference between a Linux process and a thread? Answer from the angles of resource ownership and execution scheduling.

**Explanation:** A process is mainly a resource isolation unit. A thread is an execution flow that usually shares resources with other threads in the same process.

**Correct Answer:** A process has its own virtual address space, file descriptor table, signal state, credentials, and other resource views. Threads in the same process share much of that state, including address space, heap, global variables, and open files. Linux schedules executable tasks; processes and threads are both represented as schedulable tasks with different degrees of resource sharing.

### 4. Virtual memory

**Question:** What is virtual memory? Why does each process feel like it owns a large continuous memory region even though physical memory may not be continuous?

**Explanation:** Each process sees its own virtual address space. The kernel and MMU map virtual addresses to physical memory pages.

**Correct Answer:** Virtual memory is the combination of a per-process virtual address space and address translation through page tables. Different processes can use the same virtual address values while mapping to different physical pages. Virtual memory provides isolation, supports non-contiguous physical allocation, and enables demand paging, shared libraries, `mmap()`, and swap.

### 5. File descriptors

**Question:** What is a file descriptor in Linux? Why can programs often use `read()` and `write()` uniformly for files, sockets, and pipes?

**Explanation:** A file descriptor is a small integer in a process that refers to an open file object managed by the kernel.

**Correct Answer:** File descriptors such as `0`, `1`, `2`, and later integers point to kernel-side open file objects. The object may represent a regular file, socket, pipe, terminal, or device. User programs pass the fd to system calls, while the kernel dispatches the actual operation based on the underlying object type.

### 6. Pipes

**Question:** What is a Linux pipe? Why can a shell command such as `cat file.txt | grep error` connect one command's output to another command's input?

**Explanation:** A pipe is a kernel buffer with a write end and a read end.

**Correct Answer:** The shell creates a pipe, starts `cat` with its `stdout` connected to the pipe's write end, and starts `grep` with its `stdin` connected to the pipe's read end. Data written by `cat` flows through the kernel pipe buffer and is read by `grep`. Both processes can run concurrently.

### 7. `fork()`

**Question:** What is `fork()`? After `fork()`, what is the relationship between the parent process and child process? Is memory copied immediately?

**Explanation:** `fork()` creates a child process from the current process.

**Correct Answer:** After `fork()`, the parent receives the child's pid and the child receives `0`. Both continue from the same program location after the call. Modern Linux usually uses copy-on-write, so physical memory pages are not immediately fully copied. Pages are shared read-only until one process writes to a page, at which point the kernel copies that page. A child can outlive its parent; the parent is usually responsible for calling `wait()` or `waitpid()` to reap the child's exit status.

### 8. `exec()`

**Question:** What does the `exec()` family of system calls do? How does it usually work with `fork()` to start a new program?

**Explanation:** `exec()` replaces the current process image with a new program.

**Correct Answer:** `exec()` does not create a new process by itself. If successful, it keeps the process identity such as the pid but replaces the current code, data, heap, stack, and entry point with the new program. A shell commonly calls `fork()` to create a child process, then the child calls `exec()` to run the requested command, while the parent may call `wait()`.

### 9. Signals

**Question:** What is a Linux signal? What signal does `Ctrl+C` usually send to the foreground process, and what can happen after a process receives it?

**Explanation:** A signal is an asynchronous notification delivered to a process.

**Correct Answer:** Signals can be sent by the kernel, terminal, user commands, or other processes. `Ctrl+C` usually sends `SIGINT` to the foreground process group, whose default action is termination. Different signals have different default actions; some can be caught or ignored, while `SIGKILL` cannot be caught or ignored. Examples include `SIGTERM`, `SIGKILL`, and `SIGSEGV`.

### 10. Connecting the concepts

**Question:** Summarize the relationship between user space, system calls, process, file descriptor, and fork/exec.

**Explanation:** These concepts form the core path from user programs to kernel-managed resources and program execution.

**Correct Answer:** User programs run in user space. When they need files, network, memory mapping, or process management, they use system calls to enter the kernel. The kernel manages execution and isolation through processes and tasks. A process accesses files, sockets, pipes, terminals, and devices through file descriptors. A shell commonly starts commands by using `fork()` to create a child process and `exec()` in the child to replace it with the target program.

## Extra Concepts

### Swap

`swap` is disk-backed space used as a fallback for memory pages. When RAM is under pressure, Linux can move less-used pages from memory to swap, then bring them back when accessed later. Heavy swap usage is much slower than RAM and can make the system feel slow.

### `mmap()`

`mmap()` maps a file or anonymous memory region into a process's virtual address space. Programs can then access the mapped region like memory. It is commonly used for large files, shared memory, dynamic libraries, and large anonymous allocations.

### MMU

The MMU, or Memory Management Unit, is hardware that translates virtual addresses to physical addresses using page tables maintained by the kernel. If a mapping is missing or violates permissions, the CPU raises a page fault and the kernel handles it.

## Summary

Today covered:

- kernel space and user space separation
- system calls as controlled entries into the kernel
- processes as resource isolation units and threads as shared-resource execution flows
- virtual memory and address translation
- swap, `mmap()`, and the MMU
- file descriptors as a unified I/O abstraction
- pipes as kernel buffers connecting processes
- `fork()` and copy-on-write
- `exec()` as process image replacement
- signals as asynchronous process notifications
- how shell command execution combines `fork()`, `exec()`, file descriptors, pipes, and `wait()`

## Common Mistakes

- Treating a process as a hardware resource scheduling unit instead of primarily a resource isolation unit.
- Thinking a child process must die when its parent exits; a child can outlive its parent and be adopted by `init` or `systemd`.
- Thinking `exec()` creates a new process; it replaces the current process image.
- Thinking every signal forcibly stops a program; many signals can be handled or ignored, depending on the signal.
- Treating a file descriptor as the file itself rather than a process-local handle to a kernel object.

## Next Step

Study the Linux process lifecycle and shell execution model in more detail: `fork`, `exec`, `wait`, zombie processes, orphan processes, stdin/stdout redirection, and pipe pipelines.
