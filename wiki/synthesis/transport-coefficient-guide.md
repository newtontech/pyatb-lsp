# Synthesis: How to Calculate Transport Coefficients with PYATB

## Prerequisites

1. ABACUS DFT calculation completed with `out_mat_hs2=1` and `out_mat_r=1`
2. HR, SR, rR files available
3. Fermi energy known (from ABACUS log)
4. PYATB installed (`pip install pyatb`)

## Step-by-Step Guide

### Step 1: Prepare Input Files

Copy the matrix files to your working directory:
```bash
mkdir work && cd work
cp ../abacus/OUT.YOUR_MATERIAL/data-HR-sparse_SPIN0.csr .
cp ../abacus/OUT.YOUR_MATERIAL/data-SR-sparse_SPIN0.csr .
cp ../abacus/OUT.YOUR_MATERIAL/data-rR-sparse.csr .
```

### Step 2: Write the Input File

Create a file named `Input` with the following structure:

```
INPUT_PARAMETERS
{
    nspin                  1
    package                ABACUS
    fermi_energy           YOUR_FERMI_ENERGY
    fermi_energy_unit      eV
    HR_route               data-HR-sparse_SPIN0.csr
    SR_route               data-SR-sparse_SPIN0.csr
    rR_route               data-rR-sparse.csr
    HR_unit                Ry
    rR_unit                Bohr
    max_kpoint_num         8000
}

LATTICE
{
    lattice_constant       VALUE
    lattice_constant_unit  Bohr
    lattice_vector
    A1x  A1y  A1z
    A2x  A2y  A2z
    A3x  A3y  A3z
}

BOLTZ_TRANSPORT
{
    transport_coeff_cal    1
    effective_mass_cal     1
    transport_method       CRTA
    electron_num           YOUR_ELECTRON_NUM
    grid                   50 50 50
    delta_mu_range         -5.0 5.0
    mu_step                0.1
    temperature_range      300 300
    temperature_step       50
    eta                    0.1
    relax_time             10
}
```

### Step 3: Choose Transport Method

#### CRTA (quick, qualitative)
```
transport_method       CRTA
relax_time             10
```
Best for: material screening, qualitative comparison, when relaxation time is unknown.

#### EMPC (more physical)
```
transport_method       EMPC
def_pot                2.0
young_mod              240.0
```
Best for: quantitative estimates when deformation potential and Young's modulus are known.

### Step 4: Run

```bash
export OMP_NUM_THREADS=1
mpirun -np 8 pyatb > job.log 2> job.err
```

### Step 5: Interpret Results

Results appear in `Out/TRANSPORT/`:

| File | Content | Key columns |
|------|---------|-------------|
| `carrier_DOS.dat` | Carrier density vs E vs T | Energy-fermi, n(10^20/cm3) |
| `electronic_conductivity_tensor.dat` | sigma (S/cm) | E, 9 tensor components (XX...ZZ) |
| `seebeck_tensor.dat` | S (muV/K) | E, 9 tensor components |
| `ke-tensor.dat` | k_e (V^2/K) | E, 9 tensor components |
| `mobility.dat` | mu (cm^2/V*S) | E, trace |
| `effective-mass.dat` | m* (m_e) | E, m* |

Data is grouped by temperature. The diagonal components (XX, YY, ZZ) represent transport along crystal axes.

## Tips for Accurate Results

1. **Converge the k-mesh:** Start with 30x30x30, increase until results converge
2. **Check delta_mu_range:** Should span enough to capture transport at your doping level
3. **Temperature:** Use appropriate temperature for your application (room temperature: 300 K)
4. **eta (smearing):** 0.1 eV is typical; smaller values need denser k-mesh
5. **max_kpoint_num:** Controls memory per MPI process; increase if needed

## Common Issues

- **Out of memory:** Reduce `max_kpoint_num` or increase MPI processes
- **Slow convergence:** Reduce k-mesh density first, then increase systematically
- **nspin=2 not supported:** Use nspin=1 (non-magnetic) or nspin=4 (SOC)

## Example: Cu Metal

```
INPUT_PARAMETERS
{
    nspin                  1
    package                ABACUS
    fermi_energy           Auto
    fermi_energy_unit      eV
    HR_route               data-HR-sparse_SPIN0.csr
    SR_route               data-SR-sparse_SPIN0.csr
    rR_route               data-rR-sparse.csr
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
```
