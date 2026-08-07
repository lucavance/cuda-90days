# Day 036: Ubuntu Basic Commands / Ubuntu 基本命令

Date / 日期: 2026-08-07

## Topic / 主题

**English:** Everyday Ubuntu command-line operations: directory navigation,
file manipulation, text and log inspection, redirection, pipelines, searching,
permissions, processes, system resources, package management, systemd services,
and journal logs.

**中文：** Ubuntu 日常命令行操作：目录导航、文件操作、文本与日志查看、
重定向、管道、搜索、权限、进程、系统资源、软件包管理、systemd 服务以及
journal 日志。

## Goal / 目标

**English:** Learn to select and interpret common Ubuntu commands, understand
their important options, distinguish related resource and search tools, and
perform routine inspection and maintenance with safe defaults.

**中文：** 学会选择和解释常用 Ubuntu 命令，理解其重要选项，区分相关的资源与
搜索工具，并使用安全的默认方式完成日常检查与维护。

## Core Mental Model / 核心思维模型

**English:** A shell command receives arguments and input, performs one focused
operation, and writes normal results or errors to output streams. Paths select
filesystem objects, permissions control access, pipelines compose commands,
and process, package, and service tools expose different layers of system
state.

**中文：** Shell 命令接收参数与输入，执行一个聚焦操作，并把正常结果或错误
写入输出流。路径选择文件系统对象，权限控制访问，管道组合命令，而进程、软件包
与服务工具分别展示不同层次的系统状态。

## 10 Concept Questions / 10 个概念问题

### 1. Current directory and directory listings / 当前目录与目录列表

**Question (English):** What does each command do? What additional information
does `ls -la` show compared with plain `ls`?

**问题（中文）：** 每条命令分别做什么？与普通 `ls` 相比，`ls -la` 还会显示
哪些信息？

```bash
pwd
ls
ls -la
```

**Explanation (English):** A shell maintains a current working directory, and
relative paths are interpreted from that location. `ls` lists directory
entries, while options change which entries and metadata are displayed.

**解说（中文）：** Shell 维护一个当前工作目录，相对路径以该位置为起点进行解释。
`ls` 列出目录项，而选项会改变显示哪些目录项以及显示哪些元数据。

**Correct Answer (English):** `pwd` prints the absolute path of the current
working directory. Plain `ls` normally lists non-hidden entries. In `ls -la`,
`-l` enables a long listing with type and permissions, link count, owner,
group, size, timestamp, and name; `-a` includes names beginning with `.`,
including the special `.` and `..` entries.

**正确答案（中文）：** `pwd` 打印当前工作目录的绝对路径。普通 `ls` 通常只列出
非隐藏目录项。`ls -la` 中，`-l` 启用长格式，显示类型与权限、链接数、所有者、
用户组、大小、时间戳和名称；`-a` 还显示以 `.` 开头的名称，包括特殊目录项
`.` 与 `..`。

**English:** `.` means the current directory and `..` means its parent. They
are special path components referring to directories, not a category of
ordinary files whose names happen to begin with two dots. GNU `ls -A` includes
ordinary hidden entries while omitting `.` and `..`.

**中文：** `.` 表示当前目录，`..` 表示其父目录。它们是指向目录的特殊路径组件，
而不是名称碰巧以两个点开头的一类普通文件。GNU `ls -A` 会包含普通隐藏目录项，
但省略 `.` 与 `..`。

### 2. Path navigation and special path forms / 路径导航与特殊路径形式

**Question (English):** What do `..`, `~`, and `-` mean in these commands?
Which command uses an absolute path?

**问题（中文）：** 这些命令中的 `..`、`~` 与 `-` 分别表示什么？哪个命令使用
绝对路径？

```bash
cd ..
cd /var/log
cd ~
cd -
```

**Explanation (English):** Filesystem paths can be absolute or relative. An
absolute path begins at the root directory `/`; a relative path is interpreted
from the current directory. The shell also expands convenient navigation
forms such as `~` and tracks the previous working directory.

