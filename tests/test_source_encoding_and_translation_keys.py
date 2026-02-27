import re
from pathlib import Path

import src.utils.translation_keys as translation_keys


def test_python_sources_are_utf8_decodable():
    root = Path(__file__).resolve().parents[1]
    targets = [root / "src", root / "tests"]
    files = []
    for target in targets:
        files.extend(target.rglob("*.py"))

    for path in files:
        # strict decode: fail on broken encoding bytes
        path.read_text(encoding="utf-8", errors="strict")


def test_tr_referenced_keys_exist_in_translation_keys():
    root = Path(__file__).resolve().parents[1]
    src_root = root / "src"
    tr_call_pattern = re.compile(r"\btr\(([_A-Z][_A-Z0-9]*)\)")
    used_keys = set()

    for path in src_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="strict")
        used_keys.update(tr_call_pattern.findall(text))

    missing = sorted(key for key in used_keys if not hasattr(translation_keys, key))
    assert not missing, f"Missing translation keys: {missing}"


def test_translation_keys_have_no_duplicate_assignments():
    root = Path(__file__).resolve().parents[1]
    key_file = root / "src" / "utils" / "translation_keys.py"
    text = key_file.read_text(encoding="utf-8", errors="strict")
    assignment_pattern = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=", re.MULTILINE)
    names = assignment_pattern.findall(text)

    duplicates = sorted({name for name in names if names.count(name) > 1})
    assert not duplicates, f"Duplicate key definitions found: {duplicates}"
