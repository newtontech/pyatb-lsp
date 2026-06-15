# Band & DOS Calculations / 能带与DOS计算

## Overview / 概述

Electronic structure calculations for band structure and density of states.
用于能带结构和态密度的电子结构计算。

## Band Structure / 能带结构

### Purpose / 用途

Calculate energy eigenvalues along high-symmetry k-point paths.
沿高对称 k 点路径计算能量本征值。

### Usage / 使用

```python
tb.compute_band(kpath="G-X-W-G-K-L")
result = tb.result
eigvals = tb.eigvals
```

### Keywords / 关键词

- `band`: Band structure calculation
  - 能带结构计算
- `kpath`: High-symmetry k-point path
  - 高对称 k 点路径
- `eigvals`: Eigenvalues from calculation
  - 计算得到的本征值

## Density of States / 态密度

### Purpose / 用途

Compute electronic density of states across the Brillouin zone.
计算布里渊区上的电子态密度。

### Usage / 使用

```python
tb.compute_dos()
result = tb.result
```

### Keywords / 关键词

- `dos`: Density of states calculation
  - 态密度计算

## LSP Support / LSP 支持

The LSP provides hover documentation for these terms:
LSP 为这些术语提供悬停文档：

- `band` - Band structure calculation
- `dos` - Density of states calculation
- `eigvals` - Eigenvalues
- `eigvecs` - Eigenvectors
- `weight` - K-point weights

## Related Entities / 相关实体

- [K-Mesh & K-Path](kmesh-kpath.md)
- [TightBinding Class](tightbinding.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
