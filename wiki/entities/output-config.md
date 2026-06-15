# Output Configuration / 输出配置

## Overview / 概述

PyATB workflows require explicit output path specification for reproducibility.
PyATB 工作流需要显式的输出路径规范以确保可重现性。

## Output Keywords / 输出关键词

The LSP recognizes these output-related keywords:
LSP 识别这些输出相关的关键词：

- **output**: Generic output directory or file
  - 通用输出目录或文件
- **out_file**: Output file path for results
  - 结果输出文件路径
- **output_path**: Explicit output directory path
  - 显式输出目录路径
- **result_dir**: Directory for storing calculation results
  - 存储计算结果的目录

## Usage Pattern / 使用模式

```python
output_path = "results/"
result_dir = "calculation_results/"
out_file = "band_structure.dat"
```

## LSP Diagnostics / LSP 诊断

### PYATB-W070: Missing Output Path

**Severity**: Warning
**Confidence**: 0.7

Triggered when no output keyword is found in the workflow.
当工作流中未找到输出关键词时触发。

### Quick Fix / 快速修复

```python
# LSP suggests adding:
output_path = "results/"
```

## Best Practices / 最佳实践

1. Always specify output path before running calculations
   - 始终在运行计算前指定输出路径
2. Use descriptive directory names
   - 使用描述性目录名称
3. Separate results by calculation type
   - 按计算类型分离结果

## Related Entities / 相关实体

- [TightBinding Class](tightbinding.md)
- [Diagnostic Codes](../synthesis/diagnostic-codes.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
