"""Invalid PyATB script - missing HR.dat reference."""

import pyatb

sr_file = "SR.dat"
tb = pyatb.TightBinding(sr_file=sr_file)
