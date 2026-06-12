# PYATB - Introduction and Capabilities

**Source:** https://pyatb.github.io/pyatb/introduction.html
**Retrieved:** 2026-06-12

## Description

PYATB (Python ab initio tight binding simulation package) is an open-source software package designed for computing electronic structures and related properties based on the ab initio tight binding Hamiltonian. The Hamiltonian can be directly obtained after conducting self-consistent calculations with first-principles packages using numerical atomic orbital (NAO) bases, such as ABACUS.

The package comprises three modules - **Bands**, **Geometric**, and **Optical** - each providing a comprehensive set of tools for analyzing different aspects of a material's electronic structure.

## Bands Module

- **Band structure**: Calculate energy bands and wave functions using three k-point modes: `k-point`, `k-line`, and `k-mesh`
- **Band unfolding**: Calculate spectral weight by unfolding energy bands of a supercell into the BZ of the primitive cell
- **Fermi energy**: Calculate the Fermi energy at a given temperature
- **Fermi surface**: Plot the Fermi surface
- **Find nodes**: Search for degenerate points of energy bands in the BZ within a specified energy window (find Weyl/Dirac points)
- **DOS and PDOS**: Calculate density of states and partial density of states of particular orbitals
- **Fat band**: Contribution of each atomic orbital to electronic wave functions at each k-point
- **Spin texture**: Plot the spin polarization vector as a function of momentum in the BZ
- **Surface states**: Calculate spectral weights using the iterative surface Green's function method

## Geometric Module

- **Wilson loop**: Calculate the Chern number by tracking Wannier centers along the Wilson loop
- **Electric polarization**: Evaluate electric polarization in various directions for non-centrosymmetric materials (Berry phase theory)
- **Berry curvature**: Compute the Berry curvature in the BZ
- **Anomalous Hall conductivity (AHC)**: Calculate AHC using Berry curvature
- **Spin Hall conductivity (SHC)**: Calculate SHC using band-projected Berry curvature-like term
- **Anomalous Nernst conductivity (ANC)**: Calculate ANC using Berry-curvature-related thermoelectric kernel
- **Chern number**: Calculate Chern number for any given k-plane
- **Chirality**: Examine chirality of Weyl points by calculating Berry curvature on a sphere around the point
- **Orbital magnetization**: Calculate orbital magnetization using Berry-phase formulation

## Optical Module

- **JDOS**: Joint density of states, characterizing electronic states and optical transitions
- **Optical conductivity and dielectric function**: Frequency-dependent optical conductivity and dielectric function
- **Shift current**: Shift current conductivity tensor for bulk photovoltaic effect
- **Berry curvature dipole**: Leads to nonlinear anomalous Hall effects
- **Second harmonic generation (SHG)**: SHG susceptibility using Berry-connection-based nonlinear optical matrix elements
- **Circular photogalvanic effect (CPGE)**: Calculate CPGE
- **Drude weight**: Calculate Drude weight
- **Pockels effect**: Linear electro-optic response

## Transport Module

- **Boltzmann transport**: Electrical conductivity, Seebeck coefficient, thermal conductivity, carrier mobility, effective mass
- Two methods: CRTA (constant relaxation time approximation) and EMPC (electron-phonon scattering)

## Methodology

PYATB is based on the ab initio tight binding model, where Hamiltonian parameters are generated directly from self-consistent calculations using first-principles software based on NAO bases (e.g., ABACUS).

The Kohn-Sham equation at a given k-point becomes an eigenvalue problem under the NAO basis:

H(k) * C(k) = E(k) * S(k) * C(k)

where H(k) is the Hamiltonian matrix, S(k) is the overlap matrix, and C(k) are eigenvectors.

Real-space tight binding matrices (H(R), S(R)) are obtained from ABACUS, then Fourier-transformed to k-space:

H(k) = sum_R H(R) * exp(i*k*R)
S(k) = sum_R S(R) * exp(i*k*R)

For geometric properties, the dipole matrix between NAOs is also needed:

r(k) = sum_R r(R) * exp(i*k*R)

## Workflow

1. Perform self-consistent calculations using ABACUS to generate tight binding Hamiltonian (H(R), S(R), r(R))
2. Copy HR, SR, rR files to working directory
3. Write the `Input` file specifying calculation parameters
4. Run `mpirun -np N pyatb`
5. Results appear in `Out/` directory

## Citation

Gan Jin, Hongsheng Pang, Yuyang Ji, Zujian Dai, Lixin He. "PYATB: An Efficient Python Package for Electronic Structure Calculations Using Ab Initio Tight-Binding Model." Computer Physics Communications 291 (2023) 108844. arXiv:2303.18004
