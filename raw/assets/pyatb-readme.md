# PYATB - README

**Source:** https://github.com/pyatb/pyatb
**Retrieved:** 2026-06-12
**Version:** v1.1.2 (latest release, Dec 3 2025)
**License:** GPL-3.0

## Overview

PYATB (Python ab initio tight binding simulation package) is an open-source software package for computing electronic structures and related properties based on the ab initio tight binding Hamiltonian. The Hamiltonian is directly obtained after conducting self-consistent calculations with first-principles packages using numerical atomic orbital (NAO) bases, such as ABACUS.

## Repository Structure

```
pyatb/
├── .github/workflows/
├── doc/                    # Documentation source
├── eigen/                  # Eigen library (submodule)
├── examples/               # Example calculations
│   ├── Bi2Se3/            # Band structure, Wilson loop, spin texture
│   ├── CsPbI3/            # Optical conductivity
│   ├── Cu/                # Fermi energy, Fermi surface
│   ├── Fe/                # Berry curvature, AHC
│   ├── GaAs/              # SHG
│   ├── MnBi2Te4-weyl/
│   ├── MnSbTe4/
│   ├── NV/                # Band unfolding
│   ├── PbTiO3/            # Polarization
│   ├── Si2/               # Fat band, PDOS, JDOS, optical conductivity
│   ├── Te/                # Berry curvature dipole
│   ├── WS2/               # Shift current
│   └── fcc-Ni/            # Orbital magnetization
├── src/
│   ├── cpp/               # C++ backend (Eigen-based solvers)
│   └── pyatb/             # Python package
│       ├── berry/         # Berry phase/curvature calculations
│       ├── easy_use/      # Input generator, structure analyzer
│       ├── fermi/         # Fermi surface, DOS
│       ├── io/            # Input parsing, ABACUS/Wannier90 readers
│       ├── kpt/           # K-point generation
│       ├── tb/            # Tight-binding solver
│       ├── todo/          # Additional functions
│       ├── tools/         # Utilities, smearing
│       └── transport/     # Boltzmann transport coefficients
├── tutorial/              # Step-by-step tutorials
│   ├── 00-tutorial_instructions/
│   ├── Bi2Se3_band/
│   ├── Bi2Se3_wilsonloop/
│   ├── CsPbI3_optical/
│   ├── Cu_fermi_surface/
│   ├── FeCl2_AHC_ANC/
│   ├── GaAs_SHG/
│   ├── NV_bandunfolding/
│   ├── WS2_shift_current/
│   ├── WSSe_spin_texture/
│   └── weyl_model_BCD/
├── Dockerfile
├── pyproject.toml
├── setup.py
└── README.md
```

## Installation

### From PyPI
```bash
pip install pyatb
```

Available wheels: Python 3.8-3.14 on Linux x86_64.

### From Source
```bash
git clone https://github.com/pyatb/pyatb.git
cd pyatb
python setup.py install --record log
```

Customize `setup.py`:
- `__CXX__`: C++ compiler (not MPI version)
- `__LAPACK_DIR__`: Intel MKL path

### Dependencies
- Python >= 3.8
- NumPy
- C++ compiler with Eigen3
- LAPACK/MKL
- MPI (for parallel execution)

## Running

```bash
export OMP_NUM_THREADS=2
mpirun -np 6 pyatb
```

## Developers

- Gan Jin, Hongsheng Pang, Yuyang Ji, Zujian Dai, Xudong Zhu
- Supervised by Prof. Lixin He, University of Science and Technology of China (USTC)

## Stats
- Stars: 38
- Forks: 13
- Language: Python 71.1%, C++ 28.3%, Other 0.6%
