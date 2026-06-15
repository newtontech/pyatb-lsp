# Formatter Design / 格式化器设计

## Overview / 概述

The PyATB formatter is designed to be safe and idempotent.
PyATB 格式化器设计为安全且幂等。

## Safety Principles / 安全原则

### Preserve Python Statements / 保留 Python 语句

The formatter never modifies Python control flow:
格式化器从不修改 Python 控制流：

- `import`, `from` - Import statements
- `def`, `class` - Definitions
- `if`, `elif`, `else` - Conditionals
- `for`, `while` - Loops
- `try`, `except`, `finally` - Exception handling
- `with` - Context managers
- `return`, `raise` - Control flow

### Pass Through Unchanged / 原样传递

```python
# These lines are never modified
import pyatb
def calculate():
    if condition:
        for item in items:
            ...
```

## Alignment / 对齐

### Key=Value Alignment / 键值对齐

```python
# Before
hr_file="HR.dat"
output_path = "results/"

# After
hr_file                  = "HR.dat"
output_path              = "results/"
```

### Keyword-Parameter Alignment / 关键词参数对齐

```python
# Before
tb.compute_band(kpath="G-X")
tb.run()

# After
tb.compute_band          (kpath="G-X")
tb.run                    ()
```

## Idempotence / 幂等性

The formatter guarantees idempotent operation:
格式化器保证幂等操作：

```python
formatted_once = format_text(content)
formatted_twice = format_text(formatted_once)
assert formatted_once == formatted_twice
```

## Comments / 注释

Lines starting with comment prefixes are passed through unchanged:
以注释前缀开头的行原样传递：

```python
# This comment is unchanged
! Another comment unchanged
; Semicolon comments unchanged
```

## CLI Usage / CLI 使用

```bash
pyatb-fmt -w input.py
```

- `-w`: Write back to file (in-place modification)
  - 写回文件（就地修改）

## Related Concepts / 相关概念

- [LSP Architecture](lsp-architecture.md)
- [CLI Reference](../synthesis/cli-reference.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
