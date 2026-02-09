from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from src.utils.translation_keys import BUTTON_CANCEL, BUTTON_SAVE


class SettingsDialog(QDialog):
    def __init__(self, config_loader, parent=None):
        super().__init__(parent)
        self.config_loader = config_loader
        self.main_window = parent
        self.setMinimumWidth(460)
        self._build_ui()
        self._load_values()
        self.retranslate_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        self.calculation_group = QGroupBox(self)
        calculation_layout = QFormLayout(self.calculation_group)
        self.precision_spin = QSpinBox(self)
        self.precision_spin.setRange(1, 200)
        calculation_layout.addRow(QLabel(self), self.precision_spin)

        self.rounding_group = QGroupBox(self)
        rounding_layout = QFormLayout(self.rounding_group)
        self.significant_digits_spin = QSpinBox(self)
        self.significant_digits_spin.setRange(1, 10)
        self.rounding_mode_combo = QComboBox(self)
        self.rounding_mode_combo.addItem("", "round_up")
        self.rounding_mode_combo.addItem("", "5_percent")
        rounding_layout.addRow(QLabel(self), self.significant_digits_spin)
        rounding_layout.addRow(QLabel(self), self.rounding_mode_combo)

        self.language_group = QGroupBox(self)
        language_layout = QFormLayout(self.language_group)
        self.language_combo = QComboBox(self)
        self.language_combo.addItem("日本語", "ja")
        self.language_combo.addItem("English", "en")
        self.use_system_locale_checkbox = QCheckBox(self)
        language_layout.addRow(QLabel(self), self.language_combo)
        language_layout.addRow(QLabel(self), self.use_system_locale_checkbox)

        self.calibration_group = QGroupBox(self)
        calibration_layout = QFormLayout(self.calibration_group)
        self.min_points_spin = QSpinBox(self)
        self.min_points_spin.setRange(1, 999)
        self.max_points_spin = QSpinBox(self)
        self.max_points_spin.setRange(1, 999)
        calibration_layout.addRow(QLabel(self), self.min_points_spin)
        calibration_layout.addRow(QLabel(self), self.max_points_spin)
        self.min_points_spin.valueChanged.connect(self._sync_point_limits)
        self.max_points_spin.valueChanged.connect(self._sync_point_limits)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            self,
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        root_layout.addWidget(self.calculation_group)
        root_layout.addWidget(self.rounding_group)
        root_layout.addWidget(self.language_group)
        root_layout.addWidget(self.calibration_group)
        root_layout.addWidget(self.button_box)

        self.precision_label = self.calculation_group.layout().labelForField(self.precision_spin)
        self.significant_digits_label = self.rounding_group.layout().labelForField(self.significant_digits_spin)
        self.rounding_mode_label = self.rounding_group.layout().labelForField(self.rounding_mode_combo)
        self.language_label = self.language_group.layout().labelForField(self.language_combo)
        self.use_system_locale_label = self.language_group.layout().labelForField(self.use_system_locale_checkbox)
        self.min_points_label = self.calibration_group.layout().labelForField(self.min_points_spin)
        self.max_points_label = self.calibration_group.layout().labelForField(self.max_points_spin)

    def _load_values(self):
        config = self.config_loader.config

        self.precision_spin.setValue(config.getint("Calculation", "precision", fallback=28))
        self.significant_digits_spin.setValue(
            config.getint("UncertaintyRounding", "significant_digits", fallback=2)
        )

        mode = config.get("UncertaintyRounding", "rounding_mode", fallback="5_percent").strip()
        mode_index = self.rounding_mode_combo.findData(mode)
        self.rounding_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 1)

        language = config.get("Language", "current", fallback="ja").strip().lower()
        language_index = self.language_combo.findData(language)
        self.language_combo.setCurrentIndex(language_index if language_index >= 0 else 0)
        self.use_system_locale_checkbox.setChecked(
            config.getboolean("Language", "use_system_locale", fallback=False)
        )

        self.min_points_spin.setValue(config.getint("CalibrationPoints", "min_count", fallback=1))
        self.max_points_spin.setValue(config.getint("CalibrationPoints", "max_count", fallback=30))
        self._sync_point_limits()

    def _sync_point_limits(self):
        minimum = self.min_points_spin.value()
        maximum = self.max_points_spin.value()
        if minimum > maximum:
            sender = self.sender()
            if sender is self.min_points_spin:
                self.max_points_spin.setValue(minimum)
            else:
                self.min_points_spin.setValue(maximum)

    def _is_japanese(self):
        if self.main_window and getattr(self.main_window, "language_manager", None):
            return self.main_window.language_manager.current_language == "ja"
        return True

    def retranslate_ui(self):
        ja = self._is_japanese()

        self.setWindowTitle("アプリ設定" if ja else "Application Settings")
        self.calculation_group.setTitle("計算" if ja else "Calculation")
        self.rounding_group.setTitle("表示と丸め" if ja else "Display and Rounding")
        self.language_group.setTitle("言語" if ja else "Language")
        self.calibration_group.setTitle("校正点の制限" if ja else "Calibration Point Limits")

        self.precision_label.setText("計算精度 (precision):" if ja else "Calculation precision:")
        self.significant_digits_label.setText("有効数字:" if ja else "Significant digits:")
        self.rounding_mode_label.setText("丸めモード:" if ja else "Rounding mode:")
        self.language_label.setText("表示言語:" if ja else "UI language:")
        self.use_system_locale_label.setText("システムロケールを使用:" if ja else "Use system locale:")
        self.min_points_label.setText("最小校正点数:" if ja else "Minimum points:")
        self.max_points_label.setText("最大校正点数:" if ja else "Maximum points:")

        current_mode = self.rounding_mode_combo.currentData()
        self.rounding_mode_combo.setItemText(0, "常に切り上げ" if ja else "Always round up")
        self.rounding_mode_combo.setItemText(1, "5%ルール" if ja else "5% rule")
        if current_mode:
            mode_index = self.rounding_mode_combo.findData(current_mode)
            if mode_index >= 0:
                self.rounding_mode_combo.setCurrentIndex(mode_index)

        save_button = self.button_box.button(QDialogButtonBox.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if save_button is not None:
            save_button.setText(self.tr(BUTTON_SAVE))
        if cancel_button is not None:
            cancel_button.setText(self.tr(BUTTON_CANCEL))

    def get_values(self):
        return {
            "calculation_precision": str(self.precision_spin.value()),
            "rounding_significant_digits": str(self.significant_digits_spin.value()),
            "rounding_mode": self.rounding_mode_combo.currentData(),
            "language_current": self.language_combo.currentData(),
            "language_use_system_locale": str(self.use_system_locale_checkbox.isChecked()).lower(),
            "calibration_min_count": str(self.min_points_spin.value()),
            "calibration_max_count": str(self.max_points_spin.value()),
        }
