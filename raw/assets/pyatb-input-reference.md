# PYATB - Complete Input File Reference

**Source:** https://github.com/pyatb/pyatb/blob/main/src/pyatb/io/default_input.py
**Retrieved:** 2026-06-12

This document contains the complete input parameter reference extracted from the PYATB source code (`default_input.py`).

## Input File Structure

The Input file uses a block-based format:

```
BLOCK_NAME
{
    parameter_name    value
    parameter_name    value1 value2 value3
}
```

Parameters marked `None` have no default and must be set. Parameters marked `[]` have no default but may not be needed in all configurations.

---

## INPUT_PARAMETERS (Required)

Global settings for the calculation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nspin` | int | None (required) | Spin channel: 1 (non-spin-polarized), 2 (spin-polarized), 4 (spin-orbit coupling) |
| `package` | str | `ABACUS` | Source package: `ABACUS` or `WANNIER90` |
| `fermi_energy` | str | `Auto` | Fermi energy value or `Auto` for automatic calculation |
| `fermi_energy_unit` | str | `eV` | Unit of Fermi energy |
| `max_kpoint_num` | int | 8000 | Maximum number of k-points per MPI process |
| `sparse_format` | int | 0 | Whether input matrices are in sparse format |

### Package-specific parameters

#### ABACUS package

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `HR_route` | str | None (required) | Path to Hamiltonian matrix file |
| `SR_route` | str | 1 (required) | Path to overlap matrix file |
| `rR_route` | str | 1 (optional) | Path to position/dipole matrix file |
| `binary` | int | 0 | Whether input files are in binary format |
| `HR_unit` | str | `Ry` | Energy unit of H(R): `Ry` or `eV` |
| `rR_unit` | str | `Bohr` | Length unit of r(R): `Bohr` or `Angstrom` |

#### WANNIER90 package

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `w90_TB_route` | str | None (required) | Path to Wannier90 tight-binding file |
| `w90_TB_has_r` | int | 0 | Whether the Wannier90 TB file contains position matrix |

---

## LATTICE (Required)

Crystal structure definition.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lattice_constant` | float | None (required) | Lattice constant scaling factor |
| `lattice_constant_unit` | str | `Bohr` | Unit: `Bohr` or `Angstrom` |
| `lattice_vector` | float[3][3] | None (required) | Three lattice vectors (3x3 matrix) |

---

## K-Point Modes

Several calculation blocks accept k-point specifications in three modes:

### mp (Monkhorst-Pack)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `k_start` | float[3] | [0,0,0] | Origin of k-mesh |
| `k_vect1` | float[3] | [1,0,0] | First reciprocal lattice vector |
| `k_vect2` | float[3] | [0,1,0] | Second reciprocal lattice vector |
| `k_vect3` | float[3] | [0,0,1] | Third reciprocal lattice vector |
| `mp_grid` | int[3] | None (required) | Grid dimensions, e.g. `20 20 20` |

### line (High-symmetry path)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kpoint_num` | int | None (required) | Number of high-symmetry points |
| `high_symmetry_kpoint` | float[4] per line | None (required) | kx ky kz num_points |
| `kpoint_label` | str[] | Auto | Labels for high-symmetry points |

### direct (Explicit k-points)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kpoint_num` | int | None (required) | Number of k-points |
| `kpoint_direct_coor` | float[3] per line | None (required) | kx ky kz per point |

---

## BAND_STRUCTURE

Calculate energy bands and wave functions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wf_collect` | int | 0 (False) | Whether to collect wave functions |
| `band_range` | int[2] | [-1,-1] | Range of bands to calculate |
| `kpoint_mode` | str | None (required) | `mp`, `line`, or `direct` |

---

## FAT_BAND

Calculate orbital-projected fat bands.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `band_range` | int[2] | None (required) | Band range to plot |
| `stru_file` | str | None (required) | Path to STRU file |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## PDOS

Partial density of states.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stru_file` | str | None (required) | Path to STRU file |
| `e_range` | float[2] | None (required) | Energy range [min, max] in eV |
| `de` | float | 0.01 | Energy step |
| `sigma` | float | 0.001 | Gaussian smearing width |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## FERMI_ENERGY

Calculate Fermi energy automatically.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | float | 0.0 | Temperature in K |
| `electron_num` | int | None (required) | Total number of electrons |
| `grid` | int[3] | [10,10,10] | K-mesh for Fermi energy calculation |
| `epsilon` | float | 1e-3 | Convergence threshold |

---

## FERMI_SURFACE

