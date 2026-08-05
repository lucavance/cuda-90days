# Scripts / 脚本

**English:** This directory contains repository-wide utilities for environment
checks, data downloads, experiment launches, result processing, and report
generation.

**中文：** 本目录用于存放仓库级通用脚本，例如环境检查、数据下载、实验启动、
结果整理和报告生成。

**English:** Place scripts dedicated to a specific benchmark in
`benchmarks/scripts/` instead.

**中文：** 具体 benchmark 脚本优先放在 `benchmarks/scripts/`。

## Bilingual Documentation Check / 双语文档检查

**English:** Validate all reader-facing Markdown and run the checker tests with:

**中文：** 使用以下命令校验全部读者可见 Markdown，并运行检查器测试：

```bash
python3 scripts/check_bilingual_docs.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

**English:** Pass file or directory paths to check only selected documentation.

**中文：** 传入文件或目录路径可以只检查指定文档。

```bash
python3 scripts/check_bilingual_docs.py README.md docs/
```
