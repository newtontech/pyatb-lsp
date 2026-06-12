# Testing Strategy / 测试策略

## Overview / 概述

Testing approach for pyatb-lsp using pytest with fixture-based test cases.
使用 pytest 和基于夹具的测试用例的 pyatb-lsp 测试方法。

## Test Structure / 测试结构

```
tests/
├── fixtures/          # Test input files
│   ├── complete_valid.py
│   ├── missing_import.py
│   ├── missing_symbols.py
│   ├── syntax_error.py
│   └── ...
├── test_analyzer.py   # Analyzer tests
├── test_server.py      # LSP server tests
├── test_cli.py         # CLI tool tests
└── test_diagnostics.py # Diagnostic tests
```

## Fixture Categories / 夹具类别

### Valid Scripts / 有效脚本

**complete_valid.py**: Reference valid PyATB script
```python
import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"
output_path = "results/"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
```

### Error Cases / 错误用例

- **missing_import.py**: Tests PYATB-E071
- **missing_symbols.py**: Tests PYATB-E072
- **syntax_error.py**: Tests PYATB-E070
- **missing_output.py**: Tests PYATB-W070

## Test Commands / 测试命令

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_analyzer.py

# Run with verbose output
pytest -v
```

## Test Organization / 测试组织

### Unit Tests / 单元测试

Test individual functions and modules:
测试单个函数和模块：

```python
def test_analyze_valid_file():
    """Test that valid files produce no blocking diagnostics."""
    diagnostics = analyze_file(fixture_path("complete_valid.py"))
    blocking = [d for d in diagnostics if d.severity == "error"]
    assert len(blocking) == 0
```

### Integration Tests / 集成测试

Test LSP server interactions:
测试 LSP 服务器交互：

```python
def test_server_did_open():
    """Test that opening a file triggers diagnostics."""
    server = create_server()
    server.did_open(params)
    # Verify diagnostics were published
```

## CI/CD Integration / CI/CD 集成

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --cov=src

- name: Type check
  run: mypy src

- name: Lint
  run: ruff check src tests
```

## Related Pages / 相关页面

- [CLI Reference](../synthesis/cli-reference.md)
- [Validation Rules](../synthesis/validation-rules.md)