Plot the Fermi surface.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bar` | float | 1e-3 | Threshold for Fermi surface detection |
| `nbands` | int[2] | [0,0] | Band range |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## FIND_NODES

Search for Weyl/Dirac degenerate points.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `energy_range` | float[2] | [0,0] | Energy window for search |
| `initial_grid` | int[3] | [10,10,10] | Initial search grid |
| `initial_threshold` | float | 0.1 | Initial degeneracy threshold |
| `adaptive_grid` | int[3] | [20,20,20] | Adaptive refinement grid |
| `adaptive_threshold` | float | 1e-3 | Refined degeneracy threshold |
| `k_start` | float[3] | [0,0,0] | Search origin |
| `k_vect1` | float[3] | [1,0,0] | First search direction |
| `k_vect2` | float[3] | [0,1,0] | Second search direction |
| `k_vect3` | float[3] | [0,0,1] | Third search direction |

---

## BANDUNFOLDING

Band unfolding from supercell to primitive cell.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stru_file` | str | None (required) | Path to STRU file |
| `ecut` | float | 10 | Energy cutoff |
| `band_range` | int[2] | None (required) | Band range |
| `m_matrix` | float[9] | None (required) | Transformation matrix (3x3) |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## BERRY_CURVATURE

Calculate Berry curvature along k-path or on grid.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | int | 0 | Calculation method (0 or 1) |
| `occ_band` | int | -1 | Number of occupied bands |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## AHC (Anomalous Hall Conductivity)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | int | 0 | Calculation method |
| `integrate_mode` | str | None (required) | `Grid` or `Adaptive` |

### Integration modes

#### Grid mode
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `integrate_grid` | int[3] | [4,4,4] | Integration grid |
| `adaptive_grid` | int[3] | [4,4,4] | Adaptive refinement grid |
| `adaptive_grid_threshold` | float | 50.0 | Threshold for adaptive refinement |

#### Adaptive mode
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `relative_error` | float | 1e-6 | Relative error tolerance |
| `absolute_error` | float | 0.1 | Absolute error tolerance |
| `initial_grid` | int[3] | [1,1,1] | Initial integration grid |

---

## ANC (Anomalous Nernst Conductivity)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fermi_range` | float[2] | [-1.0, 1.0] | Energy range around Fermi level (eV) |
| `de` | float | 0.01 | Energy step |
| `eta` | float | 0.01 | Smearing parameter (eV) |
| `integrate_grid` | int[3] | [4,4,4] | Integration grid |

---

## SHC (Spin Hall Conductivity)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alpha` | str | "x" | Current direction |
| `beta` | str | "y" | Spin current direction |
| `gamma` | str | "z" | Spin polarization direction |
| `fermi_range` | float[2] | [-1.0, 1.0] | Energy range around Fermi level |
| `de` | float | 0.01 | Energy step |
| `eta` | float | 0.01 | Smearing (eV) |
| `integrate_grid` | int[3] | [4,4,4] | Integration grid |

---

## CHERN_NUMBER

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | int | 0 | Calculation method |
| `occ_band` | int | -1 | Occupied bands |
| `k_start` | float[3] | [0,0,0] | Integration origin |
| `k_vect1` | float[3] | [1,0,0] | First direction |
| `k_vect2` | float[3] | [0,1,0] | Second direction |
| `integrate_mode` | str | None (required) | Integration mode |

---

## WILSON_LOOP

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `occ_band` | int | None (required) | Number of occupied bands |
| `k_start` | float[3] | [0,0,0] | Starting k-point |
| `k_vect1` | float[3] | [1,0,0] | First direction |
| `k_vect2` | float[3] | [0,1,0] | Second direction |
| `nk1` | int | 100 | Grid points along k_vect1 |
| `nk2` | int | 100 | Grid points along k_vect2 |

---

## OPTICAL_CONDUCTIVITY

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `occ_band` | int | -1 | Occupied bands |
| `omega` | float[2] | None (required) | Frequency range [min, max] (eV) |
| `domega` | float | None (required) | Frequency step |
| `eta` | float | 0.01 | Smearing (eV) |
| `grid` | int[3] | None (required) | K-mesh |
| `method` | int | 1 | Calculation method |

---

## SHIFT_CURRENT

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `occ_band` | int | None (required) | Occupied bands |
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `smearing_method` | int | 1 | 0: none, 1: Gauss, 2: adaptive |
| `eta` | float | 0.01 | Smearing (eV) |
| `grid` | int[3] | None (required) | K-mesh |
| `method` | int | 1 | Calculation method |
| `n_occ` | int | -1 | Number of occupied (from 1) |
| `m_unocc` | int | -1 | Number of unoccupied (from 1) |

---

## SHG (Second Harmonic Generation)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | int | 0 | Calculation method |
| `eta` | float | 0.05 | Smearing (eV) |
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `grid` | int[3] | None (required) | K-mesh |

---

## BERRY_CURVATURE_DIPOLE

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `grid` | int[3] | None (required) | K-mesh |

