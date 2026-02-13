from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QGroupBox, QMessageBox, QLineEdit,
                           QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal, Slot
import sympy as sp
import re
import traceback
import json
import os

from src.utils.equation_formatter import EquationFormatter
from src.tabs.base_tab import BaseTab
from src.utils.translation_keys import *
from src.utils.equation_handler import EquationHandler
from src.utils.equation_normalizer import normalize_equation_text, normalize_variable_name
from src.utils.app_logger import log_debug, log_error

class DraggableListWidget(QListWidget):
    order_changed = Signal(list)  # 荳ｦ縺ｳ鬆・′螟画峩縺輔ｌ縺溘→縺阪↓逋ｺ轣ｫ縺吶ｋ繧ｷ繧ｰ繝翫Ν
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        # 譁ｰ縺励＞荳ｦ縺ｳ鬆・ｒ蜿門ｾ励＠縺ｦ繧ｷ繧ｰ繝翫Ν繧堤匱轣ｫ
        new_order = [self.item(i).text() for i in range(self.count())]
        self.order_changed.emit(new_order)

class ModelEquationTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.variable_order_file = os.path.join("data", "variable_order.json")

        self.setup_ui()

    def retranslate_ui(self):
        """UI縺ｮ繝・く繧ｹ繝医ｒ迴ｾ蝨ｨ縺ｮ險隱槭〒譖ｴ譁ｰ"""
        log_debug(f"[DEBUG] Retranslating UI for context: {self.metaObject().className()}")
        self.equation_group.setTitle(self.tr(MODEL_EQUATION_INPUT))
        self.equation_input.setPlaceholderText(self.tr(EQUATION_PLACEHOLDER))
        self.variable_group.setTitle(self.tr(VARIABLE_LIST_DRAG_DROP))
        self.display_group.setTitle(self.tr(HTML_DISPLAY))
        
    def setup_ui(self):
        """繝｡繧､繝ｳ繧ｦ繧｣繝ｳ繝峨え縺ｮ菴懈・縺ｨ陦ｨ遉ｺ"""

        layout = QVBoxLayout()
        
        # 繝｢繝・Ν譁ｹ遞句ｼ丞・蜉帙お繝ｪ繧｢
        self.equation_group = QGroupBox(self.tr(MODEL_EQUATION_INPUT))
        equation_layout = QVBoxLayout()
        
        self.equation_input = QTextEdit()
        self.equation_input.setPlaceholderText(self.tr(EQUATION_PLACEHOLDER))
        self.equation_input.setMaximumHeight(300)
        self.equation_input.focusOutEvent = self._on_equation_focus_lost
        equation_layout.addWidget(self.equation_input)
        
        self.equation_status = QLabel("")
        equation_layout.addWidget(self.equation_status)
        
        self.equation_group.setLayout(equation_layout)
        layout.addWidget(self.equation_group)
        
        # 螟画焚繝ｪ繧ｹ繝郁｡ｨ遉ｺ繧ｨ繝ｪ繧｢
        self.variable_group = QGroupBox(self.tr(VARIABLE_LIST_DRAG_DROP))
        variable_layout = QVBoxLayout()
        
        self.variable_list = DraggableListWidget(self)
        self.variable_list.order_changed.connect(self.on_variable_order_changed)
        variable_layout.addWidget(self.variable_list)
        
        self.variable_group.setLayout(variable_layout)
        layout.addWidget(self.variable_group)
        
        # HTML陦ｨ遉ｺ繧ｨ繝ｪ繧｢
        self.display_group = QGroupBox(self.tr(HTML_DISPLAY))
        display_layout = QVBoxLayout()
        
        self.html_display = QTextEdit()
        self.html_display.setReadOnly(True)
        self.html_display.setMaximumHeight(200)
        display_layout.addWidget(self.html_display)
        
        self.display_group.setLayout(display_layout)
        layout.addWidget(self.display_group)
        
        self.setLayout(layout)


    def on_variable_order_changed(self, new_order):
        """Handle variable order changes."""
        try:
            if not hasattr(self.parent, 'variables'):
                return

            input_vars = []
            result_vars = []
            for var in new_order:
                if var in self.parent.result_variables:
                    result_vars.append(var)
                else:
                    input_vars.append(var)

            self.parent.variables = result_vars + input_vars
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
        except Exception as e:
            log_error(f"螟画焚縺ｮ荳ｦ縺ｳ鬆・峩譁ｰ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            QMessageBox.warning(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_UPDATE_FAILED')}: {str(e)}")

    def save_variable_order(self):
        """Save variable order to JSON."""
        try:
            if not hasattr(self.parent, 'variables'):
                return

            os.makedirs(os.path.dirname(self.variable_order_file), exist_ok=True)
            with open(self.variable_order_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'variables': self.parent.variables,
                    'result_variables': self.parent.result_variables
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(f"螟画焚縺ｮ荳ｦ縺ｳ鬆・ｿ晏ｭ倥お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_SAVE_FAILED')}: {str(e)}")
            
    def load_variable_order(self):
        """螟画焚縺ｮ荳ｦ縺ｳ鬆・ｒJSON繝輔ぃ繧､繝ｫ縺九ｉ隱ｭ縺ｿ霎ｼ繧"""
        try:
            if not os.path.exists(self.variable_order_file):
                return
                
            with open(self.variable_order_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not hasattr(self.parent, 'variables'):
                return
                
            # 菫晏ｭ倥＆繧後◆荳ｦ縺ｳ鬆・ｒ驕ｩ逕ｨ
            self.parent.variables = data.get('variables', self.parent.variables)
            self.parent.result_variables = data.get('result_variables', self.parent.result_variables)
            
            # 螟画焚繧ｿ繝悶・譖ｴ譁ｰ
            if hasattr(self.parent, 'variables_tab'):
                self.parent.variables_tab.update_variable_list(
                    self.parent.variables,
                    self.parent.result_variables
                )
            
            # 螟画焚繝ｪ繧ｹ繝医・譖ｴ譁ｰ
            self.update_variable_list()
            

            
        except Exception as e:
            log_error(f"螟画焚縺ｮ荳ｦ縺ｳ鬆・ｪｭ縺ｿ霎ｼ縺ｿ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            QMessageBox.critical(self, self.tr(MESSAGE_ERROR), f"{self.tr('VARIABLE_ORDER_LOAD_FAILED')}: {str(e)}")
            
    def update_variable_list(self):
        """螟画焚繝ｪ繧ｹ繝医ｒ譖ｴ譁ｰ"""
        try:
            self.variable_list.clear()
            
            if hasattr(self.parent, 'variables'):
                for var in self.parent.variables:
                    item = QListWidgetItem(var)
                    self.variable_list.addItem(item)
                    

        except Exception as e:
            log_error(f"螟画焚繝ｪ繧ｹ繝域峩譁ｰ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            
    def _on_equation_focus_lost(self, event):
        """Handle focus out on equation input (internal)."""
        QTextEdit.focusOutEvent(self.equation_input, event)
        
        # 迴ｾ蝨ｨ縺ｮ譁ｹ遞句ｼ上ｒ蜿門ｾ・
        current_equation = self.equation_input.toPlainText().strip() 
        
        # 蜑榊屓縺ｮ譁ｹ遞句ｼ上→蜷後§蝣ｴ蜷医・菴輔ｂ縺励↑縺・
        if current_equation == self.parent.last_equation:
            return

        try:
            applied = self.check_equation_changes(current_equation)
            if not applied:
                self.update_html_display(self.parent.last_equation)
                return

            # 蛛丞ｾｮ蛻・ち繝悶・譖ｴ譁ｰ
            if hasattr(self.parent, 'partial_derivative_tab'):
                self.parent.partial_derivative_tab.update_equation_display()

            # 繝ｬ繝昴・繝医ち繝悶・譖ｴ譁ｰ・域眠隕剰ｿｽ蜉・・
            if hasattr(self.parent, 'report_tab'):
                self.parent.report_tab.update_report()

            # 荳咲｢ｺ縺九＆險育ｮ励ち繝悶・譖ｴ譁ｰ・域眠隕剰ｿｽ蜉・・
            if hasattr(self.parent, 'uncertainty_calculation_tab'):
                self.parent.uncertainty_calculation_tab.update_result_combo()
                self.parent.uncertainty_calculation_tab.update_value_combo()
                
        except Exception as e:
            log_error(f"譁ｹ遞句ｼ剰ｧ｣譫舌お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            self.equation_status.setText(f"繧ｨ繝ｩ繝ｼ: {str(e)}")
        
        # HTML陦ｨ遉ｺ繧貞ｿ・★譖ｴ譁ｰ
        self.update_html_display(self.parent.last_equation)
        
    def on_equation_focus_lost(self, event):
        """Handle focus out on equation input."""
        self._on_equation_focus_lost(event)
        
    def check_equation_changes(self, equation):
        """譁ｹ遞句ｼ上・螟画峩繧堤屮隕悶＠縲∝､画焚縺ｮ霑ｽ蜉繝ｻ蜑企勁繧呈､懷・"""
        try:
            log_debug(f"\n{'#'*80}")
            log_debug(f"#" + " " * 30 + "譁ｹ遞句ｼ丞､画峩繝√ぉ繝・け" + " " * 30 + "#")
            log_debug(f"{'#'*80}")
            log_debug(f"蜈･蜉帙＆繧後◆譁ｹ遞句ｼ・ '{equation}'")
            
            # 譁ｹ遞句ｼ上ｒ蛻・牡
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            new_vars = set()  # 蜈･蜉帛､画焚
            result_vars = set()  # 險育ｮ礼ｵ先棡螟画焚
            
            # 縺ｾ縺壼ｷｦ霎ｺ縺ｮ螟画焚繧貞庶髮・ｼ郁ｨ育ｮ礼ｵ先棡螟画焚・・

            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = self._normalize_variable_name(eq.split('=', 1)[0])
                result_vars.add(left_side)
                log_debug(f"  - 蟾ｦ霎ｺ縺九ｉ讀懷・: {left_side}")
            

            
            # 蜿ｳ霎ｺ縺九ｉ蜈･蜉帛､画焚繧呈､懷・

            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = self._normalize_variable_name(left_side)
                right_side = right_side.strip()
                log_debug(f"  譁ｹ遞句ｼ剰ｧ｣譫・ {left_side} = {right_side}")
                
                # 貍皮ｮ怜ｭ舌〒蠑上ｒ蛻・牡
                # 縺ｾ縺壽ｼ皮ｮ怜ｭ舌・蜑榊ｾ後↓繧ｹ繝壹・繧ｹ繧定ｿｽ蜉
                for op in ['+', '-', '*', '/', '^', '(', ')', ',']:
                    right_side = right_side.replace(op, f' {op} ')
                terms = right_side.split()
                
                # 蜷・・°繧牙､画焚繧呈歓蜃ｺ
                for term in terms:
                    # 貍皮ｮ怜ｭ舌〒縺ｪ縺・・・縺ｿ繧貞・逅・
                    if term not in ['+', '-', '*', '/', '^', '(', ')', ',']:
                        # 謨ｰ蛟､縺ｧ縺ｪ縺・・ｒ螟画焚縺ｨ縺励※謇ｱ縺・
                        try:
                            float(term)  # 謨ｰ蛟､縺九←縺・°繧偵メ繧ｧ繝・け
                        except ValueError:
                            normalized_term = self._normalize_variable_name(term)
                            if not normalized_term:
                                continue
                            if normalized_term not in result_vars:
                                new_vars.add(normalized_term)
                                log_debug(f"    竊・蜈･蜉帛､画焚縺ｨ縺励※霑ｽ蜉: {normalized_term}")
            



            
            # 螟画焚縺ｮ霑ｽ蜉繝ｻ蜑企勁繧呈､懷・
            all_vars = new_vars | result_vars
            current_vars = {self._normalize_variable_name(var) for var in self.parent.variables}
            added_vars = all_vars - current_vars
            removed_vars = current_vars - all_vars
            


            
            # 螟画焚縺ｮ蜑企勁縺後≠繧句ｴ蜷医・遒ｺ隱阪ム繧､繧｢繝ｭ繧ｰ繧定｡ｨ遉ｺ
            if removed_vars:

                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("変数の変更確認")

                message = "モデル式の変更により、以下の変数の変更が必要です:\n\n"

                if added_vars:
                    added_inputs = added_vars & new_vars
                    added_results = added_vars & result_vars
                    if added_inputs:
                        message += f"追加される入力変数: {', '.join(sorted(added_inputs))}\n"
                    if added_results:
                        message += f"追加される計算結果: {', '.join(sorted(added_results))}\n"

                message += f"削除される変数: {', '.join(sorted(removed_vars))}\n"
                message += "\nこの変更を適用しますか？"

                msg.setText(message)
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                
                log_debug("遒ｺ隱阪Γ繝・そ繝ｼ繧ｸ:")
                log_debug(message)
                
                if msg.exec_() == QMessageBox.Yes:

                    
                    # 迴ｾ蝨ｨ縺ｮ螟画焚縺ｮ荳ｦ縺ｳ鬆・ｒ蜿門ｾ・
                    current_order = self.parent.variables.copy()
                    
                    # 蜑企勁縺輔ｌ繧句､画焚繧堤樟蝨ｨ縺ｮ荳ｦ縺ｳ鬆・°繧牙炎髯､
                    current_order = [
                        var for var in current_order
                        if self._normalize_variable_name(var) not in removed_vars
                    ]
                    
                    # 霑ｽ蜉縺輔ｌ繧句､画焚繧堤樟蝨ｨ縺ｮ荳ｦ縺ｳ鬆・・譛蠕後↓霑ｽ蜉
                    existing_normalized = {self._normalize_variable_name(var) for var in current_order}
                    for var in added_vars:
                        if var not in existing_normalized:
                            current_order.append(var)
                    
                    # 螟画峩繧帝←逕ｨ
                    input_vars = [var for var in current_order if var in new_vars]
                    result_var_list = [var for var in current_order if var in result_vars]
                    
                    # 險育ｮ礼ｵ先棡螟画焚繧貞・縺ｫ縲∝・蜉帛､画焚繧貞ｾ後↓
                    self.parent.variables = result_var_list + input_vars
                    self.parent.result_variables = result_var_list
                    
        

                    
                    # 譁ｰ縺励＞螟画焚縺ｮ縺溘ａ縺ｫ螟画焚蛟､霎樊嶌繧貞・譛溷喧
                    for var in added_vars:
                        self.parent.ensure_variable_initialized(var, is_result=var in result_vars)

                    
                    # 蜑企勁縺輔ｌ繧句､画焚縺ｮ蛟､繧貞炎髯､
                    for var in list(self.parent.variable_values):
                        if self._normalize_variable_name(var) in removed_vars:
                            del self.parent.variable_values[var]

                    
                    # 隕ｪ繧ｪ繝悶ず繧ｧ繧ｯ繝医・螟画焚讀懷・繝｡繧ｽ繝・ラ繧貞他縺ｳ蜃ｺ縺・
                    if hasattr(self.parent, 'detect_variables'):

                        self.parent.detect_variables()
                    
                    # 螟画焚繧ｿ繝悶・蠑ｷ蛻ｶ譖ｴ譁ｰ
                    if hasattr(self.parent, 'variables_tab'):

                        self.parent.variables_tab.update_variable_list(
                            self.parent.variables, 
                            self.parent.result_variables
                        )
                    
                    # 螟画焚繝ｪ繧ｹ繝医ｒ譖ｴ譁ｰ
                    self.update_variable_list()
                    
                    # 譛蠕後↓蜈･蜉帙＠縺滓婿遞句ｼ上ｒ菫晏ｭ・
                    self.parent.last_equation = equation

                    
                else:
                    # 繧ｭ繝｣繝ｳ繧ｻ繝ｫ縺ｮ蝣ｴ蜷医・蜈・・譁ｹ遞句ｼ上↓謌ｻ縺・
                    self.equation_input.setText(self.parent.last_equation)
                    return False
            else:
                if added_vars:
                    # 迴ｾ蝨ｨ縺ｮ螟画焚縺ｮ荳ｦ縺ｳ鬆・ｒ蜿門ｾ・
                    current_order = self.parent.variables.copy()
                    
                    # 霑ｽ蜉縺輔ｌ繧句､画焚繧堤樟蝨ｨ縺ｮ荳ｦ縺ｳ鬆・・譛蠕後↓霑ｽ蜉
                    existing_normalized = {self._normalize_variable_name(var) for var in current_order}
                    for var in added_vars:
                        if var not in existing_normalized:
                            current_order.append(var)
                    
                    # 螟画峩繧帝←逕ｨ
                    input_vars = [var for var in current_order if var in new_vars]
                    result_var_list = [var for var in current_order if var in result_vars]
                    
                    # 險育ｮ礼ｵ先棡螟画焚繧貞・縺ｫ縲∝・蜉帛､画焚繧貞ｾ後↓
                    self.parent.variables = result_var_list + input_vars
                    self.parent.result_variables = result_var_list
                    
                    # 譁ｰ縺励＞螟画焚縺ｮ縺溘ａ縺ｫ螟画焚蛟､霎樊嶌繧貞・譛溷喧
                    for var in added_vars:
                        self.parent.ensure_variable_initialized(var, is_result=var in result_vars)
                    
                    # 隕ｪ繧ｪ繝悶ず繧ｧ繧ｯ繝医・螟画焚讀懷・繝｡繧ｽ繝・ラ繧貞他縺ｳ蜃ｺ縺・
                    if hasattr(self.parent, 'detect_variables'):
                        self.parent.detect_variables()
                    
                    # 螟画焚繧ｿ繝悶・蠑ｷ蛻ｶ譖ｴ譁ｰ
                    if hasattr(self.parent, 'variables_tab'):
                        self.parent.variables_tab.update_variable_list(
                            self.parent.variables, 
                            self.parent.result_variables
                        )
                    
                    # 螟画焚繝ｪ繧ｹ繝医ｒ譖ｴ譁ｰ
                    self.update_variable_list()
                
                # 螟画焚縺ｮ螟画峩縺後↑縺・ｴ蜷医ｂ譁ｹ遞句ｼ上ｒ菫晏ｭ・
                self.parent.last_equation = equation

            
            log_debug(f"\n{'#'*80}")
            log_debug(f"#" + " " * 30 + "方程式変更チェック完了" + " " * 30 + "#")
            log_debug(f"{'#'*80}\n")
            return True
            
        except Exception as e:
            self.parent.log_error(
                f"譁ｹ遞句ｼ上・螟画峩繝√ぉ繝・け繧ｨ繝ｩ繝ｼ: {str(e)}",
                "譁ｹ遞句ｼ上メ繧ｧ繝・け繧ｨ繝ｩ繝ｼ",
                details=traceback.format_exc(),
            )
            return False
            
    def resolve_equation(self, target_var, equations):
        """
        騾｣遶区婿遞句ｼ上ｒ謨ｴ逅・＠縺ｦ縲∫岼讓吝､画焚縺ｮ蠑上ｒ蜈･蜉帛､画焚縺縺代・蠑上↓螟画鋤
        
        Args:
            target_var (str): 逶ｮ讓吝､画焚・井ｾ・ 'W'・・
            equations (list): 騾｣遶区婿遞句ｼ上・繝ｪ繧ｹ繝茨ｼ井ｾ・ ['W = V * I', 'V = V_MEAS + V_CAL', 'I = I_MEAS + I_CAL']・・
            
        Returns:
            str: 謨ｴ逅・＆繧後◆蠑擾ｼ井ｾ・ 'W = (V_MEAS + V_CAL) * (I_MEAS + I_CAL)'・・
        """
        try:
            # 蠑上ｒ霎樊嶌縺ｫ螟画鋤・亥ｷｦ霎ｺ繧偵く繝ｼ縲∝承霎ｺ繧貞､縺ｨ縺吶ｋ・・
            eq_dict = {}
            for eq in equations:
                if '=' not in eq:
                    continue
                left, right = eq.split('=', 1)
                eq_dict[left.strip()] = right.strip()
            
            # 逶ｮ讓吝､画焚縺ｮ蠑上ｒ蜿門ｾ・
            if target_var not in eq_dict:
                return None
            
            # 蠑上ｒ蜀榊ｸｰ逧・↓螻暮幕
            def expand_expression(expr):
                # 蠑上ｒ蛻・牡
                terms = []
                current_term = ''
                i = 0
                while i < len(expr):
                    char = expr[i]
                    if char in '+-*/^()':
                        if current_term:
                            terms.append(current_term.strip())
                            current_term = ''
                        terms.append(char)
                    else:
                        current_term += char
                    i += 1
                if current_term:
                    terms.append(current_term.strip())
                
                # 蜷・・ｒ螻暮幕
                expanded_terms = []
                for term in terms:
                    if term in '+-*/^()':
                        expanded_terms.append(term)
                    else:
                        # 螟画焚縺悟ｮ夂ｾｩ蠑上↓蜷ｫ縺ｾ繧後※縺・ｋ蝣ｴ蜷医・螻暮幕
                        if term in eq_dict:
                            expanded_terms.append(f"({expand_expression(eq_dict[term])})")
                        else:
                            expanded_terms.append(term)
                
                return ''.join(expanded_terms)
            
            # 蠑上ｒ螻暮幕
            expanded_right = expand_expression(eq_dict[target_var])
            return f"{target_var} = {expanded_right}"
            
        except Exception as e:
            log_error(f"蠑上・謨ｴ逅・お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())
            return None

    def update_html_display(self, equation):
        """譁ｹ遞句ｼ上ｒHTML蠖｢蠑上〒陦ｨ遉ｺ"""
        try:
            if not equation:
                self.html_display.clear()
                return

            # 譁ｹ遞句ｼ上ｒ蛻・牡
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            html_parts = []

            for eq in equations:
                if '=' not in eq:
                    continue

                # 荵礼ｮ苓ｨ伜捷繧剃ｸｭ鮟偵↓螟画鋤
                processed_eq = eq.replace('*', '・･')

                # 荳倶ｻ倥″譁・ｭ励・蜃ｦ逅・ｼ・縺ｮ蠕後・譁・ｭ励ｄ謨ｰ蟄励ｒ荳倶ｻ倥″譁・ｭ励↓螟画鋤・・
                processed_eq = re.sub(r'([a-zA-Zﾎｱ-ﾏ火・ﾎｩ])_([a-zA-Z0-9ﾎｱ-ﾏ火・ﾎｩ]+)', r'\1<sub>\2</sub>', processed_eq)
                
                # 荳贋ｻ倥″譁・ｭ励・蜃ｦ逅・ｼ・縺ｮ蠕後・謨ｰ蟄励ｄ譁・ｭ励ｒ荳贋ｻ倥″譁・ｭ励↓螟画鋤・・
                processed_eq = re.sub(r'\^(\d+|\([^)]+\))', r'<sup>\1</sup>', processed_eq)
                # 諡ｬ蠑ｧ縺ｮ荳ｭ縺ｮ^繧ょ・逅・
                processed_eq = re.sub(r'\(([^)]+)\^(\d+|\([^)]+\))\)', r'(\1<sup>\2</sup>)', processed_eq)

                html_parts.append(processed_eq)

            # 譁・ｭ励し繧､繧ｺ繧貞､画峩縺励∵婿遞句ｼ上ｒ謾ｹ陦後〒邨仙粋
            html = f'<div style="font-size: 16px;">{"<br>".join(html_parts)}</div>'
            
            self.html_display.setHtml(html)

        except Exception as e:
            log_error(f"HTML陦ｨ遉ｺ縺ｮ譖ｴ譁ｰ繧ｨ繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())

    def detect_variables(self, equation):
        """繝｢繝・Ν蠑上°繧牙､画焚繧呈､懷・"""
        try:


            
            # 迴ｾ蝨ｨ縺ｮ螟画焚繝ｪ繧ｹ繝医ｒ繧ｯ繝ｪ繧｢
            self.variables.clear()
            
            # 譁ｹ遞句ｼ上ｒ蛻・牡
            normalized_equation = normalize_equation_text(equation)
            equations = [eq.strip() for eq in normalized_equation.split(',')]
            
            # 蟾ｦ霎ｺ縺ｮ螟画焚・郁ｨ育ｮ礼ｵ先棡・峨ｒ菫晄戟縺吶ｋ繧ｻ繝・ヨ
            result_variables = set()
            
            # 縺ｾ縺壼ｷｦ霎ｺ縺ｮ螟画焚繧貞庶髮・
            for eq in equations:
                if '=' not in eq:
                    continue
                left_side = self._normalize_variable_name(eq.split('=', 1)[0])
                result_variables.add(left_side)
            

            
            # 蜿ｳ霎ｺ縺九ｉ螟画焚繧呈､懷・
            for eq in equations:
                if '=' not in eq:
                    continue
                    
                left_side, right_side = eq.split('=', 1)
                left_side = self._normalize_variable_name(left_side)
                right_side = right_side.strip()

                
                # 蜿ｳ霎ｺ縺九ｉ螟画焚繧呈､懷・・域ｭ｣隕剰｡ｨ迴ｾ縺ｧ逶ｴ謗･讀懷・・・
                detected_vars = re.findall(
                    r"[A-Za-z\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*",
                    right_side,
                )

                
                # 險育ｮ礼ｵ先棡螟画焚縺ｧ縺ｪ縺・､画焚縺ｮ縺ｿ繧定ｿｽ蜉
                for var in detected_vars:
                    normalized_var = self._normalize_variable_name(var)
                    if normalized_var and normalized_var not in result_variables:
                        self.variables.append(normalized_var)
            
            # 驥崎､・ｒ髯､蜴ｻ
            self.variables = list(dict.fromkeys(self.variables))

            
        except Exception as e:

            raise 

    def _normalize_variable_name(self, name):
        """荳榊庄隕匁枚蟄励ｒ髯､蜴ｻ縺励※螟画焚蜷阪ｒ豁｣隕丞喧"""
        return normalize_variable_name(name)

    def set_equation(self, equation):
        """Set equation text."""
        try:
            normalized_equation = equation or ""
            self.equation_input.setText(normalized_equation)
            self.update_html_display(normalized_equation)
            self.update_variable_list()
        except Exception as e:
            self.parent.log_error(
                f"譁ｹ遞句ｼ上・險ｭ螳壹お繝ｩ繝ｼ: {str(e)}",
                "譁ｹ遞句ｼ剰ｨｭ螳壹お繝ｩ繝ｼ",
                details=traceback.format_exc(),
            )

    def on_equation_changed(self):
        """Handle equation text changes."""
        try:
            equation = self.equation_input.toPlainText().strip()
            self.update_html_display(equation)
            self.detect_variables(equation)

            if hasattr(self.parent, 'partial_derivative_tab'):
                self.parent.partial_derivative_tab.update_equation_display()
            if hasattr(self.parent, 'report_tab'):
                self.parent.report_tab.update_report()
            if hasattr(self.parent, 'uncertainty_calculation_tab'):
                self.parent.uncertainty_calculation_tab.update_result_combo()
                self.parent.uncertainty_calculation_tab.update_value_combo()
        except Exception as e:
            log_error(f"謨ｰ蠑丞､画峩蜃ｦ逅・お繝ｩ繝ｼ: {str(e)}", details=traceback.format_exc())

    def parse_equation(self, equation):
        import re
        normalized_equation = normalize_equation_text(equation)
        equations = [eq.strip() for eq in normalized_equation.split(',')]
        result_vars = []
        input_vars = set()
        for eq in equations:
            if '=' not in eq:
                continue
            left, right = eq.split('=', 1)
            left = self._normalize_variable_name(left)
            right = right.strip()
            result_vars.append(left)
            for var in re.findall(
                r"[A-Za-z_\u03B1-\u03C9\u0391-\u03A9][A-Za-z0-9_\u03B1-\u03C9\u0391-\u03A9]*",
                right,
            ):
                normalized_var = self._normalize_variable_name(var)
                if normalized_var and normalized_var != left:
                    input_vars.add(normalized_var)
        if hasattr(self.parent, 'result_variables'):
            self.parent.result_variables = result_vars
        if hasattr(self.parent, 'input_variables'):
            self.parent.input_variables = list(input_vars)
        variables = result_vars + [v for v in input_vars if v not in result_vars]
        if hasattr(self.parent, 'variables'):
            self.parent.variables = variables
        self._ensure_variable_values_initialized()
        return variables

    def _ensure_variable_values_initialized(self):
        """讀懷・貂医∩縺ｮ螟画焚繧致ariable_values縺ｫ逋ｻ骭ｲ縺励∝腰菴阪ヵ繧｣繝ｼ繝ｫ繝峨ｒ謖√◆縺帙ｋ"""
        if not hasattr(self.parent, 'ensure_variable_initialized'):
            return

        for var in getattr(self.parent, 'result_variables', []):
            self.parent.ensure_variable_initialized(var, is_result=True)

        for var in getattr(self.parent, 'variables', []):
            if var not in getattr(self.parent, 'result_variables', []):
                self.parent.ensure_variable_initialized(var)
