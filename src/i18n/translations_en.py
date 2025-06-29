"""
English translation file
"""

from ..utils.translation_keys import *

# Translation dictionary
translations = {
    # Application general
    APP_TITLE: "Calibration Uncertainty Calculator",
    
    # Menu related
    MENU_FILE: "File",
    MENU_EDIT: "Edit",
    MENU_VIEW: "View",
    MENU_LANGUAGE: "Language",
    MENU_HELP: "Help",
    
    # File menu actions
    FILE_SAVE_AS: "Save As...",
    FILE_OPEN: "Open...",
    FILE_EXIT: "Exit",
    
    # Language related
    LANGUAGE_JAPANESE: "Japanese",
    LANGUAGE_ENGLISH: "English",
    LANGUAGE_SETTINGS: "Language Settings",
    LANGUAGE_CHANGED: "Language Changed",
    USE_SYSTEM_LOCALE: "Use System Language",
    RESTART_REQUIRED: "Restart Required",
    LANGUAGE_CHANGED_RESTART_MESSAGE: "Language settings have been changed.\nPlease restart the application to apply the changes.",
    
    # Tab names
    TAB_EQUATION: "Model Equation",
    TAB_VARIABLES: "Variables / Values",
    TAB_CALCULATION: "Calculation",
    TAB_REPORT: "Report",
    PARTIAL_DERIVATIVE: "Partial Derivatives",
    
    # Buttons
    BUTTON_ADD: "Add",
    BUTTON_EDIT: "Edit",
    BUTTON_DELETE: "Delete",
    BUTTON_SAVE: "Save",
    BUTTON_CANCEL: "Cancel",
    BUTTON_CALCULATE: "Calculate",
    BUTTON_GENERATE_REPORT: "Generate Report",
    BUTTON_SAVE_REPORT: "Save Report",
    
    # Labels
    LABEL_EQUATION: "Equation",
    LABEL_VARIABLE: "Variable",
    LABEL_VALUE: "Value",
    LABEL_NOMINAL_VALUE: "Nominal Value",
    LABEL_UNIT: "Unit",
    LABEL_DEFINITION: "Definition",
    LABEL_UNCERTAINTY: "Uncertainty",
    LABEL_UNCERTAINTY_TYPE: "Uncertainty Type",
    LABEL_DISTRIBUTION: "Distribution",
    LABEL_DEGREES_OF_FREEDOM: "Degrees of Freedom",
    LABEL_COVERAGE_FACTOR: "Coverage Factor",
    LABEL_EXPANDED_UNCERTAINTY: "Expanded Uncertainty",
    LABEL_RESULT: "Result",
    LABEL_CALCULATION_RESULT: "Calculation Result",
    
    # Uncertainty types
    UNCERTAINTY_TYPE_A: "Type A",
    UNCERTAINTY_TYPE_B: "Type B",
    UNCERTAINTY_TYPE_FIXED: "Fixed Value",
    UNCERTAINTY_TYPE_RESULT: "Calculation Result",
    
    # Distribution types
    DISTRIBUTION_NORMAL: "Normal Distribution",
    DISTRIBUTION_RECTANGULAR: "Rectangular Distribution",
    DISTRIBUTION_TRIANGULAR: "Triangular Distribution",
    DISTRIBUTION_U_SHAPED: "U-shaped Distribution",
    
    # Messages
    MESSAGE_ERROR: "Error",
    MESSAGE_WARNING: "Warning",
    MESSAGE_INFO: "Information",
    MESSAGE_CONFIRM: "Confirmation",
    MESSAGE_SUCCESS: "Success",
    MESSAGE_EQUATION_CHANGE: "The following variables need to be modified due to changes in the model equation",
    
    # Model Equation Tab related
    MODEL_EQUATION_INPUT: "Model Equation Input",
    EQUATION_PLACEHOLDER: "Example: y = a * x + b, z = x^2 + y",
    VARIABLE_LIST_DRAG_DROP: "Variable List (Drag & Drop to change order)",
    HTML_DISPLAY: "HTML Display",
    VARIABLE_ORDER_UPDATE_FAILED: "Failed to update variable order",
    VARIABLE_ORDER_SAVE_FAILED: "Failed to save variable order",
    VARIABLE_ORDER_LOAD_FAILED: "Failed to load variable order",
    FILE_LOADED: "File loaded",
    
    # Variables Tab related
    CALIBRATION_POINT_SETTINGS: "Calibration Point Settings",
    CALIBRATION_POINT_COUNT: "Calibration Point Count",
    CALIBRATION_POINT_SELECTION: "Calibration Point Selection",
    VARIABLE_LIST_AND_VALUES: "Variable List / Variable Values",
    VARIABLE_MODE: "Variable Mode",
    NOT_SELECTED: "Not Selected",
    VARIABLE_DETAIL_SETTINGS: "Variable Detail Settings",
    UNIT: "Unit",
    DEFINITION: "Definition",
    UNCERTAINTY_TYPE: "Uncertainty Type",
    TYPE_A: "Type A",
    TYPE_B: "Type B",
    FIXED_VALUE: "Fixed Value",
    MEASUREMENT_VALUES: "Measurement Values",
    MEASUREMENT_VALUES_PLACEHOLDER: "Enter comma-separated values (e.g.: 1.2, 1.3, 1.4)",
    DEGREES_OF_FREEDOM: "Degrees of Freedom",
    CENTRAL_VALUE: "Central Value",
    STANDARD_UNCERTAINTY: "Standard Uncertainty",
    DETAIL_DESCRIPTION: "Detailed Description",
    DISTRIBUTION: "Distribution",
    NORMAL_DISTRIBUTION: "Normal Distribution",
    RECTANGULAR_DISTRIBUTION: "Rectangular Distribution",
    TRIANGULAR_DISTRIBUTION: "Triangular Distribution",
    U_DISTRIBUTION: "U Distribution",
    DIVISOR: "Divisor",
    HALF_WIDTH: "Half Width",
    CALCULATION_FORMULA: "Calculation Formula",
    CALCULATE: "Calculate",
    
    # Calculation Tab related
    RESULT_SELECTION: "Result Selection",
    RESULT_VARIABLE: "Result Variable",
    CALIBRATION_POINT: "Calibration Point",
    CALIBRATION_VALUE: "Calibration Value",
    VARIABLE: "Variable",
    SENSITIVITY_COEFFICIENT: "Sensitivity Coefficient",
    CONTRIBUTION_UNCERTAINTY: "Contribution Uncertainty",
    CONTRIBUTION_RATE: "Contribution Rate",
    CALCULATION_RESULT: "Calculation Result",
    COMBINED_STANDARD_UNCERTAINTY: "Combined Standard Uncertainty",
    EFFECTIVE_DEGREES_OF_FREEDOM: "Effective Degrees of Freedom",
    COVERAGE_FACTOR: "Coverage Factor",
    EXPANDED_UNCERTAINTY: "Expanded Uncertainty",
    
    # Report Tab related
    GENERATE_REPORT: "Generate Report",
    SAVE_REPORT: "Save Report",
    SAVE_REPORT_DIALOG_TITLE: "Save Report",
    HTML_FILE: "HTML File",
    SAVE_CANCELLED: "Save cancelled",
    SAVE_SUCCESS: "Success",
    REPORT_SAVED: "Report saved successfully",
    SAVE_ERROR: "Error",
    REPORT_SAVE_ERROR: "An error occurred while saving the report",
    FILE_SAVE_ERROR: "An error occurred while saving the file",
    ERROR_OCCURRED: "An error occurred",
    
    # Report HTML text
    REPORT_TITLE_HTML: "Calibration Uncertainty Calculation Report",
    MODEL_EQUATION_HTML: "Model Equation",
    VARIABLE_LIST_HTML: "Variable List",
    QUANTITY_HTML: "Quantity",
    UNIT_HTML: "Unit",
    DEFINITION_HTML: "Definition",
    UNCERTAINTY_TYPE_HTML: "Uncertainty Type",
    VARIABLE_DETAILS_HTML: "Variable Details",
    MEASUREMENT_VALUES_HTML: "Measurement Values",
    MEASUREMENT_NUMBER_HTML: "Measurement #",
    UNCERTAINTY_BUDGET_HTML: "Uncertainty Budget",
    VALUE_HTML: "Value",
    EQUATION_HTML: "Equation",
    
    # Uncertainty types
    TYPE_A_DISPLAY: "Type A",
    TYPE_B_DISPLAY: "Type B",
    FIXED_VALUE_DISPLAY: "Fixed Value",
    CALCULATION_RESULT_DISPLAY: "Calculation Result",
    UNKNOWN_TYPE: "Unknown",
    
    # Partial Derivative Tab related
    PARTIAL_DERIVATIVE_TITLE: "Partial Derivative",
    DERIVATIVE_VARIABLE: "Target Variable",
    DERIVATIVE_RESULT: "Derivative Result",
    CALCULATE_DERIVATIVE: "Calculate Derivative",
    DERIVATIVE_CALCULATION_ERROR: "Derivative Calculation Error",
    DERIVATIVE_CALCULATION_SUCCESS: "Derivative Calculation Successful",
    DERIVATIVE_EXPRESSION: "Derivative Expression",
    
    # Report related
    REPORT_TITLE: "Calibration Uncertainty Evaluation Report",
    REPORT_MODEL_EQUATION: "Model Equation",
    REPORT_VARIABLE_LIST: "Variable List",
    REPORT_QUANTITY: "Quantity",
    REPORT_UNIT: "Unit",
    REPORT_DEFINITION: "Definition",
    REPORT_UNCERTAINTY_TYPE: "Uncertainty Type",
    REPORT_CALIBRATION_POINT: "Calibration Point",
    REPORT_CALCULATION_RESULT: "Calculation Result",
    REPORT_VARIABLE_DETAILS: "Variable Details",
    REPORT_MEASUREMENT_VALUES: "Measurement Values",
    REPORT_MEASUREMENT_NUMBER: "Measurement #",
    REPORT_UNCERTAINTY_BUDGET: "Uncertainty Budget",
    REPORT_CENTRAL_VALUE: "Central Value",
    REPORT_STANDARD_UNCERTAINTY: "Standard Uncertainty",
    REPORT_SENSITIVITY: "Sensitivity Coefficient",
    REPORT_CONTRIBUTION: "Uncertainty Contribution",
    REPORT_CONTRIBUTION_RATE: "Contribution Rate",
    REPORT_COMBINED_UNCERTAINTY: "Combined Standard Uncertainty",
    REPORT_EFFECTIVE_DOF: "Effective Degrees of Freedom",
    REPORT_EXPANDED_UNCERTAINTY: "Expanded Uncertainty",
}
