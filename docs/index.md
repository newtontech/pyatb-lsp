# PyATB LSP Wiki / PyATB LSP 知识库

**Version**: 0.1.0
**Domain**: PyATB (tight-binding materials simulation)
**Last Updated**: 2025-06-12

## About / 关于

This wiki provides comprehensive documentation for the pyatb-lsp project, a Language Server Protocol implementation for PyATB workflow scripts used in MatMaster scientific automation.
本知识库为 pyatb-lsp 项目提供全面文档，该项目是在 MatMaster 科学自动化中使用的 PyATB 工作流脚本的语言服务器协议实现。

## Navigation / 导航

### Getting Started / 入门

- [Quick Start](wiki/synthesis/quickstart.md) - Installation and basic usage
  - 安装和基本用法

### Domain Entities / 领域实体

Core PyATB concepts and data structures:
核心 PyATB 概念和数据结构：

- [TightBinding Class](wiki/entities/tightbinding.md) - Core PyATB class
  - PyATB 核心类
- [HR/SR Files](wiki/entities/hr-sr-files.md) - Data file requirements
  - 数据文件要求
- [K-Mesh & K-Path](wiki/entities/kmesh-kpath.md) - Brillouin zone sampling
  - 布里渊区采样
- [Output Configuration](wiki/entities/output-config.md) - Output path handling
  - 输出路径处理
- [Band & DOS](wiki/entities/band-dos.md) - Electronic structure calculations
  - 电子结构计算
- [Conductivity & Spin](wiki/entities/conductivity-spin.md) - Transport and spin calculations
  - 输运和自旋计算

### Concepts / 概念

Cross-cutting architectural and design concepts:
跨领域的架构和设计概念：

- [LSP Architecture](wiki/concepts/lsp-architecture.md) - Language Server implementation
  - 语言服务器实现
- [Diagnostic Contract](wiki/concepts/diagnostic-contract.md) - Diagnostic Engine v1 specification
  - 诊断引擎 v1 规范
- [MatMaster Workflow](wiki/concepts/matmaster-workflow.md) - Scientific workflow constraints
  - 科学工作流约束
- [Agent JSON](wiki/concepts/agent-json.md) - Machine-readable output
  - 机器可读输出
- [Formatter Design](wiki/concepts/formatter-design.md) - Safe formatting strategy
  - 安全格式化策略
- [Completion & Hover](wiki/concepts/completion-hover.md) - Editor integration features
  - 编辑器集成功能
- [Testing Strategy](wiki/concepts/testing-strategy.md) - Test organization and fixtures
  - 测试组织和夹具

### Synthesis / 综合

API references and workflows:
API 参考和工作流：

- [Diagnostic Codes](wiki/synthesis/diagnostic-codes.md) - Complete PYATB-E/W code reference
  - 完整的 PYATB-E/W 代码参考
- [CLI Reference](wiki/synthesis/cli-reference.md) - Command-line tools
  - 命令行工具
- [Code Actions](wiki/synthesis/code-actions.md) - Quick-fix actions
  - 快速修复操作
- [Log Parser](wiki/synthesis/log-parser.md) - Runtime log analysis
  - 运行时日志分析
- [Validation Rules](wiki/synthesis/validation-rules.md) - Static analysis rules
  - 静态分析规则

## Raw Sources / 原始来源

Source evidence files are preserved in [raw/assets/](raw/assets/).
原始证据文件保存在 raw/assets/ 中。

- README.md
- DIAGNOSTIC_ENGINE_V1.md
- server.py
- analyzer.py
- complete_valid.py

## Change Log / 变更日志

See [log.md](log.md) for wiki modification history.
查看 log.md 了解 Wiki 修改历史。

---

**Total Files**: 24 wiki pages + raw assets + index + log
**总文件数**：24 个 Wiki 页面 + 原始资源 + 索引 + 日志
