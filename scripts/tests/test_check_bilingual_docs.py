from __future__ import annotations

from pathlib import Path
import sys
import unittest


SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIRECTORY))

import check_bilingual_docs  # noqa: E402


class ValidateTextTests(unittest.TestCase):
    def validate(self, text: str):
        return check_bilingual_docs.validate_text(text, Path("docs/example.md"))

    def test_balanced_document_passes(self):
        text = """# Guide / 指南

**English:** A concise explanation.

**中文：** 一段简洁的解释。
"""

        self.assertEqual(self.validate(text), [])

    def test_missing_chinese_partner_fails(self):
        text = """# Guide / 指南

**English:** A concise explanation.
"""

        issues = self.validate(text)

        self.assertTrue(
            any("no following Chinese partner" in issue.message for issue in issues)
        )

    def test_reversed_pair_fails(self):
        text = """# Guide / 指南

**中文：** 一段简洁的解释。

**English:** A concise explanation.
"""

        issues = self.validate(text)

        self.assertTrue(
            any("appears before its English partner" in issue.message for issue in issues)
        )

    def test_legacy_label_fails(self):
        text = """# Guide / 指南

**English:** A concise explanation.

**中文：** 一段简洁的解释。

**Question:** What happens next?
"""

        issues = self.validate(text)

        self.assertTrue(any("legacy bilingual label" in issue.message for issue in issues))

    def test_code_fence_content_is_ignored(self):
        text = """# Guide / 指南

**English:** The sample is intentionally invalid as documentation.

**中文：** 该示例作为文档内容时会故意不合规范。

```markdown
**中文：** This reversed marker is sample data.
**Question:** This legacy marker is also sample data.
```
"""

        self.assertEqual(self.validate(text), [])

    def test_list_item_pairs_pass(self):
        text = """# Guide / 指南

- **English:** One paired item. **中文：** 一个配对条目。
- **English:** A wrapped paired item.
  **中文：** 一个换行的配对条目。
"""

        self.assertEqual(self.validate(text), [])

    def test_unclosed_fence_fails(self):
        text = """# Guide / 指南

**English:** The code block must close.

**中文：** 代码块必须闭合。

```python
print("hello")
"""

        issues = self.validate(text)

        self.assertTrue(any("unclosed fenced code block" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
