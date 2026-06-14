"""Failing fixture: boltzmann transport declared with a Gamma-only kmesh.

Exercises PYATB606 (k-mesh too coarse) — a runtime-risk warning rather than a
blocking error. HR.dat is present so the only finding is the kmesh.
"""
import pyatb

abf = pyatb.ABFunc(hr_file="HR.dat")
tb = pyatb.TightBinding(abf)
boltz = pyatb.BoltzmannTraj(
    tb,
    calculation="boltz_traj",
    fermi_energy=0.5,
    mu_min=-0.2,
    mu_max=0.2,
    mu_step=0.01,
    boltz_kmesh=[1, 1, 1],
    temperature=300,
    output="results/",
)
