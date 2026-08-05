# Day 015: Linux System Basics / Linux 系统基础

Date / 日期: 2026-07-07

## Topic / 主题

**English:** User/kernel space, system calls, processes and threads, virtual
memory, file descriptors, pipes, `fork/exec`, signals, swap, `mmap`, and the
MMU.

**中文：** 用户态/内核态、系统调用、进程与线程、虚拟内存、文件描述符、管道、
`fork/exec`、信号、swap、`mmap` 与 MMU。

## Goal / 目标

**English:** Build a coherent model of how Linux separates applications from
kernel-managed resources and how processes interact with files, pipes,
sockets, memory, and other programs.

**中文：** 建立 Linux 如何隔离应用与内核资源的连贯模型，并理解进程如何通过
系统调用和文件描述符使用文件、管道、socket、内存与其他程序。

## 10 Concept Questions / 10 个概念问题

### 1. Kernel space and user space / 内核态与用户态

**Question (English):** What are kernel space and user space, and why are they
separated?

**问题（中文）：** 什么是 kernel space 和 user space？为什么要把它们隔离？

**Explanation (English):** The kernel manages hardware and privileged state;
ordinary applications run without direct unrestricted access.

**解说（中文）：** 内核管理 CPU、内存、磁盘、网络设备等特权资源，普通应用不能
不受限制地直接访问。

**Correct Answer (English):** Applications run in user space and use system
calls for privileged operations. Separation improves safety and stability by
preventing ordinary programs from freely reading kernel memory, controlling
hardware, or easily crashing the whole system.

**正确答案（中文）：** 应用运行在用户态，通过系统调用请求内核执行特权操作。
隔离能防止普通程序随意读取内核内存、控制硬件或轻易破坏整个系统，从而提高安全
与稳定性。

### 2. System calls / 系统调用

**Question (English):** What is a system call, and why can an application not
read a disk directly?

**问题（中文）：** 什么是系统调用？用户程序为什么不能直接从磁盘读取文件？

**Explanation (English):** A system call is a controlled transition from user
space into kernel space.

**解说（中文）：** 系统调用是从用户态进入内核态的受控入口。

**Correct Answer (English):** Calls such as `read()`, `write()`, `open()`,
`fork()`, and `mmap()` ask the kernel to perform privileged work. For a read,
the kernel checks descriptors, permissions, page cache, and I/O state before
returning data safely.

**正确答案（中文）：** 程序通过 `read()`、`write()`、`open()`、`fork()`、
`mmap()` 等请求内核执行特权操作。读取文件时，内核检查文件描述符、权限、page
cache 与 I/O 状态，再安全地返回数据。

### 3. Process and thread / 进程与线程

**Question (English):** How do processes and threads differ in resource
ownership and scheduling?

**问题（中文）：** 从资源所有权与执行调度角度看，进程和线程有何区别？

**Explanation (English):** A process is primarily a resource-isolation unit;
a thread is an execution flow sharing much of its process state.

**解说（中文）：** 进程主要是资源隔离单位；线程是通常与同进程其他线程共享资源
的执行流。

**Correct Answer (English):** A process has a virtual address space, file
descriptor table, credentials, and other resource views. Threads in one
process share address space, heap, globals, and open files. Linux schedules
tasks representing both, with different degrees of sharing.

**正确答案（中文）：** 进程拥有虚拟地址空间、文件描述符表、凭据等资源视图。
同进程线程共享地址空间、heap、全局变量和打开文件。Linux 把两者都表示为可调度
task，但资源共享程度不同。

### 4. Virtual memory / 虚拟内存

**Question (English):** Why does each process see a large contiguous address
space even when physical memory is not contiguous?

**问题（中文）：** 物理内存不连续时，为什么每个进程仍感觉拥有很大的连续地址
空间？

**Explanation (English):** The kernel and MMU translate per-process virtual
addresses through page tables.

**解说（中文）：** 每个进程看到自己的虚拟地址空间，内核与 MMU 通过页表把虚拟
地址映射到物理页。

**Correct Answer (English):** Virtual memory combines per-process address
spaces with address translation. Identical virtual addresses in different
processes can map to different pages. It provides isolation, non-contiguous
allocation, demand paging, shared libraries, `mmap()`, and swap.