**解说（中文）：** 文件系统路径可以是绝对路径或相对路径。绝对路径从根目录
`/` 开始，相对路径从当前目录开始解释。Shell 还会展开 `~` 等便利导航形式，并
记录上一个工作目录。

**Correct Answer (English):** `cd ..` enters the parent directory. `cd ~`
enters the current user's home directory. `cd -` switches to the previous
working directory, commonly using the shell's `OLDPWD` value; it does not mean
the directory involved in the most recent arbitrary command. `/var/log`
begins with `/`, so `cd /var/log` uses an absolute path.

**正确答案（中文）：** `cd ..` 进入父目录；`cd ~` 进入当前用户的主目录；
`cd -` 切换到上一个工作目录，通常使用 Shell 的 `OLDPWD` 值，它并不表示任意
上一条命令所涉及的目录。`/var/log` 以 `/` 开头，因此 `cd /var/log` 使用绝对
路径。

### 3. Creating, copying, moving, and deleting / 创建、复制、移动与删除

**Question (English):** What does each command do? What do the `-p` and `-i`
options provide?

**问题（中文）：** 每条命令分别做什么？`-p` 与 `-i` 选项分别提供什么作用？

```bash
mkdir -p backup/config
cp app.conf backup/config/
mv notes.txt notes.old
rm -i notes.old
```

**Explanation (English):** File-manipulation commands interpret each argument
as a source, destination, or option. Copying preserves the source while moving
changes its path or name. Deletion removes a directory entry and should be
performed with particular care because recovery is not built into `rm`.

**解说（中文）：** 文件操作命令把各参数解释为源、目标或选项。复制会保留源，
移动则改变其路径或名称。删除会移除目录项，需要格外谨慎，因为 `rm` 本身不提供
恢复机制。

**Correct Answer (English):** `mkdir -p backup/config` creates every missing
directory in the path and does not fail merely because an existing component
is already a directory. `cp` copies `app.conf` into `backup/config/`. `mv`
renames `notes.txt` to `notes.old` in this example, although it can also move a
file to another directory. `rm -i` asks for confirmation before removing
`notes.old`. Options such as `cp -i` can also reduce accidental overwrites.

**正确答案（中文）：** `mkdir -p backup/config` 会创建路径中所有缺失的目录；
若已有组件本来就是目录，也不会仅因此失败。`cp` 把 `app.conf` 复制到
`backup/config/`。这里的 `mv` 把 `notes.txt` 重命名为 `notes.old`，它也可以把
文件移动到其他目录。`rm -i` 会在删除 `notes.old` 前请求确认。`cp -i` 等选项
也可以减少意外覆盖。

### 4. Inspecting text files and live logs / 查看文本文件与实时日志

**Question (English):** What does each command do? Which command is suitable
for interactively reading a large existing log, and which is suitable for
following newly appended log lines?

**问题（中文）：** 每条命令分别做什么？交互式阅读已有的大型日志应选择哪个？
持续观察新追加的日志行又应选择哪个？

```bash
cat config.yaml
less server.log
head -n 20 server.log
tail -n 50 -f server.log
```

**Explanation (English):** Different viewers serve different access patterns.
Dumping a small file is convenient, but a pager is safer and easier to navigate
for a large file. A follow mode is useful when another process is actively
appending log records.

**解说（中文）：** 不同查看工具适合不同访问模式。直接输出小文件很方便，但对
大文件而言，分页器更安全且更容易导航；当另一个进程正在持续追加日志时，follow
模式更合适。

**Correct Answer (English):** `cat` writes the whole file to standard output
without interactive paging. `less` opens an interactive pager that supports
scrolling and searching and is appropriate for a large existing log. `head
-n 20` prints the first 20 lines. `tail -n 50 -f` first prints the last 50
lines, then waits for and displays appended data. Pressing `q` exits `less`,
and `Ctrl-C` normally stops `tail -f`.

