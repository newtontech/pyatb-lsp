# Validation Rules / 验证规则

## Overview / 概述

Static analysis rules enforced by the PyATB analyzer.
PyATB 分析器强制执行的静态分析规则。

## Rule Categories / 规则类别

### Syntax Rules / 语法规则

#### Rule: Python Syntax / Python 语法

- **Code**: PYATB-E070
- **Check**: Parse content with Python AST
- **Trigger**: SyntaxError exception
- **Confidence**: 1.0

### Schema Rules / 模式规则

#### Rule: Required Import / 必需导入

- **Code**: PYATB-E071
- **Check**: `pyatb` must be imported
- **Trigger**: Missing `import pyatb`
- **Confidence**: 0.95

#### Rule: Required Symbols / 必需符号

- **Code**: PYATB-E072
- **Check**: HR.dat and SR.dat must be referenced
- **Trigger**: Missing file references
- **Confidence**: 0.88

#### Rule: Structure Reference / 结构引用

- **Code**: PYATB-E074
- **Check**: Tight-binding structure must be referenced
- **Trigger**: No hr_file, HR.dat, or TightBinding reference
- **Confidence**: 0.9

#### Rule: JSON Schema / JSON 模式

- **Code**: PYATB-E073
- **Check**: JSON files must be valid
- **Trigger**: JSONDecodeError
- **Confidence**: 1.0

### Semantic Rules / 语义规则

#### Rule: Output Path / 输出路径

- **Code**: PYATB-W070
- **Check**: Output path should be specified
- **Trigger**: No output keyword found
- **Confidence**: 0.7

### Runtime Rules / 运行时规则

#### Rule: Traceback Detection / 追踪检测

- **Code**: PYATB-E075
- **Check**: Detect Python tracebacks in logs
- **Trigger**: "Traceback (most recent call last):" pattern
- **Confidence**: 0.95

## Rule Application / 规则应用

```python
# Analyzer applies rules in sequence:
1. Syntax check (blocks on error)
2. Import check
3. Symbol check
4. Structure check
5. Output check
6. Runtime pattern check
```

## Legacy Codes / 传统代码

For backward compatibility, legacy codes are emitted alongside new codes:
为向后兼容，传统代码与新代码一起发出：

- PYATB001 → PYATB-E070
- PYATB101 → PYATB-E071
- PYATB102 → PYATB-E072

## Related Pages / 相关页面

- [Diagnostic Codes](diagnostic-codes.md)
- [MatMaster Workflow](../concepts/matmaster-workflow.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
