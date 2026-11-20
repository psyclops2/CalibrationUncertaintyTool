"""Shared correlation validation for GUM and Monte Carlo calculations."""
import numpy as np


def validate_correlation_matrix(matrix):
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("相関行列は正方行列である必要があります。")
    if not np.all(np.isfinite(matrix)) or np.any(np.abs(matrix) > 1):
        raise ValueError("相関係数は有限な−1〜1の数値にしてください。")
    if not np.allclose(matrix, matrix.T, atol=1e-12, rtol=0) or not np.allclose(np.diag(matrix), 1):
        raise ValueError("相関行列は対称で対角要素が1である必要があります。")
    if matrix.size and np.linalg.eigvalsh(matrix).min() < -1e-10:
        raise ValueError("相関係数の組合せが成立しません（行列が半正定値ではありません）。相関設定を確認してください。")
    return matrix


def build_correlation_matrix(variables, coefficients):
    if not isinstance(coefficients, dict):
        raise ValueError("相関設定は辞書形式である必要があります。")
    matrix = np.eye(len(variables))
    for i, first in enumerate(variables):
        row = coefficients.get(first, {})
        if not isinstance(row, dict):
            raise ValueError(f"相関設定 {first}: 不正な行です。")
        if first in row and float(row[first]) != 1:
            raise ValueError(f"相関設定 {first}: 対角要素は1にしてください。")
        for j in range(i + 1, len(variables)):
            second = variables[j]
            reverse = coefficients.get(second, {})
            if not isinstance(reverse, dict):
                raise ValueError(f"相関設定 {second}: 不正な行です。")
            value = float(row.get(second, reverse.get(first, 0)))
            if second in row and first in reverse and abs(value - float(reverse[first])) > 1e-12:
                raise ValueError("相関行列の上下の値が一致しません。")
            matrix[i, j] = matrix[j, i] = value
    return validate_correlation_matrix(matrix)
