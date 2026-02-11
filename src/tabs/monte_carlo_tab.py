import traceback

import numpy as np
import sympy as sp
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.tabs.base_tab import BaseTab
from src.utils.app_logger import log_error
from src.utils.equation_handler import EquationHandler
from src.utils.equation_normalizer import normalize_equation_text
from src.utils.translation_keys import *
from src.utils.value_handler import ValueHandler
from src.utils.variable_utils import get_distribution_translation_key


class HistogramWidget(QWidget):
    DEFAULT_BINS = 80

    def __init__(self, parent=None):
        super().__init__(parent)
        self._samples = np.array([], dtype=float)
        self._counts = np.array([], dtype=float)
        self._bins = np.array([], dtype=float)
        self._sigma_bounds = None
        self._interval95_bounds = None
        self._empirical_interval95_bounds = None
        self._normal_curve_mean = None
        self._normal_curve_std = None
        self._median_value = None
        self._legend_label_sigma = "1σ"
        self._legend_label_interval = "95%"
        self._legend_label_empirical_interval = "95% Empirical"
        self._legend_label_normal = "Normal"
        self._legend_label_median = "Median"
        self._empty_text = "No data"
        self.setMinimumHeight(260)

    def set_empty_text(self, text):
        self._empty_text = text
        self.update()

    def clear_data(self):
        self._samples = np.array([], dtype=float)
        self._counts = np.array([], dtype=float)
        self._bins = np.array([], dtype=float)
        self._sigma_bounds = None
        self._interval95_bounds = None
        self._empirical_interval95_bounds = None
        self._normal_curve_mean = None
        self._normal_curve_std = None
        self._median_value = None
        self.update()

    def set_data(self, samples):
        array = np.asarray(samples, dtype=float)
        array = array[np.isfinite(array)]
        if array.size == 0:
            self.clear_data()
            return

        self._samples = array
        counts, bins = np.histogram(array, bins=self.DEFAULT_BINS)
        self._counts = counts.astype(float)
        self._bins = bins.astype(float)
        self.update()

    def set_reference_lines(self, sigma_bounds, interval95_bounds, empirical_interval95_bounds=None):
        self._sigma_bounds = sigma_bounds
        self._interval95_bounds = interval95_bounds
        self._empirical_interval95_bounds = empirical_interval95_bounds
        self.update()

    def set_normal_curve(self, mean_value, std_value):
        if mean_value is None or std_value is None or float(std_value) <= 0:
            self._normal_curve_mean = None
            self._normal_curve_std = None
        else:
            self._normal_curve_mean = float(mean_value)
            self._normal_curve_std = float(std_value)
        self.update()

    def set_median_line(self, median_value):
        if median_value is None:
            self._median_value = None
        else:
            self._median_value = float(median_value)
        self.update()

    def set_legend_labels(
        self,
        sigma_label,
        interval_label,
        empirical_interval_label,
        normal_label,
        median_label,
    ):
        self._legend_label_sigma = sigma_label
        self._legend_label_interval = interval_label
        self._legend_label_empirical_interval = empirical_interval_label
        self._legend_label_normal = normal_label
        self._legend_label_median = median_label
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        margin_left = 55
        margin_right = 25
        margin_top = 20
        margin_bottom = 35

        plot_rect = self.rect().adjusted(
            margin_left,
            margin_top,
            -margin_right,
            -margin_bottom,
        )

        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return

        if self._counts.size == 0:
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(self.rect(), Qt.AlignCenter, self._empty_text)
            return

        axis_pen = QPen(QColor(60, 60, 60))
        axis_pen.setWidth(1)
        painter.setPen(axis_pen)
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())

        max_count = float(np.max(self._counts))
        if max_count <= 0:
            painter.drawText(self.rect(), Qt.AlignCenter, self._empty_text)
            return

        bar_count = len(self._counts)
        bar_width = plot_rect.width() / max(bar_count, 1)
        painter.setPen(QPen(QColor(52, 120, 246)))
        painter.setBrush(QColor(140, 184, 255))

        for index, count in enumerate(self._counts):
            height_ratio = float(count) / max_count if max_count else 0.0
            bar_height = plot_rect.height() * height_ratio
            left = plot_rect.left() + index * bar_width + 1.0
            top = plot_rect.bottom() - bar_height
            width = max(bar_width - 2.0, 1.0)
            painter.drawRect(int(left), int(top), int(width), int(bar_height))

        x_min = float(self._bins[0])
        x_max = float(self._bins[-1])
        bin_width = float(self._bins[1] - self._bins[0]) if len(self._bins) > 1 else 1.0

        if (
            self._normal_curve_mean is not None
            and self._normal_curve_std is not None
            and self._normal_curve_std > 0
            and x_max > x_min
        ):
            xs = np.linspace(x_min, x_max, 220)
            std = self._normal_curve_std
            mean = self._normal_curve_mean
            coeff = 1.0 / (std * np.sqrt(2.0 * np.pi))
            pdf = coeff * np.exp(-0.5 * ((xs - mean) / std) ** 2)
            ys = pdf * max(len(self._samples), 1) * max(bin_width, 1e-12)

            curve_pen = QPen(QColor(255, 140, 0))
            curve_pen.setWidth(2)
            painter.setPen(curve_pen)

            prev_point = None
            for x_value, y_count in zip(xs, ys):
                x_ratio = (float(x_value) - x_min) / (x_max - x_min)
                y_ratio = float(y_count) / max_count if max_count > 0 else 0.0
                x_pos = plot_rect.left() + x_ratio * plot_rect.width()
                y_pos = plot_rect.bottom() - y_ratio * plot_rect.height()
                point = (int(x_pos), int(y_pos))
                if prev_point is not None:
                    painter.drawLine(prev_point[0], prev_point[1], point[0], point[1])
                prev_point = point

        def draw_vertical(value, pen):
            if x_max <= x_min:
                return
            ratio = (float(value) - x_min) / (x_max - x_min)
            x_pos = plot_rect.left() + ratio * plot_rect.width()
            if x_pos < plot_rect.left() or x_pos > plot_rect.right():
                return
            painter.setPen(pen)
            painter.drawLine(int(x_pos), plot_rect.top(), int(x_pos), plot_rect.bottom())

        if self._sigma_bounds is not None:
            sigma_pen = QPen(QColor(34, 139, 34))
            sigma_pen.setWidth(2)
            sigma_pen.setStyle(Qt.DashLine)
            draw_vertical(self._sigma_bounds[0], sigma_pen)
            draw_vertical(self._sigma_bounds[1], sigma_pen)

        if self._interval95_bounds is not None:
            interval_pen = QPen(QColor(220, 20, 60))
            interval_pen.setWidth(2)
            interval_pen.setStyle(Qt.DashDotLine)
            draw_vertical(self._interval95_bounds[0], interval_pen)
            draw_vertical(self._interval95_bounds[1], interval_pen)

        if self._empirical_interval95_bounds is not None:
            empirical_pen = QPen(QColor(0, 139, 139))
            empirical_pen.setWidth(2)
            empirical_pen.setStyle(Qt.DotLine)
            draw_vertical(self._empirical_interval95_bounds[0], empirical_pen)
            draw_vertical(self._empirical_interval95_bounds[1], empirical_pen)

        if self._median_value is not None:
            median_pen = QPen(QColor(148, 0, 211))
            median_pen.setWidth(2)
            draw_vertical(self._median_value, median_pen)

        legend_y = plot_rect.top() + 12
        legend_x = plot_rect.right() - 210
        sigma_pen_legend = QPen(QColor(34, 139, 34))
        sigma_pen_legend.setWidth(2)
        sigma_pen_legend.setStyle(Qt.DashLine)
        painter.setPen(sigma_pen_legend)
        painter.drawLine(legend_x, legend_y, legend_x + 18, legend_y)
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.drawText(legend_x + 24, legend_y + 4, self._legend_label_sigma)

        interval_pen_legend = QPen(QColor(220, 20, 60))
        interval_pen_legend.setWidth(2)
        interval_pen_legend.setStyle(Qt.DashDotLine)
        painter.setPen(interval_pen_legend)
        painter.drawLine(legend_x, legend_y + 16, legend_x + 18, legend_y + 16)
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.drawText(legend_x + 24, legend_y + 20, self._legend_label_interval)

        empirical_pen_legend = QPen(QColor(0, 139, 139))
        empirical_pen_legend.setWidth(2)
        empirical_pen_legend.setStyle(Qt.DotLine)
        painter.setPen(empirical_pen_legend)
        painter.drawLine(legend_x, legend_y + 32, legend_x + 18, legend_y + 32)
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.drawText(legend_x + 24, legend_y + 36, self._legend_label_empirical_interval)

        normal_pen_legend = QPen(QColor(255, 140, 0))
        normal_pen_legend.setWidth(2)
        painter.setPen(normal_pen_legend)
        painter.drawLine(legend_x, legend_y + 48, legend_x + 18, legend_y + 48)
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.drawText(legend_x + 24, legend_y + 52, self._legend_label_normal)

        median_pen_legend = QPen(QColor(148, 0, 211))
        median_pen_legend.setWidth(2)
        painter.setPen(median_pen_legend)
        painter.drawLine(legend_x, legend_y + 64, legend_x + 18, legend_y + 64)
        painter.setPen(QPen(QColor(40, 40, 40)))
        painter.drawText(legend_x + 24, legend_y + 68, self._legend_label_median)

        painter.setPen(QPen(QColor(80, 80, 80)))
        min_text = f"{self._bins[0]:.6g}"
        max_text = f"{self._bins[-1]:.6g}"
        painter.drawText(
            plot_rect.left() - 2,
            self.height() - 8,
            min_text,
        )
        max_text_width = painter.fontMetrics().horizontalAdvance(max_text)
        painter.drawText(
            plot_rect.right() - max_text_width + 2,
            self.height() - 8,
            max_text,
        )
        y_text = f"{int(max_count)}"
        painter.drawText(8, plot_rect.top() + 5, y_text)


