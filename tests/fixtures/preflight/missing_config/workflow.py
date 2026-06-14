"""Failing fixture: workflow references a JSON config that does not exist.

Exercises PYATB601 (missing cross-file config artifact). HR.dat present so the
config is the sole blocking finding.
"""
import json
import pyatb

with open("config.json") as fh:
    config = json.load(fh)

abf = pyatb.ABFunc(hr_file="HR.dat")
tb = pyatb.TightBinding(abf)