**正确答案（中文）：** `cat` 把整个文件写到标准输出，不提供交互分页。`less`
打开支持滚动与搜索的交互式分页器，适合已有的大型日志。`head -n 20` 输出前
20 行。`tail -n 50 -f` 先输出最后 50 行，然后等待并显示新追加的数据。按 `q`
退出 `less`，通常使用 `Ctrl-C` 停止 `tail -f`。

### 5. Output redirection and pipelines / 输出重定向与管道

**Question (English):** What do `>`, `>>`, and `|` do? If `run.log` already
contains data, what remains after the first two commands execute?

**问题（中文）：** `>`、`>>` 与 `|` 分别做什么？如果 `run.log` 原来已有内容，
执行前两条命令后会保留什么？

```bash
echo "start" > run.log
echo "done" >> run.log
grep "ERROR" app.log | tail -n 20
```

**Explanation (English):** Redirection connects a command's output to a file.
A pipeline connects the standard output of the command on the left to the
standard input of the command on the right, allowing focused commands to be
composed without an intermediate file.

**解说（中文）：** 重定向把命令输出连接到文件。管道把左侧命令的标准输出连接到
右侧命令的标准输入，从而无需中间文件即可组合多个聚焦命令。

**Correct Answer (English):** `>` creates or truncates `run.log` and writes
`start`. `>>` creates the file if necessary or appends `done` without removing
the current content. The resulting file contains:

**正确答案（中文）：** `>` 创建或清空 `run.log`，然后写入 `start`。`>>` 在
需要时创建文件，否则在不删除现有内容的情况下追加 `done`。最终文件内容为：

```text
start
done
```

**English:** In the pipeline, `grep` emits matching lines from `app.log`, and
`tail` displays the final 20 matching lines. The pipeline carries `grep`'s
output, not the file object itself.

**中文：** 在该管道中，`grep` 输出 `app.log` 中匹配的行，`tail` 显示其中最后
20 条匹配行。管道传递的是 `grep` 的输出，而不是文件对象本身。

### 6. Finding files and searching file contents / 查找文件与搜索文件内容

**Question (English):** What does each command search? What is the main
difference between `find` and `grep`, and why is `'*.py'` quoted?

**问题（中文）：** 每条命令搜索什么？`find` 与 `grep` 的主要区别是什么？
为什么要给 `'*.py'` 加引号？

```bash
find . -type f -name '*.py'
grep -Rni 'error' logs/
```

**Explanation (English):** `find` traverses filesystem entries and filters by
metadata such as name or type. `grep` examines text for matching patterns. The
shell performs wildcard expansion before launching a command unless wildcard
characters are quoted.

**解说（中文）：** `find` 遍历文件系统目录项，并按名称、类型等元数据筛选；
`grep` 检查文本是否匹配模式。若通配符没有被引用，Shell 会在启动命令之前先进行
通配符展开。

**Correct Answer (English):** `find` recursively walks from the current
directory, keeps ordinary files with `-type f`, and selects names ending in
`.py`. `grep -Rni` recursively searches under `logs/`, ignores letter case,
and prints line numbers for text matching `error`. Quoting `'*.py'` prevents
the shell from expanding it against the current directory and passes the
pattern unchanged to `find`; within that pattern, `*` matches zero or more
characters.

**正确答案（中文）：** `find` 从当前目录开始递归遍历，通过 `-type f` 保留普通
文件，并选择名称以 `.py` 结尾的文件。`grep -Rni` 在 `logs/` 下递归搜索，忽略
字母大小写，并为匹配 `error` 的文本显示行号。引用 `'*.py'` 会阻止 Shell 按
当前目录提前展开它，让模式原样传给 `find`；在该模式中，`*` 匹配零个或多个
字符。

### 7. Reading and setting file permissions / 读取与设置文件权限

**Question (English):** Interpret the type and three permission groups in this
long listing. What numeric mode represents these permissions?

**问题（中文）：** 解释这条长格式列表中的类型与三组权限。这些权限对应什么
数字模式？

```text
-rwxr-x--- 1 luca developers 1200 Aug 7 10:00 deploy.sh
```

