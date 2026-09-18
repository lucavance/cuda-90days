# Course 01: Linux and GPU Development Environments / 课程 01：Linux 与 GPU 开发环境

## Learning Contract and Evidence / 学习目标与证据边界

**English:** This course turns familiar Linux commands into an operational model for AI infrastructure. By the end, you should be able to explain which process owns a request, which descriptor keeps a resource alive, why a service has not exited, and which layer prevents a GPU program from starting. The practical output is a reproducible CPU laboratory and an environment evidence report. A successful installation command, a running process, and a completed GPU computation are three different claims that require different evidence.

**中文：** 本课把熟悉的 Linux 命令串成面向 AI 基础设施的运行模型。学完后，你应能解释哪个进程负责一个请求、哪个描述符维持着资源的生命、服务为什么没有退出，以及哪一层阻止了 GPU 程序启动。实际产物是一组可复现的 CPU 实验和一份环境证据报告。安装命令成功、进程正在运行、GPU 计算已经完成，是三个不同的结论，必须分别提供证据。

**English:** The intended reader has already delivered system or server software. Basic terminal use and the ability to read short Python and C programs are sufficient prerequisites. The examples do not require machine-learning mathematics or access to a working GPU. They consolidate the process and shell material from Days 015, 019, and 036, then connect it to driver libraries, CUDA tools, containers, and performance investigation. Treat familiar concepts as opportunities to predict observable behavior before running the examples.

**中文：** 本课面向已经交付过系统软件或服务端软件的开发者。前置要求是会使用终端，并能阅读简短的 Python 与 C 程序，不要求掌握机器学习数学，也不要求当前 GPU 可用。内容整合第十五、第十九、第三十六天的进程与 Shell 知识，再连接到驱动库、CUDA 工具、容器和性能调查。对于熟悉的概念，也应先预测可观察结果再执行示例，用结果检验自己的理解。

**English:** Documentation was checked on 2026-09-18. The supplied local baseline is Ubuntu 26.04.1, an RTX 4060, and CUDA Toolkit 13.3. The environment report identifies NVML 610.57 and a loaded NVIDIA kernel module at 610.43.02, with a driver/library mismatch. These are the recorded conditions for this lesson, not a compatibility recommendation. GPU execution and GPU performance results remain unverified here. The exercises neither repair the driver nor reload modules, change packages, or reboot the machine.

**中文：** 官方资料核验日期为二〇二六年九月十八日。提供的本机基线是 Ubuntu 26.04.1、RTX 4060 和 CUDA Toolkit 13.3。环境报告记录了 NVML 610.57 与已加载 NVIDIA 内核模块 610.43.02，并出现驱动与库版本不匹配。它们是本课记录的环境条件，不是推荐的兼容组合。本课没有验证 GPU 执行或 GPU 性能结果。实验不会修复驱动、重新加载模块、更改软件包或重启机器。

**English:** Versioned documentation matters because an unversioned vendor page can describe a newer release than the installed tools. Use the CUDA 13.3 archive for statements about this toolkit, and separately record the actual compiler and loaded module. The installation guide lists host operating-system and compiler qualifications; passing those qualifications does not demonstrate that every component on one machine was installed consistently. [CUDA 13.3 Linux installation guide](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html) When reading documentation, identify the version it describes; when inspecting a machine, identify the version actually selected.

**中文：** 带版本的文档十分重要，因为厂商的无版本链接可能已经描述比本机更新的版本。讨论这里的工具包时，应使用 CUDA 13.3 归档，同时单独记录实际编译器与已加载模块。安装指南列出操作系统和主机编译器的支持条件，但满足这些条件，并不能证明某台机器上的所有组件已经保持一致。阅读文档要回答它适用于哪个版本，检查机器要回答当前真正使用哪个版本。[CUDA 13.3 Linux 安装指南](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html)

## 1. Follow the Request Across Boundaries / 沿请求追踪系统边界

**English:** Imagine a speech device submitting a prompt to a server. A socket becomes readable, a worker validates the request, a tokenizer prepares input, a runtime selects work, and a driver submits GPU operations. Each arrow crosses a resource or scheduling boundary. An empty GPU timeline could mean that tokenization is slow, a queue is blocked, a worker crashed, or driver initialization failed. The useful first question is therefore where progress stopped, followed by what evidence distinguishes the possible causes.

**中文：** 假设一台语音设备向服务器提交提示词。套接字变得可读，工作进程校验请求，分词器准备输入，运行时挑选任务，驱动再提交 GPU 操作。每一步都跨越资源或调度边界。GPU 时间线上没有工作，可能是分词慢、队列阻塞、工作进程崩溃，也可能是驱动初始化失败。因此，首先要问的是进展停在哪一步，再寻找能够区分这些原因的证据，而不是立即调整显卡参数。

**English:** User space contains your application and most libraries; kernel space manages protected resources and mediates operations such as creating processes, accessing files, and communicating with devices. A library function is not necessarily a system call. A buffered write can complete in the application without having reached the destination, and a CUDA submission can return before device execution completes. Always name the boundary that an observation crosses: accepted by a library, submitted to the kernel, scheduled on hardware, or completed and made visible.

**中文：** 用户空间包含应用和大多数库，内核空间负责受保护资源，并协调创建进程、访问文件以及与设备通信等操作。库函数并不必然对应一次系统调用。缓冲写入可以在应用里完成，却尚未到达目标；CUDA 提交也可能在设备执行结束前返回。描述观察结果时，要指出它跨越了哪一道边界：被库接收、交给内核、安排到硬件，还是已经完成并对后续操作可见。

**English:** A process gives an executing program an identity and a set of resources. Threads within that process generally share its address space and descriptor table while retaining their own execution state. Increasing worker processes can isolate failures, but it can also duplicate model state, increase coordination, and compete for the same device. Increasing threads can improve overlap without making a serial critical section parallel. Before changing worker counts, draw the ownership of the model, queues, connections, and device context.

**中文：** 进程为正在执行的程序提供身份和一组资源。同一进程中的线程通常共享地址空间与描述符表，同时保留各自的执行状态。增加工作进程有助于隔离故障，却也可能复制模型状态、增加协调开销，并争夺同一设备。增加线程能够改善重叠执行，但不会自动让串行临界区变成并行。修改工作进程数量之前，应先画清模型、队列、连接和设备上下文分别由谁持有。

**English:** Virtual memory is an address-management mechanism, not a promise that all mapped bytes occupy RAM. A process can reserve address space, map a file, share pages, and acquire physical pages as they are used. RSS, virtual size, file cache, and device memory answer different questions. If a model loader maps a large weight file, the virtual size alone cannot establish a leak. A useful investigation follows the same workload over time and asks which ownership event should release the growing resource.

**中文：** 虚拟内存是一种地址管理机制，并不承诺所有映射的字节都已经占用物理内存。进程可以保留地址空间、映射文件、共享页面，并在使用时获得物理页。常驻内存、虚拟空间、文件缓存和设备显存回答的是不同问题。模型加载器映射一个大权重文件后，不能仅凭虚拟空间变大就判定泄漏。有效的调查应持续观察同一负载，并明确哪一个所有权事件本应释放正在增长的资源。

## 2. Process Creation, Replacement, and Reaping / 进程创建、替换与回收

**English:** In the classic Unix model, `fork()` creates a child process and `execve()` replaces the calling process image with another program. They are separate operations: replacing a program does not by itself create a new PID. Linux ordinarily uses copy-on-write for the child's inherited address space, while inherited descriptors refer to the corresponding open-file descriptions. These distinctions explain why launching a worker is more than copying an executable into memory. [fork](https://man7.org/linux/man-pages/man2/fork.2.html), [execve](https://man7.org/linux/man-pages/man2/execve.2.html) Worker startup therefore includes resource inheritance and execution identity.

