"""Valid PyATB boltzmann-transport workflow fixture (preflight clean).

All cross-file artifacts present, calculation kwargs complete, k-mesh dense.
"""
import pyatb

config = pyatb.load_config("config.json")
abf = pyatb.ABFunc(hr_file="HR.dat", sr_file="SR.dat")

tb = pyatb.TightBinding(abf)
boltz = pyatb.BoltzmannTraj(
    tb,
    calculation="boltz_traj",
    fermi_energy=0.5,
    mu_min=-0.2,
    mu_max=0.2,
    mu_step=0.01,
    boltz_kmesh=[21, 21, 21],
    temperature=300,
    output="results/",
)