**正确答案（中文）：** 虚拟内存由每进程虚拟地址空间与页表转换组成。不同进程的
相同虚拟地址可映射到不同物理页。它支持隔离、非连续物理分配、按需分页、共享库、
`mmap()` 和 swap。

### 5. File descriptors / 文件描述符

**Question (English):** What is a file descriptor, and why do `read()` and
`write()` work uniformly for files, sockets, and pipes?

**问题（中文）：** 什么是文件描述符？为什么 `read()` 和 `write()` 能统一
操作文件、socket 与 pipe？

**Explanation (English):** A descriptor is a small process-local integer
referring to a kernel-managed open file object.

**解说（中文）：** 文件描述符是进程中的小整数，指向内核管理的打开文件对象。

**Correct Answer (English):** Descriptors such as 0, 1, and 2 can refer to
regular files, sockets, pipes, terminals, or devices. Applications pass the
fd to system calls, and the kernel dispatches based on the underlying object.

**正确答案（中文）：** 0、1、2 等 fd 可指向普通文件、socket、pipe、terminal
或 device。程序把 fd 传给系统调用，内核再根据底层对象类型分派操作。

### 6. Pipes / 管道

**Question (English):** How does `cat file.txt | grep error` connect two
programs?

**问题（中文）：** `cat file.txt | grep error` 如何连接两个程序？

**Explanation (English):** A pipe is a kernel buffer with a read end and a
write end.

**解说（中文）：** pipe 是具有读端和写端的内核缓冲区。

**Correct Answer (English):** The shell connects `cat` stdout to the write
end and `grep` stdin to the read end. Data streams through the kernel buffer
while both processes can run concurrently.

**正确答案（中文）：** shell 把 `cat` 的 stdout 连接到写端，把 `grep` 的
stdin 连接到读端。数据通过内核缓冲区流动，两个进程可以并发运行。

### 7. fork / fork

**Question (English):** What relationship does `fork()` create, and is all
memory copied immediately?

**问题（中文）：** `fork()` 创建怎样的父子关系？内存会立即完整复制吗？

**Explanation (English):** `fork()` creates a child process from the current
one.

**解说（中文）：** `fork()` 从当前进程创建子进程。

**Correct Answer (English):** The parent receives the child's PID and the
child receives zero; both continue after the call. Modern Linux uses
copy-on-write, sharing pages until either writes. A child can outlive its
parent, and a parent normally uses `wait()`/`waitpid()` to reap it.

**正确答案（中文）：** parent 收到 child PID，child 收到 0，两者从调用后继续。
现代 Linux 使用 copy-on-write，写入前共享物理页。child 可以比 parent 活得久，
parent 通常用 `wait()`/`waitpid()` 回收退出状态。

### 8. exec / exec

**Question (English):** What does the `exec()` family do, and how does a shell
combine it with `fork()`?

**问题（中文）：** `exec()` 系列做什么？shell 如何把它与 `fork()` 组合？

**Explanation (English):** `exec()` replaces the current process image.

**解说（中文）：** `exec()` 替换当前进程映像。

**Correct Answer (English):** It does not create a process. On success it
keeps identity such as PID but replaces code, data, heap, stack, and entry
point. A shell forks a child, the child execs the command, and the parent may
wait.

**正确答案（中文）：** 它本身不创建进程。成功时保留 PID 等身份，但替换 code、
data、heap、stack 与入口。shell 通常 fork child，让 child exec 目标命令，
parent 再 wait。

### 9. Signals / 信号

**Question (English):** What is a signal, what does Ctrl+C normally send, and
what can a process do after receiving one?

**问题（中文）：** 什么是 signal？Ctrl+C 通常发送什么？进程收到后会怎样？

**Explanation (English):** A signal is an asynchronous process notification.

**解说（中文）：** signal 是发送给进程的异步通知。

**Correct Answer (English):** Ctrl+C normally sends `SIGINT` to the foreground
process group, whose default action is termination. Signals have different
defaults; some can be handled or ignored, while `SIGKILL` cannot. Other
examples include `SIGTERM` and `SIGSEGV`.

