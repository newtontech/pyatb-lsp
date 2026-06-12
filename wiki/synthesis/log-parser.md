# Log Parser / 日志解析器

## Overview / 概述

Runtime log analysis capabilities for detecting errors in PyATB execution logs.
用于检测 PyATB 执行日志中错误的运行时日志分析功能。

## CLI Usage / CLI 使用

```bash
pyatb-log path/to/logfile
```

## Detected Patterns / 检测的模式

### Python Traceback / Python 追踪

**Pattern**: `Traceback (most recent call last):`
**Code**: PYATB-E075
**Severity**: error
**Confidence**: 0.95

```python
# Example log
Traceback (most recent call last):
  File "script.py", line 10, in <module>
    tb.run()
AttributeError: 'NoneType' object has no attribute 'run'
```

### Error Lines / 错误行

**Pattern**: `^Error: message`
**Code**: PYATB-E075
**Severity**: error
**Confidence**: 0.85

```
Error: HR.dat file not found
```

### File Not Found / 文件未找到

**Pattern**: `FileNotFoundError|No such file or directory`
**Code**: PYATB-E074
**Severity**: error
**Confidence**: 0.9

```
FileNotFoundError: [Errno 2] No such file or directory: 'HR.dat'
```

### Import Errors / 导入错误

**Pattern**: `ImportError|ModuleNotFoundError`
**Code**: PYATB-E071
**Severity**: error
**Confidence**: 0.9

```
ModuleNotFoundError: No module named 'pyatb'
```

### Runtime Crashes / 运行时崩溃

**Pattern**: `Segmentation fault|SIGSEGV|Aborted (core dumped)`
**Code**: PYATB-E075
**Severity**: error
**Confidence**: 0.95

```
Segmentation fault (core dumped)
```

## Programmatic API / 编程接口

```python
from pyatb_lsp.analyzer import parse_log_content

diagnostics = parse_log_content(log_text, file_path="run.log")
```

## Integration with LSP / 与 LSP 集成

The log parser is integrated into the LSP capabilities:
日志解析器集成到 LSP 能力中：

```json
{
  "capabilities": {
    "log_parser": true
  }
}
```

## Related Pages / 相关页面

- [Diagnostic Codes](diagnostic-codes.md)
- [Agent JSON](../concepts/agent-json.md)
