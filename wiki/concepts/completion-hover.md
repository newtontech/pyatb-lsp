# Completion & Hover / 补全与悬停

## Overview / 概述

IDE editor integration features for PyATB workflow scripts.
PyATB 工作流脚本的 IDE 编辑器集成功能。

## Keyword Catalog / 关键词目录

The LSP maintains a catalog of PyATB-specific keywords:
LSP 维护 PyATB 特定关键词的目录：

### Core Terms / 核心术语

- `pyatb` - PyATB tight-binding library
- `TightBinding` - Core class
- `TB` - Alias for TightBinding
- `hr_file`, `sr_file` - Data files
- `HR.dat`, `SR.dat` - Default file names

### Calculation Types / 计算类型

- `band` - Band structure
- `dos` - Density of states
- `conductivity` - Transport calculations

### Technical Terms / 技术术语

- `kmesh`, `kpath`, `kpoints` - k-point specifications
- `spin`, `SOC`, `soc` - Spin properties
- `fermi`, `EF`, `efermi` - Fermi level

### Output Terms / 输出术语

- `output`, `out_file`, `output_path`, `result_dir`

## Completion / 补全

### Triggering / 触发

Completion is triggered by typing prefix characters:
通过输入前缀字符触发补全：

```python
tb  # Shows: tb, TB, TightBinding
hr  # Shows: hr_file, HR.dat
ban # Shows: band
```

### Completion Item Kinds / 补全项种类

- `Keyword` - General keywords
- `Class` - Classes (TightBinding, TB)
- `Variable` - Variables (hr_file, sr_file)
- `File` - Files (HR.dat, SR.dat)

## Hover / 悬停

### Extended Documentation / 扩展文档

PyATB-specific symbols have rich hover documentation:
PyATB 特定符号有丰富的悬停文档：

```python
# Hover over "TightBinding" shows:
"""
**TightBinding**
PyATB core class for tight-binding calculations.

```python
import pyatb
tb = pyatb.TightBinding(hr_file='HR.dat', sr_file='SR.dat')
```

Requires `hr_file` (Hamiltonian) and optionally `sr_file` (overlap).
"""
```

### Keyword Hover / 关键词悬停

```python
# Hover over "hr_file" shows:
"""
**hr_file**
Path to the Hamiltonian real-space file (HR.dat).

Required for all tight-binding calculations in PyATB.
"""
```

## Python Builtins / Python 内置

The LSP provides limited hover for Python builtins:
LSP 为 Python 内置提供有限的悬停：

- `import` - Python import statement
- `from` - Python from...import construct

## Related Concepts / 相关概念

- [LSP Architecture](lsp-architecture.md)
- [TightBinding Class](../entities/tightbinding.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