**Explanation (English):** The first character indicates the file type. The
next nine characters form three `rwx` groups for the owner, group, and others.
Numeric modes use `r = 4`, `w = 2`, and `x = 1`, summing each group separately.

**解说（中文）：** 第一个字符表示文件类型，接下来的九个字符组成所有者、用户组
与其他用户三组 `rwx` 权限。数字模式使用 `r = 4`、`w = 2`、`x = 1`，并对每组
分别求和。

**Correct Answer (English):** The leading `-` denotes a regular file; `d`
would denote a directory and `l` a symbolic link. The owner has `rwx`, which
is 7. The group has `r-x`, which is 5. Others have no permissions, which is 0.
The corresponding command is:

**正确答案（中文）：** 开头的 `-` 表示普通文件；`d` 表示目录，`l` 表示符号
链接。所有者拥有 `rwx`，数值为 7；用户组拥有 `r-x`，数值为 5；其他用户没有
权限，数值为 0。对应命令为：

```bash
chmod 750 deploy.sh
```

### 8. Locating and terminating processes / 查找与终止进程

**Question (English):** What does each command do? How do `kill 1234` and
`kill -9 1234` differ, and which should normally be attempted first?

**问题（中文）：** 每条命令分别做什么？`kill 1234` 与 `kill -9 1234` 有何
区别？通常应先尝试哪个？

```bash
ps aux
pgrep -af sglang
kill 1234
kill -9 1234
```

**Explanation (English):** Process-inspection commands produce snapshots or
search process metadata. The `kill` command sends a signal; despite its name,
the default signal is a request for orderly termination rather than an
unavoidable immediate kill.

**解说（中文）：** 进程检查命令会生成快照或搜索进程元数据。`kill` 命令发送
信号；尽管名称如此，其默认信号是请求有序终止，而不是无法避免的立即强杀。

**Correct Answer (English):** `ps aux` displays a detailed snapshot of
processes for all users. `pgrep -af sglang` matches `sglang` against full
command lines and prints each PID with its command. `kill 1234` normally sends
`SIGTERM`, which a process can handle to shut down and clean up. `kill -9 1234`
sends `SIGKILL`, which cannot be handled or ignored and gives the process no
cleanup opportunity. Send `SIGTERM` first and reserve `SIGKILL` for a process
that fails to exit after an appropriate wait.

**正确答案（中文）：** `ps aux` 显示所有用户进程的详细快照。
`pgrep -af sglang` 使用完整命令行匹配 `sglang`，并打印各 PID 与命令。
`kill 1234` 通常发送 `SIGTERM`，进程可以处理该信号并执行关闭清理。
`kill -9 1234` 发送无法处理或忽略的 `SIGKILL`，进程没有清理机会。应先发送
`SIGTERM`，经过适当等待仍未退出时，才考虑 `SIGKILL`。

### 9. Disk, memory, and live resource inspection / 磁盘、内存与实时资源检查

**Question (English):** What does each command inspect? How can `df` and `du`
be combined when a filesystem is full, and which command helps identify a
memory-heavy process?

**问题（中文）：** 每条命令检查什么？文件系统已满时，如何结合 `df` 与 `du`
定位问题？哪个命令有助于识别高内存占用进程？

```bash
df -h
du -sh .
free -h
top
```

**Explanation (English):** Filesystem capacity, per-path disk usage, system
memory, and per-process activity are different measurements. Similar words
such as “free space” do not make disk and RAM interchangeable resources.

**解说（中文）：** 文件系统容量、逐路径磁盘占用、系统内存和逐进程活动是不同的
测量维度。“剩余空间”等相似表述并不表示磁盘与 RAM 是可以混淆的资源。

**Correct Answer (English):** `df -h` reports capacity and free space by
mounted filesystem. `du -sh .` summarizes disk blocks used under the current
path. `free -h` reports RAM and swap usage. `top` interactively displays
process CPU and memory activity; pressing `M` commonly sorts by memory. When a
filesystem is full, use `df -h` to identify the affected mount, then inspect
candidate paths on that filesystem with commands such as `du -sh *`. Hidden
entries, permissions, deleted-but-open files, and mount boundaries may require
additional investigation.

