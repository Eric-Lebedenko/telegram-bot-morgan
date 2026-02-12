from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ButtonSpec:
    label: str
    action: str
    style: str | None = None


@dataclass
class UIMessage:
    text: str
    buttons: list[list[ButtonSpec]] | None = None
    parse_mode: str = 'Markdown'
    expect_input: str | None = None
    input_hint: str | None = None


def format_section(title: str, body: str) -> str:
    return f"*{title}*\n{body}"


def format_kv(pairs: Iterable[tuple[str, str]]) -> str:
    lines = [f"*{k}:* {v}" for k, v in pairs]
    return "\n".join(lines)


def paginate(items: list[str], page: int, per_page: int = 5) -> tuple[list[str], int, int]:
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, total
