"""Invalid PyATB script - missing output path (PYATB-W070 warning)."""

import pyatb

hr_file = "HR.dat"
sr_file = "SR.dat"

tb = pyatb.TightBinding(hr_file=hr_file, sr_file=sr_file)
tb.run()
