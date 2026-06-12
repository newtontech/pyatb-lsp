# LSP Architecture / LSP 架构

## Overview / 概述

pyatb-lsp implements the Language Server Protocol for PyATB workflow scripts using pygls.
pyatb-lsp 使用 pygls 为 PyATB 工作流脚本实现语言服务器协议。

## Server Implementation / 服务器实现

```python
class PyATBServer(LanguageServer):
    """Language Server for PyATB workflow scripts."""
```

## Capabilities / 能力

### Diagnostics / 诊断

- Full diagnostic push on open/change
  - 打开/更改时的完整诊断推送
- Real-time error detection
  - 实时错误检测
- Syntax and semantic analysis
  - 语法和语义分析

### Hover / 悬停

```python
def hover(params: HoverParams) -> Hover | None:
    """Return hover documentation for symbols."""
```

- Keyword catalog hover
  - 关键词目录悬停
- Python builtin hover
  - Python 内置悬停
- PyATB-specific documentation
  - PyATB 特定文档

### Completion / 补全

```python
def completion(params: CompletionParams) -> CompletionList:
    """Provide completion items based on prefix."""
```

- PyATB keyword completion
  - PyATB 关键词补全
- Symbol name suggestions
  - 符号名建议

### Formatting / 格式化

```python
def formatting(params: DocumentFormattingParams) -> list[dict]:
    """Format document using safe formatter."""
```

- Safe idempotent formatter
  - 安全的幂等格式化器
- Preserves Python statements
  - 保留 Python 语句
- Aligns key=value pairs
  - 对齐键值对

### Code Actions / 代码操作

```python
def code_action(params: CodeActionParams) -> list[CodeAction]:
    """Generate quick-fix actions for diagnostics."""
```

- Add missing imports
  - 添加缺失的导入
- Add missing symbols
  - 添加缺失的符号
- Add output path
  - 添加输出路径

## Entry Points / 入口点

```bash
pyatb-lsp --stdio              # LSP server
pyatb-lint ./case --json       # Linter
pyatb-fmt -w input.file        # Formatter
pyatb-test static ./case       # Tester
```

## Related Concepts / 相关概念

- [Diagnostic Contract](diagnostic-contract.md)
- [MatMaster Workflow](matmaster-workflow.md)
