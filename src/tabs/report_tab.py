import csv
import io
import os
import traceback
from pathlib import Path
import sympy as sp
import numpy as np
import html as html_lib
import textwrap
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QFileDialog, QTextEdit, QLabel, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot
from src.utils.equation_handler import EquationHandler
from src.utils.value_handler import ValueHandler
from src.utils.uncertainty_calculator import UncertaintyCalculator
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.variable_utils import get_distribution_translation_key
from src.utils.equation_formatter import EquationFormatter
from src.utils.app_logger import log_error
from src.utils.markdown_renderer import render_markdown_to_html

class ReportTab(BaseTab):
    UNIT_PLACEHOLDER = '-'
    _FALLBACK_REPORT_CSS = textwrap.dedent("""\
        body { font-family: sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: auto; }
        .title { font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px;}
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .three-line, .three-line thead, .three-line tbody, .three-line tr, .three-line th, .three-line td { border: none !important; }
        .three-line th, .three-line td { padding: 8px; text-align: left; }
        .three-line .tl-first th, .three-line .tl-first td { border-top: 1.5px solid #222 !important; }
        .three-line .tl-header th, .three-line .tl-header td { border-bottom: 1px solid #666 !important; }
        .three-line .tl-last th, .three-line .tl-last td { border-bottom: 1.5px solid #222 !important; }
        .equation { font-family: 'Times New Roman', serif; font-size: 16px; padding: 10px; border: 1px solid #ccc; margin-bottom: 20px; }
        .doc-table th { width: 180px; }
        .subtitle { font-size: 20px; font-weight: bold; margin-top: 10px; margin-bottom: 6px; }
        .description-body { border: 1px solid #ddd; padding: 10px; }
        .revision-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .revision-table th, .revision-table td { border: none; padding: 8px; text-align: left; }
    """).strip()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._last_generated_html = None

        
        # 繝ｦ繝ｼ繝・ぅ繝ｪ繝・ぅ繧ｯ繝ｩ繧ｹ縺ｮ蛻晄悄蛹・
        self.equation_handler = EquationHandler(parent)
        self.value_handler = ValueHandler(parent)
        self.uncertainty_calculator = UncertaintyCalculator(parent)
        self.equation_formatter = EquationFormatter(parent)

        self.setup_ui()

    def _get_unit(self, var_name):
        """Get unit for a variable."""
        try:
            if not self.parent:
                return ''

            var_info = self.parent.variable_values.get(var_name, {})
            unit = var_info.get('unit', '').strip()
            if unit:
                return unit

            value_index = getattr(self.value_handler, 'current_value_index', None)
            if isinstance(value_index, int):
                values = var_info.get('values', [])
                if 0 <= value_index < len(values):
                    return values[value_index].get('unit', '').strip()

            return ''
        except Exception:
            return ''

    @staticmethod
    def _format_with_unit(value_text, unit):
        """Append a unit to value text for display."""
        if not value_text or value_text in ['--', '-']:
            return value_text

        unit = unit.strip()
        if unit and value_text.rstrip().endswith(unit):
            return value_text

        display_unit = unit if unit else ReportTab.UNIT_PLACEHOLDER
        if value_text.rstrip().endswith(ReportTab.UNIT_PLACEHOLDER):
            return value_text

        return f"{value_text} {display_unit}"

    @staticmethod
    def _format_multiline_cell(text, placeholder='-'):
        """Escape multiline text for HTML table cells."""
        if text is None:
            return placeholder
        raw_text = str(text)
        if not raw_text.strip():
            return placeholder
        normalized = raw_text.replace('\r\n', '\n').replace('\r', '\n')
        escaped = html_lib.escape(normalized)
        return escaped.replace('\n', '<br>')

    @staticmethod
    def _to_display_text(value, placeholder='-'):
        if value is None:
            return placeholder
        text = str(value).strip()
        return text if text else placeholder

    @staticmethod
    def _build_cell_html(text, tag="td"):
        return f"<{tag}>{html_lib.escape(str(text))}</{tag}>"

    @staticmethod
    def _format_variable_name_html(name):
        """Format variable name like V_ref_stability to V<sub>ref_stability</sub>."""
        raw = str(name)
        base, sep, suffix = raw.partition("_")
        if not sep or not suffix:
            return html_lib.escape(raw)
        return f"{html_lib.escape(base)}<sub>{html_lib.escape(suffix)}</sub>"

    def _build_variable_cell_html(self, name, tag="td"):
        return f"<{tag}>{self._format_variable_name_html(name)}</{tag}>"

    @staticmethod
    def _render_three_line_table(rows, header_row_indexes=None, table_classes="three-line"):
        if not rows:
            return f"<table class=\"{table_classes}\"><tbody></tbody></table>"

        header_set = set(header_row_indexes or [])
        last_index = len(rows) - 1
        rendered_rows = []
        for idx, row_cells in enumerate(rows):
            classes = []
            if idx == 0:
                classes.append("tl-first")
            elif idx == last_index:
                classes.append("tl-last")
            else:
                classes.append("tl-middle")
            if idx in header_set:
                classes.append("tl-header")
            rendered_rows.append(f"<tr class=\"{' '.join(classes)}\">{''.join(row_cells)}</tr>")

        return f"<table class=\"{table_classes}\"><tbody>{''.join(rendered_rows)}</tbody></table>"

    def _format_measurements_table(self, measurements):
        raw = self._to_display_text(measurements, '')
        if not raw:
            return "<div>-</div>"
        normalized = raw.replace('，', ',').replace('\r', '\n')
        items = [part for part in re.split(r'[\s,\n]+', normalized) if part.strip()]
        if not items:
            return "<div>-</div>"
        table_rows = [[
            self._build_cell_html(self.tr(REPORT_MEASUREMENT_NUMBER), "th"),
            self._build_cell_html(self.tr(REPORT_VALUE), "th"),
        ]]
        table_rows.extend(
            [
                self._build_cell_html(idx + 1),
                self._build_cell_html(item),
            ]
            for idx, item in enumerate(items)
        )
        return self._render_three_line_table(table_rows, header_row_indexes={0})

    def _format_two_row_table(self, headers, values):
        if not headers or not values or len(headers) != len(values):
            return "<div>-</div>"
        rows = [
            [self._build_cell_html(h, "th") for h in headers],
            [self._build_cell_html(v) for v in values],
        ]
        return self._render_three_line_table(rows, header_row_indexes={0})

    @staticmethod
    def _format_description_block(text):
        markdown_html = render_markdown_to_html(text or "")
        body = markdown_html if markdown_html else "-"
        return f'<div class="description-body">{body}</div>'

    @staticmethod
    def _format_markdown_inline_or_placeholder(text, placeholder='-'):
        markdown_html = render_markdown_to_html(text or "")
        return markdown_html if markdown_html else placeholder

    def retranslate_ui(self):
        """Retranslate UI text."""
        self.result_label.setText(self.tr(RESULT_VARIABLE) + ":")
        self.generate_button.setText(self.tr(GENERATE_REPORT))
        self.save_button.setText(self.tr(SAVE_REPORT))
        # 繝ｬ繝昴・繝医ｒ蜀咲函謌舌＠縺ｦ陦ｨ遉ｺ繧呈峩譁ｰ
        self.generate_report()
        
    def setup_ui(self):
        """Set up UI widgets."""

        main_layout = QVBoxLayout()
        
        # 驕ｸ謚樣Κ蛻・・繝ｬ繧､繧｢繧ｦ繝・
        selection_layout = QHBoxLayout()
        
        # 險育ｮ礼ｵ先棡驕ｸ謚・
        self.result_combo = QComboBox()
        self.result_combo.currentTextChanged.connect(self.on_result_changed)
        self.result_label = QLabel(self.tr(RESULT_VARIABLE) + ":")
        selection_layout.addWidget(self.result_label)
        selection_layout.addWidget(self.result_combo)
        
        # 繝ｬ繝昴・繝育函謌舌・繧ｿ繝ｳ
        self.generate_button = QPushButton(self.tr(GENERATE_REPORT))
        self.generate_button.clicked.connect(self.generate_report)
        selection_layout.addWidget(self.generate_button)
        
        # 繝ｬ繝昴・繝井ｿ晏ｭ倥・繧ｿ繝ｳ
        self.save_button = QPushButton(self.tr(SAVE_REPORT))
        self.save_button.clicked.connect(self.save_report)
        selection_layout.addWidget(self.save_button)
        
        selection_layout.addStretch()
        main_layout.addLayout(selection_layout)
        
        # 繝ｬ繝昴・繝郁｡ｨ遉ｺ驛ｨ蛻・
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        main_layout.addWidget(self.report_display)
        
        self.setLayout(main_layout)

        
    def update_variable_list(self, variables=None, result_variables=None):
        """Refresh result variable list."""
        try:
            current_text = self.result_combo.currentText()
            target_result = None
            if hasattr(self.parent, 'get_selected_result_variable'):
                target_result = self.parent.get_selected_result_variable()
            if not target_result and current_text:
                target_result = current_text

            self.result_combo.blockSignals(True)
            self.result_combo.clear()
            
            # 蠑墓焚縺ｧ貂｡縺輔ｌ縺溷ｴ蜷医・縺昴ｌ繧剃ｽｿ逕ｨ
            if result_variables:

                self.result_combo.addItems(result_variables)
            # 隕ｪ繧ｦ繧｣繝ｳ繝峨え縺九ｉ險育ｮ礼ｵ先棡螟画焚繧貞叙蠕・
            elif hasattr(self.parent, 'result_variables'):
                result_vars = self.parent.result_variables

                self.result_combo.addItems(result_vars)
            else:
                pass

            if target_result:
                index = self.result_combo.findText(target_result)
                if index >= 0:
                    self.result_combo.setCurrentIndex(index)
            if self.result_combo.currentIndex() < 0 and self.result_combo.count() > 0:
                self.result_combo.setCurrentIndex(0)
            self.result_combo.blockSignals(False)

            # 繝ｬ繝昴・繝医・譖ｴ譁ｰ
            self.update_report()
            
        except Exception as e:
            self.result_combo.blockSignals(False)
            log_error(f"螟画焚繝ｪ繧ｹ繝域峩譁ｰ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            
    def on_result_changed(self, result_var):
        """Handle result variable change."""
        if not result_var:
            return
            
        try:
            combo_index = self.result_combo.findText(result_var)
            if combo_index >= 0:
                current_index = self.result_combo.currentIndex()
                if current_index != combo_index:
                    self.result_combo.blockSignals(True)
                    self.result_combo.setCurrentIndex(combo_index)
                    self.result_combo.blockSignals(False)
            if hasattr(self.parent, 'set_selected_result_variable'):
                self.parent.set_selected_result_variable(result_var)
            calc_tab = getattr(self.parent, 'uncertainty_calculation_tab', None)
            if calc_tab and hasattr(calc_tab, 'result_combo'):
                result_index = calc_tab.result_combo.findText(result_var)
                current_index = (
                    calc_tab.result_combo.currentIndex()
                    if hasattr(calc_tab.result_combo, 'currentIndex')
                    else None
                )
                if result_index >= 0 and current_index != result_index:
                    if hasattr(calc_tab.result_combo, 'blockSignals'):
                        calc_tab.result_combo.blockSignals(True)
                    calc_tab.result_combo.setCurrentIndex(result_index)
                    if hasattr(calc_tab.result_combo, 'blockSignals'):
                        calc_tab.result_combo.blockSignals(False)
                    if hasattr(calc_tab, 'on_result_changed'):
                        calc_tab.on_result_changed(result_var)
            self.update_report()
        except Exception as e:
            log_error(f"險育ｮ礼ｵ先棡螟画峩繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            
    def generate_report(self):
        """Generate and display report HTML."""
        try:

            
            # 驕ｸ謚槭＆繧後◆險育ｮ礼ｵ先棡螟画焚繧貞叙蠕・
            result_var = self.result_combo.currentText()
            if not result_var:

                return
                
            # 驕ｸ謚槭＆繧後◆險育ｮ礼ｵ先棡螟画焚縺ｮ蠑上ｒ蜿門ｾ・
            equation = self.equation_handler.get_target_equation(result_var)
            if not equation:

                return
                
            # 繝ｬ繝昴・繝医・HTML繧堤函謌・
            html = self.generate_report_html(equation)
            self._last_generated_html = html
            
            # 繝ｬ繝昴・繝医ｒ陦ｨ遉ｺ
            self.report_display.setHtml(html)

            
        except Exception as e:
            log_error(f"繝ｬ繝昴・繝育函謌舌お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            QMessageBox.warning(self, self.tr(SAVE_ERROR), self.tr(REPORT_SAVE_ERROR))
            


    def _get_css_dir(self):
        """
        Return the `css/` directory under the project root.
        `report_tab.py` is under `src/tabs/`, so the project root is `.../src/..`.
        """
        try:
            return Path(__file__).resolve().parents[2] / "css"
        except Exception:
            return None

    @staticmethod
    def _read_text_file(path):
        try:
            return Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except Exception as e:
            log_error(f"CSS隱ｭ霎ｼ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            return ""

    def _get_report_css(self):
        css_dir = self._get_css_dir()
        if not css_dir:
            return self._FALLBACK_REPORT_CSS

        default_css = self._read_text_file(css_dir / "default.css").strip()
        custom_css = self._read_text_file(css_dir / "custom.css").strip()

        combined = "\n\n".join([part for part in [default_css, custom_css] if part]).strip()
        return combined if combined else self._FALLBACK_REPORT_CSS

    def _get_model_equation_text(self):
        """Return the model equation text before dependency resolution."""
        equation_text = getattr(self.parent, 'last_equation', '') if self.parent else ''
        if not equation_text and self.parent and hasattr(self.parent, 'model_equation_tab'):
            equation_text = self.parent.model_equation_tab.equation_input.toPlainText().strip()
        return equation_text

    def _get_input_variable_names(self):
        variables = getattr(self.parent, 'variables', [])
        result_variables = getattr(self.parent, 'result_variables', [])
        if isinstance(variables, dict):
            variable_names = list(variables.keys())
        elif isinstance(variables, (list, tuple)):
            variable_names = list(variables)
        else:
            variable_names = []
        return [name for name in variable_names if name not in result_variables]

    @staticmethod
    def _read_correlation_value(matrix, row_var, col_var):
        if not isinstance(matrix, dict):
            return 0.0
        row_data = matrix.get(row_var, {})
        if not isinstance(row_data, dict):
            row_data = {}
        raw = row_data.get(col_var, None)
        if raw is None:
            reverse_row = matrix.get(col_var, {})
            if isinstance(reverse_row, dict):
                raw = reverse_row.get(row_var, 0.0)
            else:
                raw = 0.0
        try:
            return float(raw)
        except Exception:
            return 0.0

    @staticmethod
    def _format_matrix_number(value):
        return format(float(value), ".12g")

    def _build_correlation_matrix_html(self):
        input_variables = self._get_input_variable_names()
        if len(input_variables) < 2:
            return ""

        matrix = getattr(self.parent, 'correlation_coefficients', {})
        has_non_default_off_diagonal = False

        for row_index, row_var in enumerate(input_variables):
            for col_index, col_var in enumerate(input_variables):
                if row_index == col_index:
                    continue
                value = self._read_correlation_value(matrix, row_var, col_var)
                if not np.isclose(value, 0.0):
                    has_non_default_off_diagonal = True
                    break
            if has_non_default_off_diagonal:
                break

        if not has_non_default_off_diagonal:
            return ""

        table_rows = [[self._build_cell_html("", "th")] + [self._build_variable_cell_html(var, "th") for var in input_variables]]
        for row_index, row_var in enumerate(input_variables):
            row_cells = [self._build_variable_cell_html(row_var, "th")]
            for col_index, col_var in enumerate(input_variables):
                if row_index == col_index:
                    value = 1.0
                else:
                    value = self._read_correlation_value(matrix, row_var, col_var)
                row_cells.append(self._build_cell_html(self._format_matrix_number(value)))
            table_rows.append(row_cells)

        return (
            f'<div class="subtitle">{self.tr(CORRELATION_MATRIX_INPUT)}</div>'
            f"{self._render_three_line_table(table_rows, header_row_indexes={0})}"
        )

    def generate_report_html(self, equation):
        """Build report HTML content."""
        try:
            result_var = self.result_combo.currentText()
            if not result_var or not equation:
                return ""

            document_info = getattr(self.parent, 'document_info', {}) or {}
            if hasattr(self.parent, 'document_info_tab'):
                document_info = self.parent.document_info_tab.get_document_info()

            doc_number = html_lib.escape(document_info.get('document_number', ''))
            doc_name = html_lib.escape(document_info.get('document_name', ''))
            version_info = html_lib.escape(document_info.get('version_info', ''))
            description_html = document_info.get('description_html', '') or ""
            description_display = description_html if description_html.strip() else "-"
            revision_rows = self.get_revision_rows(document_info)
            report_css = self._get_report_css()
            model_equation = self._get_model_equation_text() or equation
            doc_table_html = self._render_three_line_table(
                [
                    [self._build_cell_html(self.tr(DOCUMENT_NUMBER), "th"), self._build_cell_html(doc_number or "-")],
                    [self._build_cell_html(self.tr(DOCUMENT_NAME), "th"), self._build_cell_html(doc_name or "-")],
                    [self._build_cell_html(self.tr(VERSION_INFO), "th"), self._build_cell_html(version_info or "-")],
                ],
                table_classes="three-line doc-table",
            )

            html = textwrap.dedent(f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{self.tr(REPORT_TITLE_HTML)}</title>
                    <style>
{report_css}
                    </style>
                </head>
                <body>
                <div class="container">
                    <div class="title">{self.tr(REPORT_DOCUMENT_INFO)}</div>
                    {doc_table_html}
                    <div class="subtitle">{self.tr(DESCRIPTION_LABEL)}</div>
                    <div class="description-body">{description_display}</div>
                    <div class="title">{self.tr(REPORT_MODEL_EQUATION)}</div>
                    <div class="equation">{self.equation_formatter.format_equation(model_equation)}</div>
                """).strip()

            html += self._build_correlation_matrix_html()

            # 螟画焚荳隕ｧ繝・・繝悶Ν
            variable_table_rows = [[
                self._build_cell_html(self.tr(REPORT_QUANTITY), "th"),
                self._build_cell_html(self.tr(REPORT_UNIT), "th"),
                self._build_cell_html(self.tr(REPORT_DEFINITION), "th"),
                self._build_cell_html(self.tr(REPORT_UNCERTAINTY_TYPE), "th"),
            ]]
            variables = getattr(self.parent, 'variables', [])
            # variables 縺ｯ繝ｪ繧ｹ繝医∪縺溘・霎樊嶌繧呈Φ螳壹☆繧九′縲√←縺｡繧峨〒繧ょｮ牙・縺ｫ謇ｱ縺医ｋ繧医≧豁｣隕丞喧
            if isinstance(variables, dict):
                variable_names = list(variables.keys())
            elif isinstance(variables, (list, tuple)):
                variable_names = list(variables)
            else:
                variable_names = []

            variable_values = getattr(self.parent, 'variable_values', {})
            if not isinstance(variable_values, dict):
                variable_values = {}

            def get_variable_data(name):
                data = variable_values.get(name, {})
                return data if isinstance(data, dict) else {}

            for var_name in variable_names:
                var_data = get_variable_data(var_name)
                unit = var_data.get('unit', '') or self.UNIT_PLACEHOLDER
                definition = self._format_markdown_inline_or_placeholder(var_data.get('definition', ''))
                uncertainty_type = self.get_uncertainty_type_display(var_data.get('type', ''), var_name)
                safe_unit = html_lib.escape(str(unit))
                variable_table_rows.append([
                    self._build_variable_cell_html(var_name),
                    f"<td>{safe_unit}</td>",
                    f"<td>{definition}</td>",
                    f"<td>{uncertainty_type}</td>",
                ])
            html += f'<div class="title">{self.tr(REPORT_VARIABLE_LIST)}</div>'
            html += self._render_three_line_table(variable_table_rows, header_row_indexes={0})

            # 蝗槫ｸｰ繝｢繝・Ν荳隕ｧ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ
            point_names = getattr(self.parent, 'value_names', [])
            calc_tab = getattr(self.parent, 'uncertainty_calculation_tab', None)
            if calc_tab and hasattr(calc_tab, 'result_combo'):
                result_index = calc_tab.result_combo.findText(result_var)
                if result_index >= 0:
                    if hasattr(calc_tab.result_combo, 'blockSignals'):
                        calc_tab.result_combo.blockSignals(True)
                    calc_tab.result_combo.setCurrentIndex(result_index)
                    if hasattr(calc_tab.result_combo, 'blockSignals'):
                        calc_tab.result_combo.blockSignals(False)
                if hasattr(calc_tab, 'on_result_changed'):
                    calc_tab.on_result_changed(result_var)

            original_point_index = getattr(self.parent, 'current_value_index', 0)
            original_calc_point_index = None
            original_calc_combo_index = None
            if calc_tab and hasattr(calc_tab, 'value_handler'):
                original_calc_point_index = calc_tab.value_handler.current_value_index
            if calc_tab and hasattr(calc_tab, 'value_combo') and hasattr(calc_tab.value_combo, 'currentIndex'):
                original_calc_combo_index = calc_tab.value_combo.currentIndex()

            for idx, point_name in enumerate(point_names):
                self.value_handler.current_value_index = idx
                html += f'<div class="title">{self.tr(REPORT_CALIBRATION_POINT)}: {point_name}</div>'

                # 蜷・､画焚縺ｮ隧ｳ邏ｰ
                for var_name in variable_names:
                    if var_name in self.parent.result_variables:
                        continue
                    try:
                        var_data = get_variable_data(var_name)
                        html += f"<div><strong>{self._format_variable_name_html(var_name)}</strong></div>"
                        uncertainty_type = var_data.get('type', '')
                        values_list = var_data.get('values', [])
                        if not isinstance(values_list, list):
                            values_list = []
                        value_item = values_list[idx] if idx < len(values_list) else None
                        if not isinstance(value_item, dict):
                            value_item = {}

                        unit = self._to_display_text(var_data.get('unit', ''), self.UNIT_PLACEHOLDER)
                        central_value = self._to_display_text(value_item.get('central_value', '-'))
                        central_with_unit = f"{html_lib.escape(central_value)} {html_lib.escape(unit)}"

                        if uncertainty_type == 'A':
                            standard_uncertainty = self._to_display_text(value_item.get('standard_uncertainty', '-'))
                            degrees_of_freedom = self._to_display_text(value_item.get('degrees_of_freedom', '-'))
                            html += self._format_two_row_table(
                                [self.tr(REPORT_CENTRAL_VALUE), self.tr(REPORT_UNIT), self.tr(REPORT_STANDARD_UNCERTAINTY), self.tr(REPORT_DOF)],
                                [central_value, unit, standard_uncertainty, degrees_of_freedom],
                            )
                            html += self._format_measurements_table(value_item.get('measurements', ''))
                            html += self._format_description_block(value_item.get('description', ''))
                        elif uncertainty_type == 'B':
                            half_width = self._to_display_text(value_item.get('half_width', '-'))
                            distribution = var_data.get('distribution', '')
                            distribution_key = get_distribution_translation_key(distribution)
                            distribution_label = self.tr(distribution_key) if distribution_key else self._to_display_text(distribution, '-')
                            divisor = self._to_display_text(value_item.get('divisor', var_data.get('divisor', '-')))
                            degrees_of_freedom = self._to_display_text(value_item.get('degrees_of_freedom', '-'))
                            html += self._format_two_row_table(
                                [self.tr(REPORT_CENTRAL_VALUE), self.tr(REPORT_UNIT), self.tr(HALF_WIDTH), self.tr(REPORT_DISTRIBUTION), self.tr(DIVISOR), self.tr(REPORT_DOF)],
                                [central_value, unit, half_width, distribution_label, divisor, degrees_of_freedom],
                            )
                            html += self._format_description_block(value_item.get('description', ''))
                        elif uncertainty_type == 'fixed':
                            html += self._format_two_row_table(
                                [self.tr(REPORT_CENTRAL_VALUE), self.tr(REPORT_UNIT)],
                                [central_value, unit],
                            )
                            html += self._format_description_block(value_item.get('description', ''))
                        else:
                            html += "<div>-</div>"
                    except Exception:
                        html += f"<div>-</div>"

                # 荳咲｢ｺ縺九＆縺ｮ繝舌ず繧ｧ繝・ヨ・郁ｨ育ｮ励ち繝悶°繧牙叙蠕暦ｼ・
                html += f'<h4>{self.tr(REPORT_UNCERTAINTY_BUDGET)}</h4>'
                if calc_tab:
                    if hasattr(calc_tab, 'value_handler'):
                        calc_tab.value_handler.current_value_index = idx
                    if hasattr(calc_tab, 'calculate_sensitivity_coefficients'):
                        calc_tab.calculate_sensitivity_coefficients(equation)
                    elif hasattr(calc_tab, 'value_combo'):
                        if hasattr(calc_tab.value_combo, 'setCurrentIndex'):
                            calc_tab.value_combo.setCurrentIndex(idx)
                        if hasattr(calc_tab, 'on_value_changed'):
                            calc_tab.on_value_changed(idx)
                    budget = []
                    for i in range(calc_tab.calibration_table.rowCount()):
                        variable_name = calc_tab.calibration_table.item(i, 0).text() if calc_tab.calibration_table.item(i, 0) else '-'
                        unit = self._get_unit(variable_name)
                        budget.append({
                            'variable': variable_name,
                            'central_value': self._format_with_unit(
                                calc_tab.calibration_table.item(i, 1).text() if calc_tab.calibration_table.item(i, 1) else '-',
                                unit,
                            ),
                            'standard_uncertainty': self._format_with_unit(
                                calc_tab.calibration_table.item(i, 2).text() if calc_tab.calibration_table.item(i, 2) else '-',
                                unit,
                            ),
                            'dof': calc_tab.calibration_table.item(i, 3).text() if calc_tab.calibration_table.item(i, 3) else '-',
                            'distribution': (
                                self.tr(get_distribution_translation_key(self.value_handler.get_distribution(variable_name)))
                                if variable_name
                                else '-'
                            ) or '-',
                            'sensitivity': calc_tab.calibration_table.item(i, 5).text() if calc_tab.calibration_table.item(i, 5) else '-',
                            'contribution': calc_tab.calibration_table.item(i, 6).text() if calc_tab.calibration_table.item(i, 6) else '-',
                            'contribution_rate': calc_tab.calibration_table.item(i, 7).text() if calc_tab.calibration_table.item(i, 7) else '-'
                        })
                    if budget:
                        budget_rows = [[
                            self._build_cell_html(self.tr(REPORT_FACTOR), "th"),
                            self._build_cell_html(self.tr(REPORT_CENTRAL_VALUE), "th"),
                            self._build_cell_html(self.tr(REPORT_STANDARD_UNCERTAINTY), "th"),
                            self._build_cell_html(self.tr(REPORT_DOF), "th"),
                            self._build_cell_html(self.tr(REPORT_DISTRIBUTION), "th"),
                            self._build_cell_html(self.tr(REPORT_SENSITIVITY), "th"),
                            self._build_cell_html(self.tr(REPORT_CONTRIBUTION), "th"),
                            self._build_cell_html(self.tr(REPORT_CONTRIBUTION_RATE), "th"),
                        ]]
                        for item in budget:
                            budget_rows.append([
                                self._build_variable_cell_html(item['variable']),
                                self._build_cell_html(item['central_value']),
                                self._build_cell_html(item['standard_uncertainty']),
                                self._build_cell_html(item['dof']),
                                self._build_cell_html(item['distribution']),
                                self._build_cell_html(item['sensitivity']),
                                self._build_cell_html(item['contribution']),
                                self._build_cell_html(item['contribution_rate']),
                            ])
                        html += self._render_three_line_table(budget_rows, header_row_indexes={0})

                    # 險育ｮ礼ｵ先棡
                    html += f"<h4>{self.tr(REPORT_CALCULATION_RESULT)}</h4>"
                    result_rows = [
                        [self._build_cell_html(self.tr(REPORT_ITEM), "th"), self._build_cell_html(self.tr(REPORT_VALUE), "th")],
                        [self._build_cell_html(self.tr(REPORT_EQUATION)), f"<td>{self.equation_formatter.format_equation(equation)}</td>"],
                        [self._build_cell_html(self.tr(REPORT_CENTRAL_VALUE)), self._build_cell_html(calc_tab.central_value_label.text())],
                        [self._build_cell_html(self.tr(REPORT_COMBINED_UNCERTAINTY)), self._build_cell_html(calc_tab.standard_uncertainty_label.text())],
                        [self._build_cell_html(self.tr(REPORT_EFFECTIVE_DOF)), self._build_cell_html(calc_tab.effective_degrees_of_freedom_label.text())],
                        [self._build_cell_html(self.tr(REPORT_COVERAGE_FACTOR)), self._build_cell_html(calc_tab.coverage_factor_label.text())],
                        [self._build_cell_html(self.tr(REPORT_EXPANDED_UNCERTAINTY)), self._build_cell_html(calc_tab.expanded_uncertainty_label.text())],
                    ]
                    html += self._render_three_line_table(result_rows, header_row_indexes={0})

            self.value_handler.current_value_index = original_point_index
            if calc_tab and hasattr(calc_tab, 'value_handler') and original_calc_point_index is not None:
                calc_tab.value_handler.current_value_index = original_calc_point_index
            if hasattr(self.parent, 'current_value_index'):
                self.parent.current_value_index = original_point_index
            if calc_tab and hasattr(calc_tab, 'value_combo') and original_calc_combo_index is not None:
                if hasattr(calc_tab.value_combo, 'blockSignals'):
                    calc_tab.value_combo.blockSignals(True)
                calc_tab.value_combo.setCurrentIndex(original_calc_combo_index)
                if hasattr(calc_tab.value_combo, 'blockSignals'):
                    calc_tab.value_combo.blockSignals(False)
            if calc_tab and hasattr(calc_tab, 'calculate_sensitivity_coefficients'):
                calc_tab.calculate_sensitivity_coefficients(equation)

            html += f'<div class="title">{self.tr(REPORT_REVISION_HISTORY)}</div>'
            revision_table_rows = [[
                self._build_cell_html(self.tr(REVISION_VERSION), "th"),
                self._build_cell_html(self.tr(REVISION_DESCRIPTION), "th"),
                self._build_cell_html(self.tr(REVISION_AUTHOR), "th"),
                self._build_cell_html(self.tr(REVISION_CHECKER), "th"),
                self._build_cell_html(self.tr(REVISION_APPROVER), "th"),
                self._build_cell_html(self.tr(REVISION_DATE), "th"),
            ]]
            if revision_rows:
                for row in revision_rows:
                    revision_table_rows.append([
                        self._build_cell_html(row.get('version', '') or '-'),
                        self._build_cell_html(row.get('description', '') or '-'),
                        self._build_cell_html(row.get('author', '') or '-'),
                        self._build_cell_html(row.get('checker', '') or '-'),
                        self._build_cell_html(row.get('approver', '') or '-'),
                        self._build_cell_html(row.get('date', '') or '-'),
                    ])
            else:
                revision_table_rows.append([f"<td colspan=\"6\">-</td>"])
            html += self._render_three_line_table(
                revision_table_rows,
                header_row_indexes={0},
                table_classes="three-line revision-table",
            )

            html += """
            </div>
            </body>
            </html>
            """
            return html

        except Exception as e:
            log_error(f"HTML逕滓・繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            return self.tr(HTML_GENERATION_ERROR)

    def get_revision_rows(self, document_info):
        """Get parsed revision rows."""
        if hasattr(self.parent, 'document_info_tab'):
            return self.parent.document_info_tab.parse_revision_history()
        if isinstance(document_info, dict):
            return self.parse_revision_history_text(document_info.get('revision_history', ''))
        return []

    def parse_revision_history_text(self, text):
        rows = []
        reader = csv.reader(io.StringIO(text or ""))
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            version, description, author, checker, approver, date = (
                row + ["", "", "", "", "", ""]
            )[:6]
            rows.append({
                'version': version.strip(),
                'description': description.strip(),
                'author': author.strip(),
                'checker': checker.strip(),
                'approver': approver.strip(),
                'date': date.strip()
            })
        return rows

    def update_report(self):
        """Refresh report when selection is available."""
        if self.result_combo.count() > 0:
            self.generate_report()
        else:
            self._last_generated_html = ""
            self.report_display.clear()

    def save_html_to_file(self, html, file_name):
        """Save report HTML to file."""
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)

            QMessageBox.information(self, self.tr(SAVE_SUCCESS), self.tr(REPORT_SAVED))
        except Exception as e:
            log_error(f"繝輔ぃ繧､繝ｫ菫晏ｭ倥お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            QMessageBox.warning(self, self.tr(SAVE_ERROR), self.tr(FILE_SAVE_ERROR))

    def get_uncertainty_type_display(self, type_code, var_name=None):
        """Convert uncertainty type code to display text."""
        # 險育ｮ礼ｵ先棡螟画焚縺ｮ蝣ｴ蜷医・縲瑚ｨ育ｮ礼ｵ先棡縲阪→陦ｨ遉ｺ
        if var_name and hasattr(self.parent, 'result_variables') and var_name in self.parent.result_variables:
            return self.tr(CALCULATION_RESULT_DISPLAY)
            
        type_map = {
            'A': self.tr(TYPE_A_DISPLAY),
            'B': self.tr(TYPE_B_DISPLAY),
            'fixed': self.tr(FIXED_VALUE_DISPLAY),
        }
        return type_map.get(type_code, self.tr(UNKNOWN_TYPE))

    def save_report(self):
        """Save current report HTML."""
        html = self._last_generated_html or self.report_display.toHtml()
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr(SAVE_REPORT_DIALOG_TITLE), "", "HTML File (*.html);;All Files (*)")
        if file_name:
            self.save_html_to_file(html, file_name)
