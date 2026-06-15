# Agent JSON / 代理 JSON

## Overview / 概述

Agent-facing JSON output enables automated check/repair/recheck loops.
面向代理的 JSON 输出支持自动检查/修复/再检查循环。

## Check Payload / 检查负载

```bash
pyatb-lsp-tool check path/to/input --format json
```

### Response Structure / 响应结构

```json
{
  "uri": "file:///path/to/input.py",
  "operation": "check",
  "ok": false,
  "version": "1.0",
  "software": "pyatb",
  "diagnostic_engine": "1.0",
  "diagnostics": [...],
  "summary": {
    "count": 3,
    "blocking": 2,
    "errors": 2,
    "warnings": 1
  },
  "capabilities": {
    "hover": true,
    "completion": true,
    "formatting": true,
    "code_actions": true,
    "diagnostics": true,
    "log_parser": true
  },
  "rule_codes": {
    "PYATB-E070": "Python syntax errors",
    "PYATB-E071": "Missing required imports",
    ...
  }
}
```

## Agent Operations / 代理操作

```bash
pyatb-lsp-tool check   # Diagnostics
pyatb-lsp-tool context # File context
pyatb-lsp-tool complete# Completion items
pyatb-lsp-tool hover   # Hover info
pyatb-lsp-tool symbols # Symbol list
pyatb-lsp-tool fix     # Apply fixes
```

## Repair Loop Pattern / 修复循环模式

```python
# 1. Check
result = pyatb_lsp_tool.check(file)

# 2. Filter blocking diagnostics
blocking = [d for d in result["diagnostics"] if d["blocking"]]

# 3. Apply fixes
for diag in blocking:
    apply_fix(diag["fix_hints"])

# 4. Recheck
result = pyatb_lsp_tool.check(file)

# 5. Confirm ok
assert result["ok"]
```

## Related Concepts / 相关概念

- [Diagnostic Contract](diagnostic-contract.md)
- [Diagnostic Codes](../synthesis/diagnostic-codes.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
