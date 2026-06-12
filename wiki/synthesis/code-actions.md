# Code Actions / 代码操作

## Overview / 概述

Quick-fix actions provided by the LSP for PyATB diagnostics.
LSP 为 PyATB 诊断提供的快速修复操作。

## Add Missing Import / 添加缺失的导入

### Triggered By / 触发条件

- PYATB-E071: Missing required import
- PYATB101: Legacy import warning

### Action / 操作

```python
# Before
hr_file = "HR.dat"

# After
import pyatb
hr_file = "HR.dat"
```

### Code Action Kind / 代码操作类型

`CodeActionKind.QuickFix`

## Add HR.dat Reference / 添加 HR.dat 引用

### Triggered By / 触发条件

- PYATB-E072: Missing HR.dat symbol
- PYATB-E074: Missing structure reference

### Action / 操作

```python
# After imports
hr_file = "HR.dat"
```

## Add SR.dat Reference / 添加 SR.dat 引用

### Triggered By / 触发条件

- PYATB-E072: Missing SR.dat symbol

### Action / 操作

```python
# After imports
sr_file = "SR.dat"
```

## Add Output Path / 添加输出路径

### Triggered By / 触发条件

- PYATB-W070: Missing output path

### Action / 操作

```python
# At end of file
output_path = "results/"
```

## Show Syntax Error Details / 显示语法错误详情

### Triggered By / 触发条件

- PYATB-E070: Python syntax error

### Action / 操作

Displays diagnostic message with syntax error details.
显示包含语法错误详情的诊断消息。

## Insertion Logic / 插入逻辑

The LSP inserts code actions at appropriate locations:
LSP 在适当位置插入代码操作：

1. After imports for structure references
   - 在导入后插入结构引用
2. At end of file for output paths
   - 在文件末尾插入输出路径
3. At top of file for imports
   - 在文件顶部插入导入

## Related Pages / 相关页面

- [Diagnostic Codes](diagnostic-codes.md)
- [LSP Architecture](../concepts/lsp-architecture.md)
