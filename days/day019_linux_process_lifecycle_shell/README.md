# Day 019: Linux Process Lifecycle and Shell Execution / Linux 进程生命周期与 Shell 执行

Date / 日期: 2026-07-15

## Topic / 主题

**English:** Ubuntu Linux process lifecycle and shell execution: `fork`,
`exec`, `wait`, exit status, zombie and orphan processes, file-descriptor
redirection, pipelines, and background jobs.

**中文：** Ubuntu Linux 进程生命周期与 Shell 执行：`fork`、`exec`、`wait`、
退出状态、僵尸进程与孤儿进程、文件描述符重定向、管道以及后台任务。

## Goal / 目标

**English:** Understand how an Ubuntu shell creates and manages commands, how
process state is collected, and how standard streams are connected to files
and other processes.

**中文：** 理解 Ubuntu Shell 如何创建和管理命令、如何收集进程状态，以及如何
把标准流连接到文件和其他进程。

## 10 Concept Questions / 10 道概念题

### 1. `fork` and `exec` / `fork` 与 `exec`

**Question (English):** When a shell runs `ls`, what do `fork()` and `exec()`
do, and why are they commonly used together?

**问题（中文）：** Shell 运行 `ls` 时，`fork()` 和 `exec()` 分别做什么？为什么
通常要一起使用它们？

**Explanation (English):** A shell needs to preserve its own process while
starting another program in a child process.

**解说（中文）：** Shell 需要在保留自身进程的同时，在子进程中启动另一个程序。

**Correct Answer (English):** `fork()` creates a child process based on the
current shell. The child then calls `exec()` to replace its process image with
`ls`. `exec()` does not create a process. Using both lets the parent shell
remain available after `ls` exits.

**正确答案（中文）：** `fork()` 基于当前 Shell 创建子进程，随后子进程调用
`exec()`，用 `ls` 替换自己的进程映像。`exec()` 本身不创建进程。两者结合后，
父 Shell 可以在 `ls` 退出后继续工作。

### 2. Waiting for a foreground child / 等待前台子进程

**Question (English):** Why does a shell normally call `wait()` or `waitpid()`
after starting a foreground command such as `sleep 3`? What could happen if it
did not wait?

**问题（中文）：** Shell 启动 `sleep 3` 这样的前台命令后，为什么通常要调用
`wait()` 或 `waitpid()`？如果不等待，可能出现什么现象？

**Explanation (English):** Waiting coordinates terminal interaction, obtains
the child's exit status, and lets the kernel release the child's remaining
process record.

**解说（中文）：** 等待操作用于协调终端交互、获取子进程退出状态，并让内核释放
子进程剩余的进程记录。

**Correct Answer (English):** The shell waits so the foreground command owns
the terminal until completion, then collects its status and reaps it. Without
waiting, the prompt could return immediately while the child still runs, and
their terminal output could interleave. The child's output is not
automatically discarded.

**正确答案（中文）：** Shell 等待前台命令完成，使其在运行期间占用终端，随后收集
退出状态并回收进程。如果不等待，提示符可能立即返回，而子进程仍在运行，两者的
终端输出可能交错。子进程的输出不会自动被丢弃。

### 3. Command exit status / 命令退出状态

**Question (English):** What does the following print, what does `$?` mean,
and why does the shell preserve an exit status?

**问题（中文）：** 下面的命令输出什么？`$?` 表示什么？Shell 为什么要保存退出
状态？

```bash
false
echo $?
```

**Explanation (English):** Unix commands report success or failure using a
small integer status that shell control flow can inspect.

**解说（中文）：** Unix 命令使用一个小整数状态报告成功或失败，Shell 控制流可以
检查这个状态。

**Correct Answer (English):** It prints `1`. `$?` is the most recent command's
exit status. Zero conventionally means success and nonzero means failure.
Shell scripts, `if`, `&&`, and `||` use this status to choose subsequent work.

**正确答案（中文）：** 输出 `1`。`$?` 是最近一条命令的退出状态。按照惯例，0
表示成功，非 0 表示失败。Shell 脚本、`if`、`&&` 和 `||` 会根据该状态决定后续
操作。

### 4. Preserving an exit status / 保存退出状态

**Question (English):** Why does the final line print zero, and how can the
status from `false` be preserved?

**问题（中文）：** 为什么最后一行输出 0？怎样保存 `false` 的退出状态？

```bash
false
echo "hello"
echo $?
```

**Explanation (English):** `$?` is overwritten after every command, including
a successful `echo`.

**解说（中文）：** 每条命令执行后都会覆盖 `$?`，成功执行的 `echo` 也不例外。

**Correct Answer (English):** The last status is zero because `echo "hello"`
succeeded. Save the earlier status immediately:

**正确答案（中文）：** 最后的状态是 0，因为 `echo "hello"` 执行成功。必须立即
保存之前的状态：

