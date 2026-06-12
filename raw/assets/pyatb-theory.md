# PYATB - Theory and Methods

**Sources:**
- https://arxiv.org/abs/2303.18004 (arXiv paper)
- https://pyatb.github.io/pyatb/introduction.html (Official docs)
- https://github.com/pyatb/pyatb/blob/main/src/pyatb/transport/boltz_transport.py (Transport source)
**Retrieved:** 2026-06-12

## Paper Reference

**Title:** PYATB: An Efficient Python Package for Electronic Structure Calculations Using Ab Initio Tight-Binding Model

**Authors:** Gan Jin, Hongsheng Pang, Yuyang Ji, Zujian Dai, Lixin He

**Published:** Computer Physics Communications 291 (2023) 108844
**DOI:** https://doi.org/10.1016/j.cpc.2023.108844
**arXiv:** 2303.18004

## Theoretical Foundation

### Ab Initio Tight Binding Model

PYATB is based on the ab initio tight binding model where the Kohn-Sham Hamiltonian parameters are generated from self-consistent DFT calculations using numerical atomic orbital (NAO) bases (primarily from ABACUS).

In a periodic system, the Kohn-Sham equation at k-point:

H(k) * psi_n(k) = E_n(k) * S(k) * psi_n(k)

The Bloch wave function under NAO basis:

psi_n(k) = sum_i C_ni(k) * phi_i(k)

where phi_i(k) is the i-th atomic orbital, and C_ni(k) is the coefficient.

The eigenvalue problem in matrix form:

H(k) * C_n(k) = E_n(k) * S(k) * C_n(k)

Real-space tight binding parameters obtained from DFT:

H(R) = Hamiltonian matrix at lattice vector R
S(R) = Overlap matrix at lattice vector R
r(R) = Position/dipole matrix at lattice vector R

Fourier transform to k-space:

H(k) = sum_R H(R) * exp(i*k*R)
S(k) = sum_R S(R) * exp(i*k*R)
r(k) = sum_R r(R) * exp(i*k*R)

### Band Structure Methods

Three k-point modes:
1. **k-point mode**: Single k-point calculation
2. **k-line mode**: Calculate along high-symmetry lines (band path)
3. **k-mesh mode**: Uniform Monkhorst-Pack mesh

Band velocity matrix:

v_alpha(k) = (1/hbar) * dH(k)/dk_alpha

obtained via the position matrix elements.

### Geometric (Berry Phase) Properties

#### Berry Curvature

Omega_n(k) = -2 * Im * sum_{m!=n} <n|dH/dk_x|m><m|dH/dk_y|n> / (E_n - E_m)^2

#### Anomalous Hall Conductivity (AHC)

sigma_xy = -(e^2 / hbar) * sum_n * int dk Omega_n(k) * f(E_n(k))

Integration over the Brillouin zone using adaptive or regular grid methods.

#### Anomalous Nernst Conductivity (ANC)

alpha_xy = -(e / hbar*T) * sum_n * int dk Omega_n(k) * (E_n - mu) * (-df/dE)

Energy-resolved integration around the Fermi level.

#### Spin Hall Conductivity (SHC)

Uses band-projected Berry curvature-like term with spin current operator replacing charge current.

#### Wilson Loop / Chern Number

Tracks Wannier center evolution along a closed loop in k-space to determine the Chern number.

#### Electric Polarization

Berry phase formulation:

P_alpha = -(e / 2*pi) * int dk * Im * ln det S(k)

#### Orbital Magnetization

Berry-phase formulation with both bulk and surface contributions.

### Optical Properties

#### Linear Optical Conductivity

sigma_alpha_beta(omega) = (e^2 * i / omega) * sum_{n,m} * int dk * (f_n - f_m) * |<n|v_alpha|m>|^2 / (omega + E_n - E_m + i*eta)

#### Shift Current (Bulk Photovoltaic Effect)

sigma_alpha_beta_gamma(0; omega, -omega) = nonlinear response coefficient

Uses the shift vector formalism: D_mn = d(arg(r_mn))/dk - (A_m - A_n)

#### Second Harmonic Generation (SHG)

chi^(2)_abc(-2omega; omega, omega) calculated using Berry-connection-based nonlinear optical matrix elements.

#### Berry Curvature Dipole

D_alpha_beta = sum_n int dk (dOmega_n/dk_alpha) * v_n_beta

Leads to nonlinear anomalous Hall effect.

### Boltzmann Transport Theory

The Boltzmann transport module (`src/pyatb/transport/boltz_transport.py`) calculates transport coefficients using the semi-classical Boltzmann transport equation.

#### Transport Function (Sigma)

MidSigma[energy] = sum_k,n v_alpha(k,n) * v_beta(k,n) * tau(energy) * delta(E - E_n(k))

where v_alpha(k,n) is the band velocity and tau is the relaxation time.

#### Transport Coefficients

Using the transport function L_n:

L_0(mu, T) = int dE * (-df/dE) * MidSigma(E)
L_1(mu, T) = int dE * (-df/dE) * (E - mu) * MidSigma(E)
L_2(mu, T) = int dE * (-df/dE) * (E - mu)^2 * MidSigma(E)

**Electrical conductivity:** sigma = L_0
**Seebeck coefficient:** S = (1/T) * L_1 * L_0^{-1}
**Electronic thermal conductivity:** k_e = (1/T) * (L_1 * L_0^{-1} * L_1 - L_2)
**Carrier mobility:** mu = sigma / (n * e)

#### Relaxation Time Methods

1. **CRTA (Constant Relaxation Time Approximation):**
   - Uses a single constant relaxation time (parameter: `relax_time` in fs)
   - Simple model, useful for qualitative trends

2. **EMPC (Electron-Phonon Scattering / Deformation Potential):**
   - Energy-dependent relaxation time:
     tau(E) = 1 / (const_tau * DOS(E))
   - const_tau depends on temperature, deformation potential (`def_pot`), and Young's modulus (`young_mod`)
   - More physical, captures energy dependence of scattering

#### Carrier Density of States

n(E, T) = sum_k sum_n f(E_n(k), E, T) * delta(E - E_n(k)) * const_density

Includes temperature-dependent occupation via Fermi-Dirac distribution.

#### Effective Mass

Calculated from the inverse effective mass tensor, thermally averaged:

1/m* = (1/hbar^2) * sum_k,n v^2(k,n) * (-df/dE)

## Input Data Flow

```
ABACUS SCF --> H(R), S(R), r(R) --> PYATB Input file --> pyatb executable
                                            |
                                    +-------+--------+
                                    |       |        |
                                 Bands  Geometric  Optical
                                 module  module    module + Transport
```

## Supported First-Principles Backends

1. **ABACUS** (primary): Atomic-orbital Based Ab-initio Computation at UStc
   - Generates data-HR-sparse_SPIN*.csr, data-SR-sparse_SPIN*.csr, data-rR-sparse.csr
   - Website: https://abacus.ustc.edu.cn/

2. **Wannier90**: Maximally-localized Wannier functions
   - Generates tight-binding files via w90 interface
   - Parameter `w90_TB_has_r` controls whether position matrix is available