**中文：** 在经典 Unix 模型中，`fork()` 创建子进程，`execve()` 则把调用进程的程序映像替换为另一个程序。二者是分开的操作：替换程序本身并不会创建新的进程编号。Linux 通常通过写时复制处理子进程继承的地址空间，而继承的描述符会指向相应的打开文件描述。这些区别解释了为什么启动工作进程不只是把可执行文件复制进内存，还涉及资源继承和执行身份。[fork](https://man7.org/linux/man-pages/man2/fork.2.html)、[execve](https://man7.org/linux/man-pages/man2/execve.2.html)

**English:** At the application level, prefer the process-launch abstraction supplied by your language unless you need lower-level control. Python's `subprocess` is a useful laboratory interface, but do not assume that every invocation literally performs a `fork()` followed by `execve()`; implementations may choose another launch mechanism. What matters for this course is its contract: arguments are supplied, selected streams are connected, a child is created, and the parent can observe completion and its return code. Understanding the contract is more reliable than memorizing one implementation path.

**中文：** 在应用层，除非需要更底层的控制，否则优先使用语言提供的进程启动接口。Python 的 `subprocess` 很适合作为本课实验接口，但不能假设每一次调用都严格执行一次 `fork()` 再执行一次 `execve()`，实现可能选择其他启动方式。本课关注的是它的契约：传入参数、连接指定的数据流、创建子进程，以及让父进程观察完成状态和返回码。理解契约比记住某一次实现路径更可靠。

**English:** A terminated child can leave a small kernel record until its parent obtains the exit status with a wait operation. That state is a zombie; it is not a worker still performing computation. A live child whose parent disappears is an orphan, and reparenting rules determine who later collects its status. Confusing these cases leads to ineffective responses such as repeatedly signaling a process that has already exited. [wait and child states](https://man7.org/linux/man-pages/man2/waitpid.2.html) Inspect both process state and parent-child relationships.

**中文：** 子进程终止后，内核可能保留一小份记录，直到父进程通过等待操作取得退出状态。这就是僵尸状态，并不是仍在执行计算的工作进程。父进程消失而子进程仍活着，则属于孤儿情形，后续由重新指定的父进程负责回收状态。混淆这两种情况，会导致对已经结束的进程反复发送信号等无效处理。排查时应同时观察运行状态和父子关系。[等待与子进程状态](https://man7.org/linux/man-pages/man2/waitpid.2.html)

**English:** Return codes are part of an interface, so define their meaning explicitly. A nonzero code can represent invalid input, dependency failure, or an interrupted operation; it is not enough to save only the last log line. Also distinguish a subprocess return code from a shell's representation of signal termination. Python uses a negative value for a child terminated by a signal on POSIX, whereas a shell commonly reports a positive status related to that signal. Record the API that produced the number.

**中文：** 返回码属于接口的一部分，应明确规定其含义。非零返回值可能表示输入不合法、依赖故障或操作中断，因此只保存最后一行日志是不够的。还要区分子进程接口的返回码与 Shell 对信号终止的表示方式。在 POSIX 系统上，Python 用负数表示子进程被某个信号终止，而 Shell 常用与该信号有关的正状态值。记录一个数字时，也应记录它由哪个接口产生，避免误读。

## 3. Descriptors, Open Files, and Ownership / 描述符、打开文件与所有权

**English:** A file descriptor is a small integer in a process's descriptor table. It is a handle to a kernel-managed object, not the bytes of the file and not a globally unique filename. The conventional descriptors zero, one, and two represent standard input, output, and error. Duplicated descriptors can share an open-file description and its current offset; opening the same pathname twice can instead create two independent offsets. [open and open-file descriptions](https://man7.org/linux/man-pages/man2/open.2.html) This distinction determines whether two users affect each other's read position.

**中文：** 文件描述符是进程描述符表中的一个小整数，它是指向内核管理对象的句柄，不是文件内容，也不是全局唯一的文件名。惯例中的零、一、二分别表示标准输入、标准输出和标准错误。复制出来的描述符可能共享同一个打开文件描述及当前位置，而对同一路径分别打开两次，则可能得到两个独立的偏移位置。理解这种区别，才能判断两个使用者是否正在互相影响读取进度。[打开文件与描述符](https://man7.org/linux/man-pages/man2/open.2.html)

**English:** This is an ownership problem much like a Rust resource wrapper, except that the operating system cannot infer your intended lifetime. A socket can remain open because a worker inherited it; a log file can still consume space after its directory entry is removed because a process holds the open file. Closing one duplicated handle does not necessarily end the resource's lifetime. During diagnosis, list the actual descriptor owners rather than assuming that the most visible parent process is the only owner.

**中文：** 这与 Rust 资源包装器中的所有权问题很相似，只是操作系统无法推断你打算维持多久的生命周期。工作进程继承了套接字，就可能让连接持续打开；目录项被删除后，进程仍持有打开文件，也可能让日志继续占用空间。关闭一个复制出来的句柄，并不一定结束资源寿命。排查时应列出实际持有描述符的进程，不能假设最显眼的父进程就是唯一的资源拥有者。

**English:** In a request server, descriptors connect lifetime bugs to capacity failures. Suppose every completed request leaves one temporary file open. The first requests may succeed, while later unrelated requests fail when the process reaches its descriptor limit. Restarting restores capacity temporarily but does not explain the leak. A better experiment runs a fixed number of requests, samples descriptor counts before and after, repeats the cycle, and checks whether the count returns to the same baseline after cleanup.

**中文：** 在请求服务器里，描述符会把生命周期错误变成容量故障。假设每个完成的请求都留下一个未关闭的临时文件，开始的请求可能成功，后续互不相关的请求却在进程达到描述符上限后失败。重启只能暂时恢复容量，不能解释泄漏。更好的实验是运行固定数量的请求，分别采样前后的描述符数量，重复这个周期，再检查清理完成后是否回到相同基线，从趋势定位责任边界。

## 4. Pipes, Backpressure, and Redirection / 管道、背压与重定向

**English:** A pipe is a byte stream with finite buffering. A reader sees end-of-file only after the data has been consumed and all descriptors referring to the write end are closed. A writer can block when the buffer is full. This makes descriptor lifetime observable as flow control: a forgotten writer can keep a reader waiting forever even though the producer you were watching has already exited. [Linux pipe semantics](https://man7.org/linux/man-pages/man7/pipe.7.html) For a pipeline that never finishes, investigate every writer rather than only the process that most recently logged output.

**中文：** 管道是带有限缓冲区的字节流。只有数据已经被读完，并且所有指向写入端的描述符都关闭，读取方才会看到文件结束。缓冲区满时，写入方也可能阻塞。于是，描述符寿命直接影响数据流控制：即使你一直观察的生产者已经退出，一个被遗忘的写入端仍然可能让读取方永远等待。遇到没有结束的流水线，要调查所有写入端，而不只是最后写日志的进程。[Linux 管道语义](https://man7.org/linux/man-pages/man7/pipe.7.html)

**English:** A common supervisor deadlock is to wait for a child to exit before draining its captured output. The child fills the output pipe and waits for the parent to read; the parent waits for the child to finish. Neither side can make progress. For bounded output, `communicate()` provides a convenient collection interface; for large or continuous output, stream both channels or redirect them to files. The main laboratory below uses files so that the teaching supervisor does not accidentally introduce this deadlock.

**中文：** 一种常见的监管进程死锁，是先等待子进程退出，再读取它被捕获的输出。子进程把输出管道写满，等待父进程读取；父进程又等待子进程结束，双方都无法推进。输出量有界时，可以使用 `communicate()` 收集；对于大量或连续输出，则应持续消费两个通道，或者重定向到文件。后面的主实验采用文件，避免教学用监管程序自己引入这类死锁，使读者能集中观察生命周期。

**English:** Redirection changes descriptor connections in order. In `command >out 2>&1`, standard output is connected to the file before standard error duplicates that connection. In `command 2>&1 >out`, standard error first duplicates the original output destination, and only output is then redirected. Neither form means that error bytes are retrospectively moved elsewhere. Draw the destinations of descriptors one and two after each operation, and the apparently mysterious difference becomes a short sequence of assignments.

**中文：** 重定向按顺序改变描述符连接。执行 `command >out 2>&1` 时，先把标准输出接到文件，再让标准错误复制这个连接。执行 `command 2>&1 >out` 时，标准错误先复制原来的输出目标，随后只有标准输出被改到文件。两者都不是把已经发出的错误字节重新搬走。逐步画出描述符一和二在每次操作后的目标，看似难记的差别就变成一串清楚的连接变化。

**English:** A pipeline's status also needs an explicit policy. In Bash, the default status is the last command's status; enabling `pipefail` makes a failing earlier command affect the pipeline result. This is particularly important for `producer | tee log`: a successful logger does not prove successful production. The course invokes Bash explicitly because your interactive shell may be zsh and status arrays differ. A Bash-specific script should not silently depend on the caller's shell. [GNU Bash reference manual](https://www.gnu.org/s/bash/manual/bash.html)

**中文：** 流水线的状态同样需要明确策略。在 Bash 中，默认采用最后一个命令的状态；启用 `pipefail` 后，前面命令的失败也会影响整条流水线。这对于 `producer | tee log` 尤其重要：日志保存成功，不代表生产数据成功。本课明确调用 Bash，因为交互终端可能使用 zsh，而不同 Shell 的状态数组并不相同。采用 Bash 特性的脚本，不应暗中依赖调用者恰好使用同一种 Shell。[GNU Bash 参考手册](https://www.gnu.org/s/bash/manual/bash.html)

## 5. Signals and Service Shutdown / 信号与服务退出

**English:** A signal is a notification with a defined disposition. `SIGTERM` gives a program an opportunity to implement orderly shutdown, while `SIGKILL` cannot be caught to run cleanup. Signal delivery does not establish that work has completed, logs are durable, or children have exited. The sender still needs a completion observation such as waiting for its child. [Linux signal overview](https://man7.org/linux/man-pages/man7/signal.7.html) Separating notification from confirmed completion avoids treating a returned stop command as proof that every resource was released.

**中文：** 信号是一种有明确处理方式的通知。`SIGTERM` 允许程序实现有序退出，而 `SIGKILL` 不能被捕获来执行清理。发送信号本身，并不能证明工作已经完成、日志已经持久化或者子进程已经结束。发送者还需要通过等待子进程等方式观察最终完成状态。把发送通知和确认完成分开，是写好服务管理程序的重要基础，也能避免把停止命令返回误当成所有资源均已释放。[Linux 信号概览](https://man7.org/linux/man-pages/man7/signal.7.html)

**English:** For inference serving, orderly shutdown is a small state machine: stop accepting new work, decide what to do with queued requests, finish or cancel active work under a deadline, release owned resources, and publish a terminal state. The exact cancellation contract belongs to the runtime. Closing a client socket does not automatically guarantee that already submitted GPU operations stop. Even when a request is no longer useful to the client, the server must track outstanding work until its resource obligations are satisfied.

**中文：** 对推理服务来说，有序退出是一个小型状态机：停止接收新任务，决定如何处理排队请求，在期限内完成或取消正在执行的工作，释放拥有的资源，并公布终止状态。具体取消契约由运行时决定。关闭客户端套接字，并不自动保证已经提交的 GPU 操作停止。即使一个请求对客户端已无价值，服务器仍需要跟踪尚未完成的工作，直到它对资源承担的责任真正结束，才能安全回收相关对象。

**English:** Signaling the launcher and signaling the entire worker group are different operations. A wrapper can exit while its child continues running, particularly when the wrapper does not forward signals or wait for children. Service managers can supervise a group of processes, but the application still needs an explicit shutdown design. In this course, the supervisor directly owns each worker and only signals that known child. Do not adapt the example into broad process-name matching that might affect another user's workload.

**中文：** 给启动器发送信号，与给整个工作进程组发送信号，是不同的操作。包装脚本可能已经退出，但它创建的子进程仍在运行，特别是包装脚本没有转发信号或等待子进程时。服务管理器可以监管一组进程，应用自身仍需设计退出流程。本课监管程序直接拥有每个工作进程，并且只向这个已知子进程发信号。实际应用时也应保留明确的对象关系，避免用模糊的进程名匹配影响别人的任务。

## 6. Main CPU Laboratory: Own the Whole Lifecycle / CPU 主实验：管理完整生命周期

**English:** Run the following complete block from any writable working directory. It creates a uniquely named temporary directory, writes a worker and supervisor, and exercises success, application failure, and graceful termination. The worker emits structured events on standard output and diagnostics on standard error. There is no GPU work: the checksum is deliberately small and only makes request ownership concrete. Keep the printed artifact directory until you have compared the three event sequences. Compare the process evidence before reducing the experiment to its final status.

**中文：** 在任意可写工作目录执行下面的完整代码块。它会创建一个独有名称的临时目录，写入工作进程和监管程序，分别演示成功、应用失败和有序终止。工作进程通过标准输出发出结构化事件，通过标准错误记录诊断信息。这里没有 GPU 工作，小型校验计算只是为了让请求所有权更具体。请先保留程序打印的实验目录，比较三种事件序列后再决定是否删除，避免只看到总结果而遗漏过程证据。

```bash
# experiment: process-lab
COURSE01_DIR=$(mktemp -d /tmp/course01-process-XXXXXX)
export COURSE01_DIR
cat > "$COURSE01_DIR/worker.py" <<'PY'
import json
import os
from pathlib import Path
import signal
import sys
import time

mode, ready_path = sys.argv[1:]
stopping = False

def on_term(signum, frame):
    global stopping
    stopping = True

signal.signal(signal.SIGTERM, on_term)

def emit(event, **fields):
    print(json.dumps({"event": event, "pid": os.getpid(), **fields}), flush=True)

emit("started", parent=os.getppid(), mode=mode)
Path(ready_path).write_text("ready\n")
try:
    if mode == "fail":
        raise ValueError("deliberate invalid request")
    for step in range(200 if mode == "term" else 3):
        if stopping:
            emit("cancelled", completed_steps=step)
            break
        checksum = sum(value * value for value in range(1000))
        emit("step", step=step, checksum=checksum)
        time.sleep(0.01)
    else:
        emit("completed")
except ValueError as error:
    print(str(error), file=sys.stderr, flush=True)
    emit("failed", reason=type(error).__name__)
    sys.exit(7)
finally:
    emit("cleanup")
PY
cat > "$COURSE01_DIR/supervisor.py" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(os.environ["COURSE01_DIR"])
summary = []
for mode in ("success", "fail", "term"):
    ready = root / f"{mode}.ready"
    out_path = root / f"{mode}.jsonl"
    err_path = root / f"{mode}.stderr"
    with out_path.open("w") as out, err_path.open("w") as err:
        child = subprocess.Popen(
            [sys.executable, "-u", str(root / "worker.py"), mode, str(ready)],
            stdout=out,
            stderr=err,
        )
        try:
            if mode == "term":
                deadline = time.monotonic() + 3
                while not ready.exists() and child.poll() is None:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("worker did not become ready")
                    time.sleep(0.005)
                if not ready.exists():
                    raise RuntimeError("worker exited before readiness")
                child.terminate()
            code = child.wait(timeout=3)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
    events = [json.loads(line)["event"] for line in out_path.read_text().splitlines()]
    expected_code = 7 if mode == "fail" else 0
    expected_event = {"success": "completed", "fail": "failed", "term": "cancelled"}[mode]
    assert code == expected_code, (mode, code)
    assert events[0] == "started" and events[-1] == "cleanup", events
    assert expected_event in events, events
    summary.append({"mode": mode, "returncode": code, "events": events})
print(json.dumps(summary, indent=2))
print(f"artifacts={root}")
PY
python3 "$COURSE01_DIR/supervisor.py"
```

**English:** The success case ends with `completed` and `cleanup`, and the failure case ends with `failed` and `cleanup` while returning seven. The termination case ends with `cancelled` and `cleanup` and deliberately returns zero because this toy worker treats requested cancellation as a handled outcome. It may emit a varying number of `step` events before seeing the signal. The invariant is the terminal state and cleanup, not the precise event count or PID. A real service must define whether cancellation belongs in its success or failure metrics.

**中文：** 成功路径以 `completed` 和 `cleanup` 结束；失败路径以 `failed` 和 `cleanup` 结束，并返回七。终止路径以 `cancelled` 和 `cleanup` 结束，而且特意返回零，因为这个教学进程把请求取消视为已处理结果。在收到信号前，它可能输出不同数量的 `step` 事件。应验证的是终止状态与清理过程，而不是具体事件数或进程编号。真实服务还需要明确取消应归入成功指标还是失败指标。

**English:** The readiness file is a small handshake that prevents the supervisor from sending `SIGTERM` before the worker installs its handler. Sleeping for an arbitrary interval would make the experiment depend on machine speed. The final `wait()` is equally important: even when a timeout forces termination, the supervisor still collects the child. Output files remain open until the child completes, then close before the supervisor parses them. These are concrete lifetime relationships that can be checked without measuring any GPU activity.

**中文：** 就绪文件构成一个小型握手，避免监管程序在工作进程安装信号处理函数之前发送 `SIGTERM`。如果只是随意睡眠一段时间，实验就会依赖机器速度。最后的 `wait()` 同样重要：即使超时后被迫终止，监管程序仍会回收子进程。输出文件在子进程结束前保持打开，随后先关闭，再由监管程序读取。这些都是可以直接检查的生命周期关系，不需要借助任何 GPU 活动来证明。

**English:** To extend the experiment, make the worker hold a request identifier and record when that request becomes terminal. Then ask what happens if the supervisor itself is interrupted between launch and wait. A production design needs a broader cleanup strategy, but the ownership question remains the same: which component must acknowledge cancellation, release admission capacity, and collect the child? Avoid adding automatic retries until you can prove whether the previous attempt is still running; otherwise the retry can duplicate work and amplify overload.

**中文：** 扩展实验时，可以让工作进程携带请求编号，并记录请求何时进入终止状态。随后再思考：如果监管程序在启动与等待之间被中断，会发生什么。生产设计需要更完整的清理机制，但所有权问题并没有改变：哪个组件必须确认取消、归还准入容量并回收子进程。在没有确认上一次尝试是否仍在运行之前，不要急于增加自动重试，否则重试可能复制工作，并在系统已经过载时进一步放大压力。

## 7. Failure Laboratory: The Reader That Never Finishes / 失败实验：始终无法结束的读取方

**English:** This experiment deliberately retains one pipe writer. The child reads until end-of-file, so a short timeout confirms that it is waiting. Closing the retained writer then allows the same child to finish normally. The timeout is an expected observation, not a failed test, and the `finally` block ensures the laboratory cannot leave its child running. The second part shows a shared file offset through `dup()`, linking byte-stream behavior to descriptor ownership.

**中文：** 这个实验故意保留一个管道写入端。子进程一直读取到文件结束，所以短暂超时能够确认它仍在等待。关闭被保留的写入端后，同一个子进程便可以正常完成。这里的超时是预期观察，并不是测试失败；`finally` 清理则保证实验不会留下继续运行的子进程。后半部分使用 `dup()` 展示共享文件偏移，把字节流行为与描述符所有权联系起来，帮助读者解释问题，而不只是记住关闭命令。

```bash
# experiment: pipe-lab
python3 - <<'PY'
import os
import subprocess
import sys
import tempfile

reader, writer = os.pipe()
program = '''
import os, sys
fd = int(sys.argv[1])
parts = []
while True:
    part = os.read(fd, 1024)
    if not part:
        break
    parts.append(part)
os.close(fd)
print(b"".join(parts).decode())
'''
child = subprocess.Popen(
    [sys.executable, "-c", program, str(reader)],
    pass_fds=(reader,), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
os.close(reader)
try:
    os.write(writer, b"request-complete")
    try:
        child.communicate(timeout=0.2)
        raise AssertionError("EOF arrived while a writer was still open")
    except subprocess.TimeoutExpired:
        print("expected: reader waits because a writer remains open")
    os.close(writer)
    writer = None
    out, err = child.communicate(timeout=3)
    assert child.returncode == 0 and out.strip() == "request-complete", (out, err)
    print("recovered: closing the writer allowed EOF")
finally:
    if writer is not None:
        os.close(writer)
    if child.poll() is None:
        child.kill()
    child.wait()

with tempfile.TemporaryFile() as stream:
    stream.write(b"abcdef")
    stream.flush()
    stream.seek(0)
    duplicate = os.dup(stream.fileno())
    try:
        first = os.read(stream.fileno(), 2)
        second = os.read(duplicate, 2)
        assert (first, second) == (b"ab", b"cd")
        print("shared-offset:", first.decode(), second.decode())
    finally:
        os.close(duplicate)
PY
```

**English:** The child's behavior is correct: it cannot infer that the parent has finished producing useful data while the parent still holds an open writer. Sending a delimiter is a different protocol from closing a stream. If your application uses a delimiter, it must define escaping, maximum message size, and malformed-message behavior. If it uses end-of-file, every inherited writer is part of the protocol. This is why a process tree and a descriptor inventory can be more revealing than another stack trace from the waiting reader.

**中文：** 子进程的行为是正确的：父进程仍持有打开的写入端时，子进程无法推断有用数据已经全部发送。发送结束标记与关闭数据流，是两种不同的协议。若使用结束标记，就必须规定转义方式、最大消息长度以及格式错误时的处理；若使用文件结束，就必须把每一个继承的写入端都纳入协议。这也解释了为什么进程树和描述符清单，有时比再抓一份读取方的等待栈更能揭示原因。

## 8. Shell Failure as Structured Evidence / 把 Shell 失败变成结构化证据

**English:** Run this block as written. It starts a fresh Bash process for each pipeline so that the test does not alter your interactive shell's options. The producer emits valid-looking output and then exits with status seven. `cat` successfully copies the output in both runs. The first pipeline reports success under the default policy, while the second preserves the upstream failure through `pipefail`. The assertions make the distinction executable rather than rhetorical. The presence of an output file is not evidence that the producing task succeeded.

**中文：** 请按原样执行下面的代码块。每条流水线都使用新的 Bash 进程，因此不会改变交互终端的选项。生产者输出看起来正常的数据，然后以状态七退出；两次运行中的 `cat` 都成功复制了数据。第一条流水线在默认策略下报告成功，第二条则通过 `pipefail` 保留上游失败。这里用断言把区别变成可执行检查，而不是停留在口头提醒，也避免误把输出文件存在当作任务成功的证据。

```bash
# experiment: shell-lab
python3 - <<'PY'
import subprocess

pipeline = "python3 -c 'print(42); raise SystemExit(7)' | cat"
default = subprocess.run(["bash", "-c", pipeline], capture_output=True, text=True)
strict = subprocess.run(["bash", "-o", "pipefail", "-c", pipeline], capture_output=True, text=True)
assert default.returncode == 0 and default.stdout.strip() == "42"
assert strict.returncode == 7 and strict.stdout.strip() == "42"
print("default_status=0 pipefail_status=7 same_output=42")
PY
```

**English:** Saving `$?` must happen before another command overwrites it. Likewise, Bash's `PIPESTATUS` describes the most recent foreground pipeline and must be captured immediately. Do not add a diagnostic `echo` and then inspect the status you meant to preserve. `set -e` is useful in some scripts, but its exceptions and interaction with conditionals mean that it cannot replace an explicit failure contract. For important launches, use a clearly written conditional and save the failing command's status in a dedicated variable.

**中文：** 保存 `$?` 必须发生在另一个命令覆盖它之前。同样，Bash 的 `PIPESTATUS` 描述最近的前台流水线，也需要立即保存。不要先插入一个用于诊断的 `echo`，再读取本来想保留的状态。`set -e` 在一些脚本中有用，但它存在例外，而且会受到条件结构影响，不能替代明确的失败契约。对于重要启动步骤，使用清楚的条件分支，并把失败状态存入专用变量，会更容易审查。

**English:** Arguments and shell text are different data types in practice. Passing a list of arguments to `subprocess.run` preserves argument boundaries without invoking a shell. Passing one string to a shell asks it to interpret quotes, redirections, variables, and substitutions. A model name containing spaces should remain one argument; a dataset path should not become executable syntax. This is also a reproducibility issue: a correctly quoted invocation makes it possible for another person to repeat the exact workload you intended.

**中文：** 参数列表和 Shell 文本在实践中应当视为两种不同的数据类型。把参数列表传给 `subprocess.run`，可以在不调用 Shell 的情况下保留参数边界；把一整段字符串交给 Shell，则是在要求它解释引号、重定向、变量和替换。含空格的模型名称应当保持为一个参数，数据集路径也不应变成可执行语法。这同样影响可复现性：准确保留参数，别人才有可能重复你原本打算运行的负载。

## 9. Paths, Permissions, and Service Identity / 路径、权限与服务身份

**English:** Access to a file depends on more than the file's final permission bits. Resolving a pathname requires traversing its parent directories, where the search permission matters. A service running under another identity can therefore fail to read a model even when the final file appears readable. Relative paths also depend on the current working directory, which may differ between a terminal, a service unit, and a container. [Linux pathname resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html) Record execution identity, working directory, and parent-directory permissions instead of inspecting only the final pathname component.

**中文：** 能否访问文件，不只取决于最终文件的权限位。解析路径时还要经过父目录，而这些目录需要允许路径搜索。因此，以另一身份运行的服务，即使看到最终模型文件可读，也可能无法真正访问它。相对路径还依赖当前工作目录，而终端、服务单元和容器的工作目录可能不同。排查路径问题时，应同时记录运行身份、工作目录和父目录权限，不能只检查文件最后一段名称。[Linux 路径解析](https://man7.org/linux/man-pages/man7/path_resolution.7.html)

**English:** Prefer a diagnosis that names the missing permission over a broad permission change. For example, a cache writer may need write and search access to one directory but no ability to modify model weights. Giving everything world-write access conceals the resource boundary and can produce later integrity problems. Within a private laboratory, `umask 077` makes newly created files private by default; in a team service, ownership and group policy should express the intended sharing instead of being copied blindly from a personal workstation.

**中文：** 优先给出明确指出缺少哪一种权限的诊断，而不是扩大所有权限。例如，缓存写入方可能只需要对一个目录具有写入和搜索权限，并不需要修改模型权重。把所有内容改成任何人可写，会掩盖资源边界，也可能带来后续完整性问题。在私人实验目录里，`umask 077` 可以让新文件默认保持私有；团队服务则应通过所有者和组策略表达预期共享关系，不能照搬个人工作站的设置。

**English:** Configuration is another form of inherited state. The executable selected through `PATH`, the current directory, environment variables, resource limits, and identity can all differ between two apparently identical commands. Save only the relevant variables rather than dumping an entire environment that may contain credentials. A useful report states the resolved executable path, its version, the intended working directory, and the selected configuration file. This is usually more actionable than a screenshot showing that the command worked once in an interactive terminal.

**中文：** 配置也是一种继承状态。通过 `PATH` 选择的可执行文件、当前目录、环境变量、资源限制和运行身份，都可能让两条看似相同的命令表现不同。保存相关变量即可，不必导出可能包含凭据的整个环境。有用的报告应写清实际解析到的程序路径、程序版本、预期工作目录和所选配置文件。相比只提供一张交互终端里曾经运行成功的截图，这些信息更能让接手的人定位差异并重复结果。

## 10. Dynamic Libraries: Linking Is Not Loading / 动态库：链接不等于加载

**English:** Compilation transforms source into object code; linking resolves a program's relationships with other objects and libraries; loading prepares the program and its shared dependencies to execute. A program can compile and link successfully, then fail at startup because a required shared library cannot be found. It can also load a different library version than expected. This is directly relevant to CUDA, where the compiler, runtime libraries, driver-facing libraries, and kernel module are separate pieces with different selection mechanisms. Collapsing these components into one version number obscures the investigation.

**中文：** 编译把源代码转换为目标代码，链接确定程序与其他目标文件或库的关系，加载则准备程序及其共享依赖进入执行。程序可能编译和链接都成功，却因为找不到必需的共享库而在启动时失败；也可能加载了与预期不同的版本。这与 CUDA 直接相关，因为编译器、运行时库、面向驱动的用户态库和内核模块，是由不同机制选择的独立组件。把它们都简称为一个版本，会让排查失去方向。

**English:** The dynamic loader applies a documented search order involving object metadata, environment settings, the loader cache, and default directories, with additional rules for secure execution. For this course, the essential distinction is that a linker search option such as `-L` does not automatically become a runtime search path. `RUNPATH` and `LD_LIBRARY_PATH` serve different purposes and have different scope. Inspect metadata before adding another global path. [Dynamic loader search rules](https://man7.org/linux/man-pages/man8/ld.so.8.html) Repeatedly extending a global environment variable can spread a local selection problem to unrelated programs.

**中文：** 动态加载器按照文档规定的次序考虑目标文件元数据、环境设置、加载器缓存和默认目录，安全执行模式还有额外规则。本课最重要的区别是：类似 `-L` 的链接搜索选项，不会自动变成运行时搜索路径。`RUNPATH` 与 `LD_LIBRARY_PATH` 的用途和作用范围也不同。遇到加载失败时，先检查元数据，再考虑是否增加路径，避免不断追加全局环境变量，把局部问题扩散到其他程序。[动态加载器搜索规则](https://man7.org/linux/man-pages/man8/ld.so.8.html)

**English:** The following complete experiment needs a working C compiler and `readelf`, but no CUDA toolchain. It builds a tiny private library, links one executable without a runtime path, observes its expected startup failure, then builds a relocatable executable using `$ORIGIN`. All files stay in a new temporary directory. Only binaries created by this experiment are executed. The name of the temporary directory is deliberately not embedded into the working executable, so moving the directory would preserve its relative library relationship.

**中文：** 下面的完整实验需要可用的 C 编译器和 `readelf`，不需要 CUDA 工具链。它先构建一个私有小型库，再链接一个没有运行时路径的程序，观察预期的启动失败，最后使用 `$ORIGIN` 构建能够相对定位库的程序。所有文件都位于新的临时目录，只执行本实验创建的二进制。正常程序不会嵌入临时目录的绝对名称，因此移动整个目录时，仍能保留程序与库之间的相对关系。

```bash
# experiment: loader-lab
bash <<'SH'
set -eu
COURSE01_LIBDIR=$(mktemp -d /tmp/course01-loader-XXXXXX)
mkdir "$COURSE01_LIBDIR/lib"
cat > "$COURSE01_LIBDIR/value.c" <<'C'
int course_value(void) { return 42; }
C
cat > "$COURSE01_LIBDIR/main.c" <<'C'
#include <stdio.h>
extern int course_value(void);
int main(void) { printf("%d\n", course_value()); return 0; }
C
gcc -fPIC -shared "$COURSE01_LIBDIR/value.c" -o "$COURSE01_LIBDIR/lib/libcourse01.so"
gcc "$COURSE01_LIBDIR/main.c" -L"$COURSE01_LIBDIR/lib" -lcourse01 -o "$COURSE01_LIBDIR/missing_path"
if env -u LD_LIBRARY_PATH "$COURSE01_LIBDIR/missing_path" >"$COURSE01_LIBDIR/failure.stdout" 2>"$COURSE01_LIBDIR/failure.stderr"; then
    echo "unexpected: private library was found" >&2
    exit 1
else
    COURSE01_FAILED_STATUS=$?
    printf 'expected_startup_failure_status=%s\n' "$COURSE01_FAILED_STATUS"
fi
gcc "$COURSE01_LIBDIR/main.c" -L"$COURSE01_LIBDIR/lib" -lcourse01 \
    -Wl,--enable-new-dtags '-Wl,-rpath,$ORIGIN/lib' -o "$COURSE01_LIBDIR/relative_path"
readelf -d "$COURSE01_LIBDIR/relative_path"
COURSE01_VALUE=$(env -u LD_LIBRARY_PATH "$COURSE01_LIBDIR/relative_path")
test "$COURSE01_VALUE" = 42
printf 'loaded_value=%s\nartifacts=%s\n' "$COURSE01_VALUE" "$COURSE01_LIBDIR"
SH
```

**English:** The first executable's failure is not a compiler failure: it already exists, and the missing dependency is detected while preparing to run it. The second executable contains a runtime search path based on its own location. The single quotes around the linker option keep the shell from expanding `$ORIGIN`; the loader interprets it later. This example is a controlled local design, not a recommendation to rewrite the search paths of system NVIDIA libraries. Those must retain the installation method and package ownership appropriate to the machine.

**中文：** 第一个程序的失败不是编译失败：可执行文件已经存在，只是在准备运行时发现缺失依赖。第二个程序包含基于自身位置的运行时搜索路径。链接选项周围的单引号阻止 Shell 提前展开 `$ORIGIN`，让加载器稍后解释它。这个例子只是受控的局部设计，并不是建议修改系统 NVIDIA 库的搜索路径。系统组件应保持与机器相适应的安装方式和软件包归属，不能因为局部示例成功就随意替换。

## 11. Distinguish the GPU Stack's Layers / 区分 GPU 软件栈层次

**English:** Hardware visibility is the first layer: the operating system can enumerate a PCI device. A loaded kernel module is another layer. User-space driver libraries provide interfaces used by applications, while NVML supports management and monitoring. CUDA Toolkit supplies development components such as `nvcc`; a framework may additionally bring its own user-space dependencies. Evidence at one layer should not be promoted into a claim about the next. Seeing a GPU in PCI inventory does not establish that a CUDA context can be created. Finding a compiler also does not prove device code has executed.

**中文：** 硬件可见性是第一层，表示操作系统能够枚举 PCI 设备；已加载的内核模块是另一层。用户态驱动库提供应用调用的接口，NVML 支持管理与监控；CUDA Toolkit 则提供 `nvcc` 等开发组件，框架还可能携带自己的用户态依赖。某一层的证据不能自动升级为下一层的结论。在 PCI 清单里看到 GPU，并不能证明可以创建 CUDA 上下文；找到编译器，也不能证明设备代码已经执行。

**English:** The CUDA version displayed by `nvidia-smi` expresses the driver's CUDA compatibility information; it is not a direct inventory of the toolkit selected by your shell. `nvcc --version` identifies that compiler's toolkit release, while a framework's reported build version describes the framework package. Save all three under explicit labels when available. A disagreement is a reason to inspect compatibility and selection, not a rule that every displayed number must be identical. [NVIDIA System Management Interface](https://docs.nvidia.com/deploy/nvidia-smi/index.html)

**中文：** `nvidia-smi` 显示的 CUDA 版本表达的是驱动的 CUDA 兼容信息，并不是对 Shell 当前所选工具包的直接清点。`nvcc --version` 描述该编译器所属的工具包版本，框架报告的构建版本则描述框架软件包。能够取得时，应分别标注并保存这三类信息。数字不同意味着要检查兼容关系和选择路径，并不意味着所有显示值都必须完全相同。[NVIDIA 系统管理接口](https://docs.nvidia.com/deploy/nvidia-smi/index.html)

**English:** In this lesson's supplied environment, the observed NVML and loaded-module versions differ and a mismatch is reported. The supported conclusion is that the management path is not healthy under the recorded configuration. The version pair alone does not identify which installer, package update, stale process, or library search path produced the condition. Capture the loaded module version and the resolved library before proposing a repair. This course preserves the failure as evidence and does not claim that a particular administrative action has fixed it. [NVML error definitions](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceEnums.html)

**中文：** 在本课提供的环境中，观察到 NVML 与已加载模块版本不同，而且报告了不匹配。可以支持的结论是：在记录的配置下，管理接口路径没有正常工作。仅凭这组版本，无法判定具体是哪个安装器、软件包更新、旧进程或库搜索路径造成了问题。提出修复方案前，应先记录已加载模块版本和实际解析到的库。本课保留这一失败证据，不会声称某个管理操作已经将其修好。[NVML 错误定义](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceEnums.html)

**English:** The following inventory is read-only and bounded. Some commands may be missing, restricted, or unsuccessful; each result includes its exit status rather than hiding a failure. `modinfo` describes a module file found on disk, which can differ from the module already loaded in the kernel. The `/proc` entry is therefore included as a separate observation. Restrict environment reporting to selected variables, and review any collected paths before sharing the report outside your team.

**中文：** 下面的环境清点只读执行，并为每条命令设置时间限制。有些命令可能不存在、受权限限制或者运行失败，因此每个结果都保存退出状态，而不是隐藏失败。`modinfo` 描述磁盘上找到的模块文件，它可能与内核已经加载的模块不同，所以还要单独读取 `/proc` 中的信息。环境变量只收集指定项目；如果要把报告分享给团队之外的人，应先检查其中包含的路径，保留诊断所需的信息即可。

```bash
# experiment: inventory
python3 - <<'PY'
import json
import os
from pathlib import Path
import shutil
import subprocess

commands = [
    ["uname", "-a"], ["id"], ["lscpu"], ["free", "-h"],
    ["df", "-h", "."], ["lsblk"], ["lspci", "-nn"],
    ["nvcc", "--version"], ["nvidia-smi"], ["modinfo", "-F", "version", "nvidia"],
    ["ldconfig", "-p"],
]
report = {"commands": [], "files": {}, "selected_environment": {}}
for name in ("CUDA_VISIBLE_DEVICES", "CUDA_HOME", "LD_LIBRARY_PATH"):
    report["selected_environment"][name] = os.environ.get(name)
for filename in ("/etc/os-release", "/proc/driver/nvidia/version", "/proc/self/cgroup"):
    try:
        report["files"][filename] = Path(filename).read_text()
    except OSError as error:
        report["files"][filename] = {"error": str(error)}
for args in commands:
    resolved = shutil.which(args[0])
    entry = {"argv": args, "executable": resolved}
    if resolved is None:
        entry["status"] = "unavailable"
    else:
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=5)
            entry.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired:
            entry["status"] = "timeout"
    report["commands"].append(entry)
print(json.dumps(report, ensure_ascii=False, indent=2))
PY
```

## 12. Containers, Limits, and Device Access / 容器、资源限制与设备访问

**English:** A container changes namespaces, filesystem views, resource accounting, and the environment seen by the process. It does not replace the host kernel with the image's userspace. GPU access therefore depends on host-side components and the container runtime's device and library setup. Installing a compiler inside an image is not enough to make a broken host driver healthy. The NVIDIA Container Toolkit documents the integration layer; use its instructions for the chosen runtime instead of treating every Docker image as self-contained GPU firmware. [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

**中文：** 容器改变进程看到的命名空间、文件系统视图、资源计量和运行环境，却不会用镜像中的用户空间替换宿主内核。因此，GPU 访问依赖宿主组件，也依赖容器运行时对设备与库的配置。在镜像里安装编译器，并不能让损坏的宿主驱动恢复正常。NVIDIA Container Toolkit 文档说明了这一集成层，应按所用运行时选择对应说明，而不能把每个容器镜像当作自带完整 GPU 底层系统。[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

**English:** CPU and memory limits can explain why a server appears slow despite idle host resources. In cgroup v2, CPU bandwidth control and memory limits belong to the cgroup, so host-wide free capacity is not necessarily available to the process. A throttled tokenizer can starve the GPU without a CUDA bug. Record the process's cgroup membership and inspect its applicable limits before drawing conclusions from a host-wide utilization chart. [Linux cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)

**中文：** CPU 和内存限制能够解释为什么宿主看起来空闲，服务却依然缓慢。在 cgroup v2 中，CPU 带宽控制和内存限制属于相应控制组，因此宿主整体有空余资源，不等于某个进程可以使用这些资源。受到节流的分词器可能让 GPU 缺少任务，这并不需要存在 CUDA 错误。根据整机利用率图下结论之前，应先记录进程所属控制组，并检查真正作用于它的限制。[Linux cgroup v2 文档](https://docs.kernel.org/admin-guide/cgroup-v2.html)

**English:** Device selection is also part of the experiment configuration. A process can see a filtered set of devices, and ordinal numbering inside that view may not match another process's view. State which selection mechanism was used and record stable hardware identity when the management path is working. In the current mismatch state, leave unavailable fields explicitly unavailable rather than inventing a device UUID or memory capacity. Good environment reports preserve uncertainty in a way that another engineer can resolve later.

**中文：** 设备选择同样属于实验配置。某个进程看到的设备集合可能经过筛选，其中的序号也可能与另一个进程的视图不一致。应说明采用了哪种选择机制，并在管理接口正常时记录稳定的硬件身份。在当前版本不匹配的状态下，无法取得的字段就明确写为不可用，不要补造设备唯一编号或显存容量。好的环境报告会把不确定性保留下来，让下一位工程师有机会继续验证，而不是被貌似完整的数据误导。

## 13. Observe the System Before Tuning It / 先观察系统，再调整参数

**English:** Observation begins with a question and a timescale. `ps` describes process state, `top` or `htop` helps inspect changing CPU activity, `free` summarizes memory, and disk tools describe storage capacity or activity. None of these alone establishes the cause of request latency. If a service pauses every few seconds, a single snapshot can miss the event. Align timestamps, capture a bounded interval that contains the symptom, and compare the same workload before and after one controlled change. That comparison is what allows the observation to support a causal explanation.

**中文：** 观察应从问题和时间尺度开始。`ps` 描述进程状态，`top` 或 `htop` 便于查看变化中的 CPU 活动，`free` 汇总内存，而磁盘工具描述存储容量或活动。任何一个工具都不能单独证明请求延迟的原因。如果服务每隔几秒停顿一次，单次快照可能恰好错过现象。应对齐时间戳，采集覆盖症状的有限区间，并在一次受控修改前后比较相同负载，让观察能够支持因果判断。

**English:** CPU percentage needs a denominator. A tool may report usage relative to one logical CPU, all available CPUs, or a constrained allocation. Load average also includes tasks in particular waiting states and should not be read as GPU utilization. Similarly, a high resident-memory number is not automatically a leak, and low free memory can coexist with reclaimable file cache. Start by defining the metric, then relate it to queue growth, request completion, and throughput instead of treating a large number as a diagnosis.

**中文：** CPU 百分比需要明确分母。工具可能按一个逻辑 CPU、全部可用 CPU，或者受限制的配额报告利用率。平均负载也包含特定等待状态下的任务，不能把它读成 GPU 利用率。同样，常驻内存大不自动等于泄漏，可用空闲内存少也可能伴随可回收文件缓存。先定义指标，再把它与排队增长、请求完成和吞吐量联系起来，比把某个大数字直接当成诊断更有效。

**English:** NUMA topology becomes relevant when CPU threads, host memory, and a device are attached to different parts of a machine. A placement change can improve locality, but it can also reduce available scheduling capacity or shift contention. Learn to read `lscpu` and, where installed, `numactl --hardware` before applying affinity rules. On a small workstation, the experiment may reveal little meaningful NUMA structure; that is still a valid observation. Do not copy server-specific binding commands merely because they appeared in an optimization article.

**中文：** 当 CPU 线程、主机内存和设备连接在机器的不同位置时，NUMA 拓扑就可能影响性能。改变位置能够改善局部性，也可能减少可调度容量或者转移竞争。使用亲和性规则之前，应先学会阅读 `lscpu`，以及安装了相应工具时的 `numactl --hardware`。小型工作站可能没有值得优化的复杂 NUMA 结构，这也是有效观察。不能因为某篇优化文章出现了绑定命令，就把服务器特定设置复制到自己的机器上。

**English:** Nsight Systems is useful for a timeline view of application activity and the relationships between CPU work and GPU execution. Nsight Compute investigates kernel-level behavior and hardware metrics. These tools answer different questions and add collection overhead. First identify an interesting interval or kernel, then narrow the investigation. A detailed kernel profile cannot explain a long delay before that kernel was ever submitted. [Nsight Systems guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html), [Nsight Compute profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)

**中文：** Nsight Systems 适合从时间线观察应用活动，以及 CPU 工作与 GPU 执行之间的关系；Nsight Compute 则用于调查 kernel 内部行为和硬件指标。二者回答的问题不同，而且采集本身会产生开销。应先确定值得研究的时间区间或 kernel，再缩小调查范围。一份细致的 kernel 报告，无法解释该 kernel 尚未提交之前发生的漫长等待。[Nsight Systems 指南](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)、[Nsight Compute 性能分析指南](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)

**English:** Profiling access may depend on kernel settings, permissions, and the environment in which a process runs. If collection is denied, record that result and the requested collection type. It is not evidence that the application is fast or that there is no GPU work. Likewise, this lesson's blocked management path means the course cannot supply a verified GPU trace. You can still practice process observation, descriptor analysis, failure classification, and experiment design while preserving an explicit boundary around unperformed GPU measurements.

**中文：** 性能采集能否执行，可能取决于内核设置、权限以及进程运行环境。如果采集被拒绝，应记录结果和请求的采集类型。这既不能证明应用很快，也不能证明没有 GPU 工作。同样，本课管理接口受阻，因此不能提供已经验证的 GPU 时间线。但仍然可以练习进程观察、描述符分析、故障分类和实验设计，并清楚标注哪些 GPU 测量尚未执行，使已经完成的学习与未完成的验证保持一致。

## 14. Diagnose with Competing Explanations / 用竞争性解释组织诊断

**English:** Consider a model server that never becomes ready. One explanation is slow weight loading, another is a dependency failure, and a third is a child that exited while the launcher kept running. Each predicts different evidence: continuing storage activity, a loader error, or a terminated worker. Before changing a timeout, inspect the process tree and terminal error. Extending a readiness deadline may be appropriate for genuine progress, but it only makes a deterministic dependency failure take longer to report.

**中文：** 假设模型服务器始终没有就绪。一种解释是权重加载慢，另一种是依赖失败，还有一种是工作进程已经退出，但启动器仍活着。每种解释都预期出现不同证据：持续的存储活动、加载器错误，或者已经终止的工作进程。调整超时之前，应先检查进程树与终止错误。对于确实在推进的加载，延长就绪期限可能合理；对于确定性的依赖失败，它只会让报告错误变得更慢，并不会提高成功机会。

**English:** Now consider latency rising while throughput remains flat. The application may be admitting more work than it can finish, so queueing increases even if individual operations have not become slower. Alternatively, descriptor or memory pressure may progressively reduce capacity. Design one experiment that holds concurrency constant and another that holds arrival rate constant; those are different workloads. Record successful, failed, and cancelled requests separately. A single average over all outcomes can conceal the overload behavior that matters to users.

**中文：** 再考虑延迟持续上升而吞吐保持不变的情况。应用可能接收了超过完成能力的任务，因此即使单次操作没有变慢，排队也在增加；另一种可能是描述符或内存压力逐步削弱了容量。可以分别设计固定并发和固定到达速率的实验，但应认识到它们是不同负载。成功、失败与取消的请求也要分开记录。把所有结果混成一个平均值，可能隐藏用户真正遇到的过载行为，导致错误的优化选择。

**English:** A compact incident note should contain the observation, the competing explanations, the evidence collected, the smallest discriminating experiment, and the remaining uncertainty. For the current driver mismatch, the observation is a failed management initialization under two recorded component versions. A reasonable next investigation identifies the actual library and loaded module; it is not an unexplained package replacement. The same discipline applies to a leaked pipe writer or a missing shared library: preserve the first useful failure, then reduce uncertainty one boundary at a time.

**中文：** 一份简洁的故障记录应包含观察结果、竞争性解释、已收集证据、最小区分实验以及剩余不确定性。对于当前驱动不匹配，观察结果是在两组已记录组件版本下，管理初始化失败。合理的下一项调查是识别实际库与已加载模块，而不是在没有解释的情况下替换软件包。同样的方法也适用于泄漏的管道写入端或缺失的共享库：保留第一条有价值的失败信息，再逐一跨越边界减少不确定性。

## 15. Ten Exercises and Worked Answers / 十道练习与参考答案

### Exercise 1: What Does a PID Prove? / 练习一：进程编号能证明什么

**English:** A launcher prints a worker PID and your health check immediately reports the service as ready. The first request fails because the model is still loading. Identify the incorrect inference and propose a readiness condition that does not depend on an arbitrary sleep. Explain what evidence you would keep if the worker exits before becoming ready. The evidence should distinguish slow loading from a failed startup.

**中文：** 启动器打印了工作进程编号，健康检查便立刻报告服务就绪，但第一条请求因为模型仍在加载而失败。请指出这里不成立的推断，并提出一个不依赖任意睡眠时长的就绪条件。如果工作进程在就绪之前退出，你又会保存哪些证据，以便区分加载缓慢和启动失败这两种情况。

**English:** A PID proves that a process identity was created, not that model loading or dependency initialization completed. Use an explicit readiness acknowledgement after the required initialization and, if appropriate, a bounded functional probe. While waiting, observe child exit and a deadline. Preserve the return code, standard error, initialization stage, and configuration identity; do not continue waiting after a terminal failure.

**中文：** 进程编号只能证明执行身份已经创建，不能证明模型加载或依赖初始化完成。应在必要初始化结束后发送明确的就绪确认，合适时再增加有时间限制的功能探测。等待期间还要观察子进程退出与截止时间。保存返回码、标准错误、初始化阶段和配置身份，才能定位失败；一旦确认终止失败，就不应继续把它当作尚在加载而无限等待。

### Exercise 2: The Hidden Writer / 练习二：隐藏的写入端

**English:** A producer exits, but its consumer remains blocked reading a pipe. The parent's copy of the write descriptor is still open. Will sending `SIGTERM` to the already exited producer solve the problem? Give the descriptor-level explanation and identify the observation that would distinguish this case from a consumer performing slow computation.

**中文：** 生产者已经退出，但消费者仍阻塞在管道读取上，而父进程保留的写入描述符还开着。给已经退出的生产者发送 `SIGTERM` 能解决问题吗？请从描述符层面解释原因，并说明需要什么观察，才能把这种情况与消费者正在执行缓慢计算区分开来。

**English:** No. End-of-file requires every write-end reference to close after buffered data is consumed. The parent is still a writer owner even if it never writes again. Inspect descriptor ownership and the consumer's waiting operation, then close the parent's unused writer through the owning code path. If the consumer finishes when that writer closes, the experiment supports the lifetime explanation rather than a compute bottleneck.

**中文：** 不能。缓冲数据读完之后，仍需所有写入端引用关闭，消费者才会收到文件结束。父进程即使再也不写，也是写入端拥有者。应检查描述符归属和消费者正在等待的操作，再由负责该资源的代码关闭不再使用的写入端。若关闭后消费者立即完成，就支持生命周期问题这一解释，而不是把原因归结为计算能力不足。

### Exercise 3: Successful Logging, Failed Work / 练习三：日志成功而任务失败

**English:** A benchmark command is piped into `tee`, and the automation records status zero. The log contains a dependency error. Explain why both observations can be true. What should a Bash wrapper preserve, and why is adding `echo done` before reading `$?` a mistake?

**中文：** 基准命令通过管道交给 `tee`，自动化记录的状态为零，但日志里包含依赖错误。为什么这两个观察可以同时成立？Bash 包装脚本应该保留什么信息？为什么先执行 `echo done`，再读取 `$?`，会让本来想保存的结果丢失？

**English:** The logger can succeed while the producer fails, and Bash normally reports the last pipeline command's status. Enable an intentional pipeline policy such as `pipefail` and preserve relevant per-command statuses immediately when needed. Save status before running another command, because `$?` is replaced by that command's result. Keep both the error output and the machine-readable status; neither substitutes for the other. Error text helps explain the cause, while machine-readable status drives automation.

**中文：** 日志程序可以成功，而生产者失败；Bash 默认又采用流水线最后一个命令的状态。应明确采用类似 `pipefail` 的策略，必要时立即保存各命令状态。在运行其他命令之前先保存结果，因为 `$?` 会被下一条命令的返回值覆盖。错误输出与机器可读状态都应保留：前者帮助解释原因，后者驱动自动化判断，二者不能互相替代。

### Exercise 4: A Zombie Is Not a Busy Worker / 练习四：僵尸不是繁忙工作进程

**English:** Monitoring lists a child in zombie state while its parent continues serving requests. Someone proposes increasing GPU capacity because the process has remained visible for several minutes. What has already happened, what remains unfinished, and which component should be investigated?

**中文：** 监控显示一个子进程处于僵尸状态，而父进程继续处理请求。有人因为这个进程已经显示了几分钟，就建议增加 GPU 容量。实际上哪件事情已经发生，哪件事情还没有完成，又应该检查哪个组件，而不是把进程仍可见理解为它还在执行计算？

**English:** The child has terminated; the parent has not yet collected its exit status. Its visibility does not indicate active computation. Investigate the parent's wait and child-management logic, including exception paths that bypass collection. More GPU capacity does not repair missing reaping. Separately inspect why the child originally exited, because the exit cause and the parent's failure to reap are distinct defects.

**中文：** 子进程已经终止，但父进程尚未收集退出状态，因此它仍可见并不表示仍在计算。应检查父进程的等待和子进程管理逻辑，尤其是是否存在绕过回收步骤的异常路径。增加 GPU 容量无法修复缺少回收操作的问题。同时还要单独调查子进程最初为何退出，因为退出原因与父进程未回收，是两个可以同时存在但彼此不同的缺陷。

### Exercise 5: Compiled but Unloadable / 练习五：能编译却不能加载

**English:** A binary links using `-L/private/lib`, but on execution the loader cannot find its shared library. Why does adding another source include directory not solve the issue? Describe two scoped ways to provide the runtime search relationship and a reason not to change the whole machine's library path for this one experiment.

**中文：** 一个二进制使用 `-L/private/lib` 完成链接，但执行时加载器找不到共享库。为什么再增加源文件头文件搜索目录不能解决问题？请说明两种限定作用范围的运行时定位方式，并解释为什么不应为了这一个实验修改整台机器所有进程的库搜索路径。

**English:** Header search, link search, and runtime loading are different phases. A controlled per-invocation library path can help diagnose the issue, while an intentional `RUNPATH`, such as a suitable `$ORIGIN` relationship, can encode a private deployment layout. A global change may redirect unrelated programs to incompatible libraries and make the result depend on hidden workstation state. Verify the selected dependency rather than stopping at successful compilation.

**中文：** 头文件搜索、链接搜索与运行时加载属于不同阶段。限定在单次调用中的库路径可以帮助诊断，有意设置的 `RUNPATH`，例如合适的 `$ORIGIN` 相对关系，则可以表达私有部署布局。全局修改可能把无关程序导向不兼容的库，让结果依赖隐藏的工作站状态。最终应验证实际选择的依赖，而不是在看到编译成功后就认定运行环境也已正确。

### Exercise 6: Three CUDA Version Numbers / 练习六：三种 CUDA 版本信息

**English:** `nvcc`, a framework package, and `nvidia-smi` display different CUDA-related versions. Does this alone prove an invalid installation? State what each observation describes, and identify the additional failure evidence in this lesson's actual environment that prevents a GPU validation claim.

**中文：** `nvcc`、框架软件包和 `nvidia-smi` 显示不同的 CUDA 相关版本。这一点本身能证明安装错误吗？请分别说明三种观察描述的对象，并指出本课实际环境还出现了哪一项额外失败证据，因此不能把 GPU 验证写成已经完成。

**English:** Different numbers alone are insufficient: they concern the selected compiler toolkit, framework build, and driver compatibility information. Compatibility must be checked for the relevant combination. Here, a driver/library mismatch is explicitly reported and NVML 610.57 differs from the loaded module 610.43.02. That observed failure must remain in the report; compilation success cannot erase it or demonstrate that a CUDA workload executed.

**中文：** 数字不同本身还不够，因为它们分别涉及所选编译器工具包、框架构建以及驱动兼容信息，需要针对具体组合检查兼容性。本课另外明确报告了驱动与库不匹配，而且 NVML 610.57 与已加载模块 610.43.02 不同。这条失败必须保留在报告里，编译成功不能抹去它，也不能用来证明 CUDA 工作负载已经执行。

### Exercise 7: A Container Cannot Replace the Host Kernel / 练习七：容器不能替换宿主内核

**English:** A team builds an image containing a newer CUDA compiler and expects it to fix a host driver initialization failure. Which system boundary is being misunderstood? Describe what the image controls and which parts still need to work outside the image. Distinguish user-space dependencies from host device access.

**中文：** 团队构建了一个包含更新 CUDA 编译器的镜像，希望它修复宿主驱动初始化失败。这里误解了哪一道系统边界？镜像能够控制哪些内容，而哪些部分仍需在镜像之外正常工作？请把用户空间依赖与宿主设备访问分开说明。

**English:** The image supplies user-space files and software, but the container shares the host kernel. Host driver components, device availability, and runtime integration must still be healthy. A new compiler may change how code is built without repairing the loaded module or the management library relationship. First establish the failing layer and compare host and container observations under clearly recorded device and library configurations.

**中文：** 镜像提供用户空间文件和软件，容器仍共享宿主内核，所以宿主驱动组件、设备可用性和运行时集成都需要正常。更新编译器可以改变构建方式，却不必然修复已加载模块或管理库之间的关系。应先确定失败层次，再在明确记录设备和库配置的前提下比较宿主与容器观察，避免用更换镜像代替对真实边界的调查。

### Exercise 8: Shutdown and Cancellation / 练习八：退出与取消

**English:** A client disconnects, the API handler returns, and the service immediately releases a request's device buffer. The GPU operation associated with that request may still be running. What lifetime condition is missing, and how is this related to waiting for a child after sending it a signal?

**中文：** 客户端断连后，接口处理函数返回，服务立即释放该请求的设备缓冲区，但相关 GPU 操作可能仍在执行。这里缺少什么生命周期条件？它与向子进程发送信号之后仍要等待子进程结束，有什么共同之处？

**English:** Loss of client interest is not proof that every resource user has completed. Release requires the relevant completion or cancellation contract to ensure the buffer is no longer in use. Similarly, sending a signal requests a state change but does not itself observe child completion. Model notification, acknowledgement, and final resource release as separate events, and preserve the owner responsible for joining them together. This prevents a returning call stack from dropping resources still used by asynchronous work.

**中文：** 客户端不再需要结果，不等于所有资源使用者已经结束。释放缓冲区需要满足相应完成或取消契约，保证它不再被使用。同样，发送信号只是请求状态改变，本身并未观察子进程完成。应把通知、确认和最终资源释放建模为不同事件，并保留一个负责把这些事件连接起来的拥有者，防止调用栈返回时就过早丢弃仍被异步工作使用的资源。

### Exercise 9: Idle Host, Slow Service / 练习九：宿主空闲而服务缓慢

**English:** Host-wide CPU use is low, but an inference service's queue grows and its GPU has long gaps. Give two explanations consistent with these observations and one measurement that helps distinguish them. Explain why buying a faster GPU is not yet a supported conclusion.

**中文：** 宿主整体 CPU 使用率较低，但推理服务队列持续增长，GPU 时间线上又存在长间隙。请提出两个与这些观察一致的解释，再给出一项帮助区分它们的测量。为什么此时购买更快 GPU 还不是有证据支持的结论？

**English:** The service could be CPU-throttled by its cgroup, or it could be blocked on input, synchronization, or a serial preparation step. Inspect the effective CPU limits and correlate per-process activity with the request timeline. A faster device cannot remove a gap caused by work that was never submitted. Establish whether the bottleneck is device execution or the path that supplies work before changing hardware.

**中文：** 服务可能受到控制组 CPU 节流，也可能阻塞在输入、同步或串行准备步骤。应检查实际 CPU 限制，并把进程活动与请求时间线关联起来。更快的设备无法消除从未提交工作的空档。更换硬件之前，需要先确定瓶颈来自设备执行，还是来自向设备供给任务的路径，否则采购可能增加成本，却无法改善造成排队的真正原因。

### Exercise 10: Write an Evidence-Based Handoff / 练习十：撰写有证据的交接记录

**English:** Write a short handoff for the current environment without repairing it. Include the established facts, one unresolved question, the successful CPU experiments, and the GPU work that remains unverified. Avoid attributing the mismatch to an unobserved administrative action. Environment diagnosis should not be presented as a performance test.

**中文：** 请在不修复当前环境的前提下，写一段简短交接记录，包含已经确认的事实、一个尚未解决的问题、成功完成的 CPU 实验，以及仍未验证的 GPU 工作。不要把版本不匹配直接归因于自己没有观察到的某次管理操作，也不要让读者误以为环境诊断等于性能测试。

**English:** A suitable answer records Ubuntu 26.04.1, the RTX 4060 baseline, Toolkit 13.3, the NVML and loaded-module versions, and the mismatch result. It asks which library file was actually selected and whether it matches the installed package set. It reports the lifecycle, pipe, pipeline, and loader experiments separately, with their reproduction commands. It explicitly leaves CUDA execution, profiling, and throughput unverified until a healthy GPU path is available.

**中文：** 合格答案应记录 Ubuntu 26.04.1、RTX 4060 基线、Toolkit 13.3、NVML 和已加载模块的版本，以及不匹配结果。未解问题可以是实际选择了哪个库文件，以及它是否与已安装软件包集合一致。生命周期、管道、流水线和加载器实验应分别报告，并附复现命令。CUDA 执行、性能采集和吞吐结果则明确保持未验证，直到能够使用正常的 GPU 路径完成实际检查。

## 16. Acceptance, Review, and Next Steps / 验收、复盘与下一步

**English:** Acceptance requires explanations and artifacts together. Run the four CPU laboratories, retain their output, and explain each expected failure without changing unrelated machine configuration. You should be able to identify the owner of every child and pipe endpoint in the examples, predict the pipeline status under both policies, and show why the private library can be found by one executable but not the other. Merely pasting successful output is insufficient if you cannot explain the resource transition that produced it.

**中文：** 验收需要解释与产物同时成立。运行四组 CPU 实验，保留输出，并在不修改无关机器配置的前提下解释每一种预期失败。你应能指出示例中每个子进程和管道端点的拥有者，预测两种策略下的流水线状态，并说明为什么一个程序能找到私有库而另一个不能。如果无法解释产生结果的资源状态转换，即使粘贴了成功输出，也不算完成了这一层理解。

**English:** The environment report must distinguish what is installed, what is selected, what is loaded, and what has actually run. Attach the date and commands, preserve unsuccessful observations, and label GPU measurements as pending under the current mismatch. This separation prevents a later reader from interpreting a compiler version as a GPU benchmark. It also makes the report useful after the environment changes, because the next engineer can repeat the same observations and compare the affected layer directly.

**中文：** 环境报告必须区分已经安装、当前选择、已经加载以及实际运行过什么。附上日期和命令，保留失败观察，并在当前不匹配条件下把 GPU 测量标注为待完成。这能防止后来的读者把编译器版本误读成 GPU 基准，也让报告在环境变化之后仍然有用，因为下一位工程师可以重复同样的观察，直接比较发生变化的层次，而不需要根据模糊描述重新猜测当时的状态。

**English:** The next technical step is to apply this model to a small CUDA program once the GPU environment has been restored through an appropriate, separately authorized maintenance process. Record build success, device initialization, correctness, and timing as separate milestones. When moving to SGLang, preserve the same questions about process ownership, readiness, cancellation, descriptors, limits, and library selection. The surface commands will change, but the system boundaries you learned to inspect remain the foundation of reliable inference engineering.

**中文：** 下一步是在 GPU 环境经过适当且单独授权的维护恢复后，把本课模型应用到一个小型 CUDA 程序。把构建成功、设备初始化、正确性验证和计时分成不同里程碑记录。进入 SGLang 时，也继续追问进程所有权、就绪状态、取消、描述符、资源限制和库选择等问题。表面的命令会变化，但本课学会检查的系统边界仍然存在，并构成可靠推理工程的基础，帮助你把已有系统经验迁移到新领域。

## Execution Record / 实际执行记录

**English:** On 2026-09-18, the four CPU laboratory blocks were extracted from this document and executed with their embedded assertions. All passed. The lifecycle outcomes were zero, seven, and zero; the retained-writer experiment timed out as intended and completed after closing the writer; the pipeline comparison returned zero and seven for identical output; the loader experiment failed with status 127 before the executable with `RUNPATH` returned 42. These are local observations, not GPU measurements or universally fixed operating-system outputs.

**中文：** 二〇二六年九月十八日，从本文提取四组 CPU 实验代码块，执行了其中的断言，全部通过。生命周期结果依次为零、七、零；保留写入端实验按预期超时，并在关闭写入端后完成；流水线实验在相同输出下分别返回零和七；加载器实验先以状态一百二十七失败，随后含 `RUNPATH` 的程序输出四十二。这些是本机观察，不是 GPU 测量，也不是所有操作系统都必须给出的固定输出。

**English:** The read-only inventory also executed successfully as a collector while retaining unsuccessful probe results. It recorded `nvcc` 13.3.73, `nvidia-smi` status 18 with the NVML mismatch, a module file reported by `modinfo` as 610.57.04, and the loaded module as 610.43.02. This directly demonstrates why disk metadata and loaded state must remain separate. The bilingual document checker and its seven unit tests passed; those checks validate documentation structure, not GPU functionality.

**中文：** 只读清点程序也成功完成采集，并保留了探测失败结果。它记录到 `nvcc` 13.3.73、带 NVML 不匹配信息的 `nvidia-smi` 状态十八、`modinfo` 所报告的磁盘模块 610.57.04，以及已加载模块 610.43.02。这直接说明磁盘元数据与加载状态必须分开记录。双语文档检查器及其七个单元测试通过，但这些检查验证的是文档结构，并不是 GPU 功能。

## Official References and Verification / 官方资料与验证记录

**English:** The linked Linux man-pages are maintained with the Linux system-call documentation project; the kernel and NVIDIA links are upstream documentation. They were consulted for the specific interfaces and version distinctions cited in the lesson on 2026-09-18. The explanatory scenarios and laboratory programs are original teaching material. The versioned CUDA link is intentionally preferred over the changing latest-documentation landing page.

**中文：** 文中链接的 Linux man-pages 来自 Linux 系统调用文档项目，内核与 NVIDIA 链接属于上游资料。核验日期为二〇二六年九月十八日，核验对象是课程引用的具体接口与版本区别。情景分析和实验程序为原创教学内容。CUDA 链接特意使用带版本归档，避免把不断变化的最新文档入口当作已经固定的本机环境说明。

- [Linux fork](https://man7.org/linux/man-pages/man2/fork.2.html) / 进程创建。
- [Linux execve](https://man7.org/linux/man-pages/man2/execve.2.html) / 程序映像替换。
- [Linux wait](https://man7.org/linux/man-pages/man2/waitpid.2.html) / 子进程状态回收。
- [Linux open](https://man7.org/linux/man-pages/man2/open.2.html) / 描述符与打开文件描述。
- [Linux pipe](https://man7.org/linux/man-pages/man7/pipe.7.html) / 管道与文件结束。
- [Linux signal](https://man7.org/linux/man-pages/man7/signal.7.html) / 信号处理边界。
- [GNU Bash reference manual](https://www.gnu.org/s/bash/manual/bash.html) / 流水线与 Shell 状态。
- [Linux path resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html) / 路径解析。
- [Linux dynamic loader](https://man7.org/linux/man-pages/man8/ld.so.8.html) / 动态库选择。
- [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) / 资源控制。
- [CUDA 13.3 Linux installation](https://docs.nvidia.com/cuda/archive/13.3.0/cuda-installation-guide-linux/index.html) / 版本对应的开发环境要求。
- [NVIDIA System Management Interface](https://docs.nvidia.com/deploy/nvidia-smi/index.html) / 管理接口与版本显示。
- [NVML error definitions](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceEnums.html) / 驱动与库不匹配错误。
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) / 容器 GPU 集成。
- [Nsight Systems](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) / 系统时间线。
- [Nsight Compute](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html) / Kernel 性能调查。
