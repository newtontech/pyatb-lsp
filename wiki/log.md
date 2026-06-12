# Ingest Log

## Session: 2026-06-12

### Sources Collected

| # | File | Source URL | Method |
|---|------|-----------|--------|
| 1 | pyatb-readme.md | https://github.com/pyatb/pyatb | Web reader + gh API |
| 2 | pyatb-introduction.md | https://pyatb.github.io/pyatb/introduction.html | Web reader |
| 3 | pyatb-input-reference.md | https://github.com/pyatb/pyatb/blob/main/src/pyatb/io/default_input.py | gh API (base64 decode) |
| 4 | pyatb-examples.md | https://github.com/pyatb/pyatb/tree/main/examples, /tutorial | gh API (multiple Input files) |
| 5 | pyatb-theory.md | https://arxiv.org/abs/2303.18004 + pyatb docs | Web reader + synthesis |
| 6 | pyatb-abacus-integration.md | http://abacus.deepmodeling.com/en/latest/advanced/interface/pyatb.html | Web reader |
| 7 | pyatb-transport-implementation.md | https://github.com/pyatb/pyatb/blob/main/src/pyatb/transport/boltz_transport.py | gh API (base64 decode) |
| 8 | pyatb-related-tools.md | Web search compilation | Multiple search queries |

### Coverage Assessment

- **Input file format:** Complete (all parameters from default_input.py source code)
- **Examples:** All 14 example materials + 11 tutorial materials covered
- **Transport module:** Full source code analysis of boltz_transport.py
- **Theory:** Key equations from arXiv paper and source code
- **ABACUS integration:** Complete workflow documented
- **Missing:** No live documentation site pages for individual functions (site returned 404 for subpages)

### Wiki Pages Created

- wiki/index.md
- wiki/entities/pyatb-package.md
- wiki/concepts/boltzmann-transport.md
- wiki/concepts/berry-phase-geometry.md
- wiki/concepts/input-file-format.md
- wiki/concepts/abacus-integration.md
- wiki/synthesis/transport-coefficient-guide.md