**正确答案（中文）：** Ctrl+C 通常向前台进程组发送 `SIGINT`，默认动作是终止。
不同信号有不同默认动作；一些可捕获或忽略，`SIGKILL` 不行。其他例子包括
`SIGTERM` 与 `SIGSEGV`。

### 10. Connecting the concepts / 串联概念

**Question (English):** Relate user space, system calls, processes, file
descriptors, and `fork/exec`.

**问题（中文）：** 总结 user space、系统调用、进程、文件描述符与
`fork/exec` 的关系。

**Explanation (English):** Together they describe the path from applications
to kernel-managed resources and program execution.

**解说（中文）：** 这些概念构成用户程序访问内核资源与启动程序的核心路径。

**Correct Answer (English):** Applications run in user space and use system
calls to request kernel services. Processes provide execution and isolation;
file descriptors name open kernel objects. A shell forks a child and execs
the requested program, wiring descriptors and optionally waiting.

**正确答案（中文）：** 应用在用户态运行，通过系统调用请求内核服务。进程提供
执行和隔离，文件描述符指向打开的内核对象。shell fork child 并 exec 目标程序，
同时连接 fd，并可选择 wait。

## Extra Concepts / 补充概念

### Swap / Swap

**English:** Swap is disk-backed fallback space for memory pages. Under RAM
pressure, Linux can move less-used pages out and later restore them. Heavy
swap use is much slower than RAM and can make the system unresponsive.

**中文：** swap 是磁盘支持的内存页后备空间。RAM 紧张时，Linux 可把较少使用的
页面移出并在之后恢复。大量 swap 远慢于 RAM，会让系统明显变慢。

### mmap / mmap

**English:** `mmap()` maps a file or anonymous region into a process's virtual
address space so it can be accessed like memory. It is common for large files,
shared memory, dynamic libraries, and large anonymous allocations.

**中文：** `mmap()` 把文件或匿名区域映射到进程虚拟地址空间，使其可像内存一样
访问。它常用于大文件、共享内存、动态库与大型匿名分配。

### MMU / MMU

**English:** The Memory Management Unit translates virtual addresses through
kernel-maintained page tables. Missing or disallowed mappings raise a page
fault for the kernel to handle.

**中文：** MMU 使用内核维护的页表转换虚拟地址。映射缺失或违反权限时，CPU 触发
page fault，由内核处理。

## Summary / 总结

- **English:** User/kernel separation and system calls protect privileged
  resources.
  **中文：** 用户态/内核态隔离与系统调用保护特权资源。
- **English:** Processes isolate resources; threads share much of their
  process state.
  **中文：** 进程隔离资源；线程共享同进程的大量状态。
- **English:** Virtual memory and the MMU translate isolated address spaces.
  **中文：** 虚拟内存与 MMU 转换隔离的地址空间。
- **English:** File descriptors unify access to files, sockets, pipes,
  terminals, and devices.
  **中文：** 文件描述符统一表示文件、socket、pipe、terminal 与 device。
- **English:** Shell execution composes `fork`, `exec`, descriptors, pipes,
  signals, and `wait`.
  **中文：** shell 执行组合 `fork`、`exec`、fd、pipe、signal 与 `wait`。

## Common Mistakes / 常见错误

- **English:** Treating a process primarily as a hardware scheduling unit
  rather than a resource-isolation unit.
  **中文：** 把进程主要看作硬件调度单位，而不是资源隔离单位。
- **English:** Assuming a child must die when its parent exits.
  **中文：** 误以为 parent 退出后 child 必须终止。
- **English:** Assuming `exec()` creates a new process.
  **中文：** 误以为 `exec()` 创建新进程。
- **English:** Assuming every signal forcibly terminates a program.
  **中文：** 误以为所有 signal 都强制终止程序。
- **English:** Treating a file descriptor as the file itself rather than a
  process-local handle.
  **中文：** 把文件描述符当成文件本身，而不是进程本地句柄。

## Next Step / 下一步

**English:** Study process lifecycle and shell execution in more detail:
`fork`, `exec`, `wait`, zombies, orphans, redirection, and pipelines.

**中文：** 深入学习进程生命周期与 shell 执行：`fork`、`exec`、`wait`、
zombie、orphan、重定向和 pipeline。
