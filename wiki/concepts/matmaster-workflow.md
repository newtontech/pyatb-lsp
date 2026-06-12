# MatMaster Workflow / MatMaster 工作流

## Overview / 概述

PyATB scripts are used within MatMaster scientific workflow automation.
PyATB 脚本用于 MatMaster 科学工作流自动化中。

## MatMaster Execution Rules / MatMaster 执行规则

### Required References / 必需引用

```python
MATMASTER_REQUIRED_REFERENCES = ["HR.dat"]
MATMASTER_OPTIONAL_REFERENCES = ["SR.dat"]
```

### Structure References / 结构引用

```python
MATMASTER_STRUCTURE_REFERENCES = [
    "hr_file", "sr_file",
    "HR.dat", "SR.dat",
    "TightBinding", "TB",
]
```

### Output Keywords / 输出关键词

```python
MATMASTER_OUTPUT_KEYWORDS = [
    "output", "out_file",
    "output_path", "result_dir",
]
```

## Golden Test Cases / 黄金测试用例

The analyzer validates against MatMaster golden test constraints:
分析器根据 MatMaster 黄金测试约束进行验证：

1. HR.dat must be referenced
   - 必须引用 HR.dat
2. Structure reference must exist
   - 必须存在结构引用
3. Output path should be specified
   - 应指定输出路径

## Valid Example / 有效示例

```python
import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"
output_path = "results/"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
```

## LSP Enforcement / LSP 强制执行

The LSP emits diagnostics when MatMaster rules are violated:
当违反 MatMaster 规则时，LSP 发出诊断：

- PYATB-E072: Missing required symbols
- PYATB-E074: Missing structure reference
- PYATB-W070: Missing output path

## Related Concepts / 相关概念

- [LSP Architecture](lsp-architecture.md)
- [Diagnostic Contract](diagnostic-contract.md)
