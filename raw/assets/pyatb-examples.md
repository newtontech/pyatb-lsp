# PYATB - Example Calculations

**Source:** https://github.com/pyatb/pyatb/tree/main/examples and /tutorial
**Retrieved:** 2026-06-12

This document catalogs all available example and tutorial calculations from the PYATB repository, with complete Input file contents for each.

---

## Example: Bi2Se3 (Band Structure, Wilson Loop, Spin Texture)

Topological insulator with spin-orbit coupling (nspin=4).

### Input File

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

BAND_STRUCTURE
{
    wf_collect                     0
    kpoint_mode                    line
    kpoint_num                     5
    high_symmetry_kpoint
    0.00000 0.00000 0.0000 100  # G
    0.00000 0.00000 0.5000 100  # Z
    0.50000 0.50000 0.0000 100  # F
    0.00000 0.00000 0.0000 100  # G
    0.50000 0.00000 0.0000 1    # L
}

WILSON_LOOP
{
    occ_band           78
    k_start            0.0  0.0  0.5
    k_vect1            1.0  0.0  0.0
    k_vect2            0.0  0.5  0.0
    nk1                101
    nk2                101
}

SPIN_TEXTURE
{
    nband              78
    kpoint_mode        direct
    kpoint_num         140
    kpoint_direct_coor
    # ... (circular k-points around Gamma)
}
```

### Features demonstrated
- Band structure with SOC
- Wilson loop (Chern number / Z2 invariant)
- Spin texture mapping

---

## Tutorial: Bi2Se3 Band (Band + Fat Band + PDOS + Wilson Loop)

Extended tutorial with orbital-projected analysis.

```
INPUT_PARAMETERS
{
    nspin                          4
    package                        ABACUS
    fermi_energy                   9.5064566484
    fermi_energy_unit              eV
    HR_route                       ../abacus/OUT.Bi2Se3/data-HR-sparse_SPIN0.csr
    SR_route                       ../abacus/OUT.Bi2Se3/data-SR-sparse_SPIN0.csr
    rR_route                       ../abacus/OUT.Bi2Se3/data-rR-sparse.csr
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

BAND_STRUCTURE
{
    wf_collect                     0
    kpoint_mode                    line
    kpoint_num                     5
    high_symmetry_kpoint
    0.00000 0.00000 0.0000 100  # G
    0.00000 0.00000 0.5000 100  # Z
    0.50000 0.50000 0.0000 100  # F
    0.00000 0.00000 0.0000 100  # G
    0.50000 0.00000 0.0000 1    # L
    kpoint_label G, Z, F, G, L
}

FAT_BAND
{
    band_range    28 128
    stru_file     STRU
    kpoint_mode                    line
    kpoint_num                     5
    high_symmetry_kpoint
    0.00000 0.00000 0.0000 100  # G
    0.00000 0.00000 0.5000 100  # Z
    0.50000 0.50000 0.0000 100  # F
    0.00000 0.00000 0.0000 100  # G
    0.50000 0.00000 0.0000 1    # L
    kpoint_label G, Z, F, G, L
}

PDOS
{
    stru_file     STRU
    e_range       0.5064566484 19.5064566484
    de            0.01
    sigma         0.07
    kpoint_mode   mp
    mp_grid       20 20 20
}

WILSON_LOOP
{
    occ_band           78
    k_start            0.0  0.0  0.0
    k_vect1            0.0  1.0  0.0
    k_vect2            0.5  0.0  0.0
    nk1                101
    nk2                101
}
```

---

## Tutorial: CsPbI3 Optical (Optical Conductivity)

Perovskite optical properties (non-magnetic, nspin=1).

```
INPUT_PARAMETERS
{
    nspin               1
    package             ABACUS
    fermi_energy        4.2808350436
    fermi_energy_unit   eV
    HR_route            ../abacus/OUT.CsPbI3/data-HR-sparse_SPIN0.csr
    SR_route            ../abacus/OUT.CsPbI3/data-SR-sparse_SPIN0.csr
    rR_route            ../abacus/OUT.CsPbI3/data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
}

LATTICE
{
    lattice_constant        1.8897261258369282
    lattice_constant_unit   Bohr
    lattice_vector
    6.2894000000      0.0000000000      0.0000000000
    0.0000000000      6.2894000000      0.0000000000
    0.0000000000      0.0000000000      6.2894000000
}

BAND_STRUCTURE
{
    wf_collect                     0
    kpoint_mode                    line
    kpoint_num                     6
    kpoint_label                   G, X, M, G, R, X
    high_symmetry_kpoint
    0.00000 0.00000 0.0000 20  # G
    0.00000 0.50000 0.0000 20  # X
    0.50000 0.50000 0.0000 25  # M
    0.00000 0.00000 0.0000 30  # G
    0.50000 0.50000 0.5000 25  # R
    0.00000 0.50000 0.0000 1   # X
}

OPTICAL_CONDUCTIVITY
{
    occ_band      22
    omega         0.5  10
    domega        0.01
    eta           0.2
    grid          30 30 30
}
```

---

## Tutorial: FeCl2 AHC/ANC (Transport Coefficients)

Anomalous Hall and Nernst conductivities (SOC, nspin=4).

```
INPUT_PARAMETERS
{
    nspin                           4
    package                         ABACUS
    fermi_energy                    -0.82497406093
    fermi_energy_unit               eV
    HR_route                        ../abacus/OUT.FeCl2/data-HR-sparse_SPIN0.csr
    SR_route                        ../abacus/OUT.FeCl2/data-SR-sparse_SPIN0.csr
    rR_route                        ../abacus/OUT.FeCl2/data-rR-sparse.csr
    HR_unit                         Ry
    rR_unit                         Bohr
}

LATTICE
{
    lattice_constant                1.8897162
    lattice_constant_unit           Bohr
    lattice_vector
    3.4750    0.0000    0.00000
   -1.7375    3.0094    0.00000
    0.0000    0.0000   17.53999
}

BAND_STRUCTURE
{
    wf_collect                      0
    kpoint_mode                     line
    kpoint_num                      4
    high_symmetry_kpoint
    0.5       0        0       200  # M
    0         0        0       200  # G
    0.3333    0.3333   0.3333  200  # K
    0.5       0        0       1    # M
    kpoint_label                    M, G, K, M
}

ANC
{
    fermi_range                    -1.0 1.0
    de                             0.01
    eta                            0.01
    integrate_grid                 200 200 1
}
```

---

## Tutorial: WS2 Shift Current

Nonlinear optical response (nspin=1).

```
INPUT_PARAMETERS
{
    nspin                   1
    package                 ABACUS
    fermi_energy            0.93900603892
    fermi_energy_unit       eV
    HR_route                ../abacus/OUT.WS2/data-HR-sparse_SPIN0.csr
    SR_route                ../abacus/OUT.WS2/data-SR-sparse_SPIN0.csr
    rR_route                ../abacus/OUT.WS2/data-rR-sparse.csr
    HR_unit                 Ry
    rR_unit                 Bohr
}

LATTICE
{
    lattice_constant        1.8897162
    lattice_constant_unit   Bohr
    lattice_vector
    3.183820900165   0.0              0.0
   -1.591910450082   2.757269780643   0.0
    0.0              0.0              20.086904001384
}

SHIFT_CURRENT
{
    occ_band                13
    omega                   0   4
    domega                  0.01
    smearing_method         1
    eta                     0.02
    grid                    200 200 1
}
```

---

## Tutorial: GaAs SHG (Second Harmonic Generation)

```
INPUT_PARAMETERS
{
    nspin               1
    package             ABACUS
    fermi_energy        10.171348972
    fermi_energy_unit   eV
    HR_route            ../abacus/OUT.GaAs/data-HR-sparse_SPIN0.csr
    SR_route            ../abacus/OUT.GaAs/data-SR-sparse_SPIN0.csr
    rR_route            ../abacus/OUT.GaAs/data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
    max_kpoint_num      100000
}

LATTICE
{
    lattice_constant        1.889727
    lattice_constant_unit   Bohr
    lattice_vector
    0.0000000000000000    2.7650000000000001    2.7650000000000001
    2.7650000000000001    0.0000000000000000    2.7650000000000001
    2.7650000000000001    2.7650000000000001    0.0000000000000000
}

SHG
{
    omega           0.01 4
    domega          0.01
    eta             0.05
    grid            50 50 50
}
```

---

## Tutorial: NV Band Unfolding

Diamond NV center supercell unfolded to primitive cell.

```
INPUT_PARAMETERS
{
    nspin                           1
    package                         ABACUS
    fermi_energy                    15.984509735
    fermi_energy_unit               eV
    HR_route                        ../abacus/OUT.NV/data-HR-sparse_SPIN0.csr
    SR_route                        ../abacus/OUT.NV/data-SR-sparse_SPIN0.csr
    rR_route                        ../abacus/OUT.NV/data-rR-sparse.csr
    HR_unit                         Ry
    rR_unit                         Bohr
}

LATTICE
{
    lattice_constant                1.8897162
    lattice_constant_unit           Bohr
    lattice_vector
    7.13366 0 0
    0 7.13366 0
    0 0 7.13366
}

BANDUNFOLDING
{
    stru_file                       STRU
    ecut                            10
    band_range                      10 250
    m_matrix                        -2 2 2 2 -2 2 2 2 -2
    kpoint_mode                     line
    kpoint_num                      5
    high_symmetry_kpoint
    0.500000  0.000000  0.500000 300  # X
    0.500000  0.250000  0.750000 300  # W
    0.500000  0.500000  0.500000 300  # L
    0.000000  0.000000  0.000000 300  # G
    0.500000  0.000000  0.500000 1    # X
    kpoint_label                    X, W, L, G, X
}
```

---

## Example: Cu (Fermi Energy Auto + Fermi Surface)

Demonstrates automatic Fermi energy calculation.

```
INPUT_PARAMETERS
{
    nspin                  1
    package                ABACUS
    fermi_energy           Auto
    fermi_energy_unit      eV
    HR_route               data-HR-sparse_SPIN0.csr
    SR_route               data-SR-sparse_SPIN0.csr
    HR_unit                Ry
    rR_unit                Bohr
    max_kpoint_num         8000
}

LATTICE
{
    lattice_constant       6.91640
    lattice_constant_unit  Bohr
    lattice_vector
    0.50  0.50  0.00
    0.50  0.00  0.50
    0.00  0.50  0.50
}

FERMI_ENERGY
{
    temperature            0
    electron_num           11
    grid                   50 50 50
    epsilon                1e-4
}

FERMI_SURFACE
{
    bar                    1e-5
    kpoint_mode            mp
    k_start                0 0 0
    k_vect1                1 0 0
    k_vect2                0 1 0
    k_vect3                0 0 1
    mp_grid                50 50 50
}
```

---

## Example: Fe (Berry Curvature + AHC)

Magnetic system with anomalous Hall conductivity.

```
INPUT_PARAMETERS
{
    nspin               4
    package             ABACUS
    fermi_energy        17.71231891464643
    fermi_energy_unit   eV
    HR_route            data-HR-sparse_SPIN0.csr
    SR_route            data-SR-sparse_SPIN0.csr
    rR_route            data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
}

LATTICE
{
    lattice_constant        1.0
    lattice_constant_unit   Bohr
    lattice_vector
     2.71175  2.71175 2.71175
    -2.71175  2.71175 2.71175
    -2.71175 -2.71175 2.71175
}

BERRY_CURVATURE
{
    method                  0
    kpoint_mode             line
    kpoint_num              10
    high_symmetry_kpoint
    0.0   0.0    0.0   100 # G
    0.5  -0.5   -0.5   100 # H
    0.75  0.25  -0.25  100 # P
    0.5   0.0   -0.5   100 # N
    0.0   0.0    0.0   100 # G
    0.5   0.5    0.5   100 # H
    0.5   0.0    0.0   100 # N
    0.0   0.0    0.0   100 # G
    0.75  0.25  -0.25  100 # P
    0.5   0.0    0.0   1   # N
}

AHC
{
    integrate_mode          Grid
    integrate_grid          100 100 100
    adaptive_grid           20 20 20
    adaptive_grid_threshold 100
}
```

---

## Example: Si2 (DOS + PDOS + JDOS + Optical Conductivity)

Full band analysis of silicon.

```
INPUT_PARAMETERS
{
    nspin               1
    package             ABACUS
    fermi_energy        6.389728305291531
    fermi_energy_unit   eV
    HR_route            data-HR-sparse_SPIN0.csr
    SR_route            data-SR-sparse_SPIN0.csr
    rR_route            data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
}

LATTICE
{
    lattice_constant        1.8897162
    lattice_constant_unit   Bohr
    lattice_vector
    0.000000000000  2.715000000000  2.715000000000
    2.715000000000  0.000000000000  2.715000000000
    2.715000000000  2.715000000000  0.000000000000
}

BAND_STRUCTURE { ... }
FAT_BAND { band_range 1 8, stru_file STRU, ... }
PDOS { stru_file STRU, e_range -5.0 17.0, de 0.01, sigma 0.07, mp_grid 12 12 12 }
JDOS { occ_band 4, omega 0 10, domega 0.01, eta 0.2, grid 20 20 20 }
OPTICAL_CONDUCTIVITY { occ_band 4, omega 0 10, domega 0.01, eta 0.1, grid 50 50 50 }
```

---

## Example: Te (Berry Curvature Dipole)

```
INPUT_PARAMETERS
{
    nspin                     4
    package                   ABACUS
    fermi_energy              9.564418181126964
    fermi_energy_unit         eV
    HR_route                  data-HR-sparse_SPIN0.csr
    SR_route                  data-SR-sparse_SPIN0.csr
    rR_route                  data-rR-sparse.csr
    HR_unit                   Ry
    rR_unit                   Bohr
    max_kpoint_num            28000
}

LATTICE
{
    lattice_constant          1.8897162
    lattice_constant_unit     Bohr
    lattice_vector
    2.22    -3.84515    0.000
    2.22     3.84515    0.000
    0.00     0.00000    5.910
}

BERRY_CURVATURE_DIPOLE
{
    omega                     9.464  10.064
    domega                    0.001
    integrate_mode            Grid
    integrate_grid            100 100 100
    adaptive_grid             20 20 20
    adaptive_grid_threshold   20000
}
```

---

## Example: fcc-Ni (Orbital Magnetization)

```
INPUT_PARAMETERS
{
    nspin               4
    package             ABACUS
    fermi_energy        18.595382272
    fermi_energy_unit   eV
    HR_route            data-HR-sparse_SPIN0.csr
    SR_route            data-SR-sparse_SPIN0.csr
    rR_route            data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
}

LATTICE
{
    lattice_constant        6.65
    lattice_constant_unit   Bohr
    lattice_vector
    0.0  0.5  0.5
    0.5  0.0  0.5
    0.5  0.5  0.0
}

ORBITAL_MAGNETIZATION
{
    fermi_energy            18.595382272
    fermi_range             -3 3
    de                      0.05
    eta                     0.01
    grid                    40 40 40
}
```

---

## Example: PbTiO3 (Polarization)

```
INPUT_PARAMETERS
{
    nspin               1
    package             ABACUS
    fermi_energy        13.38267075814371
    fermi_energy_unit   eV
    HR_route            data-HR-sparse_SPIN0.csr
    SR_route            data-SR-sparse_SPIN0.csr
    rR_route            data-rR-sparse.csr
    HR_unit             Ry
    rR_unit             Bohr
}

LATTICE
{
    lattice_constant        7.3699
    lattice_constant_unit   Bohr
    lattice_vector
    1.0000000000         0.0000000000         0.0000000000
    0.0000000000         1.0000000000         0.0000000000
    0.0000000000         0.0000000000         1.0000000000
}

POLARIZATION
{
    occ_band      22
    nk1           10
    nk2           10
    nk3           10
    atom_type     3
    stru_file     STRU
    valence_e     14 12 6
}
```

---

## Run Script Template

```bash
#!/bin/bash
source ~/software/miniconda3/bin/activate
conda activate pyatb

export OMP_NUM_THREADS=1
num_mpi=8
mpirun -n $num_mpi pyatb > job.log 2> job.err
```
