# Calibration Uncertainty Tool

## Overview
Calibration Uncertainty Tool is a desktop GUI application for uncertainty evaluation based on GUM (JCGM 100).

It supports model-equation based uncertainty budgets, multiple calibration points, correlation handling, regression support, Monte Carlo simulation, and HTML report export.

## Current Features (from code)
- Model equation input (single or multiple equations separated by commas)
- Automatic detection of input/result variables from equations
- Variable order management by drag-and-drop
- Variable settings per calibration point:
  - Type A uncertainty (measurement list -> mean, standard uncertainty, degrees of freedom)
  - Type B uncertainty (distribution, divisor, half-width, formula-assisted entry)
  - Fixed values
- Calibration point management (add/remove/rename/reorder)
- Batch input dialog for B-type and fixed-value rows across all calibration points
- Correlation matrix editing for input variables
- Uncertainty budget calculation per selected result variable and calibration point:
  - Sensitivity coefficients
  - Contribution uncertainty and contribution rates
  - Effective degrees of freedom
  - Coverage factor and expanded uncertainty
- Monte Carlo tab:
  - Sampling from normal/rectangular/triangular/U-shaped distributions
  - Histogram, normal-curve overlay, 95% interval, empirical 95% interval, median line
- Regression tab:
  - Multiple model management
  - x/u(x)/y data table
  - CSV text import (`x, u(x), y` or `x, y`)
  - Linear regression metrics and inverse estimation (`y0 -> x0, u(x0)`)
- Partial derivative tab (symbolic derivatives from equation)
- Unit validation tab (variable units and equation dimensional consistency)
- Document info tab (document metadata, Markdown description, CSV-based revision history)
- Report tab:
  - Budget + calculation summary for all calibration points
  - HTML export
  - CSS customization via `css/default.css` + `css/custom.css`
- Japanese/English UI switching and system-locale option
- JSON save/load of project data
- Startup splash screen and file-aware window title

## Batch Input Dialog Behavior
The batch input dialog (Tools -> Bulk Input) applies values across calibration points for non-result variables.

- Target rows:
  - Type B variables: `central_value`, `half_width`, `distribution`
  - Fixed variables: `central_value`
  - Type A and result variables are not included.
- Empty cells are ignored (existing value is kept).
- Number validation uses `Decimal`; invalid input blocks apply and shows a warning.
- When a Type B `distribution` is changed:
  - `degrees_of_freedom` is automatically set to `"inf"`.
  - `divisor` is auto-set:
    - Normal distribution: `"2"`
    - Other distributions: value from configured distribution divisor.
- When a Type B numeric value (`central_value` or `half_width`) is changed:
  - `degrees_of_freedom` is automatically set to `"inf"`.
  - `divisor` is auto-set by distribution (same rules as above).
  - If both `half_width` and `divisor` are valid and divisor is not zero:
    - `standard_uncertainty = half_width / divisor` is auto-calculated.

## Regression Tab Behavior
- Regression data is managed per model (add/copy/remove).
- Each model stores description, `x` unit, and `y` unit.
- Data table columns are `x`, `u(x)`, and `y`.
- CSV paste import is supported:
  - `x, u(x), y` or `x, y`
  - Fails when fewer than 2 valid points are provided
- Column-header click toggles ascending/descending sort.
- Main computed outputs:
  - intercept, slope, Significance F, residual standard deviation, `u(beta)`, and averages for `x`, `y`, `u(x)`, `u(y)`
- Inverse estimation table:
  - input column: `y0`
  - auto-calculated columns: `x0`, `u(x0)`
  - `x0` and `u(x0)` update when `y0` changes

## Correlation Matrix Editing Constraints
- Matrix is built only for input variables (result variables are excluded).
- Diagonal cells are always `1` and read-only.
- Only upper-triangle cells are editable.
- Lower-triangle cells mirror upper-triangle values and are read-only.
- Off-diagonal defaults are `0` (independent inputs).
- Values greater than `1` are rejected with a warning and reverted.

## Requirements
- Python 3.8+
- PySide6
- numpy
- sympy
- markdown

See `requirements.txt` for the install list.

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Or use:
- `setup.bat`

## Run
```bash
python -m src
```

Or use:
- `run.bat`

## Configuration
Main settings are in `config.ini`.

Important sections:
- `[Calculation]`:
  - `precision`
- `[CalibrationPoints]`:
  - `min_count`, `max_count`
- `[UncertaintyRounding]`:
  - `significant_digits`, `rounding_mode`
- `[Language]`:
  - `current`, `use_system_locale`
- `[Distribution]`:
  - distribution divisors used in Type B conversion
- `[TValues]`:
  - coverage-factor lookup table

## Data Save Format
Project files are saved as JSON and include:
- document info
- equations
- calibration points (`value_names`, selected index)
- variables and result variables
- correlation coefficients
- variable values
- regression models

## Project Structure
```text
src/
  __main__.py
  main.py
  main_window.py
  tabs/
  dialogs/
  utils/
  i18n/
css/
  default.css
  custom.css
tests/
```

## Tests
```bash
pytest
```

## License
MIT License. See `LICENSE`.

Third-party dependency licenses are documented in `THIRD_PARTY_LICENSES.md`.
