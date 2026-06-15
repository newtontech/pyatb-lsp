"""Invalid PyATB script - missing SR.dat reference."""

import pyatb

hr_file = "HR.dat"
tb = pyatb.TightBinding(hr_file=hr_file)
