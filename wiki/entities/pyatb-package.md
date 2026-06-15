# Entity: PYATB Package

**Type:** Software package
**Version:** 1.1.2 (Dec 3, 2025)
**License:** GPL-3.0
**Repository:** https://github.com/pyatb/pyatb

## Identity

PYATB (Python ab initio tight binding simulation package) computes electronic structures and related properties from ab initio tight-binding Hamiltonians. The Hamiltonian is obtained from DFT codes using numerical atomic orbital (NAO) bases, primarily ABACUS.

## Authors

Gan Jin, Hongsheng Pang, Yuyang Ji, Zujian Dai, Xudong Zhu -- supervised by Prof. Lixin He, USTC.

## Modules

| Module | Purpose | Key Calculations |
|--------|---------|-----------------|
| **Bands** | Electronic structure | Band structure, DOS, PDOS, fat bands, Fermi surface, band unfolding, spin texture, surface states |
| **Geometric** | Berry phase properties | AHC, SHC, ANC, Chern number, Wilson loop, Berry curvature, polarization, orbital magnetization |
| **Optical** | Linear and nonlinear optics | Optical conductivity, shift current, SHG, BCD, CPGE, Drude weight, JDOS |
| **Transport** | Boltzmann transport | Conductivity, Seebeck, thermal conductivity, mobility, effective mass |

## Technical Stack

- Python 71%, C++ 28% (Eigen-based solvers)
- MPI parallel (distributed k-points)
- OpenMP threads (within-process parallelism)
- PyPI wheels for Linux x86_64, Python 3.8-3.14

## Input Requirements

Three matrix files from DFT:
- H(R) -- Hamiltonian in real space
- S(R) -- Overlap matrix in real space
- r(R) -- Position/dipole matrix in real space (not needed for all calculations)

Plus an `Input` control file with block-structured parameters.

## Key Papers

- Gan Jin et al., CPC 291 (2023) 108844. DOI: 10.1016/j.cpc.2023.108844

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