**正确答案（中文）：** `df -h` 按已挂载文件系统报告容量与剩余空间；`du -sh .`
汇总当前路径下占用的磁盘块；`free -h` 报告 RAM 与 swap 使用情况；`top` 交互式
显示进程 CPU 与内存活动，通常可以按 `M` 以内存排序。文件系统已满时，先用
`df -h` 找出受影响的挂载点，再在该文件系统的候选路径中使用 `du -sh *` 等命令
检查。隐藏目录项、权限、已经删除但仍被打开的文件和挂载边界可能需要进一步
排查。

### 10. Packages, services, and journal logs / 软件包、服务与 Journal 日志

**Question (English):** What does each command do? How do `apt update` and
`apt upgrade` differ?

**问题（中文）：** 每条命令分别做什么？`apt update` 与 `apt upgrade` 有何区别？

```bash
sudo apt update
sudo apt upgrade
sudo apt install curl
systemctl status ssh
journalctl -u ssh -n 50
```

**Explanation (English):** Ubuntu's package manager separates refreshing
repository metadata from changing installed packages. Systemd separately
manages service units and stores many service logs in its journal.

**解说（中文）：** Ubuntu 软件包管理器把刷新仓库元数据与修改已安装软件包分成
不同操作。Systemd 则独立管理 service unit，并在 journal 中保存许多服务日志。

**Correct Answer (English):** `apt update` downloads current package indexes
but does not by itself upgrade installed packages. `apt upgrade` installs
available upgrades for installed packages according to those indexes.
`apt install curl` installs the named package and required dependencies.
`systemctl status ssh` displays the current state and recent status information
for the Ubuntu SSH service. `journalctl -u ssh -n 50` displays the latest 50
journal records for that unit; adding `-f` follows new records. Administrative
package changes require `sudo`, and access to some service information or logs
may also depend on permissions.

**正确答案（中文）：** `apt update` 下载当前软件包索引，但本身不会升级已安装
软件包；`apt upgrade` 根据这些索引安装已安装软件包的可用升级。
`apt install curl` 安装指定软件包及其必要依赖。`systemctl status ssh` 显示
Ubuntu SSH 服务的当前状态与近期状态信息。`journalctl -u ssh -n 50` 显示该
unit 最近 50 条 journal 记录；增加 `-f` 可以持续观察新记录。修改软件包需要
`sudo`，访问某些服务信息或日志也可能受到权限限制。

## Summary / 总结

- **English:** `pwd`, `ls`, and `cd` establish location and navigation, while
  `.`, `..`, `~`, and `-` have distinct path meanings.
  **中文：** `pwd`、`ls` 与 `cd` 用于确定位置和导航，而 `.`、`..`、`~` 与 `-`
  分别具有不同的路径含义。
- **English:** `mkdir`, `cp`, `mv`, and `rm` manipulate filesystem entries;
  confirmation and exact target paths reduce destructive mistakes.
  **中文：** `mkdir`、`cp`、`mv` 与 `rm` 操作文件系统目录项；确认机制与准确目标
  路径能够减少破坏性错误。
- **English:** `cat`, `less`, `head`, and `tail` support different file and log
  reading patterns.
  **中文：** `cat`、`less`、`head` 与 `tail` 分别支持不同的文件和日志读取模式。
- **English:** Redirection writes command output to files, while pipelines pass
  output directly between commands.
  **中文：** 重定向把命令输出写入文件，管道则在命令之间直接传递输出。
- **English:** `find` selects filesystem entries, whereas `grep` searches text
  content; quoting controls whether the shell expands wildcard patterns.
  **中文：** `find` 筛选文件系统目录项，`grep` 搜索文本内容；引用决定 Shell
  是否提前展开通配模式。
- **English:** Long permission strings and numeric modes encode file type and
  owner, group, and other access rights.
  **中文：** 长格式权限字符串与数字模式编码文件类型，以及所有者、用户组和其他
  用户的访问权。
