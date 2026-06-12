# Concept: Berry Phase and Geometric Properties in PYATB

**Module:** `pyatb.berry`
**Input blocks:** AHC, ANC, SHC, CHERN_NUMBER, WILSON_LOOP, BERRY_CURVATURE, POLARIZATION, ORBITAL_MAGNETIZATION, CHIRALITY

## Summary

PYATB provides comprehensive Berry phase and Berry curvature calculations for topological and geometric properties of materials. These calculations rely on the position/dipole matrix r(R) to compute Berry connection and related quantities in k-space.

## Available Properties

### Anomalous Hall Conductivity (AHC)
- **Block:** `AHC`
- **Output:** 3x3 conductivity tensor (S/cm)
- **Methods:** Grid integration or adaptive integration
- **Requires:** r(R) matrix

### Anomalous Nernst Conductivity (ANC)
- **Block:** `ANC`
- **Output:** 3x3 thermoelectric tensor (A/(m*K))
- **Energy-resolved:** Scans Fermi level over `fermi_range`

### Spin Hall Conductivity (SHC)
- **Block:** `SHC`
- **Output:** Spin Hall conductivity for chosen alpha/beta/gamma directions
- **Requires:** SOC (nspin=4)

### Chern Number
- **Block:** `CHERN_NUMBER`
- **Output:** Integer Chern number for chosen k-plane
- **Integration:** Adaptive or grid-based

### Wilson Loop
- **Block:** `WILSON_LOOP`
- **Output:** Wannier center evolution (WCC) plot data
- **Purpose:** Determine Z2 invariant, Chern number from winding

### Berry Curvature
- **Block:** `BERRY_CURVATURE`
- **Output:** Omega(k) along k-path or on grid
- **Methods:** 0 (standard) or 1 (alternative formulation)

### Electric Polarization
- **Block:** `POLARIZATION`
- **Output:** Polarization vector (Berry phase)
- **Requires:** STRU file, valence electron counts

### Orbital Magnetization
- **Block:** `ORBITAL_MAGNETIZATION`
- **Output:** Orbital magnetization tensor
- **Requires:** Fermi energy and energy range

### Chirality
- **Block:** `CHIRALITY`
- **Output:** Topological charge of Weyl/Dirac points
- **Method:** Berry curvature flux through sphere around node

## Common Integration Modes

### Grid Mode
```
integrate_mode          Grid
integrate_grid          Nx Ny Nz
adaptive_grid           nx ny nz
adaptive_grid_threshold threshold
```

### Adaptive Mode
```
integrate_mode          Adaptive
relative_error          1e-6
absolute_error          0.1
initial_grid            1 1 1
```

## Theoretical Background

Berry curvature:
Omega_n(k) = -2 Im sum_{m!=n} <n|v_x|m><m|v_y|n> / (E_n - E_m)^2

AHC:
sigma_xy = -(e^2/hbar) sum_n int dk Omega_n(k) f(E_n(k))

ANC:
alpha_xy = -(e/hbar*T) sum_n int dk Omega_n(k) (E_n - mu) (-df/dE)

## Key Requirements

- All geometric calculations require the r(R) position/dipole matrix
- SOC (nspin=4) needed for AHC, SHC in non-magnetic materials
- Sufficient k-mesh convergence is critical for accurate quantized quantities
