from ..utils.translation_keys import *

# English Translation Dictionary
translations = {
    "MainWindow": {
        # Application General
        APP_TITLE: "Calibration Uncertainty Calculation Tool",
        
        # Menu related
        MENU_FILE: "File",
        MENU_EDIT: "Edit",
        MENU_VIEW: "View",
        MENU_LANGUAGE: "Language",
        MENU_HELP: "Help",
        ABOUT_APP: "About",

        # File menu actions
        FILE_OPEN: "Open...",
        FILE_SAVE_AS: "Save As...",
        FILE_EXIT: "Exit",
        
        # Dialogs
        SAVE_DIALOG_TITLE: "Save As",
        OPEN_DIALOG_TITLE: "Open File",
        
        # Language related
        LANGUAGE_JAPANESE: "Japanese",
        LANGUAGE_ENGLISH: "English",
        LANGUAGE_SETTINGS: "Language Settings",
        LANGUAGE_CHANGED: "Language Changed",
        USE_SYSTEM_LOCALE: "Use System Locale",
        RESTART_REQUIRED: "Restart Required",
        LANGUAGE_CHANGED_RESTART_MESSAGE: "Language settings have been changed.\nPlease restart the application to apply the changes.",
        
        # Tab names (set in MainWindow)
        TAB_EQUATION: "Model Equation",
        TAB_VARIABLES: "Variable Management",
        TAB_CALCULATION: "Uncertainty Calculation",
        TAB_REPORT: "Report",
        PARTIAL_DERIVATIVE: "Partial Derivative",
        POINT_SETTINGS_TAB: "Point Settings",
        DOCUMENT_INFO_TAB: "Document Info",

        # General buttons
        BUTTON_SAVE: "Save",
        BUTTON_CANCEL: "Cancel",

        # Messages
        MESSAGE_SUCCESS: "Success",
        FILE_LOADED: "File loaded successfully.",
        FILE_SAVED: "File saved successfully.",
        FILE_LOAD_ERROR: "Failed to load file.",
        FILE_NOT_FOUND: "File not found.",
        INVALID_FILE_FORMAT: "Invalid file format.",
        ERROR_OCCURRED: "An error occurred.",
        
        # Calibration point name
        CALIBRATION_POINT_NAME: "Calibration Point",
    },
    "ModelEquationTab": {
        MODEL_EQUATION_INPUT: "Model Equation Input",
        EQUATION_PLACEHOLDER: "e.g., y = a * x + b",
        VARIABLE_LIST_DRAG_DROP: "Variable List (Drag &amp; Drop to reorder)",
        HTML_DISPLAY: "HTML Display",
        VARIABLE_ORDER_UPDATE_FAILED: "Failed to update variable order.",
        VARIABLE_ORDER_SAVE_FAILED: "Failed to save variable order.",
        VARIABLE_ORDER_LOAD_FAILED: "Failed to load variable order.",
    },
    "DocumentInfoTab": {
        DOCUMENT_NUMBER: "Document Number",
        DOCUMENT_NAME: "Document Name",
        VERSION_INFO: "Version Info",
        DESCRIPTION_LABEL: "Description (Markdown only)",
        REVISION_HISTORY: "Revision History",
        REVISION_HISTORY_PLACEHOLDER: "v1,Description,Author,Reviewer,Approver,2024-01-01",
        REVISION_HISTORY_INSTRUCTION: "Enter each line as 'ver,description,author,reviewer,approver,date'.",
    },
    "VariablesTab": {
        CALIBRATION_POINT_SETTINGS: "Calibration Point Settings",
        CALIBRATION_POINT_COUNT: "Number of Calibration Points",
        CALIBRATION_POINT_SELECTION: "Select Calibration Point",
        VARIABLE_LIST_AND_VALUES: "Variable List / Values",
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
        MEASUREMENT_VALUES_PLACEHOLDER: "Enter comma-separated values (e.g., 1.2, 1.3, 1.4)",
        DEGREES_OF_FREEDOM: "Degrees of Freedom",
        CENTRAL_VALUE: "Central Value",
        STANDARD_UNCERTAINTY: "Standard Uncertainty",
        DETAIL_DESCRIPTION: "Detailed Description",
        DISTRIBUTION: "Distribution",
        NORMAL_DISTRIBUTION: "Normal Distribution",
        RECTANGULAR_DISTRIBUTION: "Rectangular Distribution",
        TRIANGULAR_DISTRIBUTION: "Triangular Distribution",
        U_DISTRIBUTION: "U-shaped Distribution",
        DIVISOR: "Divisor",
        HALF_WIDTH: "Half-width",
        CALCULATION_FORMULA: "Calculation Formula",
        CALCULATE: "Calculate",
        BUTTON_ADD: "Add",
        BUTTON_EDIT: "Edit",
        BUTTON_DELETE: "Delete",
        LABEL_UNIT: "Unit",
    },
    "PointSettingsTab": {
        POINT_SETTINGS_TAB_INFO: "Set the name for each calibration point. You can also add and remove calibration points.",
        INDEX: "Index",
        POINT_NAME: "Point Name",
        ADD_POINT: "Add Point",
        REMOVE_POINT: "Remove Point",
    },
    "UncertaintyCalculationTab": {
        RESULT_SELECTION: "Result Selection",
        RESULT_VARIABLE: "Result Variable",
        CALIBRATION_POINT: "Calibration Point",
        CALIBRATION_VALUE: "Calibration Value",
        VARIABLE: "Variable",
        CENTRAL_VALUE: "Central Value",
        STANDARD_UNCERTAINTY: "Standard Uncertainty",
        DEGREES_OF_FREEDOM: "Degrees of Freedom",
        DISTRIBUTION: "Distribution",
        SENSITIVITY_COEFFICIENT: "Sensitivity Coefficient",
        CONTRIBUTION_UNCERTAINTY: "Contribution Uncertainty",
        CONTRIBUTION_RATE: "Contribution Rate",
        CALCULATION_RESULT: "Calculation Result",
        COMBINED_STANDARD_UNCERTAINTY: "Combined Standard Uncertainty",
        EFFECTIVE_DEGREES_OF_FREEDOM: "Effective Degrees of Freedom",
        COVERAGE_FACTOR: "Coverage Factor k",
        EXPANDED_UNCERTAINTY: "Expanded Uncertainty U",
    },
    "ReportTab": {
        # UI elements
        GENERATE_REPORT: "Generate Report",
        SAVE_REPORT: "Save Report",
        
        # save_report dialog
        SAVE_REPORT_DIALOG_TITLE: "Save Report",
        HTML_FILE: "HTML File",
        SAVE_CANCELLED: "Save was cancelled.",
        SAVE_SUCCESS: "Success",
        REPORT_SAVED: "Report saved successfully.",
        SAVE_ERROR: "Save Error",
        REPORT_SAVE_ERROR: "An error occurred while saving the report.",
        FILE_SAVE_ERROR: "An error occurred while saving the file.",

        # HTML Report Title
        REPORT_TITLE_HTML: "Calibration Uncertainty Calculation Report",
        REPORT_DOCUMENT_INFO: "Document Information",

        # HTML Section Titles
        REPORT_MODEL_EQUATION: "Model Equation",
        REPORT_VARIABLE_LIST: "Variable List",
        REPORT_VARIABLE_DETAILS: "Details for Each Variable",
        REPORT_MEASUREMENT_VALUES: "Measurement Values",
        REPORT_UNCERTAINTY_BUDGET: "Uncertainty Budget",
        REPORT_CALCULATION_RESULT: "Calculation Result",
        REPORT_REVISION_HISTORY: "Revision History",

        # HTML Table Headers
        REPORT_QUANTITY: "Quantity",
        REPORT_UNIT: "Unit",
        REPORT_DEFINITION: "Definition",
        REPORT_UNCERTAINTY_TYPE: "Uncertainty Type",
        REPORT_MEASUREMENT_NUMBER: "Number of Measurements",
        REPORT_VALUE: "Value",
        REPORT_FACTOR: "Factor",
        REPORT_CENTRAL_VALUE: "Central Value",
        REPORT_STANDARD_UNCERTAINTY: "Standard Uncertainty",
        REPORT_DOF: "d.o.f.",
        REPORT_DISTRIBUTION: "Distribution",
        REPORT_SENSITIVITY: "Sensitivity",
        REPORT_CONTRIBUTION: "Contribution (Uncertainty)",
        REPORT_CONTRIBUTION_RATE: "Contribution Rate (%)",
        REPORT_ITEM: "Item",
        DOCUMENT_NUMBER: "Document Number",
        DOCUMENT_NAME: "Document Name",
        VERSION_INFO: "Version Info",
        DESCRIPTION_LABEL: "Description",
        REVISION_VERSION: "Version",
        REVISION_DESCRIPTION: "Description",
        REVISION_AUTHOR: "Author",
        REVISION_CHECKER: "Reviewer",
        REVISION_APPROVER: "Approver",
        REVISION_DATE: "Revised Date",

        # Variable details
        DETAIL_DESCRIPTION: "Detailed Description",
        HALF_WIDTH: "Half-width",
        DISTRIBUTION: "Distribution",
        FIXED_VALUE: "Fixed Value",

        # HTML Calculation Result Items
        REPORT_CALIBRATION_POINT: "Calibration Point",
        REPORT_EQUATION: "Calculation Formula",
        REPORT_COMBINED_UNCERTAINTY: "Combined Standard Uncertainty",
        REPORT_EFFECTIVE_DOF: "Effective Degrees of Freedom",
        REPORT_COVERAGE_FACTOR: "Coverage Factor k",
        REPORT_EXPANDED_UNCERTAINTY: "Expanded Uncertainty U",

        # get_uncertainty_type_display
        CALCULATION_RESULT_DISPLAY: "Calculation Result",
        TYPE_A_DISPLAY: "Type A",
        TYPE_B_DISPLAY: "Type B",
        FIXED_VALUE_DISPLAY: "Fixed Value",
        UNKNOWN_TYPE: "Unknown",

        # Error messages
        HTML_GENERATION_ERROR: "An error occurred during report generation.",
    },
    "PartialDerivativeTab": {
        PARTIAL_DERIVATIVE_TITLE: "Partial Derivative",
        LABEL_EQUATION: "Equation",
        DERIVATIVE_VARIABLE: "Variable to Differentiate",
        DERIVATIVE_RESULT: "Differentiation Result",
        CALCULATE_DERIVATIVE: "Calculate Derivative",
        DERIVATIVE_CALCULATION_ERROR: "Differentiation Calculation Error",
        DERIVATIVE_CALCULATION_SUCCESS: "Differentiation Calculation Successful",
        DERIVATIVE_EXPRESSION: "Derivative Expression",
    },
}
