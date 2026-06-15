# HR/SR Files / HR和SR文件

## Overview / 概述

PyATB tight-binding calculations require two core data files:
PyATB 紧束缚计算需要两个核心数据文件：

1. **HR.dat** - Hamiltonian Real-space file
2. **SR.dat** - Overlap Real-space file

## File Formats / 文件格式

### HR.dat (Required / 必需)

- Contains the Hamiltonian matrix in real-space representation
  - 包含实空间表示的哈密顿矩阵
- Default filename: `HR.dat`
  - 默认文件名：`HR.dat`
- Specified via `hr_file` parameter
  - 通过 `hr_file` 参数指定

### SR.dat (Recommended / 推荐)

- Contains the overlap matrix in real-space representation
  - 包含实空间表示的重叠矩阵
- Default filename: `SR.dat`
  - 默认文件名：`SR.dat`
- Specified via `sr_file` parameter
  - 通过 `sr_file` 参数指定
- Optional but improves calculation accuracy
  - 可选但能提高计算精度

## Usage Patterns / 使用模式

```python
# Direct file reference
hr_file = "HR.dat"
sr_file = "SR.dat"

# Pass to TightBinding
tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
```

## LSP Diagnostics / LSP 诊断

The LSP enforces these MatMaster workflow rules:

- **PYATB-E072**: Missing `HR.dat` reference
- **PYATB-E072**: Missing `SR.dat` reference
- **PYATB-E074**: No tight-binding structure reference

LSP 强制执行这些 MatMaster 工作流规则。

## Related Entities / 相关实体

- [TightBinding Class](tightbinding.md)
- [Output Configuration](output-config.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
