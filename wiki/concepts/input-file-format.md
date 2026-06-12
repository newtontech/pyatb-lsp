# Concept: PYATB Input File Format

**Source:** `src/pyatb/io/default_input.py`, `src/pyatb/io/input.py`

## Format

PYATB uses a block-structured text format. Each block starts with a block name (uppercase) followed by curly-brace-enclosed parameters:

```
BLOCK_NAME
{
    parameter_name    value
    parameter_name    value1 value2 value3
    multi_line_data
    x1 y1 z1 extra
    x2 y2 z2 extra
}
```

Comments use `#`. Blank lines are ignored.

## Mandatory Blocks

1. **INPUT_PARAMETERS** -- Global settings (nspin, package, fermi_energy, file paths)
2. **LATTICE** -- Crystal structure (lattice constant + 3 lattice vectors)

## Optional Calculation Blocks

Any combination of these blocks can be added to request calculations:

| Block | Category | Needs r(R) |
|-------|----------|-----------|
| BAND_STRUCTURE | Bands | No |
| FAT_BAND | Bands | No |
| PDOS | Bands | No |
| FERMI_ENERGY | Bands | No |
| FERMI_SURFACE | Bands | No |
| FIND_NODES | Bands | No |
| SPIN_TEXTURE | Bands | No |
| BANDUNFOLDING | Bands | No |
| SURFACE_STATE | Bands | No |
| JDOS | Optical | No |
| OPTICAL_CONDUCTIVITY | Optical | Yes |
| SHIFT_CURRENT | Optical | Yes |
| SHG | Optical | Yes |
| BERRY_CURVATURE_DIPOLE | Optical | Yes |
| CPGE | Optical | Yes |
| DRUDE_WEIGHT | Optical | Yes |
| POCKELS | Optical | Yes |
| BERRY_CURVATURE | Geometric | Yes |
| AHC | Geometric | Yes |
| ANC | Geometric | Yes |
| SHC | Geometric | Yes |
| CHERN_NUMBER | Geometric | Yes |
| WILSON_LOOP | Geometric | Yes |
| POLARIZATION | Geometric | Yes |
| ORBITAL_MAGNETIZATION | Geometric | Yes |
| CHIRALITY | Geometric | Yes |
| BOLTZ_TRANSPORT | Transport | Yes |

## K-Point Specification

Three modes available in any k-point-accepting block:

### Monkhorst-Pack (mp)
```
kpoint_mode   mp
k_start       0 0 0
k_vect1       1 0 0
k_vect2       0 1 0
k_vect3       0 0 1
mp_grid       20 20 20
```

### Line (band path)
```
kpoint_mode        line
kpoint_num         5
high_symmetry_kpoint
0.0 0.0 0.0 100  # G
0.0 0.0 0.5 100  # Z
0.5 0.5 0.0 100  # F
0.0 0.0 0.0 100  # G
0.5 0.0 0.0 1    # L
kpoint_label       G, Z, F, G, L
```

### Direct (explicit k-points)
```
kpoint_mode        direct
kpoint_num         3
kpoint_direct_coor
0.0 0.0 0.0
0.5 0.5 0.5
0.0 0.5 0.5
```

## Package Source

### ABACUS (default)
```
package    ABACUS
HR_route   data-HR-sparse_SPIN0.csr
SR_route   data-SR-sparse_SPIN0.csr
rR_route   data-rR-sparse.csr
HR_unit    Ry
rR_unit    Bohr
```

### Wannier90
```
package        WANNIER90
w90_TB_route   wannier90_tb.dat
w90_TB_has_r   0
```

## Fermi Energy

Can be set explicitly (`fermi_energy 9.5572`) or automatically (`fermi_energy Auto`).

When Auto, add a FERMI_ENERGY block:
```
FERMI_ENERGY
{
    temperature     0
    electron_num    11
    grid            50 50 50
    epsilon         1e-4
}
```

## Running

```bash
export OMP_NUM_THREADS=2
mpirun -np 6 pyatb
```

Results in `Out/` directory, organized by calculation type.
