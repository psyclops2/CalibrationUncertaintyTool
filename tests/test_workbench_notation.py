from types import SimpleNamespace
import math

import numpy as np
import pytest
import sympy as sp

from src.utils.model_expression import parse_expression, variable_names
from src.utils.equation_normalizer import normalize_variable_name
from src.utils.equation_formatter import EquationFormatter
from src.utils.quantity_notation import decode_greek, format_quantity_name
from src.utils.project_io import read_project, validate_project
from tests.test_project_safety import window


def test_greek_codes_and_variants_remain_distinct_in_calculation():
    assert decode_greek('\\alpha\\ \\Gamma\\ \\rho\\') == 'α Γ ρ'
    expression = parse_expression('\\theta\\ - \\theta1\\ + \\phi\\ - \\phi1\\')
    assert {str(s) for s in expression.free_symbols} == {'ϑ','θ','ϕ','φ'}
    values = {sp.Symbol(n,real=True):v for n,v in {'ϑ':4,'θ':1,'ϕ':8,'φ':2}.items()}
    assert float(expression.subs(values)) == 9
    assert normalize_variable_name(r'\mu\_ref') == 'µ_ref'
    assert variable_names(r'\mu\_ref + \rho\_W') == ['µ_ref','ρ_W']


def test_underscore_display_modes_keep_identifiers_intact():
    assert format_quantity_name('x_a_b','workbench') == 'x<sub>a</sub>b'
    assert format_quantity_name('x_ab_','workbench') == 'x<sub>ab</sub>'
    assert format_quantity_name('x_a_b','legacy') == 'x<sub>a_b</sub>'
    assert format_quantity_name(r'\rho\_W','workbench') == 'ρ<sub>W</sub>'
    assert variable_names('x_a_b + x_ab_') == ['x_a_b','x_ab_']


@pytest.mark.parametrize('formula,value', [('2^3^2',512),('-2^2',-4),('(-2)^2',4),('2^-2',.25),('2**3',8)])
def test_power_calculation_matches_normal_precedence(formula,value):
    assert float(parse_expression(formula)) == value


def test_power_preview_handles_negative_grouped_chained_and_double_star():
    formatter = EquationFormatter(SimpleNamespace(model_notation='workbench'))
    markup = formatter.format_equation(r'Y_out = \rho\_W^-2 + x^(n+1) + a^b^c + z**2 + 1e-3')
    assert 'ρ</span><sub>W</sub><sup>-2</sup>' in markup
    assert '<sup>(n+1)</sup>' in markup
    assert '<sup>b<sup>c</sup></sup>' in markup
    assert 'z</span><sup>2</sup>' in markup
    assert '1e-3' in markup
    assert '\\rho' not in markup


def test_greek_model_save_reload_calculus_mc_and_report(window,tmp_path,monkeypatch):
    raw = 'Y_out = (\\rho\\_W - \\rho\\_A)^2 + \\theta\\ - \\theta1\\ + \\phi\\ - \\phi1\\'
    centres = {'ρ_W':3,'ρ_A':1,'ϑ':4,'θ':1,'ϕ':8,'φ':2}
    variables = {'Y_out':{'type':'result','unit':'1','values':[{}]}}
    for name,value in centres.items():
        variables[name] = {'type':'B','unit':'1','distribution':'NORMAL_DISTRIBUTION','divisor':'1',
            'values':[{'central_value':str(value),'standard_uncertainty':'.1','half_width':'.1','divisor':'1','degrees_of_freedom':'inf'}]}
    project = {'last_equation':raw,'model_notation':'workbench','variables':list(variables),'result_variables':['Y_out'],
        'value_names':['P1'],'value_count':1,'variable_values':variables}
    assert window.load_data(project,show_message=False)
    tab = window.uncertainty_calculation_tab
    tab.on_result_changed('Y_out')
    result = window.calculation_results['Y_out']['P1']
    assert math.isclose(result['result_central_value'],13)
    assert math.isclose(result['result_standard_uncertainty'],.6)
    assert not hasattr(window.model_equation_tab,'notation_combo')
    markup = window.report_tab.generate_report_html(raw)
    assert 'ρ</span><sub>W</sub>' in markup
    assert 'Y<sub>out</sub>' in markup
    window.partial_derivative_tab.update_equation_display()
    assert 'ϑ' in window.partial_derivative_tab.partial_diff_area.toPlainText()
    mc = window.monte_carlo_tab
    monkeypatch.setattr(mc,'_sample_input_variables',lambda names,count:[np.full(count,centres[name]) for name in names])
    assert np.allclose(mc._evaluate_result_samples('Y_out',3),[13,13,13])
    path = tmp_path/'greek.cutp'
    window._write_save_data_to_path(path)
    assert read_project(path)['last_equation'] == raw
    assert window.load_data(read_project(path),show_message=False)
    assert window.model_notation == 'workbench'
    assert window.model_equation_tab.equation_input.toPlainText() == raw


def test_all_projects_use_workbench_notation(window):
    assert window.load_data({'model_notation':'legacy'},show_message=False)
    assert window.model_notation == 'workbench'
    assert not hasattr(window.model_equation_tab,'notation_combo')
    window.new_file()
    assert window.model_notation == 'workbench'
    assert not hasattr(window.model_equation_tab,'notation_combo')


def test_insertion_uses_ascii_code_and_unknown_codes_fail(window):
    tab = window.model_equation_tab
    tab.greek_actions['rho'].trigger()
    assert tab.equation_input.toPlainText() == '\\rho\\'
    with pytest.raises(ValueError):
        parse_expression(r'\notGreek\ + 1')
    with pytest.raises(ValueError):
        validate_project({'model_notation':'invalid'})
