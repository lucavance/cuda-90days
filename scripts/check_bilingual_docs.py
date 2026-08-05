#!/usr/bin/env python3
"""Validate the repository's paired English/Chinese Markdown convention."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from collections.abc import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "target",
    "venv",
}

FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
DAILY_DIRECTORY_RE = re.compile(r"^day\d{3}(?:_|$)")
NUMBERED_QUESTION_RE = re.compile(r"^###\s+(?P<number>\d+)\.")
QA_SECTION_RE = re.compile(r"^##\s+10 Concept Questions(?:\s*/|\s*$)")


@dataclass(frozen=True)
class PairSpec:
    name: str
    english: re.Pattern[str]
    chinese: re.Pattern[str]


PAIR_SPECS = (
    PairSpec(
        "prose",
        re.compile(r"\*\*English:\*\*"),
        re.compile(r"\*\*中文：\*\*"),
    ),
    PairSpec(
        "question",
        re.compile(r"^\s*\*\*Question \(English\):\*\*"),
        re.compile(r"^\s*\*\*问题（中文）：\*\*"),
    ),
    PairSpec(
        "explanation",
        re.compile(r"^\s*\*\*Explanation \(English\):\*\*"),
        re.compile(r"^\s*\*\*解说（中文）：\*\*"),
    ),
    PairSpec(
        "correct answer",
        re.compile(r"^\s*\*\*Correct Answer \(English\):\*\*"),
        re.compile(r"^\s*\*\*正确答案（中文）：\*\*"),
    ),
)

QA_PAIR_SPECS = PAIR_SPECS[1:]
QA_EVENT_ORDER = (
    ("question", "en"),
    ("question", "zh"),
    ("explanation", "en"),
    ("explanation", "zh"),
    ("correct answer", "en"),
    ("correct answer", "zh"),
)

LEGACY_MARKERS = (
    re.compile(r"\*\*(?:Question|Explanation|Correct Answer):\*\*"),
    re.compile(r"\*\*(?:问题|解说|正确答案)：\*\*"),
)


@dataclass(frozen=True, order=True)
class Issue:
    line: int
    message: str


def _non_fenced_lines(text: str) -> tuple[list[tuple[int, str]], list[Issue]]:
    """Return lines outside code fences and any fence-structure issues."""

    active_lines: list[tuple[int, str]] = []
    issues: list[Issue] = []
    opening_character: str | None = None
    opening_length = 0
    opening_line = 0

    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)

        if opening_character is None:
            if match:
                fence = match.group("fence")
                opening_character = fence[0]
                opening_length = len(fence)
                opening_line = line_number
            else:
                active_lines.append((line_number, line))
            continue

        if match:
            fence = match.group("fence")
            is_closing_fence = (
                fence[0] == opening_character
                and len(fence) >= opening_length
                and not match.group("rest").strip()
            )
            if is_closing_fence:
                opening_character = None
                opening_length = 0
                opening_line = 0

    if opening_character is not None:
        issues.append(Issue(opening_line, "unclosed fenced code block"))

    return active_lines, issues


def _pair_events(
    lines: Iterable[tuple[int, str]], spec: PairSpec
) -> list[tuple[int, str]]:
    events: list[tuple[int, str]] = []
    for line_number, line in lines:
        line_events = [
            *((match.start(), "en") for match in spec.english.finditer(line)),
            *((match.start(), "zh") for match in spec.chinese.finditer(line)),
        ]
        events.extend((line_number, language) for _, language in sorted(line_events))
    return events


def _validate_pair_order(
    lines: list[tuple[int, str]], spec: PairSpec
) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    events = _pair_events(lines, spec)
    pending_english_line: int | None = None

    for line_number, language in events:
        if language == "en":
            if pending_english_line is not None:
                issues.append(
                    Issue(
                        pending_english_line,
                        f"{spec.name} English marker has no following Chinese partner",
                    )
                )
            pending_english_line = line_number
            continue

        if pending_english_line is None:
            issues.append(
                Issue(
                    line_number,
                    f"{spec.name} Chinese marker appears before its English partner",
                )
            )
        else:
            pending_english_line = None

    if pending_english_line is not None:
        issues.append(
            Issue(
                pending_english_line,
                f"{spec.name} English marker has no following Chinese partner",
            )
        )

    return issues, len(events)


def _is_daily_record(path: Path) -> bool:
    return path.name == "README.md" and any(
        DAILY_DIRECTORY_RE.match(part) for part in path.parts
    )


def _validate_daily_qa(
    lines: list[tuple[int, str]], path: Path
) -> list[Issue]:
    issues: list[Issue] = []
    has_qa_section = any(QA_SECTION_RE.match(line) for _, line in lines)
    qa_events: list[tuple[int, str, str]] = []

    for spec in QA_PAIR_SPECS:
        for line_number, language in _pair_events(lines, spec):
            qa_events.append((line_number, spec.name, language))

    if not has_qa_section and not qa_events:
        return issues

    qa_events.sort()
    marker_counts: dict[tuple[str, str], int] = {
        (name, language): 0 for name, language in QA_EVENT_ORDER
    }
    for _, name, language in qa_events:
        marker_counts[(name, language)] += 1

    if _is_daily_record(path):
        for name, language in QA_EVENT_ORDER:
            count = marker_counts[(name, language)]
            if count != 10:
                label = "English" if language == "en" else "Chinese"
                issues.append(
                    Issue(
                        1,
                        f"daily Q&A requires 10 {label} {name} markers; found {count}",
                    )
                )

        numbered_questions = [
            (line_number, int(match.group("number")))
            for line_number, line in lines
            if (match := NUMBERED_QUESTION_RE.match(line))
        ]
        numbers = [number for _, number in numbered_questions]
        if numbers != list(range(1, 11)):
            line_number = numbered_questions[0][0] if numbered_questions else 1
            issues.append(
                Issue(
                    line_number,
                    "daily Q&A headings must be numbered exactly from 1 through 10",
                )
            )

    expected_events = [
        expected
        for _ in range(max(len(qa_events) // len(QA_EVENT_ORDER), 1))
        for expected in QA_EVENT_ORDER
    ]
    for index, (line_number, name, language) in enumerate(qa_events):
        if index >= len(expected_events):
            break
        if (name, language) != expected_events[index]:
            expected_name, expected_language = expected_events[index]
            issues.append(
                Issue(
                    line_number,
                    "Q&A markers are out of order; expected "
                    f"{expected_language} {expected_name}",
                )
            )
            break

    return issues


def validate_text(text: str, path: Path | str = Path("<memory>")) -> list[Issue]:
    """Validate one Markdown document and return sorted diagnostics."""

    document_path = Path(path)
    lines, issues = _non_fenced_lines(text)
    marker_count = 0

    for spec in PAIR_SPECS:
        pair_issues, event_count = _validate_pair_order(lines, spec)
        issues.extend(pair_issues)
        marker_count += event_count

    for line_number, line in lines:
        if any(pattern.search(line) for pattern in LEGACY_MARKERS):
            issues.append(
                Issue(
                    line_number,
                    "legacy bilingual label; use an explicit English/Chinese marker",
                )
            )

    if marker_count == 0:
        issues.append(
            Issue(
                1,
                "no paired bilingual markers found; add English and Chinese content",
            )
        )

    issues.extend(_validate_daily_qa(lines, document_path))
    return sorted(set(issues))


def _is_ignored(path: Path) -> bool:
    return path.name == "AGENTS.md" or any(
        part in IGNORED_DIRECTORY_NAMES for part in path.parts
    )


def discover_markdown_files(inputs: Sequence[str]) -> tuple[list[Path], list[str]]:
    """Resolve CLI inputs into Markdown files and discovery diagnostics."""

    candidates: list[Path] = []
    errors: list[str] = []
    requested_paths = [Path(value) for value in inputs]

    if not requested_paths:
        requested_paths = [REPO_ROOT]

    for requested_path in requested_paths:
        path = requested_path.resolve()
        if not path.exists():
            errors.append(f"{requested_path}:1: path does not exist")
            continue
        if path.is_dir():
            candidates.extend(path.rglob("*.md"))
        elif path.suffix.lower() == ".md":
            candidates.append(path)
        else:
            errors.append(f"{requested_path}:1: expected a Markdown file or directory")

    files = sorted({path for path in candidates if not _is_ignored(path)})
    return files, errors


def _display_path(path: Path) -> Path:
    try:
        return path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check paired English/Chinese Markdown documentation."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown files or directories; defaults to the repository",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files, discovery_errors = discover_markdown_files(args.paths)

    for error in discovery_errors:
        print(error, file=sys.stderr)

    issue_count = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            print(f"{_display_path(path)}:1: cannot read file: {error}", file=sys.stderr)
            issue_count += 1
            continue

        for issue in validate_text(text, path):
            print(
                f"{_display_path(path)}:{issue.line}: {issue.message}",
                file=sys.stderr,
            )
            issue_count += 1

    if discovery_errors or issue_count:
        print(
            f"Bilingual documentation check failed with "
            f"{len(discovery_errors) + issue_count} issue(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"Checked {len(files)} Markdown file(s): bilingual documentation is valid. "
        f"/ 已检查 {len(files)} 个 Markdown 文件：双语文档有效。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
