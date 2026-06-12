# LLM Wiki Plan / LLM Wiki 计划

**Project**: pyatb-lsp
**Domain**: PyATB (tight-binding materials simulation)
**Date**: 2025-06-12

## Wiki Structure / Wiki 结构

```
docs/
├── raw/                    # Source evidence / 原始证据
│   └── assets/
│       ├── README.md      # Original README
│       ├── DIAGNOSTIC_ENGINE_V1.md  # Diagnostic contract
│       ├── server.py      # LSP server implementation
│       ├── analyzer.py    # Static analyzer
│       └── complete_valid.py  # Valid PyATB example
├── wiki/                   # Synthesized knowledge / 综合知识
│   ├── entities/          # PyATB domain entities / PyATB领域实体
│   │   ├── tightbinding.md
│   │   ├── hr-sr-files.md
│   │   ├── kmesh-kpath.md
│   │   └── output-config.md
│   ├── concepts/          # Cross-cutting concepts / 跨领域概念
│   │   ├── lsp-architecture.md
│   │   ├── diagnostic-contract.md
│   │   ├── matmaster-workflow.md
│   │   └── agent-json.md
│   └── synthesis/        # API reference & workflows / API参考与工作流
│       ├── diagnostic-codes.md
│       ├── cli-reference.md
│       ├── code-actions.md
│       └── log-parser.md
├── index.md               # Navigation hub / 导航中心
└── log.md                 # Change log / 变更日志
```

## Content Plan / 内容计划

### Entities (实体)
1. **TightBinding Class**: Core PyATB class for tight-binding calculations
2. **HR/SR Files**: Hamiltonian and overlap real-space data files
3. **K-Mesh & K-Path**: Brillouin zone sampling specifications
4. **Output Configuration**: Output path and result directory handling

### Concepts (概念)
1. **LSP Architecture**: Language Server Protocol implementation pattern
2. **Diagnostic Contract**: Diagnostic Engine v1 specification
3. **MatMaster Workflow**: Scientific workflow execution constraints
4. **Agent JSON**: Machine-readable output for automated repair loops

### Synthesis (综合)
1. **Diagnostic Codes**: Complete PYATB-E0xx / PYATB-W0xx reference
2. **CLI Reference**: All CLI commands and usage patterns
3. **Code Actions**: Quick-fix actions for diagnostics
4. **Log Parser**: Runtime log analysis capabilities

## File Count: 20+ files / 20+ 文件

## Bilingual Format / 双语格式
- Chinese headings with English terms
- Technical terms preserved in English
- Code examples in original form


## 2026-06-12 Normalization

The canonical agent-discoverable layout is the repository root `raw/`, `wiki/`, `index.md`, and `log.md` structure registered by Bohrium. The older `docs/raw` and `docs/wiki` paths were migrated to the root layout.
