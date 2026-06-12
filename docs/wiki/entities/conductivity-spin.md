# Conductivity & Spin / 电导率与自旋

## Overview / 概述

Transport and spin-polarized calculations in PyATB.
PyATB 中的输运和自旋极化计算。

## Conductivity / 电导率

### Purpose / 用途

Compute optical or DC conductivity from electronic structure.
从电子结构计算光学或直流电导率。

### Usage / 使用

```python
tb.compute_conductivity()
```

### Keywords / 关键词

- `conductivity`: Optical/DC conductivity calculation
  - 光学/直流电导率计算
- `kernel`: Main solver kernel
  - 主求解器内核

## Spin-Polarized Calculations / 自旋极化计算

### Purpose / 用途

Handle spin-polarised systems and spin-orbit coupling.
处理自旋极化系统和自旋轨道耦合。

### Keywords / 关键词

- `spin`: Spin-polarised calculation flag or data
  - 自旋极化计算标志或数据
- `SOC`: Spin-orbit coupling flag or strength
  - 自旋轨道耦合标志或强度
- `soc`: Spin-orbit coupling (lowercase variant)
  - 自旋轨道耦合（小写变体）

### Usage / 使用

```python
tb = pyatb.TightBinding(hr_file="HR.dat", sr_file="SR.dat", spin=True)
tb.run()
```

## Fermi Level / 费米能级

### Keywords / 关键词

- `fermi`: Fermi level / Fermi energy
- `EF`: Fermi energy (abbreviation)
- `efermi`: Fermi energy attribute

### Usage / 使用

```python
fermi_level = tb.fermi
# or
fermi_level = tb.EF
```

## LSP Support / LSP 支持

The LSP keyword catalog includes these terms for completion and hover:
LSP 关键词目录包括这些术语用于补全和悬停：

- `conductivity`, `spin`, `SOC`, `soc`, `fermi`, `EF`, `efermi`

## Related Entities / 相关实体

- [TightBinding Class](tightbinding.md)
- [Band & DOS](band-dos.md)
