# PYATB - Related Tools and Ecosystem

**Source:** Web search compilation
**Retrieved:** 2026-06-12

## PYATB in the ABACUS Ecosystem

PYATB is part of the DeepModeling ecosystem centered around ABACUS (Atomic-orbital Based Ab-initio Computation at UStc).

### ABACUS
- **Website:** https://abacus.ustc.edu.cn/
- **GitHub:** https://github.com/deepmodeling/abacus-develop
- **Purpose:** DFT electronic structure code using NAO bases
- **Relationship:** ABACUS generates the H(R), S(R), r(R) files that PYATB consumes

### PYATB Documentation
- **Official docs:** https://pyatb.github.io/pyatb/
- **ABACUS docs (PYATB section):** http://abacus.deepmodeling.com/en/latest/advanced/interface/pyatb.html

### PYATB Distribution
- **PyPI:** https://pypi.org/project/pyatb/ (v1.1.2, Dec 2025)
- **Wheels:** Linux x86_64, Python 3.8-3.14
- **Source:** https://github.com/pyatb/pyatb

### Reproducible Research
- **CodeOcean:** https://codeocean.com/capsule/9408682

## Similar Transport Calculation Tools

### BoltzTraP / BoltzTraP2
- **Purpose:** Boltzmann transport calculations from DFT
- **Method:** Semi-classical Boltzmann equation with constant relaxation time
- **Input:** Band structure from DFT codes (VASP, Quantum ESPRESSO, etc.)
- **Difference from PYATB:** Uses interpolated band structure rather than tight-binding; does not require NAO basis

### Wannier90
- **Purpose:** Maximally-localized Wannier functions
- **Relationship to PYATB:** PYATB supports Wannier90 TB files as an alternative to ABACUS
- **Input parameter:** `package WANNIER90`, `w90_TB_route`

### ShengBTE
- **Purpose:** Lattice thermal conductivity from phonon Boltzmann equation
- **Complementary to PYATB:** Electronic transport (PYATB) + lattice transport (ShengBTE) = total thermoelectric properties

### AMSET
- **Purpose:** Ab initio scattering and transport
- **Method:** Solves Boltzmann equation with multiple scattering mechanisms
- **More sophisticated than PYATB's CRTA/EMPC methods**

### VASP Transport Module
- **Purpose:** Transport coefficients with electron-phonon scattering
- **Integration:** Built into VASP, solves linearized Boltzmann equation

### EPW (Electron-Phonon Wannier)
- **Purpose:** Electron-phonon coupling and transport
- **Method:** Wannier interpolation of electron-phonon matrix elements
- **Quantum ESPRESSO plugin**

## Key Differentiators of PYATB

1. **Tight-binding direct input:** Works directly with ab initio TB matrices, no band interpolation needed
2. **Topological properties:** Unique focus on Berry phase, Chern numbers, Wilson loops alongside transport
3. **Nonlinear optics:** Shift current, SHG, BCD, CPGE - rare in other packages
4. **ABACUS integration:** Tight coupling with ABACUS for NAO-based DFT
5. **MPI parallelism:** Distributed k-point calculations
6. **C++ backend:** Performance-critical operations in C++ with Eigen library

## Citation

When using PYATB, cite:

```bibtex
@article{Jin2023,
  title = {PYATB: An Efficient Python Package for Electronic Structure Calculations Using Ab Initio Tight-Binding Model},
  author = {Gan Jin and Hongsheng Pang and Yuyang Ji and Zujian Dai and Lixin He},
  journal = {Computer Physics Communications},
  volume = {291},
  pages = {108844},
  year = {2023},
  doi = {10.1016/j.cpc.2023.108844}
}
```
