"""Failing fixture: workflow references a malformed JSON config.

Exercises PYATB604 (config parse failure). HR.dat present so the config parse
error is the sole blocking finding.
"""
import json
import pyatb

with open("config.json") as fh:
    config = json.load(fh)

abf = pyatb.ABFunc(hr_file="HR.dat")
tb = pyatb.TightBinding(abf)
