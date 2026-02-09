from __future__ import annotations

import uuid
import unittest
from pathlib import Path
import shutil

from src.utils.config_loader import ConfigLoader
import src.utils.number_formatter as number_formatter


class TestUncertaintyRoundingConfig(unittest.TestCase):
    def test_config_inline_comment_stripped_for_rounding_mode(self):
        test_dir = Path(__file__).resolve().parent / f"tmp_uncertainty_rounding_{uuid.uuid4().hex}"
        test_dir.mkdir(parents=True, exist_ok=False)
        try:
            config_path = test_dir / "config.ini"
            config_path.write_text(
                "\n".join(
                    [
                        "[UncertaintyRounding]",
                        "significant_digits = 2",
                        "rounding_mode = round_up  # round_up or 5_percent",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            loader = ConfigLoader(str(config_path))
            self.assertEqual(loader.config.get("UncertaintyRounding", "rounding_mode"), "round_up")

            original = number_formatter.ConfigLoader
            try:
                number_formatter.ConfigLoader = lambda: ConfigLoader(str(config_path))
                self.assertEqual(number_formatter.format_expanded_uncertainty(288.6), "290.0")
            finally:
                number_formatter.ConfigLoader = original
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
