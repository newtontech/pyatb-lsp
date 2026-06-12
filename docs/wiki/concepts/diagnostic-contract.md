# Diagnostic Contract / 诊断规范

## Overview / 概述

pyatb-lsp implements the Diagnostic Engine v1 specification for agent-facing JSON output.
pyatb-lsp 实现了诊断引擎 v1 规范，用于面向代理的 JSON 输出。

## Severity Levels / 严重级别

| Level | Description | 描述 |
|-------|-------------|------|
| error | Blocks automated submission | 阻止自动提交 |
| warning | High-risk but may be intentional | 高风险但可能是有意的 |
| information | Style or optional facts | 样式或可选事实 |
| hint | Minor suggestions | 次要建议 |

## Categories / 类别

1. **syntax** - Python syntax errors
   - Python 语法错误
2. **schema** - Missing required elements
   - 缺失必需元素
3. **type/value** - Type or value issues
   - 类型或值问题
4. **cross-file reference** - File path references
   - 文件路径引用
5. **semantic consistency** - Logical consistency
   - 逻辑一致性
6. **preflight/runtime-risk** - Runtime error patterns
   - 运行时错误模式
7. **style/deprecation** - Style warnings
   - 样式警告

## Rich Diagnostic Shape / 丰富诊断形状

```json
{
  "diagnostic_engine": "1.0",
  "code": "PYATB-E071",
  "severity": "error",
  "category": "schema",
  "confidence": 0.95,
  "source": "pyatb-lsp",
  "range": {
    "start": {"line": 0, "character": 0},
    "end": {"line": 0, "character": 1}
  },
  "software": "pyatb",
  "file_type": "py",
  "path": "input.py",
  "message": "missing required import: 'pyatb'",
  "blocking": true
}
```

## Agent CLI / 代理 CLI

```bash
pyatb-lsp-tool check path/to/input --format json
```

Returns stable JSON for automated repair loops.
返回稳定的 JSON 用于自动修复循环。

## Related Concepts / 相关概念

- [LSP Architecture](lsp-architecture.md)
- [Agent JSON](agent-json.md)
