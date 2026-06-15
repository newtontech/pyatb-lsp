# CLI Reference / CLI 参考

## Overview / 概述

Complete command-line interface reference for pyatb-lsp tools.
pyatb-lsp 工具的完整命令行接口参考。

## LSP Server / LSP 服务器

```bash
pyatb-lsp --stdio
```

**Purpose**: Language Server Protocol server
**Use**: Editor integration (VS Code, Neovim, etc.)

## Linter / 代码检查

```bash
pyatb-lint ./case --json
```

**Purpose**: Static analysis and diagnostics
**Options**:
- `--json`: JSON output format
- Directory or file path argument

**Output**: Diagnostic JSON with LSP shape

## Formatter / 格式化工具

```bash
pyatb-fmt -w input.file
```

**Purpose**: Safe idempotent formatting
**Options**:
- `-w`: Write back to file (in-place)
- File path argument

**Behavior**:
- Aligns key=value pairs
- Preserves Python statements
- Idempotent operation

## Tester / 测试工具

```bash
pyatb-test static ./case --json
```

**Purpose**: Run static tests
**Options**:
- `--json`: JSON output format
- Directory or file path argument

## Agent Tool / 代理工具

```bash
pyatb-lsp-tool check path/to/input --format json
pyatb-lsp-tool context path/to/input --format json
pyatb-lsp-tool complete path/to/input --format json
pyatb-lsp-tool hover path/to/input --format json
pyatb-lsp-tool symbols path/to/input --format json
pyatb-lsp-tool fix path/to/input --format json
```

**Purpose**: Machine-readable JSON output for agents
**Options**:
- `--format json`: JSON output format
- Operation: check, context, complete, hover, symbols, fix

## Log Parser / 日志解析器

```bash
pyatb-log path/to/logfile
```

**Purpose**: Parse runtime logs and extract error diagnostics
**Output**: Diagnostics from traceback patterns and error markers

## Installation / 安装

```bash
python -m pip install -e ".[dev]"
```

## Development Commands / 开发命令

```bash
make format    # ruff format
make lint      # ruff check
make typecheck # mypy src
make test      # pytest
make check     # All checks
```

## Related Pages / 相关页面

- [LSP Architecture](../concepts/lsp-architecture.md)
- [Agent JSON](../concepts/agent-json.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
