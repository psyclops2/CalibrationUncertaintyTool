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

## Usage

1. **Model Equation Input Tab**

   * Input the model equation (e.g., `W = V * I / R`).
   * Use `^` for exponentiation and `_` for subscripts.
   * Left-hand side is treated as the calculated result and is excluded from direct input.
   * Quantities are automatically parsed from the equation.
   * Multiple equations can be input, separated by commas (`,`). Newlines after commas are acceptable.
   * You can drag-and-drop quantities in the list to reorder the budget sheet display.

2. **Quantity Settings**

   * Input values for each quantity.
   * Adjust the number of calibration points; each quantity can have multiple values.
   * Specify the uncertainty type, unit, and description for each quantity.

3. **Calculation Execution**

   * The "Uncertainty Calculation" tab creates a budget sheet for a selected calibration point.

4. **Report**

   * The "Report" function generates a batch budget for all calibration points of a selected result quantity.
   * Export results as HTML files.

## Notes

* Numerical display uses internal rounding to 9 significant digits and exponent multiples of 3.
* Internal calculations use full `float` precision without rounding.
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
