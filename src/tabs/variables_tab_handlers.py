from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
import traceback
from ..utils.app_logger import log_error
from ..utils.variable_utils import (
    calculate_type_a_uncertainty,
    calculate_type_b_uncertainty,
    get_distribution_divisor,
    create_empty_value_dict,
    find_variable_item
)
from ..utils.translation_keys import NORMAL_DISTRIBUTION
from ..utils.calculation_utils import evaluate_formula

class VariablesTabHandlers:
    """量管理/量の値管理タブのイベントハンドラ"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_variable = None
        self.last_selected_variable = None
        self.last_selected_value_index = 0
        self.current_variable_is_result = False

    def update_widget_visibility(self, uncertainty_type):
        """不確かさ種類や計算結果量に応じてウィジェットの表示と有効・無効を切り替える"""
        is_result = self.current_variable_is_result

        # 計算結果変数は種類選択を無効化する
        # 値のソースを取得
        for radio in [self.parent.type_a_radio, self.parent.type_b_radio, self.parent.type_fixed_radio]:
            radio.setEnabled(not is_result)
        if hasattr(self.parent, 'value_source_combo'):
            self.parent.value_source_combo.setEnabled(not is_result)

        if is_result:
            # 結果変数では入力系をすべて非表示・無効にする
            for widget in self.parent.type_a_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.type_b_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.fixed_value_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            self.parent.update_form_layout()
            return

        if uncertainty_type == 'A':
            # TypeA用のウィジェットを表示・有効化
            for widget in self.parent.type_a_widgets.values():
                widget.setVisible(True)
                widget.setEnabled(True)
            # TypeB用のウィジェットを非表示・無効化
            for widget in self.parent.type_b_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            # 固定値用のウィジェットを非表示・無効化
            for widget in self.parent.fixed_value_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)

        elif uncertainty_type == 'B':
            # TypeA用のウィジェットを非表示・無効化
            for widget in self.parent.type_a_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            # TypeB用のウィジェットを表示・有効化
            for widget in self.parent.type_b_widgets.values():
                widget.setVisible(True)
                widget.setEnabled(True)
            # 固定値用のウィジェットを非表示・無効化
            for widget in self.parent.fixed_value_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)

        # 回帰式の場合はupdate_widget_visibility_for_sourceで処理されるため、ここでは処理しない

        else:  # fixed
            # TypeA用のウィジェットを非表示・無効化
            for widget in self.parent.type_a_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            # TypeB用のウィジェットを非表示・無効化
            for widget in self.parent.type_b_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            # 固定値用のウィジェットを表示・有効化
            for widget in self.parent.fixed_value_widgets.values():
                widget.setVisible(True)
                widget.setEnabled(True)
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)

        show_half_width = (not is_result) and uncertainty_type == 'B'
        if hasattr(self.parent, 'half_width_label'):
            self.parent.half_width_label.setVisible(show_half_width)
            self.parent.half_width_label.setEnabled(show_half_width)

        self.parent.update_form_layout()

    def on_value_selected(self, index):
        """値が選択された時の処理"""
        if index < 0:
            return

        try:
            if not self.current_variable:
                return

            # 親クラスの現在の値インデックスを更新
            self.parent.parent.current_value_index = index
            self.last_selected_value_index = index  # 選択状態を保存

            # 現在の値の情報を表示
            self.parent.display_current_value()

        except Exception as e:
            log_error(f"値選択エラー: {str(e)}", details=traceback.format_exc())

    def on_variable_selected(self, current, previous):
        """量が選択された時の処理"""
        try:
            if current is None:
                self.parent.settings_group.setEnabled(False)
                self.parent.mode_display.setText("未選択")
                return
                
            var_name = current.data(Qt.UserRole)
            self.current_variable = var_name
            self.last_selected_variable = var_name  # 選択状態を保存
            is_result = var_name in self.parent.parent.result_variables
            self.current_variable_is_result = is_result
            var_mode = "計算結果" if is_result else "入力量"
            self.parent.mode_display.setText(var_mode)

            self.parent.settings_group.setEnabled(True)

            # 量辞書の初期化
            self.parent.parent.ensure_variable_initialized(var_name, is_result=is_result)

            # 値の選択コンボボックスのシグナルを一時的に切断
            self.parent.value_combo.blockSignals(True)
            
            # 値の選択コンボボックスを更新（校正点設定タブの情報を参照）
            self.parent.update_value_combo()

            # 現在選択されている値のインデックスを設定
            target_index = self.parent.parent.current_value_index
            if target_index < 0 or target_index >= self.parent.value_combo.count():
                target_index = 0

            self.parent.parent.current_value_index = target_index
            self.last_selected_value_index = target_index
            self.parent.value_combo.setCurrentIndex(target_index)

            # 値の選択コンボボックスのシグナルを再接続
            self.parent.value_combo.blockSignals(False)

            # 計算結果変数はタイプ選択を無効化し、タイプを結果用に固定
            if is_result:
                self.parent.parent.variable_values[var_name]['type'] = 'result'

            # 共通の設定を表示
            self.parent.display_common_settings()

            # 現在の値の情報を表示
            self.parent.display_current_value()

        except Exception as e:
            log_error(f"量選択エラー: {str(e)}", details=traceback.format_exc())

    def on_type_changed(self, checked):
        """不確かさ種類が変更されたときの処理"""
        if not checked:
            return

        try:
            if self.current_variable_is_result:
                return
            # 値のソースが回帰式の場合は変更を無視
            if self.parent.type_a_radio.isChecked():
                uncertainty_type = 'A'

            elif self.parent.type_b_radio.isChecked():
                uncertainty_type = 'B'

            else:  # 固定値
                uncertainty_type = 'fixed'
            self.update_widget_visibility(uncertainty_type)

            if self.current_variable:
                # 量の不確かさ種類を更新
                self.parent.parent.variable_values[self.current_variable]['type'] = uncertainty_type

            # フォームレイアウトの更新
            self.parent.update_form_layout()
            
        except Exception as e:
            log_error(f"不確かさ種類変更エラー: {str(e)}", details=traceback.format_exc())

    def on_value_source_changed(self, index):
        """値のソース変更時の処理"""
        try:
            if self.current_variable_is_result:
                return
            if not self.current_variable:
                return

            source = 'manual'
            value_info = self._get_current_value_info()
            value_info['source'] = source

            if source == 'regression':
                # 回帰式の場合、回帰モデル関連のウィジェットを表示
                self.parent.update_regression_model_options()
                # 既存の値を復元
                regression_id = value_info.get('regression_id', '')
                if regression_id:
                    model_index = self.parent.regression_widgets['model'].findText(regression_id)
                    if model_index >= 0:
                        self.parent.regression_widgets['model'].setCurrentIndex(model_index)
                
                regression_x_mode = value_info.get('regression_x_mode', 'fixed')
                x_mode_index = self.parent.regression_widgets['x_mode'].findData(regression_x_mode)
                if x_mode_index >= 0:
                    self.parent.regression_widgets['x_mode'].setCurrentIndex(x_mode_index)
                
                # 不確かさ種類のラジオボタンを無効化
                for radio in [self.parent.type_a_radio, self.parent.type_b_radio, self.parent.type_fixed_radio]:
                    radio.setEnabled(False)
            else:
                # 手入力の場合、不確かさ種類のラジオボタンを有効化
                for radio in [self.parent.type_a_radio, self.parent.type_b_radio, self.parent.type_fixed_radio]:
                    radio.setEnabled(True)
                # 現在の不確かさ種類に応じてウィジェットを表示
                var_info = self.parent.parent.variable_values[self.current_variable]
                uncertainty_type = var_info.get('type', 'A')
                self.update_widget_visibility(uncertainty_type)

            self.update_widget_visibility_for_source(source)
            self.parent.update_form_layout()
        except Exception as e:
            log_error(f"値のソース変更エラー: {str(e)}", details=traceback.format_exc())

    def update_widget_visibility_for_source(self, source):
        """値のソースに応じてウィジェットの表示を更新"""
        if source == 'regression':
            # 回帰式の場合、回帰モデル関連のウィジェットを表示
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(True)
                widget.setEnabled(True)
            # TypeA/B/Fixedのウィジェットを非表示
            for widget in self.parent.type_a_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.type_b_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
            for widget in self.parent.fixed_value_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)
        else:
            # 手入力の場合、回帰モデル関連のウィジェットを非表示
            for widget in self.parent.regression_widgets.values():
                widget.setVisible(False)
                widget.setEnabled(False)

    def on_regression_model_changed(self):
        """回帰モデル選択変更"""
        try:
            if not self.current_variable:
                return
            value_info = self._get_current_value_info()
            model_name = self.parent.regression_widgets['model'].currentText()
            value_info['regression_id'] = model_name
            value_info['regression_model'] = model_name  # 後方互換性のため
        except Exception as e:
            log_error(f"回帰モデル選択エラー: {str(e)}", details=traceback.format_exc())

    def on_regression_x_mode_changed(self, index):
        """回帰モデルのxの取り方変更"""
        try:
            if not self.current_variable:
                return
            value_info = self._get_current_value_info()
            x_mode = self.parent.regression_widgets['x_mode'].currentData() or 'fixed'
            value_info['regression_x_mode'] = x_mode
            
            # xの取り方に応じてx_valueの表示を更新
            if x_mode == 'point_name':
                # 校正点名を数値として使う場合
                point_name = self.parent.value_combo.currentText()
                try:
                    point_value = float(point_name)
                    self.parent.regression_widgets['x_value'].setText(str(point_value))
                    self.parent.regression_widgets['x_value'].setReadOnly(True)
                except ValueError:
                    self.parent.regression_widgets['x_value'].setText('')
                    self.parent.regression_widgets['x_value'].setReadOnly(True)
            elif x_mode == 'fixed':
                # 固定値を指定する場合
                self.parent.regression_widgets['x_value'].setReadOnly(False)
                regression_x_value = value_info.get('regression_x_value', '')
                if regression_x_value:
                    self.parent.regression_widgets['x_value'].setText(str(regression_x_value))
        except Exception as e:
            log_error(f"回帰モデルxの取り方変更エラー: {str(e)}", details=traceback.format_exc())

    def on_regression_x_value_changed(self):
        """回帰モデルのx値入力変更"""
        try:
            if not self.current_variable:
                return
            value_info = self._get_current_value_info()
            x_value = self.parent.regression_widgets['x_value'].text()
            value_info['regression_x_value'] = x_value
            value_info['regression_x'] = x_value  # 後方互換性のため
        except Exception as e:
            log_error(f"回帰モデルx値変更エラー: {str(e)}", details=traceback.format_exc())

    def _get_current_value_info(self):
        """現在の値辞書を取得"""
        var_info = self.parent.parent.variable_values.get(self.current_variable, {})
        values = var_info.get('values', [])
        if not isinstance(values, list):
            values = []
        while len(values) <= self.parent.value_combo.currentIndex():
            values.append(create_empty_value_dict())
        var_info['values'] = values
        self.parent.parent.variable_values[self.current_variable] = var_info
        return values[self.parent.value_combo.currentIndex()]

    def on_unit_changed(self):
        """単位が変更されたときの処理"""
        try:
            if self.current_variable:
                self.parent.parent.variable_values[self.current_variable]['unit'] = self.parent.unit_input.text()
        except Exception as e:
            log_error(f"単位変更エラー: {str(e)}", details=traceback.format_exc())

    def on_definition_changed(self):
        """定義が変更されたときの処理"""
        try:
            if self.current_variable:
                self.parent.parent.variable_values[self.current_variable]['definition'] = self.parent.definition_input.toPlainText()
        except Exception as e:
            log_error(f"定義変更エラー: {str(e)}", details=traceback.format_exc())

    def on_measurements_focus_lost(self, event):
        """測定値入力からフォーカスが外れたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            measurements_str = self.parent.type_a_widgets['measurements'].text().strip()
            if not measurements_str:
                return
                
            # TypeA不確かさの計算
            degrees_of_freedom, central_value, standard_uncertainty, measurements_str = calculate_type_a_uncertainty(measurements_str)
            
            if degrees_of_freedom is not None:
                # 結果を表示
                self.parent.type_a_widgets['degrees_of_freedom'].setText(str(degrees_of_freedom))
                self.parent.type_a_widgets['central_value'].setText(f"{central_value:.15g}")
                self.parent.type_a_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.15g}")
                
                # データを保存
                index = self.parent.value_combo.currentIndex()
                if 'values' in self.parent.parent.variable_values[self.current_variable]:
                    self.parent.parent.variable_values[self.current_variable]['values'][index].update({
                        'measurements': measurements_str,
                        'degrees_of_freedom': degrees_of_freedom,
                        'central_value': central_value,
                        'standard_uncertainty': standard_uncertainty
                    })
            
        except Exception as e:
            log_error(f"測定値計算エラー: {str(e)}", details=traceback.format_exc())

    def on_distribution_changed(self, index):
        """分布の種類が変更されたときの処理"""
        try:
            if not self.current_variable:
                return

            distribution = self.parent.type_b_widgets['distribution'].currentData()
            if not distribution:
                distribution = NORMAL_DISTRIBUTION

            # 分布の種類に応じて除数を設定
            default_divisor = get_distribution_divisor(distribution)
            divisor = ''
            value_index = self.parent.value_combo.currentIndex()
            if self.current_variable:
                var_info = self.parent.parent.variable_values.get(self.current_variable, {})
                if isinstance(var_info, dict):
                    values = var_info.get('values', [])
                    if isinstance(values, list) and 0 <= value_index < len(values):
                        divisor = values[value_index].get('divisor', '') or ''
                    if not divisor:
                        divisor = var_info.get('divisor', '') or ''

            if distribution == NORMAL_DISTRIBUTION:
                divisor = divisor or ''
            else:
                divisor = default_divisor

            self.parent.type_b_widgets['divisor'].setText(divisor)
            self.parent.type_b_widgets['divisor'].setReadOnly(distribution != NORMAL_DISTRIBUTION)

            degrees_of_freedom = self.parent.type_b_widgets['degrees_of_freedom'].text().strip()
            if degrees_of_freedom in {'', '0', '0.0'}:
                degrees_of_freedom = 'inf'
                self.parent.type_b_widgets['degrees_of_freedom'].setText(degrees_of_freedom)

            # 量の分布と除数を更新
            self.parent.parent.variable_values[self.current_variable]['distribution'] = distribution
            self.parent.parent.variable_values[self.current_variable]['divisor'] = divisor
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                try:
                    value_info = self.parent.parent.variable_values[self.current_variable]['values'][value_index]
                    value_info['divisor'] = divisor
                    if degrees_of_freedom:
                        value_info['degrees_of_freedom'] = degrees_of_freedom
                except (IndexError, TypeError):
                    pass

            # 半値幅が設定されている場合は標準不確かさを再計算
            half_width = self.parent.type_b_widgets['half_width'].text().strip()
            if half_width and divisor:
                half_width, standard_uncertainty = calculate_type_b_uncertainty(half_width, divisor)
                if standard_uncertainty is not None:
                    self.parent.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.15g}")
                    if 'values' in self.parent.parent.variable_values[self.current_variable]:
                        try:
                            value_info = self.parent.parent.variable_values[self.current_variable]['values'][value_index]
                            value_info['standard_uncertainty'] = standard_uncertainty
                        except (IndexError, TypeError):
                            pass
            
        except Exception as e:
            log_error(f"分布変更エラー: {str(e)}", details=traceback.format_exc())

    def on_half_width_focus_lost(self, event):
        """半値幅の入力欄からフォーカスが外れたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            # 半値幅と除数を取得
            half_width_str = self.parent.type_b_widgets['half_width'].text().strip()
            divisor_str = self.parent.type_b_widgets['divisor'].text().strip()
            
            # 分布に応じた除数を設定
            distribution = self.parent.type_b_widgets['distribution'].currentData()
            if not distribution:
                distribution = NORMAL_DISTRIBUTION
            if distribution != NORMAL_DISTRIBUTION:
                divisor_str = get_distribution_divisor(distribution)
                self.parent.type_b_widgets['divisor'].setText(divisor_str)
            
            # 標準不確かさを計算
            half_width, standard_uncertainty = calculate_type_b_uncertainty(half_width_str, divisor_str)
            
            if half_width is not None and standard_uncertainty is not None:
                # 値を保存
                value_index = self.parent.value_combo.currentIndex()
                if 'values' in self.parent.parent.variable_values[self.current_variable]:
                    self.parent.parent.variable_values[self.current_variable]['values'][value_index]['half_width'] = half_width
                    self.parent.parent.variable_values[self.current_variable]['values'][value_index]['divisor'] = divisor_str
                    self.parent.parent.variable_values[self.current_variable]['values'][value_index]['standard_uncertainty'] = standard_uncertainty

                # 標準不確かさを表示（高精度で表示）
                self.parent.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.15g}")
                
        except Exception as e:
            log_error(f"半値幅フォーカスロスエラー: {str(e)}", details=traceback.format_exc())

    def on_divisor_changed(self):
        """除数が変更されたときの処理"""
        try:
            if not self.current_variable:
                return
                
            divisor = self.parent.type_b_widgets['divisor'].text().strip()
            if not divisor:
                return
                
            # 量の除数を更新
            self.parent.parent.variable_values[self.current_variable]['divisor'] = divisor

            # 現在の値の半値幅が設定されている場合は標準不確かさを再計算
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                value_info = self.parent.parent.variable_values[self.current_variable]['values'][value_index]
                value_info['divisor'] = divisor
                half_width = value_info.get('half_width', '')
                
                if half_width:
                    try:
                        half_width = float(half_width)
                        divisor = float(divisor)
                        standard_uncertainty = half_width / divisor
                        self.parent.type_b_widgets['standard_uncertainty'].setText(f"{standard_uncertainty:.15g}")
                        value_info['standard_uncertainty'] = standard_uncertainty
                    except ValueError:
                        pass
            
        except Exception as e:
            log_error(f"除数変更エラー: {str(e)}", details=traceback.format_exc())

    def on_central_value_changed(self):
        """中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            central_value = self.parent.type_b_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['central_value'] = central_value
                
        except Exception as e:
            log_error(f"中央値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_fixed_value_changed(self):
        """固定値の中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            fixed_value = self.parent.fixed_value_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index].update({
                    'central_value': fixed_value  # 固定値も中央値として保存
                })
                
        except Exception as e:
            log_error(f"固定値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_degrees_of_freedom_changed(self):
        """自由度が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            degrees_of_freedom = self.parent.type_b_widgets['degrees_of_freedom'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['degrees_of_freedom'] = degrees_of_freedom
                
        except Exception as e:
            log_error(f"自由度変更エラー: {str(e)}", details=traceback.format_exc())

    def on_description_changed(self):
        """詳細説明が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            # 現在選択されている値のインデックスを取得
            index = self.parent.value_combo.currentIndex()
            
            # 現在の不確かさ種類を取得
            uncertainty_type = 'A'
            if self.parent.type_b_radio.isChecked():
                uncertainty_type = 'B'
            elif self.parent.type_fixed_radio.isChecked():
                uncertainty_type = 'fixed'
                
            # 不確かさ種類に応じた詳細説明を取得
            if uncertainty_type == 'A':
                description = self.parent.type_a_widgets['description'].toPlainText()
            elif uncertainty_type == 'B':
                description = self.parent.type_b_widgets['description'].toPlainText()
            else:  # fixed
                description = self.parent.fixed_value_widgets['description'].toPlainText()
                
            # 値の辞書を取得
            var_info = self.parent.parent.variable_values[self.current_variable]
            values = var_info.get('values', [])

            # インデックスが範囲外の場合、新しい値を追加
            while len(values) <= index:
                values.append(create_empty_value_dict())
                
            # 詳細説明を保存
            values[index]['description'] = description
            
        except Exception as e:
            log_error(f"詳細説明変更エラー: {str(e)}", details=traceback.format_exc())

    def on_calculation_formula_changed(self):
        """計算式が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            # 現在の不確かさ種類を取得
            uncertainty_type = 'A'
            if self.parent.type_b_radio.isChecked():
                uncertainty_type = 'B'
            
            # 計算式を取得
            calculation_formula = self.parent.type_b_widgets['calculation_formula'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['calculation_formula'] = calculation_formula
                
        except Exception as e:
            log_error(f"計算式変更エラー: {str(e)}", details=traceback.format_exc())

    def on_calculate_button_clicked(self):
        """計算ボタンがクリックされたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            # 現在の不確かさ種類を取得
            uncertainty_type = 'A'
            if self.parent.type_b_radio.isChecked():
                uncertainty_type = 'B'
            elif self.parent.type_fixed_radio.isChecked():
                uncertainty_type = 'fixed'
                
            # Type Bの場合のみ処理を行う
            if uncertainty_type != 'B':
                return
                
            # 計算式を取得
            calculation_formula = self.parent.type_b_widgets['calculation_formula'].text().strip()
            if not calculation_formula:
                return
                
            # 現在の校正点で利用可能な変数値を計算式へ渡す
            value_index = self.parent.value_combo.currentIndex()
            variables = {}
            for var_name, var_data in self.parent.parent.variable_values.items():
                if not isinstance(var_data, dict):
                    continue
                values = var_data.get('values', [])
                if not isinstance(values, list) or not (0 <= value_index < len(values)):
                    continue
                value_info = values[value_index]
                if not isinstance(value_info, dict):
                    continue
                central_value = value_info.get('central_value', '')
                if central_value in ('', None):
                    continue
                variables[var_name] = central_value

            # 計算式を評価
            result = evaluate_formula(calculation_formula, variables=variables)
            
            if result is not None:
                # 半値幅の入力欄に結果を設定
                self.parent.type_b_widgets['half_width'].setText(str(result))
                
                # 半値幅のフォーカスが外れたときの処理を呼び出す
                self.on_half_width_focus_lost(None)
                
                # 計算式を保存
                value_index = self.parent.value_combo.currentIndex()
                if 'values' in self.parent.parent.variable_values[self.current_variable]:
                    self.parent.parent.variable_values[self.current_variable]['values'][value_index]['calculation_formula'] = calculation_formula
                
        except Exception as e:
            log_error(f"計算ボタンクリックエラー: {str(e)}", details=traceback.format_exc())

    def on_measurements_changed(self):
        """測定値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            measurements = self.parent.type_a_widgets['measurements'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['measurements'] = measurements
                
        except Exception as e:
            log_error(f"測定値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_a_degrees_of_freedom_changed(self):
        """TypeAの自由度が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            degrees_of_freedom = self.parent.type_a_widgets['degrees_of_freedom'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['degrees_of_freedom'] = degrees_of_freedom
                
        except Exception as e:
            log_error(f"TypeA自由度変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_a_central_value_changed(self):
        """TypeAの中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            central_value = self.parent.type_a_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['central_value'] = central_value
                
        except Exception as e:
            log_error(f"TypeA中央値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_a_standard_uncertainty_changed(self):
        """TypeAの標準不確かさが変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            standard_uncertainty = self.parent.type_a_widgets['standard_uncertainty'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['standard_uncertainty'] = standard_uncertainty
                
        except Exception as e:
            log_error(f"TypeA標準不確かさ変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_a_description_changed(self):
        """TypeAの詳細説明が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            description = self.parent.type_a_widgets['description'].toPlainText()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['description'] = description
                
        except Exception as e:
            log_error(f"TypeA詳細説明変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_b_degrees_of_freedom_changed(self):
        """TypeBの自由度が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            degrees_of_freedom = self.parent.type_b_widgets['degrees_of_freedom'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['degrees_of_freedom'] = degrees_of_freedom
                
        except Exception as e:
            log_error(f"TypeB自由度変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_b_central_value_changed(self):
        """TypeBの中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            central_value = self.parent.type_b_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['central_value'] = central_value
                
        except Exception as e:
            log_error(f"TypeB中央値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_b_half_width_changed(self):
        """TypeBの半値幅が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            half_width = self.parent.type_b_widgets['half_width'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['half_width'] = half_width
                
        except Exception as e:
            log_error(f"TypeB半値幅変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_b_standard_uncertainty_changed(self):
        """TypeBの標準不確かさが変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            standard_uncertainty = self.parent.type_b_widgets['standard_uncertainty'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['standard_uncertainty'] = standard_uncertainty
                
        except Exception as e:
            log_error(f"TypeB標準不確かさ変更エラー: {str(e)}", details=traceback.format_exc())

    def on_type_b_description_changed(self):
        """TypeBの詳細説明が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            description = self.parent.type_b_widgets['description'].toPlainText()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['description'] = description
                
        except Exception as e:
            log_error(f"TypeB詳細説明変更エラー: {str(e)}", details=traceback.format_exc())

    def on_fixed_value_central_value_changed(self):
        """固定値の中央値が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            central_value = self.parent.fixed_value_widgets['central_value'].text().strip()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index].update({
                    'central_value': central_value
                })
                
        except Exception as e:
            log_error(f"固定値中央値変更エラー: {str(e)}", details=traceback.format_exc())

    def on_fixed_value_description_changed(self):
        """固定値の詳細説明が変更されたときの処理"""
        try:
            if not self.current_variable or self.parent.value_combo.currentIndex() < 0:
                return
                
            description = self.parent.fixed_value_widgets['description'].toPlainText()
            
            # データを保存
            value_index = self.parent.value_combo.currentIndex()
            if 'values' in self.parent.parent.variable_values[self.current_variable]:
                self.parent.parent.variable_values[self.current_variable]['values'][value_index]['description'] = description
                
        except Exception as e:
            log_error(f"固定値詳細説明変更エラー: {str(e)}", details=traceback.format_exc())
