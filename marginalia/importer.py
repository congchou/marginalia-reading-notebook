"""Validation and parsing for user-supplied CSV imports."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from .database import DEFAULT_STATUS, STATUSES
from .ui import normalize_tags

CSV_COLUMNS = ("type", "word", "meaning", "sentence", "translation", "structure", "source", "tags", "status")
TYPE_ALIASES = {
    "生词": "vocabulary",
    "单词": "vocabulary",
    "word": "vocabulary",
    "vocabulary": "vocabulary",
    "难句": "sentences",
    "句子": "sentences",
    "sentence": "sentences",
    "sentences": "sentences",
}


@dataclass(frozen=True)
class ImportEntry:
    row_number: int
    table: str
    payload: dict[str, str]


@dataclass
class ImportResult:
    entries: list[ImportEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def csv_template() -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerow({"type": "生词", "word": "criterion", "meaning": "标准；准则", "sentence": "Range is the key criterion.", "source": "Paper title", "tags": "methods, ecology", "status": "待复习"})
    writer.writerow({"type": "难句", "sentence": "Although results vary, the trend remains.", "translation": "尽管结果不同，趋势仍然存在。", "structure": "让步状语从句 + 主句", "source": "Paper title", "tags": "syntax", "status": "学习中"})
    return output.getvalue().encode("utf-8-sig")


def parse_csv_upload(content: bytes) -> ImportResult:
    result = ImportResult()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.errors.append("文件编码无法识别，请在 Numbers 或 Excel 中导出为 UTF-8 CSV。")
        return result
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        headers = tuple((name or "").strip() for name in (reader.fieldnames or ()))
        missing = [column for column in CSV_COLUMNS if column not in headers]
        if missing:
            result.errors.append("缺少列：" + ", ".join(missing))
            return result
        seen: set[tuple[str, str]] = set()
        for row_number, raw in enumerate(reader, start=2):
            row = {key: str(raw.get(key) or "").strip() for key in CSV_COLUMNS}
            table = TYPE_ALIASES.get(row["type"].lower())
            if table is None:
                result.errors.append(f"第 {row_number} 行：type 必须是“生词”或“难句”。")
                continue
            required = ("word", "meaning") if table == "vocabulary" else ("sentence", "translation")
            empty = [column for column in required if not row[column]]
            if empty:
                result.errors.append(f"第 {row_number} 行：缺少必填内容 {', '.join(empty)}。")
                continue
            status = row["status"] or DEFAULT_STATUS
            if status not in STATUSES:
                result.errors.append(f"第 {row_number} 行：status 必须是待复习、学习中或已掌握。")
                continue
            identity = row["word"].lower() if table == "vocabulary" else row["sentence"].lower()
            marker = (table, identity)
            if marker in seen:
                result.errors.append(f"第 {row_number} 行：文件内存在重复内容。")
                continue
            seen.add(marker)
            if table == "vocabulary":
                payload = {key: row[key] for key in ("word", "meaning", "sentence", "source")}
            else:
                payload = {key: row[key] for key in ("sentence", "translation", "structure", "source")}
            payload.update(tags=normalize_tags(row["tags"]), status=status)
            result.entries.append(ImportEntry(row_number=row_number, table=table, payload=payload))
    except csv.Error as exc:
        result.errors.append(f"CSV 格式错误：{exc}")
    return result
