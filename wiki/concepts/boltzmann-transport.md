# Concept: Boltzmann Transport in PYATB

**Module:** `pyatb.transport.boltz_transport`
**Input block:** `BOLTZ_TRANSPORT`

## Summary

PYATB calculates electronic transport coefficients by solving the semi-classical Boltzmann transport equation in the relaxation time approximation (RTA). The method works with the ab initio tight-binding Hamiltonian to compute full tensorial transport properties as functions of chemical potential and temperature.

## Transport Coefficients

All coefficients are computed as 3x3 tensors:

| Coefficient | Symbol | Unit | Output File |
|-------------|--------|------|-------------|
| Electrical conductivity | sigma | S/cm | electronic_conductivity_tensor.dat |
| Seebeck coefficient | S | muV/K | seebeck_tensor.dat |
| Electronic thermal conductivity | k_e | V^2/K | ke-tensor.dat |
| Carrier mobility | mu | cm^2/(V*S) | mobility.dat |
| Carrier density | n | 10^20/cm^3 | carrier_DOS.dat |
| Effective mass | m* | m_e | effective-mass.dat |

## Two Relaxation Time Methods

### CRTA (Constant Relaxation Time Approximation)

Single energy-independent relaxation time. Set `transport_method CRTA` and `relax_time` (in fs, default 10).

Useful for qualitative trends and comparison across materials.

### EMPC (Deformation Potential Method)

Energy-dependent relaxation time: tau(E) = 1/(C * DOS(E)), where C depends on deformation potential, Young's modulus, and temperature. Set `transport_method EMPC`, `def_pot` (eV), `young_mod` (GPa).

## Input Block Parameters

```
BOLTZ_TRANSPORT
{
    transport_coeff_cal      1          # Calculate transport coefficients
    effective_mass_cal       0          # Calculate effective mass
    transport_method         CRTA       # CRTA or EMPC
    electron_num             N          # Number of electrons
    grid                     Nx Ny Nz   # K-mesh
    delta_mu_range           -5.0 5.0   # Chemical potential range (eV)
    mu_step                  0.1        # Chemical potential step (eV)
    temperature_range        300 300    # Temperature range (K)
    temperature_step         50         # Temperature step (K)
    eta                      0.1        # Smearing (eV)
    relax_time               10         # For CRTA: relaxation time (fs)
    def_pot                  2          # For EMPC: deformation potential (eV)
    young_mod                240        # For EMPC: Young's modulus (GPa)
}
```

## Underlying Mathematics

The transport function Sigma(E) is built from band velocities:

Sigma_ab(E) = sum_{k,n} v_a(k,n) * v_b(k,n) * tau(E) * delta(E - E_n(k))

Transport integrals L_n:

L_0(mu,T) = int dE Sigma(E) * (-df/dE)
L_1(mu,T) = int dE Sigma(E) * (E-mu) * (-df/dE)
L_2(mu,T) = int dE Sigma(E) * (E-mu)^2 * (-df/dE)

sigma = L_0
S = (1/T) * L_1 * L_0^{-1}
k_e = (1/T) * (L_1 * L_0^{-1} * L_1 - L_2)

## Constraints

- nspin must be 1 or 4 (not 2)
- Requires r(R) matrix (position/dipole)
- K-mesh must be sufficiently dense for convergence

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