class MonteCarloTab(BaseTab):
    DEFAULT_SAMPLE_COUNT = 100000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.value_handler = ValueHandler(parent)
        self.equation_handler = EquationHandler(parent)
        self._has_simulation_result = False
        self._last_simulation_key = None
        self.setup_ui()
        self.refresh_controls()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.settings_group = QGroupBox()
        settings_layout = QFormLayout()

        self.value_combo = QComboBox()
        self.value_combo.currentIndexChanged.connect(self.on_selection_changed)
        self.value_label = QLabel()
        settings_layout.addRow(self.value_label, self.value_combo)

        self.variable_combo = QComboBox()
        self.variable_combo.currentIndexChanged.connect(self.on_selection_changed)
        self.variable_label = QLabel()
        settings_layout.addRow(self.variable_label, self.variable_combo)

        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(100, 500000)
        self.samples_spin.setValue(self.DEFAULT_SAMPLE_COUNT)
        self.samples_spin.setSingleStep(1000)
        self.samples_spin.valueChanged.connect(self.on_selection_changed)
        self.samples_label = QLabel()
        settings_layout.addRow(self.samples_label, self.samples_spin)

        self.run_button = QPushButton()
        self.run_button.clicked.connect(self.run_simulation)
        run_layout = QHBoxLayout()
        run_layout.addWidget(self.run_button)
        run_layout.addStretch(1)
        settings_layout.addRow(run_layout)

        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)

        self.plot_group = QGroupBox()
        plot_layout = QVBoxLayout()
        self.histogram_widget = HistogramWidget(self)
        plot_layout.addWidget(self.histogram_widget)
        self.plot_group.setLayout(plot_layout)
        layout.addWidget(self.plot_group)

        self.stats_group = QGroupBox()
        stats_layout = QFormLayout()
        self.mean_text = QLabel("--")
        self.std_text = QLabel("--")
        self.interval95_text = QLabel("--")
        self.interval95_empirical_text = QLabel("--")
        self.min_text = QLabel("--")
        self.max_text = QLabel("--")
        self.mean_label = QLabel()
        self.std_label = QLabel()
        self.interval95_label = QLabel()
        self.interval95_empirical_label = QLabel()
        self.min_label = QLabel()
        self.max_label = QLabel()
        stats_layout.addRow(self.mean_label, self.mean_text)
        stats_layout.addRow(self.std_label, self.std_text)
        stats_layout.addRow(self.interval95_label, self.interval95_text)
        stats_layout.addRow(self.interval95_empirical_label, self.interval95_empirical_text)
        stats_layout.addRow(self.min_label, self.min_text)
        stats_layout.addRow(self.max_label, self.max_text)
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.settings_group.setTitle(self.tr(MONTE_CARLO_SETTINGS))
        self.plot_group.setTitle(self.tr(MONTE_CARLO_PLOT))
        self.stats_group.setTitle(self.tr(MONTE_CARLO_STATS))
        self.value_label.setText(self.tr(CALIBRATION_POINT) + ":")
        self.variable_label.setText(self.tr(RESULT_VARIABLE) + ":")
        self.samples_label.setText(self.tr(MONTE_CARLO_SAMPLES) + ":")
        self.run_button.setText(self.tr(MONTE_CARLO_RUN))
        self.mean_label.setText(self.tr(MONTE_CARLO_MEAN) + ":")
        self.std_label.setText(self.tr(MONTE_CARLO_STD) + ":")
        self.interval95_label.setText(self.tr(MONTE_CARLO_INTERVAL_95) + ":")
        self.interval95_empirical_label.setText(self.tr(MONTE_CARLO_INTERVAL_95_EMPIRICAL) + ":")
        self.min_label.setText(self.tr(MONTE_CARLO_MIN) + ":")
        self.max_label.setText(self.tr(MONTE_CARLO_MAX) + ":")
        self.histogram_widget.set_empty_text(self.tr(MONTE_CARLO_NO_DATA))
        self.histogram_widget.set_legend_labels(
            "1σ",
            "95%",
            self.tr(MONTE_CARLO_INTERVAL_95_EMPIRICAL),
            self.tr(MONTE_CARLO_NORMAL_CURVE),
            self.tr(MONTE_CARLO_MEDIAN),
        )
        self.refresh_controls()

    def showEvent(self, event):
        self.refresh_controls()
        self.run_simulation()
        super().showEvent(event)

    def refresh_controls(self):
        previous_key = self._current_selection_key()
        self.update_value_combo()
        self.update_variable_combo()
        current_key = self._current_selection_key()
        if current_key is None:
            self._invalidate_results(clear_display=True)
            return
        if self._has_simulation_result and previous_key != current_key:
            self._invalidate_results(clear_display=True)

    def update_value_combo(self):
        current_text = self.value_combo.currentText()
        self.value_combo.blockSignals(True)
        self.value_combo.clear()
        for name in getattr(self.parent, "value_names", []):
            self.value_combo.addItem(name)
        if current_text:
            index = self.value_combo.findText(current_text)
            if index >= 0:
                self.value_combo.setCurrentIndex(index)
        if self.value_combo.currentIndex() < 0 and self.value_combo.count() > 0:
            self.value_combo.setCurrentIndex(0)
        self.value_combo.blockSignals(False)

    def update_variable_combo(self):
        current_text = self.variable_combo.currentText()
        self.variable_combo.blockSignals(True)
        self.variable_combo.clear()

        variables = list(getattr(self.parent, "result_variables", []))
        for variable in variables:
            self.variable_combo.addItem(variable)

        if current_text:
            index = self.variable_combo.findText(current_text)
            if index >= 0:
                self.variable_combo.setCurrentIndex(index)
        if self.variable_combo.currentIndex() < 0 and self.variable_combo.count() > 0:
            self.variable_combo.setCurrentIndex(0)
        self.variable_combo.blockSignals(False)

    def on_selection_changed(self, *_):
        self._invalidate_results(clear_display=True)

    def _current_selection_key(self):
        result_variable = self.variable_combo.currentText().strip()
        value_index = self.value_combo.currentIndex()
        if not result_variable or value_index < 0:
            return None
        sample_count = int(self.samples_spin.value())
        return (result_variable, value_index, sample_count)

    def _invalidate_results(self, clear_display=True):
        self._has_simulation_result = False
        self._last_simulation_key = None
        if clear_display:
            self._clear_result()

    def _clear_result(self):
        self.mean_text.setText("--")
        self.std_text.setText("--")
        self.interval95_text.setText("--")
        self.interval95_empirical_text.setText("--")
        self.min_text.setText("--")
        self.max_text.setText("--")
        self.histogram_widget.set_normal_curve(None, None)
        self.histogram_widget.set_median_line(None)
        self.histogram_widget.clear_data()

    @staticmethod
    def _format_number(value):
        return f"{value:.6g}"

    def _resolve_distribution_key(self, variable):
        distribution = self.value_handler.get_distribution(variable)
        distribution_key = get_distribution_translation_key(distribution) or distribution
        if distribution_key:
            return distribution_key

        var_info = getattr(self.parent, "variable_values", {}).get(variable, {})
        if isinstance(var_info, dict):
            saved_distribution = var_info.get("distribution", "")
            normalized = get_distribution_translation_key(saved_distribution) or saved_distribution
            if normalized:
                return normalized
        return NORMAL_DISTRIBUTION

    def _generate_samples(self, central, standard_uncertainty, distribution_key, sample_count):
        if sample_count <= 0:
            return np.array([], dtype=float)

        if standard_uncertainty == 0:
            return np.full(sample_count, central, dtype=float)

        key = get_distribution_translation_key(distribution_key) or distribution_key

        if key == RECTANGULAR_DISTRIBUTION:
            half_width = standard_uncertainty * np.sqrt(3.0)
            return np.random.uniform(central - half_width, central + half_width, sample_count)

        if key == TRIANGULAR_DISTRIBUTION:
            half_width = standard_uncertainty * np.sqrt(6.0)
            return np.random.triangular(
                central - half_width,
                central,
                central + half_width,
                sample_count,
            )

        if key == U_DISTRIBUTION:
            half_width = standard_uncertainty * np.sqrt(2.0)
            beta_values = np.random.beta(0.5, 0.5, sample_count)
            return central + (2.0 * beta_values - 1.0) * half_width

        return np.random.normal(central, standard_uncertainty, sample_count)

    def _sample_input_variable(self, variable, sample_count):
        central_raw = self.value_handler.get_central_value(variable)
        uncertainty_raw = self.value_handler.get_standard_uncertainty(variable)

        if central_raw in ("", None):
            raise ValueError(f"Missing central value: {variable}")

        try:
            central = float(central_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid central value: {variable}") from exc

        if uncertainty_raw in ("", None):
            standard_uncertainty = 0.0
        else:
            try:
                standard_uncertainty = float(uncertainty_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid uncertainty: {variable}") from exc

        if standard_uncertainty < 0:
            raise ValueError(self.tr(MONTE_CARLO_INVALID_INPUT))

        distribution_key = self._resolve_distribution_key(variable)
        return self._generate_samples(
            central=central,
            standard_uncertainty=standard_uncertainty,
            distribution_key=distribution_key,
            sample_count=sample_count,
        )

    def _evaluate_result_samples(self, result_variable, sample_count):
        equation = self.equation_handler.get_target_equation(result_variable)
        if not equation or "=" not in equation:
            raise ValueError(f"No equation: {result_variable}")

        _, right_side = equation.split("=", 1)
        right_side = right_side.strip()
        variables = self.equation_handler.get_variables_from_equation(right_side)
        if not variables:
            raise ValueError(f"No input variables: {result_variable}")

        symbols = {var: sp.Symbol(var) for var in variables}
        expression = normalize_equation_text(right_side).replace("^", "**")
        sympy_expr = sp.sympify(expression, locals=symbols)
        ordered_symbols = [symbols[var] for var in variables]

        sampled_values = [self._sample_input_variable(var, sample_count) for var in variables]
        evaluator = sp.lambdify(ordered_symbols, sympy_expr, modules="numpy")
        result = evaluator(*sampled_values)

        result_array = np.asarray(result, dtype=float)
        if result_array.ndim == 0:
            result_array = np.full(sample_count, float(result_array), dtype=float)
        return result_array.reshape(-1)

    def run_simulation(self):
        try:
            result_variable = self.variable_combo.currentText().strip()
            value_index = self.value_combo.currentIndex()
            if not result_variable or value_index < 0:
                self._invalidate_results(clear_display=True)
                return

            self.value_handler.current_value_index = value_index
            sample_count = int(self.samples_spin.value())
            samples = self._evaluate_result_samples(result_variable, sample_count)

            finite_samples = samples[np.isfinite(samples)]
            if finite_samples.size == 0:
                self._invalidate_results(clear_display=True)
                return

            mean_value = float(np.mean(finite_samples))
            std_value = float(np.std(finite_samples, ddof=1)) if finite_samples.size > 1 else 0.0
            sigma_bounds = (mean_value - std_value, mean_value + std_value)
            interval95_bounds = (
                mean_value - 1.96 * std_value,
                mean_value + 1.96 * std_value,
            )
            empirical_interval95_bounds = np.percentile(finite_samples, [2.5, 97.5])

            self.histogram_widget.set_data(finite_samples)
            self.histogram_widget.set_reference_lines(
                sigma_bounds,
                interval95_bounds,
                empirical_interval95_bounds,
            )
            self.histogram_widget.set_normal_curve(mean_value, std_value)
            self.histogram_widget.set_median_line(float(np.median(finite_samples)))
            self.mean_text.setText(self._format_number(mean_value))
            self.std_text.setText(self._format_number(std_value))
            self.interval95_text.setText(
                f"[{self._format_number(interval95_bounds[0])}, {self._format_number(interval95_bounds[1])}]"
            )
            self.interval95_empirical_text.setText(
                f"[{self._format_number(float(empirical_interval95_bounds[0]))}, {self._format_number(float(empirical_interval95_bounds[1]))}]"
            )
            self.min_text.setText(self._format_number(float(np.min(finite_samples))))
            self.max_text.setText(self._format_number(float(np.max(finite_samples))))
            self._has_simulation_result = True
            self._last_simulation_key = (result_variable, value_index, sample_count)

        except Exception as e:
            self._invalidate_results(clear_display=True)
            log_error(
                f"Monte Carlo simulation error: {str(e)}",
                details=traceback.format_exc(),
            )
