# Uncertainty Calculation Support Software

## Overview

This software is a GUI application for calculating the uncertainty of measurement results.

It is based on JCGM 100 (Guide to the Expression of Uncertainty in Measurement, GUM).

Monte Carlo propagation of distributions is **not yet implemented**.

From the mathematical model equation of the measurement, the program derives the propagation equation of uncertainty, allows the user to input the value for each quantity, calculates the combined standard uncertainty, and outputs a budget sheet.

The software also supports batch calculations of calibration uncertainty across multiple calibration points following the same model equation.

## Main Features

1. Input and management of model equations and quantities
2. Input of measured values and their uncertainties
3. Automatic calculation of sensitivity coefficients
4. Automatic calculation of uncertainty propagation equations
5. Display and export of budget sheets
6. Linear regression tools for calibration data (model management, CSV import, inverse estimation)

## System Requirements

* Python 3.8 or higher
* PySide6 (LGPLv3 license)
* NumPy (BSD license)
* SymPy (BSD license)

## Installation

1. Clone the repository:

```bash
git clone [repository-url]
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the application:

```bash
python src/main.py
```

## Configuration (config.ini)

Application settings are stored in [`config.ini`](./config.ini). Key options include:

* **[Calculation]**
  * `precision`: Decimal precision used for calculation results.
* **[Defaults]**
  * `value_count`: Default number of values (calibration points) created per quantity.
  * `current_value_index`: Initially selected value index when editing quantities.
* **[CalibrationPoints]**
  * `min_count`, `max_count`: Minimum and maximum number of calibration points the UI allows.
* **[UncertaintyRounding]**
  * `significant_digits`: Significant digits shown for uncertainty values.
  * `rounding_mode`: Rounding strategy (`round_up` or `5_percent`).
* **[Language]**
  * `current`: UI language (`ja` or `en`).
  * `use_system_locale`: Whether to prefer the system locale over the configured language.
* **[Messages]**
  * `equation_change`: Message template displayed when the model equation requires variable updates.
* **[Distribution]**
  * `normal_distribution`, `rectangular_distribution`, `triangular_distribution`, `u_distribution`: Divisors used to convert interval values into standard uncertainties for each distribution type.
* **[TValues]**
  * A lookup table for coverage factors based on degrees of freedom (use `infinity` for infinite degrees of freedom).
* **[Version]**
  * `version`: Application version string shown in the UI and reports.

## Project Structure

```
src/
├── __main__.py         # Main entry point
├── main.py             # Main application
├── main_window.py      # Main window implementation
├── dialogs/            # Dialog window implementations
├── models/             # Data models
├── tabs/               # Tab-related modules
├── utils/              # Utility modules
└── widgets/            # Custom widgets
```

See the files within each directory for details.

## Calculation Background and Basis

### 1. Law of Propagation of Uncertainty

Based on the GUM, the following propagation equation is used:

**Note:** Currently, the calculation of correlated uncertainties between two quantities is not implemented.
Please prepare model equations where correlations can be ignored.

```
u²(y) = Σ(∂f/∂xᵢ)²u²(xᵢ) + 2ΣΣ(∂f/∂xᵢ)(∂f/∂xⱼ)u(xᵢ,xⱼ)
```

Where:

* u(y): uncertainty of the result
* ∂f/∂xᵢ: sensitivity coefficient
* u(xᵢ): uncertainty of input quantity
* u(xᵢ,xⱼ): correlated uncertainty

### 2. Sensitivity Coefficients

Sensitivity coefficients are calculated as the partial derivative of the model equation with respect to each input quantity:

```
∂f/∂xᵢ = lim(Δxᵢ→0) [f(x₁,...,xᵢ+Δxᵢ,...,xₙ) - f(x₁,...,xᵢ,...,xₙ)] / Δxᵢ
```

For coupled equations, the chain rule is used.

### 3. Types of Uncertainty

#### A-Type (Evaluated by Statistical Methods)

Based on repeated measurements:

1. Standard uncertainty (experimental standard deviation of the mean):

```
u = sqrt( (1 / (n * (n - 1))) * Σ(xᵢ - x̄)² )
```

2. Degrees of freedom:

```
ν = n - 1
```

#### B-Type (Evaluated by Other Means)

Based on non-statistical information (certificates, specs, literature, prior experience):

1. Rectangular distribution:

```
u = a / sqrt(3)
```

2. Triangular distribution:

```
u = a / sqrt(6)
```

3. Normal distribution:

```
u = a / k
```

where `a` is the confidence limit and `k` is the coverage factor (e.g., for 95% confidence, k ≈ 2).

### 4. Effective Degrees of Freedom

Welch-Satterthwaite formula:

```
ν_eff = u⁴(y) / Σ[u⁴(xᵢ) / νᵢ]
```

### 5. Expanded Uncertainty

Expanded using the coverage factor `k` (typically k = 2):

```
U = k * u(y)
```

Reference k values (approximate, from t-distribution):

| ν\_eff | 1     | 2    | 3    | 4    | 5    | 6    | 7    | 8    | 9    | 10   | 20   | 50   | ∞    |
| ------ | ----- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| k      | 12.71 | 4.30 | 3.18 | 2.78 | 2.57 | 2.45 | 2.36 | 2.31 | 2.26 | 2.23 | 2.09 | 2.01 | 1.96 |

For operational use, when ν\_eff is 10 or higher, the coverage factor is treated as 2.

## Usage

1. **Model Equation Input Tab**

   * Input the model equation (e.g., `W = V * I / R`).
   * Use `^` for exponentiation and `_` for subscripts.
   * Left-hand side is treated as the calculated result and is excluded from direct input.
   * Quantities are automatically parsed from the equation.
   * Multiple equations can be input, separated by commas (`,`). Newlines after commas are acceptable.
   * You can drag-and-drop quantities in the list to reorder the budget sheet display.

2. **Point Settings**

   * Set the name for each calibration point and add or remove calibration points as needed.

3. **Quantity Settings**

   * Input values for each quantity.
   * Adjust the number of calibration points; each quantity can have multiple values.
   * Specify the uncertainty type, unit, and description for each quantity.

4. **Partial Derivative**

   * Review the partial derivatives calculated from the model equation for each variable.

5. **Calculation Execution**

   * The "Uncertainty Calculation" tab creates a budget sheet for a selected calibration point.

6. **Regression**

   * Create, copy, and delete regression models and edit descriptions and x/y units.
   * Enter calibration data in a table with `x`, `u(x)`, and `y`; add/remove rows as needed.
   * Import CSV data by pasting text (`x, u(x), y` or `x, y` format; requires at least two points).
   * Review computed results: intercept, slope, Significance F (p-value), residual variance, means, and uncertainty terms.
   * Perform inverse estimation: input `y0` values and read back estimated `x0` and `u(x0)`; add/remove rows.
   * Formulas used in the calculations:

```text
Linear model: y = βx + α
Mean values: x̄ = (1/n) Σ xᵢ, ȳ = (1/n) Σ yᵢ
Sxx = Σ (xᵢ - x̄)²
β = Σ[(xᵢ - x̄)(yᵢ - ȳ)] / Sxx
α = ȳ - β x̄
Residuals: rᵢ = yᵢ - (β xᵢ + α)
Residual variance: s² = Σ rᵢ² / (n - 2)  (n ≥ 3), s = √s²
Significance F: SSR = Σ(ŷᵢ - ȳ)², SSE = Σ rᵢ², MSE = SSE/(n-2), F = SSR/MSE
u(β) = √(s² / Sxx)
ūx = (1/n) Σ u(xᵢ)
ūy = √(s² / n)
Inverse estimation: x₀ = (y₀ - ȳ)/β + x̄
u(x₀) = √( ūy²/β² + (y₀ - ȳ)² u(β)² / β⁴ + ūx² )
```

7. **Document Information**

   * The "Document Info" tab lets you record document metadata for reports, including document number, document name, version, and a description (Markdown supported).
   * Enter revision history as CSV rows (version, description, author, checker, approver, date) to include in generated reports.

8. **Report**

   * The "Report" function generates a batch budget for all calibration points of a selected result quantity.
   * Export results as HTML files.

## Notes

* Numeric display is rounded based on the `UncertaintyRounding` settings in `config.ini` and formatted with exponents in multiples of 3.
* Calculations use `Decimal` with the precision configured under `[Calculation]` in `config.ini`.
* Ensure model equations are structured to avoid correlations between quantities, as correlated uncertainty (covariance terms) is not yet supported.

## License

This software is released under the **MIT License**.
You are free to use, copy, modify, and redistribute it, provided the original copyright notice and license text are included.

For details, see the included [`LICENSE`](./LICENSE) file.

### Third-Party Libraries and Licenses

This software depends on the following external libraries (not included in the distribution; users must install via `pip` or similar):

| Library | License                   | URL                                                                                                     |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------- |
| PySide6 | LGPLv3 (© The Qt Company) | [Qt for Python](https://www.qt.io/qt-for-python) / [LGPLv3](https://www.gnu.org/licenses/lgpl-3.0.html) |
| NumPy   | BSD 3-Clause              | [NumPy](https://numpy.org/) / [BSD License](https://opensource.org/licenses/BSD-3-Clause)               |
| SymPy   | BSD 3-Clause              | [SymPy](https://www.sympy.org/) / [BSD License](https://opensource.org/licenses/BSD-3-Clause)           |

The Python standard library (e.g., json, decimal, re, math, traceback) is used under the [Python Software Foundation License](https://docs.python.org/3/license.html).

For detailed license terms, refer to the official sites or PyPI pages of each library.
