#!/usr/bin/env python3
"""Clean a messy CSV file.

Trims extra spaces, fixes capitalisation of names, lowercases emails,
standardises phone numbers and dates, and removes empty and duplicate rows.
Uses only the Python standard library.
"""

import argparse
import csv
import io
import re
import sys
from datetime import datetime
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DATE_FORMATS = ["%Y-%m-%d", "%d.%m.%Y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"]
SLASH_FORMATS_MONTH_FIRST = ["%m/%d/%Y", "%m/%d/%y"]
SLASH_FORMATS_DAY_FIRST = ["%d/%m/%Y", "%d/%m/%y"]


def clean_text(value):
    """Trim the value and collapse repeated spaces."""
    return " ".join(value.split())


def clean_name(value):
    """Fix capitalisation only when the name is all lower or all upper case."""
    value = clean_text(value)
    if value.islower() or value.isupper():
        return value.title()
    return value


def clean_email(value):
    return clean_text(value).lower()


def clean_phone(value):
    """Keep digits and a leading plus sign: '+38 (050) 123-45-67' -> '+380501231234567'."""
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    if not digits:
        return ""
    return ("+" if value.startswith("+") else "") + digits


def clean_date(value, day_first):
    """Return the date as YYYY-MM-DD, or None when the format is not recognised."""
    value = clean_text(value)
    if not value:
        return ""
    slash_formats = SLASH_FORMATS_DAY_FIRST if day_first else SLASH_FORMATS_MONTH_FIRST
    for fmt in DATE_FORMATS + slash_formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def column_kind(header):
    """Guess what a column contains from its header."""
    name = header.lower()
    if "email" in name or "e-mail" in name:
        return "email"
    if "phone" in name or "tel" in name or "mobile" in name:
        return "phone"
    if "date" in name:
        return "date"
    if "name" in name:
        return "name"
    return "text"


def detect_delimiter(text):
    """Excel in some countries exports with semicolons instead of commas."""
    try:
        return csv.Sniffer().sniff(text[:2048], delimiters=",;\t").delimiter
    except csv.Error:
        return ","


def clean_rows(rows, day_first):
    header = [clean_text(cell) for cell in rows[0]]
    kinds = [column_kind(h) for h in header]
    email_index = kinds.index("email") if "email" in kinds else None

    stats = {
        "read": 0,
        "empty": 0,
        "duplicates": 0,
        "invalid_emails": 0,
        "bad_dates": 0,
    }
    cleaned_rows = []
    seen = set()

    for row in rows[1:]:
        stats["read"] += 1
        row = (row + [""] * len(header))[: len(header)]

        cleaned = []
        for value, kind in zip(row, kinds):
            if kind == "email":
                cleaned.append(clean_email(value))
            elif kind == "phone":
                cleaned.append(clean_phone(value))
            elif kind == "name":
                cleaned.append(clean_name(value))
            elif kind == "date":
                result = clean_date(value, day_first)
                if result is None:
                    stats["bad_dates"] += 1
                    result = clean_text(value)
                cleaned.append(result)
            else:
                cleaned.append(clean_text(value))

        if not any(cleaned):
            stats["empty"] += 1
            continue

        if email_index is not None and cleaned[email_index]:
            key = cleaned[email_index]
            if not EMAIL_RE.match(key):
                stats["invalid_emails"] += 1
        else:
            key = tuple(cleaned)

        if key in seen:
            stats["duplicates"] += 1
            continue
        seen.add(key)
        cleaned_rows.append(cleaned)

    return header, cleaned_rows, stats


def main():
    parser = argparse.ArgumentParser(description="Clean a messy CSV file.")
    parser.add_argument("input", help="path to the CSV file to clean")
    parser.add_argument("-o", "--output", help="where to save the result (default: <input>_cleaned.csv)")
    parser.add_argument(
        "--day-first",
        action="store_true",
        help="read dates like 03/04/2025 as 3 April instead of March 4",
    )
    args = parser.parse_args()

    source = Path(args.input)
    if not source.is_file():
        sys.exit(f"File not found: {source}")

    text = source.read_text(encoding="utf-8-sig")
    delimiter = detect_delimiter(text)
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    if not rows:
        sys.exit("The file is empty.")

    header, cleaned_rows, stats = clean_rows(rows, args.day_first)

    target = Path(args.output) if args.output else source.with_name(source.stem + "_cleaned.csv")
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(cleaned_rows)

    print(f"Rows read:          {stats['read']}")
    print(f"Empty rows removed: {stats['empty']}")
    print(f"Duplicates removed: {stats['duplicates']}")
    print(f"Rows written:       {len(cleaned_rows)}")
    if stats["invalid_emails"]:
        print(f"Warning: {stats['invalid_emails']} row(s) have an invalid email (kept, please check).")
    if stats["bad_dates"]:
        print(f"Warning: {stats['bad_dates']} date(s) could not be recognised (left as they were).")
    print(f"Saved to: {target}")


if __name__ == "__main__":
    main()
