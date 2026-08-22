from __future__ import annotations

import base64
import csv
import io
import re
import xml.etree.ElementTree as ET
from typing import Any
from zipfile import ZipFile


COLUMN_ALIASES: dict[str, list[str]] = {
    "handle": ["达人昵称", "达人ID", "账号", "昵称", "handle", "username", "kol", "creator", "name"],
    "platform": ["平台", "渠道", "platform", "source"],
    "country": ["国家", "国家/地区", "地区", "市场", "country", "region", "market"],
    "category": ["达人分类", "类目", "品类", "category", "niche"],
    "commerce_niche": ["带货倾向", "带货类目", "commerce_niche"],
    "followers": ["粉丝总量", "粉丝", "followers", "fans", "follower_count"],
    "avg_views": ["视频平均播放量", "平均播放", "avg_views", "views", "average_views"],
    "engagement_rate": ["视频互动率", "互动率", "engagement_rate"],
    "sales_28d": ["近28天销量", "28天销量", "sales_28d", "28d_sales"],
    "email": ["达人邮箱", "邮箱", "email", "mail", "gmail"],
    "whatsapp": ["whatsapp", "wa", "电话", "手机号", "phone", "mobile"],
    "other_contacts": ["达人其他联系方式", "其他联系方式", "other_contacts", "social_links", "links"],
    "homepage_url": ["Tiktok达人详情", "TikTok达人详情", "主页链接", "主页", "homepage", "profile", "url", "link"],
    "fastmoss_url": ["FastMoss达人详情页", "FastMoss", "fastmoss_url"],
}


def normalize_key(value: str) -> str:
    return re.sub(r"[\s_：:（）()\-/]+", "", str(value or "").strip().lower())


def parse_number(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "")
    if not text:
        return 0.0
    multiplier = 1.0
    lower = text.lower()
    if lower.endswith("k"):
        multiplier = 1000.0
        text = text[:-1]
    elif lower.endswith("m"):
        multiplier = 1000000.0
        text = text[:-1]
    elif text.endswith("万"):
        multiplier = 10000.0
        text = text[:-1]
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) * multiplier if match else 0.0


def parse_percent(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    number = parse_number(text)
    if "%" in text:
        return number
    if 0 < number < 1:
        return number * 100
    return number


def _xlsx_shared_strings(zip_file: ZipFile) -> list[str]:
    try:
        xml = zip_file.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml)
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: list[str] = []
    for item in root.findall("a:si", ns):
        texts = [node.text or "" for node in item.findall(".//a:t", ns)]
        values.append("".join(texts))
    return values


def _xlsx_first_sheet_path(zip_file: ZipFile) -> str:
    names = zip_file.namelist()
    sheets = sorted(name for name in names if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
    if not sheets:
        raise ValueError("xlsx 文件没有可读取的工作表")
    return sheets[0]


def parse_xlsx(content: bytes) -> list[dict[str, str]]:
    with ZipFile(io.BytesIO(content)) as zf:
        shared = _xlsx_shared_strings(zf)
        sheet_xml = zf.read(_xlsx_first_sheet_path(zf))
    root = ET.fromstring(sheet_xml)
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: list[list[str]] = []
    for row in root.findall(".//a:sheetData/a:row", ns):
        values: list[str] = []
        current_col = 0
        for cell in row.findall("a:c", ns):
            ref = cell.attrib.get("r", "")
            col_letters = re.sub(r"\d+", "", ref)
            if col_letters:
                col_num = 0
                for char in col_letters:
                    col_num = col_num * 26 + ord(char.upper()) - 64
                while current_col < col_num - 1:
                    values.append("")
                    current_col += 1
            cell_type = cell.attrib.get("t", "")
            node = cell.find("a:v", ns)
            raw = node.text if node is not None else ""
            if cell_type == "s" and raw != "":
                text = shared[int(raw)] if int(raw) < len(shared) else ""
            elif cell_type == "inlineStr":
                text = "".join(t.text or "" for t in cell.findall(".//a:t", ns))
            else:
                text = raw
            values.append(text)
            current_col += 1
        rows.append(values)
    if not rows:
        return []
    headers = [str(value).strip() for value in rows[0]]
    output: list[dict[str, str]] = []
    for values in rows[1:]:
        if not any(str(value).strip() for value in values):
            continue
        item = {headers[i] if i < len(headers) else f"column_{i+1}": values[i] for i in range(len(values))}
        output.append(item)
    return output


def parse_delimited(content: str, filename: str) -> list[dict[str, str]]:
    sample = content[:2048]
    if filename.lower().endswith(".tsv"):
        dialect = csv.excel_tab
    else:
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
    return list(csv.DictReader(io.StringIO(content), dialect=dialect))


def field_map(headers: list[str]) -> dict[str, str]:
    normalized = {normalize_key(header): header for header in headers}
    mapping: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = normalize_key(alias)
            if key in normalized:
                mapping[target] = normalized[key]
                break
    return mapping


def standardize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    headers = list(rows[0].keys()) if rows else []
    mapping = field_map(headers)
    standardized: list[dict[str, Any]] = []
    for row in rows:
        item = {target: str(row.get(source, "") or "").strip() for target, source in mapping.items()}
        item.setdefault("platform", "TikTok")
        item["followers"] = parse_number(item.get("followers"))
        item["avg_views"] = parse_number(item.get("avg_views"))
        item["sales_28d"] = parse_number(item.get("sales_28d"))
        item["engagement_rate"] = parse_percent(item.get("engagement_rate"))
        item["raw"] = row
        standardized.append(item)
    return standardized, mapping


def parse_upload(filename: str, content: str = "", content_base64: str = "") -> tuple[list[dict[str, Any]], dict[str, str]]:
    lower = filename.lower()
    if content_base64:
        raw_bytes = base64.b64decode(content_base64)
    else:
        raw_bytes = content.encode("utf-8-sig")
    if lower.endswith(".xlsx"):
        rows = parse_xlsx(raw_bytes)
    else:
        text = raw_bytes.decode("utf-8-sig", errors="replace")
        rows = parse_delimited(text, filename)
    return standardize(rows)
