# Concept: ABACUS Integration

## Overview

ABACUS (Atomic-orbital Based Ab-initio Computation at UStc) is the primary DFT code that generates the tight-binding Hamiltonian input for PYATB. The workflow requires ABACUS to perform a self-consistent calculation with specific output flags enabled.

## ABACUS SCF Input Requirements

Key parameters in ABACUS INPUT:

```
basis_type      lcao      # MUST use NAO basis
out_mat_hs2     1         # Output H(R) and S(R)
out_mat_r       1         # Output r(R) position matrix
```

- `out_mat_r` can be omitted for band-structure-only calculations
- `nspin 4` enables spin-orbit coupling (needed for topological properties)
- `ecutwfc` and k-mesh should be converged for the material

## File Mapping

| ABACUS Output | Location | PYATB Parameter |
|---------------|----------|-----------------|
| `data-HR-sparse_SPIN0.csr` | `OUT.*/` | `HR_route` |
| `data-SR-sparse_SPIN0.csr` | `OUT.*/` | `SR_route` |
| `data-rR-sparse.csr` | `OUT.*/` | `rR_route` |

For nspin=2 (spin-polarized): Two sets of HR/SR files (SPIN0 and SPIN1).
For nspin=4 (SOC): Single set (SPIN0 contains full spinor Hamiltonian).

## Fermi Energy

The Fermi energy is found in the ABACUS running log file (`OUT.*/running_scf.log`). Search for the Fermi energy line and copy the value to the PYATB Input file.

Alternatively, use `fermi_energy Auto` with a `FERMI_ENERGY` block specifying `electron_num`.

## Unit Conventions

- ABACUS outputs H(R) in Rydberg (Ry) -- set `HR_unit Ry`
- ABACUS outputs r(R) in Bohr -- set `rR_unit Bohr`
- Lattice constant is in Bohr by default
- Conversion: 1 Bohr = 0.529177 Angstrom

## Lattice Vectors

Copy the lattice vectors from the ABACUS STRU file or the running log. The lattice constant is the overall scaling factor applied to the lattice vectors.

## Complete Workflow

```
1. Write ABACUS INPUT with out_mat_hs2=1, out_mat_r=1
2. Run ABACUS SCF calculation
3. Copy data-HR-sparse_SPIN0.csr, data-SR-sparse_SPIN0.csr, data-rR-sparse.csr
4. Note Fermi energy from running_scf.log
5. Write PYATB Input file with correct lattice, fermi_energy, file paths
6. Run: mpirun -np N pyatb
7. Check Out/ directory for results
```

## Traceability Sources

- Raw evidence: `raw/assets/source-provenance.json`
