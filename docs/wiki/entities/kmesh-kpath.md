# K-Mesh & K-Path / K网格与K路径

## Overview / 概述

Brillouin zone sampling specifications for electronic structure calculations.
电子结构计算的布里渊区采样规范。

## K-Mesh (Monkhorst-Pack) / K网格

### Purpose / 用途

- Defines uniform k-point sampling across the Brillouin zone
  - 定义布里渊区的均匀 k 点采样
- Controls density of sampling points
  - 控制采样点密度

### Usage / 使用

```python
kmesh = [4, 4, 4]  # Monkhorst-Pack mesh
```

## K-Path / K路径

### Purpose / 用途

- Defines high-symmetry lines for band structure calculations
  - 定义带结构计算的高对称线
- Specifies sequence of k-points for band dispersion
  - 指定带色散的 k 点序列

### Usage / 使用

```python
kpath = "G-X-W-G-K-L"
```

## Band Structure Calculations / 带结构计算

```python
tb.compute_band(kpath=kpath)
```

## LSP Support / LSP 支持

The LSP provides:
- Keyword catalog for `kmesh`, `kpath`, `kpoints`
- Hover documentation for band structure terms

LSP 提供：
- `kmesh`、`kpath`、`kpoints` 的关键词目录
- 带结构术语的悬停文档

## Related Entities / 相关实体

- [TightBinding Class](tightbinding.md)
- [Output Configuration](output-config.md)