```bash
false
status=$?
echo "hello"
echo "$status"
```

**English:** The last line now prints `1`.

**中文：** 此时最后一行输出 `1`。

### 5. Zombie processes / 僵尸进程

**Question (English):** What is a zombie process? Is it still executing and
consuming CPU?

**问题（中文）：** 什么是僵尸进程？它是否仍在执行并消耗 CPU？

**Explanation (English):** Process execution can finish before the parent has
collected the child's termination information.

**解说（中文）：** 子进程可能已经结束执行，但父进程尚未收集其终止信息。

**Correct Answer (English):** A zombie is a child that has exited but whose
parent has not yet read its exit status with `wait` or `waitpid`. It no longer
executes or consumes CPU, but the kernel keeps a small record containing its
PID and termination information until it is reaped.

**正确答案（中文）：** 僵尸进程是已经退出、但父进程尚未通过 `wait` 或
`waitpid` 读取其退出状态的子进程。它不再执行或消耗 CPU，但内核会保留包含 PID
和终止信息的少量记录，直到它被回收。

### 6. Orphan processes / 孤儿进程

**Question (English):** What happens when a parent exits while its child is
still running? How does an orphan differ from a zombie?

**问题（中文）：** 父进程退出而子进程仍在运行时会发生什么？孤儿进程与僵尸进程
有什么区别？

**Explanation (English):** A running child does not normally have to terminate
only because its original parent exits.

**解说（中文）：** 正在运行的子进程通常不会仅因原父进程退出而被强制终止。

**Correct Answer (English):** The running child becomes an orphan and is
normally adopted by PID 1 (`systemd` on Ubuntu) or a designated subreaper. An
orphan is still running after losing its parent; a zombie has already exited
but has not yet been reaped.

**正确答案（中文）：** 仍在运行的子进程会成为孤儿进程，通常由 PID 1（Ubuntu
中的 `systemd`）或指定的 subreaper 接管。孤儿进程是在失去父进程后仍继续运行；
僵尸进程则已经退出，但尚未被回收。

### 7. Redirecting standard output / 重定向标准输出

**Question (English):** What does `ls > files.txt` do to file descriptor 1,
and what happens if the file already exists?

**问题（中文）：** `ls > files.txt` 会如何处理文件描述符 1？如果文件已经存在，
会发生什么？

**Explanation (English):** Redirection changes what a process's file
descriptor refers to. It is different from connecting two processes with a
pipeline.

**解说（中文）：** 重定向会改变进程文件描述符所引用的对象，这不同于使用管道
连接两个进程。

**Correct Answer (English):** The shell opens `files.txt`, makes the child's
file descriptor 1 (standard output) refer to it, and normally truncates an
existing file before running `ls`. `>` is output redirection, not a pipeline.

**正确答案（中文）：** Shell 打开 `files.txt`，让子进程的文件描述符 1（标准
输出）指向该文件，并通常在运行 `ls` 前截断已有文件。`>` 是输出重定向，不是
管道。

### 8. Output and error redirection / 输出与错误重定向

**Question (English):** Explain the differences among `>`, `>>`, and `2>` in
the following commands.

**问题（中文）：** 解释下面命令中 `>`、`>>` 和 `2>` 的区别。

```bash
command > output.txt
command >> output.txt
command 2> error.txt
```

**Explanation (English):** Standard output and standard error use distinct
file descriptors, and shell redirection can choose truncation or append mode.

**解说（中文）：** 标准输出与标准错误使用不同的文件描述符，Shell 重定向还可以
选择截断或追加模式。

**Correct Answer (English):** `>` redirects file descriptor 1 (stdout) and
truncates the destination. `>>` redirects stdout in append mode. `2>` redirects
file descriptor 2 (stderr) and truncates the destination.

**正确答案（中文）：** `>` 重定向文件描述符 1（stdout）并截断目标文件；`>>`
以追加模式重定向 stdout；`2>` 重定向文件描述符 2（stderr）并截断目标文件。

### 9. Connecting processes with a pipeline / 使用管道连接进程

**Question (English):** How are file descriptors connected in
`cat access.log | grep "ERROR"`, and can both processes run concurrently?

**问题（中文）：** 在 `cat access.log | grep "ERROR"` 中，文件描述符如何连接？
两个进程能否并发运行？

**Explanation (English):** A pipe is a kernel buffer with a write end and a
read end. It supports streaming between concurrently running processes.

**解说（中文）：** 管道是具有写端和读端的内核缓冲区，支持在并发运行的进程之间
进行流式传输。

**Correct Answer (English):** `cat` writes through file descriptor 1 (stdout)
to the pipe, and `grep` reads the pipe through file descriptor 0 (stdin). The
processes normally run concurrently, so `grep` can process data as `cat`
produces it.

