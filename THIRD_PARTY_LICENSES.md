# THIRD‑PARTY LICENSES / NOTICE

このファイルは、本ソフトウェアが **リンク／実行時に依存するものの、配布物には含まれない** 外部ライブラリの著作権表示およびライセンス情報をまとめたものです。実行前に利用者ご自身で各ライブラリをインストールしてください。

---

## 1. PySide6

| 項目     | 内容                                                                      |
| ------ | ----------------------------------------------------------------------- |
| バージョン例 | 6.\* 系（開発時に確認）                                                          |
| 配布元    | [https://www.qt.io/qt-for-python](https://www.qt.io/qt-for-python)      |
| ライセンス  | **GNU Lesser General Public License v3.0 or later (LGPL‑3.0‑or‑later)** |
| 著作権者   | © 2016 – 2025 The Qt Company Ltd.                                       |

PySide6 は Qt ランタイムを Python から利用可能にする公式バインディングです。LGPL に従い、動的リンク形態であれば本ソフトウェアと組み合わせて利用できます。

> **LGPL‑3.0 全文**は [https://www.gnu.org/licenses/lgpl-3.0.html](https://www.gnu.org/licenses/lgpl-3.0.html) を参照してください。

---

## 2. NumPy

| 項目     | 内容                                       |
| ------ | ---------------------------------------- |
| バージョン例 | 1.26.\*                                  |
| 配布元    | [https://numpy.org/](https://numpy.org/) |
| ライセンス  | **BSD 3‑Clause License**                 |
| 著作権者   | © 2005 – 2025 NumPy Developers           |

### BSD 3‑Clause License 全文

```
Copyright (c) 2005-2025, NumPy Developers
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. Neither the name of the NumPy Developers nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```

---

## 3. SymPy

| 項目     | 内容                                               |
| ------ | ------------------------------------------------ |
| バージョン例 | 1.12.\*                                          |
| 配布元    | [https://www.sympy.org/](https://www.sympy.org/) |
| ライセンス  | **BSD 3‑Clause License**                         |
| 著作権者   | © 2006 – 2025 SymPy Development Team             |

> SymPy は BSD 3‑Clause ライセンスで配布されています。ライセンス本文は NumPy と同一であるため省略し、上記 NumPy 節の BSD 3‑Clause License テキストが適用されます。

---

## 4. Python 標準ライブラリ

* **ライセンス:** Python Software Foundation License 2.0（PSF‑2.0）
* **著作権者:** © 2001 – 2025 Python Software Foundation
* **参照 URL:** [https://docs.python.org/3/license.html](https://docs.python.org/3/license.html)

標準ライブラリのモジュール (json, decimal, re, math, traceback 等) は CPython 配布物に含まれるものであり、本ソフトウェアはこれらをそのまま利用しています。

---

## 5. SPDX サマリ

```
PySide6                LGPL-3.0-or-later
NumPy                  BSD-3-Clause
SymPy                  BSD-3-Clause
python-stdlib          Python-2.0
```

---

### 免責 / Disclaimer

本ファイルはライセンス義務の履行と透明性のために提供していますが、当プロジェクトはこれら外部ライブラリを再頒布していません。ライブラリを本ソフトウェアと共に再配布する場合は、各ライセンスの追加義務（LGPL §4〜§6 など）を遵守してください。
