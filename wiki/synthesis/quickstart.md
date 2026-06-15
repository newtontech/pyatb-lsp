# Quick Start / 快速开始

## Installation / 安装

```bash
# Clone the repository
git clone https://github.com/newtontech/pyatb-lsp
cd pyatb-lsp

# Install with development dependencies
python -m pip install -e ".[dev]"
```

## Basic Usage / 基本用法

### LSP Server / LSP 服务器

Configure your editor to use `pyatb-lsp` for Python/PyATB files:
将编辑器配置为对 Python/PyATB 文件使用 `pyatb-lsp`：

```bash
pyatb-lsp --stdio
```

### Command Line Tools / 命令行工具

```bash
# Analyze a file
pyatb-lint script.py

# Format a file
pyatb-fmt -w script.py

# Run static tests
pyatb-test static ./case

# Parse a runtime log
pyatb-log run.log
```

### Agent Interface / 代理接口

```bash
# Get JSON diagnostics for automation
pyatb-lsp-tool check script.py --format json
```

## Valid PyATB Script / 有效的 PyATB 脚本

```python
import pyatb

# Configure tight-binding model
hr_file = "HR.dat"
sr_file = "SR.dat"
output_path = "results/"

# Create and run calculation
tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
```

## Expected Diagnostics / 预期诊断

For a valid script, no errors should be reported:
对于有效脚本，不应报告错误：

```bash
$ pyatb-lint valid_script.py --json
{
  "ok": true,
  "diagnostics": [],
  "summary": {"count": 0, "blocking": 0}
}
```

## Development / 开发

```bash
# Run all checks
make check

# Individual checks
make format    # ruff format
make lint      # ruff check
make typecheck # mypy src
make test      # pytest
```

## Next Steps / 下一步

- [LSP Architecture](../concepts/lsp-architecture.md)
- [Diagnostic Codes](diagnostic-codes.md)
- [CLI Reference](cli-reference.md)

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
