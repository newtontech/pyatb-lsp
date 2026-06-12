# PYATB - ABACUS Integration Guide

**Source:** http://abacus.deepmodeling.com/en/latest/advanced/interface/pyatb.html
**Retrieved:** 2026-06-12

## ABACUS-PYATB Workflow

### Step 1: ABACUS Self-Consistent Calculation

The ABACUS INPUT file must enable output of tight binding matrices:

```
INPUT_PARAMETERS

# System variables
suffix                Bi2Se3
ntype                 2
calculation           scf
esolver_type          ksdft
symmetry              1
init_chg              atomic

# Plane wave related variables
ecutwfc               100

# Electronic structure
basis_type            lcao        # MUST be lcao (NAO basis)
ks_solver             genelpa
nspin                 4           # 1, 2, or 4 (with SOC)
smearing_method       gauss
smearing_sigma        0.02
mixing_type           broyden
mixing_beta           0.7
scf_nmax              200
scf_thr               1e-8
lspinorb              1           # Enable spin-orbit coupling
noncolin              0

# Variables related to output information
out_chg               1
out_mat_hs2           1           # MUST be 1: output H(R) and S(R)
out_mat_r             1           # MUST be 1: output r(R) position matrix
```

### Key ABACUS Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `basis_type` | `lcao` | Required: use numerical atomic orbitals |
| `out_mat_hs2` | 1 | Output Hamiltonian and overlap matrices |
| `out_mat_r` | 1 | Output position/dipole matrix |
| `nspin` | 4 | Spin-orbit coupling for topological properties |

### Step 2: Copy Output Files

ABACUS generates the following files in `OUT.*` directory:

| ABACUS Output | PYATB Input | Description |
|---------------|-------------|-------------|
| `data-HR-sparse_SPIN0.csr` | HR_route | Hamiltonian matrix in real space |
| `data-SR-sparse_SPIN0.csr` | SR_route | Overlap matrix in real space |
| `data-rR-sparse.csr` | rR_route | Position/dipole matrix in real space |

For nspin=2 (spin-polarized without SOC):
- Two HR files: `data-HR-sparse_SPIN0.csr` and `data-HR-sparse_SPIN1.csr`
- Two SR files: `data-SR-sparse_SPIN0.csr` and `data-SR-sparse_SPIN1.csr`

For nspin=4 (SOC): Only `SPIN0` files are needed (the full spinor Hamiltonian is in a single file).

### Step 3: Write PYATB Input File

The Fermi energy value can be found in the ABACUS running log (OUT.*/running_scf.log).

```
INPUT_PARAMETERS
{
    nspin                          4
    package                        ABACUS
    fermi_energy                   9.557219691497478
    fermi_energy_unit              eV
    HR_route                       data-HR-sparse_SPIN0.csr
    SR_route                       data-SR-sparse_SPIN0.csr
    rR_route                       data-rR-sparse.csr
    HR_unit                        Ry
    rR_unit                        Bohr
    max_kpoint_num                 8000
}

LATTICE
{
    lattice_constant               1.8897162
    lattice_constant_unit          Bohr
    lattice_vector
    -2.069  -3.583614  0.000000
     2.069  -3.583614  0.000000
     0.000   2.389075  9.546667
}

# Add calculation blocks as needed...
```

### Step 4: Run PYATB

```bash
export OMP_NUM_THREADS=2
mpirun -np 6 pyatb
```

Results are written to the `Out/` directory, organized by calculation type:
- `Out/Band_Structure/` - Band structure data and plots
- `Out/Transport/` - Transport coefficient data
- etc.

### Unit Conventions

- ABACUS outputs H(R) in Rydberg by default (set `HR_unit` to `Ry`)
- ABACUS outputs r(R) in Bohr by default (set `rR_unit` to `Bohr`)
- Lattice constant is typically in Bohr (conversion: 1 Bohr = 0.529177 Angstrom)

### Notes

- `out_mat_r` is NOT needed for band structure-only calculations (no geometric, optical, or transport properties)
- `rR_route` can be omitted for band structure, DOS, PDOS calculations
- The `need_rR_matrix` list in the source code specifies which blocks require the r(R) matrix: AHC, ANC, BERRY_CURVATURE, BERRY_CURVATURE_DIPOLE, CHERN_NUMBER, CHIRALITY, OPTICAL_CONDUCTIVITY, ORBITAL_MAGNETIZATION, POLARIZATION, SHIFT_CURRENT, WILSON_LOOP, CPGE, DRUDE_WEIGHT, BOLTZ_TRANSPORT, SHC, SHG, POCKELS
