from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class LogWriteResult:
    ok: bool
    path: Optional[Path] = None
    error: Optional[Exception] = None


def _project_root() -> Path:
    # .../CalibrationUncertaintyTool/src/utils/app_logger.py -> .../CalibrationUncertaintyTool
    return Path(__file__).resolve().parents[2]


def _log_dir() -> Path:
    return _project_root() / "logs"


def _daily_log_path(prefix: str, now: datetime) -> Path:
    date_str = now.date().isoformat()
    return _log_dir() / f"{prefix}_{date_str}.log"


def _append_lines(path: Path, lines: list[str]) -> None:
    with path.open("a", encoding="utf-8", errors="replace", newline="\n") as f:
        f.write("\n".join(lines))


def _write_log(
    *,
    prefix: str,
    tag: str,
    message: str,
    details: str | None,
    now: datetime | None,
) -> LogWriteResult:
    """
    - エラー出力以外へ影響が出ないよう、ログ書き込みの失敗は例外を投げません。
    """
    try:
        now_dt = now or datetime.now()
        log_dir = _log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        path = _daily_log_path(prefix, now_dt)
        timestamp = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        header = f"{timestamp} [{tag}] {message}".rstrip()
        parts = [header]
        if details:
            parts.append(details.rstrip())
        parts.append("")  # newline

        _append_lines(path, parts)
        return LogWriteResult(ok=True, path=path)
    except Exception as e:
        return LogWriteResult(ok=False, error=e)

def log_error(
    message: str,
    error_type: str = "エラー",
    *,
    details: str | None = None,
    now: datetime | None = None,
) -> LogWriteResult:
    """
    エラーログを日付ごとのファイルへ追記します。

    - 出力先: <project_root>/logs/error_YYYY-MM-DD.log
    """
    return _write_log(prefix="error", tag=error_type, message=message, details=details, now=now)


def log_warning(
    message: str,
    *,
    details: str | None = None,
    now: datetime | None = None,
) -> LogWriteResult:
    """
    警告ログを日付ごとのファイルへ追記します。

    - 出力先: <project_root>/logs/warning_YYYY-MM-DD.log
    """
    return _write_log(prefix="warning", tag="警告", message=message, details=details, now=now)


def log_debug(
    message: str,
    *,
    details: str | None = None,
    now: datetime | None = None,
) -> LogWriteResult:
    """
    デバッグログを日付ごとのファイルへ追記します。

    - 出力先: <project_root>/logs/debug_YYYY-MM-DD.log
    """
    return _write_log(prefix="debug", tag="DEBUG", message=message, details=details, now=now)
