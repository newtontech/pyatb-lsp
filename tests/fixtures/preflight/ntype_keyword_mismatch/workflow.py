"""Failing fixture: calculation='boltz_traj' declared without required kwargs.

Exercises PYATB608 (keyword/version mismatch — calculation entry point
requires mu_min/mu_max/mu_step/boltz_kmesh, all absent). Also exercises
PYATB602 because HR.dat is absent.
"""
import pyatb

abf = pyatb.ABFunc(hr_file="HR.dat")
tb = pyatb.TightBinding(abf)
boltz = pyatb.BoltzmannTraj(tb, calculation="boltz_traj", output="results/")
