# PYATB - Transport Module Implementation

**Source:** https://github.com/pyatb/pyatb/blob/main/src/pyatb/transport/boltz_transport.py
**Retrieved:** 2026-06-12

## Module: `pyatb.transport.boltz_transport`

Class: `Boltz_Transport`

## Overview

The Boltzmann transport module calculates electronic transport coefficients from the ab initio tight binding Hamiltonian using the semi-classical Boltzmann transport equation. It computes:

1. **Carrier density of states** vs energy and temperature
2. **Electrical conductivity tensor** (3x3, S/cm)
3. **Seebeck coefficient tensor** (3x3, muV/K)
4. **Electronic thermal conductivity tensor** (3x3, V^2/K)
5. **Carrier mobility** (cm^2/V*S)
6. **Effective mass** (m_e units)
7. **Relaxation time** (s, for EMPC method)

## Physical Constants Used

```python
k_B = 8.6173332415e-5         # Boltzmann constant (eV/K)
eV_to_GPa = 160.21766208      # Conversion factor
e_mass = 9.1093837e-31        # Electron mass (kg)
```

## Methods

### CRTA (Constant Relaxation Time Approximation)

Uses a single user-specified relaxation time (in femtoseconds) for all energy levels.

Parameters used:
- `relax_time`: in fs (default 10 fs)

### EMPC (Electron-Phonon via Deformation Potential)

Energy-dependent relaxation time based on the density of states:

```
tau(E) = 1 / (const_tau * DOS(E))
```

where:
```
const_tau = (2*pi*k_B*T*eV_to_GPa*def_pot^2) / (V_cell * hbar * Young_mod)
```

Parameters used:
- `def_pot`: Deformation potential (eV), default 2
- `young_mod`: Young's modulus (GPa), default 240

## Calculation Pipeline

### 1. set_parameters()

Configures energy and temperature grids:
- Energy grid: from `fermi_energy + mu_min - 4*eta` to `fermi_energy + mu_max + 4*eta`
- Temperature grid: from `temp_min` to `temp_max` with `temp_step`

### 2. cal_carrier_DOS()

Computes carrier density of states:
- Smearing-based DOS: Gaussian smearing of eigenvalues onto energy grid
- Integrated DOS: Step function integration (no smearing)
- Temperature-dependent carrier concentration via Fermi-Dirac occupation

Output: `carrier_DOS.dat`

### 3. cal_relax_time() (EMPC only)

Computes energy-dependent relaxation time from DOS.

Output: `TAU.dat`

### 4. cal_MidSigma_and_MidInvMass(tau)

Core transport function:
- Iterates over k-points on the MPI grid
- Computes band velocities from the velocity matrix: `v_alpha(k,n) = velocity_matrix[k, alpha, n, n]`
- Accumulates `MidSigma[E][alpha][beta] = sum_k,n v_alpha*v_beta*tau(E)*delta(E-E_n)`
- Accumulates `MidInvMass[E] = sum_k,n |v|^2 * const_mass * delta(E-E_n)`

Uses MPI `allreduce` for global summation.

### 5. cal_transport_coefficients()

Computes transport coefficients from the MidSigma function:

```
for each (energy, temperature):
    L_0[alpha][beta] = sum_E MidSigma[E][alpha][beta] * (-df/dE) * (E-mu)^0
    L_1[alpha][beta] = sum_E MidSigma[E][alpha][beta] * (-df/dE) * (E-mu)^1
    L_2[alpha][beta] = sum_E MidSigma[E][alpha][beta] * (-df/dE) * (E-mu)^2

    sigma = L_0                         # Conductivity
    S = seebeck_const * L_1 * L_0^-1   # Seebeck
    k_e = ke_const * (L_1 * L_0^-1 * L_1 - L_2)  # Thermal conductivity
    mobility = L_0_trace * mobility_const / carrier_DOS
```

For nspin=1 (non-magnetic), transport quantities are doubled for spin degeneracy.

### 6. cal_effective_mass()

```
inv_mass(E, T) = sum_E MidInvMass[E'] * (-df/dE)(E, E', T)
eff_mass = carrier_DOS / inv_mass
```

## Output File Formats

### electronic_conductivity_tensor.dat
```
Temperature = 300.000000
  Energy-fermi(eV) sigma(S/cm)   XX     XY     XZ     YX     YY     YZ     ZX     ZY     ZZ
     -5.000000     1.23e+05     0.00e+00  ...  (9 tensor components)
```

### seebeck_tensor.dat
```
Temperature = 300.000000
  Energy-fermi(eV)  seebeck_coff (muV/K)   XX  XY  XZ  YX  YY  YZ  ZX  ZY  ZZ
```

### ke-tensor.dat
```
Temperature = 300.000000
  Energy-fermi(eV)  ke (V^2/K)   XX  XY  XZ  YX  YY  YZ  ZX  ZY  ZZ
```

### mobility.dat
```
Temperature = 300.000000
  Energy-fermi(eV) mobility(cm^2/V*S)
```

### carrier_DOS.dat
```
Temperature = 300.000000
  Energy-fermi(eV)    carrier_DOS_noT (10^20/cm3)   carrier_DOS (10^20/cm3)
```

### effective-mass.dat
```
Temperature = 300.000000
  Energy-fermi(eV) effective-mass(me)
```

## Unit Conventions

| Quantity | Unit |
|----------|------|
| Energy | eV |
| Temperature | K |
| Conductivity | S/cm |
| Seebeck coefficient | muV/K |
| Thermal conductivity | V^2/K |
| Mobility | cm^2/(V*S) |
| Carrier density | 10^20/cm^3 |
| Effective mass | m_e |
| Relaxation time | s |

## MPI Parallelization

The k-point grid is distributed across MPI processes. Each process handles a subset of k-points, computes local contributions to MidSigma and MidInvMass, then uses `COMM.allreduce(op=op_sum)` to collect results.

## Limitations

- Only supports nspin=1 and nspin=4 (not nspin=2)
- CRTA uses a single constant tau (energy-independent)
- EMPC uses a simplified deformation potential model
- No self-consistent solution of the Boltzmann equation (uses RTA only)
