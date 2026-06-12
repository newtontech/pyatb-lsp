# TightBinding Class / TightBinding 类

## Overview / 概述

The `TightBinding` class is the core PyATB class for tight-binding calculations in materials science simulations.

`TightBinding` 类是 PyATB 中用于材料科学紧束缚计算的核心类。

## Construction / 构造

```python
import pyatb

tb = pyatb.TightBinding(hr_file='HR.dat', sr_file='SR.dat')
```

### Parameters / 参数

- **hr_file** (str): Path to Hamiltonian real-space file (HR.dat)
  - 哈密顿实空间文件路径
- **sr_file** (str, optional): Path to overlap real-space file (SR.dat)
  - 重叠实空间文件路径

## Common Operations / 常见操作

### Run Calculation / 运行计算

```python
tb.run()
```

### Access Results / 访问结果

```python
result = tb.result
eigvals = tb.eigvals
eigvecs = tb.eigvecs
```

### Check Convergence / 检查收敛

```python
if tb.converged:
    print("Calculation converged")
```

## LSP Integration / LSP 集成

The LSP provides:
- Hover documentation for `TightBinding`
- Completion for `tb`, `TB` variable names
- Diagnostics for missing `hr_file` references

LSP 提供：
- `TightBinding` 的悬停文档
- `tb`、`TB` 变量名的补全
- 缺少 `hr_file` 引用的诊断

## Related Entities / 相关实体

- [HR/SR Files](hr-sr-files.md)
- [K-Mesh & K-Path](kmesh-kpath.md)
