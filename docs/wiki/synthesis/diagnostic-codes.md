# Diagnostic Codes / 诊断代码

## Overview / 概述

Complete reference for all PYATB-prefixed diagnostic codes.
所有 PYATB 前缀诊断代码的完整参考。

## Syntax Errors / 语法错误

### PYATB-E070

**Description**: Python syntax errors
**Severity**: error
**Confidence**: 1.0
**Category**: syntax

```python
# Invalid syntax
tb = pyatb.TightBinding[  # Missing closing bracket
```

**Evidence**: Python AST parser failed
**Fix**: Correct the syntax error

### Legacy Code / 传统代码

PYATB001 - Same as PYATB-E070

## Import Errors / 导入错误

### PYATB-E071

**Description**: Missing required import: `pyatb`
**Severity**: error
**Confidence**: 0.95
**Category**: schema

```python
# Missing import
hr_file = "HR.dat"  # No "import pyatb"
```

**Evidence**: MatMaster execution contracts require pyatb import
**Fix**: Add `import pyatb`

### Legacy Code / 传统代码

PYATB101 - Same as PYATB-E071 (warning severity)

## Symbol Errors / 符号错误

### PYATB-E072

**Description**: Missing required symbol: `HR.dat` or `SR.dat`
**Severity**: error
**Confidence**: 0.88
**Category**: schema

**Evidence**: MatMaster golden tests require reference to these files
**Fix**: Add symbol reference

### Legacy Code / 传统代码

PYATB102 - Same as PYATB-E072 (warning severity)

## Structure Errors / 结构错误

### PYATB-E074

**Description**: No tight-binding structure reference
**Severity**: error
**Confidence**: 0.9
**Category**: schema

```python
# Missing structure reference
import pyatb
# No hr_file, HR.dat, or TightBinding reference
```

**Evidence**: MatMaster requires a structure reference for valid execution
**Fix**: Add `hr_file`, `TightBinding`, or `TB` reference

## JSON Errors / JSON 错误

### PYATB-E073

**Description**: Invalid JSON in configuration files
**Severity**: error
**Confidence**: 1.0
**Category**: syntax

**Evidence**: JSON parser failed
**Fix**: Correct JSON syntax

## Output Warnings / 输出警告

### PYATB-W070

**Description**: No output path specified
**Severity**: warning
**Confidence**: 0.7
**Category**: semantic consistency

**Evidence**: MatMaster best practice: explicit output path for reproducibility
**Fix**: Add `output_path = "results/"`

## Runtime Errors / 运行时错误

### PYATB-E075

**Description**: Runtime log traceback detected
**Severity**: error
**Confidence**: 0.95
**Category**: preflight/runtime-risk

**Evidence**: Log parser detected Python traceback
**Fix**: Investigate the traceback

## Related Pages / 相关页面

- [Code Actions](code-actions.md)
- [Log Parser](log-parser.md)
