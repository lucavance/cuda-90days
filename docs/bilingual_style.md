# Bilingual Documentation Style / 双语文档规范

## Purpose / 目的

**English:** Reader-facing documentation in this repository is written for
both international and Chinese readers. English appears first, followed
immediately by the equivalent Chinese content, so both audiences can follow the
same structure and technical evidence.

**中文：** 本仓库面向读者的文档同时服务海外与中文读者。英文内容在前，等价的
中文内容紧随其后，使两类读者都能沿着相同结构阅读同一份技术证据。

## Scope / 适用范围

**English:** These rules apply to reader-facing Markdown files, including the
root README, directory guides, documents under `docs/`, and daily records under
`days/`. Internal agent instructions such as `AGENTS.md` are excluded from the
automated documentation scan.

**中文：** 本规范适用于面向读者的 Markdown 文件，包括根目录 README、各目录
指南、`docs/` 下的文档和 `days/` 下的每日记录。`AGENTS.md` 等内部 agent 指令
不在自动文档扫描范围内。

## Core Rules / 核心规则

### 1. Keep English First / 英文在前

**English:** Write the complete English unit first, then place its Chinese
translation immediately after it. Do not group all English into one half of a
document and all Chinese into another half.

**中文：** 先写完整的英文内容单元，再紧接其中文翻译。不要把全部英文集中在
文档前半部分、全部中文集中在后半部分。

### 2. Pair Headings / 配对标题

**English:** Use `English / 中文` for headings that need translation. A
language-neutral product name or API identifier such as `PyTorch`, `SGLang`, or
`cudaMemcpy` may stand alone.

**中文：** 需要翻译的标题使用 `English / 中文` 格式。`PyTorch`、`SGLang`、
`cudaMemcpy` 等语言无关的产品名或 API 标识符可以单独出现。

### 3. Pair Prose Explicitly / 显式配对正文

**English:** Use the following markers for ordinary prose. A paragraph may wrap
across lines, but its Chinese partner must appear before the next English
paragraph.

**中文：** 普通正文使用以下标签。段落可以跨行，但必须先给出对应中文内容，再
开始下一段英文。

```markdown
**English:** Explain the observation in precise, reproducible terms.

**中文：** 使用准确、可复现的语言解释该观察。
```

### 4. Keep Lists Locally Paired / 列表项就地配对

**English:** Short list items should keep both languages in one item, with
English first. Longer explanations should use paired prose blocks.

**中文：** 简短列表项应在同一个条目内保留两种语言，并将英文放在前面。较长的
解释应使用成对正文块。

```markdown
- Peak VRAM usage / 显存峰值
- Reproduction command / 复现命令
```

### 5. Do Not Duplicate Executable Examples / 不重复可执行示例

**English:** Keep commands, source code, console output, formulas, paths, and
configuration snippets as one canonical block. Do not translate identifiers or
duplicate a block merely to create a Chinese copy. Essential explanatory code
comments may use concise `English / 中文` wording.

**中文：** 命令、源代码、控制台输出、公式、路径和配置片段只保留一份权威代码
块。不要翻译标识符，也不要仅为中文再复制一份代码块。必要的解释性代码注释可以
使用简洁的 `English / 中文` 格式。

### 6. Preserve Meaning and Evidence / 保持语义与证据一致

**English:** Both language versions must communicate the same facts, caveats,
measurements, and next steps. Translation must not silently change commands,
benchmark values, error messages, or technical conclusions.

**中文：** 两种语言必须表达相同的事实、限制条件、测量结果和下一步。翻译不得
悄然改变命令、benchmark 数值、错误消息或技术结论。

## Daily Q&A Records / 每日问答记录

**English:** Interactive learning records use exactly ten numbered questions.
Each question follows this marker order, and the saved document does not include
the learner's original response:

**中文：** 交互式学习记录使用恰好 10 道编号问题。每道题都遵循以下标签顺序，
且保存的文档不包含学习者的原始回答：

```markdown
### 1. Concept Name / 概念名称

**Question (English):** What does this concept mean?

**问题（中文）：** 这个概念是什么意思？

**Explanation (English):** Explain why the concept matters.

**解说（中文）：** 解释这个概念为什么重要。

**Correct Answer (English):** State the complete correct answer.

**正确答案（中文）：** 给出完整的正确答案。
```

**English:** The topic, goal, summary, common mistakes, and next steps also use
paired English/Chinese prose. Experimental daily records that are not Q&A
sessions may use a normal bilingual report structure instead.

**中文：** 主题、目标、总结、常见错误和下一步也必须使用中英配对正文。不是问答
会话的每日实验记录可以使用普通双语实验报告结构。

## Validation / 校验

**English:** Run both commands before committing documentation changes:

**中文：** 提交文档变更前运行以下两条命令：

```bash
python3 scripts/check_bilingual_docs.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

**English:** The checker scans reader-facing Markdown by default, ignores
content inside fenced code blocks, checks fence closure and bilingual marker
order, rejects legacy bare Q&A labels, and verifies the ten-question structure
of daily Q&A records. One or more files or directories can be checked directly:

**中文：** 检查器默认扫描面向读者的 Markdown，忽略 fenced code block 内的
内容，检查代码围栏闭合与双语标签顺序，拒绝旧式裸问答标签，并验证每日问答记录
的十题结构。也可以直接检查一个或多个文件或目录：

```bash
python3 scripts/check_bilingual_docs.py README.md docs/ days/
```

## Maintenance Checklist / 维护清单

**English:** Before committing, confirm that:

**中文：** 提交前确认：

- Every new reader-facing section is bilingual / 每个新增的读者可见章节都是双语
- English precedes its Chinese partner / 英文位于对应中文之前
- Code and command behavior is unchanged / 代码和命令行为未改变
- Daily Q&A labels and counts are complete / 每日问答标签与数量完整
- The checker, tests, and `git diff --check` pass / 检查器、测试与 `git diff --check` 通过
