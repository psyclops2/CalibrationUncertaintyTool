import json
import os
import re
import hashlib
import tokenize
from collections import Counter
from io import StringIO
from pathlib import Path


# Fragments frequently seen when UTF-8 Japanese text becomes mojibake.
MOJIBAKE_FRAGMENTS = (
    "\u7e3a",  # 縺
    "\u7e67",  # 繧
    "\u7e5d",  # 繝
    "\u8373",  # 荳
    "\u879f",  # 螟
    "\u9015",  # 逕
    "\u96b1",  # 隱
    "\u8b5b",  # 譛
    "\u86fb",  # 蛻
    "\u8b28",  # 謨
    "\u87c7",  # 蟇
    "\u9a65",  # 驥
    "\u8708",  # 蜈
    "\u8c41",  # 豁
    "\ufffd",  # replacement character
)
FRAGMENT_PATTERN = re.compile("|".join(re.escape(x) for x in MOJIBAKE_FRAGMENTS))


def _comment_fingerprint(path: str, comment: str) -> str:
    normalized = re.sub(r"\s+", " ", comment.strip())
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]
    return f"{path}::{digest}"


def _collect_suspicious_comments(root: Path):
    suspicious = []
    targets = list((root / "src").rglob("*.py")) + list((root / "tests").rglob("*.py"))
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="strict")
        for tok in tokenize.generate_tokens(StringIO(text).readline):
            if tok.type != tokenize.COMMENT:
                continue
            if FRAGMENT_PATTERN.search(tok.string):
                rel_path = path.relative_to(root).as_posix()
                suspicious.append((rel_path, tok.start[0], tok.string))
    return sorted(set(suspicious))


def _collect_suspicious_comment_locations(root: Path):
    return sorted(
        f"{path}:{line}" for path, line, _ in _collect_suspicious_comments(root)
    )


def _collect_suspicious_comment_fingerprints(root: Path):
    return sorted(
        _comment_fingerprint(path, comment)
        for path, _, comment in _collect_suspicious_comments(root)
    )


def test_no_new_mojibake_in_comments_against_baseline():
    root = Path(__file__).resolve().parents[1]
    baseline_path = Path(__file__).resolve().parent / "mojibake_comment_baseline.json"
    baseline = set(json.loads(baseline_path.read_text(encoding="utf-8")))

    # Preferred format: "path::fingerprint"
    if any("::" in item for item in baseline):
        current = set(_collect_suspicious_comment_fingerprints(root))
        new_items = sorted(current - baseline)
        assert not new_items, (
            "New suspicious mojibake comments detected:\n"
            + "\n".join(new_items[:200])
            + ("\n... (truncated)" if len(new_items) > 200 else "")
        )
        return

    # Legacy format: "path:line". Keep compatibility without line-number fragility.
    current_locations = _collect_suspicious_comment_locations(root)
    baseline_counts = Counter(item.rsplit(":", 1)[0] for item in baseline)
    current_counts = Counter(item.rsplit(":", 1)[0] for item in current_locations)

    increased = sorted(
        f"{path} (+{current_counts[path] - baseline_counts.get(path, 0)})"
        for path in current_counts
        if current_counts[path] > baseline_counts.get(path, 0)
    )
    assert not increased, (
        "Suspicious mojibake comments increased for files:\n"
        + "\n".join(increased[:200])
        + ("\n... (truncated)" if len(increased) > 200 else "")
        + "\nPlease migrate baseline to fingerprint format."
    )


def test_no_mojibake_in_comments_when_strict_mode_enabled():
    if os.environ.get("STRICT_MOJIBAKE_CHECK") != "1":
        return

    root = Path(__file__).resolve().parents[1]
    current = _collect_suspicious_comment_locations(root)
    assert not current, (
        "Suspicious mojibake comments detected in strict mode:\n"
        + "\n".join(current[:200])
        + ("\n... (truncated)" if len(current) > 200 else "")
    )
