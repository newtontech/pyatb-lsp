"""Invalid PyATB script - missing tight-binding data file."""

import pyatb

sr_file = "SR.dat"
tb = pyatb.TightBinding(sr_file=sr_file)