---

## JDOS (Joint Density of States)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `occ_band` | int | None (required) | Occupied bands |
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `eta` | float | 0.01 | Smearing (eV) |
| `grid` | int[3] | None (required) | K-mesh |

---

## SURFACE_STATE

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cal_surface_method` | str | `green_fun` | `direct_diag`, `direct_green`, `green_fun` |
| `surface_direction` | str | `c` | Surface direction: a, b, c |
| `energy_windows` | float[2] | [-1.0, 1.0] | Energy window around Fermi |
| `de` | float | 0.01 | Energy step |
| `eta` | float | 0.01 | Smearing (eV) |
| `coupling_layers` | int | None (required) | Coupling layers |
| `calculate_layer` | int | 1 | Calculate layer |
| `kpoint_mode` | str | None (required) | K-point mode |

### Surface methods

- `direct_diag`: Requires `slab_layers`
- `direct_green`: Requires `slab_layers`, `green_eta` (default 0.001)
- `green_fun`: Requires `green_eta` (default 0.001)

---

## BOLTZ_TRANSPORT (Boltzmann Transport Coefficients)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transport_coeff_cal` | int | 1 | Whether to calculate transport coefficients |
| `effective_mass_cal` | int | 0 | Whether to calculate effective mass |
| `transport_method` | str | `CRTA` | `CRTA` (constant relaxation time) or `EMPC` (electron-phonon) |
| `electron_num` | int | None (required) | Number of electrons |
| `grid` | int[3] | None (required) | K-mesh for integration |
| `delta_mu_range` | float[2] | [-5.0, 5.0] | Chemical potential range (eV) |
| `mu_step` | float | 0.1 | Chemical potential step (eV) |
| `temperature_range` | float[2] | [300, 300] | Temperature range (K) |
| `temperature_step` | float | 50 | Temperature step (K) |
| `eta` | float | 0.1 | Smearing (eV) |
| `relax_time` | float | 10 | Relaxation time (fs), for CRTA |
| `def_pot` | float | 2 | Deformation potential (eV), for EMPC |
| `young_mod` | float | 240 | Young's modulus (GPa), for EMPC |

### Output Files (in Out/TRANSPORT/)

- `carrier_DOS.dat` - Carrier density of states vs energy vs temperature
- `electronic_conductivity_tensor.dat` - 3x3 conductivity tensor (S/cm)
- `seebeck_tensor.dat` - 3x3 Seebeck coefficient (muV/K)
- `ke-tensor.dat` - 3x3 electronic thermal conductivity (V^2/K)
- `mobility.dat` - Carrier mobility (cm^2/V*S)
- `TAU.dat` - Relaxation time (s), EMPC only
- `effective-mass.dat` - Effective mass (me)

---

## POLARIZATION

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `occ_band` | int | None (required) | Occupied bands |
| `nk1` | int | 8 | K-points in direction 1 |
| `nk2` | int | 8 | K-points in direction 2 |
| `nk3` | int | 8 | K-points in direction 3 |
| `atom_type` | int | None (required) | Number of atom types |
| `stru_file` | str | None (required) | Path to STRU file |
| `valence_e` | int[] | None (required) | Valence electrons per atom type |

---

## ORBITAL_MAGNETIZATION

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fermi_energy` | float | None (required) | Fermi energy |
| `fermi_range` | float[2] | [-2.0, 2.0] | Energy range |
| `de` | float | 0.05 | Energy step |
| `eta` | float | 0.01 | Smearing (eV) |
| `grid` | int[3] | None (required) | K-mesh |

---

## CPGE (Circular Photogalvanic Effect)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `integrate_mode` | str | None (required) | Integration mode |

---

## DRUDE_WEIGHT

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `integrate_mode` | str | None (required) | Integration mode |

---

## POCKELS

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `omega1` | float | 0 | Static frequency |
| `omega` | float[2] | None (required) | Frequency range |
| `domega` | float | None (required) | Frequency step |
| `grid` | int[3] | None (required) | K-mesh |

---

## SPIN_TEXTURE

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `band_range` | int[2] | None (required) | Band range |
| `kpoint_mode` | str | None (required) | K-point mode |

---

## CHIRALITY

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `method` | int | 0 | Calculation method |
| `occ_band` | int | -1 | Occupied bands |
| `k_vect` | float[3] | [0,0,0] | Weyl point position |
| `radius` | float | 0.01 | Sphere radius |
| `point_num` | int | 1000 | Number of points on sphere |

---

## REDUCE_BASIS

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `e_range` | float[2] | None (required) | Energy range |
| `threshold` | float | 0.02 | Threshold for basis reduction |
| `band_index_range` | int[2] | None | Band index range |
| `kpoint_mode` | str | None (required) | K-point mode |