- **English:** Process signals should escalate from graceful termination to
  forced termination only when necessary.
  **中文：** 进程信号应从优雅终止逐步升级，仅在必要时才进行强制终止。
- **English:** Disk capacity, path usage, RAM, process activity, packages,
  services, and logs are separate system layers with dedicated tools.
  **中文：** 磁盘容量、路径占用、RAM、进程活动、软件包、服务与日志是不同系统
  层次，各自具有专用工具。

## Common Mistakes / 常见错误

- **English:** Treating `..` as a category of names rather than the exact
  special path component for the parent directory.
  **中文：** 把 `..` 当成一类文件名，而不是表示父目录的精确特殊路径组件。
- **English:** Describing `ls -la` only as a detailed listing and forgetting
  that `-a` includes hidden entries.
  **中文：** 只把 `ls -la` 描述为详细列表，而忘记 `-a` 会包含隐藏目录项。
- **English:** Using `cat` as an interactive large-file viewer instead of
  selecting `less`.
  **中文：** 把 `cat` 当成交互式大文件查看器，而没有选择 `less`。
- **English:** Misreading the requested line count in `tail -n 50` or
  overlooking that `-f` continues following appended data.
  **中文：** 看错 `tail -n 50` 请求的行数，或忽略 `-f` 会继续跟踪追加数据。
- **English:** Leaving wildcard patterns unquoted when the receiving program,
  rather than the shell, must interpret them.
  **中文：** 当通配模式应由接收程序而非 Shell 解释时，没有为其添加引用。
- **English:** Forgetting to add each permission group's `r`, `w`, and `x`
  values separately, such as calculating `rwxr-x---` as 600 instead of 750.
  **中文：** 忘记分别累加每组权限的 `r`、`w` 与 `x`，例如把 `rwxr-x---` 错算
  为 600，而不是 750。
- **English:** Using `SIGKILL` immediately instead of first allowing a process
  to handle `SIGTERM` and clean up.
  **中文：** 立即使用 `SIGKILL`，而没有先让进程处理 `SIGTERM` 并执行清理。
- **English:** Confusing the RAM and swap report from `free` with disk-space
  reports from `df` and `du`.
  **中文：** 混淆 `free` 的 RAM 与 swap 报告，以及 `df`、`du` 的磁盘空间报告。
- **English:** Expecting `apt update` alone to upgrade installed packages, or
  overlooking `journalctl` when diagnosing a systemd service.
  **中文：** 误以为仅执行 `apt update` 就会升级已安装软件包，或在诊断 systemd
  服务时忽略 `journalctl`。

## Next Steps / 下一步建议

1. **English:** Learn standard input, standard output, standard error, file
   descriptors, `2>`, `2>&1`, and safe command-output capture.
   **中文：** 学习标准输入、标准输出、标准错误、文件描述符、`2>`、`2>&1` 以及
   安全的命令输出捕获。
2. **English:** Practice environment variables, quoting rules, command
   substitution, exit status, `&&`, and `||` in small shell scripts.
   **中文：** 在小型 Shell 脚本中练习环境变量、引用规则、命令替换、退出状态、
   `&&` 与 `||`。
3. **English:** Study ownership and permission administration with `chown`,
   `chgrp`, `umask`, directory execute permission, and access-control lists.
   **中文：** 学习使用 `chown`、`chgrp`、`umask`、目录执行权限与访问控制列表
   管理所有权和权限。
4. **English:** Add archive and network diagnostics with `tar`, `gzip`,
   `curl`, `ip`, `ss`, `ping`, and DNS lookup tools.
   **中文：** 补充 `tar`、`gzip`、`curl`、`ip`、`ss`、`ping` 与 DNS 查询工具，
   学习归档和网络诊断。
5. **English:** Run a safe hands-on lab that creates a temporary directory,
   generates sample logs, filters them through pipelines, inspects permissions,
   and removes only the explicitly verified temporary path.
   **中文：** 运行一个安全实践：创建临时目录、生成示例日志、通过管道过滤、检查
   权限，并且只删除经过明确确认的临时路径。