**正确答案（中文）：** `cat` 通过文件描述符 1（stdout）写入管道，`grep` 通过
文件描述符 0（stdin）从管道读取。两个进程通常并发运行，因此 `grep` 可以在
`cat` 产生数据的同时进行处理。

### 10. Background jobs / 后台任务

**Question (English):** What does `&` do in `sleep 60 &`? Is the process an
orphan, and how can the shell inspect or return it to the foreground?

**问题（中文）：** `sleep 60 &` 中的 `&` 有什么作用？该进程是孤儿进程吗？Shell
如何查看它或将其切回前台？

**Explanation (English):** Shell job control distinguishes foreground jobs
from background jobs while retaining the shell as their parent and manager.

**解说（中文）：** Shell 作业控制区分前台任务与后台任务，同时 Shell 仍作为这些
任务的父进程和管理者。

**Correct Answer (English):** `&` starts the command as a background job, so
the shell normally displays a new prompt immediately. It is not an orphan
because the shell remains its parent. Use `jobs` to list shell jobs and
`fg %1` to bring job 1 to the foreground. `top` can observe processes but does
not perform shell job control.

**正确答案（中文）：** `&` 会把命令作为后台任务启动，因此 Shell 通常立即显示
新的提示符。它不是孤儿进程，因为 Shell 仍是它的父进程。使用 `jobs` 查看 Shell
任务，使用 `fg %1` 将编号 1 的任务切回前台。`top` 可以观察进程，但不能执行
Shell 作业控制。

## Summary / 总结

### Concepts Understood / 已掌握概念

- **English:** `fork` creates a child, while `exec` replaces a process image.
  **中文：** `fork` 创建子进程，`exec` 替换进程映像。
- **English:** `wait` coordinates foreground execution, collects status, and
  reaps child processes. **中文：** `wait` 协调前台执行、收集退出状态并回收子
  进程。
- **English:** Exit status zero conventionally indicates success, and `$?`
  stores only the latest status. **中文：** 按照惯例，退出状态 0 表示成功，而
  `$?` 只保存最近一次状态。
- **English:** Zombies have exited but are not reaped; orphans are still
  running after their parent exits. **中文：** 僵尸进程已经退出但尚未回收；孤儿
  进程则在父进程退出后仍继续运行。
- **English:** File descriptors 0, 1, and 2 represent stdin, stdout, and stderr.
  **中文：** 文件描述符 0、1 和 2 分别表示 stdin、stdout 和 stderr。
- **English:** Redirection connects streams to files, while a pipeline connects
  processes and allows concurrent streaming. **中文：** 重定向把流连接到文件，
  管道则连接进程并支持并发流式处理。
- **English:** `&`, `jobs`, and `fg` are basic shell job-control mechanisms.
  **中文：** `&`、`jobs` 和 `fg` 是基本的 Shell 作业控制机制。

## Common Mistakes / 常见错误

- **English:** Assuming child output is discarded when the parent does not
  wait. **中文：** 误以为父进程不等待时，子进程输出会被丢弃。
- **English:** Thinking `exec` creates a process instead of replacing the
  current process image. **中文：** 误以为 `exec` 创建进程，而不是替换当前
  进程映像。
- **English:** Forgetting that another command overwrites `$?`.
  **中文：** 忘记执行另一条命令会覆盖 `$?`。
- **English:** Confusing a running orphan with an exited zombie.
  **中文：** 混淆仍在运行的孤儿进程与已经退出的僵尸进程。
- **English:** Calling Ubuntu's adoption process `system`; it is normally PID 1
  running `systemd`. **中文：** 把 Ubuntu 中的接管进程称为 `system`；它通常是
  运行 `systemd` 的 PID 1。
- **English:** Treating `>` as a pipeline rather than file redirection.
  **中文：** 把 `>` 当作管道，而不是文件重定向。
- **English:** Describing file descriptor 1 only as a generic system resource
  instead of identifying it as stdout. **中文：** 只把文件描述符 1 描述为普通
  系统资源，而没有指出它是 stdout。
- **English:** Expecting `sleep 60 &` to block the prompt, or using `top` in
  place of `jobs` and `fg`. **中文：** 误以为 `sleep 60 &` 会阻塞提示符，或者
  使用 `top` 代替 `jobs` 和 `fg`。

## Next Step / 下一步

**English:** Study Ubuntu signals and job control: `Ctrl+C`, `Ctrl+Z`,
`SIGINT`, `SIGTSTP`, `SIGTERM`, `SIGKILL`, `kill`, `bg`, `fg`, process groups,
and terminal foreground ownership.

**中文：** 接下来学习 Ubuntu 信号与作业控制：`Ctrl+C`、`Ctrl+Z`、`SIGINT`、
`SIGTSTP`、`SIGTERM`、`SIGKILL`、`kill`、`bg`、`fg`、进程组以及终端前台
所有权。
